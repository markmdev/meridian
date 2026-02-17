#!/usr/bin/env python3
"""
Workspace Sync Hook

Extracts session transcript and spawns a headless Claude session to update
the workspace. Runs synchronously so workspace is ready before context injection.

Triggers: SessionStart (compact, clear), SessionEnd
"""

import json
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import STATE_DIR, WORKSPACE_FILE

TRANSCRIPT_PATH_STATE = f"{STATE_DIR}/transcript-path"
WORKSPACE_SYNC_LOCK = f"{STATE_DIR}/workspace-sync.lock"
MIN_ENTRIES_THRESHOLD = 5  # Skip if fewer than this many meaningful entries


def find_compact_boundaries(transcript_path: str) -> list[int]:
    """Find line numbers of all compact_boundary entries in the transcript."""
    boundaries = []
    with open(transcript_path) as f:
        for i, line in enumerate(f):
            try:
                entry = json.loads(line)
                if entry.get("type") == "system" and entry.get("subtype") == "compact_boundary":
                    boundaries.append(i)
            except (json.JSONDecodeError, KeyError):
                continue
    return boundaries


def count_lines(path: str) -> int:
    with open(path) as f:
        return sum(1 for _ in f)


def get_extraction_range(transcript_path: str, source: str) -> tuple[int, int]:
    """Determine start/end lines for extraction based on event source."""
    boundaries = find_compact_boundaries(transcript_path)
    total = count_lines(transcript_path)

    if source == "compact":
        # Current compaction is the last boundary — extract entries before it
        if len(boundaries) >= 2:
            return boundaries[-2], boundaries[-1]
        elif len(boundaries) == 1:
            return 0, boundaries[0]
        else:
            return 0, total
    else:
        # clear / SessionEnd: everything since last boundary to end
        if boundaries:
            return boundaries[-1], total
        else:
            return 0, total


def extract_tool_input_summary(input_dict: dict) -> dict:
    """Extract key identifiers from tool input, skipping large content."""
    SKIP_KEYS = {"content", "old_string", "new_string", "new_source"}
    MAX_LEN = 200
    summary = {}
    for key, value in input_dict.items():
        if key in SKIP_KEYS:
            continue
        if isinstance(value, str) and len(value) > MAX_LEN:
            summary[key] = value[:MAX_LEN] + "..."
        else:
            summary[key] = value
    return summary


def extract_transcript(transcript_path: str, start_line: int, end_line: int) -> list[dict]:
    """Extract meaningful entries from transcript range."""
    entries = []
    with open(transcript_path) as f:
        for i, line in enumerate(f):
            if i < start_line:
                continue
            if i >= end_line:
                break

            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = raw.get("type", "")

            # Skip non-message types
            if entry_type in ("progress", "file-history-snapshot", "system"):
                continue

            msg = raw.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", "")

            # User text message
            if entry_type == "user" and role == "user" and isinstance(content, str) and content.strip():
                # Skip if it looks like injected hook context (very long system messages)
                if len(content) > 5000 and ("<injected-project-context>" in content or "<system-reminder>" in content):
                    continue
                entries.append({"type": "user", "text": content[:3000]})

            # User text from content blocks (non-tool-result)
            elif entry_type == "user" and role == "user" and isinstance(content, list):
                # Skip tool_result blocks
                if any(b.get("type") == "tool_result" for b in content):
                    continue
                for block in content:
                    if block.get("type") == "text" and block.get("text", "").strip():
                        text = block["text"]
                        if len(text) > 5000 and ("<injected-project-context>" in text or "<system-reminder>" in text):
                            continue
                        entries.append({"type": "user", "text": text[:3000]})

            # Assistant messages
            elif entry_type == "assistant" and role == "assistant" and isinstance(content, list):
                for block in content:
                    btype = block.get("type", "")
                    if btype == "text" and block.get("text", "").strip():
                        entries.append({"type": "assistant", "text": block["text"][:3000]})
                    elif btype == "thinking" and block.get("thinking", "").strip():
                        entries.append({"type": "thinking", "text": block["thinking"][:2000]})
                    elif btype == "tool_use":
                        tool_entry = {"type": "tool_use", "tool": block.get("name", "unknown")}
                        if isinstance(block.get("input"), dict):
                            tool_entry["input"] = extract_tool_input_summary(block["input"])
                        entries.append(tool_entry)

    return entries


def load_workspace(project_dir: Path) -> tuple[str, list[tuple[str, str]]]:
    """Load workspace root and all pages."""
    root_path = project_dir / WORKSPACE_FILE
    root_content = ""
    if root_path.exists():
        try:
            root_content = root_path.read_text()
        except IOError:
            pass

    pages = []
    pages_dir = project_dir / ".meridian" / "workspace"
    if pages_dir.exists():
        for page_file in sorted(pages_dir.rglob("*.md")):
            rel = page_file.relative_to(project_dir)
            try:
                pages.append((str(rel), page_file.read_text()))
            except IOError:
                continue

    return root_content, pages


def build_prompt(entries: list[dict], workspace_root: str, workspace_pages: list[tuple[str, str]]) -> str:
    """Build the prompt for the workspace maintenance agent."""
    parts = []

    parts.append("""You are the Workspace Maintenance Agent. Analyze a coding session transcript and update the project's persistent knowledge base.

The workspace is a library of project knowledge — decisions, lessons, architecture, gotchas. NOT a session log.

## Current Workspace Root (.meridian/WORKSPACE.md)
""")
    parts.append(workspace_root if workspace_root.strip() else "(empty — create it)")

    if workspace_pages:
        parts.append("\n## Current Workspace Pages\n")
        for path, content in workspace_pages:
            parts.append(f"<page path=\"{path}\">")
            parts.append(content.rstrip())
            parts.append("</page>\n")

    parts.append("\n## Session Transcript\n")
    parts.append("```json")
    parts.append(json.dumps(entries, indent=2, ensure_ascii=False))
    parts.append("```")

    parts.append("""

## Task

Update the workspace with knowledge worth preserving:

- **Decisions and rationale** — why X was chosen over Y
- **Lessons learned** — what broke, what worked, gotchas discovered
- **Architecture insights** — how components connect, patterns that emerged
- **Key technical details** — file paths, APIs, configurations that matter
- **Open questions** — what's unresolved, what needs future attention

### Rules

- Write clean reference material. No timestamps, no "in this session", no logs.
- Update existing pages when the topic already has a page. Don't duplicate.
- Create new pages in `.meridian/workspace/` for substantial new topics.
- Every new page MUST be linked from `.meridian/WORKSPACE.md`.
- Remove information superseded by this session's work.
- If nothing worth preserving happened, output "No workspace updates needed." and stop.
- Be concise — write what a future agent needs to know, not everything that happened.

Use the Write tool to update files.""")

    return "\n".join(parts)


def acquire_lock(project_dir: Path) -> bool:
    """Try to acquire the workspace sync lock. Returns True if acquired."""
    lock_path = project_dir / WORKSPACE_SYNC_LOCK
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        # Check if lock is stale (older than 5 minutes)
        try:
            import time
            age = time.time() - lock_path.stat().st_mtime
            if age < 300:
                return False
        except OSError:
            pass
    try:
        lock_path.write_text(str(os.getpid()))
        return True
    except IOError:
        return False


def release_lock(project_dir: Path):
    try:
        (project_dir / WORKSPACE_SYNC_LOCK).unlink(missing_ok=True)
    except OSError:
        pass


def run_workspace_agent(prompt: str, project_dir: Path) -> bool:
    """Run headless claude -p to update workspace. Returns True on success."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", "sonnet",
                "--allowedTools", "Write,Read",
                "--dangerously-skip-permissions",
                "--no-session-persistence",
                "--setting-sources", "user",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(project_dir),
            env=env,
        )
        if result.returncode != 0:
            print(f"[Meridian] Workspace agent exited with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"[Meridian] {result.stderr[:500]}", file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print("[Meridian] Workspace agent timed out (180s)", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("[Meridian] claude CLI not found", file=sys.stderr)
        return False


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    hook_event = input_data.get("hook_event_name", "")
    source = input_data.get("source", "")
    transcript_path = input_data.get("transcript_path", "")

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))

    # Determine which transcript to read
    if hook_event == "SessionStart" and source == "clear":
        # On clear, new transcript is created — read the OLD path from state
        saved_path = project_dir / TRANSCRIPT_PATH_STATE
        if saved_path.exists():
            transcript_path = saved_path.read_text().strip()
        else:
            print("[Meridian] No saved transcript path for clear event, skipping workspace sync", file=sys.stderr)
            sys.exit(0)
    elif hook_event == "SessionStart" and source == "compact":
        # On compact, same transcript file — use input_data directly
        pass
    elif hook_event == "SessionEnd":
        # On exit, use input_data directly
        pass
    else:
        sys.exit(0)

    if not transcript_path or not Path(transcript_path).exists():
        sys.exit(0)

    # Acquire lock
    if not acquire_lock(project_dir):
        print("[Meridian] Workspace sync already running, skipping", file=sys.stderr)
        sys.exit(0)

    try:
        # Extract transcript
        start_line, end_line = get_extraction_range(transcript_path, source if source else "end")
        entries = extract_transcript(transcript_path, start_line, end_line)

        # Skip if too few meaningful entries
        meaningful = [e for e in entries if e["type"] in ("user", "assistant")]
        if len(meaningful) < MIN_ENTRIES_THRESHOLD:
            sys.exit(0)

        # Load workspace
        workspace_root, workspace_pages = load_workspace(project_dir)

        # Build prompt and run agent
        prompt = build_prompt(entries, workspace_root, workspace_pages)

        print("[Meridian] Updating workspace from session transcript...", file=sys.stderr)
        success = run_workspace_agent(prompt, project_dir)

        if success:
            print("[Meridian] Workspace updated.", file=sys.stderr)
        else:
            print("[Meridian] Workspace update failed.", file=sys.stderr)

    finally:
        release_lock(project_dir)

    sys.exit(0)


if __name__ == "__main__":
    main()

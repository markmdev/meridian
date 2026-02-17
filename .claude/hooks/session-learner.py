#!/usr/bin/env python3
"""
Session Learner — SessionStart (compact, clear) + SessionEnd Hook

Extracts session transcript and spawns a headless Claude session to:
1. Update the workspace (persistent knowledge library)
2. Learn from user corrections (update CLAUDE.md files)

Runs synchronously on SessionStart so workspace is ready before context injection.
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
LAST_SYNC_FILE = f"{STATE_DIR}/last-workspace-sync"
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


def load_claudemd_files(project_dir: Path) -> tuple[str, str]:
    """Load global and project CLAUDE.md files."""
    global_path = Path.home() / ".claude" / "CLAUDE.md"
    project_path = project_dir / "CLAUDE.md"

    global_content = ""
    if global_path.exists():
        try:
            global_content = global_path.read_text()
        except IOError:
            pass

    project_content = ""
    if project_path.exists():
        try:
            project_content = project_path.read_text()
        except IOError:
            pass

    return global_content, project_content


def build_prompt(entries: list[dict], workspace_root: str, workspace_pages: list[tuple[str, str]], project_dir: Path) -> str:
    """Build the prompt for the workspace maintenance agent."""
    global_claudemd, project_claudemd = load_claudemd_files(project_dir)
    global_claudemd_path = str(Path.home() / ".claude" / "CLAUDE.md")
    project_claudemd_path = str(project_dir / "CLAUDE.md")

    parts = []

    parts.append("""You are a session maintenance agent with two jobs:

1. **Update the workspace** — persistent knowledge library for the project
2. **Learn from corrections** — when the user corrects the agent, save it as a permanent instruction

---

## Job 1: Workspace

The workspace is a library of project knowledge — decisions, lessons, architecture, gotchas. NOT a session log.

### Current Workspace Root (.meridian/WORKSPACE.md)
""")
    parts.append(workspace_root if workspace_root.strip() else "(empty — create it)")

    if workspace_pages:
        parts.append("\n### Current Workspace Pages\n")
        for path, content in workspace_pages:
            parts.append(f"<page path=\"{path}\">")
            parts.append(content.rstrip())
            parts.append("</page>\n")

    parts.append(f"""
### Workspace Rules

- Write clean reference material. No timestamps, no "in this session", no logs.
- Update existing pages when the topic already has a page. Don't duplicate.
- Create new pages in `.meridian/workspace/` for substantial new topics.
- Every new page MUST be linked from `.meridian/WORKSPACE.md`.
- Remove information superseded by this session's work.
- Be concise — write what a future agent needs to know, not everything that happened.

---

## Job 2: Learn from Corrections

Scan the transcript for moments where the user corrects the agent's behavior, expresses a preference, or teaches something that should apply going forward. Save these as permanent instructions in the appropriate CLAUDE.md file.

### Current CLAUDE.md Files

<file path="{global_claudemd_path}">
{global_claudemd if global_claudemd.strip() else "(empty)"}
</file>

<file path="{project_claudemd_path}">
{project_claudemd if project_claudemd.strip() else "(empty)"}
</file>

### CLAUDE.md Rules

- Write as the user giving instructions to an agent. Direct, imperative voice.
- **Global** (`{global_claudemd_path}`): preferences that apply to all projects (communication style, workflow habits, general coding preferences).
- **Project** (`{project_claudemd_path}`): instructions specific to this codebase (architecture decisions, project conventions, tech stack preferences).
- Don't duplicate instructions already present in either file.
- Don't add one-time fixes or task-specific instructions. Only lasting preferences.
- Append new entries. Don't rewrite or reorganize existing content.
- If no corrections or preferences were expressed, don't touch the CLAUDE.md files.

---

## Session Transcript
""")
    parts.append("```json")
    parts.append(json.dumps(entries, indent=2, ensure_ascii=False))
    parts.append("```")

    parts.append("""

## Execute

Do both jobs. If nothing worth preserving for either job, say so and stop.

Use the Write tool (or Read then Edit) to update files.""")

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


def was_recently_synced(project_dir: Path) -> bool:
    """Check if workspace was synced in the last 30 seconds (dedup for /clear)."""
    import time
    sync_path = project_dir / LAST_SYNC_FILE
    if sync_path.exists():
        try:
            last_sync = float(sync_path.read_text().strip())
            if time.time() - last_sync < 30:
                return True
        except (ValueError, IOError):
            pass
    return False


def mark_synced(project_dir: Path):
    """Record that workspace was just synced."""
    import time
    sync_path = project_dir / LAST_SYNC_FILE
    try:
        sync_path.parent.mkdir(parents=True, exist_ok=True)
        sync_path.write_text(str(time.time()))
    except IOError:
        pass


def run_workspace_agent(prompt: str, project_dir: Path) -> bool:
    """Run headless claude -p to update workspace. Returns True on success."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", "claude-opus-4-6",
                "--allowedTools", "Write,Read,Edit",
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
        # Save agent output for inspection
        output_path = project_dir / f"{STATE_DIR}/session-learner-output.md"
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            from datetime import datetime
            header = f"# Session Learner Output\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n**Exit code:** {result.returncode}\n\n---\n\n"
            output_path.write_text(header + (result.stdout or "*(no output)*") + "\n")
        except (IOError, OSError):
            pass

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

    # Determine if this is an event we handle
    is_compact_clear = hook_event == "SessionStart" and source in ("compact", "clear")
    is_session_end = hook_event == "SessionEnd"

    if not is_compact_clear and not is_session_end:
        sys.exit(0)

    # Dedup: /clear fires both SessionEnd and SessionStart:clear on the same transcript.
    # Skip if we already processed recently.
    if was_recently_synced(project_dir):
        sys.exit(0)

    # For compact/clear: acquire lock IMMEDIATELY so context-injector can wait.
    # Hooks run in parallel — lock must exist before context-injector checks for it.
    lock_acquired = False
    if is_compact_clear:
        if not acquire_lock(project_dir):
            print("[Meridian] Workspace sync already running, skipping", file=sys.stderr)
            sys.exit(0)
        lock_acquired = True

    try:
        # Determine which transcript to read
        if source == "clear":
            saved_path = project_dir / TRANSCRIPT_PATH_STATE
            if saved_path.exists():
                transcript_path = saved_path.read_text().strip()
            else:
                print("[Meridian] No saved transcript path for clear event, skipping", file=sys.stderr)
                return
        # compact and SessionEnd use transcript_path from input_data directly

        if not transcript_path or not Path(transcript_path).exists():
            return

        # For SessionEnd: acquire lock now (context-injector doesn't run, no rush)
        if is_session_end:
            if not acquire_lock(project_dir):
                print("[Meridian] Workspace sync already running, skipping", file=sys.stderr)
                return
            lock_acquired = True

        # Extract transcript
        start_line, end_line = get_extraction_range(transcript_path, source if source else "end")
        entries = extract_transcript(transcript_path, start_line, end_line)

        # Skip if too few meaningful entries
        meaningful = [e for e in entries if e["type"] in ("user", "assistant")]
        if len(meaningful) < MIN_ENTRIES_THRESHOLD:
            return

        # Load workspace
        workspace_root, workspace_pages = load_workspace(project_dir)

        # Build prompt and run agent
        prompt = build_prompt(entries, workspace_root, workspace_pages, project_dir)

        print("[Meridian] Updating workspace from session transcript...", file=sys.stderr)
        success = run_workspace_agent(prompt, project_dir)

        if success:
            print("[Meridian] Workspace updated.", file=sys.stderr)
            mark_synced(project_dir)
        else:
            print("[Meridian] Workspace update failed.", file=sys.stderr)

    finally:
        if lock_acquired:
            release_lock(project_dir)

    sys.exit(0)


if __name__ == "__main__":
    main()

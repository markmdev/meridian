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
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import WORKSPACE_FILE, scan_project_frontmatter, get_project_config, get_state_dir, state_path

TRANSCRIPT_PATH_STATE = "transcript-path"
WORKSPACE_SYNC_LOCK = "workspace-sync.lock"
LAST_SYNC_FILE = "last-workspace-sync"
SESSION_LEARNER_LOG = "session-learner.jsonl"
MAX_LOG_ENTRIES = 50
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


def load_workspace(project_dir: Path) -> str:
    """Load workspace root content."""
    root_path = project_dir / WORKSPACE_FILE
    if root_path.exists():
        try:
            return root_path.read_text()
        except IOError:
            pass
    return ""


def gather_git_context(project_dir: Path) -> str:
    """Gather recent git commits and PRs for the session learner.

    Gives the learner concrete evidence of what work was done,
    beyond what's visible in the transcript.
    """
    parts = []

    try:
        # Get current user's email for filtering
        user_email_result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True, text=True, timeout=5,
            cwd=str(project_dir)
        )
        user_email = user_email_result.stdout.strip() if user_email_result.returncode == 0 else None

        # Last 20 commits by user
        cmd = ["git", "log", "--format=%h %s (%cr)", "-20", "--all"]
        if user_email:
            cmd.append(f"--author={user_email}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=str(project_dir))
        if result.returncode == 0 and result.stdout.strip():
            parts.append("### Recent Commits")
            parts.append("```")
            parts.append(result.stdout.strip())
            parts.append("```")
            parts.append("")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    try:
        # Last 5 open PRs by user
        gh_user_result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True, text=True, timeout=10,
            cwd=str(project_dir)
        )
        gh_user = gh_user_result.stdout.strip() if gh_user_result.returncode == 0 else None

        if gh_user:
            result = subprocess.run(
                ["gh", "pr", "list", "--state", "open", "--author", gh_user, "--limit", "5",
                 "--json", "number,title,headRefName,createdAt",
                 "--template", '{{range .}}#{{.number}} {{.title}} [{{.headRefName}}] (created {{timeago .createdAt}})\n{{end}}'],
                capture_output=True, text=True, timeout=10,
                cwd=str(project_dir)
            )
            if result.returncode == 0 and result.stdout.strip():
                parts.append("### Open PRs")
                parts.append("```")
                parts.append(result.stdout.strip())
                parts.append("```")
                parts.append("")

            result = subprocess.run(
                ["gh", "pr", "list", "--state", "merged", "--author", gh_user, "--limit", "5",
                 "--json", "number,title,mergedAt",
                 "--template", '{{range .}}#{{.number}} {{.title}} (merged {{timeago .mergedAt}})\n{{end}}'],
                capture_output=True, text=True, timeout=10,
                cwd=str(project_dir)
            )
            if result.returncode == 0 and result.stdout.strip():
                parts.append("### Recently Merged PRs")
                parts.append("```")
                parts.append(result.stdout.strip())
                parts.append("```")
                parts.append("")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return "\n".join(parts)


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


def build_prompt(entries: list[dict], workspace_root: str, git_context: str, project_dir: Path, mode: str = "project") -> str:
    """Build the prompt for the workspace maintenance agent."""
    assistant_mode = mode == "assistant"
    global_claudemd, project_claudemd = load_claudemd_files(project_dir)
    global_claudemd_path = str(Path.home() / ".claude" / "CLAUDE.md")
    project_claudemd_path = str(project_dir / "CLAUDE.md")

    parts = []

    if assistant_mode:
        job4_desc = "**Maintain docs** — create, update, or delete files across the workspace"
    else:
        job4_desc = "**Maintain docs** — create/update long-term reference docs in `.meridian/docs/`"

    parts.append(f"""You are a session maintenance agent with four jobs:

1. **Update the workspace** — maintain WORKSPACE.md as the project's short-term memory
2. **Learn from corrections** — when the user corrects the agent, save it as a permanent instruction
3. **Capture next steps** — immediate work for the next session
4. {job4_desc}

---

## Job 1: Workspace

WORKSPACE.md is the project's **short-term memory** — what's happening now, what was just learned, what needs attention soon. Everything lives in this single file, organized by project sections.

### Current WORKSPACE.md
""")
    parts.append(workspace_root if workspace_root.strip() else "(empty — create it)")

    if assistant_mode:
        workspace_rules = """### Structure

Each project gets a section with these standard subsections:

```markdown
### Project Name

One-line description.

**Architecture:** tech stack summary

(then any of these subsections, as needed:)

**In Progress:** active work items, what's being built right now
**Known Issues:** bugs, blockers, things that need fixing
**Key Decisions:** recent decisions that affect upcoming work
**Lessons Learned:** gotchas discovered, patterns to remember
**Completed:** recently finished work worth noting for context

**Next Steps:**
1. Immediate item for next session
2. Another immediate item
```

### Rules

- Write clean reference material. No timestamps, no "in this session", no logs.
- Everything goes in WORKSPACE.md — no sub-pages, no separate workspace files.
- Update existing project sections. Don't create new sections for the same project.
- Create new sections following the project's existing conventions.
- Remove information that's no longer relevant (completed work older than a few sessions, resolved issues, superseded decisions).
- Be concise — write what the next session's agent needs to know.
- If information will be useful for more than 2 weeks, it belongs in a doc file, not here."""
    else:
        workspace_rules = """### Structure

Each project gets a section with these standard subsections:

```markdown
### Project Name

One-line description.

**Architecture:** tech stack summary

(then any of these subsections, as needed:)

**In Progress:** active work items, what's being built right now
**Known Issues:** bugs, blockers, things that need fixing
**Key Decisions:** recent decisions that affect upcoming work
**Lessons Learned:** gotchas discovered, patterns to remember
**Completed:** recently finished work worth noting for context

**Next Steps:**
1. Immediate item for next session
2. Another immediate item
```

### Rules

- Write clean reference material. No timestamps, no "in this session", no logs.
- Everything goes in WORKSPACE.md — no sub-pages in `.meridian/workspace/`.
- Update existing project sections. Don't create duplicate sections.
- Remove information that's no longer relevant (completed work older than a few sessions, resolved issues, superseded decisions).
- Be concise — write what the next session's agent needs to know.
- If information will be useful for more than 2 weeks, it belongs in `.meridian/docs/`, not here."""

    parts.append(f"""
{workspace_rules}

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

## Job 3: Next Steps

Maintain a per-project `**Next Steps:**` subsection within each project's section in WORKSPACE.md, plus a global `## Next Steps` section at the bottom for cross-project items.

### Rules

- **Only immediate work for the next 1-2 sessions.** Items that can be acted on right away.
- Do NOT include: future improvements mentioned in passing, "someday" refactors, nice-to-have ideas, long-term roadmap items, or things the user said they'd do "next week" or "later."
- Include enough context that a fresh agent can act without reading the full workspace.
- Replace previous next steps entirely — don't append.
- If everything is complete and nothing is pending, write "No pending work."

---

## Git Activity
""")

    if git_context:
        parts.append(git_context)
    else:
        parts.append("*(no git activity available)*")

    parts.append("""
---

## Session Transcript
""")
    parts.append("```json")
    parts.append(json.dumps(entries, indent=2, ensure_ascii=False))
    parts.append("```")

    # Scan project for frontmatter'd docs
    doc_index = scan_project_frontmatter(project_dir)

    parts.append("""

## Job 4: Docs

Docs are the project's **long-term memory** — reference material that stays useful for weeks or months. Any `.md` file with `summary` and `read_when` frontmatter is in scope.

### What belongs in docs

- Architecture decisions and design rationale
- Integration guides (setup, configuration, usage)
- Debugging discoveries (non-obvious behavior, sharp edges)
- Patterns and conventions specific to this project
- Gotchas and pitfalls that future agents will hit
- Guides for future agents (how to do common tasks in this codebase)

### What does NOT belong in docs

- Current project status (→ WORKSPACE.md)
- In-progress work tracking (→ WORKSPACE.md)
- Session-specific notes (→ WORKSPACE.md or discard)
- Things that will be irrelevant in 2 weeks (→ WORKSPACE.md)

### Existing Docs
""")
    parts.append(doc_index if doc_index else "No frontmatter'd docs found in the project.")

    if assistant_mode:
        docs_rules = """### Rules

**Create** new files anywhere in the project following existing directory conventions. Infer the right location from existing file paths (e.g., daily logs next to other daily logs, people files next to other people files). Every new file must have frontmatter with `summary` and `read_when`.

**Update** any existing frontmatter'd doc (listed above) when this session changed what it describes. Read the existing doc first, then rewrite with current accurate content.

**Delete** outdated or superseded files. To mark for deletion, append the relative path to `{state_path(project_dir, "docs-to-delete")}` (one path per line). Python will handle the actual file deletion. Never delete core identity or configuration files."""
    else:
        docs_rules = """### Rules

**Create** new docs in `.meridian/docs/` when this session produced long-term knowledge (see "What belongs in docs" above). Use kebab-case filenames. Skip routine fixes and obvious information.

**Update** any existing frontmatter'd doc (listed above) when this session changed what it describes. Read the existing doc first, then rewrite with current accurate content. This includes files outside `.meridian/docs/` like IDENTITY.md or SOUL.md.

**Delete** only `.meridian/docs/` files — never delete docs outside that directory. To mark for deletion, append the relative path to `{state_path(project_dir, "docs-to-delete")}` (e.g. `.meridian/docs/old-auth.md`), one path per line. Python will handle the actual file deletion after you finish."""

    parts.append(f"""

### Frontmatter Format

Every `.md` file you create or update MUST start with YAML frontmatter. Files without frontmatter are invisible to context routers — the agent will never see them.

```
---
summary: One-line description of what this doc covers
read_when:
  - keyword or phrase that would make this doc relevant
  - another keyword
---
```

If an existing file is missing frontmatter, add it.

{docs_rules}

---

## Execute

Do all four jobs. If nothing worth preserving for a job, skip it.

Use the Write tool (or Read then Edit) to update files.""")

    return "\n".join(parts)


def acquire_lock(project_dir: Path) -> bool:
    """Try to acquire the workspace sync lock. Returns True if acquired."""
    lock_path = state_path(project_dir, WORKSPACE_SYNC_LOCK)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        # Check if lock is stale (older than 5 minutes)
        try:
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
        state_path(project_dir, WORKSPACE_SYNC_LOCK).unlink(missing_ok=True)
    except OSError:
        pass


def was_recently_synced(project_dir: Path) -> bool:
    """Check if workspace was synced in the last 30 seconds (dedup for /clear)."""
    sync_path = state_path(project_dir, LAST_SYNC_FILE)
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
    sync_path = state_path(project_dir, LAST_SYNC_FILE)
    try:
        sync_path.parent.mkdir(parents=True, exist_ok=True)
        sync_path.write_text(str(time.time()))
    except IOError:
        pass


def cleanup_docs_to_delete(project_dir: Path):
    """Delete docs marked for deletion by the session learner agent."""
    delete_list_path = state_path(project_dir, "docs-to-delete")
    if not delete_list_path.exists():
        return

    try:
        paths = [p.strip() for p in delete_list_path.read_text().splitlines() if p.strip()]
        delete_list_path.unlink()
    except IOError:
        return

    deleted = []
    for rel_path in paths:
        target = project_dir / rel_path
        try:
            if target.exists() and target.is_file():
                target.unlink()
                deleted.append(rel_path)
        except OSError:
            pass

    if deleted:
        print(f"[Meridian] Deleted outdated docs: {', '.join(deleted)}", file=sys.stderr)



def parse_stream_json(stdout: str) -> tuple[list[dict], str]:
    """Parse stream-json output into (tools_used, text_output).

    tools_used: list of {"tool": "Write", "file": ".meridian/WORKSPACE.md"}
    text_output: concatenated text blocks for the human-readable output file
    """
    tools_used = []
    text_parts = []

    for line in stdout.strip().split('\n'):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Handle assistant messages with content blocks
        msg = entry.get("message", {})
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                btype = block.get("type", "")
                if btype == "tool_use":
                    tool_entry = {"tool": block.get("name", "unknown")}
                    input_data = block.get("input", {})
                    file_path = input_data.get("file_path") or input_data.get("path") or ""
                    if file_path:
                        tool_entry["file"] = file_path
                    tools_used.append(tool_entry)
                elif btype == "text":
                    text = block.get("text", "")
                    if text.strip():
                        text_parts.append(text)

        # Handle result entry
        if entry.get("type") == "result":
            result_text = entry.get("result", "")
            if result_text and isinstance(result_text, str):
                text_parts.append(result_text)

    return tools_used, "\n".join(text_parts)


def get_git_diff_after(project_dir: Path) -> tuple[list[str], str]:
    """Get changed files and diff stat after agent runs."""
    files_changed = []
    diff_stat = ""

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, timeout=5,
            cwd=str(project_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            files_changed = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, timeout=5,
            cwd=str(project_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            if lines:
                diff_stat = lines[-1].strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return files_changed, diff_stat


def log_learner_run(project_dir: Path, entry: dict):
    """Append a run entry to the JSONL log with rotation (keep last MAX_LOG_ENTRIES)."""
    log_path = state_path(project_dir, SESSION_LEARNER_LOG)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)

        existing = []
        if log_path.exists():
            for line in log_path.read_text().strip().split('\n'):
                if line.strip():
                    try:
                        existing.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        existing.append(entry)
        if len(existing) > MAX_LOG_ENTRIES:
            existing = existing[-MAX_LOG_ENTRIES:]

        log_path.write_text('\n'.join(json.dumps(e) for e in existing) + '\n')
    except (IOError, OSError):
        pass


def run_workspace_agent(prompt: str, project_dir: Path) -> dict:
    """Run headless claude -p to update workspace.

    Returns dict with: success, exit_code, tools_used, text_output
    """
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    run_info = {"success": False, "exit_code": -1, "tools_used": [], "text_output": ""}

    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", "claude-opus-4-6",
                "--output-format", "stream-json",
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
        run_info["exit_code"] = result.returncode

        # Parse stream-json output for tool usage and text
        tools_used, text_output = parse_stream_json(result.stdout or "")
        run_info["tools_used"] = tools_used
        run_info["text_output"] = text_output

        # Save human-readable agent output for inspection
        output_path = state_path(project_dir, "session-learner-output.md")
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            header = f"# Session Learner Output\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n**Exit code:** {result.returncode}\n\n---\n\n"
            output_path.write_text(header + (text_output or "*(no output)*") + "\n")
        except (IOError, OSError):
            pass

        if result.returncode != 0:
            print(f"[Meridian] Workspace agent exited with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"[Meridian] {result.stderr[:500]}", file=sys.stderr)
            return run_info

        run_info["success"] = True
        return run_info
    except subprocess.TimeoutExpired:
        print("[Meridian] Workspace agent timed out (180s)", file=sys.stderr)
        run_info["exit_code"] = -2
        return run_info
    except FileNotFoundError:
        print("[Meridian] claude CLI not found", file=sys.stderr)
        run_info["exit_code"] = -3
        return run_info


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
            saved_path = state_path(project_dir, TRANSCRIPT_PATH_STATE)
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

        # Load workspace, config, and git context
        workspace_root = load_workspace(project_dir)
        git_context = gather_git_context(project_dir)
        config = get_project_config(project_dir)
        learner_mode = config.get('session_learner_mode', 'project')

        # Build prompt and run agent
        prompt = build_prompt(entries, workspace_root, git_context, project_dir, mode=learner_mode)

        # Save prompt for inspection
        try:
            prompt_path = state_path(project_dir, "session-learner-prompt.md")
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(prompt)
        except (IOError, OSError):
            pass

        print("[Meridian] Updating workspace from session transcript...", file=sys.stderr)
        start_time = time.time()
        run_info = run_workspace_agent(prompt, project_dir)
        duration = time.time() - start_time

        # Capture git diff after agent runs
        files_changed, diff_stat = get_git_diff_after(project_dir)

        # Log to JSONL
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "trigger": source if source else "end",
            "transcript_entries": len(entries),
            "meaningful_entries": len(meaningful),
            "duration_seconds": round(duration, 1),
            "exit_code": run_info["exit_code"],
            "success": run_info["success"],
            "tools_used": run_info["tools_used"],
            "files_changed": files_changed,
            "diff_stat": diff_stat,
        }
        log_learner_run(project_dir, log_entry)

        if run_info["success"]:
            tool_count = len(run_info["tools_used"])
            print(f"[Meridian] Workspace updated ({duration:.0f}s, {tool_count} tools).", file=sys.stderr)
            cleanup_docs_to_delete(project_dir)
            mark_synced(project_dir)
        else:
            print(f"[Meridian] Workspace update failed ({duration:.0f}s).", file=sys.stderr)

    finally:
        if lock_acquired:
            release_lock(project_dir)

    sys.exit(0)


if __name__ == "__main__":
    main()

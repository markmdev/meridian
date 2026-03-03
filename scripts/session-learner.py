#!/usr/bin/env python3
"""
Session Learner — SessionEnd Hook

Extracts session transcript and spawns a headless Claude session to:
1. Update the workspace — maintain WORKSPACE.md as a slim current-state notepad
2. Learn from corrections — save user corrections as permanent CLAUDE.md instructions
3. Maintain docs — create/update long-term reference docs
"""

import json
import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import WORKSPACE_FILE, scan_project_frontmatter, get_project_config, state_path, is_system_noise, is_headless
import claude_runner

if is_headless():
    sys.exit(0)

WORKSPACE_SYNC_LOCK = "workspace-sync.lock"
SESSION_LEARNER_LOG = "session-learner.jsonl"
SESSION_LEARNER_DEBUG_LOG = "session-learner.log"
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


def get_extraction_range(transcript_path: str) -> tuple[int, int]:
    """Determine start/end lines for extraction (everything since last compact boundary)."""
    boundaries = find_compact_boundaries(transcript_path)
    total = count_lines(transcript_path)

    if boundaries:
        return boundaries[-1], total
    return 0, total


def extract_transcript(transcript_path: str, start_line: int, end_line: int) -> list[dict]:
    """Extract meaningful entries from transcript range. No truncation — full content preserved."""
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
                if is_system_noise(content):
                    continue
                entries.append({"type": "user", "text": content})

            # User text from content blocks (non-tool-result)
            elif entry_type == "user" and role == "user" and isinstance(content, list):
                # Skip tool_result blocks
                if any(b.get("type") == "tool_result" for b in content):
                    continue
                for block in content:
                    if block.get("type") == "text" and block.get("text", "").strip():
                        text = block["text"]
                        if is_system_noise(text):
                            continue
                        entries.append({"type": "user", "text": text})

            # Assistant messages (skip thinking blocks)
            elif entry_type == "assistant" and role == "assistant" and isinstance(content, list):
                for block in content:
                    btype = block.get("type", "")
                    if btype == "text" and block.get("text", "").strip():
                        entries.append({"type": "assistant", "text": block["text"]})
                    elif btype == "tool_use":
                        tool_entry = {"type": "tool_use", "tool": block.get("name", "unknown")}
                        if isinstance(block.get("input"), dict):
                            tool_entry["input"] = block["input"]
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

    if assistant_mode:
        job4_desc = "Maintain docs — create, update, or delete files across the workspace"
        doc_location = "anywhere in the project following existing directory conventions"
    else:
        job4_desc = "Maintain docs — create/update long-term reference docs in `.meridian/docs/`"
        doc_location = "`.meridian/docs/`"

    delete_list_path = str(state_path(project_dir, "docs-to-delete"))

    if assistant_mode:
        docs_create = f"**Create** new files {doc_location}. Infer the right location from existing file paths (e.g., daily logs next to other daily logs, people files next to other people files). Every new file must have frontmatter with `summary` and `read_when`."
        docs_update = "**Update** any existing frontmatter'd doc when this session changed what it describes. Read the existing doc first, then rewrite with current accurate content."
        docs_delete = f"**Delete** outdated or superseded files. To mark for deletion, append the relative path to `{delete_list_path}` (one path per line). Python will handle the actual file deletion. Never delete core identity or configuration files."
    else:
        docs_create = f"**Create** new docs in {doc_location} when this session produced long-term knowledge. Use kebab-case filenames. Skip routine fixes and obvious information."
        docs_update = "**Update** any existing frontmatter'd doc when this session changed what it describes. Read the existing doc first, then rewrite with current accurate content. This includes files outside `.meridian/docs/` like IDENTITY.md or SOUL.md."
        docs_delete = f"**Delete** only `.meridian/docs/` files — never delete docs outside that directory. To mark for deletion, append the relative path to `{delete_list_path}` (e.g. `.meridian/docs/old-auth.md`), one path per line. Python will handle the actual file deletion after you finish."

    # Scan project for frontmatter'd docs
    doc_index = scan_project_frontmatter(project_dir)

    transcript_json = json.dumps(entries, indent=2, ensure_ascii=False)

    prompt = f"""<role>
You are a session maintenance agent. You have three jobs:
1. Update the workspace — maintain WORKSPACE.md as a slim current-state notepad
2. Learn from corrections — when the user corrects the agent, save it as a permanent instruction
3. {job4_desc}

Do all three jobs. If nothing worth preserving for a job, skip it.
Use the Write tool (or Read then Edit) to update files.
</role>

<job id="workspace">
<instructions>
WORKSPACE.md is a slim current-state notepad — what's actively being worked on, key recent decisions, and what to do next. It is NOT an encyclopedia of architecture, tech stack summaries, hook behavior, or implementation details. Those belong in docs.
</instructions>

<current-workspace>
{workspace_root if workspace_root.strip() else "(empty — create it)"}
</current-workspace>

<structure>
Each project gets a section with these subsections (use only what's needed):

### Project Name
One-line description.
**In Progress:** active work items
**Known Issues:** current bugs or blockers
**Key Decisions:** recent decisions that affect upcoming work (remove after 2-3 sessions)
**Next Steps:**
1. Immediate item for next session
</structure>

<rules>
- This is a notepad, not documentation. Keep entries short — a few words per item, not paragraphs.
- No architecture descriptions, tech stack summaries, implementation docs, or hook behavior details. Those belong in `.meridian/docs/` or project knowledge files.
- No "Completed" sections. Once work is done and has no bearing on next steps, remove it.
- No timestamps, no "in this session" phrasing, no session logs.
- Remove information that's no longer relevant — resolved issues, superseded decisions, completed work.
- If information will be useful for more than 2 weeks, write a doc file, not a workspace entry.
- **Next Steps** rules: only immediate work for the next 1-2 sessions. No "someday" items, no roadmap, no future improvements mentioned in passing. Include enough context that a fresh agent can act without reading the full workspace. Replace previous next steps entirely.
- A global **## Next Steps** section at the bottom covers cross-project items.
</rules>
</job>

<job id="corrections">
<instructions>
Scan the transcript for moments where the user corrects the agent's behavior, expresses a preference, or teaches something that should apply going forward. Save these as permanent instructions in the appropriate CLAUDE.md file.
</instructions>

<current-claudemd>
<file path="{global_claudemd_path}">
{global_claudemd if global_claudemd.strip() else "(empty)"}
</file>

<file path="{project_claudemd_path}">
{project_claudemd if project_claudemd.strip() else "(empty)"}
</file>
</current-claudemd>

<rules>
- Write as the user giving instructions to an agent. Direct, imperative voice.
- Global (`{global_claudemd_path}`): preferences that apply to all projects.
- Project (`{project_claudemd_path}`): instructions specific to this codebase.
- Don't duplicate instructions already present in either file.
- Don't add one-time fixes or task-specific instructions. Only lasting preferences.
- Append new entries. Don't rewrite or reorganize existing content.
- If no corrections or preferences were expressed, don't touch the CLAUDE.md files.
</rules>
</job>

<job id="docs">
<instructions>
Docs are the project's long-term memory — reference material that stays useful for weeks or months. Any `.md` file with `summary` and `read_when` frontmatter is in scope.

What belongs: architecture decisions, integration guides, debugging discoveries, patterns, gotchas, guides for future agents.
What does NOT belong: current status (WORKSPACE.md), in-progress tracking, session-specific notes, things irrelevant in 2 weeks.
</instructions>

<existing-docs>
{doc_index if doc_index else "No frontmatter'd docs found in the project."}
</existing-docs>

<rules>
- {docs_create}
- {docs_update}
- {docs_delete}
- Every `.md` file you create or update MUST start with YAML frontmatter:
  ---
  summary: One-line description
  read_when:
    - keyword or phrase
  ---
- Files without frontmatter are invisible to context routers.
</rules>
</job>

<context id="git-activity">
{git_context if git_context else "(no git activity available)"}
</context>

<context id="transcript">
{transcript_json}
</context>"""

    return prompt


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
        log(project_dir, f"deleted docs: {', '.join(deleted)}")



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


def log_skip(project_dir: Path, reason: str, **extra):
    """Log an early-exit skip to the JSONL session-learner log."""
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "skipped": True,
        "reason": reason,
        **extra,
    }
    log_learner_run(project_dir, entry)


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
    env = claude_runner.build_env()
    args = claude_runner.build_args()
    result = claude_runner.run(prompt, args=args, env=env, cwd=str(project_dir), timeout=180)

    run_info = {
        "success": result["success"],
        "exit_code": result["exit_code"],
        "tools_used": [],
        "text_output": "",
    }

    # Log stderr for debugging
    if result["stderr"]:
        log(project_dir, f"claude stderr: {result['stderr'][:300]}")

    # Parse stream-json output for tool usage and text
    if result["stdout"]:
        tools_used, text_output = claude_runner.parse_stream_json(result["stdout"])
        run_info["tools_used"] = tools_used
        run_info["text_output"] = text_output

    # Save human-readable agent output for inspection
    output_path = state_path(project_dir, "session-learner-output.md")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        header = f"# Session Learner Output\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n**Exit code:** {result['exit_code']}\n\n---\n\n"
        output_path.write_text(header + (run_info["text_output"] or "*(no output)*") + "\n")
    except (IOError, OSError):
        pass

    if not result["success"]:
        log(project_dir, f"claude exited with code {result['exit_code']}")
        # Log last few lines of stdout for diagnosis
        stdout_lines = result["stdout"].strip().split('\n')
        for line in stdout_lines[-3:]:
            log(project_dir, f"  stdout: {line[:300]}")

    return run_info


def log(project_dir: Path, message: str):
    """Append a debug line to the session-learner log."""
    log_path = state_path(project_dir, SESSION_LEARNER_DEBUG_LOG)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(log_path, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except (IOError, OSError):
        pass


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    hook_event = input_data.get("hook_event_name", "")
    transcript_path = input_data.get("transcript_path", "")

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))

    log(project_dir, f"START event={hook_event} transcript={Path(transcript_path).name if transcript_path else 'none'}")

    # Only handle SessionEnd
    if hook_event != "SessionEnd":
        log(project_dir, f"SKIP wrong event: {hook_event}")
        log_skip(project_dir, "wrong_event", hook_event=hook_event)
        sys.exit(0)

    lock_acquired = False
    try:
        if not transcript_path or not Path(transcript_path).exists():
            log(project_dir, f"SKIP no transcript (path={'empty' if not transcript_path else 'file missing'})")
            log_skip(project_dir, "no_transcript")
            return

        if not acquire_lock(project_dir):
            log(project_dir, "SKIP lock held by another run")
            log_skip(project_dir, "lock_held")
            return
        lock_acquired = True
        log(project_dir, "lock acquired")

        # Extract transcript
        start_line, end_line = get_extraction_range(transcript_path)
        entries = extract_transcript(transcript_path, start_line, end_line)

        # Skip if too few meaningful entries
        meaningful = [e for e in entries if e["type"] in ("user", "assistant")]
        log(project_dir, f"extracted entries={len(entries)} meaningful={len(meaningful)}")
        if len(meaningful) < MIN_ENTRIES_THRESHOLD:
            log(project_dir, f"SKIP below threshold ({len(meaningful)} < {MIN_ENTRIES_THRESHOLD})")
            log_skip(project_dir, "below_threshold", entries=len(meaningful))
            return

        # Load workspace, config, and git context
        workspace_root = load_workspace(project_dir)
        git_context = gather_git_context(project_dir)
        config = get_project_config(project_dir)
        learner_mode = config.get('session_learner_mode', 'project')

        # Build prompt and run agent
        prompt = build_prompt(entries, workspace_root, git_context, project_dir, mode=learner_mode)
        log(project_dir, f"prompt built chars={len(prompt)} mode={learner_mode}")

        # Save prompt for inspection
        try:
            prompt_path = state_path(project_dir, "session-learner-prompt.md")
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(prompt)
        except (IOError, OSError):
            pass

        log(project_dir, "calling claude -p...")
        start_time = time.time()
        run_info = run_workspace_agent(prompt, project_dir)
        duration = time.time() - start_time
        log(project_dir, f"claude -p done exit_code={run_info['exit_code']} duration={duration:.0f}s tools={len(run_info['tools_used'])}")

        # Capture git diff after agent runs
        files_changed, diff_stat = get_git_diff_after(project_dir)

        # Log to JSONL
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "trigger": "end",
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
            log(project_dir, f"DONE tools={tool_count} files_changed={files_changed}")
            cleanup_docs_to_delete(project_dir)
        else:
            log(project_dir, f"FAILED exit_code={run_info['exit_code']}")

    finally:
        if lock_acquired:
            release_lock(project_dir)
            log(project_dir, "lock released")

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Last-resort logging — write to state dir if possible
        try:
            project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
            log(project_dir, f"CRASH {type(e).__name__}: {e}")
        except Exception:
            pass
        raise

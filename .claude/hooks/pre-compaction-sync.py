#!/usr/bin/env python3
"""
Pre-Compaction Context Sync Hook

Prompts agent to save context before conversation compacts (based on token usage).
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    get_project_config,
    flag_exists,
    create_flag,
    PRE_COMPACTION_FLAG,
    WORKTREE_CONTEXT_FILE,
    PLAN_MODE_STATE,
    get_main_worktree_path,
    get_worktree_name,
)

LOG_FILE = ".meridian/.pre-compaction-sync.log"


def log_calculation(base_dir: Path, request_id: str, usage: dict, total: int,
                    threshold: int, triggered: bool, error: str = None) -> None:
    """Append a log entry for debugging token calculations."""
    log_path = base_dir / LOG_FILE
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {
            "timestamp": timestamp,
            "request_id": request_id,
            "usage": usage,
            "total_calculated": total,
            "threshold": threshold,
            "triggered": triggered,
        }
        if error:
            entry["error"] = error
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Don't fail the hook if logging fails


def get_total_tokens(transcript_path: str, base_dir: Path, threshold: int) -> int:
    """Read the transcript and find the most recent entry with usage data."""
    if not transcript_path:
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, "no transcript_path")
        return 0

    path = Path(transcript_path)
    if not path.exists():
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, f"transcript not found: {transcript_path}")
        return 0

    try:
        # Read all lines and search backwards for one with usage data
        lines = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    lines.append(line.strip())

        if not lines:
            log_calculation(base_dir, "N/A", {}, 0, threshold, False, "empty transcript")
            return 0

        # Search backwards for an entry with message.usage
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                usage = entry.get("message", {}).get("usage", {})
                if usage:  # Found an entry with usage data
                    request_id = entry.get("requestId", "unknown")
                    total = 0
                    total += usage.get("input_tokens", 0)
                    total += usage.get("cache_creation_input_tokens", 0)
                    total += usage.get("cache_read_input_tokens", 0)
                    total += usage.get("output_tokens", 0)

                    triggered = total >= threshold
                    log_calculation(base_dir, request_id, usage, total, threshold, triggered)
                    return total
            except json.JSONDecodeError:
                continue

        # No entry with usage found
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, "no entry with usage data found")
        return 0
    except IOError as e:
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, f"read error: {type(e).__name__}: {e}")
        return 0


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    if input_data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)  # Can't operate without project dir
    base_dir = Path(claude_project_dir)

    # Check if enabled in config
    config = get_project_config(base_dir)
    if not config['pre_compaction_sync_enabled']:
        sys.exit(0)

    transcript_path = input_data.get("transcript_path", "")
    threshold = config['pre_compaction_sync_threshold']
    already_synced = flag_exists(base_dir, PRE_COMPACTION_FLAG)
    total_tokens = get_total_tokens(transcript_path, base_dir, threshold)

    # Already synced this session: allow (fires only once per session)
    if already_synced:
        sys.exit(0)

    # Under threshold: allow without creating flag
    if total_tokens < threshold:
        sys.exit(0)

    # Allow writes to .meridian or .claude folders (these ARE the context-saving actions)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    if tool_name in {"Write", "Edit"}:
        file_path = tool_input.get("file_path", "")
        if "/.meridian/" in file_path or "/.claude/" in file_path:
            sys.exit(0)  # Allow without blocking

    # Over threshold: create flag and block
    create_flag(base_dir, PRE_COMPACTION_FLAG)

    # Build reason message
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    reason = (
        f"**CONTEXT PRESERVATION REQUIRED** (Token usage: {total_tokens:,} / {threshold:,}) — Current time: {now}\n\n"
        "The conversation is approaching compaction. Before continuing, you MUST save your current work "
        "to preserve context for the agent that will continue after compaction.\n\n"
    )

    # Check if in plan mode
    plan_mode_file = base_dir / PLAN_MODE_STATE
    in_plan_mode = plan_mode_file.exists() and plan_mode_file.read_text().strip() == "plan"

    # Add PLAN STATE section FIRST (highest priority) - only when in plan mode
    if in_plan_mode:
        reason += (
            "**PLAN STATE** (HIGHEST PRIORITY — DO THIS FIRST):\n"
            "Update the plan file's **Verbatim Requirements** section at the TOP:\n"
            "- Capture the user's ENTIRE original request (word for word)\n"
            "- Capture ALL AskUserQuestion exchanges (questions AND answers, verbatim)\n"
            "- Capture all follow-up context from the user\n"
            "- DO NOT paraphrase. DO NOT compress. DO NOT summarize.\n"
            "- Everything the user said matters — paraphrasing loses nuance.\n\n"
        )

    # Add Pebble instructions if enabled
    if config.get('pebble_enabled', False):
        reason += (
            "**PEBBLE (AUDIT TRAIL)**: Every code change needs an issue — this is your audit trail.\n"
            "- **Already-fixed bugs**: If you discovered AND fixed a bug this session, create the issue NOW "
            "(issue → already fixed → comment what you did → close). The fix happened, but the record didn't.\n"
            "- Create issues for: bugs found, broken code, technical debt encountered, problems that need attention.\n"
            "- Close any issues you completed (with a comment).\n"
            "See `.meridian/PEBBLE_GUIDE.md` for commands.\n\n"
        )

    reason += (
        "**SESSION CONTEXT**: Update or append to:\n"
        f"`{claude_project_dir}/.meridian/session-context.md`\n\n"
        f"First, read recent entries: `tail -70 \"{claude_project_dir}/.meridian/session-context.md\"`\n\n"
        "**Update vs Append:**\n"
        "- If recent entry covers the SAME task/phase, UPDATE it (don't create another)\n"
        "- Only APPEND when starting genuinely new work\n\n"
        "**What to write:**\n"
        "- Current state + next action (not a changelog)\n"
        "- Non-obvious decisions: contradicts intuition, user preference, tradeoff, or pivot\n"
        "- Full absolute paths (e.g., `/path/to/project/src/file.py:42`)\n\n"
        "**What to skip:**\n"
        "- Task tables (use Pebble)\n"
        "- Self-evident reasoning (\"created helper because reuse\")\n"
        "- Incremental progress (consolidate into one entry)\n\n"
        "**Good:** \"Phase 8 complete. User requested inline warnings instead of toasts. Starting Phase 9 task olympus-wur6ex.\"\n"
        "**Bad:** Multiple entries for same phase, task status tables, obvious reasoning.\n\n"
    )

    # Worktree context section (always required)
    main_worktree = get_main_worktree_path(base_dir)
    worktree_root = main_worktree if main_worktree else base_dir
    worktree_name = get_worktree_name(base_dir) if main_worktree else None
    worktree_context_path = worktree_root / WORKTREE_CONTEXT_FILE
    if worktree_name:
        format_header = f"`## [{worktree_name}] YYYY-MM-DD HH:MM - Title`"
    else:
        format_header = "`## YYYY-MM-DD HH:MM - Title`"
    reason += (
        f"**WORKTREE CONTEXT**: Append a summary to:\n"
        f"`{worktree_context_path}`\n"
        f"First, check recent entries: `tail -50 \"{worktree_context_path}\"`\n"
        f"Format: {format_header}\n"
        "Start with what task/epic you were working on, then 2-3 sentences: "
        "what was done, any issues found, current state.\n\n"
    )

    # Check if auto_compact_off is enabled
    if config.get('auto_compact_off', False):
        reason += (
            "**STOP NOW.** After saving context, stop immediately and tell the user:\n"
            "\"Context saved. Please run /clear to start a new session.\"\n\n"
            "Do NOT continue working. The session will be manually cleared."
        )
    else:
        reason += "After updating, you may continue your work."

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

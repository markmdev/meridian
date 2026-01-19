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

    # Over threshold: create flag and block
    create_flag(base_dir, PRE_COMPACTION_FLAG)

    # Build reason message
    reason = (
        f"**CONTEXT PRESERVATION REQUIRED** (Token usage: {total_tokens:,} / {threshold:,})\n\n"
        "The conversation is approaching compaction. Before continuing, you MUST save your current work "
        "to preserve context for the agent that will continue after compaction.\n\n"
    )

    # Add Pebble instructions FIRST if enabled (higher priority)
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
        "**SESSION CONTEXT**: Append a dated entry to:\n"
        f"`{claude_project_dir}/.meridian/session-context.md`\n\n"
        "**What survives compaction well:**\n"
        "- Concrete decisions with rationale (\"chose X because Y\")\n"
        "- Specific file paths and line numbers\n"
        "- Error messages that took time to debug\n"
        "- Explicit next steps with full context\n"
        "- Assumptions you're making (stated clearly)\n\n"
        "**What does NOT survive well:**\n"
        "- Vague summaries (\"made good progress\")\n"
        "- References to \"the code we discussed\" without specifics\n"
        "- Implicit context that requires the full conversation\n"
        "- Progress updates without decisions\n\n"
        "Write as if briefing a new agent who has zero context.\n\n"
    )

    # Add worktree context section if in a git worktree
    main_worktree = get_main_worktree_path(base_dir)
    if main_worktree:
        worktree_name = get_worktree_name(base_dir)
        worktree_context_path = main_worktree / WORKTREE_CONTEXT_FILE
        reason += (
            f"**WORKTREE CONTEXT**: For significant work, also append a summary to:\n"
            f"`{worktree_context_path}`\n"
            f"Format: `## [{worktree_name}] YYYY-MM-DD HH:MM - Title`\n"
            "Start with what task/epic you were working on, then 2-3 sentences: "
            "what was done, any issues found, current state.\n\n"
        )

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

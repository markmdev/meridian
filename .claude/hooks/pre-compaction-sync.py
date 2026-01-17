#!/usr/bin/env python3
"""
Pre-Compaction Context Sync Hook

Prompts agent to save context before conversation compacts (based on token usage).
"""

import json
import sys
import os
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


def get_total_tokens(transcript_path: str) -> int:
    """Read the last entry from transcript and sum token usage."""
    if not transcript_path:
        return 0

    path = Path(transcript_path)
    if not path.exists():
        return 0

    try:
        # Read last line of JSONL file
        last_line = ""
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    last_line = line.strip()

        if not last_line:
            return 0

        entry = json.loads(last_line)
        usage = entry.get("message", {}).get("usage", {})

        # Sum token fields
        total = 0
        total += usage.get("input_tokens", 0)
        total += usage.get("cache_creation_input_tokens", 0)
        total += usage.get("cache_read_input_tokens", 0)
        total += usage.get("output_tokens", 0)

        return total
    except (json.JSONDecodeError, IOError, KeyError):
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
    total_tokens = get_total_tokens(transcript_path)

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
            f"**WORKTREE CONTEXT**: For significant work, also append a brief standup-style summary to:\n"
            f"`{worktree_context_path}`\n"
            f"Format: `## [{worktree_name}] YYYY-MM-DD - Title`\n"
            "Write 2-3 sentences max: what you worked on and what was achieved. "
            "No technical details — just outcomes.\n\n"
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

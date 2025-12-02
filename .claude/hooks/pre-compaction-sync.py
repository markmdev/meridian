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

        total = 0
        total += usage.get("input_tokens", 0)
        total += usage.get("cache_creation_input_tokens", 0)
        total += usage.get("cache_read_input_tokens", 0)
        total += usage.get("output_tokens", 0)

        cache_creation = usage.get("cache_creation", {})
        total += cache_creation.get("ephemeral_5m_input_tokens", 0)
        total += cache_creation.get("ephemeral_1h_input_tokens", 0)

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

    cwd = input_data.get("cwd", os.getcwd())
    base_dir = Path(cwd)

    # Check if enabled in config
    config = get_project_config(base_dir)
    if not config['pre_compaction_sync_enabled']:
        sys.exit(0)

    # If already synced this session, allow
    if flag_exists(base_dir, PRE_COMPACTION_FLAG):
        sys.exit(0)

    # Get transcript path and check token usage
    transcript_path = input_data.get("transcript_path", "")
    total_tokens = get_total_tokens(transcript_path)
    threshold = config['pre_compaction_sync_threshold']

    # Under threshold, allow
    if total_tokens < threshold:
        sys.exit(0)

    # Over threshold: create flag and block
    create_flag(base_dir, PRE_COMPACTION_FLAG)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", cwd)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"**CONTEXT PRESERVATION REQUIRED** (Token usage: {total_tokens:,} / {threshold:,})\n\n"
                "The conversation is approaching compaction. Before continuing, you MUST save your current work "
                "to preserve context for the agent that will continue after compaction.\n\n"
                "**Write to the task context file:**\n"
                f"`{claude_project_dir}/.meridian/tasks/TASK-###/TASK-###-context.md`\n\n"
                "Include:\n"
                "- Current implementation step and progress\n"
                "- Key decisions made this session and their rationale\n"
                "- Issues discovered or blockers encountered\n"
                "- What needs to be done next\n"
                "- Any important information that would be difficult to rediscover\n\n"
                "After updating the context file, you may continue your work."
            )
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Context Acknowledgment Guard - PreToolUse Hook

Blocks the first tool call after session start to ensure the agent
acknowledges the injected project context before proceeding.
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import (
    flag_exists,
    cleanup_flag,
    log_hook_output,
    CONTEXT_ACK_FLAG,
)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if input_data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)  # Can't operate without project dir
    base_dir = Path(claude_project_dir)

    # No acknowledgment flag = allow everything
    if not flag_exists(base_dir, CONTEXT_ACK_FLAG):
        sys.exit(0)

    # Flag exists - block and ask for acknowledgment, then remove flag
    cleanup_flag(base_dir, CONTEXT_ACK_FLAG)

    reason = (
        "**CONTEXT ACKNOWLEDGMENT REQUIRED**\n\n"
        "Project context has been injected into this session. "
        "Before using any tools, acknowledge what you see — "
        "briefly state what you understand about the current project state.\n\n"
        "**IMPORTANT**: After acknowledging, you MUST retry the same action that was just blocked. "
        "Do not skip it or move on to something else."
    )

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }

    log_hook_output(base_dir, "context-acknowledgment-gate", output)
    sys.exit(0)


if __name__ == "__main__":
    main()

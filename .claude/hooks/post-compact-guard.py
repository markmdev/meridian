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
from config import (
    flag_exists,
    cleanup_flag,
    CONTEXT_ACK_FLAG,
)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    if input_data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)

    cwd = input_data.get("cwd", os.getcwd())
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", cwd)
    base_dir = Path(claude_project_dir)

    # No acknowledgment flag = allow everything
    if not flag_exists(base_dir, CONTEXT_ACK_FLAG):
        sys.exit(0)

    # Flag exists - block and ask for acknowledgment, then remove flag
    cleanup_flag(base_dir, CONTEXT_ACK_FLAG)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "**CONTEXT ACKNOWLEDGMENT REQUIRED**\n\n"
                "Project context has been injected into this session. "
                "Before using any tools, please acknowledge that you have read and understood:\n\n"
                "1. The **memory entries** (past decisions and lessons learned)\n"
                "2. Any **in-progress tasks** and their current state\n"
                "3. The **CODE_GUIDE** conventions for this project\n"
                "4. The **agent-operating-manual** instructions\n\n"
                "Briefly summarize what you understand about the current project state, "
                "then ask the user what they'd like to work on."
            )
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

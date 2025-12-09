#!/usr/bin/env python3
"""
Plan Review Hook - PreToolUse ExitPlanMode

Requires plan-reviewer agent before exiting plan mode (configurable).
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    get_project_config,
    get_additional_review_files,
    flag_exists,
    create_flag,
    cleanup_flag,
    PLAN_REVIEW_FLAG,
)

REQUIRED_SCORE = 9


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")
    cwd = input_data.get("cwd", os.getcwd())
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", cwd)
    base_dir = Path(claude_project_dir)

    # Only handle PreToolUse ExitPlanMode
    if hook_event != "PreToolUse" or tool_name != "ExitPlanMode":
        sys.exit(0)

    # Check if enabled in config
    config = get_project_config(base_dir)
    if not config['plan_review_enabled']:
        sys.exit(0)

    # If flag exists: delete and allow (already reviewed)
    if flag_exists(base_dir, PLAN_REVIEW_FLAG):
        cleanup_flag(base_dir, PLAN_REVIEW_FLAG)
        sys.exit(0)

    # Flag doesn't exist: create and block
    create_flag(base_dir, PLAN_REVIEW_FLAG)

    files_list = '\n'.join(get_additional_review_files(base_dir, absolute=True))

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Cannot exit plan mode without plan review.\n\n"
                "Please call the plan-reviewer agent with EXACTLY this prompt:\n\n"
                "---\n"
                f"Plan: {{PLAN_FILE_PATH}}\n"
                f"Additional files to read:\n{files_list}\n"
                "---\n\n"
                "Replace {PLAN_FILE_PATH} with the actual path to your plan file.\n\n"
                f"**ITERATION REQUIRED**: The plan must achieve a score of {REQUIRED_SCORE}+ to proceed.\n"
                f"If the score is below {REQUIRED_SCORE}, you must:\n"
                "1. Review each finding with the user using AskUserQuestion\n"
                "2. For findings the user wants to address: update the plan\n"
                "3. For findings the user declines: mark in plan as `[USER_DECLINED: <finding> - Reason: <reason>]`\n"
                "4. Call plan-reviewer again with the updated plan\n"
                f"5. Repeat until score reaches {REQUIRED_SCORE}+\n"
            )
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Plan Review Hook - PreToolUse ExitPlanMode

Requires plan-reviewer agent before exiting plan mode (configurable).
Skips enforcement for lightweight plans (fewer than plan_review_min_actions).
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import (
    get_project_config,
    get_additional_review_files,
    flag_exists,
    create_flag,
    get_plan_action_counter,
    log_hook_output,
    PLAN_REVIEW_FLAG,
)

REQUIRED_SCORE = 9


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)  # Can't operate without project dir
    base_dir = Path(claude_project_dir)

    # Only handle PreToolUse ExitPlanMode
    if hook_event != "PreToolUse" or tool_name != "ExitPlanMode":
        sys.exit(0)

    # Check if enabled in config
    config = get_project_config(base_dir)
    if not config['plan_review_enabled']:
        sys.exit(0)

    # Check if this is a lightweight plan (fewer actions than threshold)
    min_actions = config.get('plan_review_min_actions', 20)
    plan_actions = get_plan_action_counter(base_dir)
    if plan_actions < min_actions:
        # Lightweight plan - skip enforcement
        sys.exit(0)

    # If flag exists: allow (plan-approval-reminder will clear it after PostToolUse)
    if flag_exists(base_dir, PLAN_REVIEW_FLAG):
        sys.exit(0)

    # Flag doesn't exist: create and block (first attempt to exit plan mode)
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
                f"5. Repeat until score reaches {REQUIRED_SCORE}+\n\n"
                f"**IMPORTANT**: Even if score is {REQUIRED_SCORE}+, you MUST address ALL findings before exiting:\n"
                "1. Present each finding to the user (grouped by severity)\n"
                "2. For each finding, either:\n"
                "   - Update the plan to address it, OR\n"
                "   - Get user confirmation to skip (mark as `[USER_DECLINED: <finding> - Reason: <reason>]`)\n"
                f"3. You do NOT need to re-run the reviewer after addressing findings if score was already {REQUIRED_SCORE}+\n"
            )
        }
    }

    log_hook_output(base_dir, "plan-review", output)
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Plan Approval Reminder Hook - PostToolUse ExitPlanMode

Clears plan-review-blocked flag and reminds Claude to create Pebble issues after plan is approved.
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import get_project_config, cleanup_flag, clear_plan_action_counter, log_hook_output, state_path, PLAN_REVIEW_FLAG, ACTIVE_PLAN_FILE


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    if tool_name != "ExitPlanMode":
        sys.exit(0)

    if not claude_project_dir:
        sys.exit(0)

    base_dir = Path(claude_project_dir)

    # Clear state files (ExitPlanMode succeeded = plan approved)
    cleanup_flag(base_dir, PLAN_REVIEW_FLAG)
    clear_plan_action_counter(base_dir)

    config = get_project_config(base_dir)
    pebble_enabled = config.get('pebble_enabled', False)

    # Build plan management instructions (always runs)
    plan_instructions = (
        f"[SYSTEM]: Plan approved. **Archive the plan to the project folder:**\n\n"
        f"1. **Copy and rename the plan** — pick a descriptive kebab-case name based on the plan content:\n"
        f"   ```bash\n"
        f"   mkdir -p .meridian/plans && cp ~/.claude/plans/[slug].md .meridian/plans/descriptive-name.md\n"
        f"   ```\n"
        f"   Examples: `add-user-auth.md`, `refactor-payment-api.md`, `fix-race-condition.md`\n\n"
        f"2. **Update active plan tracking** (use ABSOLUTE path to the renamed file):\n"
        f"   - Write the absolute plan path to `{state_path(base_dir, ACTIVE_PLAN_FILE)}`\n\n"
    )

    # Add Pebble scaffolder instructions if enabled
    if pebble_enabled:
        plan_instructions += (
            f"3. **Invoke the `pebble-scaffolder` agent** to document the work.\n\n"
            f"- Scope: `task`, `bug`, or `follow-up`\n"
            f"- Parent: epic ID if part of larger work, otherwise none\n\n"
            f"Skip scaffolder only for trivial 5-minute fixes."
        )

    reason = plan_instructions

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": reason
        }
    }
    log_hook_output(Path(claude_project_dir), "plan-approval-reminder", output)
    sys.exit(0)


if __name__ == "__main__":
    main()

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
from config import get_project_config, cleanup_flag, clear_plan_action_counter, PLAN_REVIEW_FLAG


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    if tool_name != "ExitPlanMode":
        sys.exit(0)

    # Clear state files (ExitPlanMode succeeded = plan approved)
    if claude_project_dir:
        base_dir = Path(claude_project_dir)
        cleanup_flag(base_dir, PLAN_REVIEW_FLAG)
        clear_plan_action_counter(base_dir)

    # Check if Pebble and scaffolder are enabled
    if not claude_project_dir:
        sys.exit(0)

    config = get_project_config(Path(claude_project_dir))
    pebble_enabled = config.get('pebble_enabled', False)
    scaffolder_enabled = config.get('pebble_scaffolder_enabled', True)

    # Build plan management instructions (always runs)
    plan_instructions = (
        f"[SYSTEM]: Plan approved. **Archive the plan to the project folder:**\n\n"
        f"1. **Copy the plan** from `~/.claude/plans/[name].md` to:\n"
        f"   - `.meridian/plans/[name].md` for regular or epic plans\n"
        f"   - `.meridian/subplans/[name].md` if this is a subplan for an epic phase\n"
        f"   Create the directory if it doesn't exist.\n\n"
        f"2. **Update active plan tracking** (use ABSOLUTE paths):\n"
        f"   - Write the absolute plan path to `.meridian/.state/active-plan`\n"
        f"   - If this is a subplan, also write the absolute path to `.meridian/.state/active-subplan`\n\n"
        f"3. **Clear the global plan file** (`~/.claude/plans/[name].md`) — content is now in project.\n\n"
    )

    # Add Pebble scaffolder instructions if enabled
    if pebble_enabled and scaffolder_enabled:
        plan_instructions += (
            f"4. **Invoke the `pebble-scaffolder` agent** to document the work.\n\n"
            f"Pass the agent:\n"
            f"- **Plan file path** — the archived plan path (`.meridian/plans/...`)\n"
            f"- **Scope hint** — `epic`, `task`, `bug`, or `follow-up`\n"
            f"- **Parent context** (optional) — existing epic/issue ID if related\n\n"
            f"Skip scaffolder only for trivial 5-minute fixes."
        )

    reason = plan_instructions

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": reason
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

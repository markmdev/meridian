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

    if not pebble_enabled or not scaffolder_enabled:
        sys.exit(0)

    reason = (
        f"[SYSTEM]: Plan approved. **Invoke the `pebble-scaffolder` agent** to document the work.\n\n"
        f"Pass the agent:\n"
        f"1. **Plan file path** — the plan you just created\n"
        f"2. **Scope hint** — assess the work and choose:\n"
        f"   - `epic` — large multi-phase work (multiple distinct phases/modules)\n"
        f"   - `task` — focused work (single feature, refactor, or enhancement)\n"
        f"   - `bug` — fix for a discovered issue\n"
        f"   - `follow-up` — continuation of previous work (pass parent issue ID)\n"
        f"3. **Parent context** (optional) — existing epic/issue ID if this relates to prior work\n\n"
        f"The scaffolder will create the appropriate structure based on scope.\n"
        f"Skip only for trivial 5-minute fixes that don't need tracking."
    )

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

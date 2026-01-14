#!/usr/bin/env python3
"""
Plan Approval Reminder Hook - PostToolUse ExitPlanMode

Reminds Claude to create Pebble issues after plan is approved.
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import get_project_config


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    if tool_name != "ExitPlanMode":
        sys.exit(0)

    # Check if Pebble is enabled
    pebble_enabled = False
    if claude_project_dir:
        config = get_project_config(Path(claude_project_dir))
        pebble_enabled = config.get('pebble_enabled', False)

    if not pebble_enabled:
        # No task tracking - just proceed
        sys.exit(0)

    reason = (
        f"[SYSTEM]: If the user has approved the plan, **invoke the `pebble-scaffolder` agent** "
        f"with the plan file path to create the Pebble issue hierarchy.\n\n"
        f"The agent will create:\n"
        f"- Epic for the overall plan\n"
        f"- Task per phase\n"
        f"- Verification subtask per feature\n"
        f"- Dependencies between sequential phases\n\n"
        f"Skip only for trivial changes that don't need tracking."
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

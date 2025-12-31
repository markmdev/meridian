#!/usr/bin/env python3
"""
Plan Approval Reminder Hook - PostToolUse ExitPlanMode

Reminds Claude to create a task after plan is approved.
"""

import json
import sys
import os


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    if tool_name == "ExitPlanMode":
        output = {
            "decision": "block",
            "reason": (
                f"[SYSTEM]: If the user has approved the plan, complete ALL steps below:\n\n"
                f"1. **Create task folder**: Run `python3 .claude/skills/task-manager/scripts/create-task.py`\n"
                f"   This creates `.meridian/tasks/TASK-###-xxxx/` and prints the task ID.\n\n"
                f"2. **Copy plan to task folder**: Copy the plan file to the new task folder:\n"
                f"   `cp <plan_file_path> {claude_project_dir}/.meridian/tasks/TASK-###-xxxx/plan.md`\n\n"
                f"3. **Add entry to task-backlog.yaml**: Edit `{claude_project_dir}/.meridian/task-backlog.yaml` and add:\n"
                f"   ```yaml\n"
                f"   - id: TASK-###-xxxx\n"
                f"     title: \"<action-oriented title from plan>\"\n"
                f"     priority: P1\n"
                f"     status: in_progress\n"
                f"     path: \".meridian/tasks/TASK-###-xxxx/\"\n"
                f"     plan_path: \"<original plan file path>\"\n"
                f"   ```\n\n"
                f"Skip task creation only for trivial changes or small bug fixes.\n"
                f"All three steps are REQUIRED. Do not skip the backlog entry."
            ),
            "systemMessage": "[Meridian] Plan approved. Claude will create task folder and register in backlog."
        }
        print(json.dumps(output))
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

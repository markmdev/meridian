#!/usr/bin/env python3
"""
Plan Approval Reminder Hook - PostToolUse ExitPlanMode

Reminds Claude to create a task after plan is approved.
If Pebble is enabled, instructs to create Pebble issues for each plan item.
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

    # Build instructions based on mode
    if pebble_enabled:
        # Pebble mode: skip task folder, use Pebble issues instead
        reason = (
            f"[SYSTEM]: If the user has approved the plan, **CREATE PEBBLE ISSUES** (MANDATORY):\n\n"
            f"Read `{claude_project_dir}/.meridian/PEBBLE_GUIDE.md` for command reference.\n\n"
            f"**Key principles:**\n"
            f"1. **Always use `--json`** on create/update/close commands\n"
            f"2. **Create ALL issues upfront** — full visibility NOW, not incrementally\n"
            f"3. **Add explicit dependencies** — parent-child is hierarchy only, NOT execution order\n"
            f"4. **No orphan issues** — every issue connected to the work graph\n"
            f"5. **Comprehensive descriptions** — Purpose, Requirements, Acceptance Criteria\n\n"
            f"**Structure your work:**\n"
            f"- Epic for the overall plan\n"
            f"- Task issues for each logical unit of work\n"
            f"- Dependencies between tasks that must run sequentially\n"
            f"- Tasks without dependencies run in parallel\n\n"
            f"**Granularity**: If it takes 2+ minutes, it's an issue. Many small issues > few large ones.\n\n"
            f"Skip issue creation only for trivial changes or small bug fixes."
        )
    else:
        # Default mode: task folder + backlog
        reason = (
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
        )

    output = {
        "decision": "block",
        "reason": reason,
        "systemMessage": "[Meridian] Plan approved. Claude will create task folder and register in backlog."
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

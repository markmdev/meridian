#!/usr/bin/env python3
"""
Plan Approval Reminder Hook - PostToolUse ExitPlanMode

Reminds Claude to create a task after plan is approved.
If Beads is enabled, instructs to create Beads issues for each plan item.
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

    # Check if Beads is enabled
    beads_enabled = False
    if claude_project_dir:
        config = get_project_config(Path(claude_project_dir))
        beads_enabled = config.get('beads_enabled', False)

    # Build instructions based on mode
    if beads_enabled:
        # Beads mode: skip task folder, use Beads issues instead
        reason = (
            f"[SYSTEM]: If the user has approved the plan, **CREATE BEADS ISSUES** (MANDATORY):\n\n"
            f"Break down the plan into granular Beads issues. **Any work that takes 2+ minutes = separate issue.**\n\n"
            f"**Structure:**\n"
            f"- Create one **epic** for the overall plan\n"
            f"- Create **task** issues for each step/phase (as children of epic)\n"
            f"- Create **sub-tasks** for individual items within steps\n\n"
            f"**Commands:**\n"
            f"```bash\n"
            f"# Create epic for the plan\n"
            f"bd create \"Plan: <title>\" -t epic --description \"<plan summary>\" --json\n\n"
            f"# Create tasks for each phase (as children)\n"
            f"bd create \"Phase 1: <title>\" -t task --deps parent:<epic-id> --description \"...\" --json\n\n"
            f"# Create sub-tasks for items within phases\n"
            f"bd create \"<specific item>\" -t task --deps parent:<phase-id> --description \"...\" --json\n"
            f"```\n\n"
            f"**Priorities**: Use `-p 0` (critical) to `-p 4` (backlog). NOT words.\n\n"
            f"**Rule**: If it takes 2+ minutes, it's an issue. Be granular — many small issues > few large ones.\n\n"
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

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
            f"1. Create one **epic** for the overall plan\n"
            f"2. Create **task** issues for each step/phase (as children of epic)\n"
            f"3. Create **sub-tasks** for ALL items within ALL phases — do this NOW, not incrementally\n"
            f"4. Add **dependencies between sub-tasks** within each phase (not just parent deps)\n\n"
            f"**CRITICAL: Create ALL sub-tasks upfront** for full visibility. Don't create Phase 1 sub-tasks "
            f"and leave others for later. The user needs to see the complete breakdown NOW.\n\n"
            f"**CRITICAL: Add inter-subtask dependencies.** Within each phase, sub-tasks depend on each other. "
            f"Example: \"Apply migrations\" depends on all \"Define X table\" tasks. Without these deps, "
            f"`bd ready` shows ALL sub-tasks as ready when the phase unblocks — wrong.\n\n"
            f"**CRITICAL: Write comprehensive PM-style descriptions.** Technical details change; outcomes don't. "
            f"Write descriptions an agent can work from WITHOUT reading the full plan:\n\n"
            f"BAD (too terse):\n"
            f"> `id, name, created_at, deleted_at (soft delete)`\n\n"
            f"GOOD (comprehensive):\n"
            f"> `## Purpose\n"
            f"> Store client entities for the multi-tenant system. Clients are the top-level organizational unit — "
            f"all data (emails, docs, slack) is scoped to clients.\n"
            f"> \n"
            f"> ## Requirements\n"
            f"> - Each client has a unique ID and display name\n"
            f"> - Support soft-delete (deleted clients hidden from queries but data preserved)\n"
            f"> - Track creation and modification timestamps for audit\n"
            f"> \n"
            f"> ## Acceptance Criteria\n"
            f"> - [ ] Can create a new client with name\n"
            f"> - [ ] Can list all active (non-deleted) clients\n"
            f"> - [ ] Can get client by ID\n"
            f"> - [ ] Can soft-delete client (sets deleted_at, excluded from list)\n"
            f"> - [ ] Timestamps auto-populated\n"
            f"> \n"
            f"> ## References\n"
            f"> See Phase 2 in plan for full schema and relationships.`\n\n"
            f"**Commands:**\n"
            f"```bash\n"
            f"# 1. Create epic\n"
            f"bd create \"Plan: <title>\" -t epic --description \"<summary>\" --json\n\n"
            f"# 2. Create phase tasks\n"
            f"bd create \"Phase 1: <title>\" -t task --deps parent:<epic-id> --description \"...\" --json\n\n"
            f"# 3. Create ALL sub-tasks for ALL phases\n"
            f"bd create \"<item>\" -t task --deps parent:<phase-id> --description \"...\" --json\n\n"
            f"# 4. Add dependencies BETWEEN sub-tasks within phases\n"
            f"bd dep add <later-subtask-id> <earlier-subtask-id>\n"
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

#!/usr/bin/env python3
"""
Stop Hook - Pre-Stop Update

Prompts agent to update task files, memory, and optionally run implementation review.
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import get_project_config, get_additional_review_files

REQUIRED_SCORE = 9


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    if input_data.get("hook_event_name") != "Stop":
        sys.exit(0)

    # If already prompted, allow stop
    if input_data.get("stop_hook_active"):
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)  # Can't operate without project dir
    base_dir = Path(claude_project_dir)

    config = get_project_config(base_dir)
    files_list = '\n'.join(get_additional_review_files(base_dir, absolute=True))

    # Base message
    reason = (
        "[SYSTEM]: Before stopping, check whether you need to update "
        f"`{claude_project_dir}/.meridian/task-backlog.yaml`, "
        f"`{claude_project_dir}/.meridian/tasks/TASK-###/TASK-###-context.md` "
        "(for the current task), "
        f"or `{claude_project_dir}/.meridian/memory.jsonl` using the `memory-curator` skill, as well as any other "
        "documents that should reflect what you accomplished during this session (for example design documents, API specifications, etc.).\n"
        "If nothing significant happened, you may skip the update.\n"
        "Before invoking the `memory-curator` skill - answer to these 3 questions and invoke the skill only if at least one of the following is true: "
        "1) Is this an important architectural decision or pattern that will be useful for future reference? Will this decision meaningfully affect how we build other features? "
        "2) Is this a problem that is worth remembering and avoiding in the future? "
        "3) If you never will work on this task again, will this insight be useful for future reference?.\n\n"
        "If you were working on a task, update the status, session progress and next steps in "
        f"`{claude_project_dir}/.meridian/tasks/TASK-###/TASK-###-context.md` with details such as: the current implementation "
        "step, key decisions made, issues discovered, complex problems solved, and any other important information from this "
        "session. Save information that would be difficult to rediscover in future sessions. If nothing significant happened, you may skip the update.\n\n"
        "If you consider the current work \"finished\" or close to completion, you MUST ensure the codebase is clean before "
        "stopping: run the project's tests, lint, and build commands. If any of these fail, you must fix the issues and rerun "
        "them until they pass before stopping. If they already passed recently and no further changes were made, you may state "
        "that they are already clean and stop.\n\n"
    )

    # Implementation review section (conditional)
    if config['implementation_review_enabled']:
        reason += (
            "**IMPLEMENTATION REVIEW**: If you were working on implementing a plan, you MUST run implementation review.\n\n"
            "**MULTI-REVIEWER STRATEGY** (for multi-phase plans):\n"
            "- Spawn **one implementation-reviewer per plan phase** — each reviewer gets a specific scope (files/folders) and the relevant plan section\n"
            "- Spawn **integration reviewer(s)** with `review_type: \"integration\"` to verify all modules are wired together — use your judgment on how many based on project complexity\n"
            "- Call **ALL reviewers in parallel** (single message with multiple Task tool calls)\n"
            "- You may spawn **more than 3 agents** for review — this is an exception to the soft limit\n\n"
            "**Reviewer prompt format** (for each reviewer):\n"
            "---\n"
            f"Review Scope: [FILES/FOLDERS TO REVIEW]\n"
            f"Plan (relevant section): [PASTE OR REFERENCE PLAN STEPS]\n"
            f"Review Type: phase | integration\n"
            f"Additional files to read:\n{files_list}\n"
            "---\n\n"
            "**Review output**: Each reviewer writes their review to `.meridian/implementation-reviews/review-{{random}}.md` and returns only the file path.\n\n"
            "**After all reviewers complete**:\n"
            "1. Read all review files from `.meridian/implementation-reviews/`\n"
            "2. Aggregate findings across all reviews\n"
            f"3. Implementation must achieve score {REQUIRED_SCORE}+ on ALL reviews\n\n"
            f"**ITERATION REQUIRED**: If any score is below {REQUIRED_SCORE}:\n"
            "1. Review each finding with the user using AskUserQuestion\n"
            "2. For findings the user wants to fix: make the fixes in the codebase\n"
            "3. For findings the user declines: note as `[USER_DECLINED: <finding> - Reason: <reason>]`\n"
            "4. Re-run the failing reviewer(s)\n"
            f"5. Repeat until all scores reach {REQUIRED_SCORE}+\n\n"
        )

    # Footer
    reason += (
        "If you have nothing to update and were not working on a plan, your response to this hook must be exactly the same as the message that was blocked. "
        "If you did update something or called implementation-reviewer, resend the same message you sent before you were interrupted by this hook. "
        "Before marking a task as complete, review the 'Definition of Done' section in "
        f"`{claude_project_dir}/.meridian/prompts/agent-operating-manual.md`."
    )

    output = {
        "decision": "block",
        "reason": reason,
        "systemMessage": "[Meridian] Before stopping, Claude is updating task files, backlog, and memory, verifying tests/lint/build, and running implementation review if needed."
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

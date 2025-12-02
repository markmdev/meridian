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

    cwd = input_data.get("cwd", os.getcwd())
    base_dir = Path(cwd)
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", cwd)

    config = get_project_config(base_dir)
    files_list = '\n'.join(get_additional_review_files(base_dir))

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
            "**IMPLEMENTATION REVIEW**: If you were working on implementing a plan, you MUST call the implementation-reviewer agent "
            "to verify the implementation matches the plan. Call it with EXACTLY this prompt:\n\n"
            "---\n"
            f"Plan: {{PLAN_FILE_PATH}}\n"
            f"Additional files to read:\n{files_list}\n"
            "---\n\n"
            "Replace {PLAN_FILE_PATH} with the actual path to your plan file.\n\n"
            f"**ITERATION REQUIRED**: The implementation must achieve a score of {REQUIRED_SCORE}+ to be considered complete.\n"
            f"If the score is below {REQUIRED_SCORE}, you must:\n"
            "1. Review each finding with the user using AskUserQuestion\n"
            "2. For findings the user wants to fix: make the fixes in the codebase\n"
            "3. For findings the user declines: note as `[USER_DECLINED: <finding> - Reason: <reason>]`\n"
            "4. Call implementation-reviewer again\n"
            f"5. Repeat until score reaches {REQUIRED_SCORE}+\n\n"
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

#!/usr/bin/env python3
"""
Reviewer Root Guard - PreToolUse Task

Blocks reviewer agent spawning if the main agent is not in the project root directory.
Reviewers read .injected-files which contains absolute paths, but they may fail if
spawned from a subdirectory.
"""

import json
import os
import sys


# Agents that require being in project root
REVIEWER_AGENTS = {
    "plan-reviewer",
    "code-reviewer",
    "implementation-reviewer",
    "browser-verifier",
    "pebble-scaffolder",
}


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")

    # Only handle PreToolUse Task
    if hook_event != "PreToolUse" or tool_name != "Task":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "").lower()

    # Only check reviewer agents
    if subagent_type not in REVIEWER_AGENTS:
        sys.exit(0)

    # Get current working directory and project root
    cwd = input_data.get("cwd", "")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    if not cwd or not project_dir:
        sys.exit(0)

    # Normalize paths for comparison
    cwd_normalized = os.path.normpath(cwd)
    project_normalized = os.path.normpath(project_dir)

    # Check if in project root
    if cwd_normalized == project_normalized:
        sys.exit(0)

    # Block - not in project root
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"**Cannot spawn {subagent_type} from subdirectory**\n\n"
                f"You are currently in: `{cwd}`\n"
                f"Project root is: `{project_dir}`\n\n"
                "Reviewer agents must be spawned from the project root directory "
                "to correctly read `.injected-files` and access project context.\n\n"
                "**Fix:** Navigate to project root first:\n"
                f"```bash\n"
                f"cd \"{project_dir}\"\n"
                f"```\n\n"
                f"Then retry spawning the {subagent_type} agent."
            )
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

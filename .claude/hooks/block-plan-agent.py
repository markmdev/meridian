#!/usr/bin/env python3
"""
Block Plan Agent Hook - PreToolUse Task

Blocks calls to the Plan agent and redirects to use the Planning skill instead.
Configurable via plan_agent_redirect_enabled in config.yaml (default: true).
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import get_project_config


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only handle PreToolUse Task
    if hook_event != "PreToolUse" or tool_name != "Task":
        sys.exit(0)

    # Check if this is a Plan agent call
    subagent_type = tool_input.get("subagent_type", "")
    if subagent_type.lower() != "plan":
        sys.exit(0)

    # Check if redirect is enabled
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if claude_project_dir:
        config = get_project_config(Path(claude_project_dir))
        if not config.get('plan_agent_redirect_enabled', True):
            sys.exit(0)

    # Block the Plan agent call
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "**Plan Agent Deprecated - Use Planning Skill Instead**\n\n"
                "The Plan agent has been replaced by the **Planning skill** to preserve "
                "full conversation context during planning.\n\n"
                "**What to do:**\n"
                "1. Invoke the `planning` skill\n"
                "2. Follow the skill's methodology to create your plan\n"
                "3. Use **Explore subagents** for codebase research and investigation\n"
                "4. Save your plan to `.claude/plans/` when complete\n\n"
                "**Why this change:**\n"
                "- You retain full conversation context (important details won't be lost)\n"
                "- You can ask clarifying questions during planning\n"
                "- Explore subagents handle research while you focus on architecture\n\n"
                "The planning skill provides the same methodology as the Plan agent. "
                "Simply proceed with planning directly."
            )
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

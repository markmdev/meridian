#!/usr/bin/env python3
"""
Context Acknowledgment Guard - PreToolUse Hook

Blocks the first tool call after session start to ensure the agent
acknowledges the injected project context before proceeding.
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    flag_exists,
    cleanup_flag,
    get_project_config,
    get_onboarding_status,
    CONTEXT_ACK_FLAG,
    ACTIVE_PLAN_FILE,
)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    if input_data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)  # Can't operate without project dir
    base_dir = Path(claude_project_dir)

    # No acknowledgment flag = allow everything
    if not flag_exists(base_dir, CONTEXT_ACK_FLAG):
        sys.exit(0)

    # Flag exists - block and ask for acknowledgment, then remove flag
    cleanup_flag(base_dir, CONTEXT_ACK_FLAG)

    # Check config and onboarding status
    config = get_project_config(base_dir)
    pebble_enabled = config.get('pebble_enabled', False)
    onboarding = get_onboarding_status(base_dir)

    # Check if api-docs exist
    api_docs_index = base_dir / ".meridian" / "api-docs" / "INDEX.md"
    has_api_docs = api_docs_index.exists()

    reason = (
        "**CONTEXT ACKNOWLEDGMENT REQUIRED**\n\n"
        "Project context has been injected into this session. "
        "Before using any tools, please acknowledge that you have read and understood:\n\n"
        "1. Any **user-provided docs** (project-specific documentation)\n"
        "2. The **user profile** (if present — user preferences and working style)\n"
        "3. The **project profile** (if present — project context and constraints)\n"
        "4. The **memory entries** (past decisions and lessons learned)\n"
        "5. Any **in-progress tasks** and their current state\n"
        "6. The **session context** (recent decisions and discoveries)\n"
        "7. Any **active plans** for in-progress tasks\n"
        "8. The **CODE_GUIDE** conventions for this project\n"
        "9. The **agent-operating-manual** instructions\n"
    )

    item_num = 10
    if has_api_docs:
        reason += (
            f"{item_num}. The **api-docs/INDEX.md** — lists documented external APIs. "
            "Before using any listed API, read its doc file first.\n"
        )
        item_num += 1

    if pebble_enabled:
        reason += f"{item_num}. **Pebble issue tracker** is enabled — check project state and available work\n"

    # Add onboarding prompts if profiles are missing
    if not onboarding['user_onboarded'] or not onboarding['project_onboarded']:
        reason += "\n---\n\n**ONBOARDING AVAILABLE**\n\n"

        if not onboarding['user_onboarded']:
            reason += (
                "**User profile not found.** After acknowledging context, offer the user a quick interview "
                "to learn their preferences (~10-15 min). Explain it helps you communicate their way, "
                "make decisions at the right autonomy level, and match their quality standards. "
                "If they agree, invoke the `/onboard-user` skill.\n\n"
            )

        if not onboarding['project_onboarded']:
            reason += (
                "**Project profile not found.** After acknowledging context, offer the user a quick interview "
                "to learn about this project (~10-15 min). Explain it helps you understand what they're building, "
                "how critical it is, security requirements, and priorities. "
                "If they agree, invoke the `/onboard-project` skill.\n\n"
            )

    reason += (
        "\nBriefly summarize what you understand about the current project state, "
        "then ask the user what they'd like to work on.\n\n"
        "**IMPORTANT**: After acknowledging, you MUST retry the same action that was just blocked. "
        "Do not skip it or move on to something else."
    )

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

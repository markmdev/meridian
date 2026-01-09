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
    CONTEXT_ACK_FLAG,
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

    # Check if Beads is enabled
    config = get_project_config(base_dir)
    beads_enabled = config.get('beads_enabled', False)

    # Check if sprint workflow is active
    sprint_active = False
    session_context = base_dir / ".meridian" / "session-context.md"
    if session_context.exists():
        try:
            content = session_context.read_text()
            sprint_active = "<!-- BEADS SPRINT WORKFLOW" in content
        except Exception:
            pass

    reason = (
        "**CONTEXT ACKNOWLEDGMENT REQUIRED**\n\n"
        "Project context has been injected into this session. "
        "Before using any tools, please acknowledge that you have read and understood:\n\n"
        "1. Any **user-provided docs** (project-specific documentation)\n"
        "2. The **memory entries** (past decisions and lessons learned)\n"
        "3. Any **in-progress tasks** and their current state\n"
        "4. The **session context** (recent decisions and discoveries)\n"
        "5. Any **active plans** for in-progress tasks\n"
        "6. The **CODE_GUIDE** conventions for this project\n"
        "7. The **agent-operating-manual** instructions\n\n"
    )

    if beads_enabled:
        reason += (
            "8. **Beads issue tracker** is enabled — check project state and available work\n\n"
        )

    if sprint_active:
        reason += (
            "⚠️ **ACTIVE SPRINT WORKFLOW DETECTED**\n\n"
            "A Beads Sprint workflow is in progress. Read the workflow section at the bottom of "
            "`.meridian/session-context.md` to understand:\n"
            "- Current scope and issues being worked on\n"
            "- Which issues are completed (checked) vs pending\n"
            "- Current phase (Planning/Implementation/Review/Verify)\n\n"
            "Resume from where you left off. Do NOT restart from the beginning.\n\n"
        )

    reason += (
        "Briefly summarize what you understand about the current project state, "
        "then "
    )

    if sprint_active:
        reason += "continue with the active sprint workflow.\n\n"
    else:
        reason += "ask the user what they'd like to work on.\n\n"

    reason += (
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

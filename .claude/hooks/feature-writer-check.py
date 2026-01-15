#!/usr/bin/env python3
"""
Feature Writer Check Hook - PreToolUse ExitPlanMode

Blocks ExitPlanMode if the active plan doesn't have verification features.
Configurable via feature_writer_enforcement_enabled in config.yaml (default: false).
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import get_project_config

VERIFICATION_MARKER = "<!-- VERIFICATION_FEATURES -->"


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")

    # Only handle PreToolUse ExitPlanMode
    if hook_event != "PreToolUse" or tool_name != "ExitPlanMode":
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)
    base_dir = Path(claude_project_dir)

    # Check if enabled in config
    config = get_project_config(base_dir)
    if not config.get('feature_writer_enforcement_enabled', False):
        sys.exit(0)

    # Find active plan file
    active_plan_file = base_dir / ".meridian" / ".active-plan"
    if not active_plan_file.exists():
        # No active plan, allow exit
        sys.exit(0)

    try:
        plan_path = active_plan_file.read_text().strip()
        if not plan_path:
            sys.exit(0)

        if plan_path.startswith('/'):
            full_path = Path(plan_path)
        else:
            full_path = base_dir / plan_path

        if not full_path.exists():
            sys.exit(0)

        plan_content = full_path.read_text()
    except IOError:
        sys.exit(0)

    # Check for verification features marker
    if VERIFICATION_MARKER in plan_content:
        sys.exit(0)

    # Block - no verification features
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "**Plan is missing verification features.**\n\n"
                "Before exiting plan mode, invoke the `feature-writer` agent "
                f"with the plan file path: `{plan_path}`\n\n"
                "The agent will generate testable acceptance criteria for each phase. "
                "These become Pebble subtasks that verify the implementation works.\n\n"
                "After feature-writer completes, retry ExitPlanMode."
            )
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

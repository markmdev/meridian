#!/usr/bin/env python3
"""
Action Counter Hook - Tracks tool calls for stop hook threshold.

Handles:
- PostToolUse: Increment counter, track file edits, track plan mode transitions
- PreToolUse: Detect code-reviewer spawn

Counter is reset by stop hooks (stop-checklist.py, work-until-stop.py)
when they actually fire. This ensures actions accumulate across user
interruptions until the agent sees the stop message.

Plan mode is tracked via EnterPlanMode/ExitPlanMode tool usage for immediate
state updates (rather than waiting for next UserPromptSubmit).
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import (
    ACTION_COUNTER_FILE,
    PLAN_MODE_STATE,
    increment_plan_action_counter,
    log_hook_output,
    state_path,
)


def get_counter(base_dir: Path) -> int:
    """Read current counter value."""
    counter_path = state_path(base_dir, ACTION_COUNTER_FILE)
    try:
        if counter_path.exists():
            return int(counter_path.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0


def set_counter(base_dir: Path, value: int) -> None:
    """Write counter value."""
    counter_path = state_path(base_dir, ACTION_COUNTER_FILE)
    try:
        counter_path.parent.mkdir(parents=True, exist_ok=True)
        counter_path.write_text(str(value))
    except IOError:
        pass


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        return 0
    base_dir = Path(claude_project_dir)

    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")

    # PostToolUse: Increment counters and track plan mode
    if hook_event == "PostToolUse":
        # Track plan mode transitions from tool usage
        plan_mode_file = state_path(base_dir, PLAN_MODE_STATE)
        plan_mode_file.parent.mkdir(parents=True, exist_ok=True)

        if tool_name == "EnterPlanMode":
            plan_mode_file.write_text("plan")
            # Inject reminder about planning resources
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        "[SYSTEM]: Plan mode activated. Activate the `/planning` skill NOW — before doing anything else. It defines your planning methodology."
                    )
                }
            }
            log_hook_output(base_dir, "action-counter", output)
        elif tool_name == "ExitPlanMode":
            plan_mode_file.write_text("other")

        # Increment main action counter
        current = get_counter(base_dir)
        set_counter(base_dir, current + 1)

        # Also increment plan action counter if in plan mode
        if plan_mode_file.exists():
            mode = plan_mode_file.read_text().strip()
            if mode == "plan":
                increment_plan_action_counter(base_dir)

    # UserPromptSubmit: Just increment main counter
    if hook_event == "UserPromptSubmit":
        current = get_counter(base_dir)
        set_counter(base_dir, current + 1)

        plan_mode_file = state_path(base_dir, PLAN_MODE_STATE)
        if plan_mode_file.exists():
            mode = plan_mode_file.read_text().strip()
            if mode == "plan":
                increment_plan_action_counter(base_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())

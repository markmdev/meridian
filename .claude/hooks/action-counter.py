#!/usr/bin/env python3
"""
Action Counter Hook - Tracks tool calls for stop hook threshold.

Handles:
- PostToolUse: Increment counter, track file edits, track plan mode transitions
- PreToolUse: Detect code-reviewer spawn

Counter is reset by stop hooks (pre-stop-update.py, work-until-stop.py)
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
from config import (
    ACTION_COUNTER_FILE,
    PLAN_MODE_STATE,
    EDITS_SINCE_REVIEW_FILE,
    increment_plan_action_counter,
    increment_edits_since,
    reset_edits_since,
)


def get_counter(base_dir: Path) -> int:
    """Read current counter value."""
    counter_path = base_dir / ACTION_COUNTER_FILE
    try:
        if counter_path.exists():
            return int(counter_path.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0


def set_counter(base_dir: Path, value: int) -> None:
    """Write counter value."""
    counter_path = base_dir / ACTION_COUNTER_FILE
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

    # PreToolUse: Reset review counter when code-reviewer is spawned
    if hook_event == "PreToolUse" and tool_name == "Task":
        tool_input = input_data.get("tool_input", {})
        subagent_type = tool_input.get("subagent_type", "").lower()
        if subagent_type == "code-reviewer":
            reset_edits_since(base_dir, EDITS_SINCE_REVIEW_FILE)

    # PostToolUse: Increment counters and track plan mode
    if hook_event == "PostToolUse":
        # Track plan mode transitions from tool usage
        plan_mode_file = base_dir / PLAN_MODE_STATE
        plan_mode_file.parent.mkdir(parents=True, exist_ok=True)

        if tool_name == "EnterPlanMode":
            plan_mode_file.write_text("plan")
            # Inject reminder about planning resources
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        "[SYSTEM]: Plan mode activated. Use `/planning` skill for methodology. "
                        "Spawn Plan agents for concrete implementation details."
                    )
                }
            }
            print(json.dumps(output))
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

        # Track Edit/Write for review counter
        if tool_name in ("Edit", "Write"):
            increment_edits_since(base_dir, EDITS_SINCE_REVIEW_FILE)

    # UserPromptSubmit: Just increment main counter
    if hook_event == "UserPromptSubmit":
        current = get_counter(base_dir)
        set_counter(base_dir, current + 1)

        plan_mode_file = base_dir / PLAN_MODE_STATE
        if plan_mode_file.exists():
            mode = plan_mode_file.read_text().strip()
            if mode == "plan":
                increment_plan_action_counter(base_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())

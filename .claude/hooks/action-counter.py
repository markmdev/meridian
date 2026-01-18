#!/usr/bin/env python3
"""
Action Counter Hook - Tracks tool calls for stop hook threshold.

Handles:
- PostToolUse: Increment counter

Counter is reset by stop hooks (pre-stop-update.py, work-until-stop.py)
when they actually fire. This ensures actions accumulate across user
interruptions until the agent sees the stop message.
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import ACTION_COUNTER_FILE, PLAN_MODE_STATE, increment_plan_action_counter


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

    if hook_event in ("PostToolUse", "UserPromptSubmit"):
        # Increment main action counter
        current = get_counter(base_dir)
        set_counter(base_dir, current + 1)

        # Also increment plan action counter if in plan mode
        plan_mode_file = base_dir / PLAN_MODE_STATE
        if plan_mode_file.exists():
            mode = plan_mode_file.read_text().strip()
            if mode == "plan":
                increment_plan_action_counter(base_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())

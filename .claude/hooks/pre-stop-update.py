#!/usr/bin/env python3
"""
Stop Hook - Pre-Stop Update

Prompts agent to update task files, memory, and optionally run implementation review.
Skips if a work-until loop is active (loop hook handles everything).
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    get_project_config,
    is_loop_active,
    build_stop_prompt,
    ACTION_COUNTER_FILE,
)


def get_action_count(base_dir: Path) -> int:
    """Read current action counter value."""
    counter_path = base_dir / ACTION_COUNTER_FILE
    try:
        if counter_path.exists():
            return int(counter_path.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0


def reset_action_count(base_dir: Path) -> None:
    """Reset action counter to 0."""
    counter_path = base_dir / ACTION_COUNTER_FILE
    try:
        counter_path.write_text("0")
    except IOError:
        pass


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    if input_data.get("hook_event_name") != "Stop":
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)  # Can't operate without project dir
    base_dir = Path(claude_project_dir)

    # If already prompted, allow stop and reset counter for next task
    if input_data.get("stop_hook_active"):
        reset_action_count(base_dir)
        sys.exit(0)

    # If work-until loop is active, exit and let loop hook handle it
    if is_loop_active(base_dir):
        sys.exit(0)

    config = get_project_config(base_dir)

    # Skip stop hook if too few actions (trivial task)
    min_actions = config.get('stop_hook_min_actions', 10)
    if min_actions > 0:
        action_count = get_action_count(base_dir)
        if action_count < min_actions:
            reset_action_count(base_dir)  # Reset so trivial tasks don't accumulate
            sys.exit(0)  # Allow stop without prompts

    # Build the stop prompt using shared helper
    reason = build_stop_prompt(base_dir, config)

    # Reset action counter now that stop hook is firing
    reset_action_count(base_dir)

    output = {
        "decision": "block",
        "reason": reason,
        "systemMessage": "[Meridian] Before stopping, Claude is updating session context, backlog, and memory, verifying tests/lint/build, and running implementation review if needed."
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

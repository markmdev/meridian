#!/usr/bin/env python3
"""
Action Counter Hook - Tracks tool calls since last user input.

Handles two events:
- PostToolUse: Increment counter
- UserPromptSubmit: Reset counter to 0

Used by pre-stop-update.py to skip prompts on short sessions.
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import ACTION_COUNTER_FILE


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

    if hook_event == "UserPromptSubmit":
        # Reset counter on user input
        set_counter(base_dir, 0)
    elif hook_event == "PostToolUse":
        # Increment counter on tool use
        current = get_counter(base_dir)
        set_counter(base_dir, current + 1)

    return 0


if __name__ == "__main__":
    sys.exit(main())

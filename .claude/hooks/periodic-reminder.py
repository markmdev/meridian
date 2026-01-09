#!/usr/bin/env python3
"""
Periodic Reminder Hook

Injects a small reminder about key behaviors every N actions.
Both tool calls and user messages increment the counter.
Resets on session start (startup, compaction, clear).

Handles:
- PostToolUse: Increment counter, inject reminder if threshold hit
- UserPromptSubmit: Increment counter, inject reminder if threshold hit
- SessionStart: Reset counter
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import get_project_config, REMINDER_COUNTER_FILE

REMINDER_TEXT = (
    "[REMINDER]: Research before implementing — search, don't assume. "
    "Every code change needs a Beads issue — even bugs fixed immediately (issue → fix → comment → close). "
    "Follow existing codebase patterns. Ask before pivoting from the plan. "
    "Save important user messages to session-context. Check memory.jsonl for past lessons."
)


def get_counter(base_dir: Path) -> int:
    """Read current counter value."""
    counter_path = base_dir / REMINDER_COUNTER_FILE
    try:
        if counter_path.exists():
            return int(counter_path.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0


def set_counter(base_dir: Path, value: int) -> None:
    """Write counter value."""
    counter_path = base_dir / REMINDER_COUNTER_FILE
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

    if hook_event == "SessionStart":
        # Reset counter on session start (startup, compaction, clear)
        set_counter(base_dir, 0)
        return 0

    if hook_event in ("PostToolUse", "UserPromptSubmit"):
        # Get config
        config = get_project_config(base_dir)
        interval = config.get('reminder_interval', 10)

        if interval <= 0:
            # Disabled
            return 0

        # Increment counter
        current = get_counter(base_dir)
        new_count = current + 1

        # Check if we hit the threshold
        if new_count >= interval:
            # Reset counter and inject reminder
            set_counter(base_dir, 0)

            # Output format differs by hook event
            if hook_event == "PostToolUse":
                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": REMINDER_TEXT
                    }
                }
            else:  # UserPromptSubmit
                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": REMINDER_TEXT
                    }
                }
            print(json.dumps(output))
        else:
            # Just increment
            set_counter(base_dir, new_count)

    return 0


if __name__ == "__main__":
    sys.exit(main())

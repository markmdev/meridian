#!/usr/bin/env python3
"""
Session Cleanup — SessionStart (startup, compact, clear) + SessionEnd Hook

Removes ephemeral state files based on event type. Some files persist
across certain events (e.g., active-plan is never deleted).
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import get_state_dir

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
STATE_DIR = get_state_dir(PROJECT_DIR)

# Files to delete on startup (fresh session)
STARTUP_DELETE = [
    "action-counter",

    "plan-mode-state",
    "plan-review-blocked",
    "plan-action-counter",
]

# Files to delete on clear (user cleared conversation)
CLEAR_DELETE = [
    "action-counter",

    "plan-mode-state",
    "plan-review-blocked",
]

# Files to delete on compact
COMPACT_DELETE = []

# Files to delete on SessionEnd
SESSION_END_DELETE = [
    "plan-action-counter",
]


def delete_files(files: list[str]) -> None:
    """Delete specified files from STATE_DIR."""
    for filename in files:
        filepath = STATE_DIR / filename
        try:
            if filepath.exists():
                filepath.unlink()
        except Exception:
            pass


def main():
    # Parse input
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    hook_event = input_data.get("hook_event_name", "")
    source = input_data.get("source", "startup")

    if not STATE_DIR.exists():
        sys.exit(0)

    # Determine which files to delete based on event
    if hook_event == "SessionEnd":
        delete_files(SESSION_END_DELETE)
    elif source == "startup":
        delete_files(STARTUP_DELETE)
    elif source == "compact":
        delete_files(COMPACT_DELETE)
    elif source == "clear":
        delete_files(CLEAR_DELETE)

    sys.exit(0)


if __name__ == "__main__":
    main()

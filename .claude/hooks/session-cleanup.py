#!/usr/bin/env python3
"""
Session cleanup hook - runs on startup, clear, and session end.

Removes ephemeral state files based on event type. Some files persist
across certain events (e.g., active-plan is never deleted).

Compact is handled by dedicated hooks (periodic-reminder.py, clear-precompaction-flag.py).
"""

import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
STATE_DIR = PROJECT_DIR / ".meridian/.state"

# Files to delete on startup (fresh session)
STARTUP_DELETE = [
    "action-counter",
    "reminder-counter",
    "pre-compaction-synced",
    "plan-mode-state",
    "plan-review-blocked",
    "plan-action-counter",
    "docs-researcher-active",
]

# Files to delete on clear (user cleared conversation)
CLEAR_DELETE = [
    "action-counter",
    "reminder-counter",
    "pre-compaction-synced",
    "plan-mode-state",
    "plan-review-blocked",
    "docs-researcher-active",
]

# Files to delete on SessionEnd
SESSION_END_DELETE = [
    "reminder-counter",
    "plan-action-counter",
    "docs-researcher-active",
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
    # Note: compact is handled by dedicated hooks (periodic-reminder.py, clear-precompaction-flag.py)
    if hook_event == "SessionEnd":
        delete_files(SESSION_END_DELETE)
    elif source == "startup":
        delete_files(STARTUP_DELETE)
    elif source == "clear":
        delete_files(CLEAR_DELETE)

    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Session Cleanup — SessionStart Hook

Removes ephemeral state files based on how the session started.
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import get_state_dir, is_headless

if is_headless():
    sys.exit(0)

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
STATE_DIR = get_state_dir(PROJECT_DIR)

# Files to delete on startup (fresh session)
# Note: last-session.md is NOT here — context-injector reads then deletes it
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

    source = input_data.get("source", "startup")

    if not STATE_DIR.exists():
        sys.exit(0)

    # Determine which files to delete based on source
    if source == "startup":
        delete_files(STARTUP_DELETE)
    elif source in ("clear", "compact"):
        delete_files(CLEAR_DELETE)

    sys.exit(0)


if __name__ == "__main__":
    main()

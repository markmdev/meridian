#!/usr/bin/env python3
"""
Session cleanup hook - runs on startup, clear, compact, and session end.

Removes ephemeral state files so next session starts fresh.
"""

import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))

# Ephemeral state files to clean up on any session event
STATE_FILES = [
    PROJECT_DIR / ".meridian/.plan-mode-state",
    PROJECT_DIR / ".meridian/.action-counter",
    PROJECT_DIR / ".meridian/.reminder-counter",
    PROJECT_DIR / ".meridian/.pre-compaction-synced",
]

# Files to clean up ONLY on fresh startup (not compact/clear)
STARTUP_ONLY_FILES = [
    PROJECT_DIR / ".meridian/.plan-review-blocked",
    PROJECT_DIR / ".meridian/.plan-action-start",
]


def main():
    # Parse input to check source
    source = "startup"
    try:
        input_data = json.load(sys.stdin)
        source = input_data.get("source", "startup")
    except (json.JSONDecodeError, EOFError):
        pass

    # Clean up standard ephemeral state files
    for state_file in STATE_FILES:
        try:
            if state_file.exists():
                state_file.unlink()
        except Exception:
            pass  # Ignore cleanup errors

    # Clean up startup-only files (not on compact/clear - user may still be mid-workflow)
    if source == "startup":
        for state_file in STARTUP_ONLY_FILES:
            try:
                if state_file.exists():
                    state_file.unlink()
            except Exception:
                pass

    sys.exit(0)


if __name__ == "__main__":
    main()

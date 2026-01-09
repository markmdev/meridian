#!/usr/bin/env python3
"""
Session cleanup hook - runs on startup, clear, and session end.

Removes ephemeral state files so next session starts fresh.
"""

import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))

# Ephemeral state files to clean up
STATE_FILES = [
    PROJECT_DIR / ".meridian/.plan-mode-state",
    PROJECT_DIR / ".meridian/.plan-review-blocked",
    PROJECT_DIR / ".meridian/.action-counter",
    PROJECT_DIR / ".meridian/.reminder-counter",
    PROJECT_DIR / ".meridian/.pre-compaction-synced",
]


def main():
    # Clean up ephemeral state files
    for state_file in STATE_FILES:
        try:
            if state_file.exists():
                state_file.unlink()
        except Exception:
            pass  # Ignore cleanup errors

    sys.exit(0)


if __name__ == "__main__":
    main()

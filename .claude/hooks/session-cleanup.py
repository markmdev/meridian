#!/usr/bin/env python3
"""
Session cleanup hook - runs on startup, clear, compact, and session end.

Removes ephemeral state files so next session starts fresh.
"""

import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
STATE_DIR = PROJECT_DIR / ".meridian/.state"

# Files to preserve on compact/clear (only delete on fresh startup)
STARTUP_ONLY_FILES = [
    "plan-review-blocked",
    "plan-action-start",
]


def main():
    # Parse input to check source
    source = "startup"
    try:
        input_data = json.load(sys.stdin)
        source = input_data.get("source", "startup")
    except (json.JSONDecodeError, EOFError):
        pass

    if not STATE_DIR.exists():
        sys.exit(0)

    if source == "startup":
        # Fresh startup: delete entire state directory
        try:
            shutil.rmtree(STATE_DIR)
        except Exception:
            pass
    else:
        # Compact/clear: delete all except startup-only files
        try:
            for item in STATE_DIR.iterdir():
                if item.name not in STARTUP_ONLY_FILES:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        except Exception:
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()

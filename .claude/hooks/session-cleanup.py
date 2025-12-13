#!/usr/bin/env python3
"""
SessionEnd hook to clean up session state files.

Removes plan-mode-state so next session starts fresh.
"""

import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
STATE_FILE = PROJECT_DIR / ".meridian/.plan-mode-state"


def main():
    # Clean up plan mode state file
    try:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
    except Exception:
        pass  # Ignore cleanup errors

    sys.exit(0)


if __name__ == "__main__":
    main()

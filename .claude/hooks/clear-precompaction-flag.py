#!/usr/bin/env python3
"""
Clears pre-compaction-synced flag after compact.

This allows the pre-compaction warning to fire again if tokens grow.
"""

import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
FLAG_FILE = PROJECT_DIR / ".meridian/.pre-compaction-synced"


def main():
    try:
        if FLAG_FILE.exists():
            FLAG_FILE.unlink()
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()

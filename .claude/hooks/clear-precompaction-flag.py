#!/usr/bin/env python3
"""
Clears pre-compaction-synced flag after compact.

This allows the pre-compaction warning to fire again if tokens grow.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import PRE_COMPACTION_FLAG

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))


def main():
    flag_file = PROJECT_DIR / PRE_COMPACTION_FLAG
    try:
        if flag_file.exists():
            flag_file.unlink()
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()

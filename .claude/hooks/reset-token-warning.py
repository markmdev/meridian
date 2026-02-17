#!/usr/bin/env python3
"""
Reset Token Warning — SessionStart (compact) Hook

Clears the token warning flag after compaction so the warning can fire again.
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

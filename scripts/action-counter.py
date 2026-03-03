#!/usr/bin/env python3
"""
PostToolUse / UserPromptSubmit hook to increment the general action counter.

The action counter tracks how many actions have occurred in the current session.
Used by the stop hook to determine if enough work has been done before triggering
the stop checklist.
"""

import json
import sys
from pathlib import Path
import os

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import get_action_counter, is_headless, set_action_counter

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))


def main():
    if is_headless():
        sys.exit(0)

    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    set_action_counter(PROJECT_DIR, get_action_counter(PROJECT_DIR) + 1)
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Code Reviewer Stop Hook - SubagentStop

Resets the edits-since-review counter when code-reviewer agent completes.
Uses flag-based detection: action-counter.py creates a flag when code-reviewer
is spawned, and this hook checks for that flag.
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    CODE_REVIEWER_FLAG,
    EDITS_SINCE_REVIEW_FILE,
    cleanup_flag,
    flag_exists,
    reset_edits_since,
)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    hook_event = input_data.get("hook_event_name", "")
    if hook_event != "SubagentStop":
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)

    base_dir = Path(claude_project_dir)

    # Check if code-reviewer flag exists (set by action-counter.py)
    if not flag_exists(base_dir, CODE_REVIEWER_FLAG):
        # This is not a code-reviewer agent stopping
        sys.exit(0)

    # Clear the flag and reset the edit counter
    cleanup_flag(base_dir, CODE_REVIEWER_FLAG)
    reset_edits_since(base_dir, EDITS_SINCE_REVIEW_FILE)

    sys.exit(0)


if __name__ == "__main__":
    main()

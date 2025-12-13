#!/usr/bin/env python3
"""
UserPromptSubmit hook to track Plan mode transitions.
"""

import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
STATE_FILE = PROJECT_DIR / ".meridian/.plan-mode-state"


def get_previous_mode() -> str:
    if STATE_FILE.exists():
        return STATE_FILE.read_text().strip()
    return "other"


def save_mode(mode: str) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(mode)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    permission_mode = input_data.get("permission_mode", "default")
    current_mode = "plan" if permission_mode == "plan" else "other"
    previous_mode = get_previous_mode()

    if previous_mode != current_mode:
        if current_mode == "plan":
            print("<system-message>")
            print("Plan mode activated. Invoke the `planning` skill before proceeding.")
            print("</system-message>")

    save_mode(current_mode)
    sys.exit(0)


if __name__ == "__main__":
    main()

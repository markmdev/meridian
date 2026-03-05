#!/usr/bin/env python3
"""
UserPromptSubmit hook to track Plan mode transitions.
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import is_headless, log_hook_output, state_path, PLAN_MODE_STATE

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))


def get_previous_mode() -> str:
    state_file = state_path(PROJECT_DIR, PLAN_MODE_STATE)
    if state_file.exists():
        return state_file.read_text().strip()
    return "other"


def save_mode(mode: str) -> None:
    state_file = state_path(PROJECT_DIR, PLAN_MODE_STATE)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(mode)


def main():
    if is_headless():
        sys.exit(0)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    permission_mode = input_data.get("permission_mode", "default")
    current_mode = "plan" if permission_mode == "plan" else "other"
    previous_mode = get_previous_mode()

    if previous_mode != current_mode:
        if current_mode == "plan":
            context = "Plan mode activated. Activate the `/planning` skill NOW — before doing anything else. It defines your planning methodology."

            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context
                }
            }
            log_hook_output(PROJECT_DIR, "plan-mode-tracker", output)

    save_mode(current_mode)
    sys.exit(0)


if __name__ == "__main__":
    main()

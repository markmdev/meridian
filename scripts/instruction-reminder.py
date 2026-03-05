#!/usr/bin/env python3
"""Inject a short reminder to follow instructions on every user message."""

import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import is_headless, get_project_config

if is_headless():
    sys.exit(0)

base_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
config = get_project_config(base_dir)
extra_reminders = config.get("instruction_reminders", [])

parts = ["Follow all instructions from injected context and CLAUDE.md files."]

if isinstance(extra_reminders, list):
    for reminder in extra_reminders:
        if isinstance(reminder, str) and reminder.strip():
            parts.append(reminder.strip())

output = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": " ".join(parts),
    }
}
print(json.dumps(output))
sys.exit(0)

#!/usr/bin/env python3
"""Inject a short reminder to follow instructions on every user message."""

import json
import sys

output = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "Follow all instructions from injected context and CLAUDE.md files.",
    }
}
print(json.dumps(output))
sys.exit(0)

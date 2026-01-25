#!/usr/bin/env python3
"""
PreToolUse hook that blocks TaskOutput tool.

Agents should continue doing useful work or sleep in a loop
instead of blocking on TaskOutput.
"""

import json
import sys

def main():
    hook_input = json.loads(sys.stdin.read())
    tool_name = hook_input.get("tool_name", "")

    if tool_name == "TaskOutput":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "TaskOutput is blocked. Background agents notify on completion automatically. Continue with other work while waiting, or sleep briefly in a loop if nothing else to do."
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Allow other tools
    sys.exit(0)

if __name__ == "__main__":
    main()

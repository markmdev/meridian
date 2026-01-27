#!/usr/bin/env python3
"""
PreToolUse hook that blocks TaskOutput tool.

Background agents notify on completion automatically.
If no other work, agent should stop and wait for notification.
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
                "permissionDecisionReason": "TaskOutput is blocked. Background agents notify on completion automatically. Continue with other work, or if nothing else to do, stop and wait for the notification."
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Allow other tools
    sys.exit(0)

if __name__ == "__main__":
    main()

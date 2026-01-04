#!/usr/bin/env python3
"""
Plan Tracker Hook - PostToolUse

Tracks the active plan by watching Edit/Write/Read operations on .claude/plans/ files.
Saves the most recently accessed plan path to .meridian/.active-plan for injection.
"""

import json
import os
import sys
from pathlib import Path


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if input_data.get("hook_event_name") != "PostToolUse":
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "Read"):
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Check if this is a plan file
    if ".claude/plans/" not in file_path:
        sys.exit(0)

    # Must be a markdown file
    if not file_path.endswith(".md"):
        sys.exit(0)

    # Get project directory
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)

    base_dir = Path(claude_project_dir)
    active_plan_file = base_dir / ".meridian" / ".active-plan"

    # Ensure .meridian directory exists
    active_plan_file.parent.mkdir(parents=True, exist_ok=True)

    # Write the plan path
    try:
        active_plan_file.write_text(file_path.strip() + "\n")
    except IOError:
        pass  # Silent fail - not critical

    sys.exit(0)


if __name__ == "__main__":
    main()

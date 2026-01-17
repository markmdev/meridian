#!/usr/bin/env python3
"""
Docs Researcher Tracker Hook - PostToolUse Task

Tracks when docs-researcher agent is spawned by creating a flag file.
The flag is used by docs-researcher-stop.py to identify which agent is stopping.
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import DOCS_RESEARCHER_FLAG, create_flag


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")

    # Only handle PostToolUse Task
    if hook_event != "PostToolUse" or tool_name != "Task":
        sys.exit(0)

    # Check if this is a docs-researcher agent
    tool_input = input_data.get("tool_input", {})
    subagent_type = tool_input.get("subagent_type", "")

    if subagent_type.lower() != "docs-researcher":
        sys.exit(0)

    # Create flag file to track that docs-researcher is active
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if claude_project_dir:
        create_flag(Path(claude_project_dir), DOCS_RESEARCHER_FLAG)

    sys.exit(0)


if __name__ == "__main__":
    main()

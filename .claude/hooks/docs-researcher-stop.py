#!/usr/bin/env python3
"""
Docs Researcher Stop Hook - SubagentStop

Blocks docs-researcher agent from stopping if it hasn't used the Write tool.
Configurable via docs_researcher_write_required in config.yaml (default: true).
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import get_project_config


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    hook_event = input_data.get("hook_event_name", "")
    if hook_event != "SubagentStop":
        sys.exit(0)

    # Check if enabled in config
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if claude_project_dir:
        config = get_project_config(Path(claude_project_dir))
        if not config.get('docs_researcher_write_required', True):
            sys.exit(0)

    # Check if this is docs-researcher by reading the transcript
    transcript_path = input_data.get("transcript_path", "")
    if not transcript_path:
        sys.exit(0)

    # Read transcript to find subagent info and tool usage
    try:
        with open(transcript_path, 'r') as f:
            content = f.read()
    except IOError:
        sys.exit(0)

    # Check if this is a docs-researcher subagent
    # The transcript contains the Task tool call with subagent_type
    if '"subagent_type": "docs-researcher"' not in content and '"subagent_type":"docs-researcher"' not in content:
        sys.exit(0)

    # Count Write tool usages in the transcript
    # Look for tool_name: Write patterns in assistant tool calls
    write_count = content.count('"tool_name": "Write"') + content.count('"tool_name":"Write"')

    if write_count == 0:
        output = {
            "decision": "block",
            "reason": (
                "**docs-researcher agent has not written any files.**\n\n"
                "Your job is to create documentation in `.meridian/api-docs/`. "
                "You MUST use Firecrawl to research and then Write to save your findings.\n\n"
                "**Required actions:**\n"
                "1. Use `firecrawl_search` or `firecrawl_scrape` to research the topic\n"
                "2. Use the `Write` tool to save documentation to `.meridian/api-docs/{tool}.md`\n"
                "3. Update `.meridian/api-docs/INDEX.md`\n\n"
                "Do not stop until you have written at least one documentation file."
            )
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()

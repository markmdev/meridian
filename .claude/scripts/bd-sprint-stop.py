#!/usr/bin/env python3
"""
Beads Sprint Stop Script

Removes the Beads Sprint Workflow section from session-context.md.
Called by the /bd-sprint-stop slash command.
"""

import re
import sys
from pathlib import Path


def main():
    # Derive project root from script location: .claude/scripts/ -> project root
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent.parent  # .claude/scripts -> .claude -> project root
    session_context = project_dir / ".meridian" / "session-context.md"

    if not session_context.exists():
        print(f"Error: {session_context} does not exist", file=sys.stderr)
        sys.exit(1)

    content = session_context.read_text()

    # Check if workflow exists
    if "<!-- BEADS SPRINT WORKFLOW" not in content:
        print("No Beads Sprint Workflow found in session-context.md")
        print("Nothing to remove.")
        sys.exit(0)

    # Remove the workflow section (from start marker to end marker, inclusive)
    pattern = r'\n<!-- BEADS SPRINT WORKFLOW - DO NOT DELETE UNTIL COMPLETE -->.*?<!-- END BEADS SPRINT WORKFLOW -->\n?'
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)

    session_context.write_text(new_content)
    print("Beads Sprint Workflow section removed from session-context.md")


if __name__ == "__main__":
    main()

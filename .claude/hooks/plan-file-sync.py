#!/usr/bin/env python3
"""
Plan File Sync Hook - PreToolUse

Tracks the current plan file by reading slug from transcript.
If slug changes (after /clear), copies old plan content to new file.

Uses PreToolUse instead of UserPromptSubmit because the user message
(containing the slug) isn't written to transcript until AFTER
UserPromptSubmit fires.
"""

import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import CURRENT_PLAN_AUTO_FILE, log_hook_output


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if input_data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)

    # Get transcript path
    transcript_path = input_data.get("transcript_path")
    if not transcript_path or not Path(transcript_path).exists():
        sys.exit(0)

    # Read transcript to get current slug from user message
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
        if not lines:
            sys.exit(0)

        # Find last user message with slug
        current_slug = None
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get("type") == "user" and "slug" in entry:
                    current_slug = entry.get("slug")
                    break
            except json.JSONDecodeError:
                continue

        if not current_slug:
            sys.exit(0)
    except IOError:
        sys.exit(0)

    # Get project directory
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)

    # Derive current plan path from slug
    home = Path.home()
    current_plan_path = home / ".claude" / "plans" / f"{current_slug}.md"

    base_dir = Path(claude_project_dir)
    current_plan_file = base_dir / CURRENT_PLAN_AUTO_FILE
    current_plan_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if we have a tracked plan
    if not current_plan_file.exists():
        # First time: just record current path
        current_plan_file.write_text(str(current_plan_path) + "\n")
        sys.exit(0)

    old_plan_path = Path(current_plan_file.read_text().strip())

    # Same path? Nothing to do
    if old_plan_path == current_plan_path:
        sys.exit(0)

    # Slug changed! Copy old plan content to new plan file (overwrite stale content)
    if old_plan_path.exists():
        try:
            content = old_plan_path.read_text()
            current_plan_path.parent.mkdir(parents=True, exist_ok=True)
            current_plan_path.write_text(content)

            # Inject context to inform Claude
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": f"[SYSTEM]: Plan file synced from previous session. Your plan is at: {current_plan_path}"
                }
            }
            log_hook_output(base_dir, "plan-file-sync", output)
        except IOError:
            pass

    # Update current-plan-auto to new path
    current_plan_file.write_text(str(current_plan_path) + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()

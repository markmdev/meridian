#!/usr/bin/env python3
"""
Task File Tracker - PostToolUse Hook

Tracks when agent accesses files in .meridian/tasks/** and saves them
to .active-task-files for injection after compaction.
"""

import json
import os
import sys
from pathlib import Path

ACTIVE_TASK_FILES = ".meridian/.active-task-files"
TASKS_PREFIX = ".meridian/tasks/"


def get_file_path_from_tool(tool_name: str, tool_input: dict) -> str | None:
    """Extract file path from tool input based on tool type."""
    if tool_name == "Read":
        return tool_input.get("file_path")
    elif tool_name == "Write":
        return tool_input.get("file_path")
    elif tool_name == "Edit":
        return tool_input.get("file_path")
    return None


def normalize_path(filepath: str, base_dir: Path) -> str | None:
    """Normalize path to be relative to base_dir, return None if outside."""
    try:
        # Handle absolute paths
        if filepath.startswith('/'):
            abs_path = Path(filepath).resolve()
        else:
            abs_path = (base_dir / filepath).resolve()

        # Check if it's within the project
        try:
            rel_path = abs_path.relative_to(base_dir.resolve())
            return str(rel_path)
        except ValueError:
            return None
    except Exception:
        return None


def is_task_file(rel_path: str) -> bool:
    """Check if the file is in .meridian/tasks/."""
    return rel_path.startswith(TASKS_PREFIX)


def add_to_tracking(base_dir: Path, rel_path: str) -> None:
    """Add file path to tracking file if not already present."""
    tracking_file = base_dir / ACTIVE_TASK_FILES

    # Read existing entries
    existing = set()
    if tracking_file.exists():
        try:
            existing = set(tracking_file.read_text().strip().split('\n'))
            existing.discard('')  # Remove empty strings
        except Exception:
            pass

    # Add if new
    if rel_path not in existing:
        try:
            tracking_file.parent.mkdir(parents=True, exist_ok=True)
            with open(tracking_file, 'a') as f:
                f.write(rel_path + '\n')
        except Exception:
            pass


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Only handle PostToolUse
    if input_data.get("hook_event_name") != "PostToolUse":
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only track Read, Write, Edit
    if tool_name not in ("Read", "Write", "Edit"):
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)
    base_dir = Path(claude_project_dir)

    # Get file path from tool input
    filepath = get_file_path_from_tool(tool_name, tool_input)
    if not filepath:
        sys.exit(0)

    # Normalize to relative path
    rel_path = normalize_path(filepath, base_dir)
    if not rel_path:
        sys.exit(0)

    # Check if it's a task file
    if is_task_file(rel_path):
        add_to_tracking(base_dir, rel_path)

    sys.exit(0)


if __name__ == "__main__":
    main()

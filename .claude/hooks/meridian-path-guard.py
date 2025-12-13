#!/usr/bin/env python3
"""
PermissionRequest Hook - Meridian Path Guard

Blocks attempts to create .meridian or .claude folders or write to these paths
outside the project root directory.
"""

import json
import os
import sys
from pathlib import Path

# Folders that must only exist at project root
GUARDED_FOLDERS = [".meridian", ".claude"]


def normalize_path(path: str, cwd: str) -> Path:
    """Resolve path to absolute, handling relative paths."""
    p = Path(path)
    if not p.is_absolute():
        p = Path(cwd) / p
    try:
        return p.resolve(strict=False)
    except Exception:
        return p.absolute()


def check_guarded_path(target_path: str, project_dir: Path, cwd: str) -> tuple[bool, str]:
    """
    Check if a guarded folder path is valid (under project root).
    Returns (is_valid, error_message).
    """
    resolved = normalize_path(target_path, cwd)
    path_str = str(resolved)

    for folder in GUARDED_FOLDERS:
        pattern = f"/{folder}/"
        pattern_end = f"/{folder}"

        # Check if path contains this guarded folder
        if pattern not in path_str and not path_str.endswith(pattern_end):
            continue

        # Valid path must be under project_dir
        valid_path = project_dir / folder

        try:
            if resolved == valid_path or str(resolved).startswith(str(valid_path) + "/"):
                return True, ""
        except Exception:
            pass

        # Invalid - provide helpful error
        return False, (
            f"Blocked: Attempted to write to {folder} outside project root.\n"
            f"  Target: {resolved}\n"
            f"  Valid path: {valid_path}/\n\n"
            f"Use the correct path under {valid_path}/"
        )

    return True, ""


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Only handle PermissionRequest events
    if input_data.get("hook_event_name") != "PermissionRequest":
        sys.exit(0)

    tool_name = input_data.get("tool_name")
    tool_input = input_data.get("tool_input") or {}

    # Only check Write, Edit, and Bash (for mkdir)
    if tool_name not in {"Write", "Edit", "Bash"}:
        sys.exit(0)

    project_dir_env = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir_env:
        sys.exit(0)

    project_dir = Path(project_dir_env).resolve()
    cwd = input_data.get("cwd", project_dir_env)

    # Gather paths to check
    paths_to_check = []

    if tool_name in {"Write", "Edit"}:
        file_path = tool_input.get("file_path")
        if file_path:
            paths_to_check.append(file_path)

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        # Check for mkdir creating guarded folders
        if "mkdir" in command:
            for folder in GUARDED_FOLDERS:
                if folder in command:
                    parts = command.split()
                    for part in parts:
                        if folder in part:
                            paths_to_check.append(part)

    # Check each path
    for path in paths_to_check:
        is_valid, error = check_guarded_path(path, project_dir, cwd)
        if not is_valid:
            output = {
                "decision": "block",
                "reason": error
            }
            print(json.dumps(output))
            sys.exit(0)

    # Allow if no issues found
    sys.exit(0)


if __name__ == "__main__":
    main()

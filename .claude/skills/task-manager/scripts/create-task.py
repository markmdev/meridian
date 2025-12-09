#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path


class WorkflowError(Exception):
    """Generic error for workflow operations."""


def get_project_root() -> Path:
    """Get the project root directory using CLAUDE_PROJECT_DIR."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir:
        raise EnvironmentError("CLAUDE_PROJECT_DIR environment variable is not set")
    return Path(project_dir)


def get_next_task_id() -> str:
    """Determine the next available task ID."""
    root = get_project_root()
    tasks_dir = root / ".meridian" / "tasks"

    if not tasks_dir.exists():
        raise FileNotFoundError(f"Tasks directory not found: {tasks_dir}")

    # Find all existing task IDs
    task_ids = []
    for item in tasks_dir.iterdir():
        if item.is_dir() and item.name.startswith("TASK-"):
            match = re.match(r"TASK-(\d+)$", item.name)
            if match:
                task_ids.append(int(match.group(1)))

    # Return next ID
    if not task_ids:
        return "TASK-001"

    next_id = max(task_ids) + 1
    return f"TASK-{next_id:03d}"


def rename_template_files(dest_dir: Path, task_id: str) -> None:
    """
    After copying the template, rename any MD files that include 'TASK-000'
    so they instead include the concrete task_id (e.g., TASK-012).
    """
    if not dest_dir.exists():
        raise FileNotFoundError(f"Destination dir does not exist: {dest_dir}")

    exts = {".md"}

    for path in dest_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in exts:
            continue

        name = path.name
        if "TASK-000" not in name:
            continue

        new_name = name.replace("TASK-000", task_id)
        new_path = path.with_name(new_name)

        if new_path.exists():
            raise WorkflowError(
                f"Cannot rename '{path.relative_to(dest_dir)}' to '{new_name}': target already exists."
            )

        try:
            path.rename(new_path)
        except PermissionError as e:
            raise WorkflowError(
                f"Permission denied while renaming '{path}' to '{new_path}'."
            ) from e
        except OSError as e:
            raise WorkflowError(
                f"Failed to rename '{path}' to '{new_path}': {e}"
            ) from e


def create_task_from_template() -> Path:
    """
    Create a new task directory under .meridian/tasks by copying the TASK-000-template.
    Then rename context.md to include the new task id instead of TASK-000.
    Returns the path to the created task directory.

    Raises detailed exceptions if anything goes wrong.
    """
    root = get_project_root()
    tasks_dir = root / ".meridian" / "tasks"
    if not tasks_dir.exists():
        raise FileNotFoundError(
            f"Tasks directory not found at '{tasks_dir}'. "
            "Please ensure '.meridian/tasks/' exists."
        )

    template_dir = tasks_dir / "TASK-000-template"
    if not template_dir.exists() or not template_dir.is_dir():
        raise FileNotFoundError(
            f"Template directory not found at '{template_dir}'. "
            "Please create a 'TASK-000-template' folder with the desired contents."
        )

    task_id = get_next_task_id()
    dest_dir = tasks_dir / task_id

    if dest_dir.exists():
        raise FileExistsError(
            f"Destination task directory already exists: '{dest_dir}'. "
            "This should not happen if IDs are generated correctly."
        )

    try:
        # copytree will fail if dest exists; that’s desired.
        shutil.copytree(src=template_dir, dst=dest_dir)
    except PermissionError as e:
        raise WorkflowError(
            f"Permission denied while copying template to '{dest_dir}'. "
            "Check directory permissions."
        ) from e
    except OSError as e:
        raise WorkflowError(
            f"Failed to copy template from '{template_dir}' to '{dest_dir}': {e}"
        ) from e

    # Rename YAML/MD files that still include the placeholder in their filenames.
    rename_template_files(dest_dir, task_id)

    return dest_dir


def main() -> None:
    try:
        new_task_dir = create_task_from_template()
        print(f"Task created: {new_task_dir.name}")
        print(f"Path: {new_task_dir}")
        print()
        print("Next steps:")
        print(f"1. Copy your plan from ~/.claude/plans/ to {new_task_dir}/")
        print(f"2. Fill in {new_task_dir.name}-context.md with task details")
        print("3. Update .meridian/task-backlog.yaml with the new task")
    except Exception as e:
        # Provide a clear, actionable error message and non-zero exit code
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

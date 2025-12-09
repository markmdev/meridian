#!/usr/bin/env python3
"""
Prune completed/done tasks so only the 10 newest remain in the active backlog.

Older completed tasks are moved to:
  - .meridian/task-backlog-archive.yaml
  - .meridian/tasks/archive/<task-folder>/

Tasks that are not in completed/done states are untouched.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - fallback parser handles runtime
    yaml = None

MAX_COMPLETED_TO_KEEP = 10
COMPLETED_STATUSES = {"done", "completed"}

BACKLOG_HEADER = [
    "# Task Backlog",
    "# Simple index of tasks - detailed definitions live in .meridian/tasks/TASK-###/",
    "",
    "tasks:",
]

ARCHIVE_HEADER = [
    "# Archived completed or done tasks (oldest first)",
    "# Generated automatically. Do not edit by hand.",
    "",
    "tasks:",
]


class PruneResult:
    def __init__(self, archived_ids: list[str], kept_ids: list[str]) -> None:
        self.archived_ids = archived_ids
        self.kept_ids = kept_ids

    @property
    def archived_count(self) -> int:
        return len(self.archived_ids)


def _simple_parse_tasks(text: str) -> List[dict]:
    tasks: List[dict] = []
    current: dict | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("tasks"):
            # Skip the "tasks:" header
            continue

        if line.startswith("- "):
            if current:
                tasks.append(current)
            current = {}
            line = line[2:].strip()
            if line:
                key, _, value = line.partition(":")
                current[key.strip()] = _parse_value(value)
            continue

        if ":" in line and current is not None:
            key, _, value = line.partition(":")
            current[key.strip()] = _parse_value(value)

    if current:
        tasks.append(current)

    return tasks


def _parse_value(raw: str) -> str | int | float | bool:
    value = raw.strip()
    if not value:
        return ""

    if value.startswith(("'", '"')) and value.endswith(value[0]):
        value = value[1:-1]

    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _format_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def _format_task(task: dict) -> List[str]:
    lines: List[str] = []
    key_order = ["id", "title", "priority", "status", "path", "links"]

    # First line includes id if available
    first_key = "id" if "id" in task else None
    if first_key:
        lines.append(f"  - {first_key}: {_format_value(task[first_key])}")
    else:
        lines.append("  - id: \"\"")

    for key in key_order:
        if key == first_key or key not in task:
            continue
        lines.append(f"    {key}: {_format_value(task[key])}")

    for key in task:
        if key in key_order:
            continue
        lines.append(f"    {key}: {_format_value(task[key])}")

    return lines


def _write_tasks_file(path: Path, tasks: Sequence[dict], header: Sequence[str]) -> None:
    lines = list(header)
    if not lines or not lines[-1].strip().startswith("tasks"):
        lines.append("tasks:")
    for task in tasks:
        lines.extend(_format_task(task))
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _load_tasks_file(path: Path) -> List[dict]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if yaml:
        try:
            data = yaml.safe_load(text) or {}
            tasks = data.get("tasks", [])
            if isinstance(tasks, list):
                return [t for t in tasks if isinstance(t, dict)]
        except Exception:
            pass
    return _simple_parse_tasks(text)


def _status_is_completed(task: dict) -> bool:
    status = task.get("status")
    if not isinstance(status, str):
        return False
    return status.strip().lower() in COMPLETED_STATUSES


def _move_task_folder(base_dir: Path, task: dict) -> None:
    path_value = task.get("path")
    if not isinstance(path_value, str) or not path_value.strip():
        return

    src = Path(path_value)
    if not src.is_absolute():
        src = base_dir / path_value
    src = src.resolve()

    tasks_dir = base_dir / ".meridian" / "tasks"
    archive_dir = tasks_dir / "archive"
    if not src.exists():
        return
    if archive_dir in src.parents:
        return  # Already archived

    destination = archive_dir / src.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    shutil.move(str(src), str(destination))

    relative = destination.relative_to(base_dir)
    task["path"] = f"{relative.as_posix().rstrip('/')}/"


def prune_completed_tasks(base_dir: Path, keep_limit: int = MAX_COMPLETED_TO_KEEP) -> PruneResult:
    backlog_path = base_dir / ".meridian" / "task-backlog.yaml"
    archive_path = base_dir / ".meridian" / "task-backlog-archive.yaml"

    if not backlog_path.exists():
        return PruneResult(archived_ids=[], kept_ids=[])

    tasks = _load_tasks_file(backlog_path)
    completed_indices = [i for i, task in enumerate(tasks) if _status_is_completed(task)]

    if len(completed_indices) <= keep_limit:
        kept_ids = [tasks[i].get("id", "") or "" for i in completed_indices]
        return PruneResult(archived_ids=[], kept_ids=kept_ids)

    keep_set = set(completed_indices[-keep_limit:])
    archive_indices = [idx for idx in completed_indices if idx not in keep_set]

    archived_tasks = [tasks[idx].copy() for idx in archive_indices]
    remaining_tasks = [task for idx, task in enumerate(tasks) if idx not in archive_indices]

    for task in archived_tasks:
        _move_task_folder(base_dir, task)

    existing_archive_tasks = _load_tasks_file(archive_path)
    updated_archive_tasks = existing_archive_tasks + archived_tasks

    _write_tasks_file(backlog_path, remaining_tasks, BACKLOG_HEADER)
    _write_tasks_file(archive_path, updated_archive_tasks, ARCHIVE_HEADER)

    archived_ids = [task.get("id", "") or "" for task in archived_tasks]
    kept_ids = [task.get("id", "") or "" for idx, task in enumerate(tasks) if idx in keep_set]

    return PruneResult(archived_ids=archived_ids, kept_ids=kept_ids)


def main() -> int:
    project_dir_env = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir_env:
        print(json.dumps({"error": "CLAUDE_PROJECT_DIR not set"}))
        return 1
    project_dir = Path(project_dir_env)
    result = prune_completed_tasks(project_dir)
    print(json.dumps({"archivedTasks": result.archived_count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


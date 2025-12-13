#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from typing import Iterable

MERIDIAN_DIR = ".meridian"
TASK_BACKLOG = f"{MERIDIAN_DIR}/task-backlog.yaml"
MEMORY_FILE = f"{MERIDIAN_DIR}/memory.jsonl"
TASKS_DIR = f"{MERIDIAN_DIR}/tasks"

SKILL_WHITELIST = {"memory-curator", "task-manager", "planning", "claudemd-writer"}
BASH_SUBSTRINGS = {"add_memory_entry.py", "create-task.py"}

ALLOWED_ACTIONS = {
    "Write": {"files": [TASK_BACKLOG, MEMORY_FILE], "dirs": [TASKS_DIR]},
    "Edit": {"files": [TASK_BACKLOG, MEMORY_FILE], "dirs": [TASKS_DIR]},
    "Read": {"files": [TASK_BACKLOG, MEMORY_FILE], "dirs": [TASKS_DIR]},
    "Grep": {"files": [TASK_BACKLOG, MEMORY_FILE], "dirs": [TASKS_DIR]},
    "Glob": {"files": [MEMORY_FILE], "dirs": []},
}


def normalize_path(path: str, base_dir: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    try:
        return candidate.resolve(strict=False)
    except Exception:
        return candidate.absolute()


def is_path_allowed(target: str, allowed_files: Iterable[str], allowed_dirs: Iterable[str], base_dir: Path) -> bool:
    if not target:
        return False

    target_path = normalize_path(target, base_dir)

    for rel in allowed_files:
        if target_path == normalize_path(rel, base_dir):
            return True

    for rel in allowed_dirs:
        allowed_dir = normalize_path(rel, base_dir)
        try:
            if target_path == allowed_dir or target_path.is_relative_to(allowed_dir):
                return True
        except AttributeError:
            allowed_str = str(allowed_dir)
            target_str = str(target_path)
            if target_str == allowed_str or target_str.startswith(f"{allowed_str}{os.sep}"):
                return True

    return False


def gather_paths(tool_input: dict) -> list[str]:
    targets: list[str] = []
    for key in ("file_path", "target_file", "path", "paths"):
        value = tool_input.get(key)
        if isinstance(value, str):
            targets.append(value)
        elif isinstance(value, list):
            targets.extend(str(item) for item in value if item)
    return targets


def is_glob_allowed(tool_input: dict, base_dir: Path) -> bool:
    pattern = tool_input.get("glob_pattern", "")
    target_directory = tool_input.get("target_directory")

    memory_abs = normalize_path(MEMORY_FILE, base_dir)

    if target_directory:
        dir_path = normalize_path(target_directory, base_dir)
        combination = dir_path / Path(pattern)
        try:
            if combination.resolve(strict=False) == memory_abs:
                return True
        except Exception:
            pass

    if MEMORY_FILE in pattern or Path(pattern).name == Path(MEMORY_FILE).name:
        return True

    if isinstance(tool_input.get("paths"), list):
        for candidate in tool_input["paths"]:
            if is_path_allowed(str(candidate), ALLOWED_ACTIONS["Glob"]["files"], [], base_dir):
                return True

    return False


def should_allow(data: dict, project_dir: Path) -> bool:
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input") or {}
    if not tool_name:
        return False

    base_dir = project_dir

    if tool_name in {"Write", "Edit", "Read", "Grep"}:
        allowed = ALLOWED_ACTIONS[tool_name]
        paths = gather_paths(tool_input)
        if not paths:
            return False
        return all(is_path_allowed(p, allowed["files"], allowed["dirs"], base_dir) for p in paths)

    if tool_name == "Glob":
        return is_glob_allowed(tool_input, base_dir)

    if tool_name == "Skill":
        return tool_input.get("skill") in SKILL_WHITELIST

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if any(substr in command for substr in BASH_SUBSTRINGS):
            return True
        # Allow cp from ~/.claude/plans/ (plan archival)
        if command.strip().startswith("cp "):
            home = str(Path.home())
            if "/.claude/plans/" in command or f"{home}/.claude/plans/" in command:
                return True
        return False

    return False


def main():
    try:
        raw_input = sys.stdin.read()
    except Exception:
        return

    project_dir_env = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir_env:
        return  # Can't auto-approve without knowing project dir
    project_dir = Path(project_dir_env)

    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError:
        return

    if should_allow(payload, project_dir):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {"behavior": "allow"},
            }
        }
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

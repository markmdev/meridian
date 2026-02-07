#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


SKILL_WHITELIST = {"planning", "claudemd-writer"}
BASH_SUBSTRINGS = {"setup-work-until.sh"}


def gather_paths(tool_input: dict) -> list[str]:
    targets: list[str] = []
    for key in ("file_path", "target_file", "path", "paths"):
        value = tool_input.get(key)
        if isinstance(value, str):
            targets.append(value)
        elif isinstance(value, list):
            targets.extend(str(item) for item in value if item)
    return targets


def is_plans_path(path: str) -> bool:
    """Check if path contains .claude/plans/ anywhere."""
    return ".claude/plans/" in path or ".claude/plans" in path


def should_allow(data: dict, project_dir: Path) -> bool:
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input") or {}
    if not tool_name:
        return False

    # Auto-approve Write/Edit to any .claude/plans/ path
    if tool_name in {"Write", "Edit"}:
        paths = gather_paths(tool_input)
        if paths and all(is_plans_path(p) for p in paths):
            return True

    if tool_name == "Skill":
        return tool_input.get("skill") in SKILL_WHITELIST

    if tool_name == "Bash":
        command = tool_input.get("command", "").strip()
        if any(substr in command for substr in BASH_SUBSTRINGS):
            return True
        # Allow Pebble CLI commands (pb)
        if command.startswith("pb ") or command == "pb":
            return True
        # Allow cp from ~/.claude/plans/ (plan archival)
        if command.startswith("cp "):
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

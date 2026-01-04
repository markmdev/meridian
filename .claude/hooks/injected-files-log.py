#!/usr/bin/env python3
"""
Injected Files Log - SessionStart Hook

Logs all files that are injected into context to .meridian/.injected-files.
Runs on startup, compact, and clear.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    get_project_config,
    get_in_progress_tasks,
    SESSION_CONTEXT_FILE,
)


def get_injected_file_paths(base_dir: Path) -> list[str]:
    """Get list of all files that will be injected into context."""
    files = []

    # 1. Memory
    memory_path = base_dir / ".meridian" / "memory.jsonl"
    if memory_path.exists():
        files.append(".meridian/memory.jsonl")

    # 2. Task backlog
    backlog_path = base_dir / ".meridian" / "task-backlog.yaml"
    if backlog_path.exists():
        files.append(".meridian/task-backlog.yaml")

    # 3. Session context
    session_context_path = base_dir / SESSION_CONTEXT_FILE
    if session_context_path.exists():
        files.append(SESSION_CONTEXT_FILE)

    # 4. Plan files from task-backlog
    in_progress_tasks = get_in_progress_tasks(base_dir)
    for task in in_progress_tasks:
        plan_path = task.get('plan_path', '')
        if plan_path:
            if plan_path.startswith('/'):
                full_path = Path(plan_path)
            else:
                full_path = base_dir / plan_path
            if full_path.exists():
                files.append(plan_path)

    # 4b. Active plan (for Beads workflows)
    active_plan_file = base_dir / ".meridian" / ".active-plan"
    if active_plan_file.exists():
        try:
            plan_path = active_plan_file.read_text().strip()
            if plan_path:
                if plan_path.startswith('/'):
                    full_path = Path(plan_path)
                else:
                    full_path = base_dir / plan_path
                if full_path.exists() and plan_path not in files:
                    files.append(plan_path)
        except IOError:
            pass

    # 5. CODE_GUIDE
    code_guide_path = base_dir / ".meridian" / "CODE_GUIDE.md"
    if code_guide_path.exists():
        files.append(".meridian/CODE_GUIDE.md")

    # 5b. CODE_GUIDE addons
    project_config = get_project_config(base_dir)
    if project_config['project_type'] == 'hackathon':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_HACKATHON.md"
        if addon_path.exists():
            files.append(".meridian/CODE_GUIDE_ADDON_HACKATHON.md")
    elif project_config['project_type'] == 'production':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_PRODUCTION.md"
        if addon_path.exists():
            files.append(".meridian/CODE_GUIDE_ADDON_PRODUCTION.md")

    # 6. BEADS_GUIDE (if enabled)
    if project_config.get('beads_enabled', False):
        beads_guide_path = base_dir / ".meridian" / "BEADS_GUIDE.md"
        if beads_guide_path.exists():
            files.append(".meridian/BEADS_GUIDE.md")

    # Note: agent-operating-manual.md is excluded - not needed for reviewer agents

    return files


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if input_data.get("hook_event_name") != "SessionStart":
        sys.exit(0)

    source = input_data.get("source", "startup")

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)

    base_dir = Path(claude_project_dir)

    # Get list of injected files
    injected_files = get_injected_file_paths(base_dir)

    # Get beads_enabled setting
    project_config = get_project_config(base_dir)
    beads_enabled = project_config.get('beads_enabled', False)

    # Write to log file
    log_file = base_dir / ".meridian" / ".injected-files"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"# Injected files ({source}) - {timestamp}\n"
        content += f"beads_enabled: {str(beads_enabled).lower()}\n"
        content += f"git_comparison: HEAD\n"  # Default: uncommitted changes
        content += "\n"
        for f in injected_files:
            content += f"{f}\n"
        log_file.write_text(content)
    except IOError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Injected Files Log - SessionStart Hook

Logs all files that are injected into context.
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
    parse_yaml_list,
    SESSION_CONTEXT_FILE,
    REQUIRED_CONTEXT_CONFIG,
    ACTIVE_PLAN_FILE,
    INJECTED_FILES_LOG,
)


def get_injected_file_paths(base_dir: Path) -> list[str]:
    """Get list of all files that will be injected into context (absolute paths)."""
    files = []

    # 1. Memory
    memory_path = base_dir / ".meridian" / "memory.jsonl"
    if memory_path.exists():
        files.append(str(memory_path))

    # 2. User-provided docs
    config_path = base_dir / REQUIRED_CONTEXT_CONFIG
    if config_path.exists():
        try:
            content = config_path.read_text()
            user_docs = parse_yaml_list(content, 'user_provided_docs')
            for doc_path in user_docs:
                full_path = base_dir / doc_path
                if full_path.exists():
                    files.append(str(full_path))
        except IOError:
            pass

    # 3. Session context
    session_context_path = base_dir / SESSION_CONTEXT_FILE
    if session_context_path.exists():
        files.append(str(session_context_path))

    # 4. Active plan
    active_plan_file = base_dir / ACTIVE_PLAN_FILE
    if active_plan_file.exists():
        try:
            plan_path = active_plan_file.read_text().strip()
            if plan_path:
                if plan_path.startswith('/'):
                    full_path = Path(plan_path)
                else:
                    full_path = base_dir / plan_path
                if full_path.exists() and str(full_path) not in files:
                    files.append(str(full_path))
        except IOError:
            pass

    # 5. CODE_GUIDE
    code_guide_path = base_dir / ".meridian" / "CODE_GUIDE.md"
    if code_guide_path.exists():
        files.append(str(code_guide_path))

    # 5b. CODE_GUIDE addons
    project_config = get_project_config(base_dir)
    if project_config['project_type'] == 'hackathon':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_HACKATHON.md"
        if addon_path.exists():
            files.append(str(addon_path))
    elif project_config['project_type'] == 'production':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_PRODUCTION.md"
        if addon_path.exists():
            files.append(str(addon_path))

    # 6. PEBBLE_GUIDE (if enabled)
    if project_config.get('pebble_enabled', False):
        pebble_guide_path = base_dir / ".meridian" / "PEBBLE_GUIDE.md"
        if pebble_guide_path.exists():
            files.append(str(pebble_guide_path))

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

    # Get pebble_enabled setting
    project_config = get_project_config(base_dir)
    pebble_enabled = project_config.get('pebble_enabled', False)

    # Write to log file
    log_file = base_dir / INJECTED_FILES_LOG
    log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"# Injected files ({source}) - {timestamp}\n"
        content += f"pebble_enabled: {str(pebble_enabled).lower()}\n"
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

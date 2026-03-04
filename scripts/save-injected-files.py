#!/usr/bin/env python3
"""
Save Injected Files — SessionStart Hook

Saves the list of files injected into context to ~/.meridian/state/<hash>/injected-files.
Agents read this file to know what context is available.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import (
    get_project_config,
    get_extra_doc_dirs,
    is_headless,
    scan_docs_directory,
    state_path,
    WORKSPACE_FILE,
    INJECTED_FILES_LOG,
)


def get_injected_file_paths(base_dir: Path, project_config: dict) -> list[str]:
    """Get list of all files that will be injected into context (absolute paths)."""
    files = []

    # Workspace
    workspace_path = base_dir / WORKSPACE_FILE
    if workspace_path.exists():
        files.append(str(workspace_path))

    # CODE_GUIDE
    code_guide_path = base_dir / ".meridian" / "docs" / "code-guide.md"
    if code_guide_path.exists():
        files.append(str(code_guide_path))

    # Note: agent-operating-manual.md is excluded - not needed for reviewer agents

    # Docs index — scan .meridian/docs/ and .meridian/api-docs/ for frontmatter'd files
    # Write to a state file so subagents can discover available docs
    doc_scan_dirs = [".meridian/docs", ".meridian/api-docs"]
    for path, _header in get_extra_doc_dirs(project_config):
        doc_scan_dirs.append(path)

    docs_index_parts = []
    for dir_rel in doc_scan_dirs:
        listing = scan_docs_directory(base_dir / dir_rel, base_dir)
        if listing:
            docs_index_parts.append(f"## {dir_rel}")
            docs_index_parts.append(listing)
            docs_index_parts.append("")

    if docs_index_parts:
        docs_index_file = state_path(base_dir, "docs-index")
        try:
            docs_index_file.parent.mkdir(parents=True, exist_ok=True)
            docs_index_file.write_text("\n".join(docs_index_parts))
            files.append(str(docs_index_file))
        except IOError:
            pass

    return files


def main():
    if is_headless():
        sys.exit(0)

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

    # Get config and list of injected files
    project_config = get_project_config(base_dir)
    injected_files = get_injected_file_paths(base_dir, project_config)
    pebble_enabled = project_config.get('pebble_enabled', False)

    # Write to log file
    log_file = state_path(base_dir, INJECTED_FILES_LOG)
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

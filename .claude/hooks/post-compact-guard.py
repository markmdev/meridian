#!/usr/bin/env python3
"""
Smart Context Guard - PreToolUse Hook

Ensures required context files are read before allowing other tools.
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import PENDING_READS_FILE


def normalize_path(path: str) -> str:
    """Normalize a path for comparison."""
    try:
        return str(Path(path).resolve())
    except Exception:
        return path


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    if input_data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)

    cwd = input_data.get("cwd", os.getcwd())
    pending_path = Path(cwd) / PENDING_READS_FILE

    # No pending reads file = allow everything
    if not pending_path.exists():
        sys.exit(0)

    # Load pending files
    try:
        pending_files = json.loads(pending_path.read_text())
        if not isinstance(pending_files, list):
            pending_files = []
    except (json.JSONDecodeError, IOError):
        pending_files = []

    # Empty list = clean up and allow
    if not pending_files:
        try:
            pending_path.unlink()
        except Exception:
            pass
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Handle Read tool specially
    if tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        normalized_target = normalize_path(file_path)

        remaining = []
        found = False
        for pending_file in pending_files:
            if normalize_path(pending_file) == normalized_target:
                found = True
            else:
                remaining.append(pending_file)

        if found:
            if remaining:
                pending_path.write_text(json.dumps(remaining))
            else:
                try:
                    pending_path.unlink()
                except Exception:
                    pass
            sys.exit(0)  # Allow this Read

    # Block: not a Read or Read for non-pending file
    file_list = "\n".join(f"- `{f}`" for f in pending_files)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "**CONTEXT REVIEW REQUIRED**\n\n"
                "You must read all required context files before using other tools.\n\n"
                f"**Remaining files to read ({len(pending_files)}):**\n{file_list}\n\n"
                "Use the Read tool to read these files, then you may continue."
            )
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Context Injector — SessionStart Hook

Injects project context (workspace, code guide, plans, file tree) into the
conversation via additionalContext. Triggers on: startup, compact, clear.
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import (
    LAST_SESSION_FILE,
    TRANSCRIPT_PATH_STATE,
    build_injected_context,
    is_headless,
    log_hook_output,
    get_state_dir,
    state_path,
)


def main() -> int:
    if is_headless():
        return 0

    # Read input to get session info
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    source = input_data.get("source", "startup")

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    base_dir = Path(claude_project_dir)

    # Build the injected context (reads last-session.md among other files)
    injected_context, injection_meta = build_injected_context(base_dir)

    # Delete last-session.md after reading — we own its lifecycle now
    # (session-cleanup can't do it because hooks run in parallel = race condition)
    last_session = state_path(base_dir, LAST_SESSION_FILE)
    try:
        if last_session.exists():
            last_session.unlink()
    except OSError:
        pass

    # Save to state for debugging/inspection and session-learner
    sd = get_state_dir(base_dir)
    try:
        (sd / "injected-context").write_text(injected_context)
    except IOError:
        pass

    # Save transcript path so session-learner can find it after /clear
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            (sd / TRANSCRIPT_PATH_STATE).write_text(transcript_path)
        except IOError:
            pass

    # Build concise systemMessage from injection metadata
    labels = []
    if injection_meta.get("workspace"):
        labels.append("workspace")
    if injection_meta.get("docs"):
        count = injection_meta["docs"]
        labels.append(f"{count} doc{'s' if count != 1 else ''}")
    if injection_meta.get("api_docs"):
        count = injection_meta["api_docs"]
        labels.append(f"{count} api-doc{'s' if count != 1 else ''}")
    if injection_meta.get("last_session"):
        labels.append("last session")
    if injection_meta.get("plan"):
        labels.append("plan")
    if injection_meta.get("pebble"):
        labels.append("pebble")
    if injection_meta.get("manual"):
        labels.append("manual")
    if injection_meta.get("soul"):
        labels.append("soul")
    if injection_meta.get("nested_repos"):
        count = injection_meta["nested_repos"]
        labels.append(f"{count} nested repo{'s' if count != 1 else ''}")

    error_count = len(injection_meta.get("errors", []))
    error_suffix = "No errors" if error_count == 0 else f"{error_count} error{'s' if error_count != 1 else ''}"
    system_msg = f"Meridian: {' \u00b7 '.join(labels)} | {error_suffix}" if labels else f"Meridian: (nothing injected) | {error_suffix}"

    # Output JSON with additionalContext
    output = {
        "systemMessage": system_msg,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": injected_context
        }
    }

    log_hook_output(base_dir, "context-injector", output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

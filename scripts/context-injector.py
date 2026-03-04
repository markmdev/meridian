#!/usr/bin/env python3
"""
Context Injector — SessionStart Hook

Injects project context (workspace, docs, git state, Pebble) into the
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

    # Output JSON with additionalContext
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": injected_context
        }
    }

    log_hook_output(base_dir, "context-injector", output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

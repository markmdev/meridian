#!/usr/bin/env python3
"""
Context Injector — SessionStart Hook

Injects project context (workspace, code guide, plans, file tree) into the
conversation via additionalContext. Triggers on: startup, compact, clear.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import (
    build_injected_context,
    log_hook_output,
    get_state_dir,
    state_path,
)

SYNC_LOCK = "workspace-sync.lock"
SYNC_WAIT_TIMEOUT = 190  # slightly longer than session-learner's 180s timeout


def wait_for_session_learner(base_dir: Path, source: str) -> None:
    """On compact/clear, wait for session-learner to finish updating workspace."""
    if source not in ("compact", "clear"):
        return
    lock_path = state_path(base_dir, SYNC_LOCK)

    # Hooks run in parallel — session-learner may not have created the lock yet.
    # Wait briefly for it to appear before giving up.
    appear_deadline = time.time() + 5
    while not lock_path.exists() and time.time() < appear_deadline:
        time.sleep(0.2)

    if not lock_path.exists():
        return  # session-learner not running or already finished

    # Lock exists — wait for session-learner to release it
    deadline = time.time() + SYNC_WAIT_TIMEOUT
    while lock_path.exists() and time.time() < deadline:
        time.sleep(0.5)


def main() -> int:
    # Read input to get session info
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    source = input_data.get("source", "startup")

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    base_dir = Path(claude_project_dir)

    # Wait for session-learner to finish updating workspace before injecting
    wait_for_session_learner(base_dir, source)

    # Build the injected context
    injected_context = build_injected_context(base_dir)

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
            (sd / "transcript-path").write_text(transcript_path)
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

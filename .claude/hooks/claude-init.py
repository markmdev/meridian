#!/usr/bin/env python3
"""
Claude Init Hook - Session Start

Injects project context directly into the conversation via additionalContext.
Triggers on: startup, resume, clear
"""

import json
import os
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    build_injected_context,
    cleanup_flag,
    create_flag,
    PRE_COMPACTION_FLAG,
    CONTEXT_ACK_FLAG,
    STATE_DIR,
)


def main() -> int:
    # Read input to get session info
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    source = input_data.get("source", "startup")

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    base_dir = Path(claude_project_dir)

    # Build the injected context
    injected_context = build_injected_context(base_dir)

    # Save to state for debugging/inspection and workspace-sync
    state_dir = base_dir / STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    try:
        (state_dir / "injected-context").write_text(injected_context)
    except IOError:
        pass

    # Save transcript path so workspace-sync can find it after /clear
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            (state_dir / "transcript-path").write_text(transcript_path)
        except IOError:
            pass

    # Output JSON with additionalContext
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": injected_context
        }
    }

    print(json.dumps(output))

    # Clean up old flags
    cleanup_flag(base_dir, PRE_COMPACTION_FLAG)

    # Create acknowledgment flag - will be checked by post-compact-guard
    create_flag(base_dir, CONTEXT_ACK_FLAG)

    return 0


if __name__ == "__main__":
    sys.exit(main())

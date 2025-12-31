#!/usr/bin/env python3
"""
Pre-Compaction Context Sync Hook

Prompts agent to save context before conversation compacts (based on token usage).
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    get_project_config,
    flag_exists,
    create_flag,
    cleanup_flag,
    PRE_COMPACTION_FLAG,
)

LOG_FILE = ".meridian/.pre-compaction-sync.log"


def log_calculation(base_dir: Path, request_id: str, usage: dict, total: int,
                    threshold: int, triggered: bool, error: str = None) -> None:
    """Append a log entry for debugging token calculations."""
    log_path = base_dir / LOG_FILE
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {
            "timestamp": timestamp,
            "request_id": request_id,
            "usage": usage,
            "total_calculated": total,
            "threshold": threshold,
            "triggered": triggered,
        }
        if error:
            entry["error"] = error
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Don't fail the hook if logging fails


def get_total_tokens(transcript_path: str, base_dir: Path, threshold: int) -> int:
    """Read the last entry from transcript and sum token usage."""
    if not transcript_path:
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, "no transcript_path")
        return 0

    path = Path(transcript_path)
    if not path.exists():
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, f"transcript not found: {transcript_path}")
        return 0

    try:
        # Read last line of JSONL file
        last_line = ""
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    last_line = line.strip()

        if not last_line:
            log_calculation(base_dir, "N/A", {}, 0, threshold, False, "empty transcript")
            return 0

        entry = json.loads(last_line)
        request_id = entry.get("requestId", "unknown")
        usage = entry.get("message", {}).get("usage", {})

        # Sum token fields (cache_creation.ephemeral_* duplicates cache_creation_input_tokens)
        total = 0
        total += usage.get("input_tokens", 0)
        total += usage.get("cache_creation_input_tokens", 0)
        total += usage.get("cache_read_input_tokens", 0)
        total += usage.get("output_tokens", 0)

        triggered = total >= threshold
        log_calculation(base_dir, request_id, usage, total, threshold, triggered)

        return total
    except (json.JSONDecodeError, IOError, KeyError) as e:
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, f"parse error: {type(e).__name__}: {e}")
        return 0


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    if input_data.get("hook_event_name") != "PreToolUse":
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)  # Can't operate without project dir
    base_dir = Path(claude_project_dir)

    # Check if enabled in config
    config = get_project_config(base_dir)
    if not config['pre_compaction_sync_enabled']:
        sys.exit(0)

    # Always calculate and log tokens (for debugging)
    transcript_path = input_data.get("transcript_path", "")
    threshold = config['pre_compaction_sync_threshold']
    already_synced = flag_exists(base_dir, PRE_COMPACTION_FLAG)
    total_tokens = get_total_tokens(transcript_path, base_dir, threshold)

    # Already synced this session: allow (fires only once per session)
    if already_synced:
        sys.exit(0)

    # Under threshold: allow without creating flag
    if total_tokens < threshold:
        sys.exit(0)

    # Over threshold: create flag and block
    create_flag(base_dir, PRE_COMPACTION_FLAG)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"**CONTEXT PRESERVATION REQUIRED** (Token usage: {total_tokens:,} / {threshold:,})\n\n"
                "The conversation is approaching compaction. Before continuing, you MUST save your current work "
                "to preserve context for the agent that will continue after compaction.\n\n"
                "**Append a dated entry to the session context file**:\n"
                f"`{claude_project_dir}/.meridian/session-context.md`\n\n"
                "Include:\n"
                "- Key decisions made this session and their rationale\n"
                "- Important discoveries or blockers encountered\n"
                "- Complex problems solved (and how)\n"
                "- What needs to be done next\n"
                "- Context that would be hard to rediscover\n\n"
                "This is a rolling file — oldest entries are automatically trimmed. "
                "After updating, you may continue your work."
            )
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

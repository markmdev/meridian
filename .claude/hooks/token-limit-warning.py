#!/usr/bin/env python3
"""
Token Limit Warning — PreToolUse Hook

Warns agent when token usage approaches compaction threshold. Prompts to save
workspace, commit changes, and preserve context before compaction occurs.
"""

import json
import subprocess
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
    log_hook_output,
    PRE_COMPACTION_FLAG,
    PLAN_MODE_STATE,
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
    """Read the transcript and find the most recent entry with usage data."""
    if not transcript_path:
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, "no transcript_path")
        return 0

    path = Path(transcript_path)
    if not path.exists():
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, f"transcript not found: {transcript_path}")
        return 0

    try:
        # Read all lines and search backwards for one with usage data
        lines = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    lines.append(line.strip())

        if not lines:
            log_calculation(base_dir, "N/A", {}, 0, threshold, False, "empty transcript")
            return 0

        # Search backwards for an entry with message.usage
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                usage = entry.get("message", {}).get("usage", {})
                if usage:  # Found an entry with usage data
                    request_id = entry.get("requestId", "unknown")
                    total = 0
                    total += usage.get("input_tokens", 0)
                    total += usage.get("cache_creation_input_tokens", 0)
                    total += usage.get("cache_read_input_tokens", 0)
                    total += usage.get("output_tokens", 0)

                    triggered = total >= threshold
                    log_calculation(base_dir, request_id, usage, total, threshold, triggered)
                    return total
            except json.JSONDecodeError:
                continue

        # No entry with usage found
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, "no entry with usage data found")
        return 0
    except IOError as e:
        log_calculation(base_dir, "N/A", {}, 0, threshold, False, f"read error: {type(e).__name__}: {e}")
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

    # Allow writes to .meridian or .claude folders (these ARE the context-saving actions)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    if tool_name in {"Write", "Edit"}:
        file_path = tool_input.get("file_path", "")
        if "/.meridian/" in file_path or "/.claude/" in file_path:
            sys.exit(0)  # Allow without blocking

    # Over threshold: create flag and block
    create_flag(base_dir, PRE_COMPACTION_FLAG)

    # Check if in plan mode
    plan_mode_file = base_dir / PLAN_MODE_STATE
    in_plan_mode = plan_mode_file.exists() and plan_mode_file.read_text().strip() == "plan"

    # Build minimal prompt - trust SOUL.md for the details
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    parts = [
        f"**CONTEXT PRESERVATION** (Tokens: {total_tokens:,} / {threshold:,}) — {now}\n",
        "Conversation approaching compaction. Save your work now.\n",
    ]

    # Plan mode: capture verbatim requirements
    if in_plan_mode:
        parts.append(
            "**Plan mode**: Update plan's Verbatim Requirements section with user's "
            "exact words and all AskUserQuestion exchanges.\n"
        )

    # Core checklist - agent knows HOW from SOUL.md
    parts.append("**Checklist:**")
    if config.get('pebble_enabled', False):
        parts.append("- Create Pebble issues for any untracked work")

    # Check for uncommitted changes
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            changed_files = len([l for l in result.stdout.strip().split('\n') if l])
            parts.append(f"- Commit {changed_files} uncommitted file{'s' if changed_files != 1 else ''}")
    except Exception:
        pass

    parts.append("")

    # Handle auto_compact_off mode
    if config.get('auto_compact_off', False):
        parts.append(
            "**Then stop**: Write `continue` to `.meridian/.state/restart-signal` and stop immediately."
        )
    else:
        parts.append("Then continue your work.")

    reason = "\n".join(parts)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }

    log_hook_output(base_dir, "token-limit-warning", output)
    sys.exit(0)


if __name__ == "__main__":
    main()

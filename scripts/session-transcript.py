#!/usr/bin/env python3
"""
Session Transcript — SessionEnd + PreCompact Hook

Extracts the user/assistant dialogue from the session transcript (no thinking,
no tool calls, no tool results) and writes it to the state directory as
last-session.md.

On SessionEnd: extracts full post-compaction dialogue for next session injection.
On PreCompact: extracts dialogue since last compact boundary — this gets injected
back via context-injector on SessionStart(compact), restoring pre-compaction context.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import state_path, LAST_SESSION_FILE, TRANSCRIPT_PATH_STATE, is_headless, is_system_noise

if is_headless():
    sys.exit(0)

SESSION_TRANSCRIPT_DEBUG_LOG = "session-transcript-debug.log"


def log(project_dir, msg):
    """Append a debug line to the session-transcript log."""
    try:
        log_path = state_path(project_dir, SESSION_TRANSCRIPT_DEBUG_LOG)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(log_path, "a") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except (IOError, OSError):
        pass


def find_last_compact_boundary(transcript_path: str) -> int:
    """Find the line number of the last compact_boundary entry. Returns -1 if none."""
    last_boundary = -1
    with open(transcript_path) as f:
        for i, line in enumerate(f):
            try:
                entry = json.loads(line)
                if entry.get("type") == "system" and entry.get("subtype") == "compact_boundary":
                    last_boundary = i
            except (json.JSONDecodeError, KeyError):
                continue
    return last_boundary


def extract_dialogue(transcript_path: str, start_after_line: int = -1) -> list[dict]:
    """Extract user and assistant text messages from the transcript.

    Deduplicates streaming assistant entries by requestId (keeps last version).
    Skips thinking blocks, tool calls, tool results, system messages, and
    hook/command injection noise.

    If start_after_line >= 0, only processes entries after that line number.
    """
    raw_entries = []
    assistant_by_request = {}  # requestId -> (index, entry)

    with open(transcript_path) as f:
        for i, line in enumerate(f):
            if i <= start_after_line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = raw.get("type", "")
            msg = raw.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", "")
            request_id = raw.get("requestId")

            # User text (string content)
            if entry_type == "user" and role == "user" and isinstance(content, str) and content.strip():
                if is_system_noise(content):
                    continue
                raw_entries.append({"role": "user", "text": content.strip()})

            # User text (content blocks)
            elif entry_type == "user" and role == "user" and isinstance(content, list):
                if any(b.get("type") == "tool_result" for b in content):
                    continue
                for block in content:
                    if block.get("type") == "text" and block.get("text", "").strip():
                        text = block["text"].strip()
                        if is_system_noise(text):
                            continue
                        raw_entries.append({"role": "user", "text": text})

            # Assistant text (extract only text blocks, skip thinking/tool_use)
            elif entry_type == "assistant" and role == "assistant" and isinstance(content, list):
                text_parts = []
                for block in content:
                    if block.get("type") == "text" and block.get("text", "").strip():
                        text_parts.append(block["text"].strip())

                if text_parts:
                    entry = {"role": "assistant", "text": "\n\n".join(text_parts)}
                    if request_id:
                        if request_id not in assistant_by_request:
                            idx = len(raw_entries)
                            raw_entries.append(None)  # placeholder
                            assistant_by_request[request_id] = (idx, entry)
                        else:
                            idx = assistant_by_request[request_id][0]
                            assistant_by_request[request_id] = (idx, entry)
                    else:
                        raw_entries.append(entry)

    # Fill in deduplicated assistant entries
    for request_id, (idx, entry) in assistant_by_request.items():
        raw_entries[idx] = entry

    return [e for e in raw_entries if e is not None]


def format_dialogue(entries: list[dict]) -> str:
    """Format dialogue entries as clean markdown. Full content preserved."""
    lines = []
    for entry in entries:
        role = entry["role"].capitalize()
        lines.append(f"**{role}:** {entry['text']}\n")

    return "# Last Session\n\n" + "\n".join(lines)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    event_name = input_data.get("hook_event_name", "")
    transcript_path = input_data.get("transcript_path", "")

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")

    if not claude_project_dir:
        # Can't log without project dir — no state path available
        sys.exit(0)

    base_dir = Path(claude_project_dir)

    log(base_dir, f"START event={event_name} transcript={Path(transcript_path).name if transcript_path else 'none'}")

    if event_name not in ("SessionEnd", "PreCompact"):
        log(base_dir, f"SKIP wrong event: {event_name}")
        sys.exit(0)

    # Fall back to saved transcript path if not provided
    if not transcript_path:
        saved = state_path(base_dir, TRANSCRIPT_PATH_STATE)
        if saved.exists():
            transcript_path = saved.read_text().strip()

    if not transcript_path or not Path(transcript_path).exists():
        log(base_dir, f"SKIP no transcript path or file missing: {transcript_path}")
        sys.exit(0)

    # Extract dialogue
    # PreCompact: only extract since last compact boundary (or session start)
    # SessionEnd: extract everything since last compact boundary
    start_after = find_last_compact_boundary(transcript_path)
    entries = extract_dialogue(transcript_path, start_after_line=start_after)
    log(base_dir, f"extracted {len(entries)} dialogue entries (start_after_line={start_after}, event={event_name})")

    if not entries:
        log(base_dir, "SKIP no dialogue entries found")
        sys.exit(0)

    # Write to state directory
    output_path = state_path(base_dir, LAST_SESSION_FILE)
    output_path.write_text(format_dialogue(entries))
    log(base_dir, f"wrote {len(entries)} entries to {output_path}")

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
            log(project_dir, f"CRASH {type(e).__name__}: {e}")
        except Exception:
            pass
        raise

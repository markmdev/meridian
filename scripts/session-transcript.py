#!/usr/bin/env python3
"""
Session Transcript — SessionEnd Hook

Extracts the user/assistant dialogue from the session transcript (no thinking,
no tool calls, no tool results) and writes it to the state directory as
last-session.md. The context injector picks this up at next session start.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from meridian_config import state_path, LAST_SESSION_FILE, TRANSCRIPT_PATH_STATE, is_headless

if is_headless():
    sys.exit(0)

MAX_ENTRY_CHARS = 2000
MAX_DIALOGUE_CHARS = 30000

# Markers that identify system/hook noise rather than real user messages
SYSTEM_NOISE_MARKERS = [
    "<system-reminder>",
    "<injected-project-context>",
    "<local-command-caveat>",
    "<command-name>",
    "<command-message>",
    "<command-args>",
    "Stop hook feedback:",
    "Base directory for this skill:",
    "SessionStart:clear hook",
    "SessionStart hook additional context:",
    "UserPromptSubmit hook",
]


def is_system_noise(text: str) -> bool:
    """Check if a message is system/hook noise rather than real dialogue."""
    for marker in SYSTEM_NOISE_MARKERS:
        if marker in text:
            return True
    return False


def extract_dialogue(transcript_path: str) -> list[dict]:
    """Extract user and assistant text messages from the full transcript.

    Deduplicates streaming assistant entries by requestId (keeps last version).
    Skips thinking blocks, tool calls, tool results, system messages, and
    hook/command injection noise.
    """
    raw_entries = []
    assistant_by_request = {}  # requestId -> (index, entry)

    with open(transcript_path) as f:
        for line in f:
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
    """Format dialogue entries as clean markdown.

    Caps total output at MAX_DIALOGUE_CHARS, keeping the most recent entries.
    Individual entries are capped at MAX_ENTRY_CHARS.
    """
    # Build lines from the end (most recent first) to stay within budget
    lines = []
    total = 0
    for entry in reversed(entries):
        role = entry["role"].capitalize()
        text = entry["text"][:MAX_ENTRY_CHARS]
        line = f"**{role}:** {text}\n"
        if total + len(line) > MAX_DIALOGUE_CHARS:
            break
        lines.append(line)
        total += len(line)

    lines.reverse()
    if len(lines) < len(entries):
        lines.insert(0, "*(earlier dialogue truncated)*\n")

    return "# Last Session\n\n" + "\n".join(lines)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if input_data.get("hook_event_name", "") != "SessionEnd":
        sys.exit(0)

    transcript_path = input_data.get("transcript_path", "")
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")

    if not claude_project_dir:
        sys.exit(0)

    base_dir = Path(claude_project_dir)

    # Fall back to saved transcript path if not provided
    if not transcript_path:
        saved = state_path(base_dir, TRANSCRIPT_PATH_STATE)
        if saved.exists():
            transcript_path = saved.read_text().strip()

    if not transcript_path or not Path(transcript_path).exists():
        sys.exit(0)

    # Extract dialogue
    entries = extract_dialogue(transcript_path)

    if not entries:
        sys.exit(0)

    # Write to state directory
    output_path = state_path(base_dir, LAST_SESSION_FILE)
    output_path.write_text(format_dialogue(entries))

    sys.exit(0)


if __name__ == "__main__":
    main()

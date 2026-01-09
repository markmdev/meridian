#!/usr/bin/env python3
"""
Work-Until Loop Stop Hook

Handles stopping when a work-until loop is active.
Checks for completion phrase or max iterations, blocks otherwise.
"""

import json
import re
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    get_project_config,
    get_loop_state,
    update_loop_iteration,
    clear_loop_state,
    build_stop_prompt,
    ACTION_COUNTER_FILE,
)


def reset_action_count(base_dir: Path) -> None:
    """Reset action counter to 0."""
    counter_path = base_dir / ACTION_COUNTER_FILE
    try:
        counter_path.write_text("0")
    except IOError:
        pass


def get_last_assistant_output(transcript_path: str) -> str | None:
    """Extract the last assistant message text from the transcript."""
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()

        # Find last assistant message (transcript is JSONL)
        # Entry format: {"type": "assistant", "message": {"role": "assistant", "content": [...]}, ...}
        last_assistant = None
        for line in lines:
            try:
                entry = json.loads(line)
                if entry.get('type') == 'assistant':
                    last_assistant = entry
            except json.JSONDecodeError:
                continue

        if not last_assistant:
            return None

        # Extract text content
        content = last_assistant.get('message', {}).get('content', [])
        texts = []
        for block in content:
            if block.get('type') == 'text':
                texts.append(block.get('text', ''))

        return '\n'.join(texts) if texts else None

    except (IOError, json.JSONDecodeError):
        return None


def check_completion_phrase(output: str, phrase: str) -> bool:
    """Check if output contains <complete>PHRASE</complete> with exact match."""
    if not output or not phrase:
        return False

    # Look for <complete>...</complete> tags
    pattern = r'<complete>(.*?)</complete>'
    matches = re.findall(pattern, output, re.DOTALL)

    for match in matches:
        # Normalize whitespace for comparison
        normalized_match = ' '.join(match.strip().split())
        normalized_phrase = ' '.join(phrase.strip().split())
        if normalized_match == normalized_phrase:
            return True

    return False


def build_loop_prompt(base_dir: Path, config: dict, state: dict) -> str:
    """Build the loop stop prompt with standard checks + loop info + original prompt."""
    parts = []

    # Add loop status header
    iteration = state.get('iteration', 1)
    max_iter = state.get('max_iterations', 0)
    phrase = state.get('completion_phrase')
    prompt = state.get('prompt', '')

    parts.append(f"🔄 **WORK-UNTIL LOOP** — Iteration {iteration}")
    if max_iter > 0:
        parts.append(f" of {max_iter}")
    parts.append("\n\n")

    # Add standard stop prompt
    parts.append(build_stop_prompt(base_dir, config))
    parts.append("\n\n")

    # Add loop-specific instructions
    parts.append("---\n\n")
    parts.append("**LOOP STATUS**: You are in a work-until loop. After completing the above checks, continue working on your task.\n\n")

    if phrase:
        parts.append(f"**TO EXIT LOOP**: Output `<complete>{phrase}</complete>` when the statement \"{phrase}\" is TRUE.\n")
        parts.append("- The phrase MUST be completely and genuinely true\n")
        parts.append("- Do NOT output a false statement to escape the loop\n")
        parts.append("- If you're stuck, keep trying — the loop continues until genuine completion\n\n")
        parts.append("**BEFORE OUTPUTTING COMPLETION PHRASE**: You MUST run reviewer agents first.\n")
        parts.append("1. Run Implementation Reviewer and Code Reviewer agents in parallel\n")
        parts.append("2. If they return ANY issues → fix them → re-run reviewers\n")
        parts.append("3. Only when reviewers return 0 issues can you output the completion phrase\n\n")
    else:
        parts.append("**TO EXIT LOOP**: No completion phrase set. Loop will run until max iterations.\n\n")

    if max_iter > 0:
        remaining = max_iter - iteration
        parts.append(f"**ITERATIONS**: {remaining} remaining before auto-stop.\n\n")

    # Add the original task prompt
    if prompt:
        parts.append("---\n\n")
        parts.append("**YOUR TASK** (continue working on this):\n\n")
        parts.append(prompt)
        parts.append("\n")

    return ''.join(parts)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    if input_data.get("hook_event_name") != "Stop":
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)
    base_dir = Path(claude_project_dir)

    # Check if loop is active
    state = get_loop_state(base_dir)
    if not state:
        # No active loop - let normal stop hook handle it
        sys.exit(0)

    iteration = state.get('iteration', 1)
    max_iterations = state.get('max_iterations', 0)
    completion_phrase = state.get('completion_phrase')

    # Check for max iterations
    if max_iterations > 0 and iteration >= max_iterations:
        print(f"🛑 Work-until loop: Max iterations ({max_iterations}) reached.", file=sys.stderr)
        clear_loop_state(base_dir)
        reset_action_count(base_dir)
        sys.exit(0)  # Allow stop

    # Check for completion phrase in transcript
    transcript_path = input_data.get('transcript_path')
    if transcript_path and completion_phrase:
        output = get_last_assistant_output(transcript_path)
        if output and check_completion_phrase(output, completion_phrase):
            print(f"✅ Work-until loop: Detected <complete>{completion_phrase}</complete>", file=sys.stderr)
            clear_loop_state(base_dir)
            reset_action_count(base_dir)
            sys.exit(0)  # Allow stop

    # Not complete - continue loop
    config = get_project_config(base_dir)
    next_iteration = iteration + 1
    update_loop_iteration(base_dir, next_iteration)

    # Build loop prompt
    reason = build_loop_prompt(base_dir, config, state)

    # Reset action counter now that loop hook is firing
    reset_action_count(base_dir)

    # Build system message
    if completion_phrase:
        sys_msg = f"🔄 Work-until iteration {next_iteration} | To complete: <complete>{completion_phrase}</complete> (only when TRUE)"
    else:
        sys_msg = f"🔄 Work-until iteration {next_iteration} | No completion phrase — runs until max iterations"

    output = {
        "decision": "block",
        "reason": reason,
        "systemMessage": sys_msg
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

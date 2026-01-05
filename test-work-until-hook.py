#!/usr/bin/env python3
"""
Diagnostic script for work-until-stop.py hook.
Tests transcript parsing and completion phrase detection.

Usage:
  python test-work-until-hook.py <transcript_path> [completion_phrase]

Example:
  python test-work-until-hook.py ~/.claude/projects/abc123/transcript.jsonl "All tests pass"
"""

import json
import re
import sys
from pathlib import Path


def get_all_assistant_outputs(transcript_path: str) -> list[dict]:
    """Extract ALL assistant messages from the transcript with metadata."""
    results = []
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            try:
                entry = json.loads(line)

                # Check both 'type' and 'role' to see what's actually in the file
                entry_type = entry.get('type')
                entry_role = entry.get('role')
                message_role = entry.get('message', {}).get('role')

                # Collect text content
                content = entry.get('message', {}).get('content', [])
                texts = []
                thinking = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get('type') == 'text':
                            texts.append(block.get('text', ''))
                        elif block.get('type') == 'thinking':
                            thinking.append(block.get('thinking', '')[:100] + '...' if len(block.get('thinking', '')) > 100 else block.get('thinking', ''))

                if entry_type == 'assistant' or entry_role == 'assistant' or message_role == 'assistant':
                    results.append({
                        'line_num': i + 1,
                        'entry_type': entry_type,
                        'entry_role': entry_role,
                        'message_role': message_role,
                        'uuid': entry.get('uuid', 'N/A')[:8],
                        'text_blocks': len(texts),
                        'thinking_blocks': len(thinking),
                        'text_content': texts,
                        'has_complete_tag': any('<complete>' in t for t in texts),
                    })
            except json.JSONDecodeError as e:
                print(f"  Line {i+1}: JSON decode error: {e}")
                continue

    except IOError as e:
        print(f"Error reading file: {e}")
        return []

    return results


def check_completion_phrase(output: str, phrase: str) -> bool:
    """Check if output contains <complete>PHRASE</complete> with exact match."""
    if not output or not phrase:
        return False

    pattern = r'<complete>(.*?)</complete>'
    matches = re.findall(pattern, output, re.DOTALL)

    for match in matches:
        normalized_match = ' '.join(match.strip().split())
        normalized_phrase = ' '.join(phrase.strip().split())
        if normalized_match == normalized_phrase:
            return True

    return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    transcript_path = sys.argv[1]
    completion_phrase = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"=" * 60)
    print(f"WORK-UNTIL HOOK DIAGNOSTIC")
    print(f"=" * 60)
    print(f"\nTranscript: {transcript_path}")
    print(f"Completion phrase: {completion_phrase or '(not provided)'}")

    # Check file exists
    if not Path(transcript_path).exists():
        print(f"\nERROR: File not found: {transcript_path}")
        sys.exit(1)

    # Get file stats
    file_size = Path(transcript_path).stat().st_size
    with open(transcript_path, 'r') as f:
        line_count = sum(1 for _ in f)

    print(f"\nFile size: {file_size:,} bytes")
    print(f"Total lines: {line_count}")

    # Parse all assistant messages
    print(f"\n{'-' * 60}")
    print("ASSISTANT MESSAGES FOUND:")
    print(f"{'-' * 60}")

    assistants = get_all_assistant_outputs(transcript_path)

    if not assistants:
        print("\n  NO ASSISTANT MESSAGES FOUND!")
        print("\n  This means the hook's get_last_assistant_output() would return None.")
        print("  Checking what entry types exist in the file...")

        with open(transcript_path, 'r') as f:
            types_found = set()
            for line in f:
                try:
                    entry = json.loads(line)
                    types_found.add(f"type={entry.get('type')}, role={entry.get('role')}")
                except:
                    pass
            print(f"\n  Entry types in file: {types_found}")
        sys.exit(1)

    print(f"\n  Found {len(assistants)} assistant message(s) (showing last 5):\n")

    # Only show last 5
    for i, msg in enumerate(assistants[-5:]):
        print(f"  [{i+1}] Line {msg['line_num']} | UUID: {msg['uuid']}...")
        print(f"      entry.type = {msg['entry_type']}")
        print(f"      entry.role = {msg['entry_role']}")
        print(f"      entry.message.role = {msg['message_role']}")
        print(f"      Text blocks: {msg['text_blocks']}, Thinking blocks: {msg['thinking_blocks']}")
        print(f"      Has <complete> tag: {msg['has_complete_tag']}")

        if msg['text_content']:
            preview = msg['text_content'][0][:200] + '...' if len(msg['text_content'][0]) > 200 else msg['text_content'][0]
            print(f"      Preview: {repr(preview)}")
        print()

    # Test completion phrase detection on last message
    if completion_phrase and assistants:
        print(f"{'-' * 60}")
        print("COMPLETION PHRASE DETECTION:")
        print(f"{'-' * 60}")

        last_msg = assistants[-1]
        full_text = '\n'.join(last_msg['text_content'])

        print(f"\n  Testing on last assistant message (line {last_msg['line_num']})...")
        print(f"  Looking for: <complete>{completion_phrase}</complete>")

        # Check for any complete tags
        pattern = r'<complete>(.*?)</complete>'
        matches = re.findall(pattern, full_text, re.DOTALL)

        if matches:
            print(f"\n  Found {len(matches)} <complete> tag(s):")
            for j, match in enumerate(matches):
                normalized = ' '.join(match.strip().split())
                print(f"    [{j+1}] Content: {repr(match[:100])}")
                print(f"         Normalized: {repr(normalized[:100])}")

                # Compare with expected
                expected_normalized = ' '.join(completion_phrase.strip().split())
                if normalized == expected_normalized:
                    print(f"         MATCH!")
                else:
                    print(f"         Expected: {repr(expected_normalized[:100])}")
                    print(f"         Match: NO")
        else:
            print(f"\n  NO <complete> tags found in the last message!")
            print(f"  Full text of last message ({len(full_text)} chars):")
            print(f"  {'-' * 40}")
            print(f"  {full_text[:1000]}")
            if len(full_text) > 1000:
                print(f"  ... (truncated, {len(full_text) - 1000} more chars)")

        # Final verdict
        result = check_completion_phrase(full_text, completion_phrase)
        print(f"\n  VERDICT: check_completion_phrase() returns {result}")

    print(f"\n{'=' * 60}")
    print("DIAGNOSIS SUMMARY:")
    print(f"{'=' * 60}")

    # Check what the hook would have done
    if not assistants:
        print("\n  PROBLEM: No assistant messages found - hook returns None")
        print("  LIKELY CAUSE: entry.get('type') != 'assistant' for all entries")
    elif assistants[-1]['entry_type'] != 'assistant':
        print(f"\n  PROBLEM: Last message has type={assistants[-1]['entry_type']}, not 'assistant'")
        print("  The hook checks entry.get('type') == 'assistant'")
    elif not assistants[-1]['text_content']:
        print("\n  PROBLEM: Last assistant message has no text content")
    elif completion_phrase:
        last_text = '\n'.join(assistants[-1]['text_content'])
        if '<complete>' not in last_text:
            print("\n  PROBLEM: No <complete> tag in last assistant output")
            print("  The agent never output the completion phrase")
        elif not check_completion_phrase(last_text, completion_phrase):
            print("\n  PROBLEM: <complete> tag exists but phrase doesn't match")
            print("  Check the exact wording of the completion phrase")
        else:
            print("\n  OK: Completion phrase found and matches!")
            print("  If the hook didn't work, the issue is elsewhere (hook not triggered?)")
    else:
        print("\n  No completion phrase provided - can't test detection")


if __name__ == "__main__":
    main()

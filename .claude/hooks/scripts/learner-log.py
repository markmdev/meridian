#!/usr/bin/env python3
"""
Session Learner Log Viewer

Reads the session-learner.jsonl log and displays a formatted table.

Usage:
    python .claude/hooks/scripts/learner-log.py [--last N]

Reads from ~/.meridian/state/<hash>/session-learner.jsonl
(auto-detects project hash from cwd).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def get_state_dir() -> Path:
    """Resolve state directory from cwd."""
    project_hash = hashlib.md5(str(Path.cwd().resolve()).encode()).hexdigest()[:12]
    return Path.home() / ".meridian" / "state" / project_hash


def format_files(files_changed: list[str], diff_stat: str) -> str:
    """Format changed files into a compact summary."""
    if not files_changed:
        return "—"

    # Show short filenames
    short = [Path(f).name for f in files_changed[:3]]
    result = ", ".join(short)
    if len(files_changed) > 3:
        result += f" +{len(files_changed) - 3}"

    # Append diff stat if available (e.g., "+15/-3")
    if diff_stat:
        # Extract insertions/deletions from stat line
        ins = dels = ""
        for part in diff_stat.split(","):
            part = part.strip()
            if "insertion" in part:
                ins = "+" + part.split()[0]
            elif "deletion" in part:
                dels = "-" + part.split()[0]
        if ins or dels:
            result += f" ({ins}/{dels})" if ins and dels else f" ({ins or dels})"

    return result


def main():
    parser = argparse.ArgumentParser(description="Session Learner Log Viewer")
    parser.add_argument("--last", type=int, default=10, help="Show last N runs (default: 10)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    log_path = get_state_dir() / "session-learner.jsonl"
    if not log_path.exists():
        print("No session learner log found.")
        print(f"Expected at: {log_path}")
        sys.exit(1)

    entries = []
    for line in log_path.read_text().strip().split('\n'):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not entries:
        print("Log file is empty.")
        sys.exit(0)

    entries = entries[-args.last:]

    if args.json:
        for entry in entries:
            print(json.dumps(entry))
        sys.exit(0)

    # Formatted table output
    print()
    print("Session Learner History")
    print("━" * 80)

    for entry in entries:
        ts = entry.get("timestamp", "?")
        # Shorten timestamp: "2026-02-27T23:32:10" -> "02-27 23:32"
        try:
            short_ts = ts[5:16].replace("T", " ")
        except (IndexError, TypeError):
            short_ts = ts

        trigger = entry.get("trigger", "?")
        success = entry.get("success", False)
        status = "✓" if success else "✗"
        duration = entry.get("duration_seconds", 0)
        tools = entry.get("tools_used", [])
        tool_count = len(tools)
        files = entry.get("files_changed", [])
        diff_stat = entry.get("diff_stat", "")

        files_str = format_files(files, diff_stat)

        if success:
            duration_str = f"{duration:.0f}s"
        else:
            exit_code = entry.get("exit_code", -1)
            if exit_code == -2:
                duration_str = f"{duration:.0f}s (timeout)"
            else:
                duration_str = f"{duration:.0f}s (exit {exit_code})"

        print(f"  {short_ts}  {trigger:<8} {status}  {duration_str:<16} {tool_count} tools  {files_str}")

    print()
    print(f"Showing last {len(entries)} of {len(entries)} entries")
    print(f"Log: {log_path}")
    print()


if __name__ == "__main__":
    main()

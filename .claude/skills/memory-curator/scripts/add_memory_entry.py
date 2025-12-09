#!/usr/bin/env python3
"""
Append a new memory entry to .meridian/memory.jsonl

Each entry is a single JSON object per line with the following shape:
{
  "id": "mem-0038",
  "timestamp": "2025-11-12T05:55:31Z",
  "summary": "...",
  "tags": ["a", "b"],
  "links": ["TASK-123", "path/to/file"]
}

Usage examples:
  python add_memory_entry.py --summary "Fixed cache bug" \
      --tags perf,bugfix --links TASK-123 services/api/cache.ts

  # Multiple flags also work (mixed with comma lists):
  python add_memory_entry.py --summary "Lesson learned" \
      --tags perf --tags reliability,lessons-learned \
      --links TASK-9 --links services/x.ts,docs/note.md

Optional flags:
  --path PATH/to/memory.jsonl   (default: .meridian/memory.jsonl)

Notes:
- The script auto-generates a strictly increasing id like mem-0001, mem-0002 ...
  by reading the last valid line in the JSONL file. If the file doesn't exist,
  it starts at mem-0001.
- Timestamps are in UTC ISO-8601 with trailing 'Z'.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

MEMORY_RELATIVE_PATH = ".meridian/memory.jsonl"
ID_PREFIX = "mem-"
ID_PATTERN = re.compile(r"^mem-(\d{4,})$")


def get_default_memory_path() -> Path:
    """Get the default memory path using CLAUDE_PROJECT_DIR if available."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        return Path(project_dir) / MEMORY_RELATIVE_PATH
    return Path(MEMORY_RELATIVE_PATH)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Append a memory entry to memory.jsonl")
    p.add_argument("--summary", required=True, help="Short markdown summary of the memory item")
    p.add_argument("--tags", action="append", default=[], help="Tags comma or space separated; may repeat the flag")
    p.add_argument("--links", action="append", default=[], help="Links (TASK ids, file paths, URLs). Comma or space separated; may repeat")
    p.add_argument("--path", default=None, help="Path to memory.jsonl (default: $CLAUDE_PROJECT_DIR/.meridian/memory.jsonl)")
    return p.parse_args()


def _split_mixed(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    for raw in items:
        if raw is None:
            continue
        # Split on commas and whitespace while preserving simple quoted groups
        # For simplicity, split on commas first then whitespace
        for chunk in str(raw).split(','):
            for token in chunk.strip().split():
                token = token.strip()
                if token:
                    out.append(token)
    # De-duplicate while preserving order
    seen = set()
    deduped = []
    for x in out:
        if x not in seen:
            seen.add(x)
            deduped.append(x)
    return deduped


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class MemoryEntry:
    id: str
    timestamp: str
    summary: str
    tags: List[str]
    links: List[str]

    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "tags": self.tags,
            "links": self.links,
        }, ensure_ascii=False)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _tail_last_nonempty_line(path: Path) -> str | None:
    """Read the last non-empty line efficiently without loading entire file."""
    try:
        with path.open('rb') as f:
            f.seek(0, os.SEEK_END)
            if f.tell() == 0:
                return None
            buf = bytearray()
            pos = f.tell() - 1
            while pos >= 0:
                f.seek(pos)
                byte = f.read(1)
                if byte == b'\n' and buf:
                    break
                if byte != b'\r' and byte != b'\n':
                    buf.extend(byte)
                pos -= 1
            if not buf:
                return None
            return bytes(reversed(buf)).decode('utf-8', errors='ignore').strip()
    except FileNotFoundError:
        return None


def _next_id(path: Path) -> str:
    last_line = _tail_last_nonempty_line(path)
    if last_line:
        try:
            obj = json.loads(last_line)
            raw_id = obj.get("id", "")
            m = ID_PATTERN.match(raw_id)
            if m:
                n = int(m.group(1)) + 1
                return f"{ID_PREFIX}{n:04d}"
        except Exception:
            # Fall back to scanning if the last line was malformed
            pass

    # Full scan fallback (handles sparse/bad trailing lines)
    max_n = 0
    if path.exists():
        try:
            with path.open('r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        raw_id = obj.get("id", "")
                        m = ID_PATTERN.match(raw_id)
                        if m:
                            max_n = max(max_n, int(m.group(1)))
                    except Exception:
                        continue
        except Exception:
            pass
    return f"{ID_PREFIX}{(max_n + 1):04d}"


def append_entry(path: Path, summary: str, tags: List[str], links: List[str]) -> MemoryEntry:
    _ensure_parent_dir(path)
    entry = MemoryEntry(
        id=_next_id(path),
        timestamp=_utc_now_iso(),
        summary=summary.strip(),
        tags=_split_mixed(tags),
        links=_split_mixed(links),
    )

    # Append atomically-ish: open with append to avoid races; write one line
    with path.open('a', encoding='utf-8') as f:
        f.write(entry.to_json())
        f.write('\n')

    return entry


def main() -> int:
    args = parse_args()
    path = Path(args.path) if args.path else get_default_memory_path()

    if not args.summary or not args.summary.strip():
        print("Error: --summary is required and cannot be empty", file=sys.stderr)
        return 2

    entry = append_entry(path, args.summary, args.tags, args.links)

    # Friendly output to stdout so this can be used in CI logs
    print(f"Added {entry.id} at {entry.timestamp} → {path}")
    print(entry.to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

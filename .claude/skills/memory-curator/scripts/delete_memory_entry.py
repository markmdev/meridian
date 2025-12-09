#!/usr/bin/env python3
"""
Delete an existing memory entry from .meridian/memory.jsonl.

Usage:
  python delete_memory_entry.py --id mem-0042
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

MEMORY_RELATIVE_PATH = ".meridian/memory.jsonl"


def get_default_memory_path() -> Path:
    """Get the default memory path using CLAUDE_PROJECT_DIR if available."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        return Path(project_dir) / MEMORY_RELATIVE_PATH
    return Path(MEMORY_RELATIVE_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete a memory entry by id")
    parser.add_argument("--id", required=True, help="Memory id (e.g. mem-0023)")
    parser.add_argument(
        "--path",
        default=None,
        help="Path to memory.jsonl (default: $CLAUDE_PROJECT_DIR/.meridian/memory.jsonl)",
    )
    return parser.parse_args()


def _load_entries(path: Path) -> List[dict]:
    if not path.exists():
        raise FileNotFoundError(f"No memory file at {path}")

    entries: List[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Malformed JSON line in {path}: {line}") from exc
    return entries


def _write_entries(path: Path, entries: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False))
            handle.write("\n")


def delete_entry(entries: List[dict], entry_id: str) -> bool:
    initial_len = len(entries)
    entries[:] = [entry for entry in entries if entry.get("id") != entry_id]
    return len(entries) < initial_len


def main() -> int:
    args = parse_args()
    path = Path(args.path) if args.path else get_default_memory_path()

    try:
        entries = _load_entries(path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if not delete_entry(entries, args.id):
        print(f"Error: entry {args.id} not found", file=sys.stderr)
        return 1

    _write_entries(path, entries)
    print(f"Deleted {args.id} from {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


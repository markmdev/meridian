#!/usr/bin/env python3
"""
Edit an existing memory entry inside .meridian/memory.jsonl.

Usage example:
  python edit_memory_entry.py --id mem-0042 --summary "Refined insight" \
      --tags architecture,lesson --links TASK-123 docs/adr.md

You must supply at least one field to update (--summary, --tags, --links).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable, List

MEMORY_RELATIVE_PATH = ".meridian/memory.jsonl"


def get_default_memory_path() -> Path:
    """Get the default memory path using CLAUDE_PROJECT_DIR if available."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        return Path(project_dir) / MEMORY_RELATIVE_PATH
    return Path(MEMORY_RELATIVE_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Edit a memory entry by id")
    parser.add_argument("--id", required=True, help="Memory id (e.g. mem-0007)")
    parser.add_argument("--summary", help="Updated summary text")
    parser.add_argument(
        "--tags",
        action="append",
        default=[],
        help="New tags (comma or space separated); replaces existing tags",
    )
    parser.add_argument(
        "--links",
        action="append",
        default=[],
        help="New links (comma or space separated); replaces existing links",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Path to memory.jsonl (default: $CLAUDE_PROJECT_DIR/.meridian/memory.jsonl)",
    )
    return parser.parse_args()


def _split_mixed(items: Iterable[str]) -> List[str]:
    output: List[str] = []
    for raw in items:
        if raw is None:
            continue
        for chunk in str(raw).split(","):
            for token in chunk.strip().split():
                token = token.strip()
                if token:
                    output.append(token)
    seen = set()
    deduped: List[str] = []
    for val in output:
        if val not in seen:
            seen.add(val)
            deduped.append(val)
    return deduped


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


def edit_entry(entries: List[dict], entry_id: str, summary: str | None, tags: List[str], links: List[str]) -> bool:
    updated = False
    for entry in entries:
        if entry.get("id") != entry_id:
            continue
        if summary is not None:
            entry["summary"] = summary.strip()
            updated = True
        if tags:
            entry["tags"] = tags
            updated = True
        if links:
            entry["links"] = links
            updated = True
        return updated
    return False


def main() -> int:
    args = parse_args()
    path = Path(args.path) if args.path else get_default_memory_path()

    tags = _split_mixed(args.tags)
    links = _split_mixed(args.links)

    if args.summary is None and not tags and not links:
        print("Error: provide at least one field to update (--summary, --tags, --links)", file=sys.stderr)
        return 2

    try:
        entries = _load_entries(path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    changed = edit_entry(entries, args.id, args.summary, tags, links)
    if not changed:
        print(f"Error: entry {args.id} not found or no changes applied", file=sys.stderr)
        return 1

    _write_entries(path, entries)
    print(f"Updated {args.id} in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


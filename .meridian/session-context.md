# Session Context

> **Rolling context file** — Captures important information across sessions. Oldest entries are automatically trimmed when the file exceeds the configured line limit (`session_context_max_lines` in config.yaml).

## Rules

**DO NOT read this file.** It is already injected into your context at session start. Reading it wastes tokens.

**ALWAYS add new entries at the BOTTOM of this file.** Oldest entries are at the top and get trimmed first.

## How to Use

Append timestamped entries (format: `YYYY-MM-DD HH:MM`) with:
- Key decisions made and rationale
- Important discoveries or blockers
- Complex problems solved (and how)
- Context that would be hard to rediscover
- Next steps if work is interrupted
- **Important user messages** — if a user's messages contains instructions, preferences, constraints, or context that should persist across sessions, copy it here (verbatim if needed)

**Do NOT include**: Routine progress updates, obvious information, or content better suited for task-specific docs.

---

<!-- SESSION ENTRIES START - Add new entries at the BOTTOM -->

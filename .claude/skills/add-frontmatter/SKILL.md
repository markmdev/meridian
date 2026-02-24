---
name: add-frontmatter
description: Scan all .md files in the project and add or fix YAML frontmatter (summary + read_when) so they can be discovered by context routers like Reflex.
---

# Add Frontmatter

Scan every `.md` file in the project and ensure it has the required frontmatter so Reflex can discover and route it.

## Required frontmatter format

```
---
summary: One-line description of what this file covers
read_when:
  - keyword or phrase that signals this file is relevant
  - another keyword
---
```

## What to skip

- Files already having correct `summary` + `read_when` frontmatter — leave them alone
- Files that have frontmatter with any other keys (e.g. `name`, `description`, `title`) — do not replace or merge, leave them alone
- `node_modules/`, `.git/`, `dist/`, `build/`, `vendor/`, `__pycache__/`
- `.claude/` — agents, skills, commands, hooks all use their own frontmatter schemas
- Files that are purely generated output, changelogs, or boilerplate with no reusable knowledge (e.g. `CHANGELOG.md`, `LICENSE`)

## Process

1. Glob all `.md` files, excluding skip dirs
2. For each file: check if frontmatter with `summary` and `read_when` already exists
3. If missing or incomplete: read the file content, infer a concise `summary` and 2-4 `read_when` keywords from the actual content
4. Prepend the frontmatter block (or insert after existing `---` if only partially present)
5. Write the updated file

## Quality criteria

- `summary` is a single line, factual, specific — describes what the file actually covers
- `read_when` keywords match how someone would describe a task that needs this file (e.g. `"setting up auth"`, `"debugging routing"`, `"OpenClaw plugin"`)
- Don't invent knowledge not in the file — infer from actual content only

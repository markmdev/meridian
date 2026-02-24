---
name: docs
description: Create or update .meridian/docs/ files for a specific module or directory. Use when the user wants to document a part of the codebase for future agent sessions.
---

# Docs

Document a module so future agents (and humans) understand it without re-reading the code. Every doc must be worth the context window space it occupies.

## Process

### 1. Scope

Identify the module or directory the user specified. Verify it exists. If ambiguous, clarify before proceeding.

### 2. Check existing docs

Search `.meridian/docs/` for docs already covering this area — grep for the module name, read matches. Understand what's documented, what's missing, what's stale.

### 3. Explore the module

Launch Explore agents to build deep understanding:

- **Entry points** — what starts execution? Exports, routes, handlers, CLI commands
- **Data flow** — what comes in, how it transforms, where it goes
- **Dependencies** — what this module uses, what depends on it
- **Patterns** — conventions, unusual approaches, implicit contracts
- **Gotchas** — non-obvious behavior that would trip someone up
- **Integration points** — connections to other modules, services, external APIs

Spawn multiple Explore agents in parallel for different aspects. Follow up on findings — expect 2+ rounds.

### 4. Identify topics

Each doc covers one topic a future agent would need. Split by topic, not by file. Common categories:

- **Architecture/overview** — how the module works as a whole
- **Integration guide** — external API, service, or cross-module connection
- **Non-obvious behavior** — gotchas, sharp edges, implicit contracts
- **Complex workflow** — multi-step process, state machine, async flow

Small modules might produce one doc. Large modules might produce three or four.

### 5. Write docs

For each topic, create a file in `.meridian/docs/`:

- **Filename**: kebab-case reflecting the topic (`billing-architecture.md`, `stripe-webhook-handling.md`)
- **Frontmatter**: `summary` (one line) and `read_when` (2-5 keywords matching task contexts where an agent would need this)
- **Content**: what it is, how it works, why it's designed this way, gotchas
- **References**: point at code with `file:line`, not code snippets (snippets go stale)
- **Length**: under ~100 lines per doc — if longer, split into multiple topics

If a doc already exists for a topic, update it. Don't create duplicates.

### 6. Validate `read_when` keywords

For each keyword, ask: "What would someone be doing when they need this?" Good keywords describe tasks, not topics:
- "modifying billing logic" — specific, matches real tasks
- "debugging webhook failures" — describes a situation
- "working with code" — too vague, matches everything

## What NOT to document

- Function signatures and parameter lists — that's what code is for
- What the code already says clearly — focus on the non-obvious
- Every file in the module — only what's worth context window space
- Style or formatting conventions — that's for linters and CLAUDE.md

## Checklist

- [ ] Every doc has `summary` and `read_when` frontmatter?
- [ ] `read_when` keywords match real task contexts?
- [ ] Content is non-obvious knowledge, not code restated in English?
- [ ] File:line references instead of code snippets?
- [ ] Each doc covers one focused topic?
- [ ] Existing docs updated rather than duplicated?

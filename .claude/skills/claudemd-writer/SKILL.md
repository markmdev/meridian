---
name: claudemd-writer
description: Create or update CLAUDE.md files. Use when adding a new module, explaining patterns, or fixing repeated agent mistakes.
---

# CLAUDE.md Writer

CLAUDE.md files provide context to Claude Code when working in a directory. Claude reads them automatically based on the files being accessed.

## Core Principle: Less is More

Claude Code's system prompt tells Claude to **ignore CLAUDE.md content if it seems irrelevant**. The more irrelevant content, the more likely Claude ignores everything.

Frontier LLMs reliably follow ~150-200 instructions. Claude Code's system prompt uses ~50. Every line in CLAUDE.md competes for attention.

## Hierarchical Injection

CLAUDE.md files inject based on path depth. When reading `modules/payments/lib/checkout.ts`, Claude receives CLAUDE.md from: project root → modules/ → payments/ → lib/

**Closest file wins** if instructions conflict. Keep each CLAUDE.md focused on its level — don't duplicate parent content.

## What Goes Where

**Root CLAUDE.md**: Commands (install/dev/test/build/lint), project purpose, stack overview, project-wide conventions.

**Domain CLAUDE.md** (e.g., `modules/`, `services/`): What the domain handles, shared patterns, cross-module dependencies.

**Module CLAUDE.md** (e.g., `payments/`, `auth/`): Module-specific test commands, what it does, how it works, why it's designed this way, gotchas.

## Writing Guidelines

### Describe What, How, Why — Concisely

- **What** this module does
- **How** it works (architecture, data flow, key patterns)
- **Why** it's designed this way (rationale, constraints)
- **Gotchas** that cause mistakes

Don't write API reference documentation. Write context that helps agents make good decisions.

### Use Pointers, Not Copies

Reference canonical examples by file and line number: "Follow the pattern in `src/services/UserService.ts:45-60`"

Code snippets go stale. File references can be verified.

### Provide Alternatives to "Never"

"Never use `--force`" leaves Claude stuck. "Never use `--force`, use `--force-with-lease` instead" gives a path forward.

### Don't Use CLAUDE.md as a Linter

Style rules (indentation, semicolons, quotes) belong in ESLint/Prettier. Claude learns style from existing code.

## When to Create

- New module or significant directory
- Patterns need explanation
- Agent repeatedly makes wrong assumptions
- You fix a bug caused by missing context

## When NOT to Create/Update

- Bug fixes that don't change behavior
- Refactoring that preserves API
- Internal implementation details
- Small utility files or tests

## Structure

No rigid template. Common sections, in order of usefulness:

1. **Commands** — Put runnable commands first (test, dev, lint)
2. **How It Works** — Architecture, data flow, key components
3. **Why This Design** — Rationale, constraints, tradeoffs
4. **Key Patterns** — Reference canonical examples by file:line
5. **Gotchas** — Non-obvious things that cause mistakes

Include only sections that help agents work effectively in this directory.

## Checklist

Before saving:

- [ ] Explains what, how, and why — concisely?
- [ ] Includes gotchas not obvious from code?
- [ ] Every line relevant to this directory?
- [ ] File references instead of code snippets?
- [ ] Every "never" has an alternative?
- [ ] Concise enough that Claude won't ignore it?

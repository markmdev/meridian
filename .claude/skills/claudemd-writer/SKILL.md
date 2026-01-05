# CLAUDE.md Writer Skill

Use this skill when creating or updating CLAUDE.md files in the codebase.

## What is CLAUDE.md?

CLAUDE.md files are documentation that Claude Code automatically reads when working in a directory. They provide context to agents without requiring them to read every file.

## Core Principle: Less is More

Claude Code includes a system reminder that tells Claude to **ignore CLAUDE.md content if it seems irrelevant**. The more irrelevant content you include, the more likely Claude will ignore everything.

**Key insight**: Frontier LLMs can reliably follow ~150-200 instructions. Claude Code's system prompt already uses ~50. Every instruction in CLAUDE.md competes for attention.

## Hierarchical Injection

CLAUDE.md files are injected based on the path Claude is reading:

```
project/
├── CLAUDE.md                    # Injected for everything
├── modules/
│   ├── CLAUDE.md                # Injected when reading modules/*
│   └── payments/
│       ├── CLAUDE.md            # Injected when reading modules/payments/*
│       └── lib/
│           └── CLAUDE.md        # Injected when reading modules/payments/lib/*
```

When Claude reads `modules/payments/lib/checkout.ts`, it receives:
- `project/CLAUDE.md`
- `project/modules/CLAUDE.md`
- `project/modules/payments/CLAUDE.md`
- `project/modules/payments/lib/CLAUDE.md`

**Precedence**: The closest CLAUDE.md to the file being edited takes precedence if instructions conflict.

**Implication**: Keep each CLAUDE.md focused on its level. Don't duplicate parent content.

## What Goes Where

### Root CLAUDE.md (project root)
- **Commands first**: install, dev, test, build, lint
- What the project is and its purpose
- Stack and architecture overview
- Project-wide conventions
- Pointers to where module docs live
- Keep concise — every line competes for Claude's attention

### Domain CLAUDE.md (e.g., `modules/`, `services/`)
- What this domain handles
- Shared patterns across modules in this domain
- Cross-module dependencies and data flow

### Module CLAUDE.md (e.g., `payments/`, `auth/`)
- **Commands first**: how to test this module specifically
- What the module does and its role
- How it works (architecture, key components)
- Why it's designed this way (rationale, constraints)
- Gotchas and anti-patterns

## Writing Guidelines

### Describe What, How, and Why — Concisely

CLAUDE.md should give agents the context they need to work effectively:
- **What** this module/service does
- **How** it works (architecture, data flow, key patterns)
- **Why** it's designed this way (rationale, constraints)
- **Gotchas** — things that aren't obvious and cause mistakes

**Bad** (API reference dump):
```markdown
## API Reference
### createUser(email, name, options)
Creates a new user in the database.
Parameters:
- email: string - The user's email address
- name: string - The user's full name
- options: object - Additional options
  - sendWelcomeEmail: boolean - Whether to send welcome email
...
```

**Good** (context + gotchas):
```markdown
## How It Works
User creation flows through `UserService` which validates input, creates the DB record,
and triggers async welcome emails via the job queue.

## Why This Design
We use a job queue for emails because Stripe webhooks have a 30s timeout — synchronous
email sending caused webhook failures.

## Gotchas
- Never call `createUser` without validating email format first
- Always wrap user operations in `withTransaction()`
- Don't import from `internal/` — use public exports only
```

### Use Pointers, Not Copies

**Bad**:
```markdown
## Error Handling Pattern
try {
  const result = await service.doThing();
  return { success: true, data: result };
} catch (error) {
  logger.error('Operation failed', { error });
  return { success: false, error: error.message };
}
```

**Good**:
```markdown
## Error Handling
Follow the pattern in `src/services/UserService.ts:45-60`
```

Code snippets go stale. File references can be verified.

### Provide Alternatives to "Never"

**Bad**:
```markdown
- Never use the --force flag
```

**Good**:
```markdown
- Never use `--force`, use `--force-with-lease` instead
```

Claude will get stuck if told "never" without an alternative.

### Don't Use CLAUDE.md as a Linter

**Bad**:
```markdown
## Code Style
- Use 2 spaces for indentation
- Always use semicolons
- Prefer const over let
- Use single quotes for strings
```

**Good**: Configure ESLint/Prettier and let them handle it. Claude learns from existing code.

## When to Create

Create CLAUDE.md when:
- New module, service, or significant directory
- Patterns need explanation
- Common mistakes keep happening
- Agent repeatedly makes the same wrong assumptions

## When to Update

Update CLAUDE.md when:
- Public API changes
- New patterns established
- Architectural decisions made
- You fix a bug caused by missing context

## When NOT to Create/Update

Skip CLAUDE.md updates for:
- Bug fixes that don't change behavior
- Refactoring that preserves API
- Internal implementation details
- Small utility files
- Test files

## Suggested Structure

No rigid template — adapt to what's useful for the module. Common sections:

```markdown
# [Module Name]

[1-2 sentences: what this does and its role in the system]

## Commands
[Put runnable commands at the top — agents need these most]
- Test: `pnpm test:module-name`
- Dev: `pnpm dev`
- Lint: `pnpm lint`

## How It Works
[Architecture, data flow, key components — enough to understand the module]

## Why This Design
[Rationale, constraints, tradeoffs — helps agent make consistent decisions]

## Key Patterns
[Patterns to follow when adding code here]
[Reference canonical examples: "See `UserService.ts:45-60`"]

## Gotchas
[Things that aren't obvious and cause mistakes]
- Never [X], use [Y] instead
- [Common mistake] → [How to fix]
```

**Not all sections are needed.** Include what helps agents work effectively here.

## Examples

### Good Root CLAUDE.md
```markdown
# MyProject

E-commerce platform for digital products.

## Commands
- Install: `pnpm install`
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Lint: `pnpm lint`

## Stack
Next.js 14, TypeScript, Prisma, PostgreSQL, Stripe

## Architecture
- `src/app/` — Next.js app router pages
- `src/services/` — Business logic (each has its own CLAUDE.md)
- `src/lib/` — Shared utilities

## Conventions
- All database operations use Prisma — no raw SQL
- Environment variables in `.env.local`, never commit secrets
```

### Good Module CLAUDE.md
```markdown
# Payments Module

Handles Stripe integration for subscriptions and one-time payments.

## Commands
- Test: `pnpm test:payments`
- Test watch: `pnpm test:payments --watch`

## How It Works
`PaymentService` wraps all Stripe API calls. Webhooks are processed async via
`WebhookProcessor` which validates signatures and dispatches to handlers.

## Why This Design
Stripe webhooks timeout at 30s. We immediately acknowledge and process async
to avoid retry storms. Handlers are idempotent using event ID deduplication.

## Gotchas
- Never call Stripe API directly — use `PaymentService`
- All amounts are in cents, not dollars
- Webhook handlers must be idempotent (check `processedEvents` table)
```

### Bad CLAUDE.md (Too Verbose)
```markdown
# Payments Module

## Overview
The payments module is responsible for handling all payment-related operations
in our application. It integrates with Stripe for processing credit card
payments, managing subscriptions, handling refunds, and...

[500 more lines explaining every function]
```

### Bad CLAUDE.md (Only Guardrails, No Context)
```markdown
# Payments Module

- Don't call Stripe directly
- Use cents not dollars
- Handlers must be idempotent
```
This tells Claude what NOT to do but not WHY or HOW the module works.

## Final Checklist

Before saving a CLAUDE.md:
- [ ] Does it explain what, how, and why — concisely?
- [ ] Does it include gotchas that aren't obvious from code?
- [ ] Is every line relevant to work in this directory?
- [ ] Are code references (file:line) used instead of code snippets?
- [ ] Does every "never" have an alternative?
- [ ] Is it concise? (Every line competes for Claude's attention)
- [ ] Would an agent understand the module well enough to work on it?

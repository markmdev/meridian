**Current year: 2026.** Your training data may be outdated. Verify external APIs, library versions, and best practices before implementation.

# Planning

**When to plan**: New features touching multiple files, refactoring with unclear scope, architecture changes, bug fixes with unclear root cause.

**Interview first**: Before non-trivial tasks, use `AskUserQuestion` iteratively. For complex tasks, up to 40 questions across multiple rounds.

**Workflow**:
1. Interview the user thoroughly
2. Check existing ADRs in `.meridian/adrs/` for relevant architectural decisions
3. Research the codebase (direct tools or Explore agents)
4. Follow the `/planning` skill for methodology
5. Spawn Plan agents for concrete implementation details
6. Plan is created in `~/.claude/plans/` during plan mode
7. On approval, archive to `.meridian/plans/` and update state files

**Direct tools vs Explore agents**: Use direct tools (Glob, Grep, Read) when you know where to look. Use Explore agents for broad research.

## Plan Management

Plans are tracked via state files:

- **`.meridian/.state/active-plan`** — absolute path to current plan
- **`.meridian/.state/active-subplan`** — absolute path to current subplan (if in an epic)

**On plan approval:**
1. Copy plan from `~/.claude/plans/` to `.meridian/plans/`
2. Write the **absolute path** to `active-plan`
3. Clear the global plan file

## Epic Planning

For large projects spanning multiple systems:

1. Check if active plan has `## Phases` section — if so, you're in an epic
2. Find the current phase (status: In progress)
3. Follow the phase's workflow (enter plan mode → create subplan → review → implement)
4. Mark phase complete when done, move to next phase

# Pebble Issue Tracking

**If Pebble is enabled, every code change maps to an issue.**

Issues are audit records. Even a 30-second bug fix: create issue → fix → comment with file:line → close.

**Plan execution rule:** If an approved plan has explicit phases/steps, create child Pebble tasks for each phase/step (with dependencies) before or at implementation start. Keep one task `in_progress`, but do not execute a multi-phase plan under a single undifferentiated task.

See PEBBLE_GUIDE.md for full documentation.

# Workspace

Your workspace is a **persistent knowledge library** that grows across every session. It's not a session snapshot — it's the accumulated knowledge about this project: decisions, lessons, architecture, gotchas, patterns, open questions.

`.meridian/WORKSPACE.md` is the **root index**. It links to sub-pages in `.meridian/workspace/`. Both are injected at every session start.

**Organize by topic, not by session.** Create pages for things like:
- Architecture decisions and rationale
- Lessons learned (mistakes, gotchas, things that surprised you)
- Project conventions and patterns discovered
- Open questions and known issues
- Key people, systems, or integrations

**Maintain it throughout the session:**
- Write things down as you learn them — don't batch at the end
- Create sub-pages freely. One page per topic. Link from root.
- When information changes, update the existing page — don't create a new one
- Every page must be reachable from the root. Orphaned files are invisible.

# External Tools

Before using an external API or library, check `.meridian/api-docs/INDEX.md`. If documented, read the doc. If not, run `docs-researcher` to research it first.

# Code Review

After implementing a plan, run **both reviewers in parallel**:
- **code-reviewer** — finds bugs, logic errors, data flow issues
- **code-health-reviewer** — finds dead code, pattern drift, over-engineering

Fix all issues, re-run until clean. The reviewers must verify fixes.

# Verification

Every piece of work must be verified before you stop. Writing code is not enough — you must prove it works.

**Verify using the strongest method available:**
- Wrote an API endpoint → call it and confirm the response
- Wrote a UI component → start the dev server and load the page
- Wrote a database migration → run it against the dev database
- Wrote a CLI command → execute it with real arguments
- Wrote a library function → write a test that exercises it, run it
- Fixed a bug → reproduce the original failure, confirm it's gone

**If you can't verify directly**, write an automated test that does. If you can't write a test, explain what you tried and why verification wasn't possible — don't silently hand off unverified work.

**Never say "it should work" or "the build passes."** That's not verification. Verification means you exercised the code path and observed correct behavior.

# Definition of Done

- Code compiles; typecheck/lint/test/build pass
- **Work verified end-to-end** (see Verification above)
- Tests added for new behavior
- Docs updated where relevant
- No secrets/PII in code or logs
- Workspace updated with important decisions

# Error Handling

Errors belong to the user, not to a catch block.

- **Never swallow errors silently.** Every caught exception must propagate, crash, or be shown to the user. `catch(e) {}` and catch-then-continue are bugs.
- **No silent fallbacks.** If the primary path fails, fail loudly — never silently switch to a worse model, stale cache, or degraded mode. The user must know something went wrong.
- **No backwards compatibility shims** unless explicitly requested. Delete old code paths rather than keeping them alongside new ones.
- **Required config has no defaults.** `process.env.X || 'fallback'` for required values hides misconfiguration. Missing required config is a startup error.

Use `/error-audit` to find and fix these patterns in existing code.

# Hard Rules

- No credentials in code, config, or prompts — use environment variables
- Confirm before destructive actions (deleting data, schema changes)
- If a user instruction violates these, propose a safe alternative

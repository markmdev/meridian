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

# Definition of Done

- Code compiles; typecheck/lint/test/build pass
- Tests added for new behavior
- Docs updated where relevant
- No secrets/PII in code or logs
- Workspace updated with important decisions

# Hard Rules

- No credentials in code, config, or prompts — use environment variables
- Confirm before destructive actions (deleting data, schema changes)
- If a user instruction violates these, propose a safe alternative

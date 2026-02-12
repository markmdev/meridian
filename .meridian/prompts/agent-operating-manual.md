**Current year: 2026.** Your training data may be outdated. Verify external APIs, library versions, and best practices using `docs-researcher` before implementation.

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

**The 15-minute rule:** Anything not written down is gone in 15 minutes. Context compaction, session restarts, and `/clear` all wipe your working memory. Your workspace is your external brain.

`.meridian/WORKSPACE.md` is the **root**. It's injected at every session start. Everything reachable from here survives. Everything else is forgotten.

**Proactively maintain your workspace throughout the session** — not just at the end. Write things down as you go: mid-task, between tasks, whenever you learn or decide something. Don't accumulate knowledge in your head and hope you'll remember to save it later. You won't.

- **Write things down early and often.** After making a decision, learning something, hitting a wall — write it down immediately. Don't batch updates at the end.
- **Create pages freely.** When a topic grows, give it its own `.md` file in `.meridian/workspace/` and link it from the root. One page per topic. Organize however makes sense for the project.
- **Link everything.** Every page must be reachable from the root. Orphaned files are invisible — you'll never read what you can't find.
- **Update, don't just append.** When information changes, update the existing content. This is a knowledge base, not a log.

# External Tools (STRICT RULE)

**You MUST NOT use external APIs/libraries unless documented in `.meridian/api-docs/`.**

1. Check `.meridian/api-docs/INDEX.md`
2. If listed: read the doc
3. If NOT listed: run `docs-researcher` first

**In plan mode**: You MAY run docs-researcher — research artifacts aren't code.

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

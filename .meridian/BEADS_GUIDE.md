# Beads Guide for Agents

**Beads is ENABLED for this project.** You MUST actively use Beads to manage all work.

Beads is a git-backed issue tracker designed for AI agents. It provides persistent memory across sessions, dependency tracking, and structured workflows. All work should be tracked as Beads issues.

---

## Understanding Project State (Start Here)

At the beginning of each session, understand what's happening:

| Command | Purpose |
|---------|---------|
| `bd ready` | **Start here** — shows unblocked issues ready for work |
| `bd list --status in_progress` | What's currently being worked on |
| `bd blocked` | Issues waiting on dependencies |
| `bd show <id>` | Deep dive into specific issue |

Use these commands to understand context from previous sessions — what was in progress, what got blocked, what's next.

---

## When to Create Issues

Create Beads issues when:
- User mentions work to do ("fix X", "add Y", "investigate Z")
- You discover bugs or problems during implementation
- Work has dependencies or could block other work
- Breaking large tasks into trackable sub-tasks
- Research or exploratory work with fuzzy boundaries
- Ideas worth capturing for later

**Be proactive**: Suggest creating issues during conversations.

**Granularity**: If it takes 2+ minutes, it's an issue. Many small issues > few large ones.

---

## Creating Issues (Research First!)

**IMPORTANT**: Before creating an issue, thoroughly research the task:
- Explore relevant code to understand scope and complexity
- Identify affected files and modules
- Note dependencies on other systems or issues
- Understand edge cases and potential blockers
- Gather enough context to write a comprehensive description

A well-researched issue saves time later. Don't create vague issues.

---

## Core Principles

### 1. Always Use `--json`

**Every command that creates or modifies issues MUST include `--json`** for parseable output. This lets you capture IDs and verify state.

```bash
bd create "Fix login bug" -t bug -p 1 --json          # Returns {"id": "PROJ-abc", ...}
bd update PROJ-abc --status in_progress --json
bd close PROJ-abc --reason "Fixed" --json
```

### 2. Dependencies Control Execution

Issues become "ready" when all their blockers are closed. Use `bd ready` to see what's unblocked — this is your **Ready Front** (what can be worked on right now).

- **No dependency** = runs in parallel with siblings
- **Has dependency** = blocked until dependency closes

```bash
# B depends on A (B is blocked until A closes)
bd dep add B-id A-id
```

**Walk backward from the goal to create correct dependencies:**

```
"What's the final deliverable?"
  → Integration tests passing
    "What does that need?"
      → Streaming support, Header display
        "What do those need?"
          → Message rendering
            "What does that need?"
              → Buffer layout (foundation, no deps)
```

This produces correct deps because you're asking "X needs Y", not "X before Y".

**Cognitive trap to avoid:**
> "Phase 1 before Phase 2" → brain thinks "Phase 1 blocks Phase 2" → WRONG: `bd dep add phase1 phase2`

**Correct thinking:**
> "Phase 2 needs Phase 1" → `bd dep add phase2 phase1`

Always use requirement language, not temporal language.

### 3. Children Are Parallel by Default

Creating issues under a parent (`--parent <id>`) only creates hierarchy, NOT execution order. All children can run in parallel unless you add explicit `blocks` dependencies between them.

```bash
# These three tasks can run in PARALLEL (no deps between them)
bd create "Task A" -t task --parent $EPIC --json
bd create "Task B" -t task --parent $EPIC --json
bd create "Task C" -t task --parent $EPIC --json

# To sequence them, add blocks dependencies
bd dep add $TASK_B $TASK_A    # B blocked by A
bd dep add $TASK_C $TASK_B    # C blocked by B
```

### 4. No Orphan Issues

Every issue should be connected to the work graph — either as a child of an epic or with dependencies to related work. Stray issues get lost.

### 5. Comprehensive Descriptions

Write descriptions that stand alone — an agent should be able to work from the issue without reading external documents. **Write like a PM, not an engineer.** Focus on outcomes and context, not technical implementation details (those can change).

**Bad (too terse, too technical):**
> `id, name, created_at, deleted_at (soft delete)`

**Good (PM-style, comprehensive):**

> ## Purpose
> Store client entities for the multi-tenant system. Clients are the top-level organizational unit — all data (emails, docs, slack messages) is scoped to a client.
>
> ## Why This Matters
> Without clients, we can't isolate customer data. This is foundational for the entire data model.
>
> ## Requirements
> - Each client has a unique ID and human-readable display name
> - Support soft-delete (deleted clients hidden from queries but data preserved for compliance)
> - Track creation and modification timestamps for audit trail
>
> ## Acceptance Criteria
> - [ ] Can create a new client with name
> - [ ] Can list all active (non-deleted) clients
> - [ ] Can retrieve a client by ID
> - [ ] Can soft-delete a client (sets deleted_at, excluded from normal queries)
> - [ ] Timestamps auto-populated on create/update
>
> ## Context
> This is part of Phase 2 (PostgreSQL Schema). Must be created before domain mappings table which references clients.

**Key principles:**
- **Purpose**: What is this and why does it exist?
- **Why This Matters**: Context for prioritization and understanding
- **Requirements**: What must it do? (outcomes, not implementation)
- **Acceptance Criteria**: How do we know it's done?
- **Context**: Dependencies, related work, where this fits

---

## Essential Commands

### Create Issues

```bash
bd create "Title" -t <type> -p <priority> --description "..." --json
bd create "Title" -t task --parent <epic-id> --json                    # As child of epic
bd create "Title" --deps discovered-from:<id>,blocks:<id> --json       # With multiple deps
```

**Types:** `task`, `bug`, `epic`, `feature`, `chore`

**Priority:** `0` (critical) to `4` (backlog). Use numbers, not words.

### Update Issues

```bash
bd update <id> --status in_progress --json
bd update <id> --claim --json                    # Atomically claim (set assignee + in_progress)
bd update <id> --description "New desc" --json
bd update <id> --parent <new-parent-id> --json   # Reparent
```

**Statuses:** `open`, `in_progress`, `blocked`, `deferred`, `closed`

**Status lifecycle:**
```
open → in_progress    (starting work)
in_progress → blocked (dependency discovered)
blocked → in_progress (blocker resolved)
in_progress → closed  (work complete)
```

Keep status current so `bd ready` and `bd blocked` reflect reality.

### Close Issues

```bash
bd close <id> --reason "Why it's done" --json
bd close <id> --suggest-next                     # Show newly unblocked issues
bd reopen <id> --reason "Why reopening" --json   # Reopen a closed issue
```

### View Issues

```bash
bd ready                              # What's ready to work on (no open blockers)
bd blocked                            # Issues waiting on dependencies
bd show <id>                          # Full issue details
bd list --status open --pretty        # List open issues as tree
bd list --parent <epic-id>            # Children of an epic
```

### Dependencies

```bash
bd dep add <issue> <depends-on>       # issue is blocked by depends-on (blocks type)
bd dep add <issue> <dep> -t <type>    # With specific type
bd dep list <id>                      # List dependencies of an issue
bd dep list <id> --direction up       # List what depends on this issue
bd dep remove <issue> <depends-on>    # Remove a dependency
bd dep tree <id>                      # Visualize dependency tree
bd dep tree <id> --direction up       # Show what depends on this issue
```

**Dependency types:**

| Type | Affects `bd ready`? | Purpose |
|------|---------------------|---------|
| `blocks` | **Yes** | Hard blocker — issue can't start until dependency closes |
| `parent-child` | No | Hierarchy — structural grouping (epic/subtasks) |
| `related` | No | Soft link — informational context |
| `discovered-from` | No | Provenance — tracks where issue was found |

**Only `blocks` affects execution order.** Other types provide structure and context.

### Choosing Dependency Type

**Decision tree:**
```
Does A prevent B from starting?
  YES → blocks (A blocks B: `bd dep add B A`)
  NO  ↓

Is B a subtask of A (epic/task relationship)?
  YES → parent-child (use `--parent A` when creating B)
  NO  ↓

Was B discovered while working on A?
  YES → discovered-from (`bd dep add B A -t discovered-from`)
  NO  ↓

Are A and B just related?
  YES → related (`bd dep add B A -t related`)
```

**Direction mnemonic:** `bd dep add <blocked> <blocker>` — the first issue is blocked BY the second.

Think: "prerequisite blocks dependent" — so `bd dep add B A` means "B is blocked by A" (A is the prerequisite).

### Graph Visualization

```bash
bd graph <epic-id>                    # ASCII graph of epic and children
```

---

## Common Patterns

### Breaking Down Work (Ready Front Model)

Think in **Ready Fronts**, not phases. Walk backward from the goal:

1. "What's the final deliverable?" → Create epic
2. "What does that need?" → Create tasks, working backward
3. Add `blocks` deps using requirement language: "X needs Y" → `bd dep add X Y`
4. `bd ready` shows current Ready Front; as issues close, front advances

```bash
# Walk backward: Tests need Implementation needs Design
EPIC=$(bd create "Feature X" -t epic --json | jq -r .id)
T1=$(bd create "Design" -t task --parent $EPIC --json | jq -r .id)
T2=$(bd create "Implement" -t task --parent $EPIC --json | jq -r .id)
T3=$(bd create "Test" -t task --parent $EPIC --json | jq -r .id)

# Requirement language: "Implement needs Design", "Test needs Implement"
bd dep add $T2 $T1    # Implement blocked by Design
bd dep add $T3 $T2    # Test blocked by Implement

# Ready Front 1: Design (no deps)
# Ready Front 2: Implement (after Design closes)
# Ready Front 3: Test (after Implement closes)
```

### Discovered Work

When you find bugs or new work while working on an issue:

```bash
bd create "Found: memory leak in cache" -t bug -p 1 --deps discovered-from:$CURRENT_ISSUE --json
```

### Working Through Issues

```bash
# 1. See what's ready
bd ready

# 2. Claim an issue
bd update <id> --claim --json

# 3. Do the work
# ...

# 4. Close when done
bd close <id> --reason "Implemented and tested" --suggest-next
```

---

## Pitfalls to Avoid

1. **Forgetting `--json`** — You need the ID to reference the issue later
2. **Assuming hierarchy = sequence** — `--parent` creates structure only; add `blocks` deps for order
3. **Inverting dependency direction** — "B blocked by A" means `bd dep add B A`, not `bd dep add A B`
4. **Using blocks for preferences** — Only use `blocks` for actual technical dependencies where work literally cannot proceed
5. **Over-using blocks** — If everything blocks everything, no parallel work is possible. Use `blocks` sparingly.
6. **Using discovered-from for planning** — For planned task breakdown, use `--parent`. Use `discovered-from` only for emergent discoveries during work.
7. **Terse descriptions** — Future agents (including you after context loss) need full context
8. **Orphan issues** — Always connect issues to the work graph

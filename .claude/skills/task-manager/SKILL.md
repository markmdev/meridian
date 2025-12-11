---
name: task-manager
description: Create and manage development tasks after the user approves a plan. Initializes folders/files, updates the backlog, and keeps progress notes synchronized.
---
<task_manager>
# Task Manager Skill

## When to Use
Immediately after a plan is approved. The script scaffolds the task folder and registers the work in the backlog. Skip this skill for speculative ideas or unapproved work.

### New Task vs Continue Existing

**Create a NEW task when:**
- Different objective or deliverable
- Major pivot in approach (warrants fresh context)
- Unrelated follow-up work

**Continue EXISTING task when:**
- Same goal, additional work discovered
- Bug found during implementation (add to current task)
- Scope refinement without changing objective

When in doubt: if the same context.md would serve both pieces of work, continue the existing task.

---

## Workflow

### Create the task
```bash
python3 .claude/skills/task-manager/scripts/create-task.py
```
The script auto-detects project root by walking up to find `.claude/` and `.meridian/` directories.
Creates `.meridian/tasks/TASK-###/` with:
- `TASK-###-context.md` — the primary source of truth for task state and history

IDs are zero-padded (`TASK-001`). Read the file before editing.

### Populate context.md
This is the main file. A new agent reading it should immediately understand the full picture.

**Structure:**
```markdown
# TASK-### Context

## Origin
Why this task was created, key constraints from planning, alternatives considered.

## Status
- **Current state**: planning | in_progress | blocked | done
- **Blockers**: none | description

## Key Decisions & Tradeoffs
- [Decision]: [Rationale]

## Session Log
### YYYY-MM-DD
- What was done
- Issues discovered
- Next steps

## References
- Related: TASK-045
- Docs: design-doc.md
```

Document:
- Important decisions and tradeoffs (with rationale)
- User discussions and their outcomes
- Issues discovered during implementation
- Links to related tasks, files, external docs

### Register in the backlog
Add an item to `.meridian/task-backlog.yaml`:
```yaml
- id: TASK-###
  title: "Action-oriented title"
  priority: P1
  status: todo
  path: ".meridian/tasks/TASK-###/"
  plan_path: "/absolute/path/to/.claude/plans/plan-name.md"
```

Allowed values:
- `status`: `todo | in_progress | blocked | done`
- `priority`: `P0 | P1 | P2 | P3`

---

## During Execution
- Switch backlog status to `in_progress` when coding starts; use `blocked` with a note in context if waiting.
- **Append to** `TASK-###-context.md` — never overwrite previous content. The file is a chronological log preserving full task history.
- Add timestamped entries for each session:
  - What was done
  - Decisions made with rationale
  - Issues discovered
  - "MEMORY:" candidates (then call `memory-curator`)
- Use `memory-curator` for durable facts (architecture shifts, lessons learned, traps to avoid). Never edit `.meridian/memory.jsonl` manually.

---

## Finishing
Mark `done` only when all conditions hold:
- Code builds, lint/tests pass, migrations applied.
- Docs updated (README, API refs, etc.) if behavior changed.
- Backlog entry set to `done`.
- Durable insights recorded via `memory-curator`.

---

## Plan or Scope Changes
- Re-seek approval for any material change.
- The plan file (in `.claude/plans/`) is managed by Claude Code.
- Log rationale and links in `TASK-###-context.md`.
</task_manager>

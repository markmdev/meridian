---
name: task-manager
description: Create and manage development tasks after the user approves a plan. Initializes folders/files and updates the backlog.
---
<task_manager>
# Task Manager Skill

## When to Use
Immediately after a plan is approved. The script scaffolds the task folder and registers the work in the backlog. Skip this skill for speculative ideas or unapproved work.

### New Task vs Continue Existing

**Create a NEW task when:**
- Different objective or deliverable
- Major pivot in approach
- Unrelated follow-up work

**Continue EXISTING task when:**
- Same goal, additional work discovered
- Bug found during implementation
- Scope refinement without changing objective

---

## Workflow

### Create the task
```bash
python3 .claude/skills/task-manager/scripts/create-task.py
```
The script auto-detects project root by walking up to find `.claude/` and `.meridian/` directories.
Creates `.meridian/tasks/TASK-###/` for storing plans, design docs, and task-specific artifacts.

IDs are zero-padded with random suffix (`TASK-001-x7k3`) for worktree safety.

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
- Switch backlog status to `in_progress` when coding starts; use `blocked` if waiting.
- Save important context to `.meridian/session-context.md` (rolling file, always available).
- Use `memory-curator` for durable facts (architecture shifts, lessons learned). Never edit `.meridian/memory.jsonl` manually.

---

## Finishing
Mark `done` only when all conditions hold:
- Code builds, lint/tests pass, migrations applied.
- Docs updated if behavior changed.
- Backlog entry set to `done`.
- Durable insights recorded via `memory-curator`.

---

## Plan or Scope Changes
- Re-seek approval for any material change.
- The plan file (in `.claude/plans/`) is managed by Claude Code.
</task_manager>

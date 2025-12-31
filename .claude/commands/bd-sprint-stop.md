---
allowed-tools: Bash(python3:*)
description: End Beads sprint workflow and remove workflow section from session-context
---

!`python3 .claude/scripts/bd-sprint-stop.py`

# End Beads Sprint Workflow

This command removes the Beads Sprint Workflow section from session-context.md.

## Before Running

Verify the sprint is complete:
1. All issue checkboxes are checked `[x]`
2. All reviews passed (score >= 9)
3. All verification commands passed (typecheck, lint, build)
4. Epic closed in Beads (if applicable)
5. Final session context entry added summarizing the work

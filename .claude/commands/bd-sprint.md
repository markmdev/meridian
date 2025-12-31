---
allowed-tools: Bash(python3:*)
description: Start autonomous Beads sprint workflow
---

!`python3 .claude/scripts/bd-sprint-init.py`

# Beads Sprint - Autonomous Workflow

This command starts an autonomous workflow for completing Beads work (epic, issue with dependencies, or any scoped work).

## Before Proceeding

1. **Verify work is defined**: Did the user discuss specific work before running this command?
2. **If no prior context**:
   - Ask: "What epic or issue do you want to complete? Should I check `bd ready` for available work?"
   - Use `bd show <id>` and `bd dep tree <id>` to understand scope and dependencies
   - Get user confirmation on the scope before proceeding
3. **Do NOT blindly start working** - the user must confirm the scope first

## After Scope is Confirmed

1. Fill in the `[FILL IN]` sections in the workflow template (now in session-context.md)
2. Begin working through the Per-Issue Workflow
3. The workflow survives context compaction - check progress and continue after any reset

---
description: Start a work-until loop that keeps you working on a task until completion
argument-hint: TASK [--completion-phrase "TEXT"] [--max-iterations N]
allowed-tools: Bash
---

# Work-Until Loop

!`[ -f .meridian/scripts/setup-work-until.sh ] || { echo "Error: Run /work-until from project root directory" >&2; exit 1; }; .meridian/scripts/setup-work-until.sh $ARGUMENTS`

!`cat .meridian/prompts/work-until-loop.md`

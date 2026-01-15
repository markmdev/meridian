---
description: Handle CodeRabbit AI review cycles after creating a PR
allowed-tools: Bash
---

# CodeRabbit Review Loop

!`[ -f .claude/hooks/scripts/setup-work-until.sh ] || { echo "Error: Run /coderabbit-review from project root directory" >&2; exit 1; }; .claude/hooks/scripts/setup-work-until.sh "$(cat .meridian/prompts/coderabbit-task.md)" --completion-phrase "All CodeRabbit issues addressed" --max-iterations 20`

!`cat .meridian/prompts/work-until-loop.md`

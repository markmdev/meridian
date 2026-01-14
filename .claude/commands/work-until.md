---
description: Start a work-until loop that keeps you working on a task until completion
argument-hint: TASK [--completion-phrase "TEXT"] [--max-iterations N]
allowed-tools: "Bash"
---

# Work-Until Loop

Execute the setup script:

!`[ -f .claude/hooks/scripts/setup-work-until.sh ] || { echo "Error: Run /work-until from project root directory" >&2; exit 1; }; .claude/hooks/scripts/setup-work-until.sh $ARGUMENTS`

You are now in a **work-until loop**. This means:

1. **You cannot stop** until the completion condition is met
2. **The stop hook will block** your exit and resend the task
3. **Between iterations**, you'll do the normal stop hook checks (memory, session context, tests, etc.)

## How the Loop Works

- Each time you try to stop, the stop hook intercepts
- It checks if you've output `<complete>PHRASE</complete>` with the exact completion phrase
- If not (and max iterations not reached), it blocks and resends your task
- You continue working with full context of what you've done (via session-context.md)

## To Exit the Loop

Output the completion phrase in XML tags:
```
<complete>Your completion phrase here</complete>
```

**CRITICAL**: The phrase must be TRUE. Do not output false statements to escape.

## Now: Start Working

Read `.meridian/.loop-state` to see your task and settings, then begin working.

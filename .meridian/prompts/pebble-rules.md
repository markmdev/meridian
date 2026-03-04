# Pebble Issue Tracking

**Every code change maps to an issue.** Issues are audit records. Even a 30-second bug fix: create issue → fix → comment with file:line → close.

## Work Loop

```
pb ready              # What's unblocked
pb claim <id>         # Start work (one at a time)
# ... implement ...
pb comments add <id> "Done: file:line changes, tests added"
pb close <id> --reason "Implemented"
```

## Rules

1. **One task at a time.** Only one issue `in_progress`. Transition current before claiming another.
2. **Comment before closing.** Every close needs file paths, line numbers, and what was done.
3. **Every code change gets an issue.** No issue = invisible fix.
4. **Dependencies = "blocked by."** `pb dep add B A` means B needs A first. Prefer `--blocked-by`/`--blocks` flags for clarity.
5. **Parent is not sequence.** `--parent` creates hierarchy. Use `pb dep add` for ordering.
6. **No orphans.** Every issue connects to a parent epic or has dependencies.
7. **Comprehensive descriptions.** Write like a PM: purpose, requirements, acceptance criteria.
8. **Plan decomposition.** If an approved plan has phases/steps, create child Pebble tasks for each with dependencies. One `in_progress` at a time.

Use `pb --help` and `pb <command> --help` for command reference.

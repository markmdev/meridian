# Worktree Context

High-level context shared across all git worktrees. When working in a feature worktree, summarize significant work here so the main branch retains knowledge after the worktree is removed.

## What to Save

- Major features completed and key implementation decisions
- Architectural changes that affect other parts of the codebase
- Important discoveries that other worktrees should know about
- Summary of what was accomplished (not detailed technical notes)

## What NOT to Save

- Detailed implementation notes (use session-context.md in the worktree)
- In-progress work details
- Content that's already in commit messages

## Entry Format

```
## [branch-name] YYYY-MM-DD - Brief Title

Working on: [Epic/Task ID and name]

What was done, what issues were encountered, current state of the work.
```

**Start with context**: What task/epic were you working on? Then explain what was accomplished, any problems found, and where things stand now.

---
<!-- WORKTREE ENTRIES START - entries from all worktrees below -->


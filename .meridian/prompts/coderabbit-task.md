CodeRabbit AI reviews PRs automatically after creation. First review takes up to 7 minutes — check CI status ('pending' = in progress).

## Comment Types

- **Critical, Major, Minor, Outside diff range** — must fix
- **Nitpick** — skip (style preferences)

## Workflow

1. Fetch CodeRabbit comments from PR
2. Group comments by file
3. Spawn **implement** agents in parallel — one agent per file, all that file's issues in one spec
4. Commit and push
5. Reply to each comment explaining the fix
6. Wait for next review cycle (CodeRabbit re-reviews on push)
7. Repeat until CodeRabbit has no remaining issues and CI passes

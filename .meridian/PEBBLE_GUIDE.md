# Pebble Guide

Git-backed issue tracker for AI agents. Track all work as Pebble issues.

## Quick Reference

```bash
pb ready                    # Show unblocked issues (start here)
pb list --status in_progress  # What's being worked on
pb blocked                  # Issues waiting on dependencies
pb show <id>                # Issue details

pb create "Title" -t task -p 1 --parent $EPIC | jq -r .id
pb claim <id>               # Set in_progress + assignee
pb update <id> --status blocked
pb comments add <id> "What was done, file:line"
pb close <id> --reason "Done"

pb dep add <blocked> <blocker>  # First issue blocked BY second
pb dep tree <id>
```

**Types:** `task`, `bug`, `epic`, `verification` | **Priority:** 0 (critical) to 4 (backlog) | **Status:** `open`, `in_progress`, `blocked`, `pending_verification`, `closed`

---

## Core Rules

### 1. One Task at a Time
Only ONE issue `in_progress`. Transition current issue (block/close) before claiming another.

### 2. Comment Before Closing
Every close needs a comment with file paths, line numbers, and what was done. No comment = work isn't verified.

```bash
pb comments add <id> "Implemented X in src/foo.ts:45-78. Tests in foo.test.ts."
pb close <id> --reason "Done"
```

### 3. Every Code Change Gets an Issue
Found and fixed a bug? Create issue → fix → comment → close. Issues are audit records. No issue = invisible fix.

### 4. Dependencies: Blocked BY
`pb dep add B A` means "B is blocked by A" (A must close before B is ready).

**Think:** "B needs A" → `pb dep add B A`

### 5. Parent ≠ Sequence
`--parent` creates hierarchy only. Children run in parallel unless you add explicit `pb dep add` between them.

### 6. No Orphans
Every issue connects to the work graph (parent epic or dependencies).

### 7. Comprehensive Descriptions
Write like a PM: Purpose, Why It Matters, Requirements, Acceptance Criteria. Future agents need full context.

---

## Verification Issues

Verification issues are post-completion checks — they become ready AFTER their target is closed.

```bash
# Create verification that targets a task
pb create "User can log in" --verifies $TASK_ID

# List verifications for an issue
pb verifications $TASK_ID

# Ready verifications (target closed, verification open)
pb ready --type verification
```

### Ready Behavior

| Target Status | Verification Status | In `pb ready`? |
|---------------|---------------------|----------------|
| open | open | No |
| closed | open | **Yes** |
| closed | closed | No |

### Creating Verifications from Plans

When plans have **Verification Features** (from feature-writer), each feature becomes a verification issue:

```bash
TASK=$(pb create "Implement login" -t task --parent $PHASE | jq -r .id)

# Each feature = verification issue targeting the task
pb create "User can log in with valid credentials" --verifies $TASK \
  --description "Navigate to /login, enter valid creds, verify redirect to dashboard"
pb create "Invalid password shows error" --verifies $TASK \
  --description "Navigate to /login, enter wrong password, verify error message"
```

### Performing Verification

When a verification appears in `pb ready`, its target is done. **You perform the verification:**

1. Follow the steps in the description
2. Capture evidence (screenshots, responses, output)
3. Comment with proof
4. Close if passing, or create bug if failing

**Evidence varies by type:**
- **UI**: Screenshot or description of what you observed
- **API**: Request sent, response received (status, body)
- **CLI**: Command run, output produced
- **Data**: Query executed, results returned

```bash
# Good: evidence included
pb comments add $ID "POST /login with valid creds → 200, session cookie set, redirected to /dashboard"
pb close $ID --reason "Verified"

# Bad: no evidence
pb comments add $ID "Works"
```

**If verification fails:** Don't close. Create a bug issue, link it, fix, then re-verify.

### Pending Verification Status

When you close an issue that has open verification issues targeting it, it goes to `pending_verification` instead of `closed`. This enforces that verification actually happens.

```bash
pb close $TASK_ID --reason "Implementation done"
# Output: Issue set to pending_verification. Pending: BEAD-abc123, BEAD-def456

# Complete the verification issues first
pb close BEAD-abc123 --reason "Verified"
pb close BEAD-def456 --reason "Verified"

# Now the task auto-closes, or close it again
pb close $TASK_ID --reason "All verifications passed"
```

---

## Related Links

Use `pb dep relate` for issues that share context but don't block each other. Unlike `blocks`, related links are bidirectional and don't affect `pb ready`.

```bash
# Link related issues (bidirectional, non-blocking)
pb dep relate $ISSUE1 $ISSUE2

# Remove the link
pb dep unrelate $ISSUE1 $ISSUE2

# View all dependencies including related
pb dep list $ISSUE1
```

**Use cases:**
- Issues that touch the same code but can run in parallel
- Cross-references for context without ordering requirements
- Grouping conceptually linked issues

---

## Common Workflows

### Create Epic with Tasks

```bash
EPIC=$(pb create "Feature X" -t epic | jq -r .id)
T1=$(pb create "Design" -t task --parent $EPIC | jq -r .id)
T2=$(pb create "Implement" -t task --parent $EPIC | jq -r .id)
T3=$(pb create "Test" -t task --parent $EPIC | jq -r .id)

# Sequence them (otherwise parallel)
pb dep add $T2 $T1    # Implement needs Design
pb dep add $T3 $T2    # Test needs Implement
```

### Discovered Blocker

```bash
NEW=$(pb create "Found: auth needs refactor" -t bug -p 1 | jq -r .id)
pb dep add $CURRENT $NEW    # Current blocked by new
pb update $CURRENT --status blocked
pb claim $NEW               # Work on blocker
```

### Work Loop

```bash
pb ready                    # What's unblocked
pb claim <id>               # Start work
# ... implement ...
pb comments add <id> "Done: file:line, tests added"
pb close <id> --reason "Implemented"
```

---

## Pitfalls

| Don't | Do |
|-------|-----|
| Multiple `in_progress` | One at a time, transition before switching |
| Close without comment | Comment with file:line first |
| Fix without issue | Create issue → fix → comment → close |
| `pb dep add A B` for "A before B" | `pb dep add B A` — B blocked BY A |
| Assume `--parent` sequences | Add explicit deps for order |
| Terse descriptions | PM-style: purpose, requirements, acceptance criteria |

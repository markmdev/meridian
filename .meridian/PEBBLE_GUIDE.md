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

**Types:** `task`, `bug`, `epic` | **Priority:** 0 (critical) to 4 (backlog) | **Status:** `open`, `in_progress`, `blocked`, `closed`

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

## Verification Subtasks

When plans have **Verification Features** (from feature-writer), each feature becomes a subtask:

```
Task: Implement auth
├── User can register with email and password
│   description: Navigate to /register, fill form, submit, check redirect
├── Invalid login shows error message
│   description: Navigate to /login, enter wrong password, verify error
└── ...
```

Parent can't close until all children close.

```bash
TASK=$(pb create "Implement auth" -t task --parent $EPIC | jq -r .id)

# Each feature = subtask with steps in description
pb create "User can register with email" -t task --parent $TASK \
  --description "Navigate to /register, fill form, submit, check redirect"
pb create "Invalid login shows error" -t task --parent $TASK \
  --description "Navigate to /login, enter wrong password, verify error"
```

### Verifying and Closing

**You perform the verification.** Follow the steps in the description, capture evidence, comment, then close.

**Evidence varies by verification type:**
- **UI**: Screenshot or description of what you observed
- **API**: Request sent, response received (status, body)
- **CLI**: Command run, output produced
- **Data**: Query executed, results returned

**The comment must contain proof**, not just "verified" or "works". Future agents need to see what was actually tested.

```bash
# Good: evidence included
pb comments add $ID "Sent POST /api/users with {name:'test'}. Got 201, user ID 42 returned. Verified user exists in DB."
pb close $ID --reason "Verified"

# Bad: no evidence
pb comments add $ID "Tested and it works"
```

**If verification fails:** Don't close. Create a bug issue, link it as a blocker, and fix before re-verifying.

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

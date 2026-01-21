---
name: planning
description: Create implementation plans through deep exploration and understanding. Use for new features, refactoring, architecture changes, or any non-trivial work.
---
<planning_skill>
# Planning Skill

**Plans are documentation of understanding, not templates to fill out.**

A good plan proves you understand the problem deeply. A bad plan follows a structure without understanding. There is no "standard" plan size or format — the plan should match the complexity of what you're building.

## Verbatim Requirements (WRITE FIRST)

Before anything else, capture the user's exact words at the top of the plan file.

**DO NOT paraphrase. DO NOT compress. DO NOT summarize.**

```markdown
## Verbatim Requirements

### Original Request
> [User's ENTIRE message, word for word]

### Clarifications
**Q:** [Your question]
**A:** [User's ENTIRE answer, verbatim]

### Additional Context
> [EVERY follow-up message from the user]
```

Capture ALL exchanges. You don't know which details matter until implementation.

## The Core Loop: Explore Until You Understand

Planning is not a sequence of phases. It's a loop:

```
ASK → EXPLORE → LEARN → HAVE MORE QUESTIONS? → REPEAT
```

**Keep looping until you can explain:**
- What data exists and what shape it takes
- How data flows through the system
- What the current behavior is (precisely)
- What needs to change and why
- What could go wrong

If you can't explain these clearly, you haven't explored enough.

## Interviewing the User

Interview iteratively: 2-4 questions → answers → deeper follow-ups → repeat.

**Don't ask everything upfront.** Ask, learn, then ask smarter questions based on what you learned.

**Depth varies:** Simple bug? 3-5 questions. Complex feature? 20-40+ questions across multiple rounds.

**Cover:**
- What exactly should happen (inputs, outputs, behavior)
- What's out of scope
- Edge cases and error scenarios
- Constraints (performance, compatibility, security)
- Why this matters (context helps you make better decisions)

**Push back** if something seems wrong. You're the technical expert.

## Exploring the Codebase

**Spawn as many Explore agents as you need.**

If you have 5 distinct questions, spawn 5 agents. If you have 15, spawn 15. Don't artificially limit yourself to 2-3 agents when the codebase is large and your questions span different areas.

**Run follow-ups.** When agents return findings that raise new questions — and they will — spawn more agents to investigate those questions. Exploration is iterative, not one-shot.

**What to explore:**
- How does the current system work? (trace actual code paths)
- What data structures exist? (schemas, types, shapes)
- How do similar features work? (find patterns to follow)
- What depends on what? (imports, calls, data flow)
- What are the constraints? (validation, permissions, limits)

**Explore until you stop having questions**, not until you've "done enough exploring."

## What Plans Must Contain

Plans document your understanding. They should include:

**Data specifics:**
- What tables/collections/files are involved
- What fields matter and what they contain
- What the actual data looks like (examples help)
- What transformations happen

**Flow specifics:**
- How data moves through the system
- What functions/endpoints are called in what order
- Where state changes happen
- What triggers what

**Decision specifics:**
- Why this approach over alternatives
- What tradeoffs you're making
- What assumptions you're relying on
- What could break this

**Change specifics:**
- Every file to create, modify, or delete
- What each change accomplishes
- How changes connect to each other
- What order changes must happen in
- What existing patterns and code to reuse

## What Plans Should NOT Be

**Not a template.** There's no "7 phases" or "standard structure." A plan for a simple rename might be 20 lines. A plan for a complex feature might be 2000 lines. Size matches complexity.

**Not vague.** "Update the data layer" is not a plan step. "Add `reconciled_at` timestamp to `transactions` table, update `TransactionService.reconcile()` to set it, add index for queries" is.

**Not deferred.** If the plan says "TBD" or "figure out during implementation," you haven't planned — you've procrastinated. Investigate NOW.

## External APIs

Before using any external library/API, check `.meridian/api-docs/INDEX.md`.

- Listed? Read the doc.
- Not listed? Run `docs-researcher` first.

Your training data is outdated. Always verify.

## Integration (Multi-Module Work)

If your plan creates new modules or touches multiple systems, explicitly document:

- How modules connect (imports, calls, data passing)
- Entry points (how does the app load/call this?)
- Configuration (what needs to be set up)

Plans fail when code exists but isn't wired up.

## Testing

Ask the user what testing depth they want:
- **Light** — happy path only
- **Standard** — happy path + key edge cases
- **Thorough** — comprehensive coverage
- **Skip** — no tests

Include in the plan what gets tested and how.

## Documentation

If it changes behavior users see:
- Update CLAUDE.md for the module
- Update human docs (README, API docs, etc.)

## Quality Check

Before finalizing, verify:

- [ ] Verbatim requirements captured (original request + all Q&A)
- [ ] User confirmed understanding of requirements
- [ ] Explored until questions stopped (not just "explored some")
- [ ] Data specifics documented (tables, fields, shapes, examples)
- [ ] Flow specifics documented (what calls what, in what order)
- [ ] Every file path verified or confirmed as new
- [ ] External APIs documented in api-docs
- [ ] No "TBD" or "investigate later" anywhere
- [ ] Plan size matches actual complexity (not a template)
</planning_skill>

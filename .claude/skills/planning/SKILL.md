---
name: planning
description: Create implementation plans through deep exploration and understanding. Use for new features, refactoring, architecture changes, or any non-trivial work.
---

# Planning

Good plans prove you understand the problem. Bad plans follow templates without understanding. Size matches complexity — a rename might be 20 lines, a complex feature might be 500.

**The handoff test:** Could someone implement this plan without asking you questions? If not, find what's missing.

## Verbatim Requirements

Capture the user's exact words at the top of every plan. No paraphrasing, no compression, no summarization.

```markdown
## Verbatim Requirements

### Original Request
> [User's ENTIRE message, word for word]

### Clarifications
**Q:** [Your question]
**A:** [User's ENTIRE answer, verbatim]
```

You don't know which details matter until implementation. Capture everything.

## The Core Loop

Planning is a loop, not a sequence:

```
ASK → EXPLORE → LEARN → MORE QUESTIONS? → REPEAT
```

Keep looping until you can explain: what data exists, how it flows, what needs to change, and what could go wrong. If you can't explain these clearly, explore more.

## Interviewing

Interview iteratively: 2-4 questions → answers → deeper follow-ups → repeat. Don't ask everything upfront.

**Depth varies:** Simple bug → 3-5 questions. Complex feature → 20-40+ questions across multiple rounds.

**Cover:** What should happen (inputs, outputs, behavior), what's out of scope, edge cases, constraints, and why this matters.

**Push back** if something seems wrong. You're the technical expert.

## Exploring the Codebase

**More exploration = better plans.** The number one cause of plan failure is insufficient exploration.

**Spawn many Explore agents — 5, 10, 15, whatever the codebase demands.** Each question or area gets its own agent. Don't batch unrelated questions hoping for efficiency.

| Task | Agents |
|------|--------|
| Small bugfix | 1-2 |
| Feature touching 3 modules | 5-8 |
| Major refactor or new system | 10-20 |
| "I'm not sure where to start" | 5 broad, then more based on findings |

**Run follow-ups aggressively.** Every finding that raises questions spawns more exploration. Expect 2-3 rounds before you're ready to plan.

**Explore until you stop having questions**, not until you've "done enough."

## Plan Content

Plans document your understanding. Include:

**Data:** Tables/collections involved, fields that matter, what the data looks like (examples help), transformations.

**Flow:** How data moves through the system, what calls what in what order, where state changes, what triggers what, entry point context.

**Decisions:** Why this approach, what tradeoffs, what assumptions, what could break.

**Changes:** Every file to create/modify/delete, what each change accomplishes, how changes connect, what order they must happen, existing patterns to reuse.

**Acceptance criteria:** What must be true when each step is "done." Specific ("returns object with `status` field"), not vague ("works correctly").

**Test cases:** For behavioral changes, include example inputs → expected outputs.

## ASCII Diagrams

For visual concepts, draw ASCII diagrams. They're clearer than descriptions.

**UI changes:** Draw the interface with sample data and edge cases.
```
┌─────────────────────────────────┐
│ User Profile                    │
├─────────────────────────────────┤
│ Name: John Doe                  │
│ Role: [Admin ▼]                 │
│                                 │
│ [Save]  [Cancel]                │
└─────────────────────────────────┘

Edge case (long name):
┌─────────────────────────────────┐
│ Name: Bartholomew Fitzgerald... │
└─────────────────────────────────┘
```

**Data flow:** Show how data moves through the system.
```
Request → AuthMiddleware → Controller → Service → Database
                ↓                          ↓
           401 if no token           Transform → Response
```

**Architecture:** Show module relationships when relevant.

## Rules

**No TBD.** If the plan says "figure out during implementation," you haven't planned — you've procrastinated. Investigate now.

**No literal code.** Code snippets become brittle. Describe structure instead: "Function that fetches user, validates permissions, returns filtered data." Reference patterns: "Follow the pattern in validateUser."

**External APIs:** Check `.meridian/api-docs/INDEX.md` first. Not listed? Run `docs-researcher`. Your training data is outdated.

**No repetition.** Define schemas once, reference by name. Don't repeat the same structure three times.

## PRD Sections

Include PRD sections (Vision, Problem Statement, User Stories, Feature Spec, MVP Scope) when:
- New project from scratch
- Feature with unclear scope
- Multi-phase work spanning weeks
- User explicitly requests requirements

Skip for bug fixes, small features, refactoring, or when scope is already clear.

## Epic Planning

For large tasks spanning multiple systems or weeks:

**Signals:** "Build X from scratch", multiple subsystems, user says "big project", exploration reveals massive scope.

**When detected, ask:** "This looks like a multi-phase project. Should I create an epic plan with subplans per phase?"

**Epic structure:**
- Phases are epics, not implementation steps
- Each phase gets a subplan (created just-in-time when starting that phase)
- Subplans go through plan-reviewer before implementing
- Epic plan contains all research findings; subplans focus on implementation detail

## Integration

If your plan creates modules or touches multiple systems, document:
- How modules connect (imports, calls, data passing)
- Entry points (how does the app call this?)
- Configuration needed

Plans fail when code exists but isn't wired up.

## Testing

Ask the user: light (happy path), standard (+ key edge cases), thorough (comprehensive), or skip.

## Verification

Every plan ends with verification:

```markdown
## Verification

**Per-step:** `npm run typecheck` passes after step 1
**Checkpoint:** Run code-reviewer after auth changes (step 3)
**End-to-end:** Create user, assign role, verify permissions work
```

For large plans (5+ phases), include intermediate review checkpoints.

## Execution Table

Every plan ends with an execution table:

```markdown
## Execution

| Step | Agent | Parallel |
|------|-------|----------|
| 1.1 | implement | A |
| 1.2 | implement | A |
| 2.1 | refactor | B |
| 2.2 | test-writer | - |
```

**Agents:** `implement` (new code), `refactor` (moves/renames), `test-writer` (tests), `main` (coordination)

**Parallel:** Steps in same group run simultaneously. `-` means sequential.

Each step must contain enough detail for the agent to execute without questions.

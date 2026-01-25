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

## PRD vs Implementation Plan

Plans have two parts:

1. **PRD sections** — What to build and why (Vision, Problem, User Stories, Feature Spec, MVP Scope)
2. **Implementation sections** — How to build it (Files, Steps, Verification)

**When to include PRD sections:**
- New project from scratch
- New feature with unclear scope (user stories not obvious)
- Multi-phase work spanning weeks
- User explicitly requests "requirements" or "PRD"

**When to skip PRD sections:**
- Bug fixes
- Small, well-defined features
- Refactoring
- Changes where scope is already clear

**If PRD criteria detected:**
Ask: "This looks like it needs requirements definition. Should I include PRD sections (Vision, Problem, User Stories, Feature Spec) in the plan?"

### PRD Sections Structure

```markdown
## Vision

What this is and why it matters. 1-2 paragraphs.

## Problem Statement

**User:** Who is this for?

**Pain points:**
1. ...
2. ...

**Current workflow:** How they handle this today.

## User Stories

### [Category]
- **As a [user]**, I want [goal] so I can [benefit].

## Feature Specification

### 1. [Feature Area]

Detailed breakdown:
- Data fields and sources
- Display format
- Actions available
- Edge cases

(Use tables where helpful)

## MVP Scope

**Must have (v0.1):**
- [ ] Feature 1
- [ ] Feature 2

**Nice to have (v0.2+):**
- [ ] Future feature 1

## Open Questions

1. Unknowns to resolve before implementation
```

### PRD Quality Check

- [ ] Vision is clear and compelling
- [ ] Problem statement names specific user and pain points
- [ ] User stories cover all user types and workflows
- [ ] Feature spec is detailed enough to estimate work
- [ ] MVP scope has clear boundaries
- [ ] Open questions are genuine unknowns (not things to research now)
- [ ] No implementation details in PRD sections (that comes after)

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

Plans document your understanding. The categories below are starting points — real plans answer every question that would come up during implementation.

**The handoff test:** If you gave this plan to another developer, what would they ask? Answer those questions now.

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
- What context each entry point has (and where it comes from)

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

**Acceptance criteria per step:**
- What must be true when this step is "done"
- Verifiable conditions (compiles, exported, returns expected shape)
- Not vague ("works correctly") — specific ("returns object with `status` field")

**Test cases (for behavioral changes):**
- Example inputs → expected outputs
- Edge cases the plan author has in mind
- Format: "Empty input array → returns empty array, not error"

## What Plans Should NOT Be

**Not a template.** There's no "7 phases" or "standard structure." A plan for a simple rename might be 20 lines. A plan for a complex feature might be 2000 lines. Size matches complexity.

**Not vague.** "Update the data layer" is not a plan step. "Add `reconciled_at` timestamp to `transactions` table, update `TransactionService.reconcile()` to set it, add index for queries" is.

**Not deferred.** If the plan says "TBD" or "figure out during implementation," you haven't planned — you've procrastinated. Investigate NOW.

**Not literal code.** Code snippets become brittle when variable names differ. Instead:
- Describe structure: "Function that fetches user, validates permissions, returns filtered data"
- Reference patterns: "Follow the pattern in existing validateUser function"
- Use placeholders if showing structure: `/* adapt to actual variable names */`

## Anti-Patterns

**Repetition:** Don't define the same schema 3 times. Define once, reference by name.

**Obvious details:** "Add export keyword" doesn't need a step — agents know syntax.

**Incremental changelog:** Don't list every micro-step. Group into meaningful units.

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

## Epic-Level Planning

For large tasks spanning multiple systems or weeks of work:

**Detection signals:**
- "Build X from scratch"
- Multiple distinct subsystems (auth, billing, API, UI)
- User says "this is a big project"
- Initial exploration reveals massive scope

**When detected, propose epic planning:**
"This looks like a multi-phase project. Should I create an epic plan with separate subplans for each phase?"

**Epic planning workflow:**
1. Interview and explore as usual — capture verbatim requirements and all findings
2. Create PRDs and specs (optional) for major areas — requirements, data models, API contracts
3. Create epic plan with phases and the required workflow section (see below)

**Epic plans contain everything:**
- Verbatim requirements (same as any plan)
- All research findings and discoveries
- Phase breakdown with dependencies
- The workflow instructions that the implementing agent must follow

Subplans are for detailed implementation focus on a single phase. They don't replace the discovery work in the epic plan — they build on it.

**Epic plan structure:**
- Phases are epics, not implementation steps
- Reference specs (`.meridian/specs/`) and subplans (`.meridian/subplans/`) by path
- Track phase status: Not started | In progress | Complete

**Required: Include this workflow section at the end of every epic plan:**

```markdown
## Epic Workflow (REQUIRED)

For EACH phase, you MUST follow this workflow. This is not optional.

1. Mark phase status: `In progress`
2. Enter plan mode
3. Create a subplan for this phase
4. Run plan-reviewer on the subplan
5. Get user approval
6. Move approved subplan to `.meridian/subplans/`
7. Implement the subplan
8. Run code-reviewer on the implementation
9. Mark phase status: `Complete`

Do NOT skip the subplan step, even if this epic plan contains detailed specs for the phase. Subplans incorporate learnings from prior phases and get validated against current codebase state.
```

**Specs (optional):**
- Store in `.meridian/specs/`
- Requirements that span multiple phases
- Data models, API contracts, acceptance criteria

**Subplans (required per phase):**
- Created just-in-time when starting each phase
- Moved to `.meridian/subplans/` after approval
- Focused on implementation details for that phase

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

## Verification

Every plan should end with a verification section:

**Per-step checks:** Quick commands to verify each step works
**Review checkpoints:** For large plans (5+ phases), include intermediate code reviews
**End-to-end:** Command to verify the full implementation

Example:
```
## Verification
- Step 1: `npm run typecheck` passes
- After Phase 3: Run code-reviewer on auth module changes
- Step 5: `curl localhost:3001/api/users/1` returns user object with `role` field
- End-to-end: Create user, assign role, verify permissions work
```

Review checkpoints catch issues early when context is fresh, rather than reviewing everything at the end.

## Execution Table

Every plan ends with an Execution table mapping steps to agents and parallel groups.

```markdown
## Execution

| Step | Agent | Parallel Group |
|------|-------|----------------|
| 1.1 | implement | A |
| 1.2 | implement | A |
| 2.1 | implement | B |
| 2.2 | refactor | B |
| 2.3 | test-writer | - |

Steps in same parallel group run simultaneously.
```

**Agent selection:**
- `implement` — New files, new functions, feature implementation
- `refactor` — Renames, moves, extractions across files
- `test-writer` — Test file generation
- `main` — Coordination steps, verification, complex multi-file changes

**Parallel groups:**
- Steps in the same group have no file conflicts or dependencies
- Use letters (A, B, C) or numbers for groups
- `-` means sequential (depends on prior steps)

**Specs must be implementation-ready.** Each step should contain enough detail that the assigned agent can execute without asking questions.

## Finding Gaps

Checklists create false confidence. To find real gaps:

**Simulate execution** — Walk through the code mentally. "Request comes in, then what? I call X. X needs Y. Where does Y come from?" When you hit uncertainty, that's a gap. Investigate it.

**The handoff test** — Could someone implement this plan without asking you questions? If not, find what's missing.

## Quality Check

The real test: **someone could implement this plan without asking clarifying questions.**

The checklist below is a starting point. If you're uncertain whether the plan is complete, simulate implementing it step by step.

- [ ] Verbatim requirements captured (original request + all Q&A)
- [ ] User confirmed understanding of requirements
- [ ] Explored until questions stopped (not just "explored some")
- [ ] Data specifics documented (tables, fields, shapes, examples)
- [ ] Flow specifics documented (what calls what, in what order)
- [ ] Every file path verified or confirmed as new
- [ ] External APIs documented in api-docs
- [ ] No "TBD" or "investigate later" anywhere
- [ ] Plan size matches actual complexity (not a template)
- [ ] Acceptance criteria defined for each step
- [ ] Test cases included for behavioral changes
- [ ] Verification section with concrete commands
- [ ] Review checkpoints for large plans (5+ phases)
- [ ] No literal code snippets (structural descriptions instead)
- [ ] No repeated definitions (define once, reference)
</planning_skill>

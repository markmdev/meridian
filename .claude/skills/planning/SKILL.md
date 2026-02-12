---
name: planning
description: Create implementation plans through deep exploration and understanding. Use for new features, refactoring, architecture changes, or any non-trivial work.
---

# Planning

Good plans prove you understand the problem. Size matches complexity — a rename might be 20 lines, a complex feature might be 500.

**The handoff test:** Could someone implement this plan without asking you questions? If not, find what's missing.

## Verbatim Requirements

Capture the user's exact words at the top of every plan. No paraphrasing, no compression.

```markdown
## Verbatim Requirements

### Original Request
> [User's ENTIRE message, word for word]

### Clarifications
**Q:** [Your question]
**A:** [User's ENTIRE answer, verbatim]
```

## The Core Loop

```
ASK → EXPLORE → LEARN → MORE QUESTIONS? → REPEAT
```

Keep looping until you can explain: what data exists, how it flows, what needs to change, and what could go wrong.

## Interviewing

**Interviewing is the most important part of planning.** You cannot build what you don't understand. Every unasked question is a assumption that will break during implementation.

Interview iteratively: 2-4 questions → answers → deeper follow-ups → repeat. Each round of answers should trigger new, deeper questions. If the answers don't spark follow-ups, you're not thinking hard enough.

Simple bug → 3-5 questions. Complex feature → 20-40+ questions across multiple rounds.

Push back if something seems wrong. You're the technical expert.

## Exploring the Codebase

**More exploration = better plans.** The number one cause of plan failure is insufficient exploration.

Spawn as many Explore agents simultaneously as the task demands — 5, 10, 15, there is no limit. The system default of 3 concurrent agents does NOT apply here. Each question or area gets its own agent, all launched in parallel.

**Follow up aggressively.** When a round of Explore agents completes, read their findings, identify every new question or uncertainty, and immediately spawn another round of agents to investigate those. Expect 2-4 rounds of exploration before you're ready to plan. Findings always raise new questions — if they don't, you're not reading carefully enough.

**Explore until you stop having questions**, not until you've "done enough."

## Plan Content

Plans document your understanding. Include what matters for this specific task:

- **Data**: Tables, fields, transformations, what the data looks like
- **Flow**: How data moves, what calls what, where state changes
- **Decisions**: Why this approach, tradeoffs, assumptions
- **Changes**: Every file to create/modify/delete, how changes connect
- **Acceptance criteria**: What must be true when each step is "done" — specific, not vague
- **Test cases**: For behavioral changes, include input → expected output examples

Use ASCII diagrams when they'd clarify visual concepts, data flow, or architecture.

## Rules

**No TBD.** If the plan says "figure out during implementation," you haven't planned — you've procrastinated. Investigate now.

**No literal code.** Describe structure instead. Reference patterns: "Follow the pattern in validateUser."

**External APIs:** Check `.meridian/api-docs/INDEX.md` first. Not listed? Run `docs-researcher`.

## Epic Planning

For large tasks spanning multiple systems or weeks, propose an epic plan with subplans per phase. Each phase gets a subplan created just-in-time. Subplans go through plan-reviewer before implementing.

## Integration

If your plan creates modules or touches multiple systems, document how they connect: imports, entry points, configuration. Plans fail when code exists but isn't wired up.

## Verification

Every plan ends with verification — commands or checks that prove the implementation works.

## Plan Review

Before exiting plan mode, run the **plan-reviewer** agent. It validates the plan against the actual codebase — checking file paths, APIs, dependencies, and feasibility. The plan must score 9+ to proceed. If below 9, address findings with the user, update the plan, and re-run until passing.

## TLDR

End every plan with a TLDR — 2-4 sentences that capture what you're building, the approach, and why. Anyone should be able to read just the TLDR and understand what this plan accomplishes.

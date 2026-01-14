---
name: planning
description: Create comprehensive implementation plans for complex tasks. Use when in Plan mode, for new features, refactoring efforts, architecture changes, bug fixes with unclear scope, or any work touching multiple files/systems.
---
<planning_skill>
# Planning Skill

Great plans come from deep understanding. Superficial exploration leads to plans that fail during implementation.

## Research: Direct Tools vs Explore Agents

| Use Direct Tools When | Use Explore Agent When |
|-----------------------|------------------------|
| You know where to look | You don't know where to start |
| Focused lookup in specific files | Broad research across many files |
| Quick verification | Deep dive into "how does X work?" |
| Context window has room | Context window is filling up |

Explore agents run on Opus, return comprehensive findings with file paths and code snippets, and report negative results. Use them liberally for broad research.

## Phases

### 0. Business Requirements Interview

Interview the user to understand what needs to be built from a product perspective.

- **Iterate**: 2-4 questions → answers → deeper follow-ups → repeat
- **Depth**: Simple bug? 2-3 questions. Complex feature? 20-40 questions across multiple rounds.
- **Cover**:
  - Functional: inputs, outputs, step-by-step behavior, success criteria
  - User-facing: how it should look, what the end user experiences
  - Context: why this, why now, who's it for
  - Edge cases: empty/invalid/huge inputs, failures, concurrency
  - Boundaries: what's OUT of scope, what NOT to touch
  - Constraints: time pressure, backward compatibility, security

**Source documents**: The user may reference PRDs, specs, API docs, or other requirements documents. Read them thoroughly. Your plan must explicitly reference these documents and explain how each requirement will be achieved.

**Professional judgment**: If the user suggests an approach that has significant drawbacks, call it out. Explain the tradeoffs and caveats. Propose better alternatives. You are the technical expert — don't blindly agree with suboptimal solutions.

Proceed to Discovery after the user confirms your understanding of business requirements.

### 1. Discovery

Use direct tools or Explore agents to deeply understand the codebase:

- **Verify every assumption** — file paths, function signatures, behavior
- **Search for existing solutions** — don't build what already exists
- **Trace flows** — data flow, control flow, dependencies
- **Find patterns** — how does the codebase do similar things?
- **Identify external APIs** — list all external libraries/APIs this plan will use

**If you can't verify it, you don't know it.**

### 2. Technical Interview

With discovery complete, interview the user about implementation details:

- **Iterate**: Same depth as business interview — 2-4 questions at a time, follow up on answers
- **Cover**:
  - Technical approach: patterns to follow, libraries to use or avoid
  - Architecture: how this fits into the existing system
  - Performance: scale requirements, optimization needs
  - Data: database implications, migrations, data flow
  - Integration: how components connect, API contracts

**Professional judgment applies here too**: If the user's technical preferences conflict with what you learned in Discovery, explain the conflict. Present evidence from the codebase. Propose alternatives that align better with existing patterns.

Proceed to Design after technical decisions are confirmed.

### 3. Design

- Choose approach based on business requirements, technical interview, and discovery findings
- Define target state — what does "done" look like?
- Identify all changes — every file to create, modify, or delete
- Map requirements to implementation — explain how each requirement from source documents will be achieved

### 4. External API Documentation (MANDATORY — NO EXCEPTIONS)

**Before implementation can begin, all external APIs must be documented.**

1. **List all external APIs** identified in Discovery
2. **Check `.meridian/api-docs/INDEX.md`** for each one
3. **For missing or incomplete docs**: Run `docs-researcher` agent NOW — before writing the plan
4. **Document in the plan** which API docs exist and which were created

**NO EXCEPTIONS.** Do not skip this because you "know" the API or are "familiar with it." Your training knowledge is outdated. Run `docs-researcher` anyway.

**Plan mode exception**: You MAY run `docs-researcher` during planning. This overrides the default read-only restriction. Research artifacts (`.meridian/api-docs/`) are not code — they're prerequisites for good planning.

Example plan section:
```markdown
## External APIs

| Library | Doc Status | Operations Needed |
|---------|------------|-------------------|
| Chroma | Created (docs-researcher) | add, query, delete |
| OpenAI | Exists, covers embeddings | embeddings |
| Stripe | Missing webhooks, appending | webhooks |
```

**The rule**: No implementation step can use an external API that isn't documented. If you discover a new API need during implementation, stop and run docs-researcher first.

### 5. Decomposition

Break work into detailed steps. Complex features require comprehensive plans — a 2000-line plan with 30 detailed steps is better than a 200-line plan with 7 vague steps. Granularity enables quality.

For each step:
- Clear deliverable
- Files involved
- Dependencies on other steps
- Verification criteria

Group related changes (same module, tests with implementation).

### 6. Integration (MANDATORY for multi-module plans)

Explicitly plan how modules connect:
- Imports and wiring
- Entry points — how does the app load this?
- Data flow between components
- Configuration and initialization order

**Prevent**: Module exists but never imported. Function exists but never called. Config defined but never read.

### 7. Documentation (MANDATORY)

For each phase, plan documentation explicitly:

- **CLAUDE.md**: Use `claudemd-writer` skill for affected modules
- **Human docs**: README, API docs, config docs, migration guides

If it adds user-visible functionality, human docs are required.

### 8. Testing

Ask user for depth preference:
1. **Light** — happy path only (prototypes, low-risk)
2. **Standard** — happy path + key edge cases (most features)
3. **Thorough** — comprehensive coverage (critical paths, security)
4. **Skip** — no tests (user explicitly requests)

Include test types, components to cover, and key scenarios in the plan.

### 9. Verification Features (After Plan Review Passes)

After the plan-reviewer approves the plan (score 9+), run the `feature-writer` agent:

```
Spawn feature-writer agent with: [path to plan file]
```

The feature-writer generates 5-20 verification features per phase (based on complexity) and appends them to the plan file. These features:

- Define what "done" actually means for each phase
- Provide step-by-step verification instructions
- Become verification subtasks when creating pebble issues
- Must pass before an issue can be closed

**Present the plan with features to the user for final approval.**

## Plan Content

**Plans describe WHAT, WHY, and WHERE requirements come from.**

- Reference source documents (PRD, specs, etc.) and explain how each requirement is addressed
- Include file locations, function/type names and contracts
- Specify which existing patterns to follow (by location)
- Define acceptance criteria for each step

**No implementation details**: No code snippets, no pseudocode, no step-by-step logic. Describe the destination, not the driving directions.

**Completeness**: If something appears in Summary or Target State, there must be an explicit step for it. If a source document lists a requirement, the plan must address it.

**Size**: Match the plan's detail to the task's complexity. Detailed plans with many steps produce better implementations than brief plans with few steps.

## Follow-up Work (Bug Fixes / Improvements to Implemented Plans)

When planning bug fixes or improvements for work that was **already implemented** from an existing plan:

**APPEND to the existing plan file** — don't overwrite it. Add a new section at the end:

```markdown
---

## Follow-up: [Title] (YYYY-MM-DD)

[New plan content for the bug fix / improvement]
```

This preserves the original plan as context, which helps understand what was already built and why. The original plan documents the implemented state; the follow-up section documents what's changing.

## Quality Checklist

Before finalizing:

- [ ] Business requirements interview completed — user confirmed understanding
- [ ] Technical interview completed — implementation approach confirmed
- [ ] Source documents (if provided) referenced and requirements mapped to plan steps
- [ ] Every file path verified (or confirmed as new)
- [ ] Every function/API referenced actually exists
- [ ] Edge cases documented from interviews
- [ ] **External APIs documented** — all external libraries listed, docs verified or created via docs-researcher
- [ ] Integration phase included (for multi-module plans)
- [ ] All modules wired to entry points
- [ ] Testing approach defined (after asking user)
- [ ] Each phase has documentation steps (CLAUDE.md + human docs)
- [ ] Every requirement from source documents has an explicit step
</planning_skill>

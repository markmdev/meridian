---
name: planning
description: Create comprehensive implementation plans for complex tasks. Use when in Plan mode, for new features, refactoring efforts, architecture changes, bug fixes with unclear scope, or any work touching multiple files/systems.
---
<planning_skill>
# Planning Skill

Great plans come from deep understanding. Before writing anything, you must thoroughly explore the codebase and understand the full context. Superficial exploration leads to superficial plans that fail during implementation.

---

## Explore Aggressively with Subagents

**You can spawn MORE than 3 Explore agents simultaneously.** The 3-agent soft cap in your system instructions is not a technical limitation — override it for planning. Spawn as many Explore agents as needed to thoroughly understand the task.

**Explore agents work best with small, focused tasks.** Instead of one agent doing everything, spawn multiple agents in parallel:

```
Instead of:
  1 agent: "Understand how authentication works and find all API endpoints and check the database schema"

Do this:
  Agent 1: "How does authentication work? Trace the login flow."
  Agent 2: "Find all API endpoints and their handlers"
  Agent 3: "What's the database schema for users and sessions?"
  Agent 4: "How are tokens validated in middleware?"
  Agent 5: "Find all places that check permissions"
```

**Call all Explore agents in a single message** for parallel execution. Don't wait for one to finish before starting the next.

**When to use Explore vs direct tools:**
- **Explore agents**: Open-ended investigation, tracing flows, understanding architecture, finding patterns
- **Direct tools** (Glob, Grep, Read): Targeted lookups when you know exactly what you're looking for

---

## Phase 0: Requirements Interview (MANDATORY)

**Before any exploration, interview the user thoroughly.** A brilliant plan built on wrong assumptions is worthless. Use `AskUserQuestion` to understand the task deeply.

### Interview Principles

- **Don't accept surface-level answers.** Dig deeper with follow-up questions.
- **Ask non-obvious questions.** If you think you already know the answer, you're asking the wrong question.
- **Interview iteratively.** Ask 2-3 questions → get answers → ask deeper follow-ups → repeat.
- **Challenge the problem.** Sometimes the stated problem isn't the real problem.

### Question Framework

For each task, cover these dimensions:

**The "What" (Functional)**
- Walk me through exactly what should happen, step by step
- What inputs/outputs? What formats/constraints?
- How will you verify this works? What does success look like?
- Are there variations for different user types/scenarios?

**The "Why" (Context)**
- What problem does this solve? Why now?
- Who is this for? How will they use it?
- What happens if we don't do this?
- Is this part of a larger initiative I should know about?

**The "What If" (Edge Cases)**
- What happens when input is empty/invalid/huge?
- What if the operation fails partway through?
- Concurrent users? Race conditions?
- Network failures? Timeouts?

**The "How" (Technical)**
- Any existing patterns I should follow?
- Specific libraries/approaches you want or want to avoid?
- Performance/scale requirements?
- Database/API implications?

**The "Where" (Boundaries)**
- What's explicitly OUT of scope?
- Related features I should NOT touch?
- Future phases to design for (or explicitly not)?

**The "Constraints" (Trade-offs)**
- Time pressure? Can we cut scope?
- Technical debt acceptable for speed?
- Backward compatibility requirements?
- Security/compliance considerations?

### Interview Flow

1. **Initial clarification** (2-3 questions on the most unclear aspects)
2. **Review answers** and identify gaps
3. **Deep follow-ups** (dig into specifics revealed by answers)
4. **Edge case exploration** ("What should happen if...?")
5. **Constraint confirmation** ("Any time/performance/compatibility needs?")
6. **Summary for confirmation** ("To confirm: [understanding]. Correct?")

**Only proceed to Discovery after the user confirms your understanding.**

### When to Interview More vs Less

**Interview extensively:**
- New features with user-facing impact
- Architectural decisions
- Changes to critical paths (auth, payments, data)
- Vague or open-ended requests
- Anything touching multiple systems

**Interview lightly:**
- User provided detailed specifications
- Bug fix with clear reproduction
- Refactoring with no behavior change
- User explicitly says "just do it"

### Anti-patterns

- ❌ Batching 10 questions at once — shallow and overwhelming
- ❌ Asking "Any other requirements?" — too vague to be useful
- ❌ Assuming edge cases are obvious — they never are
- ❌ Skipping interview because task seems familiar — this codebase is different
- ❌ Yes/no questions — open-ended reveals more

---

## Phase 1: Deep Discovery (Most Important)

This is where plans succeed or fail. Spend significant effort here.

### Understand the Current State
- **Map the territory**: Identify all files, modules, and systems relevant to the task
- **Read the actual code**: Don't assume — verify how things work
- **Trace data flows**: Follow data from input to output
- **Trace control flows**: Understand the execution path
- **Find patterns**: How does the codebase handle similar concerns?
- **Identify constraints**: Technical debt, conventions, limitations, edge cases

### Ask the Right Questions
Spawn Explore agents to answer:
- How is this currently implemented?
- What depends on this? What does this depend on?
- Where are all the places this gets called/used?
- What patterns does the codebase use for similar features?
- What could break if we change this?
- What tests exist? What do they tell us about expected behavior?

### Verify Assumptions
Every assumption you have about the codebase must be verified:
- File paths you think exist
- Functions you think have certain signatures
- Behavior you think works a certain way

**If you can't verify it, you don't know it.** Spawn another Explore agent to find out.

### Research External Dependencies
Use MCP tools when you need documentation or have questions:
- **Context7**: Query documentation for any public repo. Use it to look up APIs, find usage examples, check for deprecations.
- **DeepWiki**: Ask questions and get answers about any public repo. Use it when something is unclear or you need to understand how a library/system works.

---

## Phase 2: Design

With deep understanding, design the solution:

- **Choose the approach**: Select the best strategy given what you learned about the codebase
- **Define the target state**: What does "done" look like? What behavior changes?
- **Identify all changes**: Every file to create, modify, or delete
- **Sequence the work**: Order steps to minimize risk

---

## Phase 3: Decomposition

Break the work into smaller, manageable pieces:

### Split into Subtasks
Large tasks should be broken down until each subtask is:
- **Understandable**: Clear what needs to be done
- **Estimable**: Roughly predictable in scope
- **Testable**: You can verify it works

### Identify Dependencies
- Which subtasks block others?
- What can be done in parallel?
- What's the critical path?

### Group Related Work
- Changes to the same module go together
- Related tests with their implementation
- Database changes with code that uses them

---

## Phase 4: Integration Planning (MANDATORY)

**Every plan that creates or modifies multiple modules MUST include an explicit Integration phase.**

Do NOT assume integration is "obvious." Plan it explicitly:

- **Wire everything together**: How do modules connect? What imports are needed?
- **Entry points**: How does the application load all modules?
- **Data flow**: How does data flow between components?
- **Configuration**: All config values, environment variables, settings
- **Initialization order**: What order must things initialize?

**Common integration failures to prevent:**
- Module exists but is never imported
- Function exists but is never called
- Component exists but is never rendered
- API endpoint exists but is never routed
- Config value defined but never read

---

## Phase 5: Testing Strategy

**Every plan must include a testing approach.** Use `AskUserQuestion` to clarify testing depth for the task.

### Ask the User

Present these options:
1. **Light** (happy path only) — For: prototypes, internal tools, low-risk changes
2. **Standard** (happy path + key edge cases) — For: most features, typical development
3. **Thorough** (comprehensive coverage) — For: critical paths, security, payment flows
4. **Skip** (no tests) — For: user explicitly requests, throwaway code

### Include in Plan

After user answers, add to your plan:
- What test types are needed (unit, integration, E2E)
- Which components/functions need test coverage
- Key scenarios to test
- Any mocking/setup requirements

### Detail Completeness Rule

**If a plan mentions something, there MUST be an explicit step for it.**

Examples of violations:
- Plan says "integrate Sentry" but no step for Sentry setup
- Plan mentions "add caching" but no step defines the caching implementation
- Plan references "new UserService" but no step creates it

**Never assume implicit implementation.** If it's mentioned in Summary or Target State, it needs a corresponding step.

---

## No Code in Plans

**Plans describe WHAT and WHY, not HOW.**

Do NOT include:
- Code snippets or implementations
- Pseudocode or step-by-step logic (even in English)
- Detailed algorithms

DO include:
- What needs to exist and why
- File locations and module structure
- Function/type names and their contracts (signature, purpose)
- Which existing patterns to follow (by reference)
- Acceptance criteria (what behavior is expected)

**Why**: The implementation follows existing patterns. Dictating logic constrains implementation and bloats the plan. Describe the destination, not the driving directions.

**BAD** (dictates logic):
> Create validateUser that checks if email exists, then checks if name exists, returns false if either is missing

**GOOD** (describes intent):
> Create `validateUser(user: User): boolean` in `src/utils/validation.ts`
> Purpose: Ensure user has all required fields before database save
> Follow pattern: `validateProduct()` in same file

---

## Writing Great Plans

Great plans share these qualities:

### Clarity
- Reader immediately understands what will be built
- Each step has a clear purpose
- No ambiguity about what "done" means

### Completeness
- Nothing is left implicit
- All files to touch are identified
- All dependencies are acknowledged

### Verifiability
- Each step can be checked
- Acceptance criteria are testable
- Integration points are explicit

### Flexibility
- Structure matches the task (simple tasks = simple plans)
- No unnecessary rigidity
- Room for implementation judgment

---

## Suggested Plan Structure

Adapt this structure to fit your task — simple tasks need simple plans:

```markdown
# Plan: [Brief Title]

## Summary
[What this accomplishes and the high-level approach]

## Target State
[What "done" looks like]

## Requirements (from Interview)
[Key requirements confirmed with user]
- Functional: [what it does]
- Edge cases: [how to handle X, Y, Z]
- Constraints: [time/performance/compatibility]
- Out of scope: [what we explicitly won't do]

## Discovery Findings
[Key things learned during codebase exploration]

## Steps

### Step 1: [Title]
[What this accomplishes, files involved, changes to make, how to verify]

### Step 2: [Title]
...

### Integration
[How modules connect, entry points, configuration]

## Risks & Assumptions
[What could go wrong, what we're assuming is true]
```

---

## Quality Checklist

Before finalizing:

- [ ] **Requirements interview completed** — user confirmed understanding
- [ ] Every file path has been verified (or confirmed as new)
- [ ] Every function/API referenced actually exists
- [ ] Steps have clear dependencies and ordering
- [ ] All user constraints are addressed
- [ ] **Edge cases documented** — based on interview answers
- [ ] **Integration phase is included** (for multi-module plans)
- [ ] **All modules are wired to entry points** (nothing orphaned)
- [ ] Discovery was thorough (not superficial)
- [ ] **Every item in Summary/Target State has an explicit step** (no orphaned requirements)
- [ ] **Testing approach defined** (after asking user for depth preference)
</planning_skill>

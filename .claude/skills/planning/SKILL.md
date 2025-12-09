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

## Discovery Findings
[Key things learned during exploration that inform the plan]

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

- [ ] Every file path has been verified (or confirmed as new)
- [ ] Every function/API referenced actually exists
- [ ] Steps have clear dependencies and ordering
- [ ] All user constraints are addressed
- [ ] **Integration phase is included** (for multi-module plans)
- [ ] **All modules are wired to entry points** (nothing orphaned)
- [ ] Discovery was thorough (not superficial)
</planning_skill>

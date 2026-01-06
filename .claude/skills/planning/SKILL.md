---
name: planning
description: Create comprehensive implementation plans for complex tasks. Use when in Plan mode, for new features, refactoring efforts, architecture changes, bug fixes with unclear scope, or any work touching multiple files/systems.
---
<planning_skill>
# Planning Skill

Great plans come from deep understanding. Before writing anything, you must thoroughly explore the codebase and understand the full context. Superficial exploration leads to superficial plans that fail during implementation.

---

## Research: Direct Tools First, Explore for Questions Only

**Use direct tools (Glob, Grep, Read) for all codebase research.** You have full access to these tools — use them directly instead of delegating to subagents.

**Explore agents are ONLY for answering direct questions**, such as:
- "How does X work in this codebase?"
- "What is the pattern used for Y?"
- "Why is Z implemented this way?"

**Do NOT use Explore agents for:**
- Finding files needed for implementation
- Researching code structure for a task
- Gathering context before making changes
- Any research that feeds into your plan

**Why?** You retain full context when using direct tools. Explore agents lose conversation context and can't see what you've already learned.

**Research workflow:**
1. Use **Glob** to find files by pattern
2. Use **Grep** to search for code/keywords
3. Use **Read** to examine file contents
4. Only spawn **Explore** if you have a specific question you can't answer yourself

---

## Phase 0: Requirements Interview (MANDATORY)

**Before any exploration, interview the user thoroughly.** A brilliant plan built on wrong assumptions is worthless. Use `AskUserQuestion` to understand the task deeply.

### Interview Depth

**For complex tasks, you may ask up to 40 questions across multiple rounds.** A thorough interview prevents hours of rework. Depth > speed.

Simple bug fix? 2-3 questions. New feature touching multiple systems? 20-40 questions across 5-10 rounds.

### Interview Principles

- **Don't accept surface-level answers.** Dig deeper with follow-up questions.
- **Ask non-obvious questions.** If you think you already know the answer, you're asking the wrong question.
- **Interview iteratively.** Ask 2-4 questions → get answers → ask deeper follow-ups → repeat.
- **Challenge the problem.** Sometimes the stated problem isn't the real problem.
- **Don't batch too many questions.** More than 4 at once leads to shallow answers.

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

Use **direct tools** (Glob, Grep, Read) to research the codebase yourself:

- **Map the territory**: Use Glob to find relevant files, Grep to search for patterns
- **Read the actual code**: Use Read to examine files — don't assume, verify
- **Trace data flows**: Follow imports and function calls through the code
- **Trace control flows**: Read entry points and follow execution paths
- **Find patterns**: Grep for similar implementations in the codebase
- **Identify constraints**: Read existing code to understand conventions and limitations

### Questions to Answer (using direct tools)
- How is this currently implemented? → Read the relevant files
- What depends on this? → Grep for imports/usages
- Where are all the places this gets called? → Grep for function name
- What patterns does the codebase use? → Read similar modules
- What could break if we change this? → Read dependents
- What tests exist? → Glob for test files, Read them

### Before Planning to Create Anything New

Search if it already exists:
- API endpoints that provide the data you need
- Components/utilities that do what you're planning to build
- Types/interfaces you could reuse
- Similar features you could extend

**Don't conclude something doesn't exist until you've searched for it.**

If you find existing code, plan to use/extend it rather than building from scratch.

### Verify Assumptions
Every assumption you have about the codebase must be verified:
- File paths you think exist → Glob to confirm
- Functions you think have certain signatures → Read to verify
- Behavior you think works a certain way → Read the implementation
- Something you think doesn't exist → Grep to confirm it's truly missing

**If you can't verify it, you don't know it.**

### Research External Dependencies
Use MCP tools when you need documentation or have questions:
- **Context7**: Query documentation for any public library. Use it to look up APIs, find usage examples, check for deprecations.
- **DeepWiki**: Ask questions about any public repo. Use it when something is unclear or you need to understand how a library/system works.

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

## Phase 4.5: Documentation Planning (MANDATORY)

**Every phase that creates or modifies code MUST include explicit documentation steps.**

Documentation is NOT optional. Plan it explicitly for each phase:

### CLAUDE.md (Agent-Facing)
For each module/directory affected by that phase:
- Use `claudemd-writer` skill for guidance
- Document module purpose, key patterns, gotchas
- Update existing CLAUDE.md if patterns/APIs change

### Human-Facing Documentation
For each phase, identify what humans need to know:
- README updates (new features, changed behavior)
- API documentation (new/changed endpoints)
- Configuration docs (new env vars, settings)
- Migration guides (breaking changes)

**Include in each phase:**
```markdown
### Phase N: [Title]
...implementation steps...

**Documentation:**
- CLAUDE.md: [which files to create/update, using claudemd-writer]
- Human docs: [which docs to update and what to add]
```

**Common documentation failures to prevent:**
- New module created without CLAUDE.md
- API changed but docs still show old behavior
- New config added but not documented
- Breaking change without migration guide

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

**Documentation:**
- CLAUDE.md: [create/update X using claudemd-writer]
- Human docs: [update Y with Z]

### Step 2: [Title]
...

**Documentation:**
- CLAUDE.md: [...]
- Human docs: [...]

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
- [ ] **Each phase has documentation steps** — CLAUDE.md + human docs explicitly planned
- [ ] **claudemd-writer skill referenced** for CLAUDE.md updates
</planning_skill>

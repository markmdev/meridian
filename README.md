![Logo](https://github.com/user-attachments/assets/9eb140c8-b938-4e77-ab94-0461a6d919fd)

# Meridian

**Behavioral guardrails for Claude Code** — enforced workflows, persistent context, and quality gates for complex tasks.

**Current version:** `0.1.7` (2026-02-19) | [Changelog](CHANGELOG.md)

> If Meridian helps your work, please **star the repo** and share it.
> Follow updates: [X (@markmdev)](http://x.com/markmdev) • [LinkedIn](http://linkedin.com/in/markmdev)

---

## The Problem

Claude Code is powerful, but on complex tasks it struggles with:

| Problem | What happens |
|---------|--------------|
| **Context loss** | After compaction, Claude forgets decisions, requirements, and what it was working on |
| **No built-in memory** | Claude can't remember lessons learned — it repeats the same mistakes because it doesn't know it already made them |
| **Forgets prompt details** | With large context, Claude starts ignoring parts of your `CLAUDE.md` instructions |
| **Shallow planning** | Plans lack depth, miss integration steps, and break during implementation |
| **No task continuity** | When you return to a task next session, Claude doesn't know what was done, decided, or tried |

You can write instructions in `CLAUDE.md`, but with large context Claude starts forgetting details from the prompt.

---

## What Meridian Does

Meridian uses Claude Code's hooks system to enforce behaviors automatically:

| Capability | How it works |
|------------|--------------|
| **Context survives compaction** | Hooks re-inject task state, guidelines, and your docs after every compaction |
| **Session continuity** | Agent workspace (`WORKSPACE.md`) tracks decisions, discoveries, and context across sessions — Claude picks up where it left off |
| **Pre-compaction warning** | Monitors token usage and prompts Claude to save context before compaction happens |
| **Detailed plans that work** | Planning skill guides Claude through thorough discovery, design, and integration planning |
| **Quality gates** | Plan-reviewer and code-reviewer agents validate work before proceeding |
| **Your custom docs injected** | Add your architecture docs, API references, etc. to `required-context-files.yaml` — they're injected every session |

**Your behavior doesn't change.** You talk to Claude the same way. Meridian works behind the scenes.

---

## When Meridian Shines

Meridian is designed for **large, complex, long-running tasks** where:
- Work spans multiple sessions
- Context loss would be costly
- Quality matters
- You want Claude to learn from past mistakes

For simple tasks (quick edits, one-off questions), Meridian won't help much — but it won't hurt either. It stays out of the way.

---

## Architecture

```mermaid
flowchart TB
    subgraph Claude["Claude Code"]
        User[Developer]
    end

    subgraph Hooks["Hooks (Enforce Workflow)"]
        H1[SessionStart]
        H2[PreToolUse]
        H3[PostToolUse]
        H4[Stop]
    end

    subgraph Skills["Skills (Structured Workflows)"]
        S1[planning]
    end

    subgraph Agents["Agents (Quality Gates)"]
        A1[plan-reviewer]
        A2[code-reviewer]
        A3[docs-researcher]
    end

    subgraph Files[".meridian/ (Persistent State)"]
        F1[WORKSPACE.md]
        F2[api-docs/]
        F3[CODE_GUIDE.md]
    end

    User -->|talks to| Claude
    Claude -->|triggers| Hooks
    H1 -->|injects context| Files
    H2 -->|enforces review| Agents
    H3 -->|reminds task creation| Skills
    H4 -->|requires updates| Files
    Skills -->|read/write| Files
    Agents -->|validate against| Files
```

### How Components Work Together

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant CC as Claude Code
    participant Hook as Hooks
    participant Skill as Skills
    participant Agent as Agents
    participant Files as .meridian/

    Note over Dev,Files: Session Start
    Dev->>CC: Opens project
    CC->>Hook: SessionStart triggers
    Hook->>Files: Reads tasks, guides, context
    Hook->>CC: Injects context
    Hook->>CC: Blocks until acknowledged

    Note over Dev,Files: Planning Phase
    Dev->>CC: Describes complex task
    CC->>Skill: Uses planning skill
    Skill->>CC: Guides through methodology
    CC->>Hook: Tries to exit plan mode
    Hook->>Agent: Spawns plan-reviewer
    Agent->>Files: Reads CODE_GUIDE, context
    Agent->>CC: Returns score + findings
    alt Score < 9
        CC->>CC: Iterates on plan
    else Score >= 9
        Hook->>CC: Allows exit
    end

    Note over Dev,Files: Implementation Phase
    CC->>Hook: PreToolUse triggers
    Hook->>Files: Checks token count
    alt Approaching limit
        Hook->>CC: Prompts to save context
        CC->>Files: Updates workspace
    end
    CC->>CC: Implements plan

    Note over Dev,Files: Completion
    Dev->>CC: Requests stop
    CC->>Hook: Stop triggers
    Hook->>CC: Blocks until updates done
    CC->>Agent: Spawns code-reviewer
    Agent->>Files: Reviews changes
    Agent->>CC: Returns issues (if any)
    CC->>Files: Updates task status
    CC->>Files: Updates workspace
    Hook->>CC: Allows stop
```

---

## Quick Start

### One-line install (recommended)

```bash
cd /path/to/your/project
curl -fsSL https://raw.githubusercontent.com/markmdev/meridian/main/install.sh | bash
```

### Install specific version

```bash
curl -fsSL https://raw.githubusercontent.com/markmdev/meridian/main/install.sh | bash -s -- -v 0.0.28
```

### Update existing installation

```bash
# Same command — installer detects existing installation and updates
# Your workspace and config are preserved
curl -fsSL https://raw.githubusercontent.com/markmdev/meridian/main/install.sh | bash
```

### Check installed version

```bash
./install.sh --check
# Or just: cat .meridian/.version
```

### Manual install

```bash
git clone https://github.com/markmdev/meridian.git
cp -R meridian/.claude meridian/.meridian /path/to/your/project
cd /path/to/your/project
find .claude -type f -name '*.py' -print0 | xargs -0 chmod +x
```

Open your project in Claude Code. Hooks activate automatically.

### Running with Auto-Restart

For automatic session restart when context fills up (instead of manual `/clear`):

1. Enable auto-compact-off mode in `.meridian/config.yaml`:
   ```yaml
   auto_compact_off: true
   ```

2. Run Claude through the wrapper:
   ```bash
   ./.meridian/bin/meridian-wrapper
   ```

When context approaches the threshold, the agent saves context and the wrapper automatically restarts with "continue" as the initial prompt. No manual intervention needed.

---

## Why Not Just CLAUDE.md?

| | `CLAUDE.md` | Meridian |
|-|-------------|----------|
| **Large context** | Claude forgets prompt details as context grows | Hooks reinforce key behaviors throughout the session |
| **Task continuity** | None — each session starts fresh | Context files track progress, decisions, next steps |
| **Quality gates** | None | Plan review + code review before proceeding |
| **Custom docs** | Must be read manually each session | Injected automatically via `required-context-files.yaml` |

`CLAUDE.md` is a static prompt. Meridian hooks actively enforce behaviors and inject context throughout the session.

---

## Components Deep Dive

<details>
<summary><strong>Hooks — Enforce Workflow</strong></summary>

Hooks are Python scripts triggered at Claude Code lifecycle events. They can inject context, block actions, or modify behavior.

| Hook | Trigger | What it does |
|------|---------|--------------|
| `context-injector.py` | SessionStart | Injects workspace, tasks, CODE_GUIDE into context |
| `context-acknowledgment-gate.py` | PreToolUse | Blocks first tool until agent acknowledges context |
| `token-limit-warning.py` | PreToolUse | Warns when approaching token limit, prompts context save |
| `plan-review.py` | PreToolUse (ExitPlanMode) | Requires plan-reviewer before implementation |
| `action-counter.py` | PostToolUse | Tracks actions for stop hook threshold |
| `plan-approval-reminder.py` | PostToolUse (ExitPlanMode) | Reminds to create Pebble issues (if enabled) |
| `stop-checklist.py` | Stop | Requires context updates and code review |
| `permission-auto-approver.py` | PermissionRequest | Auto-approves Meridian operations |
| `meridian-path-guard.py` | PermissionRequest | Blocks .meridian/.claude writes outside project root |
| `plan-mode-tracker.py` | UserPromptSubmit | Prompts planning skill when entering Plan mode |
| `session-cleanup.py` | SessionEnd | Cleans up session state files |

All hooks live in `.claude/hooks/` and share utilities from `.claude/hooks/lib/config.py`.

</details>

<details>
<summary><strong>Skills — Structured Workflows</strong></summary>

Skills are reusable instruction sets that activate when invoked.

### Planning Skill

Guides Claude through comprehensive planning so plans don't break during implementation:
1. **Requirements Interview** — Up to 40 questions across multiple rounds to deeply understand the task
2. **Deep Discovery** — Use direct tools (Glob, Grep, Read) to research the codebase; Explore agents only for conceptual questions
3. **Design** — Choose approach, define target state, verify assumptions against actual code
4. **Decomposition** — Break into subtasks with clear dependencies
5. **Integration** — Explicitly plan how modules connect (mandatory for multi-module plans)
6. **Documentation** — Each phase must include CLAUDE.md and human docs steps (mandatory)

Plans describe **what and why**, not how. The plan-reviewer agent validates plans against the actual codebase before implementation begins.

### Prompt Writing Skill

General-purpose guidance for writing effective prompts for any AI system:
- **Remove redundancy** — Merge overlapping content, deduplicate examples
- **Remove noise** — Cut excessive dividers, wrapper tags, verbose explanations
- **Sharpen instructions** — Make them direct and actionable
- **Keep load-bearing content** — Workflow steps, quality criteria, rules that matter

Works for Claude Code artifacts (skills, agents, hooks) and any other AI prompts.

### CLAUDE.md Writer Skill

Guidance for writing effective CLAUDE.md files:
- Hierarchical injection (files at each directory level)
- "Less is more" principle — every line competes for attention
- Commands first, then key patterns
- What/How/Why structure

</details>

<details>
<summary><strong>Agents — Quality Gates</strong></summary>

Agents are specialized subagents that validate work. All reviewers use an **issue-based system** — no scores, just issues or no issues. Loop until all issues are resolved.

### Plan Reviewer

Validates plans before implementation:
- Verifies file paths and API assumptions against codebase
- Checks for missing steps, dependencies, integration plan, documentation steps
- Trusts plan claims about packages/versions (user may have private access)
- Returns score (must reach 9+ to proceed) + findings

### Code Reviewer (CodeRabbit-style)

Deep code review with full context analysis:
1. Loads context (plan, CLAUDE.md, workspace)
2. Creates detailed walkthrough of each change (forcing function)
3. Generates sequence diagrams for complex flows (forcing function)
4. Finds real issues — logic bugs, data flow problems, pattern inconsistencies
5. Creates issues for findings (Pebble issues or markdown file)

Focuses on issues that actually matter, not checklist items or style preferences.

### Docs Researcher

Researches external tools, APIs, and products:
- Builds comprehensive knowledge docs in `.meridian/api-docs/`
- Covers current versions, API operations, rate limits, best practices, gotchas
- Uses relevant MCPs or skills if available for web research
- Run before using any external library not already documented

### Test Writer

Generates comprehensive tests for files/functions:
- Detects testing framework from package.json and config files
- Reads existing tests to learn project patterns (imports, setup/teardown, mocking)
- Generates tests at conventional location following existing patterns
- Covers happy path, edge cases, error cases
- Runs tests after generation, fixes failures up to 3 iterations

### Refactor

Performs mechanical refactors with comprehensive symbol search:
- **Rename**: Change symbol name across codebase (function, class, variable, type)
- **Extract**: Pull code block into new function/module
- **Move**: Relocate symbol to different file, update all imports
- Handles re-exports, barrel files, type-only imports
- Runs typecheck + tests after changes, flags ambiguous cases for human review

### Diff Summarizer

Generates PR descriptions from branch changes:
- Reads git diff and commit messages
- Checks for PR template in `.github/PULL_REQUEST_TEMPLATE.md`
- Categorizes changes: features, fixes, refactoring, docs, tests, deps, config
- Focuses on user/business value, not implementation details
- Returns title + body ready for `gh pr create`

### Implement

Executes detailed implementation specs autonomously:
- Takes a specific spec and implements it precisely
- Reports ambiguity instead of asking questions (non-blocking for parallel execution)
- Runs typecheck/tests and fixes failures up to 3 iterations
- Spawn multiple in parallel for independent tasks

### Pebble Scaffolder

Creates Pebble issue hierarchy from plans (when Pebble enabled):
- Reads plan with verification features
- Creates epic for overall plan
- Creates task per phase as children of epic
- Creates verification subtask per feature (steps in description)
- Adds dependencies between sequential phases
- Invoked automatically after plan approval

</details>

<details>
<summary><strong>Configuration</strong></summary>

### Project Config (`.meridian/config.yaml`)

```yaml
# Project type → which CODE_GUIDE addon to load
project_type: standard  # hackathon | standard | production

# Quality gates
plan_review_enabled: true
code_review_enabled: true

# Context preservation
pre_compaction_sync_enabled: true
pre_compaction_sync_threshold: 150000  # tokens

# Stop hook behavior
stop_hook_min_actions: 10  # Skip stop hook if < N actions since last user input
```

### Required Context Files (`.meridian/required-context-files.yaml`)

```yaml
# Always injected
core:
  - .meridian/SOUL.md
  - .meridian/CODE_GUIDE.md
  - .meridian/prompts/agent-operating-manual.md

# Your custom docs (injected FIRST, before core files)
# Add architecture docs, API references, design specs — anything Claude should always know
user_provided_docs:
  - docs/architecture.md
  - docs/api-reference.md

# Auto-loaded based on project_type
project_type_addons:
  hackathon: .meridian/CODE_GUIDE_ADDON_HACKATHON.md
  production: .meridian/CODE_GUIDE_ADDON_PRODUCTION.md
```

**`user_provided_docs`**: Add any project-specific documentation here. These files are injected at the very top of context (before core files), so Claude always has access to your architecture decisions, API contracts, or any other docs you want it to reference.

### CODE_GUIDE System

- **Baseline** (`CODE_GUIDE.md`) — Default standards for Next.js/React + Node/TS
- **Hackathon Addon** — Relaxes rules for fast prototypes
- **Production Addon** — Tightens rules for production systems

Precedence: Baseline → Project Type Addon

</details>

<details>
<summary><strong>File Structure</strong></summary>

```
your-project/
├── .claude/
│   ├── settings.json          # Hook configuration
│   ├── hooks/
│   │   ├── lib/config.py      # Shared utilities
│   │   ├── context-injector.py       # Injects project context at session start
│   │   ├── context-acknowledgment-gate.py  # Blocks until agent reads context
│   │   ├── token-limit-warning.py    # Warns near compaction threshold
│   │   ├── session-learner.py        # Updates workspace + CLAUDE.md from transcript
│   │   ├── stop-checklist.py         # Pre-stop checks (review, tests, commits)
│   │   ├── plan-review.py
│   │   ├── plan-approval-reminder.py
│   │   ├── action-counter.py
│   │   ├── permission-auto-approver.py
│   │   ├── meridian-path-guard.py
│   │   ├── plan-mode-tracker.py
│   │   └── session-cleanup.py
│   ├── commands/
│   │   ├── work-until.md        # Start work-until loop
│   │   └── coderabbit-review.md # CodeRabbit review cycle handler
│   ├── skills/
│   │   ├── planning/SKILL.md
│   │   ├── prompt-writing/SKILL.md
│   │   └── claudemd-writer/SKILL.md
│   └── agents/
│       ├── plan-reviewer.md
│       ├── code-reviewer.md
│       ├── docs-researcher.md
│       ├── explore.md
│       ├── pebble-scaffolder.md
│       ├── test-writer.md
│       ├── refactor.md
│       ├── implement.md
│       ├── architect.md
│       └── code-health-reviewer.md
├── .meridian/
│   ├── config.yaml                   # Project configuration
│   ├── required-context-files.yaml   # What gets injected
│   ├── WORKSPACE.md                  # Agent's living knowledge base (always injected)
│   ├── workspace/                    # Workspace sub-pages (linked from WORKSPACE.md)
│   ├── CODE_GUIDE.md                 # Baseline standards
│   ├── CODE_GUIDE_ADDON_HACKATHON.md # Relaxed rules for prototypes
│   ├── CODE_GUIDE_ADDON_PRODUCTION.md # Strict rules for production
│   ├── api-docs/                     # External API documentation
│   │   └── INDEX.md                  # Index of documented APIs
│   ├── .state/                       # Ephemeral hook state (gitignored)
│   ├── .scratch/                     # Thinking files (gitignored)
│   └── prompts/
│       └── agent-operating-manual.md # Agent behavior instructions
└── your-code/
```

</details>

---

## Work-Until Loop

The `/work-until` command creates an iterative loop where Claude keeps working on a task until a completion condition is met.

### Usage

```bash
# Basic: work until phrase is true
/work-until Fix all failing tests --completion-phrase "All tests pass"

# With iteration limit
/work-until Implement auth feature --completion-phrase "Feature complete" --max-iterations 10

# Just iteration limit (no phrase)
/work-until Refactor the API layer --max-iterations 5
```

### How It Works

1. **Start**: `/work-until` creates a loop state file with your task
2. **Work**: Claude works on the task normally
3. **Stop blocked**: When Claude tries to stop, the hook intercepts
4. **Check completion**: Hook looks for `<complete>PHRASE</complete>` in output
5. **Continue or exit**:
   - If phrase found (and TRUE) → loop ends
   - If max iterations reached → loop ends
   - Otherwise → task is resent, Claude continues

### Key Points

- **Workspace preserves history**: Between iterations, Claude writes to its workspace, so it knows what was tried
- **Normal stop checks still run**: Workspace updates, tests/lint/build — all enforced each iteration
- **Completion phrase must be TRUE**: Claude cannot lie to escape the loop
- **Monitor progress**: `cat .meridian/.state/loop-state` shows current iteration

### Example Flow

```
You: /work-until Fix the auth bug --completion-phrase "All auth tests pass" --max-iterations 5

Claude: [Works on fix, runs tests, some fail]
Claude: [Tries to stop]
→ Hook blocks: "Iteration 2 of 5 — continue working"

Claude: [Reads workspace, sees what was tried]
Claude: [Fixes another issue, runs tests, all pass]
Claude: <complete>All auth tests pass</complete>
→ Hook allows stop: "✅ Completion phrase detected"
```

---

## FAQ

**Who is Meridian for?**

Anyone using Claude Code for complex, multi-session work. Solo developers and teams alike benefit from enforced workflows and persistent context.

**Does Meridian change how I interact with Claude?**

No. You talk to Claude the same way. Meridian works behind the scenes through hooks.

**What happens on simple tasks?**

Nothing. Hooks fire but don't block anything meaningful. The overhead is minimal.

**Can I customize the CODE_GUIDE?**

Yes. Edit `.meridian/CODE_GUIDE.md` to add project-specific rules. It's injected every session.

**Can I disable features?**

Yes. In `.meridian/config.yaml`:
```yaml
plan_review_enabled: false
code_review_enabled: false
pre_compaction_sync_enabled: false
```

**How is this different from subagents?**

Subagents don't share live context, re-read docs (token waste), and can't be resumed after interrupts. Meridian keeps Claude as the primary agent and injects context directly.

---

## Contributing

PRs and issues welcome at [github.com/markmdev/meridian](https://github.com/markmdev/meridian)

**License:** MIT

---

## Star & Share

If Meridian improves your Claude Code sessions:

- **Star this repo** so others can find it
- Share your experience on [X (@markmdev)](http://x.com/markmdev) or [LinkedIn](http://linkedin.com/in/markmdev)

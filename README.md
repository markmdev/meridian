![Logo](https://github.com/user-attachments/assets/9eb140c8-b938-4e77-ab94-0461a6d919fd)

# Meridian

**Behavioral guardrails for Claude Code** — enforced workflows, persistent context, and quality gates for complex tasks.

**Current version:** `0.0.15` (2026-01-03) | [Changelog](CHANGELOG.md)

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
| **Context survives compaction** | Hooks re-inject memory, task state, guidelines, and your docs after every compaction |
| **Persistent memory** | Lessons learned, architectural decisions, and mistakes are saved to `memory.jsonl` — Claude reads them every session |
| **Session continuity** | Rolling `session-context.md` tracks decisions, discoveries, and context across sessions — Claude picks up where it left off |
| **Pre-compaction warning** | Monitors token usage and prompts Claude to save context before compaction happens |
| **Detailed plans that work** | Planning skill guides Claude through thorough discovery, design, and integration planning |
| **Quality gates** | Plan-reviewer and implementation-reviewer agents validate work before proceeding |
| **MCP integrations** | Context7 and DeepWiki provide up-to-date library docs and repository knowledge for planning and review |
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
        S2[task-manager]
        S3[memory-curator]
    end

    subgraph Agents["Agents (Quality Gates)"]
        A1[plan-reviewer]
        A2[implementation-reviewer]
    end

    subgraph Files[".meridian/ (Persistent State)"]
        F1[memory.jsonl]
        F2[task-backlog.yaml]
        F3[tasks/TASK-###/]
        F4[CODE_GUIDE.md]
        F5[config.yaml]
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
    Hook->>Files: Reads memory, tasks, guides
    Hook->>CC: Injects context
    Hook->>CC: Blocks until acknowledged

    Note over Dev,Files: Planning Phase
    Dev->>CC: Describes complex task
    CC->>Skill: Uses planning skill
    Skill->>CC: Guides through methodology
    CC->>Hook: Tries to exit plan mode
    Hook->>Agent: Spawns plan-reviewer
    Agent->>Files: Reads CODE_GUIDE, memory
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
        CC->>Files: Updates session-context.md
    end
    CC->>CC: Implements plan

    Note over Dev,Files: Completion
    Dev->>CC: Requests stop
    CC->>Hook: Stop triggers
    Hook->>CC: Blocks until updates done
    CC->>Agent: Spawns implementation-reviewer
    Agent->>Files: Compares to plan
    Agent->>CC: Returns score + findings
    CC->>Files: Updates task status
    CC->>Skill: Uses memory-curator
    Skill->>Files: Appends to memory.jsonl
    Hook->>CC: Allows stop
```

---

## Quick Start

```bash
# Clone Meridian
git clone https://github.com/markmdev/meridian.git
cd meridian

# Copy to your project
cp -R .claude .meridian .mcp.json /path/to/your/project
cd /path/to/your/project

# Make scripts executable
find .claude -type f -name '*.py' -print0 | xargs -0 chmod +x

# (Optional) Configure project type
# Edit .meridian/config.yaml → project_type: hackathon|standard|production
```

Open your project in Claude Code. Hooks activate automatically, MCP servers connect.

---

## Why Not Just CLAUDE.md?

| | `CLAUDE.md` | Meridian |
|-|-------------|----------|
| **Large context** | Claude forgets prompt details as context grows | Hooks reinforce key behaviors throughout the session |
| **Memory** | None | `memory.jsonl` persists lessons across sessions |
| **Task continuity** | None — each session starts fresh | Context files track progress, decisions, next steps |
| **Quality gates** | None | Plan review + implementation review before proceeding |
| **Library docs** | Claude's training data (potentially outdated) | MCP servers provide current documentation |
| **Custom docs** | Must be read manually each session | Injected automatically via `required-context-files.yaml` |

`CLAUDE.md` is a static prompt. Meridian hooks actively enforce behaviors and inject context throughout the session.

---

## Components Deep Dive

<details>
<summary><strong>Hooks — Enforce Workflow</strong></summary>

Hooks are Python scripts triggered at Claude Code lifecycle events. They can inject context, block actions, or modify behavior.

| Hook | Trigger | What it does |
|------|---------|--------------|
| `claude-init.py` | SessionStart (startup) | Injects memory, tasks, CODE_GUIDE into context |
| `session-reload.py` | SessionStart (compact) | Re-injects context after compaction |
| `post-compact-guard.py` | PreToolUse | Blocks first tool until agent acknowledges context |
| `pre-compaction-sync.py` | PreToolUse | Warns when approaching token limit, prompts context save |
| `block-plan-agent.py` | PreToolUse (Task) | Redirects deprecated Plan agent to planning skill |
| `plan-review.py` | PreToolUse (ExitPlanMode) | Requires plan-reviewer before implementation |
| `action-counter.py` | PostToolUse, UserPromptSubmit | Tracks actions for stop hook threshold |
| `plan-approval-reminder.py` | PostToolUse (ExitPlanMode) | Reminds to create task folder |
| `pre-stop-update.py` | Stop | Requires task/memory updates and implementation review |
| `startup-prune-completed-tasks.py` | SessionStart | Archives old completed tasks |
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

### Task Manager Skill

Creates and manages task folders (`.meridian/tasks/TASK-###/`) for storing:
- Plans copied from `.claude/plans/`
- Design docs and task-specific artifacts
- Any task-related documentation

Session context is stored separately in `session-context.md` (always available, not task-dependent).

### Beads Sprint Commands (requires Beads integration)

When `beads_enabled: true`, two slash commands enable autonomous multi-issue workflows:

**`/bd-sprint`** — Starts autonomous workflow for completing Beads work (epics, issues, any scoped work):
- Appends comprehensive workflow template to `session-context.md`
- Template survives context compaction (stays at bottom of file)
- Enforces all phases: Planning → Implementation → Review → Verify → Complete
- Acknowledgment hook detects active sprint and prompts agent to resume after compaction

**`/bd-sprint-stop`** — Removes workflow section when sprint is complete

The workflow ensures agents don't skip steps — planning is mandatory for every issue, all reviewers must pass (score 9+), and session context entries track progress.

### Memory Curator Skill

Manages `memory.jsonl` via scripts (never edit manually). Uses strict criteria:

**The critical test:** "If I delete this entry, will the agent make the same mistake again — or is the fix already in the code?"

- **Add**: Architectural patterns, data model gotchas, API limitations, cross-agent patterns
- **Don't add**: One-time bug fixes (code is fixed), SDK quirks (code handles it), agent behavior rules (belong in operating manual)

```bash
# Add entry
python3 .claude/skills/memory-curator/scripts/add_memory_entry.py \
  --summary "Lesson learned about X" \
  --tags architecture,pattern \
  --links "TASK-042 src/service.ts"

# Edit entry
python3 .claude/skills/memory-curator/scripts/edit_memory_entry.py \
  --id mem-0042 --summary "Updated summary"

# Delete entry
python3 .claude/skills/memory-curator/scripts/delete_memory_entry.py \
  --id mem-0042
```

</details>

<details>
<summary><strong>Agents — Quality Gates</strong></summary>

Agents are specialized subagents that validate work. All reviewers use an **issue-based system** — no scores, just issues or no issues. Loop until all issues are resolved.

### Plan Reviewer

Validates plans before implementation:
- Reads `memory.jsonl` for domain knowledge before analysis
- Verifies file paths and API assumptions against codebase
- Checks for missing steps, dependencies, integration plan, documentation steps
- Uses Context7 and DeepWiki to verify library claims
- Trusts plan claims about packages/versions (user may have private access)
- Returns score (must reach 9+ to proceed) + findings

### Implementation Reviewer

Verifies every plan item was implemented:
- Extracts checklist of EVERY item from the plan
- Verifies each item individually (no skipping, no assumptions)
- Creates issues for incomplete items (Beads issues or markdown file)
- Loop: fix issues → re-run → repeat until no issues

### Code Reviewer (CodeRabbit-style)

Deep code review with full context analysis:
1. Loads context (memory.jsonl, plan, CLAUDE.md)
2. Creates detailed walkthrough of each change (forcing function)
3. Generates sequence diagrams for complex flows (forcing function)
4. Finds real issues — logic bugs, data flow problems, pattern inconsistencies
5. Creates issues for findings (Beads issues or markdown file)

Focuses on issues that actually matter, not checklist items or style preferences.

### Browser Verifier (experimental)

Manual QA using Claude for Chrome MCP:
- Extracts user-facing items from plan
- Actually uses the application in a browser to verify functionality
- Checks visual appearance (layout, styling, responsiveness)
- Tests user flows, form submissions, error states
- Creates issues for failures (Beads issues or markdown file)

Requires Claude for Chrome browser extension.

</details>

<details>
<summary><strong>MCP Servers — External Knowledge</strong></summary>

MCP (Model Context Protocol) servers give Claude access to up-to-date external knowledge. Meridian includes two:

### Context7

Queries documentation for any public library. Claude uses this to:
- Verify library APIs exist and work as expected
- Find correct usage patterns and examples
- Check for deprecations or breaking changes

### DeepWiki

Asks questions about any public GitHub repository. Claude uses this to:
- Understand how external libraries work internally
- Verify integration patterns are correct
- Research best practices for specific tools

**Why MCPs matter:** Claude's training data has a cutoff date. When planning or reviewing, Claude can verify claims against current documentation instead of relying on potentially outdated knowledge.

**Configuration:** `.mcp.json` in project root:
```json
{
  "mcpServers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp"
    },
    "deepwiki": {
      "type": "http",
      "url": "https://mcp.deepwiki.com/mcp"
    }
  }
}
```

</details>

<details>
<summary><strong>Configuration</strong></summary>

### Project Config (`.meridian/config.yaml`)

```yaml
# Project type → which CODE_GUIDE addon to load
project_type: standard  # hackathon | standard | production

# Quality gates
plan_review_enabled: true
implementation_review_enabled: true

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
  - .meridian/memory.jsonl
  - .meridian/task-backlog.yaml
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

**`user_provided_docs`**: Add any project-specific documentation here. These files are injected at the very top of context (before memory and core files), so Claude always has access to your architecture decisions, API contracts, or any other docs you want it to reference.

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
├── .mcp.json                   # MCP server configuration
├── .claude/
│   ├── settings.json          # Hook configuration
│   ├── hooks/
│   │   ├── lib/config.py      # Shared utilities
│   │   ├── claude-init.py     # Session start
│   │   ├── session-reload.py  # Post-compaction
│   │   ├── post-compact-guard.py
│   │   ├── pre-compaction-sync.py
│   │   ├── plan-review.py
│   │   ├── plan-approval-reminder.py
│   │   ├── pre-stop-update.py
│   │   ├── block-plan-agent.py
│   │   ├── action-counter.py  # Tracks actions for stop hook
│   │   ├── startup-prune-completed-tasks.py
│   │   ├── permission-auto-approver.py
│   │   ├── meridian-path-guard.py
│   │   ├── plan-mode-tracker.py
│   │   └── session-cleanup.py
│   ├── commands/
│   │   ├── bd-sprint.md         # Start autonomous workflow
│   │   └── bd-sprint-stop.md    # End autonomous workflow
│   ├── scripts/
│   │   ├── bd-sprint-init.py    # Appends workflow template
│   │   └── bd-sprint-stop.py    # Removes workflow section
│   ├── skills/
│   │   ├── planning/SKILL.md
│   │   ├── task-manager/
│   │   │   ├── SKILL.md
│   │   │   └── scripts/create-task.py
│   │   ├── memory-curator/
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   │       ├── add_memory_entry.py
│   │   │       ├── edit_memory_entry.py
│   │   │       └── delete_memory_entry.py
│   │   └── claudemd-writer/SKILL.md
│   └── agents/
│       ├── plan-reviewer.md
│       ├── implementation-reviewer.md
│       ├── code-reviewer.md
│       └── browser-verifier.md
├── .meridian/
│   ├── config.yaml                   # Project configuration
│   ├── required-context-files.yaml   # What gets injected
│   ├── session-context.md            # Rolling context (always injected)
│   ├── CODE_GUIDE.md                 # Baseline standards
│   ├── CODE_GUIDE_ADDON_HACKATHON.md # Relaxed rules for prototypes
│   ├── CODE_GUIDE_ADDON_PRODUCTION.md # Strict rules for production
│   ├── memory.jsonl                  # Persistent lessons/decisions
│   ├── task-backlog.yaml             # Task index
│   ├── tasks/
│   │   ├── TASK-000-template/        # Template for new tasks
│   │   ├── TASK-001/                 # Plans, docs, artifacts
│   │   └── archive/                  # Old completed tasks
│   └── prompts/
│       └── agent-operating-manual.md # Agent behavior instructions
└── your-code/
```

</details>

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
implementation_review_enabled: false
pre_compaction_sync_enabled: false
```

**How is this different from subagents?**

Subagents don't share live context, re-read docs (token waste), and can't be resumed after interrupts. Meridian keeps Claude as the primary agent and injects context directly.

**What are the MCP servers for?**

Context7 and DeepWiki give Claude access to current library documentation. Claude's training data has a cutoff, so when it needs to verify an API exists or check usage patterns, it queries these servers instead of guessing.

---

## Contributing

PRs and issues welcome at [github.com/markmdev/meridian](https://github.com/markmdev/meridian)

**License:** MIT

---

## Star & Share

If Meridian improves your Claude Code sessions:

- **Star this repo** so others can find it
- Share your experience on [X (@markmdev)](http://x.com/markmdev) or [LinkedIn](http://linkedin.com/in/markmdev)

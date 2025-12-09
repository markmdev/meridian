![Logo](https://github.com/user-attachments/assets/9eb140c8-b938-4e77-ab94-0461a6d919fd)
# **Meridian**: zero‑config Claude Code setup for Tasks, Memory & Guardrails

Meridian keeps Claude Code predictable without changing how you talk to it. You still chat normally while it preserves context, enforces rules, writes tasks, and supports optional TDD.

* **Zero‑config install**: copy two folders, make scripts executable, and go.
* **Deterministic behavior**: hooks *enforce* the right steps (not just suggest them).
* **Persistent context**: tasks, memory, and docs live in your repo.
* **Plug‑in rules**: baseline `CODE_GUIDE.md` + project‑type add‑ons + optional **TDD** override.
* **Zero behavior change**: no commands, no scripts, no special phrasing. You talk to Claude normally; Meridian handles everything behind the scenes.

**Current version:** `0.0.7` (updated 2025‑12‑09). See [CHANGELOG.md](CHANGELOG.md) for details.

> If this setup helps, please ⭐ star the repo and share it.
> Follow updates: [X (Twitter)](http://x.com/markmdev) • [LinkedIn](http://linkedin.com/in/markmdev)

---

## Why this setup exists

Default Claude Code often loses context after compaction, forgets history, and drifts from standards. Claude is customizable: **hooks** and **skills** let you shape behavior, but you need a structure that **can’t be skipped**.

**Meridian** adds lightweight guardrails so Claude:

* **Documents tasks** (brief, approved plan, context) in your repo.
* **Follows guides** (baseline + add‑ons) every session, re-injected by hooks.
* **Injects your docs** into context at startup (configurable in `required-context-files.yaml`).
* **Curates memory** of durable decisions (append‑only `memory.jsonl`).
* **Never loses context after compaction**: hooks reinject the essential docs, standards, and the task Claude was working on so it always returns with full context.

You keep chatting normally; Claude does the rest.

---

## Zero‑config (really)

* No API keys or service wiring required.
* No code changes to your project.
* No subagent orchestration to maintain.

Just copy two folders, make scripts executable, and continue working with Claude as usual.
No workflow changes for the developer: no slash commands, no scripts, no special instructions. You interact with Claude exactly as you already do.

---

## Quick start

```bash
# 0) Get this setup
git clone <THIS_REPO_URL> meridian-setup
cd meridian-setup

# 1) Copy to your project root
cp -R .claude .meridian /path/to/your/project
cd /path/to/your/project

# 2) Make hooks & skills executable
find .claude -type f -name '*.py' -print0 | xargs -0 chmod +x

# 3) (Optional) choose project type / TDD in config
#    .meridian/config.yaml → project_type: hackathon|standard|production; tdd_mode: true|false
```

Open your repo in **Claude Code** and talk to Claude as always.
Hooks inject the system prompt, guides, tasks, memory, and docs—and **Claude** follows them.

---

## Talk in **Plan mode** (important)

**Describe work in Plan mode** so Claude proposes a plan you can approve.
When you approve the plan, a hook forces Claude to create a task (`TASK-###` folder with brief/plan/context) and update the backlog every single time.

Why Plan mode?

* Planning quality improves (fewer back‑and‑forths).
* Exiting Plan mode is a reliable signal for the hook to persist the task plan.
* Your repo becomes the *single source of truth* for ongoing work.

> Shortcut: **Shift + Tab** to switch modes in Claude Code.

---

## What this setup includes

### Main agent manual

The core system prompt that sets behavior and guardrails.
**Default file:** `.meridian/prompts/agent-operating-manual.md`

### Guides

* **Baseline:** `.meridian/CODE_GUIDE.md` — organized by sections (General, Frontend, Backend) with focused, principle-based guidance for Next.js/React + Node/TS.
* **Add‑ons (auto‑injected by config):**

  * `CODE_GUIDE_ADDON_HACKATHON.md` — loosens requirements for simpler projects. Includes graduation checklist.
  * `CODE_GUIDE_ADDON_PRODUCTION.md` — tightens requirements for production needs. Principles only, no specific tool prescriptions.
  * `CODE_GUIDE_ADDON_TDD.md` — **overrides all testing rules**; tests first (Red→Green→Refactor), even in hackathon mode.

### Tasks (after every **approved plan**)

Each task lives in `.meridian/tasks/TASK-###/`:

* `TASK-###-context.md`: the primary source of truth for task state and history — origin, decisions, blockers, session progress, and `MEMORY:` markers

Plans are managed by Claude Code and stored in `.claude/plans/`. The backlog references each plan via `plan_path`.

Backlog: `.meridian/task-backlog.yaml` tracks status (`todo`, `in_progress`, `blocked`, `done`) and `plan_path`.

These task folders aren’t just for the developer; Claude actively uses them to restore context after startup or compaction.

### User-provided docs

Add your own documentation to the agent's context via `.meridian/required-context-files.yaml`:

```yaml
user_provided_docs:
  - docs/architecture.md
  - docs/api-reference.md
```

These files are injected at the very top of the context, before memory and other core files. Use this for architecture docs, API references, or any project-specific documentation the agent should always have access to.

### Memory (append‑only)

`memory.jsonl` stores durable decisions and patterns. Claude reads it automatically.

This memory exists primarily for Claude’s benefit: issues it encountered, architectural decisions, pitfalls, and patterns it should not repeat.

* Claude uses the script (never edits manually):

  ```
  .claude/skills/memory-curator/scripts/add_memory_entry.py \
    --summary "Decision/Pattern…" --tags architecture,pattern --links "TASK-012 services/x.ts"
  ```

---

## Project types (what they mean)

Set in `.meridian/config.yaml`:

```yaml
project_type: standard   # hackathon | standard | production
tdd_mode: false          # true enables TDD add-on and overrides testing rules

# Optional review toggles
plan_review_enabled: true           # require plan-reviewer before exiting plan mode
implementation_review_enabled: true # require implementation-reviewer before stopping

# Pre-compaction context preservation
pre_compaction_sync_enabled: true   # prompt to save context before compaction
pre_compaction_sync_threshold: 150000  # token threshold for warning
```

* **hackathon**: a loosened mode for simpler projects and fast iteration. Use it whenever you don't need production-grade quality.
* **standard**: the baseline defaults, balanced for most work.
* **production**: a stricter mode for production-grade needs (security, reliability, performance).

**TDD (`tdd_mode: true`)**: Tests are written **first** for each behavior slice; this **overrides** any testing guidance from hackathon/production/baseline.

**Precedence:** baseline → project‑type add‑on → **TDD** (if enabled; TDD wins on test rules).

---

## How it actually runs (Claude does the work)

1. **Startup/Reload**
   Hooks inject the Agent Operating Manual, guides, memory, backlog, and task context directly into the conversation via `additionalContext`. A context guard blocks the first tool call until Claude acknowledges it has read the injected context.

2. **Plan**
   You describe the task in Plan mode; Claude proposes a plan. If `plan_review_enabled`, a plan-reviewer agent validates the plan before Claude can exit plan mode.

3. **Approve plan**
   A hook reminds Claude to create a task folder (`TASK-###-context.md`) and update the backlog with the plan path.

4. **Implement**
   Claude writes code following the guides, updates `TASK-###-context.md`, and—if needed—adds memory entries via the script.

   * **If TDD is on:** Claude writes a failing test first, makes it pass, then refactors (per slice).

5. **Approaching Compaction**
   When token usage approaches the threshold (default 150k), a hook prompts Claude to save current progress to the context file—preserving context for the agent that continues after compaction.

6. **Compaction/Resume**
   Reload hook re-injects guidelines, memory, and task context via `additionalContext`. Context guard requires acknowledgment before continuing work.

7. **Stop**
   Stop hook blocks exit until Claude verifies tests/lint/build are clean and task/memory/doc updates are saved. If `implementation_review_enabled`, requires implementation-reviewer agent.

> You don't perform these steps manually—**Claude does**. You chat, approve, and review as normal.

---

## Hooks (what each one enforces)

* **`claude-init.py`** — on session start
  Injects project context (manual, guides, memory, backlog, task context) directly via `additionalContext`. Files are wrapped in XML tags. Creates acknowledgment flag for the context guard.

* **`startup-prune-completed-tasks.py`** — on startup/clear
  Keeps only the 10 most recent completed tasks in `task-backlog.yaml`, moves older `done/completed` entries into `task-backlog-archive.yaml`, and relocates their folders under `.meridian/tasks/archive/`.

* **`session-reload.py`** — on compaction/resume
  Re-injects essential context via `additionalContext` after compaction. In-progress tasks and their context files are included automatically. Creates acknowledgment flag for the context guard.

* **`post-compact-guard.py`** — context acknowledgment guard (before tool use)
  Blocks the first tool call after session start until agent acknowledges the injected context. Ensures Claude reads and understands memory, tasks, CODE_GUIDE, and operating manual before proceeding.

* **`pre-compaction-sync.py`** — before tool use (token monitoring)
  Monitors token usage from transcript. When approaching compaction threshold (default 150k), prompts Claude to save current work to context file. Configurable via `pre_compaction_sync_threshold`.

* **`block-plan-agent.py`** — before Task tool use
  Blocks calls to the deprecated Plan agent and redirects to use the planning skill instead. Ensures main agent retains full conversation context during planning.

* **`plan-review.py`** — before exiting Plan mode
  Requires plan-reviewer agent to validate the plan before implementation. Configurable via `plan_review_enabled`.

* **`plan-approval-reminder.py`** — after exiting Plan mode
  Instructs Claude to archive the plan (copy from `~/.claude/plans/` to task folder), create `TASK-###` via **task‑manager**, and update the backlog.

* **`pre-stop-update.py`** — on stop
  Blocks until Claude updates task files/backlog/memory and verifies tests/lint/build. Optionally requires implementation-reviewer (configurable via `implementation_review_enabled`).

* **`permission-auto-approver.py`** — on `PermissionRequest`
  Auto-allows whitelisted Meridian actions (task-manager, memory-curator, backlog updates, etc.).

These guardrails turn guidance into **deterministic behavior**.

---

## Skills (how Claude writes things down)

* **planning**
  Guides Claude through comprehensive implementation planning. Activates in Plan mode. Claude plans directly (retaining full conversation context) and uses Explore subagents for codebase research.

* **task‑manager**
  Script `create-task.py` creates `TASK-###` from a template and enforces filenames.
  Skill doc `SKILL.md` defines when to create tasks, status transitions, and templates.

* **memory‑curator**
  Scripts `add_memory_entry.py`, `edit_memory_entry.py`, and `delete_memory_entry.py` handle append/update/delete flows for `.meridian/memory.jsonl` (never edit manually).
  Skill doc `SKILL.md` explains when to capture memories, the summary/tag format, and how to run the helper scripts.

---

## FAQ

**Is “hackathon” only for hackathons?**
No. It’s just a label for the *looser* mode—use it for any simpler project where production strength isn’t required.

**Why not subagents?**
They don’t share the full live context, re‑read docs (token waste), can’t be resumed after interrupts, and their actions may not make it back into memory. This setup focuses on making every single interaction more efficient and traceable. You can still add subagents for specialized work if you like.

**Will TDD slow me down?**
In hackathon mode, tests remain minimal but are still **first**. For critical paths, TDD tends to reduce regressions and rework.

**Can I add project‑specific rules?**
Yes—edit `CODE_GUIDE.md` (e.g., “use Drizzle instead of Prisma”). Because the guide is injected each session, Claude will follow it.

---

## Contribute & License

PRs and issues welcome
License: MIT

---

## Star & share

If Meridian improves your Claude sessions:

* ⭐ **Star this repo** so others can find it.
* Share your first `TASK-###` flow with me on [X](http://x.com/markmdev) or [LinkedIn](http://linkedin.com/in/markmdev).

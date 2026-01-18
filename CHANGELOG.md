# Changelog

## [0.0.29] - 2026-01-18

### Added
- **Worktree context preservation**: Install script now preserves `worktree-context.md` entries on update, only refreshing the header (same behavior as `session-context.md`).

### Changed
- **Timestamp format**: Context entries now use `YYYY-MM-DD HH:MM` format (added time to worktree context).

## [0.0.28] - 2026-01-18

### Added
- **PEBBLE_GUIDE**: `pending_verification` status — auto-set when closing issues with open verifications. Enforces that verification actually happens before full closure.
- **PEBBLE_GUIDE**: `pb dep relate/unrelate` — bidirectional non-blocking links for issues that share context without blocking each other.

### Changed
- **Worktree context entry format**: Entries should start with what task/epic was being worked on, then explain what was done, issues found, and current state.

### Fixed
- **Stale state file paths**: Fixed references to `.meridian/.loop-state` and `.meridian/.active-plan` in prompts and README — now correctly point to `.meridian/.state/` directory.

## [0.0.27] - 2026-01-17

### Added
- **`/prompt-writing` skill**: General-purpose prompt writing skill for any AI system. Covers removing redundancy, removing noise, sharpening instructions, and keeping load-bearing content.
- **Deferral prohibition in planning**: Planning skill now explicitly prohibits deferrals ("TBD", "needs investigation", "figure out later"). All investigation must happen during planning, not implementation.
- **Deferral detection in plan-reviewer**: New Phase 6 detects and flags deferred investigation as critical findings.
- **State directory consolidation**: All ephemeral hook state files now live in `.meridian/.state/` for cleaner organization.
- **Worktree context sharing**: New `worktree-context.md` in main worktree for sharing high-level context across git worktrees. Stop and pre-compaction hooks prompt for standup-style updates. Auto-trims to `worktree_context_max_lines` (default: 200).
- **docs-researcher flag tracking**: New PostToolUse hook (`docs-researcher-tracker.py`) creates flag when docs-researcher spawns. SubagentStop hook checks flag for reliable agent detection.
- **install.sh settings.json merge**: Fresh installs now merge user's existing hooks with Meridian's hooks instead of overwriting.

### Changed
- **Session cleanup simplified**: Now deletes entire `.meridian/.state/` directory on startup instead of individual files.
- **claudemd-writer skill**: Fixed missing YAML frontmatter (name, description fields).
- **memory-curator skill**: Cleaned up — removed wrapper tags, excessive dividers, consolidated Field Guidelines section. 143 → 110 lines.
- **Worktree context guidance**: Stop and pre-compaction hooks now use standup-style guidance (2-3 sentences, what was worked on and achieved, no technical implementation details).
- **Removed pre-compaction-sync.log**: No longer logs token calculations to file.

### Technical
- New: `.claude/skills/prompt-writing/SKILL.md`, `.claude/hooks/docs-researcher-tracker.py`, `.meridian/worktree-context.md`
- New constants in `config.py`: `STATE_DIR`, `DOCS_RESEARCHER_FLAG`, worktree detection functions (`get_main_worktree_path()`, `is_main_worktree()`, `get_worktree_name()`), `trim_worktree_context()`
- Migrated all flag paths to use `STATE_DIR`: `PENDING_READS_DIR`, `PRE_COMPACTION_FLAG`, `PLAN_REVIEW_FLAG`, `CONTEXT_ACK_FLAG`, `ACTION_COUNTER_FILE`, `REMINDER_COUNTER_FILE`, `PLAN_ACTION_START_FILE`, `PLAN_MODE_STATE`, `ACTIVE_PLAN_FILE`, `INJECTED_FILES_LOG`, `LOOP_STATE_FILE`
- Updated: All hooks referencing state files, all agent files referencing `.injected-files`, `.gitignore`

## [0.0.26] - 2026-01-15

### Added
- **Lightweight plan detection**: Skip plan-reviewer and feature-writer enforcement when fewer than `plan_review_min_actions` (default: 20) actions occurred since entering plan mode. Quick plans skip heavyweight review.
- **`/coderabbit-review` command**: Wrapper for `/work-until` that handles CodeRabbit AI review cycles. Automatically addresses Critical, Major, Minor, and Out-of-diff comments; skips Nitpicks.
- **Skip-if-unchanged guidance**: Stop hook now tells agent to skip re-running implementation/code reviewers if no significant code changes since last run.
- **Four new config options**:
  - `code_review_enabled` — Control code reviewer separately from implementation reviewer (default: true)
  - `docs_researcher_write_required` — Block docs-researcher if it didn't write to api-docs (default: true)
  - `pebble_scaffolder_enabled` — Control auto-scaffolding after plan approval (default: true)
  - `plan_agent_redirect_enabled` — Control Plan agent → planning skill redirect (default: true)

### Changed
- **Work-until command refactored**: Extracted loop instructions to shared `.meridian/prompts/work-until-loop.md`. Both `/work-until` and `/coderabbit-review` use the same file, reducing duplication.
- **Removed legacy sprint_active detection**: Cleaned unused code from `post-compact-guard.py` that referenced removed `/pb-sprint` commands.

### Technical
- New: `.claude/commands/coderabbit-review.md`, `.meridian/prompts/work-until-loop.md`, `.meridian/prompts/coderabbit-task.md`
- New config helpers in `lib/config.py`: `save_plan_action_start()`, `get_plan_action_count()`, `clear_plan_action_start()`
- Updated: `config.py`, `plan-mode-tracker.py`, `plan-review.py`, `feature-writer-check.py`, `plan-approval-reminder.py`, `docs-researcher-stop.py`, `block-plan-agent.py`, `post-compact-guard.py`, `session-cleanup.py`, `work-until.md`, `config.yaml`

## [0.0.25] - 2026-01-15

### Added
- **docs-researcher SubagentStop hook**: Blocks docs-researcher agent from stopping if it hasn't used the Write tool. Ensures API documentation is actually written to `.meridian/api-docs/`.
- **Pebble context injection**: Session start now injects `pb summary --pretty` (active epics) and `pb history --type create,close --pretty` (recent activity) when Pebble is enabled. Provides immediate visibility into project state.
- **feature-writer enforcement hook**: Optional PreToolUse hook blocks ExitPlanMode if plan is missing verification features (`<!-- VERIFICATION_FEATURES -->` marker). Enable via `feature_writer_enforcement_enabled: true` in config.yaml (default: false).
- **Verification issues with `--verifies` flag**: New Pebble relationship type for verification issues. Verification issues target the task they verify rather than being children. Ready behavior: verification appears in `pb ready` only after its target closes.

### Changed
- **Plan-review-blocked flag timing**: Flag now clears after plan approval (in PostToolUse), not on second ExitPlanMode attempt. Prevents premature flag clearing.
- **Pebble Scaffolder path fix**: Added to reviewer-root-guard.py so it reads PEBBLE_GUIDE.md from correct location.
- **"Fix something → check Epic" guidance**: Agent operating manual now instructs to check relevant Epic/backlog when fixing bugs or making improvements discovered during work.
- **Session-context.md header**: Now explicitly states "DO NOT read this file" since it's already injected at session start.
- **install.sh header update**: Installer now updates session-context.md header while preserving user entries (uses `<!-- SESSION ENTRIES START` marker).
- **Verification issue guidance**: Agent operating manual and PEBBLE_GUIDE.md now explain: if verification can't be performed, don't close — add a comment explaining what's blocking verification.
- **PEBBLE_GUIDE.md verification section**: Complete rewrite explaining `--verifies` flag, ready behavior, and evidence requirements.
- **pebble-scaffolder agent**: Updated to use `--verifies` flag for verification issues instead of parent-child relationship.

### Technical
- New: `docs-researcher-stop.py` SubagentStop hook, `feature-writer-check.py` PreToolUse hook
- New config option: `feature_writer_enforcement_enabled` (default: false)
- Updated: `config.py` (get_pebble_context, stop prompt), `plan-review.py`, `plan-approval-reminder.py`, `reviewer-root-guard.py`, `settings.json`, `agent-operating-manual.md`, `PEBBLE_GUIDE.md`, `pebble-scaffolder.md`, `feature-writer.md`, `code-reviewer.md`, `implementation-reviewer.md`, `install.sh`, `session-context.md`

## [0.0.24] - 2026-01-14

### Added
- **install.sh**: One-line installer and updater. Supports version pinning (`-v X.X.X`), preserves state files on update (memory, session-context, api-docs, config), merges new config options automatically.
- **pebble-scaffolder agent**: Creates Pebble issue hierarchy (epic, tasks, verification subtasks) from approved plans. Reads PEBBLE_GUIDE.md for rules, parses plan phases and verification features, creates all issues with proper parent-child relationships and dependencies. Invoked automatically after plan approval when Pebble is enabled.
- **feature-writer agent**: Generates 5-20 verification features per plan phase. Features are testable acceptance criteria with concrete steps. Supports any verification type (UI, API, CLI, Library, Config/Infra, Data).

### Changed
- **plan-approval-reminder hook**: Now instructs main agent to invoke pebble-scaffolder instead of manually creating issues.
- **PEBBLE_GUIDE.md**: Added verification subtasks section explaining how to verify and close with evidence.
- **agent-operating-manual.md**: Compacted from 447 to 145 lines (68% reduction) following prompt-writing-guide principles.
- **CODE_GUIDE.md**: Expanded Type Safety section (35 lines) emphasizing compiler strictness, no `any`, library type reuse. Variable section sizes instead of artificial uniformity.
- **CODE_GUIDE_ADDON_PRODUCTION.md**: Reorganized by concern (Security, Reliability, Data, Observability, Build & Deploy). Removed Strengthen/Add labels.

### Removed
- **task-backlog system**: Removed in favor of Pebble for task tracking. Removed task-backlog.yaml injection, startup-prune-completed-tasks.py hook, and related code.

## [0.0.23] - 2026-01-13

### Added
- **docs-researcher agent**: New Opus-powered agent that researches external tools, APIs, and products using Firecrawl. Builds comprehensive knowledge docs in `.meridian/api-docs/` covering current versions, API operations, rate limits, best practices, and gotchas.
- **Firecrawl MCP server**: Added to `.mcp.json` for web scraping capabilities. All reviewer agents now have access to Firecrawl tools.
- **API docs system**: New `.meridian/api-docs/` directory with INDEX.md. Injected at session start so agents know which external tools are documented.
- **External API documentation requirement**: Strict new rule — no code using external APIs unless documented in api-docs. Agent operating manual has full workflow for checking INDEX.md and running docs-researcher.

### Changed
- **Renamed Beads to Pebble**: Issue tracker renamed from "Beads" to "Pebble" throughout. Commands changed from `bd` to `pb`. All hooks, agents, guides updated.
- **Planning skill external API phase**: New mandatory Phase 4 (External API Documentation) before decomposition. All external libraries must be documented via docs-researcher before implementation begins.
- **Planning skill follow-up section**: New guidance for appending bug fixes/improvements to existing plan files rather than overwriting.
- **Periodic reminder simplified**: Now prints text directly instead of JSON-wrapped output. Added reminder about api-docs and docs-researcher.
- **Work-until command safety**: Added check to ensure command runs from project root directory.

### Technical
- New: `docs-researcher.md` agent, `.meridian/api-docs/INDEX.md`
- Updated: `.mcp.json`, `planning/SKILL.md`, `agent-operating-manual.md`, `config.py`, `periodic-reminder.py`, `work-until.md`, all agents referencing Beads→Pebble

## [0.0.22] - 2026-01-07

### Added
- **Explore agent**: New Opus-powered agent for deep codebase exploration. Use when you don't know where to start, need broad research across many files, or context window is filling up. Returns comprehensive findings with file paths, line numbers, code snippets. Read-only — cannot modify files.

### Changed
- **Pebble audit trail enforcement**: Stop hook and pre-compaction-sync now emphasize that already-fixed bugs still need issues ("The fix happened, but the record didn't"). Pebble section moved before session context (higher priority). Renamed to "PEBBLE (AUDIT TRAIL)" to reinforce purpose.
- **Implementation-focused pebble language**: Changed "future improvements" and "ideas worth tracking" to "bugs found, broken code, missing error handling, problems that need attention" — language that matches what agents encounter during implementation.
- **Condensed prompts** (preserving behavior):
  - Planning skill: 445 → 150 lines (66% reduction). Two interview phases (business requirements before discovery, technical after). Professional judgment to push back on suboptimal suggestions. No artificial plan size limits.
  - CLAUDE.md writer skill: 292 → 89 lines (70% reduction)
  - Reviewer agents: 1,204 → 454 lines total (62% reduction). All workflow steps, quality criteria, and orphan issue prevention preserved.
- **Explore vs direct tools guidance**: Updated agent-operating-manual and planning skill with decision table for when to use Explore agents vs direct tools (Glob, Grep, Read).

### Technical
- New: `explore.md` agent
- Updated: `planning/SKILL.md`, `claudemd-writer/SKILL.md`, `plan-reviewer.md`, `implementation-reviewer.md`, `code-reviewer.md`, `browser-verifier.md`, `agent-operating-manual.md`, `PEBBLE_GUIDE.md`, `config.py`, `pre-compaction-sync.py`, `periodic-reminder.py`

## [0.0.21] - 2026-01-06

### Changed
- **Human documentation emphasis**: Planning skill and plan-reviewer now treat human-facing documentation as equally important to CLAUDE.md. Phases adding user-visible functionality REQUIRE human docs (README, API docs, etc.), not just agent docs.
- **Plan mode tracker clarity**: Now explicitly tells users to "Send /planning in the chat" when plan mode activates.
- **Plan-reviewer doc checks expanded**: New red flag for phases that add user-visible features without README/user doc updates.

### Technical
- Updated: `plan-reviewer.md`, `plan-mode-tracker.py`, `planning/SKILL.md`

## [0.0.20] - 2026-01-05

### Added
- **Periodic reminder system**: Injects short reminder about key behaviors every N actions (tool calls + user messages). Configurable via `reminder_interval` in config.yaml (default: 10). Resets on session start. Non-blocking — uses `additionalContext`.
- **Important user messages in session-context**: Session context now captures important user instructions, preferences, and constraints that should persist across sessions. Agent can copy user prompts verbatim if needed.
- **Research Before Implementation**: New section in agent-operating-manual.md with mandatory research steps and exploration mindset. Emphasizes searching before assuming something doesn't exist.

### Changed
- **Reviewer agents prevent orphaned issues**: Implementation reviewer, code reviewer, and browser verifier now include guidance to check existing issues, connect to parent work, use `discovered-from` dependencies, and set proper blockers. Every issue should have at least one connection.
- **Planning skill research emphasis**: Added "Before Planning to Create Anything New" subsection — search for existing API endpoints, utilities, components before proposing new ones.
- **Action counter reset timing**: Counter now resets when stop hooks fire (not on every user message). Prevents counter drift when user interrupts mid-work.
- **Session context separator detection**: Fixed to use `SESSION ENTRIES START` marker instead of `---`.

### Technical
- New: `periodic-reminder.py` hook, `REMINDER_COUNTER_FILE` constant in config.py
- Updated: `session-context.md` header, `agent-operating-manual.md`, `config.py` (stop hook, separator detection), `action-counter.py`, `pre-stop-update.py`, `implementation-reviewer.md`, `code-reviewer.md`, `browser-verifier.md`, `planning/SKILL.md`

## [0.0.19] - 2026-01-04

### Added
- **CLAUDE.md section in stop hook**: Prompts agent to create/update CLAUDE.md when creating new modules or making significant architectural changes.
- **Work-until requires reviewers**: Before outputting completion phrase, agent MUST run Implementation Reviewer and Code Reviewer. Loop continues until reviewers return 0 issues.

### Changed
- **Stop hook improvements**:
  - Implementation review: Clarified trigger ("after finishing a plan, epic, or large multi-file task") and added `cd $PROJECT_DIR` instruction
  - Memory section: Rewritten to explain the critical test clearly, references `/memory-curator` skill
  - Pebble section: Expanded with explicit guidance (close, create, update, comment) — removed PEBBLE_GUIDE.md reference (already in context)
- **Reviewer agents navigate to project root**: All reviewers (implementation, code, plan, browser) now `cd "$CLAUDE_PROJECT_DIR"` as Step/Phase 0 before reading `.injected-files`.
- **Injected files use absolute paths**: `.meridian/.injected-files` now contains absolute paths instead of relative paths.
- **claudemd-writer skill**: Emphasizes "Commands first" — setup/test commands should be at the top of CLAUDE.md files. Removed hard line limits (50/100), replaced with "every line competes for Claude's attention". Added precedence note.

### Removed
- **`/pb-sprint` and `/pb-sprint-stop` commands**: Superseded by `/work-until` which provides stop-hook enforcement. The pb-sprint workflow template lacked enforcement mechanism.

### Technical
- Deleted: `pb-sprint.md`, `pb-sprint-stop.md`, `pb-sprint-init.py`, `pb-sprint-stop.py`, `.claude/scripts/` directory
- Updated: `config.py`, `work-until-stop.py`, `injected-files-log.py`, `implementation-reviewer.md`, `code-reviewer.md`, `plan-reviewer.md`, `browser-verifier.md`, `claudemd-writer/SKILL.md`, `README.md`

## [0.0.18] - 2026-01-04

### Added
- **Work-until loop** (`/work-until`): Iterative task completion loop that keeps Claude working until a condition is met.
  - `/work-until TASK --completion-phrase "PHRASE"` — loops until `<complete>PHRASE</complete>` is output (must be TRUE)
  - `--max-iterations N` — auto-stop after N iterations
  - Task prompt is resent each iteration; session-context preserves history
  - Normal stop hook checks (memory, session context, tests) run between iterations
- **Session context rules**: Header now explicitly states to add entries at BOTTOM and re-read fully if partial read was done.

### Changed
- **Stop hook refactored**: Extracted prompt building to shared `build_stop_prompt()` helper in `lib/config.py`. Reduced from 337 to 81 lines.
- **CLAUDE.md section removed**: Stop hook no longer prompts for CLAUDE.md review (now handled in plans).
- **Reviewer agents**: Added "Critical Rules" section — NEVER read partial files, Step 0 is MANDATORY.

### Technical
- New `work-until-stop.py` Stop hook for loop control
- New `.claude/commands/work-until.md` slash command
- New `.claude/hooks/scripts/setup-work-until.sh` setup script
- New loop helpers in `lib/config.py`: `is_loop_active()`, `get_loop_state()`, `update_loop_iteration()`, `clear_loop_state()`, `build_stop_prompt()`
- Added `.loop-state` to `.gitignore`

## [0.0.17] - 2026-01-03

### Added
- **Injected files log**: New hook logs all injected context files to `.meridian/.injected-files` on session start/compact/clear. Includes `pebble_enabled` and `git_comparison` settings.
- **Self-loading reviewer agents**: Implementation Reviewer, Code Reviewer, and Browser Verifier now auto-load context from `.injected-files` — no prompts needed.

### Changed
- **Stop hook simplified**: No longer requires manual prompts for reviewers. Just says "spawn Implementation Reviewer agent" and "Code Reviewer agent".
- **Reviewer agents have Step 0**: All three reviewer agents now read `.meridian/.injected-files` as first step to get plan, settings, and context files.

### Technical
- New `injected-files-log.py` SessionStart hook
- Updated: `implementation-reviewer.md`, `code-reviewer.md`, `browser-verifier.md`, `pre-stop-update.py`
- Added `.injected-files` to `.gitignore`

## [0.0.16] - 2026-01-03

### Added
- **Plan tracker hook**: Automatically tracks active plan by watching Edit/Write/Read operations on `.claude/plans/` files. Saves to `.meridian/.active-plan` for injection after compaction.
- **Pebble workflow improvements**:
  - **One task at a time**: Only ONE issue should be `in_progress` at any moment. Must transition current issue (block/defer/close) before claiming another.
  - **Discovered work pattern**: Full pattern for handling blockers vs deferrable work discovered during implementation.
  - **Comment before closing**: Must add comment with file paths and implementation details before closing any issue. Prevents false closures.
- **Pattern consistency rules**: New guidance requiring agents to read full files and follow established patterns (factory functions, naming, error handling, logging).
- **Full file reads required**: Agents must NEVER use offset/limit to read partial files. Partial reads miss context and lead to inconsistent code.

### Changed
- **Implementation reviewer**: Now checks for pattern consistency violations (e.g., direct instantiation when factory exists).
- **Plan injection for Pebble**: Plans now inject after compaction for Pebble workflows via `.active-plan` file (previously only worked with task-backlog.yaml).

### Technical
- New `plan-tracker.py` PostToolUse hook for Edit|Write|Read matcher
- Updated `config.py` to inject from `.meridian/.active-plan`
- Added `.active-plan` to `.gitignore`
- Updated: `agent-operating-manual.md`, `CODE_GUIDE.md`, `implementation-reviewer.md`, `PEBBLE_GUIDE.md`

## [0.0.15] - 2026-01-03

### Added
- **PEBBLE_GUIDE.md**: Comprehensive Pebble reference guide for agents. Single source of truth for commands, dependency types, and best practices. Injected at session start when Pebble is enabled.

### Changed
- **Pebble guidance centralized**: All hooks/prompts now reference `PEBBLE_GUIDE.md` instead of duplicating command examples. Reduces maintenance burden and ensures consistency.
- **Dependency types clarified**: Only `blocks` affects `pb ready`. Parent-child, related, and discovered-from are informational only — this was a common source of confusion.
- **Ready Front model**: Guide teaches "Ready Front" thinking instead of "phases". Walk backward from goal to create correct dependencies.
- **Cognitive trap documented**: Explicit warning about temporal language ("A before B") inverting dependencies. Use requirement language ("B needs A").
- **PM-style descriptions**: Expanded guidance on writing comprehensive issue descriptions with Purpose/Why This Matters/Requirements/Acceptance Criteria/Context sections.
- **`--parent` flag**: Corrected from `--deps parent:<id>` to `--parent <id>` throughout.

### Technical
- Removed 150+ line `PEBBLE_PROMPT` from `lib/config.py`, now injects `PEBBLE_GUIDE.md` file directly
- Updated: `plan-approval-reminder.py`, `pre-stop-update.py`, `pre-compaction-sync.py`, `code-reviewer.md`, `implementation-reviewer.md`, `pb-sprint-init.py`, `pb-sprint.md`, `config.yaml`

## [0.0.14] - 2026-01-03

### Added
- **Browser verifier agent** (experimental): Manual QA agent using Claude for Chrome MCP. Verifies implementations by actually using the application in a browser — tests user flows, checks visual appearance, creates issues for failures.
- **Action counter for stop hook**: Stop hook skips if fewer than `stop_hook_min_actions` (default: 10) tool calls since last user input. Prevents hook from firing on trivial interactions.
- **Interview depth guidance**: Planning skill now explicitly allows up to 40 questions across multiple rounds for complex tasks.
- **Documentation planning phase**: Planning skill now has mandatory Phase 4.5 requiring explicit CLAUDE.md and human documentation steps for each implementation phase.
- **Documentation verification in plan reviewer**: Plan reviewer now checks that every phase has documentation steps (Phase 3.5).
- **Trust plan claims**: Plan reviewer no longer rejects plans claiming packages/versions/models "don't exist" — user may have access to private/internal/beta resources.
- **Memory context in plan reviewer**: Plan reviewer now reads `memory.jsonl` in Phase 1 for domain knowledge before analyzing plans.

### Changed
- **Code reviewer rewritten (CodeRabbit-style)**: Complete rewrite with 8-phase deep analysis workflow — Load Context, Change Summary, Deep Research, Walkthrough (forcing function), Sequence Diagrams (forcing function), Find Issues, Create Issues, Cleanup. Reviews now include detailed walkthroughs and sequence diagrams to ensure deep understanding.
- **Implementation reviewer simplified**: Replaced multi-type reviewers (phase/integration/completeness) with single checklist-based approach. Extract every item from plan → verify each individually → create issues for incomplete items.
- **Issue-based review system**: Both reviewers now output issues instead of scores. No more 1-10 scoring — just issues or no issues. Loop until all issues resolved.
- **Pebble integration in reviewers**: When `pebble_enabled: true`, reviewers create Pebble issues directly instead of writing to files.
- **Direct tools over Explore agents**: Planning skill now instructs to use Glob/Grep/Read directly for codebase research. Explore agents only for answering direct conceptual questions.
- **Stop hook section reorder**: Sections now ordered by priority (lower in prompt = higher priority): Implementation Review → Memory → Session Context → CLAUDE.md → Pebble → Human Actions → Tests/Lint/Build (highest priority).
- **Stop hook text condensed**: More concise instructions while preserving key information.
- **Pre-compaction sync improved**: Better guidance on what survives compaction (concrete decisions, file paths, error messages) vs what doesn't (vague summaries, implicit context).
- **Pre-compaction Pebble instructions**: When Pebble enabled, prompts agent to create issues for findings discovered during session.
- **Agent operating manual simplified**: Removed redundant Requirements Interview section (~90 lines), replaced with reference to planning skill Phase 0.

### Technical
- New `ACTION_COUNTER_FILE` constant and `stop_hook_min_actions` config option in `.claude/hooks/lib/config.py`
- New `action-counter.py` hook tracks tool calls, resets on UserPromptSubmit
- Reviewers pass `pebble_enabled` flag to control output mode
- Plan reviewer has new "documentation" finding category

### Fixed
- **Plan approval reminder (Pebble mode)**: Now instructs to create ALL sub-tasks upfront (not just first phase), add dependencies BETWEEN sub-tasks within each phase, and write comprehensive PM-style descriptions with Purpose/Requirements/Acceptance Criteria sections. Previously, agents would only create Phase 1 sub-tasks, skip inter-subtask dependencies, and write terse technical descriptions.

## [0.0.13] - 2025-12-30

### Added
- **`/pb-sprint` autonomous workflow**: New slash command starts a comprehensive workflow for completing Pebble work (epics, issues with dependencies, any scoped work). Appends workflow template to `session-context.md` that survives context compaction.
- **`/pb-sprint-stop`**: Removes the workflow section when sprint is complete.
- **Sprint workflow detection**: Acknowledgment hook detects active sprint workflow and prompts agent to resume from where it left off.
- **Auto-approve for plans**: Write/Edit to paths containing `.claude/plans/` now auto-approved.
- **Auto-approve for Pebble CLI**: All `pb` commands now auto-approved.

### Changed
- **Planning mandatory in sprint**: Workflow template now explicitly requires planning for every issue — "No exceptions — even if the issue is 'detailed' or 'simple'".
- **Session context marker clarified**: Changed from `<!-- Session entries below this line... -->` to `<!-- SESSION ENTRIES START - Add timestamped entries below, oldest at top -->`.
- **Reviewer streaming warning**: Added prominent warning about context pollution when listening to reviewer agent streaming output.
- **Session-context.md added to reviewer files**: Reviewers now read session context for additional context.

### Technical
- Slash commands use Python scripts (not bash heredocs) because `$CLAUDE_PROJECT_DIR` unavailable in slash command context.
- Scripts derive project root from `__file__` path and print template so agent sees it immediately.
- Workflow section goes at bottom of session-context.md; regular entries go above it.

## [0.0.12] - 2025-12-30

### Added
- **Rolling session context file**: New `.meridian/session-context.md` replaces per-task context files. Always injected at session start regardless of task status. Agent saves key decisions, discoveries, and context that would be hard to rediscover.
- **Automatic context trimming**: When session context exceeds `session_context_max_lines` (default: 1000), oldest entries are trimmed while preserving the header.
- **CLAUDE.md decision criteria in stop hook**: Stop hook now shows when to create/update CLAUDE.md (new module, public API change, new patterns) vs when to skip (bug fixes, refactoring, internal details).
- **Timestamped session entries**: Session context entries now use `YYYY-MM-DD HH:MM` format instead of just dates.

### Changed
- **Simplified context injection**: Removed per-task context file injection and task file tracking. Session context is always available, even without a formal task.
- **Stop hook updated**: Now prompts to update `session-context.md` instead of `TASK-###-context.md`.
- **Pre-compaction sync updated**: Now prompts to save to `session-context.md` before compaction.
- **Agent operating manual updated**: New "Session Context" section explains how to use the rolling context file.
- **Plan approval reminder rewritten**: Now explicitly lists all 3 required steps (create task folder, copy plan, add backlog entry) with exact YAML format. Previously agent would only copy the plan and skip the backlog entry.
- **Memory curator stricter criteria**: New critical test: "If I delete this entry, will the agent make the same mistake again — or is the fix already in the code?" Explicit SHOULD/SHOULD NOT lists. One-time bug fixes, SDK quirks, and agent behavior rules no longer belong in memory.
- **Stop hook memory guidance updated**: Reflects stricter memory criteria — add patterns affecting future features, don't add one-time fixes.
- **Pebble prompt improvements**: Added `pb stats` for project health, `pb close <id1> <id2> ...` for closing multiple issues, and explicit priority format note (use 0-4 or P0-P4, NOT "high"/"medium"/"low").
- **Pebble reminders in hooks**: When Pebble is enabled, reminders appear in context acknowledgment (check project state), stop hook (update issues), and plan mode tracker (use Pebble to track work).

### Removed
- **Task file tracker hook**: `task-file-tracker.py` removed — no longer needed with rolling session context.
- **Per-task context file injection**: Task context files (`TASK-###-context.md`) are no longer auto-injected. Task folders still exist for plans/docs.
- **`sibling_repos` config**: Removed unused configuration option that was never implemented.

## [0.0.11] - 2025-12-29

### Added
- **Pebble integration**: Optional Git-backed issue tracker for AI agents. When `pebble_enabled: true` in config.yaml, agents receive comprehensive instructions for using Pebble to manage work: understanding project state (`pb ready`, `pb list`, `pb blocked`), creating well-researched issues, managing dependencies, using molecules (epics with execution intent) and gates (quality checkpoints). Agents are instructed to proactively suggest creating issues during conversations.

### Changed
- **Context injection order**: Reordered for better context flow — task backlog now appears before task context files; Pebble prompt (when enabled) appears before agent operating manual.

## [0.0.10] - 2025-12-29

### Added
- **CLAUDE.md review suggestions**: Stop hook detects changed files via `git status` and lists all CLAUDE.md files on path from root to changed folders. Shows (exists) or (missing - create if needed) for each.
- **Configurable CLAUDE.md ignored folders**: New `claudemd_ignored_folders` in config.yaml to skip folders from review suggestions (defaults: node_modules, .git, dist, build, coverage, __pycache__, .next, .nuxt, .output, .cache, .turbo, .parcel-cache, .vite, .svelte-kit).
- **Task file auto-tracking**: New `task-file-tracker.py` PostToolUse hook tracks when agent accesses files in `.meridian/tasks/**`. Tracked files are automatically injected after compaction even if the task isn't in `task-backlog.yaml`. Tracking file cleared after injection.

### Changed
- **Stop hook enhanced**: Now includes CLAUDE.md review section prompting agent to create/update module documentation for changed areas.
- **Context acknowledgment message**: Now reminds agent to retry the blocked action after acknowledging context (prevents skipping steps after compaction).

## [0.0.9] - 2025-12-28

### Added
- **Requirements Interview phase**: Planning skill now has mandatory Phase 0 that requires thorough user interview before any exploration. Covers functional requirements, edge cases, technical implementation, UI/UX, constraints, and scope boundaries.
- **Professional Judgment section**: Agent operating manual now instructs agents to push back on wrong/suboptimal user suggestions. Explain what's wrong, why, propose 2+ alternatives, let user decide.
- **Worktree-safe IDs**: Memory entries (`mem-0001-x7k3`) and task folders (`TASK-001-x7k3`) now include random 4-char suffixes to prevent ID collisions when running parallel Claude sessions via git worktrees.
- **Interview mindset guidance**: Agents should assume they don't know enough, ask non-obvious questions, go deep not broad, interview continuously.

### Changed
- **"Clarify → then act" → "Interview → then act"**: Core behavior now emphasizes iterative questioning (2-3 questions → answers → deeper follow-ups) before implementation.
- **Plan structure template**: Now includes "Requirements (from Interview)" section documenting functional requirements, edge cases, constraints, and out-of-scope items confirmed with user.
- **Quality checklist**: Added "Requirements interview completed" and "Edge cases documented" checkboxes.

### Fixed
- **Pre-compaction sync double-fire bug**: Removed logic that cleaned flag when tokens dropped below threshold. Hook now fires exactly once per session when crossing threshold.

## [0.0.8] - 2025-12-13

### Added
- **Code reviewer agent** (`.claude/agents/code-reviewer.md`): Line-by-line review of all code changes. Reviews for bugs, security, performance, and CODE_GUIDE compliance. Handles different git states (feature branch, uncommitted, staged).
- **Completeness reviewer**: New `review_type: completeness` for implementation-reviewer verifies every plan item was implemented.
- **CLAUDE.md writer skill** (`.claude/skills/claudemd-writer/`): Comprehensive guidance for writing effective CLAUDE.md files. Covers hierarchical injection, "less is more" principle, what/how/why structure.
- **Plan mode tracker** (`plan-mode-tracker.py`): UserPromptSubmit hook detects Plan mode entry and prompts agent to invoke planning skill.
- **Session cleanup hook** (`session-cleanup.py`): Cleans up plan-mode state on session end, compaction, and /clear.
- **Path guard hook** (`meridian-path-guard.py`): Blocks writes to `.meridian/` or `.claude/` folders outside project root. Prevents agents from creating duplicate config folders in subfolders.
- **Human actions docs workflow**: Pre-stop hook now prompts agent to create actionable docs in `.meridian/human-actions-docs/` when work requires human setup (env vars, service accounts, etc.).
- **Dependency management guidance**: Agent operating manual now includes strict workflow for adding dependencies—always query registry, never rely on training data for versions.
- **CI failure fix cycle**: Agent operating manual documents how to handle test/lint/build failures (read full output, fix root cause, verify).
- **Testing strategy in planning**: Planning skill now includes testing requirements section with `AskUserQuestion` for test depth preferences.

### Changed
- **Multi-reviewer strategy expanded**: Pre-stop hook now requires 4 parallel reviewers: phase reviewers, integration reviewer, completeness reviewer, and code reviewer. Exact prompts provided for each.
- **Subagent limits relaxed**: Agent operating manual and planning skill now document that >3 subagents are allowed for thorough exploration and review phases.
- **"Never without alternatives" audit**: Fixed 7 prohibitions that lacked alternatives across CODE_GUIDE.md and agent-operating-manual.md. Every "never do X" now includes "do Y instead".
- **Memory-curator scripts**: Fixed misleading help text—scripts use auto-detected project root, not `CLAUDE_PROJECT_DIR` env var.
- **Detail completeness in planning**: Planning skill now requires explicit steps for every mentioned integration, service, or module.

### Removed
- **TDD addon** (`CODE_GUIDE_ADDON_TDD.md`): Deprecated. Testing guidance moved to planning skill. Agents should always write tests; depth is task-specific.
- **TDD references**: Cleaned up from config.py, required-context-files.yaml, config.yaml.

## [0.0.7] - 2025-12-09

### Added
- **user_provided_docs**: New section in `required-context-files.yaml` for custom documentation. User docs are injected first, before memory and core files.
- **Auto-approve plan copying**: `permission-auto-approver.py` now auto-approves `cp` commands from `~/.claude/plans/` for plan archival.
- **Task creation reminder**: `create-task.py` now outputs next steps including reminder to copy plan from `~/.claude/plans/`.

### Changed
- **CLAUDE_PROJECT_DIR enforcement**: All hooks and scripts now require `CLAUDE_PROJECT_DIR` environment variable with no fallbacks. Prevents scripts from creating files in wrong locations when agent cd's to subfolders.
- **Pre-compaction sync**: Improved token calculation and logging.
- **Cleaner context injection**: Removed noisy `=` separator lines from injected context header/footer.

### Removed
- **relevant-docs.md**: Deprecated file removed. Use `user_provided_docs` in `required-context-files.yaml` instead.

## [0.0.6] - 2025-12-09

### Added
- **Context injection**: Session hooks (`claude-init.py`, `session-reload.py`) now inject file contents directly via `additionalContext` instead of requiring Read tool calls. Files are wrapped in XML tags with explanatory header and acknowledgment footer.
- **Planning skill** (`.claude/skills/planning/SKILL.md`): Replaces the Plan agent. Main agent now plans directly while retaining full conversation context. Uses Explore subagents for codebase research.
- **Plan agent blocker** (`block-plan-agent.py`): Hook that intercepts Plan agent calls and redirects to the planning skill.
- **Multi-reviewer architecture**: For large projects, spawn multiple focused implementation-reviewers (one per phase) plus integration reviewer(s). All reviewers run in parallel and write output to `.meridian/implementation-reviews/`.
- **Mandatory Integration phase**: Every multi-module plan must include an explicit Integration phase covering wiring, entry points, config, data flow, and error propagation.
- **Strict quality checks**: Implementation reviewer now flags hardcoded values, TODO/FIXME comments, and unused/orphaned code.

### Changed
- **Planning workflow**: Main agent creates plans directly using the planning skill instead of delegating to a Plan subagent. This preserves full conversation context—important details discussed with the user won't be lost during planning.
- **Plan content policy**: Plans now describe WHAT and WHY, not HOW. No code snippets or pseudocode (even in English). Describe the destination, not the driving directions.
- **Context acknowledgment flow**: `post-compact-guard.py` simplified to block first tool call and require acknowledgment of injected context before proceeding.
- **Task status filtering**: Changed from whitelist (`in-progress`, `active`) to blacklist approach (not in `done`, `completed`, `finished`, `cancelled`, `archived`).
- **Implementation reviewer output**: Now writes reviews to files (`$CLAUDE_PROJECT_DIR/.meridian/implementation-reviews/`) instead of returning directly. Uses `CLAUDE_PROJECT_DIR` for absolute paths.

### Removed
- **Plan agent** (`.claude/agents/plan.md`): Replaced by the planning skill. The skill provides the same methodology but allows the main agent to retain conversation context.

### Fixed
- Token calculation double-counting: Removed duplicated ephemeral values from calculation
- TASK-TASK prefix bug: Fixed duplicate prefix in context file paths
- Absolute path handling: All agents now use `CLAUDE_PROJECT_DIR` environment variable
- Logging always happens: Token logging now occurs even when pre-compaction flag is active
- Context files added to required reads after compaction

## [0.0.5] - 2025-12-03

### Added
- **Plan archival workflow**: `plan-approval-reminder.py` now instructs agent to copy plans from Claude Code's ephemeral location (`~/.claude/plans/`) to task folders (`.meridian/tasks/TASK-###/plan.md`). Plans persist across sessions.
- **In-progress task injection**: `session-reload.py` and `claude-init.py` now parse `task-backlog.yaml` and inject in-progress tasks at the top of context with XML tags (`<in_progress_tasks>`, `<task_###>`). Plan files from in-progress tasks are automatically added to required reads.
- **Token calculation logging**: `pre-compaction-sync.py` now logs all calculations to `.meridian/.pre-compaction-sync.log` with request IDs for debugging.
- **Task backlog helpers**: New `get_in_progress_tasks()` and `build_task_xml()` functions in shared config module.

### Changed
- **Planning workflow**: Main agent now instructed to delegate to Plan agent instead of manually writing plans. Plan agent must save plans to `.claude/plans/` and can use Explorer subagents.
- **Pending reads**: Changed from single JSON file to directory-based marker files (`.meridian/.pending-context-reads/*.pending`). File deletion is atomic, fixing race conditions when agent reads files in parallel.
- **Absolute paths everywhere**: All hooks and memory-curator scripts now use `CLAUDE_PROJECT_DIR` environment variable for absolute paths. Fixes issues when agent is in subdirectories.
- **`get_additional_review_files()`**: Now accepts `absolute=True` parameter to return absolute paths.

### Fixed
- Race condition when agent reads required context files simultaneously
- Relative paths failing when agent cd's into subdirectories
- Memory curator scripts failing due to relative path resolution

## [0.0.4] - 2025-12-01

### Changed
- **CODE_GUIDE.md refactored**: Complete rewrite from 121 numbered rules to organized sections with headers. Now has shared "General" section for cross-cutting concerns (TypeScript, Error Handling, Security, Testing, Config). Removed universal rules (naming conventions, "comments explain why"), removed niche rules (stampede control, COOP/COEP), removed arbitrary numbers ("~150 lines"), softened absolutes to "prefer X unless Y".
- **CODE_GUIDE_ADDON_HACKATHON.md refactored**: Streamlined with headers, generalized provider names (no more Auth0/Clerk/Firebase specifics), added graduation checklist.
- **CODE_GUIDE_ADDON_PRODUCTION.md refactored**: Principles only, removed specific tech details (TS flags, distroless images, SBOM). Removed dark mode requirement. Focus on what to strengthen, not how.
- **CODE_GUIDE_ADDON_TDD.md refactored**: 244 → 87 lines. Removed code skeletons and output templates. Kept core TDD workflow and "Confirm Test Cases with User" section.
- **agent-operating-manual.md**: Added "Never Do" section (no silent pivots, no arbitrary metric targets, no silent error swallowing). Added "Verify Before Assuming" and "Reading Context Effectively" sections. Added DoD anti-patterns ("NOT done if"). Changed question guidance to encourage asking more.
- **task-manager SKILL.md**: Added "New Task vs Continue Existing" criteria. Added inline context.md template with Origin section.
- **memory-curator SKILL.md**: Added good/bad examples for when to create entries.
- **TASK-000-context.md template**: Added Origin section for planning decisions.

### Removed
- PR link references from all documentation files
- Arbitrary line count guidance from all guides
- Code skeletons from TDD addon
- Output format templates from TDD addon
- Specific tool/flag names from production addon (kept as principles)

## [0.0.3] - 2025-12-01

### Added
- **Pre-compaction sync hook** (`pre-compaction-sync.py`): Monitors token usage from transcript and prompts agent to save context before conversation compacts. Configurable threshold (default 150k tokens).
- **Smart context guard** (`post-compact-guard.py` rewrite): Tracks required file reads in `.meridian/.pending-context-reads`. Allows Read tool for pending files, blocks other tools until all required files are read. No more "read files twice" problem.
- **Required context files config** (`.meridian/required-context-files.yaml`): Centralized config for files that must be read on session start/reload. Supports core files, project-type addons, and TDD addon.
- **Plan review hook** (`plan-review.py`): Requires plan-reviewer agent before exiting plan mode. Configurable via `plan_review_enabled` in config.yaml.
- **Shared helpers module** (`.claude/hooks/lib/config.py`): Extracted common code (YAML parsing, config reading, flag management) from hooks to reduce duplication.
- New config options in `.meridian/config.yaml`:
  - `plan_review_enabled`: Toggle plan-reviewer requirement (default: true)
  - `implementation_review_enabled`: Toggle implementation-reviewer in pre-stop hook (default: true)
  - `pre_compaction_sync_enabled`: Toggle pre-compaction context save prompt (default: true)
  - `pre_compaction_sync_threshold`: Token threshold for pre-compaction warning (default: 150000)

### Changed
- **Task workflow simplified**: Removed `TASK-###.yaml` and `TASK-###-plan.md` from task template. Plans are now managed by Claude Code in `.claude/plans/`. Task folders contain only `TASK-###-context.md` as the primary source of truth.
- **task-backlog.yaml**: Now includes `plan_path` field pointing to Claude Code plan files.
- **TASK-###-context.md template**: Enhanced with Status section, Key Decisions & Tradeoffs section, and structured Session Log format.
- **session-reload.py**: Simplified post-compaction instructions since context should already be saved by pre-compaction hook. Now reads from required-context-files.yaml.
- **claude-init.py**: Now reads from required-context-files.yaml instead of hardcoded file list.
- All hooks refactored to use shared helpers module, reducing code duplication.

### Removed
- `TASK-###.yaml` template file (objective, constraints, requirements now live in Claude Code plan)
- `TASK-###-plan.md` template file (plans managed by Claude Code)
- `.claude/hooks/prompts/session-reload.md` (prompt now generated dynamically)
- `.meridian/.needs-context-review` flag (replaced by `.pending-context-reads` smart tracking)

## [0.0.2] - 2025-11-20

### Added
- `startup-prune-completed-tasks.py` hook, triggered on startup/clear, that automatically archives older `done/completed` tasks. Only the 10 most recent completed tasks stay in `task-backlog.yaml`, and pruned tasks move to `task-backlog-archive.yaml` plus `.meridian/tasks/archive/`.
- `edit_memory_entry.py` and `delete_memory_entry.py` scripts for the memory-curator skill, enabling safe updates/removals in `.meridian/memory.jsonl`. `SKILL.md` now documents how to run both scripts.
- `permission-auto-approver.py`, a PermissionRequest hook that silently whitelists known-safe Meridian actions (memory/task skills, backlog edits, etc.). `settings.json` now invokes this hook for every PermissionRequest event.

### Changed
- Task-manager and memory-curator SKILL guides were heavily trimmed to remove noisy guidance. Both are now shorter, strictly action-focused, and avoid repeating information that bloated the context.
- `relevant-docs.md` now describes section-based doc requirements (“when working on X, read Y”) instead of forcing Claude to read every listed file on startup. Hooks will prompt Claude to read only the docs tied to the area it’s actively working on.


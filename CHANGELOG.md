# Changelog

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
- **Beads integration in reviewers**: When `beads_enabled: true`, reviewers create Beads issues directly instead of writing to files.
- **Direct tools over Explore agents**: Planning skill now instructs to use Glob/Grep/Read directly for codebase research. Explore agents only for answering direct conceptual questions.
- **Stop hook section reorder**: Sections now ordered by priority (lower in prompt = higher priority): Implementation Review → Memory → Session Context → CLAUDE.md → Beads → Human Actions → Tests/Lint/Build (highest priority).
- **Stop hook text condensed**: More concise instructions while preserving key information.
- **Pre-compaction sync improved**: Better guidance on what survives compaction (concrete decisions, file paths, error messages) vs what doesn't (vague summaries, implicit context).
- **Pre-compaction Beads instructions**: When Beads enabled, prompts agent to create issues for findings discovered during session.
- **Agent operating manual simplified**: Removed redundant Requirements Interview section (~90 lines), replaced with reference to planning skill Phase 0.

### Technical
- New `ACTION_COUNTER_FILE` constant and `stop_hook_min_actions` config option in `.claude/hooks/lib/config.py`
- New `action-counter.py` hook tracks tool calls, resets on UserPromptSubmit
- Reviewers pass `beads_enabled` flag to control output mode
- Plan reviewer has new "documentation" finding category

## [0.0.13] - 2025-12-30

### Added
- **`/bd-sprint` autonomous workflow**: New slash command starts a comprehensive workflow for completing Beads work (epics, issues with dependencies, any scoped work). Appends workflow template to `session-context.md` that survives context compaction.
- **`/bd-sprint-stop`**: Removes the workflow section when sprint is complete.
- **Sprint workflow detection**: Acknowledgment hook detects active sprint workflow and prompts agent to resume from where it left off.
- **Auto-approve for plans**: Write/Edit to paths containing `.claude/plans/` now auto-approved.
- **Auto-approve for Beads CLI**: All `bd` commands now auto-approved.

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
- **Beads prompt improvements**: Added `bd stats` for project health, `bd close <id1> <id2> ...` for closing multiple issues, and explicit priority format note (use 0-4 or P0-P4, NOT "high"/"medium"/"low").
- **Beads reminders in hooks**: When Beads is enabled, reminders appear in context acknowledgment (check project state), stop hook (update issues), and plan mode tracker (use Beads to track work).

### Removed
- **Task file tracker hook**: `task-file-tracker.py` removed — no longer needed with rolling session context.
- **Per-task context file injection**: Task context files (`TASK-###-context.md`) are no longer auto-injected. Task folders still exist for plans/docs.
- **`sibling_repos` config**: Removed unused configuration option that was never implemented.

## [0.0.11] - 2025-12-29

### Added
- **Beads integration**: Optional Git-backed issue tracker for AI agents. When `beads_enabled: true` in config.yaml, agents receive comprehensive instructions for using Beads to manage work: understanding project state (`bd ready`, `bd list`, `bd blocked`), creating well-researched issues, managing dependencies, using molecules (epics with execution intent) and gates (quality checkpoints). Agents are instructed to proactively suggest creating issues during conversations.

### Changed
- **Context injection order**: Reordered for better context flow — task backlog now appears before task context files; Beads prompt (when enabled) appears before agent operating manual.

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


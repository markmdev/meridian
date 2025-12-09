# Changelog

## [0.0.7] - 2025-12-09

### Added
- **user_provided_docs**: New section in `required-context-files.yaml` for custom documentation. User docs are injected first, before memory and core files.
- **Auto-approve plan copying**: `permission-auto-approver.py` now auto-approves `cp` commands from `~/.claude/plans/` for plan archival.
- **Task creation reminder**: `create-task.py` now outputs next steps including reminder to copy plan from `~/.claude/plans/`.

### Changed
- **CLAUDE_PROJECT_DIR enforcement**: All hooks and scripts now require `CLAUDE_PROJECT_DIR` environment variable with no fallbacks. Prevents scripts from creating files in wrong locations when agent cd's to subfolders.
- **Pre-compaction sync**: Flag is now removed when token count drops below threshold, allowing retriggering if context grows again.
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


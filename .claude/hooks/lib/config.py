"""
Shared configuration helpers for Meridian hooks.
"""

from pathlib import Path


# =============================================================================
# PATH CONSTANTS
# =============================================================================
MERIDIAN_CONFIG = ".meridian/config.yaml"
REQUIRED_CONTEXT_CONFIG = ".meridian/required-context-files.yaml"
PENDING_READS_DIR = ".meridian/.pending-context-reads"
PRE_COMPACTION_FLAG = ".meridian/.pre-compaction-synced"
PLAN_REVIEW_FLAG = ".meridian/.plan-review-blocked"
CONTEXT_ACK_FLAG = ".meridian/.context-acknowledgment-pending"
SESSION_CONTEXT_FILE = ".meridian/session-context.md"
ACTION_COUNTER_FILE = ".meridian/.action-counter"


# =============================================================================
# YAML PARSING (simple, no dependencies)
# =============================================================================
def get_config_value(content: str, key: str, default: str = "") -> str:
    """Get a simple key: value from YAML content."""
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith(f'{key}:'):
            return stripped.split(':', 1)[1].strip().strip('"\'')
    return default


def parse_yaml_list(content: str, key: str) -> list[str]:
    """Parse a simple YAML list under a key."""
    lines = content.split('\n')
    result = []
    in_section = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            continue

        if stripped.startswith(f'{key}:'):
            in_section = True
            continue

        if in_section and not line.startswith(' ') and not line.startswith('\t') and ':' in stripped:
            break

        if in_section and stripped.startswith('- '):
            result.append(stripped[2:].strip())

    return result


def parse_yaml_dict(content: str, key: str) -> dict[str, str]:
    """Parse a simple YAML dict under a key."""
    lines = content.split('\n')
    result = {}
    in_section = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            continue

        if stripped.startswith(f'{key}:'):
            in_section = True
            continue

        if in_section and not line.startswith(' ') and not line.startswith('\t') and ':' in stripped:
            break

        if in_section and ':' in stripped:
            k, v = stripped.split(':', 1)
            result[k.strip()] = v.strip()

    return result


# =============================================================================
# CONFIG FILE HELPERS
# =============================================================================
def read_file(path: Path) -> str:
    """Read file content or return missing marker."""
    if path.is_file():
        return path.read_text()
    return f"(missing: {path})\n"


def get_project_config(base_dir: Path) -> dict:
    """Read project config and return as dict with defaults."""
    config = {
        'project_type': 'standard',
        'plan_review_enabled': True,
        'implementation_review_enabled': True,
        'pre_compaction_sync_enabled': True,
        'pre_compaction_sync_threshold': 150000,
        'session_context_max_lines': 1000,
        'beads_enabled': False,
        'stop_hook_min_actions': 10,
    }

    config_path = base_dir / MERIDIAN_CONFIG
    if not config_path.exists():
        return config

    try:
        content = config_path.read_text()

        # Project type
        pt = get_config_value(content, 'project_type')
        if pt in ('hackathon', 'standard', 'production'):
            config['project_type'] = pt

        # Plan review
        pr = get_config_value(content, 'plan_review_enabled')
        if pr:
            config['plan_review_enabled'] = pr.lower() != 'false'

        # Implementation review
        ir = get_config_value(content, 'implementation_review_enabled')
        if ir:
            config['implementation_review_enabled'] = ir.lower() != 'false'

        # Pre-compaction sync
        pcs = get_config_value(content, 'pre_compaction_sync_enabled')
        if pcs:
            config['pre_compaction_sync_enabled'] = pcs.lower() != 'false'

        # Threshold
        threshold = get_config_value(content, 'pre_compaction_sync_threshold')
        if threshold:
            try:
                config['pre_compaction_sync_threshold'] = int(threshold)
            except ValueError:
                pass

        # Session context max lines
        max_lines = get_config_value(content, 'session_context_max_lines')
        if max_lines:
            try:
                config['session_context_max_lines'] = int(max_lines)
            except ValueError:
                pass

        # Beads integration
        beads = get_config_value(content, 'beads_enabled')
        if beads:
            config['beads_enabled'] = beads.lower() == 'true'

        # Stop hook minimum actions threshold
        min_actions = get_config_value(content, 'stop_hook_min_actions')
        if min_actions:
            try:
                config['stop_hook_min_actions'] = int(min_actions)
            except ValueError:
                pass

    except IOError:
        pass

    return config


def get_required_files(base_dir: Path) -> list[str]:
    """Get list of required context files based on config."""
    config_path = base_dir / REQUIRED_CONTEXT_CONFIG
    if not config_path.exists():
        return [
            ".meridian/prompts/agent-operating-manual.md",
            ".meridian/CODE_GUIDE.md",
            ".meridian/memory.jsonl",
            ".meridian/task-backlog.yaml",
        ]

    content = config_path.read_text()
    files = parse_yaml_list(content, 'core')

    # Get project config for conditional files
    project_config = get_project_config(base_dir)

    # Add project type addon
    addons = parse_yaml_dict(content, 'project_type_addons')
    project_type = project_config['project_type']
    if project_type in addons:
        addon_path = addons[project_type]
        if (base_dir / addon_path).exists():
            files.append(addon_path)

    return files


def get_additional_review_files(base_dir: Path, absolute: bool = False) -> list[str]:
    """Get list of additional files for implementation/plan review.

    Args:
        base_dir: Base directory of the project
        absolute: If True, return absolute paths; otherwise relative paths
    """
    files = [".meridian/CODE_GUIDE.md", ".meridian/memory.jsonl", ".meridian/session-context.md"]
    project_config = get_project_config(base_dir)

    if project_config['project_type'] == 'hackathon':
        addon = ".meridian/CODE_GUIDE_ADDON_HACKATHON.md"
        if (base_dir / addon).exists():
            files.append(addon)
    elif project_config['project_type'] == 'production':
        addon = ".meridian/CODE_GUIDE_ADDON_PRODUCTION.md"
        if (base_dir / addon).exists():
            files.append(addon)

    if absolute:
        return [str(base_dir / f) for f in files]
    return files


# =============================================================================
# FLAG FILE HELPERS
# =============================================================================
def cleanup_flag(base_dir: Path, flag_path: str) -> None:
    """Delete a flag file if it exists."""
    path = base_dir / flag_path
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


def create_flag(base_dir: Path, flag_path: str) -> None:
    """Create a flag file."""
    path = base_dir / flag_path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    except Exception:
        pass


def flag_exists(base_dir: Path, flag_path: str) -> bool:
    """Check if a flag file exists."""
    return (base_dir / flag_path).exists()


# =============================================================================
# SESSION CONTEXT HELPERS
# =============================================================================
def trim_session_context(base_dir: Path, max_lines: int) -> None:
    """Trim session context file to max_lines, preserving header.

    The header (everything up to and including the "---" separator line)
    is preserved. Lines after the separator are trimmed from the top
    (oldest first) to keep the file under max_lines total.

    Args:
        base_dir: Project root directory
        max_lines: Maximum lines to keep (0 = no trimming)
    """
    if max_lines <= 0:
        return

    context_file = base_dir / SESSION_CONTEXT_FILE
    if not context_file.exists():
        return

    try:
        content = context_file.read_text()
        lines = content.split('\n')

        if len(lines) <= max_lines:
            return

        # Find header separator (---)
        separator_idx = -1
        for i, line in enumerate(lines):
            if line.strip() == '---':
                separator_idx = i
                break

        if separator_idx == -1:
            # No separator found, just trim from top
            trimmed = lines[-max_lines:]
        else:
            # Preserve header (including separator)
            header = lines[:separator_idx + 1]
            body = lines[separator_idx + 1:]

            # Calculate how many body lines we can keep
            available_for_body = max_lines - len(header)
            if available_for_body <= 0:
                # Header alone exceeds max, just keep header
                trimmed = header
            else:
                # Keep newest body lines (from end)
                trimmed = header + body[-available_for_body:]

        context_file.write_text('\n'.join(trimmed))
    except Exception:
        pass


# =============================================================================
# PENDING READS DIRECTORY HELPERS
# =============================================================================
def create_pending_reads(base_dir: Path, files: list[str]) -> None:
    """Create pending reads directory with marker files for each required file."""
    pending_dir = base_dir / PENDING_READS_DIR

    # Clean up any existing directory
    if pending_dir.exists():
        try:
            for f in pending_dir.iterdir():
                f.unlink()
            pending_dir.rmdir()
        except Exception:
            pass

    # Create fresh directory with marker files
    try:
        pending_dir.mkdir(parents=True, exist_ok=True)
        for i, file_path in enumerate(files):
            marker = pending_dir / f"{i}.pending"
            marker.write_text(file_path)
    except Exception:
        pass


def get_pending_reads(base_dir: Path) -> list[str]:
    """Get list of pending files from marker directory."""
    pending_dir = base_dir / PENDING_READS_DIR

    if not pending_dir.exists() or not pending_dir.is_dir():
        return []

    files = []
    try:
        for marker in sorted(pending_dir.iterdir()):
            if marker.suffix == ".pending":
                files.append(marker.read_text().strip())
    except Exception:
        pass

    return files


def remove_pending_read(base_dir: Path, file_path: str) -> bool:
    """Remove a file from pending reads. Returns True if found and removed."""
    pending_dir = base_dir / PENDING_READS_DIR

    if not pending_dir.exists():
        return False

    normalized_target = str(Path(file_path).resolve())

    try:
        for marker in pending_dir.iterdir():
            if marker.suffix == ".pending":
                pending_file = marker.read_text().strip()
                try:
                    normalized_pending = str(Path(pending_file).resolve())
                except Exception:
                    normalized_pending = pending_file

                if normalized_pending == normalized_target:
                    marker.unlink()  # Atomic delete
                    return True
    except Exception:
        pass

    return False


def cleanup_pending_reads(base_dir: Path) -> None:
    """Remove pending reads directory if empty."""
    pending_dir = base_dir / PENDING_READS_DIR

    if not pending_dir.exists():
        return

    try:
        remaining = list(pending_dir.iterdir())
        if not remaining:
            pending_dir.rmdir()
    except Exception:
        pass


# =============================================================================
# TASK BACKLOG HELPERS
# =============================================================================
COMPLETED_STATUSES = ('done', 'completed', 'finished', 'cancelled', 'archived')


def get_in_progress_tasks(base_dir: Path) -> list[dict]:
    """Parse task-backlog.yaml and return all non-completed tasks."""
    backlog_path = base_dir / ".meridian" / "task-backlog.yaml"
    if not backlog_path.exists():
        return []

    try:
        content = backlog_path.read_text()
    except IOError:
        return []

    tasks = []
    current_task = {}
    in_tasks_section = False

    for line in content.split('\n'):
        stripped = line.strip()

        # Detect tasks section
        if stripped.startswith('tasks:'):
            in_tasks_section = True
            continue

        if not in_tasks_section:
            continue

        # New task item
        if stripped.startswith('- id:'):
            if current_task and current_task.get('status', '').lower() not in COMPLETED_STATUSES:
                tasks.append(current_task)
            current_task = {'id': stripped.split(':', 1)[1].strip().strip('"\'') }
            continue

        # Task properties
        if current_task and ':' in stripped and not stripped.startswith('-'):
            key, value = stripped.split(':', 1)
            current_task[key.strip()] = value.strip().strip('"\'')

    # Don't forget the last task
    if current_task and current_task.get('status', '').lower() not in COMPLETED_STATUSES:
        tasks.append(current_task)

    return tasks


def build_task_xml(tasks: list[dict], claude_project_dir: str) -> str:
    """Build XML representation of in-progress tasks."""
    if not tasks:
        return ""

    xml_parts = ["<in_progress_tasks>"]
    for task in tasks:
        task_id = task.get('id', 'unknown')
        status = task.get('status', 'unknown')
        plan_path = task.get('plan_path', '')
        task_path = task.get('path', '')

        # Build absolute paths
        if plan_path and not plan_path.startswith('/'):
            plan_path = f"{claude_project_dir}/{plan_path}"
        if task_path and not task_path.startswith('/'):
            task_path = f"{claude_project_dir}/{task_path}"

        # Handle IDs with or without TASK- prefix
        id_part = task_id if task_id.startswith('TASK-') else f"TASK-{task_id}"

        xml_parts.append(f"<task_{task_id}>")
        xml_parts.append(f"  status: {status}")
        if task_path:
            xml_parts.append(f"  context: {task_path}{id_part}-context.md")
        if plan_path:
            xml_parts.append(f"  plan: {plan_path}")
        xml_parts.append(f"</task_{task_id}>")

    xml_parts.append("</in_progress_tasks>")
    return "\n".join(xml_parts)


# =============================================================================
# BEADS INTEGRATION
# =============================================================================
BEADS_PROMPT = """
<beads-issue-tracker>

**Beads is ENABLED for this project.** You MUST actively use Beads to manage all work.

Beads is a Git-backed graph issue tracker designed for AI coding agents. It provides persistent memory across sessions, dependency tracking, and structured workflows. All work should be tracked as Beads issues.

## Understanding Project State (Start Here)

At the beginning of each session, understand what's happening in the project:

| Command | Purpose |
|---------|---------|
| `bd ready --json` | **Start here** — shows unblocked issues ready for work |
| `bd list --status in_progress --json` | What's currently being worked on |
| `bd blocked --json` | Issues waiting on dependencies |
| `bd stats` | Project health — open/closed/blocked counts |
| `bd list --json` | All open issues |
| `bd show <id> --json` | Deep dive into specific issue (description, deps, history) |

Use these commands to understand context from previous sessions — what was in progress, what got blocked, what's next.

## When to Create Issues (Be Proactive)

Create Beads issues when:
- User mentions work to do ("fix X", "add Y", "investigate Z")
- You discover bugs or problems during implementation
- Work has dependencies or could block other work
- Breaking large tasks into trackable sub-tasks
- Research or exploratory work with fuzzy boundaries
- Ideas worth capturing for later

**Suggest creating issues during conversations**: "Would you like me to create a Beads issue to track this?"

## Creating Issues (Research First!)

**IMPORTANT**: Before creating an issue, thoroughly research the task:
- Explore relevant code to understand scope and complexity
- Identify affected files and modules
- Note dependencies on other systems or issues
- Understand edge cases and potential blockers
- Gather enough context to write a comprehensive description

A well-researched issue saves time later. Don't create vague issues.

```bash
bd create "Title" --description "Context and details" -t <type> -p <priority> --json
```

**Types**: `task` (default), `bug`, `feature`, `epic`, `chore`

**Priorities**: `0` (critical) → `4` (backlog), default is `2`. Use 0-4 or P0-P4 — NOT "high"/"medium"/"low".

## Managing Dependencies

Dependencies control execution order and show relationships:

| Dependency Type | Meaning |
|-----------------|---------|
| `blocks` | Hard dependency — must complete first |
| `discovered-from` | Found while working on parent task |
| `parent-child` | Hierarchical (epic → subtasks) |
| `related` | Soft link, doesn't block |

**Commands**:
```bash
bd dep add <child-id> <parent-id>              # child is blocked by parent
bd dep add <id> <other> --type discovered-from # link discovered work
```

**Tracking discovered work**: When you find bugs or new work during a task, create an issue with `--deps discovered-from:<current-task-id>` to maintain traceability.

## Workflow Commands

| Command | Purpose |
|---------|---------|
| `bd update <id> --status in_progress --json` | Claim a task |
| `bd update <id> --status blocked --json` | Mark as blocked |
| `bd update <id> --assignee <name> --json` | Assign to someone |
| `bd close <id> --reason "..." --json` | Complete work |
| `bd close <id1> <id2> ...` | Close multiple issues at once (more efficient) |

## Complex Workflows: Molecules & Gates

### What are Molecules?

A **molecule** is an epic with execution intent — a parent issue with child tasks that form a workflow. Unlike simple epics that just group issues, molecules are designed to be *executed* by agents.

How molecules work:
- Parent issue contains the overall goal
- Child issues are the steps to achieve it
- Dependencies between children control execution order
- Agent picks up the molecule and executes ready children in parallel
- When all children close, the molecule is complete

### What are Gates?

A **gate** is a quality checkpoint issue. It's a special issue type that must pass before downstream work can proceed. Gates enforce quality, reviews, or approvals in workflows.

**Examples of gates**:
- "QA Sign-off" — blocks release until QA approves
- "Security Review" — blocks deployment until security team reviews
- "Performance Benchmark" — blocks merge until performance criteria met

### Creating Molecules & Gates

```bash
# Create the parent molecule (epic)
bd create "Feature Name" -t epic --description "..." --json

# Create child tasks with parent dependency
bd create "Step 1" -t task --deps parent:<epic-id> --json
bd create "Step 2" -t task --deps parent:<epic-id> --json
bd create "Quality gate" -t gate --deps parent:<epic-id> --json

# Add execution order dependencies between children
bd dep add <step2-id> <step1-id>     # step2 waits for step1
bd dep add <gate-id> <step2-id>       # gate waits for step2
```

Now `bd ready` will show steps in correct order based on dependencies.

## Filtering & Querying

```bash
bd list --status open --json           # All open issues
bd list --priority 0 --json            # Critical issues only
bd list --type bug --json              # All bugs
bd list --label backend --json         # By label
bd list --assignee alice --json        # By assignee
```

## Best Practices

1. **Always use `--json`** flag for programmatic output
2. **Research before creating** — explore code, understand scope, write detailed descriptions
3. **Link discovered work** to parent with `discovered-from`
4. **Break down large work** into dependent sub-issues
5. **Use molecules for multi-step work** — not just grouping, but execution flow
6. **Add gates for quality checkpoints** — enforce reviews and approvals
7. **Update status** as you work (in_progress → blocked → done)
8. **Check `bd ready`** to find your next task
9. **Use `bd show`** to understand issue history and context

</beads-issue-tracker>
"""


# =============================================================================
# CONTEXT INJECTION HELPERS
# =============================================================================
def build_injected_context(base_dir: Path, claude_project_dir: str, source: str = "startup") -> str:
    """Build the full injected context string with XML-wrapped file contents.

    Args:
        base_dir: Base directory of the project
        claude_project_dir: CLAUDE_PROJECT_DIR environment variable value
        source: Source of the injection (startup, resume, clear, compact)

    Returns:
        Full context string ready for additionalContext injection
    """
    parts = []

    # Header
    parts.append("<injected-project-context>")
    parts.append("")
    parts.append("This context contains critical project information you MUST understand before working.")
    parts.append("Read and internalize it before responding to the user.")
    parts.append("")

    # Get in-progress tasks
    in_progress_tasks = get_in_progress_tasks(base_dir)

    # Build ordered file list
    files_to_inject = []

    # 0. User-provided docs (injected first, before everything else)
    config_path = base_dir / REQUIRED_CONTEXT_CONFIG
    if config_path.exists():
        content = config_path.read_text()
        user_docs = parse_yaml_list(content, 'user_provided_docs')
        for doc_path in user_docs:
            full_path = base_dir / doc_path
            if full_path.exists():
                files_to_inject.append((doc_path, full_path))

    # 1. Memory (past decisions)
    memory_path = base_dir / ".meridian" / "memory.jsonl"
    if memory_path.exists():
        files_to_inject.append((".meridian/memory.jsonl", memory_path))

    # 2. Task backlog
    backlog_path = base_dir / ".meridian" / "task-backlog.yaml"
    if backlog_path.exists():
        files_to_inject.append((".meridian/task-backlog.yaml", backlog_path))

    # 3. Session context (rolling cross-session context)
    session_context_path = base_dir / SESSION_CONTEXT_FILE
    if session_context_path.exists():
        files_to_inject.append((SESSION_CONTEXT_FILE, session_context_path))

    # 4. Plan files for in-progress tasks
    for task in in_progress_tasks:
        plan_path = task.get('plan_path', '')
        if plan_path:
            if plan_path.startswith('/'):
                full_path = Path(plan_path)
            else:
                full_path = base_dir / plan_path
            if full_path.exists():
                files_to_inject.append((plan_path, full_path))

    # 5. CODE_GUIDE and addons
    code_guide_path = base_dir / ".meridian" / "CODE_GUIDE.md"
    if code_guide_path.exists():
        files_to_inject.append((".meridian/CODE_GUIDE.md", code_guide_path))

    # Get project config for addons and beads
    project_config = get_project_config(base_dir)

    if project_config['project_type'] == 'hackathon':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_HACKATHON.md"
        if addon_path.exists():
            files_to_inject.append((".meridian/CODE_GUIDE_ADDON_HACKATHON.md", addon_path))
    elif project_config['project_type'] == 'production':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_PRODUCTION.md"
        if addon_path.exists():
            files_to_inject.append((".meridian/CODE_GUIDE_ADDON_PRODUCTION.md", addon_path))

    # Inject each file with XML tags
    for rel_path, full_path in files_to_inject:
        try:
            content = full_path.read_text()
            parts.append(f'<file path="{rel_path}">')
            parts.append(content.rstrip())
            parts.append('</file>')
            parts.append("")
        except IOError:
            parts.append(f'<file path="{rel_path}" error="Could not read file" />')
            parts.append("")

    # 6. Beads integration prompt (if enabled)
    if project_config.get('beads_enabled', False):
        parts.append(BEADS_PROMPT.strip())
        parts.append("")

    # 7. Agent operating manual
    manual_path = base_dir / ".meridian" / "prompts" / "agent-operating-manual.md"
    if manual_path.exists():
        try:
            content = manual_path.read_text()
            parts.append(f'<file path=".meridian/prompts/agent-operating-manual.md">')
            parts.append(content.rstrip())
            parts.append('</file>')
            parts.append("")
        except IOError:
            parts.append(f'<file path=".meridian/prompts/agent-operating-manual.md" error="Could not read file" />')
            parts.append("")

    # Footer with acknowledgment request
    parts.append("You have received the complete project context above.")
    parts.append("This information is CRITICAL for working correctly on this project.")
    parts.append("")
    parts.append("Before doing anything else:")
    parts.append("1. Confirm you have read and understood the memory entries")
    parts.append("2. Confirm you understand any in-progress tasks and their current state")
    parts.append("3. Confirm you will follow the CODE_GUIDE conventions")
    parts.append("4. Confirm you will operate according to the agent-operating-manual")
    parts.append("")
    parts.append("Acknowledge this context by briefly stating what you understand about")
    parts.append("the current project state, then ask the user what they'd like to work on.")
    parts.append("")
    parts.append("</injected-project-context>")

    # Trim session context file if over limit
    max_lines = project_config.get('session_context_max_lines', 1000)
    trim_session_context(base_dir, max_lines)

    return "\n".join(parts)

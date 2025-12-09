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
        'tdd_mode': False,
        'plan_review_enabled': True,
        'implementation_review_enabled': True,
        'pre_compaction_sync_enabled': True,
        'pre_compaction_sync_threshold': 150000,
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

        # TDD mode
        tdd = get_config_value(content, 'tdd_mode')
        config['tdd_mode'] = tdd.lower() in ('true', 'yes', 'on', '1')

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
            ".meridian/relevant-docs.md",
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

    # Add TDD addon if enabled
    if project_config['tdd_mode']:
        tdd_addon = get_config_value(content, 'tdd_addon')
        if tdd_addon and (base_dir / tdd_addon).exists():
            files.append(tdd_addon)

    return files


def get_additional_review_files(base_dir: Path, absolute: bool = False) -> list[str]:
    """Get list of additional files for implementation/plan review.

    Args:
        base_dir: Base directory of the project
        absolute: If True, return absolute paths; otherwise relative paths
    """
    files = [".meridian/CODE_GUIDE.md", ".meridian/memory.jsonl"]
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

    # Header explanation
    parts.append("<injected-project-context>")
    parts.append("")
    parts.append("=" * 80)
    parts.append("IMPORTANT: PROJECT CONTEXT INJECTION")
    parts.append("=" * 80)
    parts.append("")
    parts.append("This context has been automatically injected at session start.")
    parts.append("It contains critical project information you MUST understand before working:")
    parts.append("")
    parts.append("- Memory: Past decisions, lessons learned, architectural patterns")
    parts.append("- Tasks: Current work in progress with context and plans")
    parts.append("- Code Guide: Coding conventions and standards for this project")
    parts.append("- Operating Manual: How you should behave as an agent")
    parts.append("")
    parts.append("READ AND INTERNALIZE this context before responding to the user.")
    parts.append("")

    # Get in-progress tasks
    in_progress_tasks = get_in_progress_tasks(base_dir)

    # Build ordered file list
    files_to_inject = []

    # 1. Memory (most important - past decisions)
    memory_path = base_dir / ".meridian" / "memory.jsonl"
    if memory_path.exists():
        files_to_inject.append((".meridian/memory.jsonl", memory_path))

    # 2. Task context files (current work)
    for task in in_progress_tasks:
        task_id = task.get('id', '')
        task_path = task.get('path', '')
        if task_path and task_id:
            id_part = task_id if task_id.startswith('TASK-') else f"TASK-{task_id}"
            context_file = base_dir / task_path / f"{id_part}-context.md"
            if context_file.exists():
                files_to_inject.append((f"{task_path}{id_part}-context.md", context_file))

    # 3. Task backlog
    backlog_path = base_dir / ".meridian" / "task-backlog.yaml"
    if backlog_path.exists():
        files_to_inject.append((".meridian/task-backlog.yaml", backlog_path))

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

    # Get project config for addons
    project_config = get_project_config(base_dir)

    if project_config['project_type'] == 'hackathon':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_HACKATHON.md"
        if addon_path.exists():
            files_to_inject.append((".meridian/CODE_GUIDE_ADDON_HACKATHON.md", addon_path))
    elif project_config['project_type'] == 'production':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_PRODUCTION.md"
        if addon_path.exists():
            files_to_inject.append((".meridian/CODE_GUIDE_ADDON_PRODUCTION.md", addon_path))

    if project_config['tdd_mode']:
        tdd_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_TDD.md"
        if tdd_path.exists():
            files_to_inject.append((".meridian/CODE_GUIDE_ADDON_TDD.md", tdd_path))

    # 6. Agent operating manual
    manual_path = base_dir / ".meridian" / "prompts" / "agent-operating-manual.md"
    if manual_path.exists():
        files_to_inject.append((".meridian/prompts/agent-operating-manual.md", manual_path))

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

    # Footer with acknowledgment request
    parts.append("=" * 80)
    parts.append("END OF PROJECT CONTEXT")
    parts.append("=" * 80)
    parts.append("")
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

    return "\n".join(parts)

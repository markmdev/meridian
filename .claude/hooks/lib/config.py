"""
Shared configuration helpers for Meridian hooks.
"""

import subprocess
from pathlib import Path


# =============================================================================
# PATH CONSTANTS
# =============================================================================
MERIDIAN_CONFIG = ".meridian/config.yaml"
REQUIRED_CONTEXT_CONFIG = ".meridian/required-context-files.yaml"
SESSION_CONTEXT_FILE = ".meridian/session-context.md"
WORKTREE_CONTEXT_FILE = ".meridian/worktree-context.md"

# System state files (ephemeral, cleaned up on session start)
STATE_DIR = ".meridian/.state"
PENDING_READS_DIR = f"{STATE_DIR}/pending-context-reads"
PRE_COMPACTION_FLAG = f"{STATE_DIR}/pre-compaction-synced"
PLAN_REVIEW_FLAG = f"{STATE_DIR}/plan-review-blocked"
CONTEXT_ACK_FLAG = f"{STATE_DIR}/context-acknowledgment-pending"
ACTION_COUNTER_FILE = f"{STATE_DIR}/action-counter"
REMINDER_COUNTER_FILE = f"{STATE_DIR}/reminder-counter"
PLAN_ACTION_START_FILE = f"{STATE_DIR}/plan-action-start"
DOCS_RESEARCHER_FLAG = f"{STATE_DIR}/docs-researcher-active"
PLAN_MODE_STATE = f"{STATE_DIR}/plan-mode-state"
ACTIVE_PLAN_FILE = f"{STATE_DIR}/active-plan"
INJECTED_FILES_LOG = f"{STATE_DIR}/injected-files"


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
        'worktree_context_max_lines': 200,
        'pebble_enabled': False,
        'stop_hook_min_actions': 10,
        'feature_writer_enforcement_enabled': False,
        'plan_review_min_actions': 20,
        'code_review_enabled': True,
        'docs_researcher_write_required': True,
        'pebble_scaffolder_enabled': True,
        'plan_agent_redirect_enabled': True,
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

        # Worktree context max lines
        wt_max_lines = get_config_value(content, 'worktree_context_max_lines')
        if wt_max_lines:
            try:
                config['worktree_context_max_lines'] = int(wt_max_lines)
            except ValueError:
                pass

        # Pebble integration
        pebble = get_config_value(content, 'pebble_enabled')
        if pebble:
            config['pebble_enabled'] = pebble.lower() == 'true'

        # Stop hook minimum actions threshold
        min_actions = get_config_value(content, 'stop_hook_min_actions')
        if min_actions:
            try:
                config['stop_hook_min_actions'] = int(min_actions)
            except ValueError:
                pass

        # Feature writer enforcement
        fw_enabled = get_config_value(content, 'feature_writer_enforcement_enabled')
        if fw_enabled:
            config['feature_writer_enforcement_enabled'] = fw_enabled.lower() == 'true'

        # Plan review minimum actions threshold
        plan_min_actions = get_config_value(content, 'plan_review_min_actions')
        if plan_min_actions:
            try:
                config['plan_review_min_actions'] = int(plan_min_actions)
            except ValueError:
                pass

        # Code review (separate from implementation review)
        cr_enabled = get_config_value(content, 'code_review_enabled')
        if cr_enabled:
            config['code_review_enabled'] = cr_enabled.lower() != 'false'

        # Docs researcher write requirement
        dr_write = get_config_value(content, 'docs_researcher_write_required')
        if dr_write:
            config['docs_researcher_write_required'] = dr_write.lower() != 'false'

        # Pebble scaffolder auto-invocation
        ps_enabled = get_config_value(content, 'pebble_scaffolder_enabled')
        if ps_enabled:
            config['pebble_scaffolder_enabled'] = ps_enabled.lower() != 'false'

        # Plan agent redirect to planning skill
        pa_redirect = get_config_value(content, 'plan_agent_redirect_enabled')
        if pa_redirect:
            config['plan_agent_redirect_enabled'] = pa_redirect.lower() != 'false'

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
# GIT WORKTREE HELPERS
# =============================================================================
def get_main_worktree_path(base_dir: Path) -> Path | None:
    """Get path to main worktree using 'git worktree list --porcelain'.

    The first 'worktree' entry is always the main worktree.

    Args:
        base_dir: Any directory in the git repository

    Returns:
        Path to main worktree, or None if not a git repo or command fails
    """
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(base_dir)
        )
        if result.returncode != 0:
            return None

        # First 'worktree' line is always the main worktree
        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                return Path(line.split(" ", 1)[1])
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def is_main_worktree(base_dir: Path) -> bool:
    """Check if the given directory is the main worktree.

    Args:
        base_dir: Directory to check

    Returns:
        True if base_dir is the main worktree, False otherwise
    """
    main = get_main_worktree_path(base_dir)
    if main is None:
        return False
    try:
        return main.resolve() == base_dir.resolve()
    except OSError:
        return False


def get_worktree_name(base_dir: Path) -> str:
    """Get current worktree name (branch name or folder name).

    Uses 'git branch --show-current' to get the branch name.
    Falls back to folder name if not on a branch.

    Args:
        base_dir: Directory in the worktree

    Returns:
        Branch name or folder name as string
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Fallback to folder name
    return base_dir.resolve().name


def get_worktree_context_path(base_dir: Path) -> Path | None:
    """Get path to worktree-context.md in the main worktree.

    This file stores high-level context shared across all worktrees.

    Args:
        base_dir: Any directory in the git repository

    Returns:
        Path to worktree-context.md in main worktree, or None if not found
    """
    main = get_main_worktree_path(base_dir)
    if main is None:
        return None
    return main / WORKTREE_CONTEXT_FILE


# =============================================================================
# ACTION COUNTER HELPERS
# =============================================================================
def get_action_counter(base_dir: Path) -> int:
    """Get current action counter value."""
    counter_path = base_dir / ACTION_COUNTER_FILE
    try:
        if counter_path.exists():
            return int(counter_path.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0


def save_plan_action_start(base_dir: Path) -> None:
    """Save current action counter as plan mode start point."""
    current = get_action_counter(base_dir)
    start_path = base_dir / PLAN_ACTION_START_FILE
    try:
        start_path.parent.mkdir(parents=True, exist_ok=True)
        start_path.write_text(str(current))
    except IOError:
        pass


def get_plan_action_count(base_dir: Path) -> int:
    """Get number of actions since plan mode started.

    Returns the difference between current action counter and saved start value.
    Returns -1 if no start value exists (plan mode not entered properly).
    """
    start_path = base_dir / PLAN_ACTION_START_FILE
    try:
        if not start_path.exists():
            return -1
        start_value = int(start_path.read_text().strip())
        current = get_action_counter(base_dir)
        return current - start_value
    except (ValueError, IOError):
        return -1


def clear_plan_action_start(base_dir: Path) -> None:
    """Remove plan action start file."""
    start_path = base_dir / PLAN_ACTION_START_FILE
    try:
        if start_path.exists():
            start_path.unlink()
    except IOError:
        pass


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

        # Find header separator (SESSION ENTRIES START comment)
        separator_idx = -1
        for i, line in enumerate(lines):
            if 'SESSION ENTRIES START' in line:
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


def trim_worktree_context(worktree_context_path: Path, max_lines: int) -> None:
    """Trim worktree context file to max_lines, preserving header.

    Similar to trim_session_context, but operates on the shared worktree context
    file in the main worktree. Uses 'WORKTREE ENTRIES START' as separator.

    Args:
        worktree_context_path: Path to worktree-context.md in main worktree
        max_lines: Maximum lines to keep (0 = no trimming)
    """
    if max_lines <= 0:
        return

    if not worktree_context_path or not worktree_context_path.exists():
        return

    try:
        content = worktree_context_path.read_text()
        lines = content.split('\n')

        if len(lines) <= max_lines:
            return

        # Find header separator (WORKTREE ENTRIES START comment)
        separator_idx = -1
        for i, line in enumerate(lines):
            if 'WORKTREE ENTRIES START' in line:
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

        worktree_context_path.write_text('\n'.join(trimmed))
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
# PEBBLE INTEGRATION
# =============================================================================


def get_pebble_context(base_dir: Path) -> str:
    """Get Pebble epic summary and recent activity for context injection.

    Runs pb commands to get:
    - Epic summary with child counts
    - Recent create/close activity

    Returns formatted string or empty if commands fail.
    """
    parts = []

    try:
        # Get epic summary
        result = subprocess.run(
            ["pb", "summary", "--pretty"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## Active Epics")
            parts.append("")
            parts.append(result.stdout.strip())
            parts.append("")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    try:
        # Get recent activity (create and close events)
        result = subprocess.run(
            ["pb", "history", "--type", "create,close", "--pretty"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## Recent Activity")
            parts.append("")
            parts.append(result.stdout.strip())
            parts.append("")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return "\n".join(parts) if parts else ""


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

    # 2. Session context (rolling cross-session context)
    session_context_path = base_dir / SESSION_CONTEXT_FILE
    if session_context_path.exists():
        files_to_inject.append((SESSION_CONTEXT_FILE, session_context_path))

    # 2.5. Worktree context (shared across all worktrees, read from main worktree)
    worktree_context_path = get_worktree_context_path(base_dir)
    if worktree_context_path and worktree_context_path.exists():
        # Trim worktree context before injecting
        wt_config = get_project_config(base_dir)
        wt_max_lines = wt_config.get('worktree_context_max_lines', 200)
        trim_worktree_context(worktree_context_path, wt_max_lines)

        # Use path relative to main worktree for display
        main_worktree = get_main_worktree_path(base_dir)
        if main_worktree:
            rel_path = str(worktree_context_path.relative_to(main_worktree))
            files_to_inject.append((f"[main-worktree]/{rel_path}", worktree_context_path))

    # 3. Active plan file (if set)
    active_plan_file = base_dir / ACTIVE_PLAN_FILE
    if active_plan_file.exists():
        try:
            plan_path = active_plan_file.read_text().strip()
            if plan_path:
                if plan_path.startswith('/'):
                    full_path = Path(plan_path)
                else:
                    full_path = base_dir / plan_path
                if full_path.exists():
                    files_to_inject.append((plan_path, full_path))
        except IOError:
            pass

    # 4. CODE_GUIDE and addons
    code_guide_path = base_dir / ".meridian" / "CODE_GUIDE.md"
    if code_guide_path.exists():
        files_to_inject.append((".meridian/CODE_GUIDE.md", code_guide_path))

    # Get project config for addons and pebble
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

    # 6. API docs index (tells agent which external APIs are documented)
    api_docs_index = base_dir / ".meridian" / "api-docs" / "INDEX.md"
    if api_docs_index.exists():
        try:
            content = api_docs_index.read_text()
            parts.append(f'<file path=".meridian/api-docs/INDEX.md">')
            parts.append(content.rstrip())
            parts.append('</file>')
            parts.append("")
        except IOError:
            parts.append(f'<file path=".meridian/api-docs/INDEX.md" error="Could not read file" />')
            parts.append("")

    # 7. Pebble guide and context (if enabled)
    if project_config.get('pebble_enabled', False):
        pebble_guide_path = base_dir / ".meridian" / "PEBBLE_GUIDE.md"
        if pebble_guide_path.exists():
            try:
                content = pebble_guide_path.read_text()
                parts.append(f'<file path=".meridian/PEBBLE_GUIDE.md">')
                parts.append(content.rstrip())
                parts.append('</file>')
                parts.append("")
            except IOError:
                parts.append(f'<file path=".meridian/PEBBLE_GUIDE.md" error="Could not read file" />')
                parts.append("")

        # Get live Pebble context (epics, recent activity)
        pebble_context = get_pebble_context(base_dir)
        if pebble_context:
            parts.append('<pebble-context>')
            parts.append(pebble_context.rstrip())
            parts.append('</pebble-context>')
            parts.append("")

    # 8. Agent operating manual
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
    parts.append("the current project state.")
    parts.append("")
    parts.append("</injected-project-context>")

    # Trim session context file if over limit
    max_lines = project_config.get('session_context_max_lines', 1000)
    trim_session_context(base_dir, max_lines)

    return "\n".join(parts)


# =============================================================================
# LOOP STATE HELPERS
# =============================================================================

LOOP_STATE_FILE = f"{STATE_DIR}/loop-state"


def is_loop_active(base_dir: Path) -> bool:
    """Check if a work-until loop is currently active."""
    loop_state = base_dir / LOOP_STATE_FILE
    if not loop_state.exists():
        return False
    try:
        content = loop_state.read_text().strip()
        # Check for active: true in the state file
        for line in content.split('\n'):
            if line.strip().startswith('active:'):
                value = line.split(':', 1)[1].strip().lower()
                return value == 'true'
    except IOError:
        pass
    return False


def get_loop_state(base_dir: Path) -> dict | None:
    """Get current loop state if active, None otherwise.

    State file format:
    ```
    active: true
    iteration: 1
    max_iterations: 10
    completion_phrase: "All tests pass"
    started_at: "2026-01-04T12:00:00Z"
    ---
    The prompt text goes here
    ```
    """
    loop_state = base_dir / LOOP_STATE_FILE
    if not loop_state.exists():
        return None
    try:
        content = loop_state.read_text()

        # Split on --- separator
        if '---' in content:
            parts = content.split('---', 1)
            header = parts[0].strip()
            prompt = parts[1].strip() if len(parts) > 1 else ''
        else:
            header = content.strip()
            prompt = ''

        state = {'prompt': prompt}
        for line in header.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"')
                if key == 'active':
                    state['active'] = value.lower() == 'true'
                elif key == 'iteration':
                    state['iteration'] = int(value)
                elif key == 'max_iterations':
                    state['max_iterations'] = int(value)
                elif key == 'completion_phrase':
                    state['completion_phrase'] = value if value and value != 'null' else None
                elif key == 'started_at':
                    state['started_at'] = value
        if state.get('active'):
            return state
    except (IOError, ValueError):
        pass
    return None


def update_loop_iteration(base_dir: Path, new_iteration: int) -> bool:
    """Update the iteration count in the loop state file."""
    loop_state = base_dir / LOOP_STATE_FILE
    if not loop_state.exists():
        return False
    try:
        content = loop_state.read_text()
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('iteration:'):
                lines[i] = f'iteration: {new_iteration}'
                break
        loop_state.write_text('\n'.join(lines))
        return True
    except IOError:
        return False


def clear_loop_state(base_dir: Path) -> bool:
    """Remove the loop state file to end the loop."""
    loop_state = base_dir / LOOP_STATE_FILE
    try:
        if loop_state.exists():
            loop_state.unlink()
        return True
    except IOError:
        return False


# =============================================================================
# STOP PROMPT BUILDER
# =============================================================================

def build_stop_prompt(base_dir: Path, config: dict) -> str:
    """
    Build the stop hook prompt with all sections.

    This is shared between the normal stop hook and the loop stop hook
    to ensure consistency.

    Args:
        base_dir: Project root directory
        config: Project config from get_project_config()

    Returns:
        The stop prompt string
    """
    pebble_enabled = config.get('pebble_enabled', False)
    claude_project_dir = str(base_dir)

    parts = ["[SYSTEM]: Before stopping, complete these checks:\n"]

    # Skip-if-unchanged principle
    parts.append(
        "**SKIP IF UNCHANGED**: If you already ran a check (reviewers, tests, lint, build) this session "
        "and made no significant code changes since, skip re-running it — just state it passed earlier. "
        "Only re-run checks after significant code changes.\n"
    )

    # Implementation review section (lowest priority - at top)
    impl_review = config.get('implementation_review_enabled', True)
    code_review = config.get('code_review_enabled', True)

    if impl_review or code_review:
        parts.append(
            "**IMPLEMENTATION REVIEW**: After finishing a plan, epic, or large multi-file task, run reviewers.\n\n"
            f"First `cd {claude_project_dir}`, then:\n"
        )

        # Build reviewer list based on config
        reviewers = []
        if impl_review:
            reviewers.append("Implementation Reviewer agent")
        if code_review:
            reviewers.append("Code Reviewer agent")

        if pebble_enabled:
            reviewer_list = "\n".join(f"- {r}" for r in reviewers)
            parts.append(
                "**Spawn in parallel** — include `Parent issue: #<id>` in the prompt (the epic/task you were working on):\n"
                f"{reviewer_list}\n"
                "**After reviewers**: If issues created → fix → re-run. Repeat until no issues.\n"
            )
        else:
            reviewer_list = "\n".join(f"{i+1}. {r}" for i, r in enumerate(reviewers))
            parts.append(
                "**Spawn in parallel** (no prompts needed — they read from `.meridian/.state/injected-files`):\n"
                f"{reviewer_list}\n"
                "**After reviewers**: Read `.meridian/implementation-reviews/`. If issues → fix → re-run. Repeat until clean.\n"
            )

    # Pebble reminder if enabled (before session context - higher priority)
    if pebble_enabled:
        parts.append(
            "**PEBBLE (AUDIT TRAIL)**: Every code change needs an issue — this is your audit trail.\n"
            "- **Already-fixed bugs**: If you discovered AND fixed a bug this session, create the issue NOW (issue → already fixed → comment what you did → close). The fix happened, but the record didn't.\n"
            "- **Close** issues you fully completed (with a comment summarizing what was done).\n"
            "- **Create** issues for: bugs found, broken code, missing error handling, problems that need attention.\n"
            "- **Update** existing issues if status changed, scope evolved, or you have new context.\n"
            "- **Comment** on issues you worked on but didn't finish, explaining current state.\n"
        )

    # Session context section
    parts.append(
        "**SESSION CONTEXT**: Append timestamped entry (`YYYY-MM-DD HH:MM`) to "
        f"`{claude_project_dir}/.meridian/session-context.md` with key decisions, discoveries, context worth preserving, "
        "and important user messages (instructions, preferences, constraints — copy verbatim if needed).\n"
    )

    # Worktree context section (only if in a git worktree)
    main_worktree = get_main_worktree_path(base_dir)
    if main_worktree:
        worktree_name = get_worktree_name(base_dir)
        worktree_context_path = main_worktree / WORKTREE_CONTEXT_FILE
        parts.append(
            f"**WORKTREE CONTEXT**: For significant work, append a brief standup-style summary to "
            f"`{worktree_context_path}` (in main worktree). "
            f"Format: `## [{worktree_name}] YYYY-MM-DD - Title`\n"
            "Write 2-3 sentences max: what you worked on and what was achieved. "
            "No technical implementation details — just outcomes. Skip for trivial changes.\n"
        )

    # Memory section
    parts.append(
        "**MEMORY**: Consider if you learned something that future agents need to know.\n"
        "The test: \"If I don't record this, will a future agent make the same mistake — or is the fix already in the code?\"\n"
        "- **Add**: Architectural patterns, data model gotchas, external API limitations, cross-agent coordination patterns.\n"
        "- **Skip**: One-time bug fixes (code handles it), SDK quirks (code works around them), agent behavior rules (use agent-operating-manual.md), module-specific details (use CLAUDE.md).\n"
        "If you have something worth preserving, invoke the `/memory-curator` skill to add it properly.\n"
    )

    # CLAUDE.md section
    parts.append(
        "**CLAUDE.md**: If you created a new module/service directory or made significant architectural changes, "
        "consider creating or updating the CLAUDE.md file in that directory.\n"
        "- Include: setup/test commands, what the module does, how it works, why it's designed this way, gotchas.\n"
        "- Invoke `/claudemd-writer` skill for guidance on writing effective CLAUDE.md files.\n"
    )

    # Human actions section
    parts.append(
        "**HUMAN ACTIONS**: If work requires human actions (external accounts, env vars, integrations), "
        "create doc in `.meridian/human-actions-docs/` with actionable steps.\n"
    )

    # Tests/lint/build section (highest priority - near bottom)
    parts.append(
        "**TESTS/LINT/BUILD**: If work is finished, ensure codebase is clean. Run tests, lint, build. "
        "Fix failures and rerun until passing.\n"
    )

    # Footer
    parts.append(
        "If you have nothing to update and were not working on a plan, your response to this hook must be exactly the same as the message that was blocked. "
        "If you did update something or called implementation-reviewer, resend the same message you sent before you were interrupted by this hook. "
        "Before marking a task as complete, review the 'Definition of Done' section in "
        f"`{claude_project_dir}/.meridian/prompts/agent-operating-manual.md`."
    )

    return "\n".join(parts)

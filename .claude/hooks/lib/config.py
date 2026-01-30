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
PLAN_ACTION_COUNTER_FILE = f"{STATE_DIR}/plan-action-counter"
DOCS_RESEARCHER_FLAG = f"{STATE_DIR}/docs-researcher-active"
EDITS_SINCE_REVIEW_FILE = f"{STATE_DIR}/edits-since-review"
PLAN_MODE_STATE = f"{STATE_DIR}/plan-mode-state"
ACTIVE_PLAN_FILE = f"{STATE_DIR}/active-plan"
ACTIVE_SUBPLAN_FILE = f"{STATE_DIR}/active-subplan"
CURRENT_PLAN_AUTO_FILE = f"{STATE_DIR}/current-plan-auto"
INJECTED_FILES_LOG = f"{STATE_DIR}/injected-files"
RESTART_SIGNAL = f"{STATE_DIR}/restart-signal"


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
        'pre_compaction_sync_enabled': True,
        'pre_compaction_sync_threshold': 150000,
        'auto_compact_off': False,
        'session_context_max_lines': 1000,
        'worktree_context_max_lines': 200,
        'pebble_enabled': False,
        'stop_hook_min_actions': 10,
        'plan_review_min_actions': 20,
        'code_review_enabled': True,
        'docs_researcher_write_required': True,
        'pebble_scaffolder_enabled': True,
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

        # Auto-compact off
        aco = get_config_value(content, 'auto_compact_off')
        if aco:
            config['auto_compact_off'] = aco.lower() == 'true'

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

        # Plan review minimum actions threshold
        plan_min_actions = get_config_value(content, 'plan_review_min_actions')
        if plan_min_actions:
            try:
                config['plan_review_min_actions'] = int(plan_min_actions)
            except ValueError:
                pass

        # Code review
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

    except IOError:
        pass

    return config


def get_required_files(base_dir: Path) -> list[str]:
    """Get list of required context files based on config."""
    config_path = base_dir / REQUIRED_CONTEXT_CONFIG
    if not config_path.exists():
        return [
            ".meridian/SOUL.md",
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
# EDIT COUNTER HELPERS
# =============================================================================
def increment_edits_since(base_dir: Path, counter_file: str) -> None:
    """Increment an edit counter."""
    path = base_dir / counter_file
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        current = 0
        if path.exists():
            try:
                current = int(path.read_text().strip())
            except (ValueError, IOError):
                pass
        path.write_text(str(current + 1))
    except IOError:
        pass


def reset_edits_since(base_dir: Path, counter_file: str) -> None:
    """Reset an edit counter to 0."""
    path = base_dir / counter_file
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("0")
    except IOError:
        pass


def get_edits_since(base_dir: Path, counter_file: str) -> int:
    """Get current edit counter value."""
    path = base_dir / counter_file
    try:
        if path.exists():
            return int(path.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0


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


def get_plan_action_counter(base_dir: Path) -> int:
    """Get current plan action counter value."""
    counter_path = base_dir / PLAN_ACTION_COUNTER_FILE
    try:
        if counter_path.exists():
            return int(counter_path.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0


def increment_plan_action_counter(base_dir: Path) -> None:
    """Increment plan action counter (only called while in plan mode)."""
    counter_path = base_dir / PLAN_ACTION_COUNTER_FILE
    try:
        current = get_plan_action_counter(base_dir)
        counter_path.parent.mkdir(parents=True, exist_ok=True)
        counter_path.write_text(str(current + 1))
    except IOError:
        pass


def clear_plan_action_counter(base_dir: Path) -> None:
    """Reset plan action counter to 0 (called when plan is approved)."""
    counter_path = base_dir / PLAN_ACTION_COUNTER_FILE
    try:
        counter_path.parent.mkdir(parents=True, exist_ok=True)
        counter_path.write_text("0")
    except IOError:
        pass


# =============================================================================
# SESSION CONTEXT HELPERS
# =============================================================================
def trim_session_context(base_dir: Path, max_lines: int) -> None:
    """Trim session context file to max_lines, keeping newest entries.

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

        # Keep newest lines (from end)
        trimmed = lines[-max_lines:]
        context_file.write_text('\n'.join(trimmed))
    except Exception:
        pass


def trim_worktree_context(worktree_context_path: Path, max_lines: int) -> None:
    """Trim worktree context file to max_lines, keeping newest entries.

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

        # Keep newest lines (from end)
        trimmed = lines[-max_lines:]
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
    """Get Pebble context for injection: epics overview, in-progress work, ready issues.

    Runs pb commands to get:
    - Epic summary (open epics, progress, verification counts)
    - Currently in-progress issues
    - Ready issues (unblocked, can be picked up)

    Returns formatted string or empty if commands fail.
    """
    parts = []

    try:
        # Get epic summary (big picture: what epics exist, progress)
        result = subprocess.run(
            ["pb", "summary", "--pretty"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## Epics Overview")
            parts.append("")
            parts.append(result.stdout.strip())
            parts.append("")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    try:
        # Get in-progress issues (what's being worked on now)
        result = subprocess.run(
            ["pb", "list", "--status", "in_progress", "--pretty"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## In Progress")
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

    # Current datetime
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    parts.append(f"**Current datetime:** {now}")
    parts.append("")

    # Uncommitted changes (git diff --stat)
    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## Uncommitted Changes")
            parts.append("```")
            parts.append(result.stdout.strip())
            parts.append("```")
            parts.append("")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Recent commits (user's only, all branches, with branch decoration and relative time)
    try:
        # Get current user's email for filtering
        user_email_result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(base_dir)
        )
        user_email = user_email_result.stdout.strip() if user_email_result.returncode == 0 else None

        cmd = ["git", "log", "--format=%h%d %s (%cr)", "-20", "--all"]
        if user_email:
            cmd.append(f"--author={user_email}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## Recent Commits")
            parts.append("```")
            parts.append(result.stdout.strip())
            parts.append("```")
            parts.append("")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Recent PRs (open)
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--limit", "5"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## Open PRs")
            parts.append("```")
            parts.append(result.stdout.strip())
            parts.append("```")
            parts.append("")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Recent PRs (merged)
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--state", "merged", "--limit", "5"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            parts.append("## Recently Merged PRs")
            parts.append("```")
            parts.append(result.stdout.strip())
            parts.append("```")
            parts.append("")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

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

    # 0.5. SOUL.md (core identity and principles - injected early to set the tone)
    soul_path = base_dir / ".meridian" / "SOUL.md"
    if soul_path.exists():
        files_to_inject.append((".meridian/SOUL.md", soul_path))

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

    # 3.5. Active subplan file (if in an epic)
    active_subplan_file = base_dir / ACTIVE_SUBPLAN_FILE
    if active_subplan_file.exists():
        try:
            subplan_path = active_subplan_file.read_text().strip()
            if subplan_path:
                if subplan_path.startswith('/'):
                    full_path = Path(subplan_path)
                else:
                    full_path = base_dir / subplan_path
                if full_path.exists():
                    files_to_inject.append((subplan_path, full_path))
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

    # 5. Architecture Decision Records index (agent reads individual ADRs when needed)
    adr_index = base_dir / ".meridian" / "adrs" / "INDEX.md"
    if adr_index.exists():
        files_to_inject.append((".meridian/adrs/INDEX.md", adr_index))

    # Inject each file with XML tags (deduplicate by resolved path)
    injected_paths = set()
    for rel_path, full_path in files_to_inject:
        resolved = full_path.resolve()
        if resolved in injected_paths:
            continue
        injected_paths.add(resolved)
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
    parts.append("1. Embody SOUL.md — this defines who you are and how you work")
    parts.append("2. Confirm you have read and understood the memory entries")
    parts.append("3. Confirm you understand any in-progress tasks and their current state")
    parts.append("4. Confirm you will follow the CODE_GUIDE conventions")
    parts.append("5. Confirm you will operate according to the agent-operating-manual")
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
    Build a minimal stop hook prompt.

    Trusts SOUL.md and agent-operating-manual.md for details.
    This is just a checklist trigger, not re-training.

    Args:
        base_dir: Project root directory
        config: Project config from get_project_config()

    Returns:
        The stop prompt string
    """
    from datetime import datetime
    pebble_enabled = config.get('pebble_enabled', False)
    code_review_enabled = config.get('code_review_enabled', True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    parts = [f"**Before stopping** ({now}):\n"]

    # Core checklist - agent knows HOW from SOUL.md and operating manual
    parts.append("**Checklist:**")

    if code_review_enabled:
        edits_since_review = get_edits_since(base_dir, EDITS_SINCE_REVIEW_FILE)
        if edits_since_review > 0:
            parts.append(f"- Code review needed ({edits_since_review} edits since last review)")

    parts.append("- Update `session-context.md` with current state")
    parts.append("- Update `worktree-context.md` if relevant")

    if pebble_enabled:
        parts.append("- Close/update Pebble issues for completed work")

    parts.append("- Run tests/lint/build if you made code changes")
    parts.append("- Consider memory if you learned something reusable")

    # Check for uncommitted changes
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(base_dir)
        )
        if result.returncode == 0 and result.stdout.strip():
            changed_files = len([l for l in result.stdout.strip().split('\n') if l])
            parts.append(f"- Commit {changed_files} uncommitted file{'s' if changed_files != 1 else ''}")
    except Exception:
        pass

    parts.append("")
    parts.append("Skip items you already did this session. Then continue with your stop.")

    return "\n".join(parts)

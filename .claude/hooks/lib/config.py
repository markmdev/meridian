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
WORKSPACE_FILE = ".meridian/WORKSPACE.md"

# System state files (ephemeral, cleaned up on session start)
STATE_DIR = ".meridian/.state"
PLAN_REVIEW_FLAG = f"{STATE_DIR}/plan-review-blocked"
CONTEXT_ACK_FLAG = f"{STATE_DIR}/context-acknowledgment-pending"
ACTION_COUNTER_FILE = f"{STATE_DIR}/action-counter"
PLAN_ACTION_COUNTER_FILE = f"{STATE_DIR}/plan-action-counter"
PLAN_MODE_STATE = f"{STATE_DIR}/plan-mode-state"
ACTIVE_PLAN_FILE = f"{STATE_DIR}/active-plan"
ACTIVE_SUBPLAN_FILE = f"{STATE_DIR}/active-subplan"
CURRENT_PLAN_AUTO_FILE = f"{STATE_DIR}/current-plan-auto"
INJECTED_FILES_LOG = f"{STATE_DIR}/injected-files"
HOOK_LOGS_DIR = f"{STATE_DIR}/hook_logs"


# =============================================================================
# HOOK OUTPUT LOGGING
# =============================================================================
def log_hook_output(base_dir: Path, hook_name: str, output: dict) -> None:
    """Write hook output to stdout and save a readable markdown copy to hook_logs/.

    Logs are overwritten each time the hook fires, keeping only the latest output.
    """
    import json
    from datetime import datetime

    output_str = json.dumps(output)

    # Log readable markdown version
    log_dir = base_dir / HOOK_LOGS_DIR
    try:
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hook_specific = output.get("hookSpecificOutput", {})
        event_name = hook_specific.get("hookEventName", output.get("decision", "unknown"))
        decision = hook_specific.get("permissionDecision", output.get("decision", ""))

        lines = [f"# {hook_name}", f"**Time:** {timestamp}  ", f"**Event:** {event_name}  "]
        if decision:
            lines.append(f"**Decision:** {decision}  ")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Extract the human-readable content
        content = (
            hook_specific.get("additionalContext")
            or hook_specific.get("permissionDecisionReason")
            or output.get("reason")
            or ""
        )
        if content:
            lines.append(content)
        else:
            lines.append("*(no content)*")

        (log_dir / f"{hook_name}.md").write_text("\n".join(lines) + "\n")
    except (IOError, OSError):
        pass

    # Print to stdout for Claude Code
    print(output_str)


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


# =============================================================================
# CONFIG FILE HELPERS
# =============================================================================
def get_project_config(base_dir: Path) -> dict:
    """Read project config and return as dict with defaults."""
    config = {
        'project_type': 'standard',
        'plan_review_enabled': True,
        'pebble_enabled': False,
        'stop_hook_min_actions': 10,
        'plan_review_min_actions': 20,
        'code_review_enabled': True,
        'pebble_scaffolder_enabled': True,
        'file_tree_max_files_per_dir': 2000,
        'file_tree_ignored_extensions': [],
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

        # Pebble scaffolder auto-invocation
        ps_enabled = get_config_value(content, 'pebble_scaffolder_enabled')
        if ps_enabled:
            config['pebble_scaffolder_enabled'] = ps_enabled.lower() != 'false'

        # Project structure tree filtering
        max_files = get_config_value(content, 'file_tree_max_files_per_dir')
        if max_files:
            try:
                parsed = int(max_files)
                if parsed > 0:
                    config['file_tree_max_files_per_dir'] = parsed
            except ValueError:
                pass

        ignored_exts = parse_yaml_list(content, 'file_tree_ignored_extensions')
        if ignored_exts:
            config['file_tree_ignored_extensions'] = ignored_exts

    except IOError:
        pass

    return config


def get_additional_review_files(base_dir: Path, absolute: bool = False) -> list[str]:
    """Get list of additional files for implementation/plan review.

    Args:
        base_dir: Base directory of the project
        absolute: If True, return absolute paths; otherwise relative paths
    """
    files = [".meridian/CODE_GUIDE.md", ".meridian/WORKSPACE.md"]
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
# ACTION COUNTER HELPERS
# =============================================================================
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
# FILE TREE HELPERS
# =============================================================================

_IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", ".next", "dist", "build",
    ".venv", "venv", "coverage", ".cache", ".turbo", "target", "vendor",
    "bin", ".gradle", ".idea", "obj", ".eggs", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".nuxt", ".output", ".svelte-kit",
    ".parcel-cache", ".vite",
}

_IGNORED_FILE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".bmp", ".ico",
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ".mp3", ".wav", ".aiff", ".m4a", ".mp4", ".mov", ".avi", ".webm",
    ".zip", ".gz", ".tar", ".tgz", ".7z", ".dmg", ".pdf",
}


def _normalize_extension(value: str) -> str:
    """Normalize extension values from config to lowercase .ext form."""
    value = value.strip().lower()
    if not value:
        return ""
    if not value.startswith("."):
        value = f".{value}"
    return value


def _build_file_tree(base_dir: Path) -> str:
    """Build a TOON-style compact file tree. Directories as nested keys, files inline."""
    lines = []
    project_config = get_project_config(base_dir)
    max_files_per_dir = project_config.get('file_tree_max_files_per_dir', 2000)
    ignored_extensions = set(_IGNORED_FILE_EXTENSIONS)
    for ext in project_config.get('file_tree_ignored_extensions', []):
        normalized = _normalize_extension(ext)
        if normalized:
            ignored_extensions.add(normalized)

    def _walk(dir_path: Path, indent: int):
        try:
            entries = sorted(dir_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return

        dirs = []
        files = []
        filtered_count = 0
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in _IGNORED_DIRS:
                    continue
                dirs.append(entry)
            else:
                if entry.name == '.DS_Store':
                    continue
                ext = Path(entry.name).suffix.lower()
                if ext in ignored_extensions:
                    filtered_count += 1
                    continue
                files.append(entry.name)

        prefix = "  " * indent
        shown_files = files
        truncated_count = 0
        if max_files_per_dir and len(files) > max_files_per_dir:
            shown_files = files[:max_files_per_dir]
            truncated_count = len(files) - max_files_per_dir

        if shown_files:
            suffix_parts = []
            if filtered_count:
                suffix_parts.append(f"+{filtered_count} filtered")
            if truncated_count:
                suffix_parts.append(f"+{truncated_count} truncated")
            suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""
            lines.append(f"{prefix}[{len(shown_files)}{suffix}]: {','.join(shown_files)}")
        elif filtered_count:
            lines.append(f"{prefix}[0 shown (+{filtered_count} filtered)]")

        for d in dirs:
            lines.append(f"{prefix}{d.name}/")
            _walk(d, indent + 1)

    _walk(base_dir, 0)
    return '\n'.join(lines)


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
# FRONTMATTER-BASED DOC SCANNING
# =============================================================================
def extract_frontmatter(file_path: Path) -> tuple[str, list[str]]:
    """Extract summary and read_when from YAML frontmatter.

    Returns (summary, read_when_list). Both empty if no valid frontmatter.
    """
    try:
        content = file_path.read_text()
    except IOError:
        return "", []

    if not content.startswith("---"):
        return "", []

    end_idx = content.find("\n---", 3)
    if end_idx == -1:
        return "", []

    frontmatter = content[3:end_idx].strip()
    summary = ""
    read_when: list[str] = []
    collecting_read_when = False

    for line in frontmatter.split("\n"):
        stripped = line.strip()

        if stripped.startswith("summary:"):
            summary = stripped[len("summary:"):].strip().strip("'\"")
            collecting_read_when = False

        elif stripped.startswith("read_when:"):
            collecting_read_when = True
            inline = stripped[len("read_when:"):].strip()
            if inline.startswith("[") and inline.endswith("]"):
                try:
                    import json
                    parsed = json.loads(inline.replace("'", '"'))
                    if isinstance(parsed, list):
                        read_when.extend(str(x).strip() for x in parsed if x)
                except (json.JSONDecodeError, ValueError):
                    pass

        elif collecting_read_when and stripped.startswith("- "):
            hint = stripped[2:].strip()
            if hint:
                read_when.append(hint)
        elif collecting_read_when and stripped:
            collecting_read_when = False

    return summary, read_when


def scan_docs_directory(dir_path: Path, base_dir: Path) -> str:
    """Scan a directory for .md files with frontmatter, return formatted listing.

    Skips INDEX.md and README.md files. Returns empty string if no docs found.
    """
    if not dir_path.exists():
        return ""

    skip_names = {"INDEX.md", "README.md"}
    entries = []

    for md_file in sorted(dir_path.rglob("*.md")):
        if md_file.name in skip_names:
            continue
        rel_path = md_file.relative_to(base_dir)
        summary, read_when = extract_frontmatter(md_file)
        if summary:
            entry = f"- **{rel_path}** — {summary}"
            if read_when:
                entry += f"\n  Read when: {'; '.join(read_when)}"
            entries.append(entry)
        else:
            entries.append(f"- **{rel_path}** — *(missing summary frontmatter)*")

    return "\n".join(entries)


# =============================================================================
# CONTEXT INJECTION HELPERS
# =============================================================================
def build_injected_context(base_dir: Path) -> str:
    """Build the full injected context string with XML-wrapped file contents.

    Args:
        base_dir: Base directory of the project

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

    # Recent PRs (open, with authors)
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--limit", "5",
             "--json", "number,title,author,headRefName",
             "--template", '{{range .}}#{{.number}} {{.title}} ({{.author.login}}) [{{.headRefName}}]\n{{end}}'],
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

    # Recent PRs (merged, with authors)
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--state", "merged", "--limit", "5",
             "--json", "number,title,author,mergedAt",
             "--template", '{{range .}}#{{.number}} {{.title}} ({{.author.login}}) merged {{timeago .mergedAt}}\n{{end}}'],
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

    # Build ordered file list: (rel_path, full_path, description)
    # Description is optional — appears above the file to explain its purpose.
    files_to_inject = []

    # User-provided docs (injected first, before everything else)
    config_path = base_dir / REQUIRED_CONTEXT_CONFIG
    if config_path.exists():
        content = config_path.read_text()
        user_docs = parse_yaml_list(content, 'user_provided_docs')
        for doc_path in user_docs:
            full_path = base_dir / doc_path
            if full_path.exists():
                files_to_inject.append((doc_path, full_path, ""))

    # Active plan file (if set)
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
                    files_to_inject.append((plan_path, full_path, "Active implementation plan. Follow this plan during implementation."))
        except IOError:
            pass

    # Active subplan file (if in an epic)
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
                    files_to_inject.append((subplan_path, full_path, "Active subplan for current epic phase."))
        except IOError:
            pass

    # CODE_GUIDE and addons
    code_guide_path = base_dir / ".meridian" / "CODE_GUIDE.md"
    if code_guide_path.exists():
        files_to_inject.append((".meridian/CODE_GUIDE.md", code_guide_path, "Project coding conventions. Follow these standards in all code you write."))

    # Get project config for addons and pebble
    project_config = get_project_config(base_dir)

    if project_config['project_type'] == 'hackathon':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_HACKATHON.md"
        if addon_path.exists():
            files_to_inject.append((".meridian/CODE_GUIDE_ADDON_HACKATHON.md", addon_path, "Hackathon-mode coding standards overlay."))
    elif project_config['project_type'] == 'production':
        addon_path = base_dir / ".meridian" / "CODE_GUIDE_ADDON_PRODUCTION.md"
        if addon_path.exists():
            files_to_inject.append((".meridian/CODE_GUIDE_ADDON_PRODUCTION.md", addon_path, "Production-mode coding standards overlay."))

    # Inject each file with XML tags (deduplicate by resolved path)
    injected_paths = set()
    for rel_path, full_path, desc in files_to_inject:
        resolved = full_path.resolve()
        if resolved in injected_paths:
            continue
        injected_paths.add(resolved)
        try:
            content = full_path.read_text()
            if desc:
                parts.append(f"**{desc}**")
            parts.append(f'<file path="{rel_path}">')
            parts.append(content.rstrip())
            parts.append('</file>')
            parts.append("")
        except IOError:
            parts.append(f'<file path="{rel_path}" error="Could not read file" />')
            parts.append("")

    # Documentation directories — scan for frontmatter summaries
    doc_dirs = [
        (".meridian/adrs", "Architecture Decision Records. Read the relevant ADR before making related decisions."),
        (".meridian/api-docs", "External API docs. Read the relevant doc before using any listed API."),
        (".meridian/docs", "Project documentation. Read relevant docs when your task matches a hint below."),
    ]
    any_docs = False
    for dir_rel, header in doc_dirs:
        listing = scan_docs_directory(base_dir / dir_rel, base_dir)
        if listing:
            any_docs = True
            parts.append(f"**{header}**")
            parts.append(f"<docs-index dir=\"{dir_rel}\">")
            parts.append(listing)
            parts.append("</docs-index>")
            parts.append("")
    if any_docs:
        parts.append("When your task matches a \"Read when\" hint above, read that doc before coding. When you make changes that affect a documented topic, update the doc. When you discover something worth preserving — a decision, a gotcha, a new integration — create a new doc in `.meridian/docs/` with frontmatter (`summary`, `read_when`). Documentation is part of the work, not an afterthought.")
        parts.append("")

    # Pebble guide and context (if enabled)
    if project_config.get('pebble_enabled', False):
        pebble_guide_path = base_dir / ".meridian" / "PEBBLE_GUIDE.md"
        if pebble_guide_path.exists():
            try:
                content = pebble_guide_path.read_text()
                parts.append("**Pebble issue tracker reference. Use these commands to manage issues.**")
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

    # Agent operating manual (authoritative — follow at all times)
    manual_path = base_dir / ".meridian" / "prompts" / "agent-operating-manual.md"
    if manual_path.exists():
        try:
            content = manual_path.read_text()
            parts.append("**Agent operating manual. This is authoritative — follow these procedures at all times.**")
            parts.append(f'<file path=".meridian/prompts/agent-operating-manual.md">')
            parts.append(content.rstrip())
            parts.append('</file>')
            parts.append("")
        except IOError:
            parts.append(f'<file path=".meridian/prompts/agent-operating-manual.md" error="Could not read file" />')
            parts.append("")

    # SOUL.md (agent identity and principles)
    soul_path = base_dir / ".meridian" / "SOUL.md"
    if soul_path.exists():
        try:
            content = soul_path.read_text()
            parts.append("**Agent identity and principles. This defines who you are and how you work.**")
            parts.append(f'<file path=".meridian/SOUL.md">')
            parts.append(content.rstrip())
            parts.append('</file>')
            parts.append("")
        except IOError:
            pass

    # Workspace (agent's living knowledge base — last for highest attention)
    workspace_path = base_dir / WORKSPACE_FILE
    if workspace_path.exists():
        try:
            content = workspace_path.read_text()
            parts.append("**Your persistent knowledge base. Update this throughout the session with decisions, discoveries, and lessons.**")
            parts.append(f'<file path="{WORKSPACE_FILE}">')
            parts.append(content.rstrip())
            parts.append('</file>')
            parts.append("")
        except IOError:
            pass

    # Active work-until loop (if any)
    loop_state_path = base_dir / f"{STATE_DIR}/loop-state"
    if loop_state_path.exists():
        try:
            loop_content = loop_state_path.read_text().strip()
            if 'active: true' in loop_content:
                parts.append('<work-until-loop>')
                parts.append("**A work-until loop is active.** You are in an iterative work loop.")
                parts.append("Read `.meridian/.state/loop-state` for your task and current iteration.")
                parts.append("See `.meridian/prompts/work-until-loop.md` for how the loop works.")
                parts.append('</work-until-loop>')
                parts.append("")
        except IOError:
            pass

    # Footer with acknowledgment request
    parts.append("You have received the complete project context above.")
    parts.append("This information is CRITICAL for working correctly on this project.")
    parts.append("")
    parts.append("Before doing anything else:")
    parts.append("1. Embody SOUL.md — this defines who you are and how you work")
    parts.append("2. Confirm you understand any in-progress tasks and their current state")
    parts.append("3. Confirm you will follow the CODE_GUIDE conventions")
    parts.append("4. Confirm you will operate according to the agent-operating-manual")
    parts.append("")
    parts.append("Acknowledge this context by briefly stating what you understand about")
    parts.append("the current project state.")
    parts.append("")
    parts.append("</injected-project-context>")

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
        parts.append("- Run **code-reviewer** and **code-health-reviewer** in parallel if you made significant code changes")

    if pebble_enabled:
        parts.append("- Close/update Pebble issues for completed work")

    parts.append("- Run tests/lint/build if you made code changes")
    parts.append("- Consider updating CLAUDE.md if you made architectural changes")

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

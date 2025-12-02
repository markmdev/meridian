"""
Shared configuration helpers for Meridian hooks.
"""

from pathlib import Path


# =============================================================================
# PATH CONSTANTS
# =============================================================================
MERIDIAN_CONFIG = ".meridian/config.yaml"
REQUIRED_CONTEXT_CONFIG = ".meridian/required-context-files.yaml"
PENDING_READS_FILE = ".meridian/.pending-context-reads"
PRE_COMPACTION_FLAG = ".meridian/.pre-compaction-synced"
PLAN_REVIEW_FLAG = ".meridian/.plan-review-blocked"


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


def get_additional_review_files(base_dir: Path) -> list[str]:
    """Get list of additional files for implementation/plan review."""
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

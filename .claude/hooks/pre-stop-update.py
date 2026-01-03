#!/usr/bin/env python3
"""
Stop Hook - Pre-Stop Update

Prompts agent to update task files, memory, and optionally run implementation review.
"""

import json
import subprocess
import sys
import os
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import get_project_config, get_additional_review_files, parse_yaml_list, MERIDIAN_CONFIG, ACTION_COUNTER_FILE

def get_action_count(base_dir: Path) -> int:
    """Read current action counter value."""
    counter_path = base_dir / ACTION_COUNTER_FILE
    try:
        if counter_path.exists():
            return int(counter_path.read_text().strip())
    except (ValueError, IOError):
        pass
    return 0


# Default folders to ignore for CLAUDE.md review
DEFAULT_IGNORED_FOLDERS = [
    ".git",
    ".meridian",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
]


def get_changed_files(base_dir: Path) -> list[str]:
    """Get list of changed files using git (staged + unstaged + untracked)."""
    try:
        # Get modified/staged files
        # -uall shows individual files in untracked directories (not just dir name)
        result = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return []

        files = []
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
            # Format: XY filename or XY "filename with spaces"
            # Skip first 3 chars (status + space)
            filename = line[3:].strip().strip('"')
            # Handle renames (old -> new)
            if ' -> ' in filename:
                filename = filename.split(' -> ')[1]
            files.append(filename)

        return files
    except Exception:
        return []


def get_claudemd_ignored_folders(base_dir: Path) -> list[str]:
    """Get list of folders to ignore for CLAUDE.md review from config."""
    config_path = base_dir / MERIDIAN_CONFIG
    if not config_path.exists():
        return DEFAULT_IGNORED_FOLDERS

    try:
        content = config_path.read_text()
        custom = parse_yaml_list(content, 'claudemd_ignored_folders')
        if custom:
            return custom
    except Exception:
        pass

    return DEFAULT_IGNORED_FOLDERS


def should_ignore_folder(folder: str, ignored_folders: list[str]) -> bool:
    """Check if a folder path should be ignored."""
    parts = Path(folder).parts
    for part in parts:
        if part in ignored_folders:
            return True
    return False


def is_root_level_doc_or_config(filepath: str) -> bool:
    """Check if file is a root-level documentation or config file (not code)."""
    root_docs = {
        'README.md', 'CHANGELOG.md', 'LICENSE', 'LICENSE.md', 'CONTRIBUTING.md',
        'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
        'tsconfig.json', 'pyproject.toml', 'requirements.txt', 'Makefile',
    }
    filename = Path(filepath).name
    # Root-level docs and configs
    if filepath in root_docs:
        return True
    # Dotfiles at root (config files like .gitignore, .eslintrc, etc.)
    if Path(filepath).parent == Path('.') and filename.startswith('.'):
        return True
    return False


def get_claudemd_review_info(base_dir: Path) -> dict | None:
    """
    Analyze changed files and return CLAUDE.md review info.

    Returns dict with:
      - folders: list of modified folder paths
      - files_by_folder: dict mapping folder to list of changed files
      - claudemd_files: list of (path, exists) tuples for all CLAUDE.md on path

    Returns None if no review needed.
    """
    changed_files = get_changed_files(base_dir)
    if not changed_files:
        return None

    ignored_folders = get_claudemd_ignored_folders(base_dir)

    # Filter out ignored folders and root-level docs
    relevant_files = []
    for f in changed_files:
        folder = str(Path(f).parent)
        if folder == '.':
            # Root level file - skip docs/config, include code
            if not is_root_level_doc_or_config(f):
                relevant_files.append(f)
        elif not should_ignore_folder(folder, ignored_folders):
            relevant_files.append(f)

    if not relevant_files:
        return None

    # Group files by folder
    files_by_folder: dict[str, list[str]] = {}
    for f in relevant_files:
        folder = str(Path(f).parent)
        if folder == '.':
            folder = './'
        if folder not in files_by_folder:
            files_by_folder[folder] = []
        files_by_folder[folder].append(f)

    # For each folder, find all CLAUDE.md files on the path
    claudemd_paths = set()
    claudemd_paths.add('./CLAUDE.md')  # Always include root

    for folder in files_by_folder.keys():
        if folder == './':
            continue

        # Walk up the path
        current = Path(folder)
        while str(current) != '.':
            claudemd_paths.add(str(current / 'CLAUDE.md'))
            current = current.parent

    # Check which CLAUDE.md files exist
    claudemd_files = []
    for path in sorted(claudemd_paths, key=lambda p: p.count('/')):
        exists = (base_dir / path).exists()
        claudemd_files.append((path, exists))

    return {
        'folders': sorted(files_by_folder.keys()),
        'files_by_folder': files_by_folder,
        'claudemd_files': claudemd_files,
    }


def format_claudemd_section(info: dict) -> str:
    """Format the CLAUDE.md review section for the hook message."""
    lines = ["**CLAUDE.md Review Required**\n"]

    # Decision criteria
    lines.append("**Create/update CLAUDE.md when:**")
    lines.append("- New module or significant directory added")
    lines.append("- Public API changed")
    lines.append("- New patterns established or architectural decisions made")
    lines.append("")
    lines.append("**Skip CLAUDE.md for:**")
    lines.append("- Bug fixes without behavior change")
    lines.append("- Refactoring that preserves API")
    lines.append("- Internal implementation details, test files, small utilities")
    lines.append("")

    # List modified folders
    lines.append(f"Modified folders: {', '.join(info['folders'])}\n")

    # List changed files
    lines.append("Files changed:")
    for folder, files in sorted(info['files_by_folder'].items()):
        for f in files:
            lines.append(f"- {f}")
    lines.append("")

    # List CLAUDE.md files to review
    lines.append("CLAUDE.md files on modified paths:")
    for path, exists in info['claudemd_files']:
        status = "(exists)" if exists else "(missing)"
        lines.append(f"- {path} {status}")
    lines.append("")

    lines.append("Use `claudemd-writer` skill for guidance on content.\n")

    return '\n'.join(lines)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    if input_data.get("hook_event_name") != "Stop":
        sys.exit(0)

    # If already prompted, allow stop
    if input_data.get("stop_hook_active"):
        sys.exit(0)

    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not claude_project_dir:
        sys.exit(0)  # Can't operate without project dir
    base_dir = Path(claude_project_dir)

    config = get_project_config(base_dir)

    # Skip stop hook if too few actions since last user input
    min_actions = config.get('stop_hook_min_actions', 10)
    if min_actions > 0:
        action_count = get_action_count(base_dir)
        if action_count < min_actions:
            sys.exit(0)  # Allow stop without prompts

    files_list = '\n'.join(get_additional_review_files(base_dir, absolute=True))

    # Get CLAUDE.md review info
    claudemd_info = get_claudemd_review_info(base_dir)

    # Build message with sections ordered by priority (lower = more important)
    beads_enabled = config.get('beads_enabled', False)
    beads_str = str(beads_enabled).lower()

    reason = "[SYSTEM]: Before stopping, complete these checks:\n\n"

    # Implementation review section (lowest priority - at top)
    if config['implementation_review_enabled']:
        reason += (
            "**IMPLEMENTATION REVIEW**: If you were working on implementing a plan, run reviewers.\n\n"
            "**Spawn in parallel:**\n"
            "1. **Implementation Reviewer** — verifies every plan item was implemented\n"
            "2. **Code Reviewer** — line-by-line review of all changes\n\n"
            "**1. Implementation Reviewer**:\n"
            "```\n"
            "Plan file: [EXACT PLAN PATH, e.g., /path/.claude/plans/my-plan.md]\n"
            f"beads_enabled: {beads_str}\n"
            "```\n\n"
            "**2. Code Reviewer**:\n"
            "```\n"
            "Git comparison: [SPECIFY: main...HEAD | HEAD | --staged]\n"
            "Plan file: [EXACT PLAN PATH]\n"
            f"beads_enabled: {beads_str}\n"
            "```\n\n"
            "Git state: feature branch → `main...HEAD`, uncommitted → `HEAD`, staged only → `--staged`\n\n"
        )

        if beads_enabled:
            reason += (
                "**After reviewers**: If issues created → fix → re-run. Repeat until no issues.\n\n"
            )
        else:
            reason += (
                "**After reviewers**: Read `.meridian/implementation-reviews/`. If issues → fix → re-run. Repeat until clean.\n\n"
            )

    # Memory section
    reason += (
        "**MEMORY** — Ask: \"If I delete this entry, will the agent make the same mistake again — or is the fix already in the code?\"\n"
        "Add: Architectural patterns, data model gotchas, external API limitations, cross-agent coordination.\n"
        "Skip: One-time fixes (code handles it), SDK quirks, module-specific details (use CLAUDE.md).\n\n"
    )

    # Session context section
    reason += (
        "**SESSION CONTEXT**: Append timestamped entry (`YYYY-MM-DD HH:MM`) to "
        f"`{claude_project_dir}/.meridian/session-context.md` with key decisions, discoveries, and context worth preserving.\n\n"
    )

    # CLAUDE.md section
    reason += "**CLAUDE.md FILES**: "
    if claudemd_info:
        reason += format_claudemd_section(claudemd_info)
    else:
        reason += "No code changes detected that require CLAUDE.md review.\n\n"

    # Beads reminder if enabled
    if beads_enabled:
        reason += (
            "**BEADS**: Update issues (close completed, update status, create discovered work). "
            "See `.meridian/BEADS_GUIDE.md`. Always use `--json` flag.\n\n"
        )

    # Human actions section
    reason += (
        "**HUMAN ACTIONS**: If work requires human actions (external accounts, env vars, integrations), "
        "create doc in `.meridian/human-actions-docs/` with actionable steps.\n\n"
    )

    # Tests/lint/build section (highest priority - near bottom)
    reason += (
        "**TESTS/LINT/BUILD**: If work is finished, you MUST ensure codebase is clean. Run tests, lint, build. "
        "Fix failures and rerun until passing. If already passed and no changes since, state they're clean.\n\n"
    )

    # Footer
    reason += (
        "If you have nothing to update and were not working on a plan, your response to this hook must be exactly the same as the message that was blocked. "
        "If you did update something or called implementation-reviewer, resend the same message you sent before you were interrupted by this hook. "
        "Before marking a task as complete, review the 'Definition of Done' section in "
        f"`{claude_project_dir}/.meridian/prompts/agent-operating-manual.md`."
    )

    output = {
        "decision": "block",
        "reason": reason,
        "systemMessage": "[Meridian] Before stopping, Claude is updating session context, backlog, and memory, verifying tests/lint/build, and running implementation review if needed."
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

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
from config import get_project_config, get_additional_review_files, parse_yaml_list, MERIDIAN_CONFIG

REQUIRED_SCORE = 9

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
        result = subprocess.run(
            ["git", "status", "--porcelain"],
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
    files_list = '\n'.join(get_additional_review_files(base_dir, absolute=True))

    # Get CLAUDE.md review info
    claudemd_info = get_claudemd_review_info(base_dir)

    # Base message
    reason = (
        "[SYSTEM]: Before stopping, check whether you need to update "
        f"`{claude_project_dir}/.meridian/task-backlog.yaml`, "
        f"`{claude_project_dir}/.meridian/session-context.md`, "
        f"or `{claude_project_dir}/.meridian/memory.jsonl` using the `memory-curator` skill, as well as any other "
        "documents that should reflect what you accomplished during this session (for example design documents, API specifications, etc.).\n"
        "If nothing significant happened, you may skip the update.\n\n"
        "**MEMORY** — Before adding to memory, ask: \"If I delete this entry, will the agent make the same mistake again — or is the fix already in the code?\"\n"
        "**Add to memory**: Architectural patterns affecting future features, data model gotchas not obvious from code, external API limitations, cross-agent coordination patterns.\n"
        "**DON'T add**: One-time bug fixes (code is fixed), SDK quirks (code handles it), agent behavior rules (belong in operating manual), module-specific details (belong in CLAUDE.md).\n\n"
        "**SESSION CONTEXT**: Append a timestamped entry (format: `YYYY-MM-DD HH:MM`) to "
        f"`{claude_project_dir}/.meridian/session-context.md` with: key decisions made, important discoveries, "
        "complex problems solved, and context that would be hard to rediscover. This is a rolling file — oldest entries "
        "are automatically trimmed. If nothing significant happened, you may skip the update.\n\n"
        "**CLAUDE.md FILES**: "
    )

    # Add dynamic CLAUDE.md section if there are relevant changes
    if claudemd_info:
        reason += format_claudemd_section(claudemd_info)
    else:
        reason += "No code changes detected that require CLAUDE.md review.\n\n"

    # Beads reminder if enabled
    if config.get('beads_enabled', False):
        reason += (
            "**BEADS**: Update Beads issues to reflect work done this session (close completed, update status, create discovered work).\n\n"
        )

    reason += (
        "**HUMAN ACTIONS**: If this work requires human actions (e.g., create external service accounts, add environment variables, "
        "configure third-party integrations), create a doc in `.meridian/human-actions-docs/` with concise actionable steps. "
        "Assume the user knows the tools; focus on what to do, not why.\n\n"
        "If you consider the current work \"finished\" or close to completion, you MUST ensure the codebase is clean before "
        "stopping: run the project's tests, lint, and build commands. If any of these fail, you must fix the issues and rerun "
        "them until they pass before stopping. If they already passed recently and no further changes were made, you may state "
        "that they are already clean and stop.\n\n"
    )

    # Implementation review section (conditional)
    if config['implementation_review_enabled']:
        reason += (
            "**IMPLEMENTATION REVIEW**: If you were working on implementing a plan, you MUST run all reviewers.\n\n"
            "**MULTI-REVIEWER STRATEGY** — spawn ALL of these in parallel:\n"
            "1. **Phase reviewers**: One `implementation-reviewer` per plan phase (scope: files/folders for that phase)\n"
            "2. **Integration reviewer**: One `implementation-reviewer` with `review_type: integration` (verifies modules wired together)\n"
            "3. **Completeness reviewer**: One `implementation-reviewer` with `review_type: completeness` (verifies every plan item implemented)\n"
            "4. **Code reviewer**: One `code-reviewer` (line-by-line review of all changes)\n\n"
            "- Call **ALL reviewers in parallel** (single message with multiple Task tool calls)\n"
            "- You may spawn **more than 3 agents** for review — this is an exception to the soft limit\n\n"
            "**Review output**: Each reviewer writes to `.meridian/implementation-reviews/` and returns only the file path.\n\n"
            "---\n\n"
            "**EXACT PROMPTS** (fill in bracketed values):\n\n"
            "**1. Phase Implementation Reviewer** (one per phase):\n"
            "```\n"
            "Review Scope: [FILES/FOLDERS FOR THIS PHASE]\n"
            "Plan file: [EXACT PLAN PATH, e.g., /path/.claude/plans/my-plan.md]\n"
            "Plan section: [STEPS X-Y]\n"
            "Review Type: phase\n"
            "Verify: Each step executed correctly, no deviations, quality standards met\n"
            f"Additional files to read:\n{files_list}\n"
            "```\n\n"
            "**2. Integration Reviewer**:\n"
            "```\n"
            "Review Scope: Full codebase entry points\n"
            "Plan file: [EXACT PLAN PATH]\n"
            "Plan section: Integration phase\n"
            "Review Type: integration\n"
            "Verify: All modules wired together, entry points defined, data flow complete, no orphaned code\n"
            f"Additional files to read:\n{files_list}\n"
            "```\n\n"
            "**3. Completeness Reviewer**:\n"
            "```\n"
            "Review Scope: Entire plan vs implementation\n"
            "Plan file: [EXACT PLAN PATH]\n"
            "Review Type: completeness\n"
            "Verify: Every plan item implemented, no missing features, obvious implications covered (integrations need env vars, APIs need error handling)\n"
            f"Additional files to read:\n{files_list}\n"
            "```\n\n"
            "**4. Code Reviewer**:\n"
            "```\n"
            "Git comparison: [SPECIFY: main...HEAD | HEAD | --staged]\n"
            "Plan file: [EXACT PLAN PATH] (for context on intent)\n"
            "Review Type: code\n"
            "Verify: Every changed line reviewed line-by-line, bugs, security, performance, CODE_GUIDE compliance\n"
            f"Additional files to read:\n{files_list}\n"
            "```\n\n"
            "**IMPORTANT**: Determine git state before calling code-reviewer:\n"
            "- Feature branch: use `main...HEAD` (fetch main first if stale)\n"
            "- Uncommitted changes: use `HEAD`\n"
            "- Staged only: use `--staged`\n\n"
            "---\n\n"
            "**After all reviewers complete**:\n"
            "1. Read all review files from `.meridian/implementation-reviews/`\n"
            "2. Aggregate findings across all reviews\n"
            f"3. ALL reviewers must achieve score {REQUIRED_SCORE}+\n\n"
            f"**ITERATION REQUIRED**: If any score is below {REQUIRED_SCORE}:\n"
            "1. Review each finding with the user using AskUserQuestion\n"
            "2. For findings the user wants to fix: make the fixes in the codebase\n"
            "3. For findings the user declines: note as `[USER_DECLINED: <finding> - Reason: <reason>]`\n"
            "4. Re-run the failing reviewer(s)\n"
            f"5. Repeat until all scores reach {REQUIRED_SCORE}+\n\n"
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

#!/usr/bin/env python3
"""
Claude Init Hook - Session Start

Outputs instructions to read required context files and creates pending reads list.
"""

import os
import sys
import json
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))
from config import (
    get_required_files,
    read_file,
    cleanup_flag,
    PENDING_READS_FILE,
    PRE_COMPACTION_FLAG,
)


def main() -> int:
    claude_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    base_dir = Path(claude_project_dir)

    # Get required files from config
    required_files = get_required_files(base_dir)

    # Build file list for prompt
    file_bullets = "\n".join(f"   - `{claude_project_dir}/{f}`" for f in required_files)

    # Load agent prompt
    prompt_path = base_dir / ".meridian" / "prompts" / "agent-operating-manual.md"
    prompt_content = read_file(prompt_path)
    if not prompt_content.endswith("\n"):
        prompt_content += "\n"

    # Build output
    output = f"""{prompt_content}[SYSTEM]:

NEXT STEPS:
1. Read the following files before starting your work:
{file_bullets}

2. Read all additional relevant documents listed in `{claude_project_dir}/.meridian/relevant-docs.md`.

3. Review all uncompleted tasks in `{claude_project_dir}/.meridian/tasks/` — you MUST read ALL files within each task folder.

4. Ask the user what they would like to work on.

IMPORTANT:
Claude must always complete all steps listed in this system message before doing anything else. Even if the user sends any message after this system message, Claude must first perform everything described above and only then handle the user's request.
"""

    print(output, end="")

    # Create pending reads file with absolute paths
    pending_reads_path = base_dir / PENDING_READS_FILE
    absolute_files = [f"{claude_project_dir}/{f}" for f in required_files]
    try:
        pending_reads_path.parent.mkdir(parents=True, exist_ok=True)
        pending_reads_path.write_text(json.dumps(absolute_files))
    except Exception:
        pass

    # Clean up flags
    cleanup_flag(base_dir, PRE_COMPACTION_FLAG)

    return 0


if __name__ == "__main__":
    sys.exit(main())

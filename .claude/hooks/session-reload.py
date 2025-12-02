#!/usr/bin/env python3
"""
Session Reload Hook - After Compaction

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
    file_bullets = "\n".join(f"- `{claude_project_dir}/{f}`" for f in required_files)

    # Build reload context message
    output = f"""<reload_context_system_message>
This conversation was recently compacted. Read these files before continuing:

{file_bullets}

Check `{claude_project_dir}/.meridian/task-backlog.yaml` for uncompleted tasks. For each:
1. Read the context file at `{claude_project_dir}/.meridian/tasks/TASK-###/TASK-###-context.md`
2. Read the plan file referenced in the backlog's `plan_path` field

The context file contains the previous agent's progress, decisions, and next steps.

After reviewing, check `{claude_project_dir}/.meridian/relevant-docs.md` for additional required docs.
</reload_context_system_message>"""

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

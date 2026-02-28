#!/bin/bash
# Resolve the Meridian state directory for the current project.
# State lives in ~/.meridian/state/<project-hash>/ for worktree isolation.
# Usage: state_dir=$(.claude/hooks/scripts/state-dir.sh)
python3 -c "
import hashlib
from pathlib import Path
d = Path('${CLAUDE_PROJECT_DIR:-.}').resolve()
h = hashlib.md5(str(d).encode()).hexdigest()[:12]
print(Path.home() / '.meridian' / 'state' / h)
"

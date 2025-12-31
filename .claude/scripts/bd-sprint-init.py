#!/usr/bin/env python3
"""
Beads Sprint Init Script

Appends the Beads Sprint Workflow template to session-context.md.
Called by the /bd-sprint slash command.
"""

import sys
from pathlib import Path

TEMPLATE = '''
<!-- BEADS SPRINT WORKFLOW - DO NOT DELETE UNTIL COMPLETE -->
<!-- ⚠️ SESSION ENTRIES GO ABOVE THIS WORKFLOW SECTION, NOT BELOW IT ⚠️ -->

## Beads Sprint Workflow

**Scope**: [FILL IN: epic, issue, or work description]

**Issues/Tasks** (in dependency order):
- [ ] [FILL IN: issue-id - description]
- [ ] [FILL IN: issue-id - description]

**Done When**: [FILL IN: completion criteria]

---

### Per-Issue Workflow

**CRITICAL**: Follow ALL phases in order. Do NOT skip phases or jump ahead.

For each issue:

#### 1. PLANNING ⚠️ MANDATORY - DO NOT SKIP

**You MUST create a plan before writing any code.**

- No exceptions — even if the issue is "detailed" or "simple"
- Even if the Beads issue description is comprehensive
- Even if you think you know what to do
- The plan ensures reviewers can verify your work

1. Use `/planning` skill to create comprehensive plan
2. Save plan to `.claude/plans/`
3. Run `plan-reviewer` agent with this prompt:
   ```
   Plan file: [EXACT PLAN PATH]
   Additional files to read:
   - .meridian/CODE_GUIDE.md
   - .meridian/memory.jsonl
   - .meridian/session-context.md
   ```
4. Iterate until score >= 9

#### 2. IMPLEMENTATION

1. Execute the approved plan step by step
2. Update Beads status: `bd update <id> --status in_progress`
3. **If you discover bugs or new work**: Create Beads issue immediately with `bd create "..." --deps discovered-from:<current-id>`

#### 3. REVIEW

**IMPORTANT**: When spawning reviewer agents, DO NOT listen to their streaming output. Either:
- Use blocking Task calls and only read the final result, OR
- Read the review files from `.meridian/implementation-reviews/` after completion

Listening to streaming output causes massive context pollution.

Spawn ALL reviewers in parallel (single message with multiple Task tool calls):

**Phase Reviewers** (one per plan phase):
```
Review Scope: [FILES/FOLDERS FOR THIS PHASE]
Plan file: [EXACT PLAN PATH]
Plan section: [STEPS X-Y]
Review Type: phase
Verify: Each step executed correctly, no deviations, quality standards met
Additional files to read:
- .meridian/CODE_GUIDE.md
- .meridian/memory.jsonl
- .meridian/session-context.md
```

**Integration Reviewer**:
```
Review Scope: Full codebase entry points
Plan file: [EXACT PLAN PATH]
Plan section: Integration phase
Review Type: integration
Verify: All modules wired together, entry points defined, data flow complete, no orphaned code
Additional files to read:
- .meridian/CODE_GUIDE.md
- .meridian/memory.jsonl
- .meridian/session-context.md
```

**Completeness Reviewer**:
```
Review Scope: Entire plan vs implementation
Plan file: [EXACT PLAN PATH]
Review Type: completeness
Verify: Every plan item implemented, no missing features, obvious implications covered
Additional files to read:
- .meridian/CODE_GUIDE.md
- .meridian/memory.jsonl
- .meridian/session-context.md
```

**Code Reviewer**:
```
Git comparison: [main...HEAD | HEAD | --staged]
Plan file: [EXACT PLAN PATH]
Review Type: code
Verify: Line-by-line review, bugs, security, performance, CODE_GUIDE compliance
Additional files to read:
- .meridian/CODE_GUIDE.md
- .meridian/memory.jsonl
- .meridian/session-context.md
```

**Git state for code-reviewer**:
- Feature branch: `main...HEAD`
- Uncommitted changes: `HEAD`
- Staged only: `--staged`

**After reviewers complete**:
1. Read all review files from `.meridian/implementation-reviews/`
2. ALL must score >= 9
3. If below 9: fix issues, re-run failing reviewers

#### 4. VERIFY

Run project verification commands:
- Typecheck (e.g., `pnpm typecheck`)
- Lint (e.g., `pnpm lint`)
- Build (e.g., `pnpm build`)

Fix any failures before proceeding.

#### 5. COMPLETE ISSUE

**CLAUDE.md Review**:
- Create/update when: new module, API change, new patterns established
- Skip when: bug fixes, refactoring, internal implementation details
- Use `claudemd-writer` skill for guidance

**Memory** (use `memory-curator` skill):
- Critical test: "If I delete this entry, will agent make same mistake again?"
- Add: architectural patterns, data model gotchas, API limitations, cross-agent patterns
- Don't add: one-time fixes, SDK quirks, agent behavior rules, module-specific details

**Session Context**:
- Append timestamped entry (YYYY-MM-DD HH:MM) to `.meridian/session-context.md`
- **IMPORTANT**: Add entries ABOVE this workflow section, not below it
- Include: key decisions, important discoveries, complex problems solved

**Close Issue**:
- `bd close <id> --reason "..."`
- Update checkbox above to `[x]`

#### 6. NEXT ISSUE

Continue to next unchecked issue. Repeat from step 1.

---

### On Problems

- Document discovery in session context
- Create blocking issue: `bd create "..." --deps discovered-from:<current-id>`
- Continue workflow

### On Context Compaction

This section survives at bottom of session-context.md. After compaction:
1. Re-read this workflow
2. Check progress (checkboxes above)
3. Continue from current issue/phase

### Workflow Complete

When all checkboxes checked and completion criteria met:
1. Close epic if applicable: `bd close <epic-id> --reason "All child issues complete"`
2. Final session context entry summarizing the work
3. Run `/bd-sprint-stop` to remove this workflow section

<!-- END BEADS SPRINT WORKFLOW -->
'''


def main():
    # Derive project root from script location: .claude/scripts/ -> project root
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent.parent  # .claude/scripts -> .claude -> project root
    session_context = project_dir / ".meridian" / "session-context.md"

    if not session_context.exists():
        print(f"Error: {session_context} does not exist", file=sys.stderr)
        sys.exit(1)

    # Check if workflow already exists
    content = session_context.read_text()
    if "<!-- BEADS SPRINT WORKFLOW" in content:
        print("Beads Sprint Workflow already exists in session-context.md")
        print("Run /bd-sprint-stop first to remove it, or continue the existing workflow.")
        sys.exit(0)

    # Append template
    with open(session_context, "a") as f:
        f.write(TEMPLATE)

    print("Beads Sprint Workflow template added to session-context.md\n")
    print("=" * 60)
    print("WORKFLOW TEMPLATE (now in session-context.md):")
    print("=" * 60)
    print(TEMPLATE)


if __name__ == "__main__":
    main()

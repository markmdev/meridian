# Meridian Setup Guide

## Add to your global CLAUDE.md

Copy the following into `~/.claude/CLAUDE.md`:

```markdown
## Documentation

Be proactive about documentation. When you encounter any of the following, create or update a doc in `.meridian/docs/`:

- A significant architectural decision or trade-off
- A new integration, API, or external dependency
- A debugging session that revealed non-obvious behavior
- A complex workflow or process that future sessions need to understand
- A new feature with design rationale worth preserving
- A gotcha, pitfall, or sharp edge discovered during implementation

Every doc must have YAML frontmatter:

    ---
    summary: One-line description of what this doc covers
    read_when:
      - keyword or phrase matching task context
      - another keyword
    ---

Use kebab-case filenames: `auth-flow.md`, `stripe-webhook-setup.md`, `postgres-migration-gotchas.md`.

Don't ask permission to create docs. Just write them when the knowledge is worth preserving.
```

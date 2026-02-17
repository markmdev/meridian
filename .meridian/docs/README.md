# Project Documentation

General-purpose docs for the project. Create docs here about anything worth preserving — architecture overviews, integration guides, debugging playbooks, onboarding notes.

Docs in this directory are automatically scanned and their summaries injected into the agent's context at session start. The agent sees *what* each doc covers and *when* to read it — and reads the full doc on demand.

## Frontmatter Format

Every doc needs YAML frontmatter:

```yaml
---
summary: Brief description of what this doc covers
read_when:
  - keyword or phrase matching task context
  - another keyword
---
```

- **summary**: One-line description. Injected into context so the agent knows what the doc contains.
- **read_when**: List of keywords/phrases. When the agent's task matches a hint, it reads the full doc before working.

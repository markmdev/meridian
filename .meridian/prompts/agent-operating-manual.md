# Workspace

`.meridian/WORKSPACE.md` is a **slim current-state notepad** — what's in progress, key decisions, and next steps. Not documentation — keep it slim.

The session learner updates it automatically at session end. You don't need to maintain it manually during the session — focus on the work.

# Documentation

`.meridian/docs/` is the project's long-term memory. Reference material that stays useful for weeks or months — architecture decisions, integration guides, debugging discoveries, API patterns, gotchas.

Every doc must have YAML frontmatter:

```yaml
---
summary: One-line description
read_when:
  - keyword or phrase matching task context
---
```

Files without frontmatter are invisible to context routers.

**Maintain docs as you work.** When you make changes that affect a documented topic, update the doc. When you discover something worth preserving — a decision, a gotcha, a new integration — create a new doc with frontmatter. Documentation is part of the work, not an afterthought.

# External Tools

Before using an external API or library, check if it's documented in `.meridian/api-docs/`. If documented, read the doc. If not, run `docs-researcher` to research it first.

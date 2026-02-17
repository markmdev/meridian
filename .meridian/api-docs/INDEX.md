# External Tools & APIs

Knowledge docs for external tools, APIs, and libraries. Each doc contains everything needed to work with that tool: overview, API operations, limits, gotchas.

**Rule: You MUST NOT write code using an external tool unless it's documented here.** If you need a tool that isn't listed, research it first using the `docs-researcher` agent.

## Frontmatter Format

Every API doc needs YAML frontmatter so it appears in the agent's context:

```yaml
---
summary: Stripe API integration — payments, subscriptions, webhooks
read_when:
  - payments
  - billing
  - subscriptions
---
```

## Documentation

<!-- Add API doc files to this directory with frontmatter -->

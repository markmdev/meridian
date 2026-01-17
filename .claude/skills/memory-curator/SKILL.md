---
name: memory-curator
description: Manage architectural decisions and insights in memory.jsonl. Use when you need to document strategic decisions, lessons learned, or architectural insights.
---

# Memory Curator

`memory.jsonl` stores durable engineering knowledge that can't be inferred from code. Never edit the file manually — use the scripts below.

## The Critical Test

Before adding ANY memory entry, ask:

> "If I delete this entry, will the agent make the same mistake again — or is the fix already in the code?"

**If the fix is in the code, don't add to memory.** The code IS the memory.

## SHOULD Add to Memory

1. **Architectural patterns** that affect how future features are built
   - Cross-cutting decisions (auth strategy, error handling approach, state management)
   - Patterns that must be followed consistently across modules

2. **Data model gotchas** not obvious from code
   - "Plaid sandbox returns per-share cost_basis, production returns total"
   - "Artemis stores cost_basis per-share, multiply by quantity for total"

3. **External API limitations** requiring workarounds
   - "Polygon.io doesn't support hourly bars on this plan tier"
   - "CloudFlare Workers has no filesystem - use build-time bundling"

4. **Cross-agent coordination patterns**
   - How agents pass context to each other
   - What data format specialized agents expect

## SHOULD NOT Add to Memory

1. **One-time bug fixes** → The fix is in the code
   - ❌ "Fixed Hermes returning strings instead of numbers" → Code now does parseFloat()
   - ❌ "Fixed double-counting bug in portfolio calculation" → Code is fixed

2. **SDK/library quirks** → Once code handles it, done
   - ❌ "AI SDK useChat id prop doesn't transmit to server" → Code passes it in body
   - ❌ "Drizzle sql<Date> returns strings" → Code wraps in new Date()

3. **Agent behavior rules** → Belong in operating manual
   - ❌ "Never commit without asking" → Put in agent-operating-manual.md
   - ❌ "Never skip plan steps" → Put in agent-operating-manual.md

4. **Module-specific implementation details** → Belong in CLAUDE.md
   - ❌ "This service uses connection pooling" → Document in module's CLAUDE.md

## Examples

**Good:**

- "Sequential agent pattern: tool-using agent first (mode:'generate'), then structured output agent receives results via promptVariables. Required because generateObject() doesn't support tools."
- "Portfolio validation must calculate ALL requirements before checking sufficiency. Two-pass approach: first calculate costs, then validate. Otherwise shows $0 transfer needed when insufficient."
- "LLM agents ignore validation tool errors unless prompt explicitly says what to do when valid=false. Must include iteration pattern with fix-and-retry loop."

**Poor** (don't create):
- "Fixed the parseFloat bug in price service" → Code is fixed
- "Hermes API returns strings not numbers" → Code handles it
- "Used React Query for data fetching" → Obvious, no rationale

## Workflow

```bash
python3 .claude/skills/memory-curator/scripts/add_memory_entry.py \
  --summary "<see Summary Format below>" \
  --tags architecture,api,lessons-learned \
  --links "TASK-090 services/backend-api/src/stripe/stripe-service.ts"
```
The script auto-detects project root by walking up to find `.claude/` and `.meridian/` directories.
Note: if `python3` is failing, try using `python` instead.

**The script will:**

* Compute the next sequential ID (`mem-0001`, `mem-0002`, …)
* Add a UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`)
* Append a single JSON object as one line to `.meridian/memory.jsonl`
* Echo the written entry for confirmation

### Edit an existing entry

```bash
python3 .claude/skills/memory-curator/scripts/edit_memory_entry.py \
  --id mem-0042 \
  --summary "<new summary>" \
  --tags architecture,api \
  --links "TASK-090 docs/design.md"
```
- Provide at least one field to change (`--summary`, `--tags`, `--links`).  
- Tags/links flags replace the lists entirely; include the full set you want to keep.

### Delete an entry

```bash
python3 .claude/skills/memory-curator/scripts/delete_memory_entry.py \
  --id mem-0042
```
- Only delete when clearly obsolete. No undo.

## Field Guidelines

**Summary:** 2-3 sentences max. If longer, it's a design doc — link to it instead.

**Tags:** Few broad tags. Examples: `architecture`, `lessons-learned`, `pattern`, `decision`, `tradeoff`

**Links:** Task IDs, file paths, or design docs. Single quoted string: `--links "TASK-091 path/to/file.ts"`
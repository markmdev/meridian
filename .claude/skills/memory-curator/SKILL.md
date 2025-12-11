---
name: memory-curator
description: Manage architectural decisions and insights in memory.jsonl. Use when you need to document strategic decisions, lessons learned, fixed problems, or architectural insights.
---
<memory_curator>
# Memory Curator Skill

`memory.jsonl` is an audit trail of durable engineering knowledge.
- **Never** write to the file manually. Always use the `add_memory_entry.py` script.

---

## When to Use (Triage Test — all three are quick yes/no)
Create a memory entry if at least one is true:

1) Is this an important architectural decision or pattern that will be useful for future reference? Will this decision meaningfully affect how we build other features?  
2) Is this a problem that is worth remembering and avoiding in the future?
3) If you never will work on this task again, will this insight be useful for future reference?

If none of the above is true, do not create an entry.

### Good Examples
- "Switched from Prisma to Drizzle for type-safe queries. Prisma's generated client caused 3s cold starts in serverless; Drizzle reduced to 200ms. Migration pattern in TASK-045."
- "Auth tokens must be validated server-side even for internal APIs. TASK-023 security audit found client-side checks were bypassable."
- "Rate limiting middleware must be first in chain. Discovered after production incident where auth middleware consumed rate limit tokens."

### Poor Examples (don't create these)
- "Fixed the bug in UserService" — too vague, no reusable insight
- "Used React Query for data fetching" — obvious choice, no decision rationale
- "Implemented TASK-067" — task summary belongs in task files, not memory

---

## Workflow

Always use the helper script and never edit the file by hand.

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
- Only delete when an entry is clearly obsolete or incorrect.  
- The script rewrites the file without that entry; there is no undo.

---

## Summary Format (consistent & skimmable)

Write `--summary` as concise paragraph with maximum 2-3 sentences. If it doesn't fit, it's probably a design doc, not a memory entry—link to that doc and keep the summary short.

---

## Tags

Prefer a few broad tags over many hyper‑specific ones.

Examples: `architecture`, `lessons-learned`, `problem-solved`, `pattern`, `decision`, `tradeoff`, `deprecation`, `migration`

---

## Links (make future retrieval easy)

Use `--links` for **TASK IDs, critical file paths, or design docs**. Examples:

```
--links "TASK-091 services/web/app/(auth)/route.ts docs/design-docs/authentication.md"
```

It should be a single string with quotes around it.
</memory_curator>
---
name: error-audit
description: Audit code for silent error swallowing, fallbacks to degraded alternatives, backwards compatibility shims, and UI that fails to show errors to the user. Finds and fixes all occurrences in the specified scope.
---

# Error Audit

The core principle: **every error belongs to the user**. Not to a catch block, not to a console, not to a null return. Scan the specified code, fix every violation, report what changed.

## Step 0: Understand the app's error mechanisms

Before fixing anything, identify how this app surfaces errors to users — toast notifications, error banners, error boundaries, returned error states, alert dialogs, inline messages. Use these patterns exclusively. Don't invent a new one.

## Anti-patterns to find and fix

**Silent error swallowing — backend/logic layer:**
- Empty catch blocks: `catch(e) {}`
- Log-and-continue: `catch(e) { console.error(e) }` with execution proceeding normally
- `.catch(() => {})` on promises
- Functions returning `null`, `undefined`, or empty defaults on failure instead of throwing

**Silent error swallowing — UI layer:**
- Data fetching catches an error and returns null/empty → component renders blank with no explanation
- Error boundaries that catch but show nothing (or a generic "something went wrong" with no recovery path)
- `try/catch` in a loader or server action that swallows the error and returns partial/empty data
- Async operations where the UI has no error state at all — success renders fine, failure renders identical to loading or empty

**Fallbacks to degraded alternatives:**
- Catch → silently switch to a worse model, API, or service
- Catch → return cached or stale data without telling the user
- Catch → offline/degraded mode with no visible indication

**Backwards compatibility shims:**
- `if (legacyFormat)` or `if (oldVersion)` branches
- Deprecated fields still being populated alongside new ones
- Old code paths running in parallel with new ones

**Config defaults that hide misconfiguration:**
- `process.env.X || 'fallback'` for required values — missing required config is a startup crash, not a default
- Optional environment variables that should be required

**Optional chaining hiding missing required data:**
- `user?.profile?.name ?? 'Guest'` when profile must always exist — the absence is a bug, not an edge case to handle silently

## Fix principles

- Throw or re-throw rather than catch-and-continue
- In the UI: every error path must render something visible — use the app's established error display mechanism
- Required config missing at startup → log a clear message and exit
- Delete fallback branches — don't comment them out
- When unsure if a fallback was intentional, flag it in your report rather than guessing

## Report

After fixing, summarize by file: what was found, what the fix was. Be specific — file paths and the pattern removed.

---
name: error-audit
description: Audit code for silent error swallowing, fallbacks to degraded alternatives, backwards compatibility shims, and other patterns that hide failures from users. Finds and fixes all occurrences in the specified scope.
---

# Error Audit

The core principle: **errors belong to the user, not to a catch block**. Scan the specified code, fix every violation, report what changed.

## Anti-patterns to find and fix

**Silent error swallowing** — caught but not surfaced:
- Empty catch blocks: `catch(e) {}`
- Log-and-continue: `catch(e) { console.error(e) }` with execution continuing normally
- `.catch(() => {})` on promises
- Functions returning `null`, `undefined`, or empty defaults on failure instead of throwing

**Fallbacks to degraded alternatives** — failure silently switches to something worse:
- Catch → use a worse model, API, or service
- Catch → return cached or stale data without telling the user
- Catch → offline/degraded mode with no visible error

**Backwards compatibility shims** — old code kept "just in case":
- `if (legacyFormat)` or `if (oldVersion)` branches
- Deprecated fields still being populated alongside new ones
- Old code paths running in parallel with new ones

**Config defaults that hide misconfiguration**:
- `process.env.X || 'fallback'` for required values — missing config is a startup crash, not a default
- Optional environment variables that should be required

**Optional chaining hiding missing required data**:
- `user?.profile?.name ?? 'Guest'` when profile must always exist — the absence is a bug, not a case to handle

## Process

1. Identify the scope from the user's request — whole app, a module, a specific file or page
2. Read all relevant files thoroughly
3. Find every instance of the anti-patterns above
4. Fix each one: propagate the error, throw, or surface it to the user via the app's error mechanism (toast, error boundary, returned error state, process.exit, etc.)
5. Delete fallback branches — don't comment them out
6. Report all changes

## Fix principles

- Throw or re-throw rather than catch-and-continue
- Required config missing at startup → log a clear message and exit
- Use whatever the app's established error display mechanism is — don't invent a new one
- When unsure if a fallback was intentional, surface it in your report rather than guessing

## Report

After fixing, summarize by file: what was found, what the fix was. Be specific — file paths and the pattern that was removed.

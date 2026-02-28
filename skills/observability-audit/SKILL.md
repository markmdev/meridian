---
name: observability-audit
description: Audit code for observability gaps — debug logs left in, errors caught without being logged, missing context on log entries, untracked slow operations. Uses the app's existing observability tooling exclusively.
---

# Observability Audit

Code that works locally but is impossible to debug in production. This skill finds and fixes observability gaps using whatever tools the app already has.

## Step 0: Research existing observability tooling

Before anything else, explore the codebase to understand what's already in use:
- Error tracking: Sentry, Bugsnag, Rollbar, or similar?
- Logging: structured logger (Pino, Winston, Bunyan), cloud provider SDK, custom wrapper?
- APM / metrics: Datadog, New Relic, OpenTelemetry?
- Analytics: PostHog, Segment, Amplitude?
- Any custom `logger` or `telemetry` utilities?

Read how they're configured and how they're used in existing code. All fixes must use these — never introduce a new observability dependency or pattern.

## What to look for

**Debug artifacts left in production code:**
- `console.log`, `console.debug`, `console.info` that aren't part of the established logging pattern
- Temporary logging added during debugging and never removed
- Commented-out log statements

**Errors that disappear:**
- `catch(e)` that propagates or re-throws without logging first — the error reaches the user but leaves no trace for debugging
- Errors logged with no context: `logger.error(e)` alone, with no info about what operation failed, what inputs were involved, or what the user was doing
- Errors tracked to the error tracker but without relevant metadata (user ID, request ID, relevant state)

**Missing context on log entries:**
- Logs that say what happened but not enough to reproduce it (no entity IDs, no relevant parameters)
- No correlation/request ID on logs in request-handling code
- Log entries that can't be connected to a specific user or session when that would be needed for debugging

**Untracked slow or critical operations:**
- External API calls with no timing logged on failure or when slow
- Database queries with no observability when they're critical path
- Background jobs or queues with no start/complete/fail tracking

## Process

1. Research existing tooling (Step 0) — do not skip this
2. Identify the scope from the user's request
3. Find every instance of the anti-patterns above
4. Fix using the existing tooling and patterns
5. Remove debug artifacts, add context to thin logs, add tracking where missing
6. Report changes

## Fix principles

- Every caught error should be logged with enough context to reproduce the problem
- Use the existing logger/tracker — never introduce a second one
- Debug `console.log` goes away entirely — no conversion to structured log, just deleted
- Log context should include: what operation, what failed, relevant IDs (user, entity, request)
- Don't add logging to every function — focus on boundaries (external calls, queue handlers, critical paths)

## Report

Summarize by file: what was removed, what was added or improved, what context was missing and is now included.

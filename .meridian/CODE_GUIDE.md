# Code Guide

Universal principles for writing maintainable code. Stack-specific details should live in project CLAUDE.md files.

## Type Safety

Type safety is non-negotiable. The compiler is your first line of defense.

- Write as if strict mode is enabled. Type errors are build blockers.
- Never use `any` — use `unknown` with type guards instead
- Reuse types from libraries (`@types/*`, built-in exports) — never recreate types a library already exports
- Be explicit at boundaries (function params, return types, API types, public interfaces). Let TypeScript infer internally.
- Use discriminated unions for state: `{ status: 'loading' } | { status: 'success', data: T } | { status: 'error', error: E }`
- Validate external data (HTTP, files, user input) with schema validation (Zod, etc.) at boundaries

## Error Handling

Errors belong to the user, not to a catch block.

- Fail explicitly — no silent fallbacks (`data || {}`, empty catch blocks)
- Every caught exception must propagate, crash, or be shown to the user
- No silent degradation — never switch to a worse model, stale cache, or degraded mode without telling the user
- No backwards compatibility shims unless explicitly requested — delete old code paths
- Required config has no defaults — missing required config is a startup crash, not a fallback
- Actionable messages with context: "User 123 not found in database" not "Not found"

## Security

Never compromise on security fundamentals.

- No credentials in code, config, or prompts — use environment variables
- Auth tokens in httpOnly cookies — never in localStorage or sessionStorage
- Sanitize all user-supplied content before rendering
- Validate and verify webhook signatures
- Tenant isolation enforced at the database layer — never rely on application-level filtering alone

## Reliability

Systems must handle failure gracefully and visibly.

- Timeouts on every external call — network, database, APIs
- Idempotent operations — safe to retry without unintended side effects
- Transactions for consistency — multi-step writes must be atomic
- Failed async work must be observable and recoverable — no silent job failures

## Observability

If you can't see it, you can't debug it.

- Structured logging with consistent fields — never ad-hoc string concatenation
- Include enough context to reproduce issues: who, what, where
- Never log passwords, tokens, PII, or secrets
- Every error path must leave a trace — caught exceptions that vanish are bugs

## Code Organization

- Group by feature/domain (`billing/`, `users/`), not technical layer (`controllers/`, `services/`)
- Consistent structure — similar things should look similar across the codebase
- Flat over nested — 2-3 directory levels is usually enough

## Testing

- Fast unit tests for pure logic, integration tests at boundaries, E2E for critical paths only
- Tests must be deterministic — no flaky tests
- Test behavior, not implementation

## Frontend

- Server by default — fetch data and render on server when possible
- Handle all states: every async operation has loading, success, and error states

## Backend

- Validate config at startup — exit on invalid configuration, don't fall back to defaults for required values
- Separate long-running work from request handlers
- Bound all retries — never retry indefinitely

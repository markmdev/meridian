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

- Fail explicitly — no silent fallbacks (`data || {}`, empty catch blocks)
- Actionable messages with context: "User 123 not found in database" not "Not found"
- Use a consistent error shape `{ code, message, details }` so callers can handle programmatically

## Code Organization

- Group by feature/domain (`billing/`, `users/`), not technical layer (`controllers/`, `services/`)
- Consistent structure — similar things should look similar across the codebase
- Flat over nested — 2-3 directory levels is usually enough

## Breaking Changes

- Extend rather than modify existing interfaces when possible
- Deprecate before removing — give consumers time to migrate
- Version APIs when breaking changes are necessary

## Logging

- Structured format: JSON with consistent fields (level, timestamp, message, context)
- Include context: request IDs, user IDs, operation, relevant entity IDs
- Never log passwords, tokens, PII, or secrets

## Testing

- Fast unit tests for pure logic, integration tests at boundaries, E2E for critical paths only
- Tests must be deterministic — no flaky tests
- Test behavior, not implementation

## Frontend

- Server by default — fetch data and render on server when possible
- Handle all states: every async operation has loading, success, and error states

## Backend

- Transactions for consistency — multi-step writes should be atomic
- Idempotent operations — safe to retry without unintended side effects
- Timeouts everywhere — network calls, database queries, external APIs

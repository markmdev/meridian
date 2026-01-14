# Code Guide

Universal principles for writing maintainable code. Stack-specific details should live in project CLAUDE.md files.

## Type Safety

Type safety is non-negotiable. The compiler is your first line of defense.

**Compiler strictness:**
- Write as if `strict`, `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes` are enabled
- Type errors are build blockers — never merge code with type errors
- Never use `@ts-ignore` or `@ts-expect-error` to silence errors — fix the underlying issue

**No `any`:**
- `any` disables type checking and defeats the purpose of TypeScript
- If you think you need `any`, you're likely missing a type import or fighting the type system
- Use `unknown` for truly unknown data, then narrow with type guards
- If a library is untyped, add types or find a typed alternative

**Reuse types from libraries:**
- Always use official `@types/*` packages or built-in types from libraries
- Never recreate types that a library already exports — import them
- Search node_modules for existing types before writing custom ones
- If a function returns a library type, use that type, don't create a lookalike

**Be explicit at boundaries:**
- Function parameters and return types should be explicit
- API request/response types should be explicit
- Props and public interfaces should be explicit
- Let TypeScript infer types for local variables and internal code

**Type narrowing:**
- Use type guards to narrow `unknown` or union types
- Prefer discriminated unions for state: `{ status: 'loading' } | { status: 'success', data: T } | { status: 'error', error: E }`
- Avoid type assertions (`as`) — they bypass the compiler. If you must use them, you're probably missing a type guard.

**Runtime validation:**
- External data (HTTP, files, user input) has no type guarantees at runtime
- Use schema validation (Zod, etc.) at boundaries to get both runtime checks and type inference
- Trust internal data — don't re-validate what you've already validated

## Naming

- **Be descriptive**: `getUserById` not `getUser`, `isValidEmail` not `check`
- **Be consistent**: Pick conventions and stick to them across the codebase
- **Avoid abbreviations**: `customer` not `cust`, `transaction` not `txn` (unless domain-standard)
- **Match the domain**: Use terms from the business domain, not generic programming terms
- **Boolean names**: Should read as yes/no questions — `isActive`, `hasPermission`, `canEdit`

## Functions & Methods

- **Single responsibility**: One function does one thing
- **Reasonable size**: If you can't see the whole function on one screen, consider splitting
- **Early returns**: Prefer guard clauses over deeply nested conditionals
- **Minimize parameters**: More than 3-4 suggests the function does too much or needs an options object
- **Pure when possible**: Functions without side effects are easier to test and reason about
- **Avoid boolean parameters**: `createUser(true, false)` is unreadable — use options objects or separate functions

## Error Handling

- **Fail explicitly**: Don't hide errors with silent fallbacks (`data || {}`, empty catch blocks). Problems should surface early.
- **Actionable messages**: "User 123 not found in database" not "Not found"
- **Include context**: What operation failed? What were the inputs? What should the caller do?
- **Typed errors**: Use a consistent error shape `{ code, message, details }` so callers can handle programmatically
- **Don't catch and ignore**: If you catch an exception, handle it meaningfully or rethrow

## Comments & Documentation

- **Explain why, not what**: Code shows what. Comments explain non-obvious decisions, tradeoffs, or constraints.
- **Keep current**: Stale comments are worse than no comments — delete or update
- **Document public APIs**: Function purpose, parameters, return values, edge cases, errors thrown
- **Skip the obvious**: `// increment counter` above `counter++` adds noise

## Code Organization

- **Group by feature/domain**: `billing/`, `users/` not `controllers/`, `services/`, `utils/`
- **High cohesion**: Related code lives together
- **Low coupling**: Modules interact through clear interfaces, not internal knowledge
- **Consistent structure**: Similar things should look similar across the codebase
- **Flat over nested**: Avoid deep directory hierarchies — 2-3 levels is usually enough
- **Index exports**: Use barrel files for public API, import from domain-level, not deep paths

## Constants & Configuration

- **No magic numbers**: `const MAX_RETRIES = 3` not `if (attempts > 3)`
- **No magic strings**: `const STATUS_ACTIVE = 'active'` or use enums
- **Centralize config**: Environment-specific values in one place, validated at startup
- **Fail fast**: Missing or invalid config should crash immediately, not cause subtle bugs later

## Breaking Changes

- **Avoid when possible**: Extend rather than modify existing interfaces
- **Deprecate first**: Warn before removing — give consumers time to migrate
- **Version APIs**: When breaking changes are necessary, version the interface
- **Document migration**: If callers need to change, tell them exactly what to do

## Logging

- **Structured format**: JSON with consistent fields (level, timestamp, message, context)
- **Appropriate levels**: ERROR for failures needing attention, WARN for concerning but handled issues, INFO for significant events, DEBUG for troubleshooting
- **Include context**: Request IDs, user IDs, operation being performed, relevant entity IDs
- **No sensitive data**: Never log passwords, tokens, PII, full credit card numbers, or secrets
- **Log at boundaries**: Incoming requests, outgoing calls, important state changes

## Testing

- **Fast unit tests**: For pure logic, edge cases, and complex algorithms
- **Integration tests at boundaries**: HTTP handlers, database operations, external API calls
- **E2E for critical paths only**: Login, checkout, core user journeys — expensive to maintain
- **Deterministic**: No flaky tests. If it fails intermittently, fix it or delete it.
- **Test behavior, not implementation**: Tests shouldn't break when you refactor internals

## Security Essentials

- **Secrets in environment**: Never in code, config files, or logs
- **Validate all input**: Assume external data is malicious until validated
- **Principle of least privilege**: Request only permissions you need
- **Sanitize output**: Prevent injection (SQL, XSS, command injection)
- **Auth at every layer**: Don't rely solely on frontend checks — enforce server-side

---

## Frontend

- **Server by default**: Fetch data and render on server when possible — better performance, SEO, and security
- **Minimize client state**: Derive values, avoid duplicating server state locally
- **Semantic HTML**: Use proper elements (`button`, `nav`, `article`), labels, ARIA when needed
- **Handle all states**: Every async operation has loading, success, and error states — design for all three

## Backend

- **Domain-driven structure**: Group by business capability, not technical layer
- **Explicit over implicit**: Dependency injection, clear data flow, no magic globals
- **Transactions for consistency**: Multi-step writes should be atomic — partial updates corrupt data
- **Idempotent operations**: Safe to retry without unintended side effects
- **Timeouts everywhere**: Network calls, database queries, external APIs — nothing should hang forever
- **Health checks**: Expose endpoints for liveness and readiness probes

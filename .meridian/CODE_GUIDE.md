<CODE_GUIDE>
# Code Guide — Next.js/React + Node.js/TypeScript Baseline

## General

### TypeScript
Write code as if these compiler options are enabled:
- `strict`, `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`
- `noUnusedLocals`, `noUnusedParameters`, `noImplicitReturns`

Type errors are build blockers. Never merge code with type errors.

**Library types**: Always use official `@types/*` packages or built-in types from libraries. Never write custom type definitions for typed libraries — only as a last resort for untyped libraries.

**No `as any`**: Never use `as any` to silence type errors. If you think you need it, you're likely:
- Missing a type import
- Fighting the type system instead of fixing the underlying issue
- Using an untyped library (add types or use a typed alternative)

Only use `as any` when there is genuinely no other option, and document why.

**Reuse existing types**: Before creating new types or interfaces, search the codebase for existing ones. Reuse what exists rather than creating duplicates.

Use explicit interfaces for props and API contracts.

### Project Structure
- Organize by feature/domain (e.g., `billing/`, `users/`) rather than technical layers.
- Use absolute path aliases (e.g., `@/components`) over deep relative paths.

### Error Handling
- Use typed errors with a stable shape `{ code, message, details }`.
- Don't hide errors with silent fallbacks (e.g., `data || {}`). Fail explicitly so problems surface early.
- Validate all external inputs (HTTP, queues, webhooks) with schemas (e.g., Zod).

### Security Essentials
- Load secrets from environment/secret stores; redact in logs.
- Prefer httpOnly cookies for auth tokens over localStorage.
- Sanitize any third-party HTML before rendering.

### Testing
- Fast unit tests for pure logic; integration tests at boundaries (HTTP handlers, components).
- Use fakes or containers for data stores; mock HTTP with tools like MSW.
- E2E tests for critical user journeys only.

### Config & Environment
- Validate env vars at startup; fail fast on invalid/missing values.
- Provide `.env.example` with placeholder values; never commit real secrets.

### Module Documentation
- Use `CLAUDE.md` files to document module context for agents
- Use the `claudemd-writer` skill for guidance on creating/updating these files

### Pattern Consistency
When adding code that integrates with existing modules:
1. Read the **full file** you're integrating with — never partial reads
2. Identify established patterns: factory functions, naming, error handling, logging, types
3. Follow those patterns in new code
4. If patterns conflict with this guide, follow existing code — consistency > standards

---

## Frontend (Next.js/React)

### Components
- Keep components focused; extract logic to hooks when it aids clarity.
- Use explicit prop interfaces; mark optional vs required clearly.

### Server vs Client
- Default to Server Components; add `use client` only when browser APIs or state are needed.
- Fetch data on the server by default; use client fetching when truly client-only.

### Data & State
- Use a data-fetching library (e.g., TanStack Query, SWR) for remote state.
- Store only necessary local state; derive values where possible.
- For forms, use schema validation colocated with the form.

### Routing & Data Flow
- Use App Router with nested layouts; colocate components with routes.
- Avoid data-fetching waterfalls — use parallel fetching or Suspense boundaries to stream above-the-fold content first.

### Styling
- Pick one approach (CSS Modules, Tailwind, or CSS-in-JS) and stay consistent.
- Use design tokens (CSS variables) for colors, spacing, typography.

### Performance
- Use `next/image` for images with proper dimensions.
- Code-split heavy widgets with `dynamic()`.
- Profile before adding memoization; prefer component boundaries first.

### Accessibility
- Use semantic HTML and proper labeling for inputs.
- Include automated checks (e.g., axe) on key flows.

### Error Handling
- Implement route-level `error.tsx` and `not-found.tsx`.
- Show users recovery options and support paths.

---

## Backend (Node.js/TypeScript)

### Architecture
- Prefer ESM with `"type": "module"`.
- Group by domain with clear application/infra separation.
- Export via index barrels; import from domain-level exports, not deep paths like `../../../other-domain/internal/`.

### Logging & Observability
- Use structured JSON logging (e.g., pino) with level, timestamp, requestId.
- Expose `/health` and `/ready` endpoints.
- Attach correlation IDs to requests and propagate to downstream calls.

### HTTP & API
- Map domain errors to precise HTTP status codes.
- Set security headers (e.g., via Helmet); configure CORS explicitly.
- Set timeouts on server and outbound requests; use AbortController.

### Authentication & Authorization
- Prefer session cookies (httpOnly, SameSite, Secure). If using JWTs, keep them short-lived.
- Enforce authorization in handlers and near data access.
- For multi-tenant systems, enforce tenant scoping server-side.

### Database
- Use an ORM or query builder with generated types.
- Version and review migrations; back up before destructive changes.
- Index lookup and join columns; monitor slow queries.
- Wrap multi-step writes in transactions.

### Background Work
- Use a queue (e.g., SQS, Redis) for async jobs; define retry and DLQ behavior.
- Keep scheduled jobs idempotent; guard against duplicate runs.

### Webhooks
- Verify signatures and timestamps.
- Retry with backoff; deduplicate deliveries.

### API Design
- Choose one style (REST, RPC, or GraphQL) and document it.
- Use cursor-based pagination; cap page sizes.
- Prefer UUIDs over sequential IDs for public-facing identifiers.

### Build & Deploy
- Use a fast bundler (e.g., tsup, esbuild); emit ESM.
- Run typecheck, lint, tests, and build in CI; block merges on failures.
</CODE_GUIDE>

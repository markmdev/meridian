# Code Guide — Production Addon

Stricter requirements for production systems. Applies on top of CODE_GUIDE.md.

---

## Security

- **CSP**: Configure strict Content-Security-Policy headers
- **Auth tokens**: httpOnly cookies only, short-lived, no client storage (localStorage/sessionStorage)
- **User content**: Sanitize all user-generated HTML before rendering
- **Webhooks**: Per-destination secrets, timestamp tolerance checks, replay protection
- **Tenant isolation**: Enforce at database layer (row-level policies) in addition to application checks

## Reliability

- **Resilience**: Outbound timeouts, retries with backoff, circuit breakers for external dependencies
- **Rate limiting**: Per IP/user/endpoint limits with `Retry-After` headers
- **Caching**: Stampede prevention, explicit invalidation paths, jittered TTLs
- **Background work**: Separate workers from API processes, DLQs mandatory, observable retry policies
- **Query safety**: Limit query depth/complexity, bound filters and aggregations

## Data

- **Database migrations**: Online schema changes for zero-downtime, strict indexing discipline
- **Transactions**: Bounded retry attempts, explicit timeout limits
- **Idempotency**: Require idempotency keys for unsafe POST endpoints, retain keys for reasonable duration
- **Data lifecycle**: Retention and purge policies implemented in code, purge jobs idempotent

## Observability

- **Logging**: Structured logs with correlation IDs, sensitive data redacted by default
- **Tracing**: Distributed tracing across services
- **Dashboards**: RED (Rate/Error/Duration) or USE (Utilization/Saturation/Errors) metrics
- **Alerting**: SLOs defined with alerts on breach
- **Error UX**: Standardized error pages with correlation IDs and support paths

## Build & Deploy

- **Config validation**: Environment must validate before startup, exit on invalid config
- **Containers**: Minimal images, pinned base versions, vulnerability scanning in CI
- **CI strictness**: Treat warnings as errors, block deploys on failures

## Frontend-Specific

- **Server components**: Default to server rendering, document justification for client components
- **Server actions**: Schema validation mandatory, return typed domain results
- **Data flow**: Per-route caching strategy documented, invalidation triggers explicit
- **Assets**: Optimized image formats, responsive sizes, font subsetting
- **Uploads**: Malware scanning, resumable uploads, robust error handling

## Backend-Specific

- **JWT handling**: Token rotation and revocation if using JWTs, consider device binding

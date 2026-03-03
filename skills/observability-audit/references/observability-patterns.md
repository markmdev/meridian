# Observability Anti-Patterns Reference

Concrete patterns to look for when auditing observability. Each pattern describes what to search for and what to look for when reading the code. Some patterns have literal search terms; others describe structural anti-patterns you identify by reading surrounding code.

## Debug Artifacts in Production

### Console.log/debug left in
**Search:** `console\.(log|debug|info|dir|trace|table)\(` (exclude test files, scripts)
**Note:** `console.warn` and `console.error` are sometimes intentional — check if they should use the app's logger instead.

**Bad:**
```ts
console.log('user data:', user)  // leaks PII, noise in production
```

**Fix:**
```ts
logger.debug('user loaded', { userId: user.id })  // structured, no PII
// or just delete it if it was temporary
```

### Temporary debugging code
**Search:** `// TODO.*debug|// TEMP|// HACK|debugger;|\.only\(`
**Note:** `.only(` catches leftover focused tests (`it.only`, `describe.only`) which won't run the full suite in CI.

**Bad:**
```ts
debugger;  // left from dev session
// HACK: remove this after testing
console.log('DEBUG ORDER:', JSON.stringify(order, null, 2))
```

**Fix:** Delete entirely. These have no production purpose.

### Printf/print debugging (Python, Go)
**Search (Python):** `\bprint\(` (exclude `__main__`, test files, CLI output)
**Search (Go):** `fmt\.Print|fmt\.Println|fmt\.Printf` (check if project uses a structured logger)
**Note:** In Go, `fmt.Print*` in non-CLI code is almost always debug output. In Python, `print()` in library/service code (not CLI/scripts) is the same signal.

**Bad:**
```python
print(f"processing user {user.email}")  # PII in stdout, no structure
```

**Fix:**
```python
logger.debug("processing user", extra={"user_id": user.id})
```

### Commented-out log statements
**Search:** `//\s*console\.|//\s*log\.|//\s*logger\.|#\s*print\(|#\s*logging\.`
**Note:** Commented-out logs are dead code that signals incomplete cleanup. Delete them.

## Errors That Disappear

### Catch without logging
**What to look for:** Any `catch` block where the caught error is neither logged nor re-thrown. The error enters the catch and disappears — no `logger.error`, no `console.error`, no `throw`. The function returns a default value or continues silently, and the failure is invisible in production.
**False positives:** Catch blocks that re-throw immediately (`catch (e) { throw new CustomError(..., e) }`) are fine — the error propagates upward where it should be logged.

**Bad:**
```ts
try { await processPayment(order) } catch (e) { return null }
```

**Fix:**
```ts
try { await processPayment(order) } catch (e) {
  logger.error('payment failed', { orderId: order.id, error: e.message })
  throw e
}
```

### Go error swallowing
**What to look for:** `if err != nil` blocks that return the error (or discard it with `_`) without logging, especially at service boundaries like HTTP handlers, gRPC handlers, and queue consumers. Deep in the call stack, `return err` or `return fmt.Errorf("...: %w", err)` is idiomatic propagation and fine. But at the top-level handler — where the error stops propagating and becomes an HTTP 500 or a dropped message — there should be a log call with context about what failed and why.
**Note:** In Go, `if err != nil { return err }` is idiomatic propagation — but at service boundaries (HTTP handlers, queue consumers), the error should be logged before returning.

**Bad:**
```go
if err != nil {
    return nil, err  // at an HTTP handler boundary — no log, no context
}
```

**Fix:**
```go
if err != nil {
    log.Error("failed to fetch user profile", "userID", userID, "error", err)
    return nil, fmt.Errorf("fetch user profile: %w", err)
}
```

### Python bare except / pass
**What to look for:** `except` blocks that do nothing with the error — the body is `pass`, an empty block, or a bare `continue`. Also look for broad `except Exception` blocks that catch everything but log with no context (just `logger.exception(e)` with no extra fields). The key signal is: if this exception fires in production, would anyone be able to figure out what happened?
**Note:** `except Exception: pass` is the Python version of silent error swallowing. Even `except Exception as e: logger.exception(e)` without context is nearly as bad.

**Bad:**
```python
try:
    send_notification(user)
except Exception:
    pass
```

**Fix:**
```python
try:
    send_notification(user)
except Exception:
    logger.exception("notification failed", extra={"user_id": user.id})
```

### Error logged without context
**What to look for:** Calls to `logger.error` or `logger.warn` where the only argument is a bare string message or just the error's message property. There are no entity IDs (order ID, user ID, request ID), no operation name, and no structured metadata object. In production, the log entry would read something like "failed" or "something went wrong" with nothing to tie it to a specific request or entity.
**False positives:** Utility/helper functions that don't have entity context available — the caller should add context instead.

**Bad:** `logger.error('failed')` or `logger.error(e.message)`
**Fix:** `logger.error('payment processing failed', { orderId, userId, error: e.message })`

### Promise rejection without handler
**What to look for:** Promises with empty catch handlers — `.catch(() => {})` or `.catch(() => undefined)` — that swallow the rejection silently. Also look for `.then()` chains with no `.catch()` at the end, especially for fire-and-forget calls where no one awaits the result. The async equivalent of `catch (e) { return null }`.
**Note:** Empty `.catch(() => {})` is the async equivalent of silent swallowing.

**Bad:**
```ts
fetchUserPreferences(userId).catch(() => {})
```

**Fix:**
```ts
fetchUserPreferences(userId).catch((e) => {
  logger.warn('failed to load user preferences', { userId, error: e.message })
})
```

### Error tracker without metadata
**Search:** `Sentry.captureException`, `captureException`, `Bugsnag.notify`, `rollbar.error`
**What to look for:** Calls to error tracking services that pass only the exception object with no additional context — no tags, no extra metadata, no user info, no `setContext`/`setTag`/`setUser` call nearby. The error shows up in Sentry/Bugsnag as a stack trace with no business context, making triage painful because you can't tell which user, request, or operation triggered it.
**Note:** Sending an exception to the tracker without request context, user info, or relevant state makes triage painful.

**Bad:**
```ts
Sentry.captureException(error)
```

**Fix:**
```ts
Sentry.captureException(error, {
  tags: { operation: 'payment_processing' },
  extra: { orderId: order.id, amount: order.total },
})
```

## Missing Context on Log Entries

### No entity IDs
**What to look for:** Log calls that pass only a message string with no structured context object as a second argument. The log entry would appear in production as just "order processed" or "payment failed" with no request ID, user ID, order ID, or any data to identify which specific entity or request the message applies to. Focus on `info`, `warn`, and `error` level calls — `debug` and `trace` with bare strings are lower priority.
**Note:** A log message without entity IDs is useless for debugging specific incidents. Every log at info level or above should identify what entity the operation applies to.

**Bad:**
```ts
logger.info('order processed')
```

**Fix:**
```ts
logger.info('order processed', { orderId: order.id, userId: order.userId, total: order.total })
```

### No request/correlation ID
**What to look for:** HTTP handlers, middleware chains, and service entry points that process incoming requests but never generate, extract, or propagate a request ID (sometimes called correlation ID or trace ID). Check whether the service has any mechanism for tying log entries from a single request together — look for `requestId`, `correlationId`, `traceId`, `x-request-id` in headers or context objects. If a service handles HTTP requests and none of these concepts appear anywhere, request tracing across services is impossible.
**False positives:** Internal tools, CLIs, and batch scripts don't need request IDs. Only applies to request-handling services.

### No operation timing
**What to look for:** Calls to external services, databases, or third-party APIs where there is no duration measurement around them — no `Date.now()` before/after, no `performance.now()`, no `time.Since()`, no APM span wrapping. Look at `fetch`, `axios`, HTTP client calls, database queries (`.query()`, `.execute()`, `.findMany()`), and similar I/O operations on the critical path. If the call takes 30 seconds in production, would anyone know?
**Note:** Not every call needs timing. Focus on calls that are on the critical path or known to be slow (external APIs, large queries).

### Log level misuse
**What to look for:** Log calls where the severity level contradicts the message content. Errors and failures logged at `info` or `debug` level (so they never trigger alerts), or routine successes logged at `warn` or `error` level (creating noise that drowns real issues). Read the log message — does it describe a failure? It should be `error` or `warn`. Does it describe normal operation? It should be `info` or `debug`.
**Note:** Wrong log level means alerts don't fire and noise drowns signal.

**Bad:**
```ts
logger.info('payment failed', { error: e.message })  // should be error level
logger.error('cache hit')  // should be debug level
```

**Fix:**
```ts
logger.error('payment failed', { error: e.message })
logger.debug('cache hit')
```

## Untracked Slow Operations

### External API calls without timing
**What to look for:** Calls to external services — payment providers, third-party APIs, ML inference endpoints, OAuth providers — where no duration is recorded. Look for `fetch()`, `axios`, `got()`, `requests.get/post`, `http.Do()`, and similar HTTP client calls. Check whether there is a `Date.now()` or `time.Now()` before the call and a duration log after, or whether the call is wrapped in an APM/tracing span. Internal service-to-service calls in well-instrumented systems may already be traced by APM — focus on external calls that cross trust boundaries.
**Note:** Not every fetch needs timing — focus on external services (payment providers, third-party APIs, ML inference). Internal service-to-service calls in well-instrumented systems may already be traced by APM.

**Bad:**
```ts
const result = await externalApi.call(params)
```

**Fix:**
```ts
const start = Date.now()
const result = await externalApi.call(params)
logger.info('external api call', { duration: Date.now() - start, endpoint: 'foo' })
```

### Database queries without observability
**What to look for:** Database calls — raw SQL via `.query()` or `.execute()`, ORM calls like `prisma.user.findMany()`, `knex('users').where(...)`, or `sequelize.query()` — with no timing, no slow-query detection, and no logging of query metadata. Check whether the ORM or database driver is configured with query-level logging/timing before flagging individual calls. Focus on raw queries (where ORM instrumentation does not apply) and queries that operate on large tables or use complex joins.
**Note:** ORM-level query logging may already exist — check the ORM config before adding manual timing. Focus on raw queries and queries known to be slow.

**Bad:**
```ts
const users = await db.query('SELECT * FROM users WHERE org_id = $1', [orgId])
```

**Fix:**
```ts
const start = Date.now()
const users = await db.query('SELECT * FROM users WHERE org_id = $1', [orgId])
const duration = Date.now() - start
if (duration > 100) {
  logger.warn('slow query', { query: 'users_by_org', orgId, duration })
}
```

### Background jobs without lifecycle logging
**What to look for:** Background job handlers — cron jobs, queue consumers, scheduled tasks, workers — that execute without logging their lifecycle. A properly instrumented job logs three things: when it starts (with job ID and input summary), when it completes (with duration), and when it fails (with error details and duration). Look for queue processor callbacks, `@task` decorators, cron handler functions, `setInterval` callbacks, and similar patterns. If the handler body has no log calls, a failed or hung job is invisible in production.
**Note:** Every background job should log when it starts, when it completes (with duration), and when it fails. Without this, you can't tell if a job ran, how long it took, or why it failed.

**Bad:**
```ts
queue.process('send-emails', async (job) => {
  await sendBulkEmails(job.data.userIds)
})
```

**Fix:**
```ts
queue.process('send-emails', async (job) => {
  const { userIds } = job.data
  logger.info('send-emails started', { jobId: job.id, userCount: userIds.length })
  const start = Date.now()
  try {
    await sendBulkEmails(userIds)
    logger.info('send-emails completed', { jobId: job.id, duration: Date.now() - start })
  } catch (e) {
    logger.error('send-emails failed', { jobId: job.id, duration: Date.now() - start, error: e.message })
    throw e
  }
})
```

### Webhook handlers without request logging
**What to look for:** Route handlers for webhook endpoints (paths containing `webhook`, `/hook`, `/callback`, or similar) where the handler does not log the incoming event type, a payload identifier, or the processing outcome. Webhooks are fire-and-forget from the sender's perspective — if your handler fails silently, the sender will retry (or not), and you have no visibility into what happened. A properly instrumented webhook handler logs: what event arrived (type + ID), whether processing succeeded or failed, and what action was taken.
**Note:** Webhooks are fire-and-forget from the sender's perspective. If your handler fails silently, you may never know. Log the event type, a payload identifier, and the processing result.

**Bad:**
```ts
app.post('/webhooks/stripe', async (req, res) => {
  const event = req.body
  await handleStripeEvent(event)
  res.sendStatus(200)
})
```

**Fix:**
```ts
app.post('/webhooks/stripe', async (req, res) => {
  const event = req.body
  logger.info('stripe webhook received', { type: event.type, id: event.id })
  try {
    await handleStripeEvent(event)
    logger.info('stripe webhook processed', { type: event.type, id: event.id })
    res.sendStatus(200)
  } catch (e) {
    logger.error('stripe webhook failed', { type: event.type, id: event.id, error: e.message })
    res.sendStatus(500)
  }
})
```

## Sensitive Data Exposure

### PII in log output
**What to look for:** Log calls that pass entire user objects, customer records, or request bodies to the logger instead of specific safe fields. Look for patterns like `logger.info('user', { user })` or `console.log(customer)` where the logged object contains fields like `.email`, `.password`, `.ssn`, `.phone`, `.address`, `.creditCard`, or `.token`. The fix is always the same: log the entity ID and relevant non-sensitive fields, never the full object.
**Note:** Logging user objects, request bodies, or full error stacks can leak PII. Log IDs, not data.

**Bad:**
```ts
logger.info('user signed up', { user })  // logs email, name, maybe password hash
```

**Fix:**
```ts
logger.info('user signed up', { userId: user.id, plan: user.plan })
```

### Full request/response body logging
**What to look for:** Log calls that pass `req.body`, `res.body`, `request.body`, `response.body`, or `response.data` directly as a logged value. The full request or response body may contain credentials, payment card numbers, personal data, or API keys. Look for these being passed into logger calls, `console.log`, or error tracker `extra` fields. The fix is to log specific safe fields (endpoint, content length, status code) rather than the full body.
**False positives:** Debug-level logging in development is acceptable if the logger respects log-level configuration and debug is off in production.

**Bad:**
```ts
logger.debug('incoming request', { body: req.body })
```

**Fix:**
```ts
logger.debug('incoming request', { endpoint: req.path, contentLength: req.headers['content-length'] })
```

### Secrets in error messages
**What to look for:** Error messages or log calls that interpolate environment variables or config values containing secrets — things like `process.env.API_KEY`, `config.secret`, `settings.TOKEN`, or `os.environ['PASSWORD']` inside template literals, f-strings, or string concatenation passed to `new Error()`, `throw`, `logger.*`, or `console.*`. The secret ends up in error trackers, log aggregators, and potentially in API responses shown to end users.
**Note:** Error messages that interpolate config values can leak secrets to error trackers, log aggregators, or end users.

**Bad:**
```ts
throw new Error(`Auth failed with key ${process.env.API_KEY}`)
```

**Fix:**
```ts
throw new Error('Auth failed: invalid API key')
```

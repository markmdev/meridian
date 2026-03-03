# Observability Anti-Patterns Reference

Concrete patterns to search for when auditing observability. Each section has detection patterns, bad examples, and fixes.

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
**Search:** `catch\s*\([^)]*\)\s*\{` then check body for absence of logger/console.error
**The test:** If a catch block exists, does it log? If not, the error vanishes.
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
**Search (Go):** `if err != nil \{` then check if the block contains only `return` with no logging
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
**Search (Python):** `except.*:\s*$` followed by `pass` or empty block; `except Exception:`
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
**Search:** `logger\.(error|warn)\(.*\)` — check if it includes entity IDs, operation name
**False positives:** Utility/helper functions that don't have entity context available — the caller should add context instead.

**Bad:** `logger.error('failed')` or `logger.error(e.message)`
**Fix:** `logger.error('payment processing failed', { orderId, userId, error: e.message })`

### Promise rejection without handler
**Search (JS/TS):** `\.catch\(\(\)\s*=>\s*\{\s*\}\)` or `\.catch\(\(\)\s*=>\s*undefined\)` or unhandled `.then()` chains with no `.catch()`
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
**Search:** `Sentry\.captureException|captureException|Bugsnag\.notify|rollbar\.error` — check if `setContext`, `setTag`, `setUser`, or metadata object is provided
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
**Detection:** Log calls with string message but no structured context object
**Search:** `logger\.\w+\(['"][^'"]+['"]\)$` (log with only a string, no second arg)
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
**Detection:** HTTP handlers or middleware with no request ID propagation
**Search:** `req\.id|requestId|correlationId|traceId|x-request-id` — if absent in a service handling requests, it's a gap
**False positives:** Internal tools, CLIs, and batch scripts don't need request IDs. Only applies to request-handling services.

### No operation timing
**Detection:** External calls (HTTP, DB, API) with no duration tracking
**Search:** `fetch\(|axios\.|http\.|\.query\(|\.execute\(` — check if surrounded by timing
**Note:** Not every call needs timing. Focus on calls that are on the critical path or known to be slow (external APIs, large queries).

### Log level misuse
**Search:** `logger\.info\(.*error|logger\.debug\(.*fail|logger\.warn\(.*success`
**Detection:** Errors logged at info/debug level, successes logged at warn/error level.
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
**Search:** `fetch\(|axios\.|got\(|superagent|urllib|requests\.(get|post|put|delete)|http\.Do\(`
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
**Search:** `\.query\(|\.execute\(|\.raw\(|\.findMany\(|\.findOne\(|db\.|prisma\.|knex\.|sequelize\.`
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
**Detection:** Background/async jobs with no start/complete/fail logs
**Search:** `cron\.|schedule\.|setInterval\(|worker\.|queue\.|Bull\(|Agenda\(|celery|@task`
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
**Search:** `webhook|/hook|/callback` in route definitions — check if incoming payload is logged (at debug level) and processing outcome is logged
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
**Search:** `\.email|\.password|\.ssn|\.phone|\.address|creditCard|cardNumber|\.token` adjacent to `logger\.|console\.|log\.|print\(`
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
**Search:** `req\.body|res\.body|request\.body|response\.body|response\.data` adjacent to log calls
**Note:** Logging full request bodies catches credentials, payment info, and personal data. Log specific fields or a sanitized summary.
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
**Search:** `API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL` adjacent to `Error\(|throw|logger\.|console\.|log\(`
**Note:** Error messages that interpolate config values can leak secrets to error trackers, log aggregators, or end users.

**Bad:**
```ts
throw new Error(`Auth failed with key ${process.env.API_KEY}`)
```

**Fix:**
```ts
throw new Error('Auth failed: invalid API key')
```

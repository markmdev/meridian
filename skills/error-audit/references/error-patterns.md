# Error Anti-Patterns Reference

Patterns to identify when auditing error handling. Each section describes the anti-pattern structurally — what the code does, not what keywords to grep for. Code examples show the bad pattern and the correct fix. "OK when" notes prevent false positives.

## Table of Contents

1. [Silent Error Swallowing](#silent-error-swallowing)
2. [Fallbacks to Degraded Alternatives](#fallbacks-to-degraded-alternatives)
3. [Config Defaults Hiding Misconfiguration](#config-defaults-hiding-misconfiguration)
4. [Backwards Compatibility Shims](#backwards-compatibility-shims)
5. [Optional Chaining on Required Data](#optional-chaining-on-required-data)
6. [UI Error Blindness](#ui-error-blindness)

---

## Silent Error Swallowing

### 1. Empty catch blocks

**Grep (JS/TS):** `catch\s*\([^)]*\)\s*\{\s*\}` or `\.catch\(\s*\(\)\s*=>\s*\{\s*\}\s*\)`
**Grep (Python):** `except.*:\s*\n\s*(pass|\.\.\.)\s*$`
**Grep (Go):** `, _ :?=` or `if err != nil \{\s*\}`

**What to look for:** A try/catch, except, or error return where the error path is completely empty — no logging, no re-throw, no return, nothing. In Go, this shows up as assigning the error to `_` or having an empty `if err != nil` block. The error is caught and silently discarded.

Bad (JS):
```js
try {
  await save(data);
} catch (e) {}
```

Bad (Python):
```python
try:
    save(data)
except Exception:
    pass
```

Bad (Go):
```go
result, _ := save(data)
```

Fix (JS):
```js
try {
  await save(data);
} catch (e) {
  throw e;
}
```

Fix (Python):
```python
try:
    save(data)
except Exception:
    logger.error("Failed to save", exc_info=True)
    raise
```

Fix (Go):
```go
result, err := save(data)
if err != nil {
    return fmt.Errorf("save failed: %w", err)
}
```

**OK when:** Intentionally ignoring a known-benign error (e.g., closing an already-closed connection) with a comment explaining why.

---

### 2. Log-and-continue

**What to look for:** A catch block that logs the error (console.error, logger.error, log.Print) but then lets execution continue as if nothing happened. The logging creates a false sense of "we handled it" — but the caller never learns the operation failed. Look for catch blocks where the only action is a log/print call with no throw, raise, or return after it.

Bad (JS):
```js
try {
  await processPayment(order);
} catch (e) {
  console.error("Payment failed:", e);
}
// execution continues as if payment succeeded
```

Fix (JS):
```js
try {
  await processPayment(order);
} catch (e) {
  console.error("Payment failed:", e);
  throw e;
}
```

**OK when:** The operation is genuinely non-critical (analytics, telemetry) and failure doesn't affect the user's workflow.

---

### 3. Return null/undefined/empty on failure

**What to look for:** A function that wraps its core logic in try/catch and returns a neutral value (null, undefined, empty array, empty object, empty string, zero) from the catch block. The caller receives what looks like a valid "not found" or "empty" response, but the real cause was an error — a database timeout, a network failure, a permission issue. The error is converted into a silent non-result.

Bad (JS):
```js
async function getUser(id) {
  try {
    return await db.users.findOne(id);
  } catch (e) {
    return null;
  }
}
```

Bad (Python):
```python
def get_user(user_id):
    try:
        return db.users.find_one(user_id)
    except Exception:
        return None
```

Fix (JS):
```js
async function getUser(id) {
  return await db.users.findOne(id);
  // Let the caller handle the error
}
```

Fix (Python):
```python
def get_user(user_id):
    return db.users.find_one(user_id)
    # Let the caller handle the error
```

**OK when:** The function's contract explicitly defines `null` as "not found" (not "error occurred"). The catch should only handle the specific "not found" case, not all exceptions.

---

### 4. Promise .catch with no-op

**Grep (JS/TS):** `\.catch\(\s*\(\)\s*=>` or `\.catch\(\s*\(_\)\s*=>`

**What to look for:** A promise chain ending with `.catch(() => {})` or `.catch(() => undefined)` — an explicit decision to swallow the rejection. Often appears on fire-and-forget calls where the developer didn't want an unhandled rejection warning but also didn't bother handling the error at all.

Bad:
```js
sendAnalytics(event).catch(() => {});
saveToCache(data).catch(() => undefined);
```

Fix:
```js
sendAnalytics(event).catch((e) => {
  console.error("Analytics send failed:", e);
  // OK to not re-throw for fire-and-forget analytics
});
```

**OK when:** Fire-and-forget for truly non-critical side effects (analytics, prefetch) — but the catch should still log, not silently swallow.

---

### 5. Bare except / broad exception catch

**Grep (Python):** `except\s*:` (bare except) or `except\s+Exception\s*:`

**What to look for:** A catch-all that handles every possible error type with the same recovery path. In Python, this is bare `except:` or `except Exception:`. In JS/TS, all `catch(e)` are technically broad, but the issue is when a single handler treats network errors, validation errors, and programming bugs identically — usually by returning a default value or logging and continuing.

Bad (Python):
```python
try:
    result = json.loads(data)
    process(result)
except:
    return default_result
```

Fix (Python):
```python
try:
    result = json.loads(data)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON input: {e}") from e
process(result)
```

**OK when:** Genuinely catching at the top-level boundary (e.g., a request handler that must return a response). Even then, catch `Exception` not bare `except`.

---

### 6. Error variable assigned but unused (Go)

**Grep (Go):** `, _ :?=` or `_ = .*\(`

**What to look for:** A function call that returns an error, but the error is assigned to `_` (explicit discard) or assigned to `err` and never checked on subsequent lines. Two or more consecutive calls discarding errors is a strong signal — if the first call fails, the second will likely produce garbage results from the nil/zero input.

Bad (Go):
```go
data, _ := json.Marshal(payload)
resp, _ := http.Post(url, "application/json", bytes.NewReader(data))
```

Fix (Go):
```go
data, err := json.Marshal(payload)
if err != nil {
    return fmt.Errorf("marshal payload: %w", err)
}
resp, err := http.Post(url, "application/json", bytes.NewReader(data))
if err != nil {
    return fmt.Errorf("post to %s: %w", url, err)
}
```

**OK when:** The function signature guarantees no error for the given input (e.g., `json.Marshal` on a struct with only basic types). Even then, prefer handling — it future-proofs against struct changes.

---

## Fallbacks to Degraded Alternatives

### 7. Silent model/API downgrade on failure

**What to look for:** A try/catch around an API or service call where the catch block retries with a different provider, model, endpoint, or tier — and the caller has no way to know a downgrade happened. The telltale structure: a mutable variable is assigned in the try block from service A, then reassigned in the catch block from service B. The downstream code uses the result identically regardless of which path produced it.

Bad:
```js
let result;
try {
  result = await callGPT4(prompt);
} catch {
  result = await callGPT3(prompt); // silent quality downgrade
}
```

Fix:
```js
const result = await callGPT4(prompt);
// If GPT-4 fails, the caller sees the error and decides what to do
```

Or if degradation is the product decision:
```js
try {
  result = await callGPT4(prompt);
} catch (e) {
  console.warn("GPT-4 unavailable, falling back to GPT-3:", e);
  result = await callGPT3(prompt);
  result.degraded = true; // surface to the user
}
```

**OK when:** Never OK to do silently. If the product requires fallback, the user must see an indication that they're getting degraded output.

---

### 8. Stale cache without indication

**What to look for:** A catch block that returns previously-fetched data from a cache, local storage, or an in-memory variable — without any signal to the caller that the data is stale. The structure: try block fetches fresh data and updates a cache; catch block reads from that same cache and returns it as if it were a normal response. The returned shape is identical in both paths, so the caller cannot distinguish fresh from stale.

Bad:
```js
async function fetchPrices() {
  try {
    const prices = await api.getPrices();
    cache.set("prices", prices);
    return prices;
  } catch {
    return cache.get("prices"); // could be hours old
  }
}
```

Fix:
```js
async function fetchPrices() {
  try {
    const prices = await api.getPrices();
    cache.set("prices", { data: prices, fetchedAt: Date.now() });
    return { data: prices, stale: false };
  } catch (e) {
    const cached = cache.get("prices");
    if (!cached) throw e;
    return { data: cached.data, stale: true, fetchedAt: cached.fetchedAt };
  }
}
// Caller must display staleness to the user
```

**OK when:** Never OK to serve stale data without indicating staleness. The cache fallback itself can be fine — the silence is the problem.

---

### 9. Offline/degraded mode with no UI indication

**What to look for:** A catch block that switches to a local or offline behavior path — saving locally instead of syncing, queuing instead of sending, using an in-memory store instead of the database — without any notification to the user. The user performs an action, sees no error, and assumes it completed normally. The key signal: a catch block that calls a different storage/transport mechanism than the try block, with no UI feedback (no toast, no banner, no status change).

Bad:
```js
try {
  await syncToServer(data);
} catch {
  saveLocally(data); // user thinks it synced
}
```

Fix:
```js
try {
  await syncToServer(data);
} catch (e) {
  saveLocally(data);
  toast.warn("Saved locally — will sync when connection restores");
}
```

**OK when:** The app has a visible, persistent offline indicator (e.g., a banner) that's already being shown. Don't duplicate the notification — but verify the indicator exists.

---

## Config Defaults Hiding Misconfiguration

### 10. Required env var with fallback value

**Grep (JS/TS):** `process\.env\.\w+\s*\|\|` or `process\.env\.\w+\s*\?\?`
**Grep (Python):** `os\.environ\.get\(.*,` or `os\.getenv\(.*,`

**What to look for:** An environment variable read with a hardcoded fallback value, where the variable holds something that MUST be explicitly configured — API keys, database URLs, secrets, service endpoints. The fallback means a missing or misconfigured deployment silently connects to the wrong database, uses a test API key in production, or talks to the wrong service. The danger is not the `||` operator itself but what it defaults: `PORT || 3000` is fine; `DATABASE_URL || "postgres://localhost/dev"` is not.

Bad (JS):
```js
const DB_URL = process.env.DATABASE_URL || "postgres://localhost:5432/dev";
const API_KEY = process.env.STRIPE_KEY || "sk_test_default";
```

Bad (Python):
```python
DB_URL = os.environ.get("DATABASE_URL", "postgres://localhost:5432/dev")
API_KEY = os.environ.get("STRIPE_KEY", "sk_test_default")
```

Fix (JS):
```js
const DB_URL = process.env.DATABASE_URL;
if (!DB_URL) throw new Error("DATABASE_URL is required");
const API_KEY = process.env.STRIPE_KEY;
if (!API_KEY) throw new Error("STRIPE_KEY is required");
```

Fix (Python):
```python
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL is required")
```

**OK when:** The value has a genuinely sensible default (e.g., `PORT || 3000`, `LOG_LEVEL || 'info'`, `NODE_ENV || 'development'`). Only flag values that MUST be configured: API keys, database URLs, secrets, service endpoints.

---

### 11. Optional config that should be required

**What to look for:** An environment variable read deep inside a handler, service, or utility function — far from application startup — without any validation. The variable is used directly (passed to an API client, used in a URL, etc.) and if it's undefined, the failure happens at runtime with a cryptic error from the downstream library rather than a clear startup-time message. The structural signal: `process.env.X` or `os.getenv("X")` appearing inside a function body rather than in a centralized config module.

Bad:
```js
// Buried in a handler, 500 lines from startup
async function sendEmail(to, body) {
  const key = process.env.SENDGRID_KEY; // undefined if not set
  await sendgrid.send({ apiKey: key, to, body }); // cryptic runtime error
}
```

Fix:
```js
// At startup (config.ts):
export const config = {
  sendgridKey: requireEnv("SENDGRID_KEY"),
};

// In handler:
async function sendEmail(to, body) {
  await sendgrid.send({ apiKey: config.sendgridKey, to, body });
}
```

**OK when:** The env var truly is optional and the feature gracefully disables without it (e.g., optional analytics integration).

---

## Backwards Compatibility Shims

### 12. Legacy format branches

**What to look for:** A conditional branch that handles an old data format, protocol version, or schema shape alongside the current one. The function checks a version field, tests for the presence/absence of old field names, or inspects the shape of the input to decide which parsing path to take. Often accompanied by comments mentioning dates, old version numbers, or migration context. The risk: these branches accumulate silently and never get removed because no one tracks whether old-format data still exists.

Bad:
```js
function parseConfig(data) {
  if (data.version === 1) {
    // Legacy format from 2023
    return { name: data.config_name, value: data.config_value };
  }
  return { name: data.name, value: data.value };
}
```

Fix:
```js
function parseConfig(data) {
  if (data.version === 1) {
    throw new Error("Config v1 is no longer supported. Migrate with: npx migrate-config");
  }
  return { name: data.name, value: data.value };
}
```

Or just delete the branch if v1 data no longer exists.

**OK when:** The legacy format is still in active production use (data in databases, files on disk). If it's only in old API clients, the API version should handle it — not inline branching.

---

### 13. Deprecated fields still populated

**What to look for:** An API response, data model, or event payload that assigns the same value to multiple fields with different naming conventions — camelCase and snake_case variants, fields prefixed with `old_` or `legacy_`, or simply two field names that carry identical data. The duplication exists because old consumers read the old field name and no one has coordinated removal. Look for object literals or serialization code where two or more keys are assigned from the same source value.

Bad:
```js
// API response
return {
  user_name: user.name,       // new field
  userName: user.name,         // old camelCase field, kept for compat
  display_name: user.name,     // even older field
};
```

Fix:
```js
return {
  user_name: user.name,
};
// Old clients should migrate. Announce deprecation with a deadline.
```

**OK when:** You're in a deprecation period with a documented sunset date. Flag it if there's no sunset date — it'll live forever.

---

### 14. Dual code paths

**What to look for:** A conditional that picks between two fully-implemented code paths based on a feature flag, toggle, or configuration value. Both branches do the same thing (process an order, render a page, handle a request) but through different implementations. The structural signal: an if/else or ternary where each branch calls a different module, pipeline, or service to accomplish the same task. If the flag has been at 100% for more than a release cycle, the old branch is dead code waiting to cause confusion.

Bad:
```js
function processOrder(order) {
  if (USE_NEW_PIPELINE) {
    return newPipeline.process(order);
  }
  return oldPipeline.process(order);
}
```

Fix:
```js
function processOrder(order) {
  return newPipeline.process(order);
}
// Delete oldPipeline entirely
```

**OK when:** The feature flag is actively being rolled out (partial traffic, A/B test). Flag it if the flag has been at 100% for weeks — the old path is dead code.

---

## Optional Chaining on Required Data

### 15. Defensive access on core entity fields

**What to look for:** Optional chaining (`?.`) or null checks on fields that the database schema defines as NOT NULL, or that the type system marks as required. The code treats guaranteed-present data as if it might be missing, often pairing `?.` with a fallback like `?? "Unknown"` or `?? ""`. This hides bugs: if the data IS missing, it means something upstream broke (a bad query, a corrupted record, a type mismatch) and the code should fail loudly, not silently substitute a placeholder. Cross-reference the field access with the schema or type definition to determine whether the chaining is warranted.

Bad:
```js
// User is fetched from DB where name is NOT NULL
const displayName = user?.name ?? "Unknown";
const email = user?.email ?? "";
```

Fix:
```js
// Trust the schema — if user exists, name exists
const displayName = user.name;
const email = user.email;
```

**OK when:** The data comes from an external API with unreliable schemas, or the type is a union that includes `null`/`undefined` (e.g., `User | null` from a find query). The chaining is wrong when the data is guaranteed present by the query that fetched it.

---

### 16. Chaining through always-present nested objects

**What to look for:** Multiple optional chaining operators stacked on a single property access path (`a?.b?.c?.d`). When the nesting represents a required relationship (an order's shipping address, a user's account settings), each `?.` is a silent null check that suppresses what should be a hard failure. The deeper the chain, the more likely it is masking a missing validation or a broken invariant upstream. Check the data model: if the relationship is required, the chaining should be replaced with an explicit existence check and a thrown error.

Bad:
```js
const city = order?.shipping?.address?.city ?? "N/A";
// If order has a shipping address, all fields are required
```

Fix:
```js
if (!order.shipping?.address) {
  throw new Error(`Order ${order.id} missing shipping address`);
}
const city = order.shipping.address.city;
```

**OK when:** The nesting genuinely represents optional relationships (e.g., a user who may or may not have a profile, which may or may not have a bio). Check the schema before deciding.

---

### 17. Nullish coalescing default on required field

**What to look for:** A nullish coalescing operator (`??`) or Python `or` providing a default value for a field that should never be null according to the data model. The default masks a broken invariant — if `session.userId` is null, there's an authentication bug; substituting `"anonymous"` hides it. The structural signal: `??` followed by a string literal, zero, empty array, or empty object on a field that the schema or type says is required. Compare the defaulted field against its type definition or schema constraint.

Bad:
```js
const userId = session.userId ?? "anonymous";
const role = user.role ?? "viewer";
```

Fix:
```js
if (!session.userId) {
  throw new Error("Session has no userId — authentication bug");
}
const userId = session.userId;
const role = user.role; // role is required in the User schema
```

**OK when:** The default genuinely represents the correct behavior for missing data (e.g., `timezone ?? "UTC"`, `locale ?? "en"`).

---

## UI Error Blindness

### 18. Fetch error renders blank/empty

**What to look for:** A component that fetches data and initializes its state to an empty array or null, but has no separate error state. When the fetch fails, the component renders its "empty" state — an empty list, a blank area, no items — which is indistinguishable from "the data loaded and there's genuinely nothing there." Look for components using `useState([])` or `useState(null)` with a fetch in `useEffect` or a data hook, where the error path either swallows the error or doesn't exist. Also check for destructuring with defaults (`const { items = [] } = data`) that silently convert undefined (error) into empty (no data).

Bad:
```jsx
function UserList() {
  const [users, setUsers] = useState([]);
  useEffect(() => {
    fetchUsers().then(setUsers).catch(() => {});
  }, []);
  return <ul>{users.map(u => <li>{u.name}</li>)}</ul>;
  // On error: renders empty list, user sees blank space
}
```

Fix:
```jsx
function UserList() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState(null);
  useEffect(() => {
    fetchUsers().then(setUsers).catch(setError);
  }, []);
  if (error) return <ErrorMessage error={error} retry={() => fetchUsers().then(setUsers)} />;
  return <ul>{users.map(u => <li>{u.name}</li>)}</ul>;
}
```

**OK when:** Never OK. Every data fetch must have a visible error state.

---

### 19. Error boundary with generic message and no recovery

**What to look for:** An error boundary (React class with `componentDidCatch` or `getDerivedStateFromError`, or a library wrapper) whose fallback UI is a dead end — a generic "Something went wrong" message with no retry button, no navigation link, no context about what failed. The user's only option is to refresh the entire page or leave. Check the fallback render: does it offer any action (retry, go home, contact support)? Does it say what went wrong?

Bad:
```jsx
class AppErrorBoundary extends React.Component {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) return <p>Something went wrong.</p>;
    return this.props.children;
  }
}
```

Fix:
```jsx
render() {
  if (this.state.hasError) {
    return (
      <ErrorFallback
        error={this.state.error}
        onRetry={() => this.setState({ hasError: false })}
        onGoHome={() => window.location.href = "/"}
      />
    );
  }
  return this.props.children;
}
```

**OK when:** It's the outermost boundary acting as a last resort — but even then, offer a "Go home" or "Refresh" action. Pure dead-end error screens are never OK.

---

### 20. Async operation with no loading or error state

**What to look for:** A button click handler, form submit handler, or other user-initiated action that calls an async function (API request, mutation, delete) without try/catch and without any loading/pending state. When the operation fails, nothing happens — the button stays enabled, no error appears, the user clicks again. When it's slow, there's no indication that anything is in progress. The structural signal: an `async` function called from `onClick` or `onSubmit` with a bare `await` and no surrounding try/catch, no loading boolean, and no error state variable.

Bad:
```jsx
function DeleteButton({ id }) {
  const handleDelete = async () => {
    await api.delete(id);
    router.refresh();
  };
  return <button onClick={handleDelete}>Delete</button>;
  // No loading state, no error handling — button does nothing on failure
}
```

Fix:
```jsx
function DeleteButton({ id }) {
  const [pending, setPending] = useState(false);
  const handleDelete = async () => {
    setPending(true);
    try {
      await api.delete(id);
      router.refresh();
    } catch (e) {
      toast.error("Failed to delete. Please try again.");
    } finally {
      setPending(false);
    }
  };
  return <button onClick={handleDelete} disabled={pending}>
    {pending ? "Deleting..." : "Delete"}
  </button>;
}
```

**OK when:** Never OK for user-initiated actions. Navigation-triggered fetches can rely on framework loading states (Next.js `loading.tsx`), but explicit user actions (button clicks, form submits) need inline feedback.

---

### 21. Toast/notification on error without context

**What to look for:** A catch block that shows a user-facing notification (toast, alert, modal) with a generic message like "An error occurred", "Something went wrong", or just "Error" — with no indication of what operation failed or what the user can do about it. The user sees a red notification and has no idea whether their save failed, their payment bounced, or their upload timed out. Check catch blocks that call toast/notification/alert functions and inspect the message string: does it name the failed operation?

Bad:
```js
catch (e) {
  toast.error("An error occurred");
}
```

Fix:
```js
catch (e) {
  toast.error(`Failed to save document: ${e.message}`);
  // Or for user-facing: toast.error("Could not save your document. Please try again.");
}
```

**OK when:** Never OK to show a message with zero context. At minimum, say *what* failed. Include the error message in logs even if the toast is user-friendly.

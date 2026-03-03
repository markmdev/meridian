# Error Anti-Patterns Reference

Concrete patterns to search for when auditing error handling. Each section includes grep-able patterns, examples of bad code, and the correct fix. When a pattern is sometimes legitimate, the "OK when" note prevents false positives.

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

**Search (JS/TS):** `catch\s*\([^)]*\)\s*\{\s*\}` or `\.catch\(\s*\(\)\s*=>\s*\{\s*\}\s*\)`
**Search (Python):** `except.*:\s*\n\s*(pass|\.\.\.)\s*$`
**Search (Go):** `if err != nil \{\s*\}` or lines with `err` on LHS but no check

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

**Search (JS/TS):** `catch\s*\([^)]*\)\s*\{[^}]*console\.(log|error|warn)` (without a subsequent `throw`)
**Search (Python):** `except.*:\s*\n\s*(logging\.|logger\.|print\()` (without a subsequent `raise`)
**Search (Go):** `log\.(Print|Fatal|Error).*\n[^}]*\}` inside an `if err != nil` block that doesn't return

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

**Search (JS/TS):** `catch\s*\([^)]*\)\s*\{[^}]*(return\s+(null|undefined|void 0|\[\]|\{\}|""|''))` or `\.catch\(\s*\(\)\s*=>\s*(null|\[\]|\{\})`
**Search (Python):** `except.*:\s*\n\s*return\s+(None|\[\]|\{\}|"")`
**Search (Go):** `if err != nil \{[^}]*return\s+(nil|""|0|\[\])`

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

**Search (JS/TS):** `\.catch\(\s*\(\)\s*=>` or `\.catch\(\s*\(_\)\s*=>` or `\.catch\(\(\)\s*=>\s*\{\}\)`
**Search (broader):** `\.catch\(` then check the handler body

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

**Search (Python):** `except\s*:` (bare except) or `except\s+Exception\s*:`
**Search (JS/TS):** Generally all `catch(e)` are broad, but look for catches that handle different error types identically
**Search (Go):** N/A (Go uses typed errors)

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

**Search (Go):** `err\s*:?=` then check the next lines don't reference `err`
**Search (Go, underscore):** `, _ :?=` or `_ = .*\(` (explicit discard of error)

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

**Search:** `catch.*=.*fallback|catch.*=.*default|\.catch\(\(\).*=>` combined with model/API identifiers
**Search (broader):** Look for try/catch around API calls where the catch uses a different endpoint, model, or service

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

**Search:** `catch.*(cache|stale|cached|getCache|readCache)` or `catch.*localStorage` or `catch.*sessionStorage`
**Search (broader):** Error handlers that return cached/previous values

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

**Search:** `catch.*(offline|degraded|fallback)` or `navigator\.onLine` or `catch.*mode\s*=`
**Search (broader):** State variables set inside catch blocks

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

**Search (JS/TS):** `process\.env\.\w+\s*\|\|\s*['"]` or `process\.env\.\w+\s*\?\?\s*['"]`
**Search (Python):** `os\.environ\.get\(\s*['"][^'"]+['"]\s*,\s*['"]` or `os\.getenv\(\s*['"][^'"]+['"]\s*,\s*['"]`
**Search (Go):** `os\.Getenv\(` followed by `if.*==\s*""\s*\{` with a default assignment

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

**Search (JS/TS):** `process\.env\.\w+` used without validation
**Search (broader):** Environment variables read deep in the code (not at startup) without any check

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

**Search:** `if.*legacy|if.*deprecated|if.*old_|if.*v1[^.]|if.*oldFormat|if.*previousVersion`
**Search (broader):** `TODO.*remove|HACK|COMPAT|backwards.*compat`

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

**Search:** `deprecated|@deprecated|DEPRECATED` or field names with `old_`, `legacy_`, `prev_`
**Search (broader):** Assignments to two fields that seem to carry the same data

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

**Search:** `if.*new.*\{|if.*feature.*flag|if.*useNew|if.*enableV2`
**Search (broader):** Feature flags or toggles that have both branches fully implemented

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

**Search (JS/TS):** `\?\.\w+` combined with core entity names (user, order, session, account, etc.)
**Search (broader):** Optional chaining on fields that are required by the database schema or type definition

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

**Search (JS/TS):** `\?\.\w+\?\.\w+` (double optional chain) or `\?\.\w+\?\.\w+\?\.\w+` (triple)
**Search (broader):** Chains of 3+ optional accesses on a single expression

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

**Search (JS/TS):** `\?\?\s*['"]` (nullish coalescing to string default) or `\?\?\s*0` or `\?\?\s*\[\]` or `\?\?\s*\{\}`
**Search (Python):** `or\s*['"]` or `if.*is None.*=` (defaulting on None)

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

**Search (JS/TS):** `catch.*return\s*\{` in data fetching functions, then check if the component has error state rendering
**Search (React):** `useQuery|useSWR|fetch\(` without corresponding error UI
**Search (broader):** Components that destructure data with defaults: `const { items = [] } = data`

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

**Search (React):** `ErrorBoundary|componentDidCatch|getDerivedStateFromError`
**Search (broader):** Check what the fallback UI renders — does it offer retry, navigation, or context?

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

**Search (React):** `useState.*loading|isLoading|isPending` — check that corresponding error state exists too
**Search (broader):** `onClick.*await|onSubmit.*await` handlers without try/catch or error state

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

**Search:** `toast\.(error|warn)|notification\.(error|warn)|showError|alert\(` — check the message content
**Search (broader):** Error messages that are generic strings: "Error", "Something went wrong", "An error occurred"

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

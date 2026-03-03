# UX State Patterns Reference

What to look for when auditing loading, empty, and error states. Organized by framework with structural descriptions and fix examples.

## React / Next.js

### Missing Loading States

#### 1. Data hook without loading check

**What to look for:** A component that destructures a data-fetching hook but never handles the pending state. The component renders the data value directly, which is `undefined` on first mount before the fetch resolves.

Common shapes:
- Data hook destructured without `isLoading` or `isPending` — the component renders `data` which is undefined on first mount
- Component immediately passes hook result into child components with no guard for the not-yet-loaded case
- Status field exists on the hook but is never read or branched on

**Bad:**
```tsx
const { data } = useQuery({ queryKey: ['users'], queryFn: fetchUsers })
return <UserList users={data} />  // undefined during fetch
```

**Fix:**
```tsx
const { data, isLoading } = useQuery({ queryKey: ['users'], queryFn: fetchUsers })
if (isLoading) return <UserListSkeleton />
return <UserList users={data} />
```

**When it's OK:** Server components that await data before rendering. Prefetched queries where data is guaranteed by the parent.

---

#### 2. useState + async useEffect with no loading flag

**What to look for:** A component that uses `useState` to hold fetched data and `useEffect` to trigger the fetch, but has no companion loading state. The state variable starts as `null` or `undefined`, and nothing tells the user that data is on its way.

Common shapes:
- `useState(null)` paired with a `useEffect` that fetches and calls the setter, but no second `useState` for loading
- The component renders the null initial state directly (blank screen, missing content) until the effect resolves
- Sometimes a conditional like `if (!data) return null` hides the gap, but this is indistinguishable from "no data exists"

**Bad:**
```tsx
const [users, setUsers] = useState(null)
useEffect(() => {
  fetch('/api/users').then(r => r.json()).then(setUsers)
}, [])
return <UserList users={users} />  // null during fetch
```

**Fix:**
```tsx
const [users, setUsers] = useState(null)
const [isLoading, setIsLoading] = useState(true)
useEffect(() => {
  fetch('/api/users').then(r => r.json()).then(setUsers).finally(() => setIsLoading(false))
}, [])
if (isLoading) return <Spinner />
return <UserList users={users} />
```

**When it's OK:** When the parent component handles the loading state and this component only renders after data is ready.

---

#### 3. Form submission with no pending state

**What to look for:** A submit handler that calls an API but provides no feedback while the request is in flight. The button stays clickable, the form stays interactive, and nothing indicates the operation is processing.

Common shapes:
- An async click/submit handler that awaits an API call, but the button has no disabled state and no text change
- The handler sets no state before the `await` — the UI looks identical during the request
- Double-click risk: the button can be clicked multiple times, firing duplicate requests

**Bad:**
```tsx
const handleSubmit = async () => {
  await createUser(formData)
  router.push('/users')
}
return <button onClick={handleSubmit}>Create</button>
```

**Fix:**
```tsx
const handleSubmit = async () => {
  setIsSubmitting(true)
  await createUser(formData)
  router.push('/users')
}
return <button onClick={handleSubmit} disabled={isSubmitting}>
  {isSubmitting ? 'Creating...' : 'Create'}
</button>
```

**When it's OK:** Trivial instant operations (toggling local state). Server actions in Next.js where `useFormStatus` handles the pending state externally.

---

#### 4. Route transition with no loading indicator

**What to look for:** Navigation to a data-heavy page with no loading UI during the transition. The user clicks a link and the screen either freezes (while the new page loads server-side) or flashes blank content before the new page hydrates.

Common shapes:
- Links to dynamic routes that fetch data, but no `loading.tsx` file in the target route segment
- `router.push` calls with no transition wrapper — the current page stays frozen until the new one is ready
- App Router pages that do server-side fetching without a sibling `loading.tsx` to show during the Suspense boundary

**Bad:**
```tsx
<Link href={`/projects/${id}`}>View Project</Link>
// No loading.tsx in the target route segment
```

**Fix:**
```tsx
// app/projects/[id]/loading.tsx
export default function Loading() {
  return <ProjectDetailSkeleton />
}
```

**When it's OK:** Static pages with no data fetching. Pages where the layout already shows a global progress bar (NProgress, Next.js built-in).

---

#### 5. Mutation hook without pending feedback

**What to look for:** A mutation hook wired to a button or action, but the component never reads the pending state from the hook. The trigger element looks identical before, during, and after the mutation.

Common shapes:
- Mutation hook is created but only `.mutate()` is called — `isPending` is never destructured or referenced in JSX
- The button that triggers the mutation has no disabled prop and no text/icon change during the request
- Destructive actions (delete, archive) with no visual confirmation that the operation is in progress

**Bad:**
```tsx
const deleteMutation = useMutation({ mutationFn: deleteItem })
return <button onClick={() => deleteMutation.mutate(id)}>Delete</button>
```

**Fix:**
```tsx
const deleteMutation = useMutation({ mutationFn: deleteItem })
return (
  <button onClick={() => deleteMutation.mutate(id)} disabled={deleteMutation.isPending}>
    {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
  </button>
)
```

**When it's OK:** When an optimistic update with `onMutate` provides immediate visual feedback instead.

---

### Missing Empty States

#### 6. Array `.map()` with no empty check

**What to look for:** A data array from a fetch/query rendered via `.map()` with no guard for the zero-length case. The component renders an empty container element (blank `<ul>`, empty grid) when there's no data.

Common shapes:
- `.map()` on a data array inside JSX with no preceding length check — renders an empty wrapper element
- The empty wrapper is styled with padding/borders, making the blank space look broken rather than intentional
- Array comes from a hook or state that can legitimately be empty (search results, filtered lists, new accounts)

**Bad:**
```tsx
return (
  <ul>
    {users.map(u => <UserRow key={u.id} user={u} />)}
  </ul>
)  // empty <ul> when no users
```

**Fix:**
```tsx
if (users.length === 0) {
  return <EmptyState message="No users yet" action={{ label: 'Invite', href: '/invite' }} />
}
return (
  <ul>
    {users.map(u => <UserRow key={u.id} user={u} />)}
  </ul>
)
```

**When it's OK:** Container components where the empty case is structurally impossible (e.g., data is pre-validated upstream).

---

#### 7. Conditional rendering that shows nothing

**What to look for:** A short-circuit conditional (`data && <Component />`) that renders content when data exists but shows absolutely nothing when it doesn't. The user sees blank space with no explanation.

Common shapes:
- `{data && <Component />}` with no else/fallback — the falsy branch renders nothing
- `{items.length > 0 && <List />}` that hides the entire section when empty instead of explaining why it's empty
- Nested conditionals where the else branches all return null, leaving the user with a blank area

**Bad:**
```tsx
{searchResults && searchResults.length > 0 && (
  <SearchResultsList results={searchResults} />
)}
// Shows blank space when no results
```

**Fix:**
```tsx
{searchResults && searchResults.length > 0 ? (
  <SearchResultsList results={searchResults} />
) : (
  <p className="text-muted">No results found. Try different keywords.</p>
)}
```

**When it's OK:** Progressive disclosure where the section genuinely should not appear until data exists (e.g., "Recent activity" on a brand-new account where showing "No activity" is worse than hiding the section).

---

#### 8. Table or grid with no "no results" row

**What to look for:** A table component where the body maps over rows but has no fallback for when the row array is empty. The user sees table headers with an empty body below them.

Common shapes:
- `<tbody>` that contains only a `.map()` call — renders zero `<tr>` elements when data is empty
- Table or DataTable component that receives an array prop and iterates it without an empty-state slot
- The empty table looks broken: headers are visible but the body area is collapsed or awkwardly spaced

**Bad:**
```tsx
<table>
  <thead><tr><th>Name</th><th>Email</th></tr></thead>
  <tbody>
    {users.map(u => <tr key={u.id}><td>{u.name}</td><td>{u.email}</td></tr>)}
  </tbody>
</table>  // empty tbody when no users
```

**Fix:**
```tsx
<tbody>
  {users.length === 0 ? (
    <tr><td colSpan={2} className="text-center py-8">No users found</td></tr>
  ) : (
    users.map(u => <tr key={u.id}><td>{u.name}</td><td>{u.email}</td></tr>)
  )}
</tbody>
```

**When it's OK:** Paginated tables where the parent already guards against page 1 having zero results.

---

#### 9. Dashboard widget with no empty content

**What to look for:** A dashboard card or widget that renders a chart or statistic but has no handling for when the underlying data is empty or all zeros. The chart renders blank or with misleading axes.

Common shapes:
- A chart component receives a data array that can be empty — the chart renders with axes but no data points, looking broken
- A stat card shows "0" or "NaN" when there's no data, instead of a contextual message
- The widget has no conditional: it always renders the visualization regardless of whether there's meaningful data

**Bad:**
```tsx
<Card title="Revenue">
  <LineChart data={revenueData} />
</Card>  // blank chart when no data
```

**Fix:**
```tsx
<Card title="Revenue">
  {revenueData.length === 0 ? (
    <p className="text-muted py-8">No revenue data for this period</p>
  ) : (
    <LineChart data={revenueData} />
  )}
</Card>
```

**When it's OK:** Charts that gracefully render an empty state internally (some chart libraries show "No data" by default).

---

### Missing Error States

#### 10. Data hook without error check

**What to look for:** A component that uses a data-fetching hook but never reads or handles the error state. If the fetch fails, the component either renders with undefined data (crashing or showing blank content) or stays in the loading state forever.

Common shapes:
- Data hook destructured with `data` and `isLoading` but `error`/`isError` is never read
- The component has loading and success states but no branch for the failure case
- On fetch failure, the component falls through to rendering `data` which is undefined, causing either a blank screen or a runtime error

**Bad:**
```tsx
const { data, isLoading } = useQuery({ queryKey: ['users'], queryFn: fetchUsers })
if (isLoading) return <Spinner />
return <UserList users={data} />  // silently shows nothing on error
```

**Fix:**
```tsx
const { data, isLoading, error } = useQuery({ queryKey: ['users'], queryFn: fetchUsers })
if (isLoading) return <Spinner />
if (error) return <ErrorBanner message="Failed to load users" onRetry={refetch} />
return <UserList users={data} />
```

**When it's OK:** When wrapped in an Error Boundary that catches rendering errors from undefined data. But the error boundary won't catch the query error unless the component throws it.

---

#### 11. try/catch that swallows the error

**What to look for:** A `try/catch` around a data operation where the catch block does nothing visible to the user. The error is logged to console or silently discarded, and the UI stays in whatever state it was in — no feedback, no recovery option.

Common shapes:
- Catch block that only has `console.error(e)` — the user sees the form/page freeze with no explanation
- Catch block that returns null or early-returns without setting any error state or showing a notification
- Empty catch block `catch (e) {}` that completely swallows the failure

**Bad:**
```tsx
try {
  const data = await fetchUsers()
  setUsers(data)
} catch (e) {
  console.error(e)  // user sees nothing
}
```

**Fix:**
```tsx
try {
  const data = await fetchUsers()
  setUsers(data)
} catch (e) {
  toast.error('Failed to load users. Please try again.')
  setError(e)
}
```

**When it's OK:** Background telemetry/analytics where failure is acceptable and users should not be interrupted.

---

#### 12. Mutation with no error handling in UI

**What to look for:** A mutation (via hook or direct API call in an event handler) with no error callback and no error state shown to the user. If the mutation fails, the UI provides zero feedback — the user doesn't know if their action succeeded or failed.

Common shapes:
- Mutation hook created without an `onError` callback, and `isError`/`error` never referenced in the component
- Direct `await fetch()` in a handler wrapped in try/catch that only logs, or not wrapped at all
- The component has success handling (redirect, toast, close modal) but no corresponding failure handling

**Bad:**
```tsx
const mutation = useMutation({ mutationFn: updateProfile })
const handleSave = () => mutation.mutate(formData)
// No error feedback anywhere
```

**Fix:**
```tsx
const mutation = useMutation({
  mutationFn: updateProfile,
  onError: (err) => toast.error(`Save failed: ${err.message}`),
})
const handleSave = () => mutation.mutate(formData)
```

**When it's OK:** Optimistic updates where rollback is handled via `onError` + `queryClient.setQueryData` and the user sees the revert as feedback.

---

## Go (Server-Side / API)

### Missing Error Responses

#### 13. Handler returns without writing error response

**What to look for:** An HTTP handler that detects an error condition (failed DB query, bad input, missing resource) but returns from the handler without writing an error response to the client. The client receives an empty 200 OK.

Common shapes:
- `if err != nil` block that logs the error and returns, but never calls an error response function — the handler exits and the default 200 status is sent
- Early return after a validation failure with no response written — the response body is empty
- Multiple error checks where some write responses and others silently return

**Bad:**
```go
user, err := db.GetUser(id)
if err != nil {
    log.Printf("failed to get user: %v", err)
    return  // client gets empty 200
}
```

**Fix:**
```go
user, err := db.GetUser(id)
if err != nil {
    log.Printf("failed to get user: %v", err)
    http.Error(w, "Failed to load user", http.StatusInternalServerError)
    return
}
```

**When it's OK:** Middleware that delegates error handling to a centralized error handler downstream.

---

#### 14. json.Encode error not handled

**What to look for:** A response encoding call where the returned error is silently discarded. If encoding fails (rare but possible with broken writers or circular references), the client gets a partial or corrupt response with no logging.

Common shapes:
- `json.NewEncoder(w).Encode(data)` called as a statement with the return value ignored
- The encode call is the last line of the handler — if it fails, nothing catches it
- Similar pattern with `xml.NewEncoder`, `yaml.NewEncoder`, or manual `w.Write(jsonBytes)` without checking the error

**Bad:**
```go
w.Header().Set("Content-Type", "application/json")
json.NewEncoder(w).Encode(response)
```

**Fix:**
```go
w.Header().Set("Content-Type", "application/json")
if err := json.NewEncoder(w).Encode(response); err != nil {
    log.Printf("failed to encode response: %v", err)
}
```

**When it's OK:** In practice, `Encode` to `http.ResponseWriter` rarely fails, so some codebases accept this. But it's technically a gap.

---

#### 15. Middleware continues after auth failure

**What to look for:** Auth middleware that writes an error response (401/403) when authentication fails but doesn't return afterward. Execution falls through to the next handler, which runs with an unauthenticated request and writes a second response to the already-responded writer.

Common shapes:
- The error response is written inside an `if` block but there's no `return` after it — the next handler runs unconditionally
- The `if !authenticated` branch writes the 401 and the code continues past the closing brace to `next.ServeHTTP`
- Similar pattern in authorization middleware: writes 403 but falls through to the protected handler

**Bad:**
```go
func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if !isAuthenticated(r) {
            http.Error(w, "Unauthorized", 401)
        }
        next.ServeHTTP(w, r)  // runs even when auth failed
    })
}
```

**Fix:**
```go
func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if !isAuthenticated(r) {
            http.Error(w, "Unauthorized", 401)
            return
        }
        next.ServeHTTP(w, r)
    })
}
```

**When it's OK:** Never. This is always a bug.

---

## General (Framework-Agnostic)

### Skeleton vs. Spinner Guidelines

- **Skeletons** (content-shaped placeholders): Use when the layout of the loaded content is predictable. Lists, cards, profile pages, tables. The skeleton mirrors the final shape.
- **Spinners** (generic loading indicator): Use when the content shape is unpredictable or the loading area is small (inline button, icon action).
- **Inline loading** (button spinner, disabled state): Use for user-initiated actions — form submissions, mutations, button clicks. The trigger element shows feedback.
- **Page/route loading** (skeleton or progress bar): Use for navigation between pages or major content swaps.

### Empty State Guidelines

- Every empty state should answer: **why is this empty?** and **what can I do?**
- Prefer "No projects yet. Create your first project." over a blank area.
- Distinguish between "no data exists" and "filters returned nothing" — these need different messages and actions.
- Use illustrations or icons sparingly. The message matters more than decoration.
- Avoid negative language ("Nothing here", "No results") without context. Add the reason or next step.

### Error State Guidelines

- Say what went wrong in user terms — "Couldn't load your projects" not "500 Internal Server Error" or "Something went wrong."
- Always offer an action: retry, go back, contact support.
- Don't show raw error messages, stack traces, or technical details to end users.
- Distinguish between recoverable errors (retry) and permanent errors (navigate away, contact support).
- For inline errors (form fields, mutations), show the error near the trigger — not in a disconnected toast.
- For page-level errors, provide a full-page error state with navigation options.

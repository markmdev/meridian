# UX State Patterns Reference

What to look for when auditing loading, empty, and error states. Organized by framework with detection patterns and fix examples.

## React / Next.js

### Missing Loading States

#### 1. Data hook without loading check

**Detection pattern:** `useQuery|useSWR|useFetch` used but the component never checks `isLoading`, `isPending`, or `status === 'loading'`.

**Grep:** `useQuery|useSWR` in a file that does NOT contain `isLoading|isPending|isFetching`

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

**Detection pattern:** `useState` holding fetched data, `useEffect` calling an async function, but no companion `isLoading` state variable.

**Grep:** `useState.*null\)` near `useEffect` with `fetch|axios` but no `Loading|loading|pending` state

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

**Detection pattern:** `onSubmit` or `handleSubmit` handler that calls an API but never sets `isSubmitting` or disables the button.

**Grep:** `onSubmit|handleSubmit` calling `fetch|mutate|axios` without `disabled|isSubmitting|isPending`

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

**Detection pattern:** `router.push` or `<Link>` navigation to data-heavy pages with no loading UI during the transition.

**Grep:** `router.push|useRouter` without `useTransition|loading.tsx|Suspense`

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

**Detection pattern:** `useMutation` called without using `isPending` to show inline feedback.

**Grep:** `useMutation` without `isPending|isLoading` referenced in JSX

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

**Detection pattern:** `.map()` called on a data array with no preceding `length === 0` or `!data.length` guard.

**Grep:** `\.map\(` on a variable that came from a query/fetch, without `.length` check nearby

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

**Detection pattern:** `data && <Component />` or `data?.length > 0 && <List />` that renders nothing when the condition is false.

**Grep:** `&&\s*<` with data or array checks, no else/fallback branch

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

**Detection pattern:** `<table>` or `<DataTable>` component with a body that maps rows but no fallback for zero rows.

**Grep:** `<table|<Table|<DataTable` with `.map` in tbody but no empty/fallback

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

**Detection pattern:** Dashboard card or widget that renders a chart or stat but has no handling for when the underlying data is empty or zero.

**Grep:** Chart components (`<BarChart|<LineChart|<PieChart`) that don't check `data.length`

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

**Detection pattern:** `useQuery|useSWR` used but the component never checks `error`, `isError`, or `failureReason`.

**Grep:** `useQuery|useSWR` in a file that does NOT contain `isError|error\b|failureReason`

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

**Detection pattern:** `try/catch` around a data fetch where the catch block returns null, logs to console, or does nothing visible.

**Grep:** `catch.*\{` followed by `console\.|return null|return;|\}` with no toast/setState/throw

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

**Detection pattern:** `useMutation` or direct API call in event handler with no `onError` callback and no error state shown to the user.

**Grep:** `useMutation` without `onError|isError|error` in the same component

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

**Detection pattern:** HTTP handler checks an error condition but returns without calling `http.Error`, `json.NewEncoder`, or the framework's error response method.

**Grep:** `if err != nil \{` followed by `return` without `http\.Error|w\.Write|json\.NewEncoder|c\.JSON|RespondWith`

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

**Detection pattern:** `json.NewEncoder(w).Encode(data)` called without checking the returned error.

**Grep:** `json\.NewEncoder.*\.Encode\(` not assigned to an error variable or checked

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

**Detection pattern:** Auth middleware checks credentials but doesn't return after writing the 401/403 — execution falls through to the next handler.

**Grep:** `Unauthorized|Forbidden|401|403` followed by handler chain without `return`

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

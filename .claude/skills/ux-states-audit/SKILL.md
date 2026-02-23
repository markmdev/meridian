---
name: ux-states-audit
description: Audit UI code for missing loading states, empty states, and error states. Every async operation and data-driven UI must handle all three. Finds gaps and implements the missing states using the app's existing patterns.
---

# UX States Audit

Every piece of UI that fetches data or triggers async work has three states beyond the happy path: **loading**, **empty**, and **error**. LLMs implement the happy path and leave the rest blank. This skill finds and fills those gaps.

This is distinct from error-audit: error-audit finds errors that are *suppressed*. This finds states that were *never implemented*.

## Step 0: Understand existing patterns

Before touching anything, read the codebase to understand how it currently handles these states:
- What components or primitives exist for loading (skeletons, spinners, shimmer)?
- What does an empty state look like — is there a shared component, or inline?
- How are errors shown to users — toast, inline message, error boundary?

Use these patterns exclusively. Don't introduce a new loading spinner if one already exists.

## What to look for

**Missing loading state:**
- Data fetch starts, nothing changes in the UI until data arrives
- Button triggered action with no pending/disabled state
- Form submission with no in-progress indicator
- Navigation or route transition with no feedback

**Missing empty state:**
- List or table that renders nothing (blank space) when data is an empty array
- Search results that show nothing without explanation
- Dashboard widgets that disappear when there's no data instead of explaining why

**Missing error state:**
- Fetch fails → component renders identical to loading or blank
- Form submission fails → nothing visible changes
- Mutation errors that are caught in the data layer but never reach the UI

## Process

1. Identify the scope from the user's request
2. Find every component that fetches data or triggers async work
3. For each: check whether loading, empty, and error states are handled
4. Implement missing states using the patterns found in Step 0
5. Report what was added, by component

## Fix principles

- Loading states should be immediate — shown before the first byte arrives
- Empty states should explain the situation and, where appropriate, offer an action ("No results — try a different search")
- Error states should say what went wrong and what the user can do (retry, go back, contact support)
- Don't invent new UI primitives — use what already exists in the codebase

## Report

Summarize by component: which states were missing, what was added.

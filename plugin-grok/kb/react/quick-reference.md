# React Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Hooks

| Hook | Purpose | When to Use |
|------|---------|-------------|
| `useState` | Local component state | Simple state (toggle, counter, form field) |
| `useReducer` | Complex state with actions | Multiple related state values, state machines |
| `useEffect` | Side effects | Subscriptions, DOM manipulation, external sync |
| `useRef` | Mutable ref, no re-render | DOM access, instance variables, previous values |
| `useMemo` | Memoize computation | Expensive calculations, referential equality |
| `useCallback` | Memoize function | Callback passed to optimized child components |
| `useContext` | Read context value | Theme, auth, shared state across tree |
| `use` | Read promise/context | Server Components data, async context |

## Component Types

| Type | Directive | JS Bundle | Hooks | When to Use |
|------|-----------|-----------|-------|-------------|
| Server Component | None (default) | 0 KB | No | Data fetching, static content, DB access |
| Client Component | `"use client"` | Yes | Yes | Interactivity, browser APIs, event handlers |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Display data from DB/API | Server Component |
| Form with validation | Client Component |
| Static content | Server Component |
| onClick, onChange handlers | Client Component |
| Expensive import (date-fns, chart lib) | Server Component or dynamic import |
| Read cookies/headers | Server Component |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `useEffect` for data fetching | Use Server Components or React Query |
| `"use client"` on every file | Default to Server Component, add directive only when needed |
| Props drilling > 2 levels | Use composition, Context, or state library |
| Mutate state directly | Return new object/array from setState |
| Missing key in lists | Use stable, unique key (not index) |

## Related Documentation

| Topic | Path |
|-------|------|
| Getting Started | `concepts/hooks-patterns.md` |
| Full Index | `index.md` |

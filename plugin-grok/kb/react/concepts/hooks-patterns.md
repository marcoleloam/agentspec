# Hooks Patterns

> **Purpose**: Core React hooks — rules, patterns, and custom hook extraction
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Hooks are functions that let you use state and lifecycle features in function components. All hooks follow the Rules of Hooks: call at top level only, call from React functions only.

## The Concept

```tsx
// useState — local state
const [count, setCount] = useState(0);
const [user, setUser] = useState<User | null>(null);

// useEffect — side effects (subscriptions, DOM)
useEffect(() => {
  const sub = subscribe(id);
  return () => sub.unsubscribe(); // cleanup
}, [id]); // re-run when id changes

// useRef — mutable ref, no re-render
const inputRef = useRef<HTMLInputElement>(null);
inputRef.current?.focus();

// useMemo — memoize expensive computation
const sorted = useMemo(() => items.sort(compareFn), [items]);

// useCallback — memoize function reference
const handleClick = useCallback(() => {
  setCount(c => c + 1);
}, []);

// Custom hook — extract reusable logic
function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
```

## Quick Reference

| Hook | Re-renders? | Use For |
|------|-------------|---------|
| `useState` | Yes | Local component state |
| `useReducer` | Yes | Complex state with actions |
| `useEffect` | No | Side effects, subscriptions |
| `useRef` | No | DOM refs, mutable values |
| `useMemo` | No | Expensive calculations |
| `useCallback` | No | Stable function references |

## Common Mistakes

### Wrong

```tsx
// useEffect for data fetching — race conditions
useEffect(() => {
  fetch("/api/user").then(r => r.json()).then(setUser);
}, []);
```

### Correct

```tsx
// Server Component fetch (Next.js) or React Query
const user = await fetchUser(); // Server Component
// OR
const { data: user } = useQuery({ queryKey: ["user"], queryFn: fetchUser });
```

## Related

- [server-components.md](../concepts/server-components.md)
- [component-composition.md](../patterns/component-composition.md)

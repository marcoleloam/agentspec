# State Management

> **Purpose**: Choosing the right state solution — Context, Zustand, Jotai, React Query
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Most state doesn't need a library. Server state belongs in React Query/SWR. Client state in useState/useReducer. Global state in Zustand (simple) or Jotai (atomic). Context for dependency injection, not frequent updates.

## The Concept

```tsx
// 1. URL State — useSearchParams (Next.js)
const searchParams = useSearchParams();
const filter = searchParams.get("status");

// 2. Server State — React Query
const { data, isLoading } = useQuery({
  queryKey: ["orders", filter],
  queryFn: () => fetchOrders(filter),
});

// 3. Global Client State — Zustand (simple)
import { create } from "zustand";
const useCartStore = create<CartStore>((set) => ({
  items: [],
  addItem: (item) => set((s) => ({ items: [...s.items, item] })),
  clearCart: () => set({ items: [] }),
}));

// 4. Context — dependency injection, not frequent updates
const ThemeContext = createContext<Theme>("light");
function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

## Quick Reference

| State Type | Solution | When |
|------------|----------|------|
| Form input | `useState` | Single component |
| Complex form | React Hook Form | Multiple fields + validation |
| Server data | React Query / SWR | API data with cache |
| URL params | `useSearchParams` | Filters, pagination, search |
| Global UI | Zustand | Theme, sidebar, modals |
| Atomic state | Jotai | Fine-grained reactivity |
| Dependency injection | Context | Theme, auth, i18n |

## Common Mistakes

### Wrong

```tsx
// Storing server data in useState — no cache, no revalidation
const [users, setUsers] = useState([]);
useEffect(() => { fetch("/api/users").then(r => r.json()).then(setUsers); }, []);
```

### Correct

```tsx
// React Query handles cache, revalidation, loading, error
const { data: users } = useQuery({ queryKey: ["users"], queryFn: fetchUsers });
```

## Related

- [hooks-patterns.md](../concepts/hooks-patterns.md)
- [data-fetching.md](../patterns/data-fetching.md)

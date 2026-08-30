# Frontend Patterns Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Project Structure

| Directory | Purpose | Example |
|-----------|---------|---------|
| `src/app/` | Routes (Next.js App Router) | `app/dashboard/page.tsx` |
| `src/components/ui/` | Shared UI primitives | Button, Input, Dialog |
| `src/components/` | Feature components | ProductCard, UserAvatar |
| `src/lib/` | Utilities, API client | `utils.ts`, `api.ts` |
| `src/hooks/` | Custom hooks | `useDebounce.ts` |
| `src/types/` | Shared TypeScript types | `api.types.ts` |

## Error Handling Strategy

| Error Type | Where to Handle | UI Treatment |
|-----------|----------------|-------------|
| Render error | Error Boundary | error.tsx fallback |
| API 4xx | Fetch wrapper | Toast or inline message |
| API 5xx | Fetch wrapper | Toast + retry button |
| Network error | Fetch wrapper | Offline banner |
| Form validation | Form library | Inline field errors |
| Not found | not-found.tsx | 404 page |

## Performance Checklist

| Check | Tool | Target |
|-------|------|--------|
| LCP | Lighthouse | < 2.5s |
| FID/INP | Lighthouse | < 200ms |
| CLS | Lighthouse | < 0.1 |
| Bundle size | `next build` output | < 100KB first load JS |
| Images | next/image | WebP, responsive sizes |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Shared state across routes | Zustand or Context |
| Server data with cache | React Query + Server Components |
| Form state | React Hook Form |
| URL state (filters, search) | `useSearchParams` |
| Optimistic UI | React Query `useMutation` |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Organize by file type (all components/) | Feature-based folders |
| Catch errors silently | Show user-friendly error + log |
| Load everything upfront | Dynamic import for heavy components |
| Store server data in useState | Use React Query or server fetch |

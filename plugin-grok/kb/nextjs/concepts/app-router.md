# App Router

> **Purpose**: File-based routing with layouts, loading states, and error boundaries
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Next.js App Router uses the filesystem to define routes. Special files (layout.tsx, loading.tsx, error.tsx) provide automatic UI patterns. Layouts persist across navigation, loading.tsx creates Suspense boundaries, error.tsx creates Error Boundaries.

## The Concept

```text
app/
├── layout.tsx          # Root layout — wraps ALL pages
├── page.tsx            # Home route: /
├── loading.tsx         # Loading UI for / (Suspense)
├── error.tsx           # Error UI for / (Error Boundary)
├── not-found.tsx       # 404 page
├── dashboard/
│   ├── layout.tsx      # Nested layout — persists within /dashboard/*
│   ├── page.tsx        # /dashboard
│   ├── settings/
│   │   └── page.tsx    # /dashboard/settings
│   └── @analytics/     # Parallel route (slot)
│       └── page.tsx    # Renders alongside dashboard
├── blog/
│   ├── page.tsx        # /blog
│   └── [slug]/         # Dynamic segment
│       └── page.tsx    # /blog/my-post
└── (marketing)/        # Route group — no URL segment
    ├── about/
    │   └── page.tsx    # /about (not /marketing/about)
    └── pricing/
        └── page.tsx    # /pricing
```

```tsx
// layout.tsx — persists across child navigations
export default function DashboardLayout({
  children,
  analytics, // parallel route slot
}: {
  children: React.ReactNode;
  analytics: React.ReactNode;
}) {
  return (
    <div className="flex">
      <Sidebar />
      <main>{children}</main>
      <aside>{analytics}</aside>
    </div>
  );
}
```

## Quick Reference

| File | Purpose | Rendered |
|------|---------|----------|
| `page.tsx` | Route UI | Required for route |
| `layout.tsx` | Shared wrapper | Persists on navigation |
| `loading.tsx` | Loading state | Auto Suspense boundary |
| `error.tsx` | Error state | Auto Error Boundary |
| `not-found.tsx` | 404 | When `notFound()` called |
| `route.ts` | API handler | GET/POST/PUT/DELETE |
| `template.tsx` | Re-mounting wrapper | Re-creates on navigate |

## Common Mistakes

### Wrong

```tsx
// Using layout.tsx when you need re-mount on navigation
export default function Layout({ children }) { /* ... */ }
```

### Correct

```tsx
// Use template.tsx if you need fresh state per navigation
export default function Template({ children }) { /* re-mounts */ }
```

## Related

- [rendering-strategies.md](../concepts/rendering-strategies.md)
- [middleware.md](../concepts/middleware.md)

# Next.js Quick Reference

> Fast lookup tables. For code examples, see linked files.

## File Conventions (App Router)

| File | Purpose | Renders |
|------|---------|---------|
| `page.tsx` | Route UI | Required for route to be accessible |
| `layout.tsx` | Shared wrapper | Wraps page and nested layouts, persists across navigation |
| `loading.tsx` | Loading UI | Automatic Suspense boundary for page |
| `error.tsx` | Error UI | Automatic Error Boundary for page |
| `not-found.tsx` | 404 UI | Shown when `notFound()` is called |
| `route.ts` | API endpoint | Route Handler (GET, POST, etc.) |
| `middleware.ts` | Request interceptor | Runs before every matched request |
| `template.tsx` | Re-rendered wrapper | Like layout but re-mounts on navigation |

## Rendering Strategies

| Strategy | When to Use | Data Freshness | Performance |
|----------|-------------|----------------|-------------|
| Static (SSG) | Content rarely changes | Build time | Fastest |
| ISR | Content changes periodically | Revalidate interval | Fast |
| SSR | Content changes per request | Every request | Slower |
| PPR | Mix of static and dynamic | Partial | Fast shell + streaming |
| Client | User-specific, interactive | Client fetch | Depends on API |

## Cache Layers

| Layer | Scope | Duration | Opt Out |
|-------|-------|----------|---------|
| Request Memoization | Same render pass | Single request | N/A |
| Data Cache | `fetch()` results | Until revalidate | `cache: 'no-store'` |
| Full Route Cache | Static HTML + RSC | Until revalidate | `dynamic = 'force-dynamic'` |
| Router Cache | Client-side prefetch | 30s dynamic, 5min static | `router.refresh()` |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `"use client"` at layout level | Keep layouts as Server Components |
| Fetch in Client Component when server works | Fetch in Server Component, pass as props |
| Ignore cache layers | Explicitly configure caching per fetch |
| `getServerSideProps` in App Router | Use `async` Server Components instead |
| Static paths without `generateStaticParams` | Define params for build-time generation |

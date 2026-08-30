# Next.js Knowledge Base

> **Purpose**: Next.js App Router patterns — rendering strategies, caching, middleware, deployment
> **MCP Validated**: 2026-03-29

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/app-router.md](concepts/app-router.md) | Layouts, loading, error, parallel routes |
| [concepts/rendering-strategies.md](concepts/rendering-strategies.md) | SSR, SSG, ISR, PPR, streaming |
| [concepts/caching.md](concepts/caching.md) | Request memo, Data Cache, Full Route, Router Cache |
| [concepts/middleware.md](concepts/middleware.md) | Auth, redirects, headers, geolocation |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/api-routes.md](patterns/api-routes.md) | Route handlers, validation, streaming responses |
| [patterns/auth-patterns.md](patterns/auth-patterns.md) | NextAuth v5, middleware auth, sessions |
| [patterns/image-optimization.md](patterns/image-optimization.md) | next/image, blur, responsive sizes |
| [patterns/deployment.md](patterns/deployment.md) | Vercel, Docker, static export |

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **App Router** | File-system routing with layouts, loading states, and error boundaries |
| **Server Components** | Default rendering — fetch data on server, zero client JS |
| **Caching** | Four layers: request memo → data cache → full route → router cache |
| **Middleware** | Runs before every request — auth, redirects, headers |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| react-developer | All files | Component implementation in Next.js |
| frontend-architect | concepts/rendering-strategies.md, concepts/caching.md | Architecture decisions |

# Rendering Strategies

> **Purpose**: SSR, SSG, ISR, PPR — choosing the right strategy per page
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Next.js defaults to static rendering. Pages with dynamic data can use ISR (revalidate), SSR (force-dynamic), or PPR (static shell + streaming dynamic parts). Choose per-route based on data freshness needs.

## The Concept

```tsx
// 1. Static (SSG) — default, fastest
// No dynamic functions, no uncached fetch
async function AboutPage() {
  return <h1>About Us</h1>; // Built at build time
}

// 2. ISR — revalidate periodically
async function ProductsPage() {
  const products = await fetch("https://api.example.com/products", {
    next: { revalidate: 3600 }, // Rebuild every hour
  }).then(r => r.json());
  return <ProductGrid products={products} />;
}

// 3. SSR — fresh on every request
export const dynamic = "force-dynamic";
async function DashboardPage() {
  const data = await fetchUserDashboard(); // Always fresh
  return <Dashboard data={data} />;
}

// 4. PPR (Partial Prerendering) — static shell + streaming
import { Suspense } from "react";
async function StorePage() {
  return (
    <div>
      <Header />           {/* Static shell — instant */}
      <Suspense fallback={<Skeleton />}>
        <DynamicProducts /> {/* Streams when ready */}
      </Suspense>
    </div>
  );
}
```

## Quick Reference

| Strategy | Data | Performance | Use When |
|----------|------|-------------|----------|
| Static | Build time | Fastest | Marketing, docs, blog |
| ISR | Periodic refresh | Fast | Products, listings |
| SSR | Every request | Slower | Dashboard, personalized |
| PPR | Mixed | Fast shell | E-commerce, feeds |

## Common Mistakes

### Wrong

```tsx
// SSR everything — unnecessary server load
export const dynamic = "force-dynamic"; // On a static about page!
```

### Correct

```tsx
// Default to static, opt into dynamic only when needed
// No export needed — static by default
```

## Related

- [caching.md](../concepts/caching.md)
- [app-router.md](../concepts/app-router.md)

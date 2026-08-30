# Caching

> **Purpose**: Four cache layers — request memo, data cache, full route, router cache
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Next.js has four distinct cache layers that work together. Understanding each layer and how to opt out is critical for correct data freshness behavior.

## The Concept

```tsx
// Layer 1: Request Memoization — same render pass
// Two components calling same fetch → one request
async function Layout() {
  const user = await getUser(); // fetch #1
  return <Nav user={user}><Page /></Nav>;
}
async function Page() {
  const user = await getUser(); // deduped — uses #1's result
  return <Profile user={user} />;
}

// Layer 2: Data Cache — fetch results persisted
// Opt out: cache: 'no-store'
const data = await fetch(url, { cache: "no-store" }); // skip data cache
const data = await fetch(url, { next: { revalidate: 60 } }); // ISR

// Layer 3: Full Route Cache — rendered HTML + RSC payload
// Opt out: export const dynamic = 'force-dynamic'
export const dynamic = "force-dynamic"; // page.tsx

// Layer 4: Router Cache — client-side prefetch
// Invalidate with router.refresh()
import { useRouter } from "next/navigation";
const router = useRouter();
router.refresh(); // clears router cache for current route
```

## Quick Reference

| Layer | Scope | Duration | Opt Out |
|-------|-------|----------|---------|
| Request Memo | Single render | One request | N/A |
| Data Cache | fetch() results | Until revalidate | `cache: 'no-store'` |
| Full Route | HTML + RSC | Until revalidate | `dynamic = 'force-dynamic'` |
| Router Cache | Client prefetch | 30s (dynamic) / 5min (static) | `router.refresh()` |

## Common Mistakes

### Wrong

```tsx
// Not understanding why stale data appears
// (Router Cache serves old prefetch for 30 seconds)
```

### Correct

```tsx
// After mutation, invalidate both server and client caches
"use server";
async function updateProduct(id: string, data: FormData) {
  await db.update("products", id, data);
  revalidatePath("/products"); // server cache
  // Router cache auto-invalidated by Server Action
}
```

## Related

- [rendering-strategies.md](../concepts/rendering-strategies.md)
- [api-routes.md](../patterns/api-routes.md)

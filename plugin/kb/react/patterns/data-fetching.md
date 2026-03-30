# Data Fetching

> **Purpose**: Server Components fetch, React Query for client, Suspense loading
> **MCP Validated**: 2026-03-29

## When to Use

- Loading data from APIs or databases
- Caching and revalidating server data
- Handling loading and error states

## Implementation

```tsx
// 1. Server Component — direct fetch (preferred in Next.js)
async function ProductPage({ params }: { params: { id: string } }) {
  const product = await fetch(`https://api.example.com/products/${params.id}`, {
    next: { revalidate: 3600 }, // ISR: revalidate every hour
  }).then(r => r.json());

  return <ProductDetail product={product} />;
}

// 2. Client Component — React Query
"use client";
import { useQuery } from "@tanstack/react-query";

function ProductSearch({ query }: { query: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["products", "search", query],
    queryFn: () =>
      fetch(`/api/products/search?q=${query}`).then(r => r.json()),
    enabled: query.length > 2,
  });

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;
  return <ProductGrid products={data} />;
}

// 3. Suspense boundary for async Server Components
import { Suspense } from "react";

function Page() {
  return (
    <div>
      <h1>Products</h1>
      <Suspense fallback={<ProductListSkeleton />}>
        <ProductList />  {/* async, streams when ready */}
      </Suspense>
    </div>
  );
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `staleTime` | `0` | How long data is considered fresh |
| `gcTime` | `5min` | How long inactive data stays in cache |
| `retry` | `3` | Number of retries on failure |
| `enabled` | `true` | Conditionally enable/disable query |

## See Also

- [server-components.md](../concepts/server-components.md)
- [rendering-patterns.md](../concepts/rendering-patterns.md)

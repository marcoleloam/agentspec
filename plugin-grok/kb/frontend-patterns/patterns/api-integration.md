# API Integration

> **Purpose**: Typed fetch wrapper, Zod validation, error types, retry
> **MCP Validated**: 2026-03-29

## When to Use

- Calling REST APIs from client or server
- Type-safe API responses with runtime validation
- Consistent error handling across the app

## Implementation

```tsx
// lib/api.ts — typed fetch wrapper
import { z } from "zod";

class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function api<T>(
  url: string,
  options?: RequestInit & { schema?: z.ZodType<T> }
): Promise<T> {
  const { schema, ...fetchOptions } = options ?? {};

  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...fetchOptions.headers },
    ...fetchOptions,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.code ?? "UNKNOWN", body.message ?? res.statusText);
  }

  const data = await res.json();
  return schema ? schema.parse(data) : data;
}

// Usage with Zod schema validation
const ProductSchema = z.object({
  id: z.string(),
  name: z.string(),
  price: z.number(),
});

const ProductListSchema = z.array(ProductSchema);

// Server Component
async function getProducts() {
  return api("/api/products", { schema: ProductListSchema });
}

// Client Component with React Query
function useProducts() {
  return useQuery({
    queryKey: ["products"],
    queryFn: () => api("/api/products", { schema: ProductListSchema }),
  });
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `schema` | — | Zod schema for runtime validation |
| `headers` | `Content-Type: application/json` | Auto-set JSON header |
| Retry | Via React Query | `retry: 3` in query config |

## See Also

- [error-handling.md](../concepts/error-handling.md)
- [optimistic-updates.md](../patterns/optimistic-updates.md)

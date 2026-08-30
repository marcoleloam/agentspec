# Server Components

> **Purpose**: React Server Components — default rendering, client boundaries, Server Actions
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Server Components are the default in Next.js App Router. They render on the server, have zero JS bundle impact, and can directly access databases and APIs. Add `"use client"` only when interactivity is needed.

## The Concept

```tsx
// Server Component (DEFAULT — no directive needed)
async function ProductList() {
  const products = await db.query("SELECT * FROM products");
  return (
    <ul>
      {products.map(p => <li key={p.id}>{p.name}</li>)}
    </ul>
  );
}

// Client Component — needs interactivity
"use client";
import { useState } from "react";

function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}

// Server Action — server-side mutation from client
"use server";
async function addToCart(productId: string) {
  await db.insert("cart_items", { productId, userId: getUser().id });
  revalidatePath("/cart");
}
```

## Quick Reference

| Feature | Server Component | Client Component |
|---------|-----------------|-----------------|
| Directive | None (default) | `"use client"` |
| JS bundle | 0 KB | Included |
| Hooks | No | Yes |
| Browser APIs | No | Yes |
| async/await | Yes | No (use useEffect) |
| DB/filesystem | Yes | No |

## Common Mistakes

### Wrong

```tsx
"use client"; // Unnecessary! This component has no interactivity
function Header() {
  return <h1>Welcome</h1>;
}
```

### Correct

```tsx
// No directive — defaults to Server Component
function Header() {
  return <h1>Welcome</h1>;
}
```

## Related

- [hooks-patterns.md](../concepts/hooks-patterns.md)
- [data-fetching.md](../patterns/data-fetching.md)

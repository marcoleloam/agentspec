# Rendering Patterns

> **Purpose**: Suspense, Error Boundaries, Streaming SSR, transitions
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

React provides built-in patterns for handling loading (Suspense), errors (Error Boundary), and non-urgent updates (useTransition). In Next.js, these map to file conventions: loading.tsx and error.tsx.

## The Concept

```tsx
// Suspense — loading fallback
import { Suspense } from "react";

function Page() {
  return (
    <Suspense fallback={<Skeleton />}>
      <ProductList />  {/* async Server Component */}
    </Suspense>
  );
}

// Error Boundary — catch render errors (error.tsx in Next.js)
"use client";
function ErrorFallback({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button onClick={reset}>Try again</button>
    </div>
  );
}

// useTransition — non-urgent updates
"use client";
import { useTransition } from "react";

function FilterBar() {
  const [isPending, startTransition] = useTransition();
  const [filter, setFilter] = useState("");

  function handleChange(value: string) {
    startTransition(() => setFilter(value)); // won't block typing
  }

  return (
    <>
      <input onChange={(e) => handleChange(e.target.value)} />
      {isPending && <Spinner />}
      <Results filter={filter} />
    </>
  );
}
```

## Quick Reference

| Pattern | Purpose | Next.js Convention |
|---------|---------|-------------------|
| Suspense | Loading fallback | `loading.tsx` |
| Error Boundary | Error fallback | `error.tsx` |
| useTransition | Non-blocking update | N/A (client only) |
| Streaming | Progressive HTML | Automatic with Suspense |

## Common Mistakes

### Wrong

```tsx
// Manual loading state instead of Suspense
const [loading, setLoading] = useState(true);
```

### Correct

```tsx
// Suspense handles loading automatically
<Suspense fallback={<Skeleton />}>
  <AsyncComponent />
</Suspense>
```

## Related

- [server-components.md](../concepts/server-components.md)
- [data-fetching.md](../patterns/data-fetching.md)

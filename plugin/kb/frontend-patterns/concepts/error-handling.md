# Error Handling

> **Purpose**: Error Boundaries, error.tsx, toast notifications, retry logic
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Handle errors at every level: Error Boundaries for rendering crashes, error.tsx for route-level errors, toast for user feedback, and typed errors for API calls. Never swallow errors silently.

## The Concept

```tsx
// 1. Next.js error.tsx — route-level error boundary
"use client";
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4 p-8">
      <h2 className="text-xl font-semibold">Something went wrong</h2>
      <p className="text-muted-foreground">{error.message}</p>
      <button onClick={reset} className="rounded bg-primary px-4 py-2 text-white">
        Try again
      </button>
    </div>
  );
}

// 2. Typed API errors
class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// 3. Toast notifications (using sonner)
import { toast } from "sonner";

async function deleteProduct(id: string) {
  try {
    await api.delete(`/products/${id}`);
    toast.success("Product deleted");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      toast.error("Product not found");
    } else {
      toast.error("Failed to delete product");
    }
  }
}

// 4. Global error handler in layout
// app/global-error.tsx — catches errors in root layout
"use client";
export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <html><body>
      <h1>Application Error</h1>
      <button onClick={reset}>Retry</button>
    </body></html>
  );
}
```

## Quick Reference

| Error Type | Handler | User Feedback |
|-----------|---------|---------------|
| Render crash | error.tsx / Error Boundary | Fallback UI + retry |
| API 4xx | Fetch wrapper | Toast or inline message |
| API 5xx | Fetch wrapper | Toast + retry |
| Network | Fetch wrapper | Offline banner |
| Form validation | Form library | Inline field errors |
| Not found | not-found.tsx | 404 page |

## Common Mistakes

### Wrong

```tsx
try { await api.post(data); } catch (e) { /* silently ignored */ }
```

### Correct

```tsx
try { await api.post(data); toast.success("Saved"); }
catch (e) { toast.error(e instanceof ApiError ? e.message : "Unexpected error"); }
```

## Related

- [api-integration.md](../patterns/api-integration.md)
- [project-structure.md](../concepts/project-structure.md)

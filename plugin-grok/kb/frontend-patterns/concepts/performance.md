# Performance

> **Purpose**: Code splitting, lazy loading, memoization, Core Web Vitals
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Frontend performance is measured by Core Web Vitals: LCP (loading), INP (interactivity), CLS (visual stability). Optimize with code splitting, lazy loading, memoization, and image optimization. Measure first, optimize second.

## The Concept

```tsx
// 1. Dynamic import — code split heavy components
import dynamic from "next/dynamic";

const Chart = dynamic(() => import("@/components/chart"), {
  loading: () => <Skeleton className="h-64" />,
  ssr: false, // Client-only (uses canvas)
});

// 2. React.lazy + Suspense — manual code split
import { lazy, Suspense } from "react";
const HeavyEditor = lazy(() => import("./heavy-editor"));

function Page() {
  return (
    <Suspense fallback={<Skeleton />}>
      <HeavyEditor />
    </Suspense>
  );
}

// 3. useMemo — expensive computation
const sortedItems = useMemo(
  () => items.sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);

// 4. Virtualization — long lists
import { useVirtualizer } from "@tanstack/react-virtual";

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} className="h-[400px] overflow-auto">
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((row) => (
          <div key={row.key} style={{ transform: `translateY(${row.start}px)` }}>
            {items[row.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Quick Reference

| Metric | Target | How to Improve |
|--------|--------|----------------|
| LCP | < 2.5s | Optimize images, preload fonts, SSR |
| INP | < 200ms | Reduce JS, useTransition, debounce |
| CLS | < 0.1 | Set image dimensions, avoid layout shifts |
| Bundle | < 100KB first load | Code split, tree shake, dynamic imports |

## Common Mistakes

### Wrong

```tsx
// Import heavy lib at top level
import { Chart } from "chart.js"; // 200KB in initial bundle
```

### Correct

```tsx
// Dynamic import — loads only when component renders
const Chart = dynamic(() => import("./chart"), { ssr: false });
```

## Related

- [project-structure.md](../concepts/project-structure.md)
- [api-integration.md](../patterns/api-integration.md)

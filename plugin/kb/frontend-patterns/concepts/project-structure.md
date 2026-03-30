# Project Structure

> **Purpose**: Feature-based organization, barrel exports, file colocation
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Organize by feature, not by file type. Colocate related files (component + test + hook). Use barrel exports for clean imports. This scales better than flat `components/` folders as the project grows.

## The Concept

```text
src/
├── app/                      # Next.js App Router routes
│   ├── layout.tsx
│   ├── page.tsx
│   ├── dashboard/
│   │   ├── page.tsx
│   │   └── loading.tsx
│   └── api/
│       └── products/route.ts
├── components/
│   ├── ui/                   # Design system primitives (shadcn)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   └── dialog.tsx
│   └── product/              # Feature components
│       ├── product-card.tsx
│       ├── product-card.test.tsx
│       ├── product-grid.tsx
│       ├── use-product-filter.ts
│       └── index.ts          # Barrel export
├── lib/
│   ├── utils.ts              # cn(), formatDate, etc.
│   ├── api.ts                # Fetch wrapper
│   └── validations.ts        # Zod schemas
├── hooks/
│   └── use-debounce.ts       # Shared custom hooks
└── types/
    └── api.ts                # Shared TypeScript types
```

```tsx
// components/product/index.ts — barrel export
export { ProductCard } from "./product-card";
export { ProductGrid } from "./product-grid";
export { useProductFilter } from "./use-product-filter";

// Consumer imports cleanly
import { ProductCard, ProductGrid } from "@/components/product";
```

## Quick Reference

| Directory | Contains | Rule |
|-----------|----------|------|
| `app/` | Routes only | No business logic |
| `components/ui/` | Design system | shadcn primitives |
| `components/{feature}/` | Feature components | Colocate tests |
| `lib/` | Utilities | Pure functions |
| `hooks/` | Shared hooks | Cross-feature |
| `types/` | Shared types | API contracts |

## Common Mistakes

### Wrong

```text
components/
  Button.tsx
  ProductCard.tsx
  ProductGrid.tsx
  UserAvatar.tsx
  OrderTable.tsx
  ... 50 more files in flat folder
```

### Correct

```text
components/
  ui/button.tsx
  product/product-card.tsx
  product/product-grid.tsx
  user/user-avatar.tsx
  order/order-table.tsx
```

## Related

- [error-handling.md](../concepts/error-handling.md)
- [performance.md](../concepts/performance.md)

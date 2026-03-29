# Utility-First CSS

> **Purpose**: Understand the utility-first philosophy, when to extract components, and why @apply is discouraged
> **Confidence**: 0.95
> **MCP Validated:** 2026-03-29

## Overview

Utility-first CSS composes small, single-purpose classes directly in markup instead of writing custom CSS. Tailwind's Just-in-Time (JIT) engine generates only the classes you use, producing tiny production bundles. This approach eliminates naming fatigue, dead CSS, and specificity wars while keeping styles colocated with the markup they affect.

## The Concept

```tsx
// Utility-first: styles live in the markup
function ProductCard({ name, price, image }: ProductCardProps) {
  return (
    <div className="group relative rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-lg">
      <img
        src={image}
        alt={name}
        className="aspect-square w-full rounded-xl object-cover"
      />
      <div className="mt-4 space-y-1">
        <h3 className="text-sm font-medium text-gray-900 group-hover:text-blue-600">
          {name}
        </h3>
        <p className="text-lg font-semibold text-gray-700">
          ${price.toFixed(2)}
        </p>
      </div>
    </div>
  );
}
```

```tsx
// JIT: arbitrary values when design tokens don't fit
<div className="top-[117px] grid grid-cols-[1fr_2fr_1fr] bg-[#1da1f2]">
  {/* JIT generates these classes on demand — zero bloat */}
</div>
```

## Quick Reference

| Approach | When to Use | Notes |
|----------|-------------|-------|
| Inline utilities | Default for all styling | Keeps styles colocated |
| Extract React component | Same utility combo used 3+ times | Reuse via props, not CSS |
| `@apply` in CSS | Almost never — only global prose styles | Defeats the purpose of utility-first |
| Arbitrary values `[...]` | One-off values outside design tokens | JIT generates on demand |
| `@layer components` | Third-party integration CSS | Keep scoped and minimal |

## Common Mistakes

### Wrong

```css
/* Extracting component classes with @apply — creates maintenance burden */
.btn-primary {
  @apply rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700;
}
```

### Correct

```tsx
// Extract a React component instead of a CSS class
function Button({ children, ...props }: ButtonProps) {
  return (
    <button
      className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700"
      {...props}
    >
      {children}
    </button>
  );
}
```

## When @apply Is Acceptable

```css
/* Global prose/markdown content where you cannot control markup */
@layer base {
  .prose h2 {
    @apply mt-8 text-2xl font-bold text-gray-900;
  }
  .prose p {
    @apply mt-4 leading-7 text-gray-600;
  }
}
```

## Related

- [Design Tokens](../concepts/design-tokens.md)
- [Component Styling](../patterns/component-styling.md)
- [cn() Utility](../patterns/cn-utility.md)

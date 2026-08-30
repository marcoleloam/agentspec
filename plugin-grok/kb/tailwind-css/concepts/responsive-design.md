# Responsive Design

> **Purpose**: Mobile-first breakpoints, container queries, and fluid typography with Tailwind
> **Confidence**: 0.95
> **MCP Validated:** 2026-03-29

## Overview

Tailwind uses a mobile-first breakpoint system where unprefixed utilities apply to all screens and prefixed utilities (`sm:`, `md:`, `lg:`, `xl:`) apply at that breakpoint and above. Container queries (`@container`) let components respond to their parent's size instead of the viewport. Fluid typography with `clamp()` avoids breakpoint jumps for text sizing.

## The Concept

```tsx
// Mobile-first: base styles for mobile, overrides for larger screens
function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col lg:flex-row">
      {/* Sidebar: hidden on mobile, fixed width on desktop */}
      <aside className="hidden lg:block lg:w-64 lg:shrink-0">
        <Nav />
      </aside>

      {/* Main: full width on mobile, flexible on desktop */}
      <main className="min-w-0 flex-1 p-4 md:p-6 xl:p-8">
        {/* Grid: 1 col mobile, 2 cols tablet, 3 cols desktop */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {children}
        </div>
      </main>
    </div>
  );
}
```

```tsx
// Container queries: component responds to parent size
function CardGrid() {
  return (
    <div className="@container">
      <div className="grid grid-cols-1 @sm:grid-cols-2 @lg:grid-cols-3 gap-4">
        <Card />
        <Card />
        <Card />
      </div>
    </div>
  );
}
```

## Quick Reference

| Breakpoint | Min-Width | CSS | Target |
|------------|-----------|-----|--------|
| (default) | 0px | No media query | Mobile |
| `sm:` | 640px | `@media (min-width: 640px)` | Large phones |
| `md:` | 768px | `@media (min-width: 768px)` | Tablets |
| `lg:` | 1024px | `@media (min-width: 1024px)` | Laptops |
| `xl:` | 1280px | `@media (min-width: 1280px)` | Desktops |
| `2xl:` | 1536px | `@media (min-width: 1536px)` | Large screens |
| `@sm:` | 20rem container | `@container (min-width: 20rem)` | Container query |
| `@lg:` | 32rem container | `@container (min-width: 32rem)` | Container query |

## Common Mistakes

### Wrong

```tsx
{/* Desktop-first: hides on small screens — wrong mental model */}
<div className="grid grid-cols-3 sm:grid-cols-1">
  {/* sm: means 640px AND UP, not "small screens only" */}
</div>
```

### Correct

```tsx
{/* Mobile-first: starts with 1 column, grows at breakpoints */}
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
  {/* Each prefix adds behavior at that size and above */}
</div>
```

## Fluid Typography with clamp()

```typescript
// tailwind.config.ts — fluid type scale
extend: {
  fontSize: {
    "fluid-sm": "clamp(0.875rem, 0.8rem + 0.25vw, 1rem)",
    "fluid-base": "clamp(1rem, 0.9rem + 0.5vw, 1.25rem)",
    "fluid-lg": "clamp(1.25rem, 1rem + 1vw, 2rem)",
    "fluid-xl": "clamp(1.5rem, 1rem + 2vw, 3rem)",
  },
}
```

```tsx
<h1 className="text-fluid-xl font-bold">Scales smoothly</h1>
<p className="text-fluid-base">No breakpoint jumps in text size.</p>
```

## Related

- [Design Tokens](../concepts/design-tokens.md)
- [Component Styling](../patterns/component-styling.md)
- [Utility-First](../concepts/utility-first.md)

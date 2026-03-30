# Tailwind CSS Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Spacing Scale

| Class | Value | Pixels |
|-------|-------|--------|
| `p-0` | 0 | 0px |
| `p-1` | 0.25rem | 4px |
| `p-2` | 0.5rem | 8px |
| `p-3` | 0.75rem | 12px |
| `p-4` | 1rem | 16px |
| `p-6` | 1.5rem | 24px |
| `p-8` | 2rem | 32px |
| `p-12` | 3rem | 48px |
| `p-16` | 4rem | 64px |

## Breakpoints

| Prefix | Min Width | Target |
|--------|-----------|--------|
| (none) | 0px | Mobile (default) |
| `sm:` | 640px | Large phones |
| `md:` | 768px | Tablets |
| `lg:` | 1024px | Laptops |
| `xl:` | 1280px | Desktops |
| `2xl:` | 1536px | Large screens |

## Common Patterns

| Pattern | Classes |
|---------|---------|
| Center content | `flex items-center justify-center` |
| Stack vertical | `flex flex-col gap-4` |
| Grid 3 cols | `grid grid-cols-3 gap-4` |
| Responsive grid | `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4` |
| Card | `rounded-lg border bg-card p-6 shadow-sm` |
| Truncate text | `truncate` or `line-clamp-2` |
| Visually hidden | `sr-only` |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| One-off style | Utility classes in markup |
| Repeated pattern (3+ times) | Extract component or use cn() |
| Complex animation | `@keyframes` in CSS + Tailwind `animate-*` |
| Theme colors | Semantic tokens in tailwind.config |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `w-[347px]` when token exists | `w-96` (384px) or nearest token |
| `@apply` in global CSS | `cn()` in components |
| Desktop-first (`lg:hidden`) | Mobile-first (`hidden lg:block`) |
| Hardcoded colors `text-[#1a1a1a]` | Semantic tokens `text-foreground` |
| Inline styles for spacing | Tailwind spacing utilities |

# Design Systems Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Token Tiers

| Tier | Example | Purpose |
|------|---------|---------|
| Primitive | `blue-500: #3b82f6` | Raw value, never used directly |
| Semantic | `--primary: var(--blue-500)` | Purpose-based, theme-aware |
| Component | `--button-bg: var(--primary)` | Component-specific binding |

## Component Variant Types (cva)

| Type | Example | Use Case |
|------|---------|----------|
| Variant | `variant: "default" \| "destructive"` | Visual style |
| Size | `size: "sm" \| "md" \| "lg"` | Dimensions |
| Compound | `variant: "destructive" + size: "lg"` → extra styles | Conditional combos |
| Default | `defaultVariants: { variant: "default", size: "md" }` | Fallback values |

## shadcn/ui Component Structure

| File | Purpose |
|------|---------|
| `components/ui/button.tsx` | Base component with cva variants |
| `components/ui/dialog.tsx` | Radix Dialog primitive + custom styling |
| `lib/utils.ts` | cn() utility (clsx + twMerge) |
| `tailwind.config.ts` | Design tokens, custom colors |
| `globals.css` | CSS custom properties for theming |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Simple variant (color, size) | cva directly |
| Complex interactive widget | Radix primitive + custom styling |
| Full design system | shadcn/ui as foundation, customize |
| One-off styled component | Tailwind classes + cn() |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Hardcode colors in components | Use semantic tokens from config |
| Create variants without types | Export `VariantProps<typeof cva>` |
| Override shadcn internals | Extend via className prop and cn() |
| Mix styling approaches | Pick one: Tailwind + cva consistently |

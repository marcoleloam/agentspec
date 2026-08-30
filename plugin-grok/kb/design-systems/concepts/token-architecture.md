# Token Architecture

> **Purpose**: Three-tier design tokens — primitive → semantic → component
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Design tokens are the atomic values of a design system. A three-tier architecture separates raw values (primitive) from meaning (semantic) and usage (component), enabling themes and consistent design.

## The Concept

```css
/* Tier 1: Primitive tokens — raw values, never used in components */
:root {
  --blue-50: #eff6ff;
  --blue-500: #3b82f6;
  --blue-900: #1e3a5f;
  --gray-50: #f9fafb;
  --gray-900: #111827;
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
}

/* Tier 2: Semantic tokens — purpose-based, theme-aware */
:root {
  --background: var(--gray-50);
  --foreground: var(--gray-900);
  --primary: var(--blue-500);
  --primary-foreground: white;
  --muted: var(--gray-50);
  --border: var(--gray-200);
  --ring: var(--blue-500);
  --radius: var(--radius-md);
}

.dark {
  --background: var(--gray-900);
  --foreground: var(--gray-50);
  --primary: var(--blue-400);
  --muted: var(--gray-800);
  --border: var(--gray-700);
}

/* Tier 3: Component tokens — specific bindings */
:root {
  --button-bg: var(--primary);
  --button-text: var(--primary-foreground);
  --card-bg: var(--background);
  --card-border: var(--border);
  --input-border: var(--border);
  --input-ring: var(--ring);
}
```

## Quick Reference

| Tier | Example | Used By |
|------|---------|---------|
| Primitive | `--blue-500: #3b82f6` | Only semantic tokens |
| Semantic | `--primary: var(--blue-500)` | Component tokens or directly |
| Component | `--button-bg: var(--primary)` | Specific components |

## Common Mistakes

### Wrong

```tsx
// Hardcoded color — breaks in dark mode
<div className="bg-[#3b82f6]">...</div>
```

### Correct

```tsx
// Semantic token — adapts to theme
<div className="bg-primary">...</div>
```

## Related

- [component-api.md](../concepts/component-api.md)
- [variant-pattern.md](../patterns/variant-pattern.md)

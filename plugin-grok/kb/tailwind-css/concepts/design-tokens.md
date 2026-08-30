# Design Tokens

> **Purpose**: Configure colors, spacing, and typography in tailwind.config.ts with extend vs override strategies
> **Confidence**: 0.95
> **MCP Validated:** 2026-03-29

## Overview

Tailwind's configuration file is the single source of truth for design tokens. Using `extend` adds tokens alongside defaults; top-level keys replace them entirely. CSS custom properties bridge Tailwind tokens to non-Tailwind contexts. TypeScript config (`tailwind.config.ts`) provides autocomplete and type safety for all token definitions.

## The Concept

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    // Override: replaces ALL default screens
    screens: {
      sm: "640px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
    },
    extend: {
      // Extend: adds to defaults without removing them
      colors: {
        brand: {
          50: "#eff6ff",
          500: "#3b82f6",
          600: "#2563eb",
          900: "#1e3a8a",
        },
        // CSS custom property bridge
        surface: "var(--color-surface)",
        "on-surface": "var(--color-on-surface)",
      },
      spacing: {
        18: "4.5rem",
        88: "22rem",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.75rem" }],
      },
      borderRadius: {
        "4xl": "2rem",
      },
    },
  },
  plugins: [],
};

export default config;
```

## Quick Reference

| Strategy | Key Location | Effect | Use Case |
|----------|-------------|--------|----------|
| `theme.extend.colors` | Inside `extend` | Adds to defaults | Custom brand colors |
| `theme.colors` | Top-level | Replaces ALL colors | Strict design system |
| `theme.extend.spacing` | Inside `extend` | Adds custom spacing | Extra sizes |
| `theme.screens` | Top-level | Replaces breakpoints | Custom breakpoint set |
| CSS variable bridge | `var(--token)` | Dynamic runtime values | Theming, dark mode |

## Common Mistakes

### Wrong

```typescript
// Replaces ALL default colors — loses gray, red, blue, etc.
const config: Config = {
  theme: {
    colors: {
      brand: "#3b82f6",
    },
  },
};
```

### Correct

```typescript
// Extends default palette with brand colors
const config: Config = {
  theme: {
    extend: {
      colors: {
        brand: "#3b82f6",
      },
    },
  },
};
```

## CSS Custom Properties Bridge

```css
/* globals.css — define semantic tokens */
@layer base {
  :root {
    --color-surface: 255 255 255;
    --color-on-surface: 15 23 42;
  }
  .dark {
    --color-surface: 15 23 42;
    --color-on-surface: 248 250 252;
  }
}
```

```typescript
// tailwind.config.ts — consume with rgb() for opacity support
extend: {
  colors: {
    surface: "rgb(var(--color-surface) / <alpha-value>)",
    "on-surface": "rgb(var(--color-on-surface) / <alpha-value>)",
  },
}
```

## Related

- [Utility-First](../concepts/utility-first.md)
- [Responsive Design](../concepts/responsive-design.md)
- [Dark Mode](../patterns/dark-mode.md)
- [Token Architecture](../../design-systems/concepts/token-architecture.md)

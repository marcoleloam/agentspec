# Tailwind CSS Knowledge Base

> **Purpose**: Tailwind CSS utility-first patterns — design tokens, responsive design, dark mode, animations
> **MCP Validated**: 2026-03-29

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/utility-first.md](concepts/utility-first.md) | Philosophy, when to extract, @apply debate |
| [concepts/design-tokens.md](concepts/design-tokens.md) | Colors, spacing, typography in config |
| [concepts/responsive-design.md](concepts/responsive-design.md) | Breakpoints, mobile-first, container queries |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/component-styling.md](patterns/component-styling.md) | Card, button, modal, table patterns |
| [patterns/dark-mode.md](patterns/dark-mode.md) | Class-based dark mode, next-themes |
| [patterns/animations.md](patterns/animations.md) | Transitions, keyframes, motion presets |
| [patterns/cn-utility.md](patterns/cn-utility.md) | clsx + tailwind-merge for conditional classes |

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Utility-First** | Apply small, single-purpose classes directly in markup |
| **Design Tokens** | Configure colors, spacing, fonts in tailwind.config |
| **Responsive** | Mobile-first breakpoints: sm (640), md (768), lg (1024), xl (1280) |
| **Dark Mode** | Class-based toggle with `dark:` variant |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| css-specialist | All files | Styling, tokens, responsive, dark mode |
| react-developer | patterns/component-styling.md | Component class application |

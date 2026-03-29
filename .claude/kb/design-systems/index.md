# Design Systems Knowledge Base

> **Purpose**: Design system architecture — token tiers, component APIs, variants, theming
> **MCP Validated**: 2026-03-29

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/token-architecture.md](concepts/token-architecture.md) | Primitive → semantic → component tokens |
| [concepts/component-api.md](concepts/component-api.md) | Props, slots, composition, polymorphic |
| [concepts/documentation.md](concepts/documentation.md) | Storybook, MDX, playground |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/variant-pattern.md](patterns/variant-pattern.md) | cva, compound variants, typed props |
| [patterns/shadcn-patterns.md](patterns/shadcn-patterns.md) | shadcn/ui customization, Radix primitives |
| [patterns/theme-switching.md](patterns/theme-switching.md) | next-themes, CSS variables, system preference |

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Token Tiers** | Primitive (raw values) → Semantic (purpose) → Component (specific use) |
| **Variants** | Named style variations via class-variance-authority (cva) |
| **Composition** | Build complex components from primitive building blocks |
| **Theming** | CSS custom properties + class-based dark mode switching |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| css-specialist | All files | Design system implementation |
| ux-designer | concepts/component-api.md | Component API design decisions |

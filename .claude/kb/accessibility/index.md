# Accessibility Knowledge Base

> **Purpose**: Web accessibility patterns — WCAG 2.1 AA, aria attributes, keyboard navigation, screen readers
> **MCP Validated**: 2026-03-29

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/wcag-guidelines.md](concepts/wcag-guidelines.md) | WCAG 2.1 AA principles and key criteria |
| [concepts/aria-patterns.md](concepts/aria-patterns.md) | Roles, states, properties, live regions |
| [concepts/keyboard-navigation.md](concepts/keyboard-navigation.md) | Tab order, focus management, skip links |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/form-accessibility.md](patterns/form-accessibility.md) | Labels, errors, required fields, fieldsets |
| [patterns/modal-dialog.md](patterns/modal-dialog.md) | Focus trap, escape, aria-modal, return focus |
| [patterns/table-accessibility.md](patterns/table-accessibility.md) | th scope, caption, headers, sortable columns |

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **POUR** | Perceivable, Operable, Understandable, Robust — four WCAG principles |
| **ARIA** | Accessible Rich Internet Applications — roles, states, properties for dynamic content |
| **Focus Management** | Tab order, focus trap for modals, visible focus indicators |
| **Semantic HTML** | Use native elements (`button`, `nav`, `main`) before ARIA attributes |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| a11y-specialist | All files | Accessibility audit, compliance, fixes |
| react-developer | patterns/form-accessibility.md | Accessible form implementation |

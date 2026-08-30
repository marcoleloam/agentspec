# Accessibility Quick Reference

> Fast lookup tables. For code examples, see linked files.

## WCAG 2.1 AA Key Criteria

| Criterion | Requirement | Test |
|-----------|-------------|------|
| 1.1.1 Non-text Content | All images have alt text | Check every `<img>` for alt attribute |
| 1.4.3 Contrast Minimum | Text ≥ 4.5:1, large text ≥ 3:1 | Use contrast checker tool |
| 2.1.1 Keyboard | All functionality via keyboard | Tab through entire page |
| 2.4.7 Focus Visible | Visible focus indicator | Tab and check focus ring |
| 3.3.2 Labels | All inputs have labels | Check every form field |
| 4.1.2 Name, Role, Value | Custom widgets have aria attributes | Inspect with screen reader |

## ARIA Roles Cheat Sheet

| Role | Use For | Native Alternative |
|------|---------|-------------------|
| `role="button"` | Clickable non-button | Use `<button>` instead |
| `role="dialog"` | Modal/popup | Use `<dialog>` element |
| `role="navigation"` | Nav section | Use `<nav>` instead |
| `role="alert"` | Important message | Dynamic status updates |
| `role="tab"` | Tab interface | Part of tablist pattern |
| `role="status"` | Non-urgent update | Live region for status |

## Keyboard Shortcuts

| Key | Expected Behavior |
|-----|-------------------|
| Tab | Move to next focusable element |
| Shift+Tab | Move to previous focusable element |
| Enter/Space | Activate button/link |
| Escape | Close modal/dropdown |
| Arrow keys | Navigate within widget (tabs, menu, grid) |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `<div onClick>` for buttons | `<button onClick>` |
| `outline: none` on focus | Custom `:focus-visible` styles |
| Color as only indicator | Add icon, text, or pattern |
| Skip heading levels (h1→h3) | Sequential h1→h2→h3 |
| `aria-label` on visible text | Use `aria-labelledby` |
| Empty alt on informative images | Descriptive alt text |
| Missing form labels | Visible `<label htmlFor>` |

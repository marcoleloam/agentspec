# ARIA Patterns

> **Purpose**: aria-label, aria-labelledby, aria-describedby, roles, live regions
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

ARIA (Accessible Rich Internet Applications) provides attributes that make dynamic content accessible. The first rule of ARIA: don't use ARIA if a native HTML element does the job. Use ARIA only for custom widgets that lack native semantics.

## The Concept

```tsx
// aria-label — names an element (no visible text)
<button aria-label="Close dialog">
  <XIcon />
</button>

// aria-labelledby — points to visible text element
<h2 id="dialog-title">Edit Profile</h2>
<div role="dialog" aria-labelledby="dialog-title">...</div>

// aria-describedby — links to description/help text
<input
  id="email"
  aria-describedby="email-hint email-error"
/>
<p id="email-hint">We'll never share your email.</p>
<p id="email-error" role="alert">Email is required.</p>

// aria-expanded — toggle state
<button aria-expanded={isOpen} aria-controls="menu">
  Menu
</button>
<ul id="menu" hidden={!isOpen}>...</ul>

// aria-live — announce dynamic updates
<div aria-live="polite">  {/* screen reader announces changes */}
  {message && <p>{message}</p>}
</div>

// role — when native element isn't available
<div role="tablist">
  <button role="tab" aria-selected={active === 0}>Tab 1</button>
  <button role="tab" aria-selected={active === 1}>Tab 2</button>
</div>
<div role="tabpanel">...</div>
```

## Quick Reference

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `aria-label` | Name (no visible text) | Icon buttons |
| `aria-labelledby` | Name (points to element) | Dialog titles |
| `aria-describedby` | Description | Error messages, hints |
| `aria-expanded` | Open/closed state | Dropdowns, accordions |
| `aria-hidden="true"` | Hide from AT | Decorative icons |
| `aria-live` | Announce changes | Toast, status updates |
| `role` | Semantic role | Custom widgets |

## Common Mistakes

### Wrong

```tsx
// ARIA where native element works
<div role="button" tabIndex={0} onClick={handleClick}>Click</div>
```

### Correct

```tsx
// Use native element
<button onClick={handleClick}>Click</button>
```

## Related

- [wcag-guidelines.md](../concepts/wcag-guidelines.md)
- [form-accessibility.md](../patterns/form-accessibility.md)

# Keyboard Navigation

> **Purpose**: Tab order, focus management, focus trap, skip links
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

All interactive content must be operable via keyboard. Tab moves between focusable elements. Enter/Space activates buttons. Escape closes overlays. Focus must be visible and logically ordered.

## The Concept

```tsx
// Skip link — first focusable element on page
<a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:p-2">
  Skip to main content
</a>
<main id="main-content">...</main>

// Focus trap for modals — keep focus inside
import { useEffect, useRef } from "react";

function useFocusTrap(isOpen: boolean) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !ref.current) return;

    const focusable = ref.current.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    first?.focus();

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key !== "Tab") return;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first?.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  return ref;
}

// Visible focus indicators — never remove outline without replacement
// globals.css:
// :focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; }
```

## Quick Reference

| Key | Expected Behavior |
|-----|-------------------|
| Tab | Next focusable element |
| Shift+Tab | Previous focusable element |
| Enter | Activate button/link |
| Space | Activate button, toggle checkbox |
| Escape | Close modal/dropdown/tooltip |
| Arrow keys | Navigate within widget (tabs, menu) |

| tabIndex | Behavior |
|----------|----------|
| `0` | Focusable in natural DOM order |
| `-1` | Focusable via JS only (not Tab) |
| `>0` | Avoid — breaks natural order |

## Common Mistakes

### Wrong

```css
/* Removes focus for ALL users */
*:focus { outline: none; }
```

### Correct

```css
/* Custom focus only when keyboard navigating */
:focus-visible { outline: 2px solid hsl(var(--ring)); outline-offset: 2px; }
```

## Related

- [modal-dialog.md](../patterns/modal-dialog.md)
- [wcag-guidelines.md](../concepts/wcag-guidelines.md)

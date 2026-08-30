# WCAG Guidelines

> **Purpose**: WCAG 2.1 AA principles and key success criteria
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

WCAG (Web Content Accessibility Guidelines) 2.1 AA is the standard for web accessibility. It's organized around four principles: Perceivable, Operable, Understandable, Robust (POUR).

## The Concept

```text
POUR Principles:

1. PERCEIVABLE — Users can perceive the content
   ├── 1.1.1 Non-text Content: Images have alt text
   ├── 1.3.1 Info and Relationships: Semantic HTML structure
   ├── 1.4.1 Use of Color: Not the only visual means
   ├── 1.4.3 Contrast Minimum: Text ≥ 4.5:1, large text ≥ 3:1
   └── 1.4.4 Resize Text: Usable at 200% zoom

2. OPERABLE — Users can navigate and interact
   ├── 2.1.1 Keyboard: All functionality via keyboard
   ├── 2.4.1 Bypass Blocks: Skip navigation link
   ├── 2.4.3 Focus Order: Logical tab sequence
   ├── 2.4.6 Headings and Labels: Descriptive headings
   └── 2.4.7 Focus Visible: Visible focus indicator

3. UNDERSTANDABLE — Users can understand content
   ├── 3.1.1 Language of Page: html lang attribute
   ├── 3.2.1 On Focus: No unexpected changes on focus
   ├── 3.3.1 Error Identification: Describe errors in text
   └── 3.3.2 Labels or Instructions: Form fields have labels

4. ROBUST — Content works with assistive technology
   ├── 4.1.1 Parsing: Valid HTML
   └── 4.1.2 Name, Role, Value: Custom widgets have ARIA
```

## Quick Reference

| Criterion | Requirement | Quick Test |
|-----------|-------------|------------|
| 1.1.1 | Alt text on images | Check every `<img>` |
| 1.4.3 | Contrast ≥ 4.5:1 | Browser contrast checker |
| 2.1.1 | Keyboard accessible | Tab through entire page |
| 2.4.7 | Visible focus | Tab and look for focus ring |
| 3.3.2 | Form labels | Every input has `<label>` |

## Common Mistakes

### Wrong

```html
<!-- Color as only indicator -->
<span style="color: red;">Error</span>
```

### Correct

```html
<!-- Color + icon + text -->
<span class="text-red-500 flex items-center gap-1">
  <svg aria-hidden="true"><!-- error icon --></svg>
  Error: Email is required
</span>
```

## Related

- [aria-patterns.md](../concepts/aria-patterns.md)
- [keyboard-navigation.md](../concepts/keyboard-navigation.md)

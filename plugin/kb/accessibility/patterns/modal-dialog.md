# Modal Dialog Accessibility

> **Purpose**: Focus trap, escape to close, aria-modal, return focus
> **MCP Validated**: 2026-03-29

## When to Use

- Modal dialogs, confirmation prompts
- Any overlay that requires user attention

## Implementation

```tsx
"use client";
import { useEffect, useRef } from "react";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

function Dialog({ open, onClose, title, children }: DialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (open) {
      // Save trigger element to return focus later
      triggerRef.current = document.activeElement as HTMLElement;
      dialogRef.current?.showModal();
    } else {
      dialogRef.current?.close();
      // Return focus to trigger element
      triggerRef.current?.focus();
    }
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby="dialog-title"
      aria-modal="true"
      onClose={onClose}
      onClick={(e) => {
        // Close on backdrop click
        if (e.target === dialogRef.current) onClose();
      }}
      className="rounded-lg p-0 backdrop:bg-black/50"
    >
      <div className="p-6">
        <header className="flex items-center justify-between mb-4">
          <h2 id="dialog-title">{title}</h2>
          <button onClick={onClose} aria-label="Close dialog">
            &times;
          </button>
        </header>
        {children}
      </div>
    </dialog>
  );
}
```

## Configuration

| Requirement | Implementation |
|-------------|---------------|
| Focus trap | Native `<dialog>` handles it |
| Escape to close | Native `<dialog>` `onClose` event |
| `aria-modal` | Prevents AT from leaving dialog |
| `aria-labelledby` | Points to dialog title |
| Return focus | Save and restore `activeElement` |
| Backdrop click | Check `e.target === dialogRef` |

## See Also

- [keyboard-navigation.md](../concepts/keyboard-navigation.md)
- [aria-patterns.md](../concepts/aria-patterns.md)

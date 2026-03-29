# shadcn/ui Patterns

> **Purpose**: Copy-paste components, Radix primitives, customization patterns
> **MCP Validated**: 2026-03-29

## When to Use

- Starting a new project with a component library
- Needing accessible, unstyled primitives (Radix)
- Customizing components without fighting a library

## Implementation

```bash
# Initialize shadcn/ui
npx shadcn@latest init

# Add individual components
npx shadcn@latest add button dialog card input table
```

```tsx
// Customizing a shadcn component — extend via className
import { Button } from "@/components/ui/button";

// Consumer uses it with overrides
<Button variant="outline" className="rounded-full">
  Pill Button
</Button>

// Adding a new variant — edit the component directly
// components/ui/button.tsx
const buttonVariants = cva("...", {
  variants: {
    variant: {
      // ... existing variants
      gradient: "bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:opacity-90",
    },
  },
});

// Composing Radix primitives — Dialog example
import * as DialogPrimitive from "@radix-ui/react-dialog";

const Dialog = DialogPrimitive.Root;
const DialogTrigger = DialogPrimitive.Trigger;

const DialogContent = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="fixed inset-0 bg-black/50" />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
        "w-full max-w-lg rounded-lg bg-background p-6 shadow-lg",
        className
      )}
      {...props}
    >
      {children}
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
));
```

## Configuration

| File | Purpose |
|------|---------|
| `components.json` | shadcn config (style, paths, aliases) |
| `components/ui/` | Generated components (editable) |
| `lib/utils.ts` | cn() utility |
| `globals.css` | CSS variables for theming |
| `tailwind.config.ts` | Design tokens |

## See Also

- [variant-pattern.md](../patterns/variant-pattern.md)
- [theme-switching.md](../patterns/theme-switching.md)

# Variant Pattern (cva)

> **Purpose**: class-variance-authority for typed component variants
> **MCP Validated**: 2026-03-29

## When to Use

- Components with multiple visual styles (variant, size)
- Type-safe variant props exported from component
- Composing with cn() for className overrides

## Implementation

```tsx
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  // Base classes — always applied
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 rounded-md px-3 text-xs",
        md: "h-10 px-4 py-2",
        lg: "h-12 rounded-md px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    // Compound variants — conditional combos
    compoundVariants: [
      {
        variant: "destructive",
        size: "lg",
        className: "font-bold uppercase",
      },
    ],
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

// Export variant types for consumer
export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    className?: string;
  };

function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}
```

## Configuration

| Setting | Purpose |
|---------|---------|
| Base string | Classes always applied |
| `variants` | Named variant groups |
| `compoundVariants` | Styles for specific combinations |
| `defaultVariants` | Fallback when prop not provided |

## See Also

- [cn-utility.md](../../tailwind-css/patterns/cn-utility.md)
- [component-api.md](../concepts/component-api.md)

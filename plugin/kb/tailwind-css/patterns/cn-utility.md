# cn() Utility

> **Purpose**: clsx + tailwind-merge for conditional and conflict-free class merging
> **MCP Validated**: 2026-03-29

## When to Use

- Merging conditional Tailwind classes without conflicts
- Building component APIs that accept className prop
- Composing variant classes with overrides

## Implementation

```tsx
// lib/utils.ts — the cn() function
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Why both? clsx handles conditionals, twMerge resolves conflicts
cn("px-4 py-2", "px-6");           // → "px-6 py-2" (twMerge dedupes)
cn("text-red-500", false && "hidden"); // → "text-red-500" (clsx filters)

// Component with className override
interface CardProps {
  className?: string;
  children: React.ReactNode;
}

function Card({ className, children }: CardProps) {
  return (
    <div className={cn("rounded-lg border bg-card p-6 shadow-sm", className)}>
      {children}
    </div>
  );
}

// Consumer can override any default
<Card className="p-4 shadow-lg">   // p-4 overrides p-6, shadow-lg overrides shadow-sm
  Content
</Card>

// With cva variants
import { cva, type VariantProps } from "class-variance-authority";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        success: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
        warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
        error: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

type BadgeProps = VariantProps<typeof badgeVariants> & { className?: string };

function Badge({ variant, className }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} />;
}
```

## Configuration

| Package | Purpose | Install |
|---------|---------|---------|
| `clsx` | Conditional class joining | `npm i clsx` |
| `tailwind-merge` | Resolve Tailwind conflicts | `npm i tailwind-merge` |
| `class-variance-authority` | Typed variants | `npm i class-variance-authority` |

## See Also

- [component-styling.md](../patterns/component-styling.md)
- [variant-pattern.md](../../design-systems/patterns/variant-pattern.md)

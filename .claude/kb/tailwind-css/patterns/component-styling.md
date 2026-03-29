# Component Styling

> **Purpose**: Tailwind patterns for common UI components — card, button, input, table
> **MCP Validated**: 2026-03-29

## When to Use

- Building consistent UI components with Tailwind
- Following design system patterns across the project
- Creating reusable styled components

## Implementation

```tsx
// Card
function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      {children}
    </div>
  );
}

// Button with variants using cn()
import { cn } from "@/lib/utils";

function Button({
  variant = "default",
  size = "md",
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "disabled:pointer-events-none disabled:opacity-50",
        variant === "default" && "bg-primary text-primary-foreground hover:bg-primary/90",
        variant === "outline" && "border border-input bg-background hover:bg-accent",
        variant === "ghost" && "hover:bg-accent hover:text-accent-foreground",
        size === "sm" && "h-8 px-3 text-sm",
        size === "md" && "h-10 px-4",
        size === "lg" && "h-12 px-6 text-lg",
        className
      )}
      {...props}
    />
  );
}

// Input
function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
        "placeholder:text-muted-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}
```

## See Also

- [cn-utility.md](../patterns/cn-utility.md)
- [dark-mode.md](../patterns/dark-mode.md)

# Component API Design

> **Purpose**: Props design, polymorphic components, forwardRef, compound components
> **Confidence**: 0.90
> **MCP Validated**: 2026-03-29

## Overview

Good component APIs are predictable, composable, and type-safe. Design system components should accept className for customization, use forwardRef for DOM access, and support polymorphic rendering with the `as` prop.

## The Concept

```tsx
import { forwardRef, type ComponentPropsWithoutRef, type ElementType } from "react";
import { cn } from "@/lib/utils";

// 1. Basic component with className override
interface CardProps extends ComponentPropsWithoutRef<"div"> {
  variant?: "default" | "outline";
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg p-6",
        variant === "default" && "bg-card shadow-sm border",
        variant === "outline" && "border-2",
        className
      )}
      {...props}
    />
  )
);
Card.displayName = "Card";

// 2. Polymorphic component — render as any element
type PolymorphicProps<T extends ElementType> = {
  as?: T;
  children: React.ReactNode;
} & ComponentPropsWithoutRef<T>;

function Text<T extends ElementType = "p">({
  as,
  className,
  ...props
}: PolymorphicProps<T>) {
  const Component = as || "p";
  return <Component className={cn("text-foreground", className)} {...props} />;
}

// Usage: <Text as="h1" className="text-2xl">Title</Text>
//        <Text as="span" className="text-sm">Subtitle</Text>

// 3. Compound component — Accordion.Item pattern
// See react/patterns/component-composition.md for full example
```

## Quick Reference

| Pattern | When | Example |
|---------|------|---------|
| `className` prop | Always | Every DS component |
| `forwardRef` | DOM access needed | Input, Button, Dialog |
| Polymorphic `as` | Render as different element | Text, Box, Container |
| Compound | Parent-child relationship | Accordion, Tabs, Select |
| Slot (children) | Flexible content | Card.Header, Card.Body |

## Common Mistakes

### Wrong

```tsx
// No className — can't customize
function Badge({ label }: { label: string }) {
  return <span className="bg-primary px-2">{label}</span>;
}
```

### Correct

```tsx
// className prop + cn() for merge
function Badge({ label, className }: { label: string; className?: string }) {
  return <span className={cn("bg-primary px-2", className)}>{label}</span>;
}
```

## Related

- [token-architecture.md](../concepts/token-architecture.md)
- [variant-pattern.md](../patterns/variant-pattern.md)

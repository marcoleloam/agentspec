# Animations

> **Purpose**: Tailwind transitions, custom keyframes, motion presets, reduced motion
> **MCP Validated**: 2026-03-29

## When to Use

- Adding entrance animations to page elements
- Hover/focus transitions on interactive elements
- Respecting prefers-reduced-motion for accessibility

## Implementation

```tsx
// Built-in transitions
<button className="transition-colors duration-200 hover:bg-primary/90">
  Hover me
</button>

<div className="transition-transform duration-300 hover:scale-105">
  Scale on hover
</div>

// Built-in animations
<div className="animate-spin" />     // Loading spinner
<div className="animate-pulse" />    // Skeleton loading
<div className="animate-bounce" />   // Attention bounce

// Custom keyframes — tailwind.config.ts
const config = {
  theme: {
    extend: {
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.3s ease-out",
        "slide-in": "slide-in 0.2s ease-out",
      },
    },
  },
};

// Usage with custom animations
<div className="animate-fade-up">Fades up on mount</div>

// Staggered entrance — using style for delay
{items.map((item, i) => (
  <div
    key={item.id}
    className="animate-fade-up"
    style={{ animationDelay: `${i * 50}ms`, animationFillMode: "both" }}
  >
    {item.name}
  </div>
))}

// Respect reduced motion
<div className="motion-safe:animate-fade-up motion-reduce:opacity-100">
  Animates only if user allows motion
</div>
```

## See Also

- [component-styling.md](../patterns/component-styling.md)
- [responsive-design.md](../concepts/responsive-design.md)

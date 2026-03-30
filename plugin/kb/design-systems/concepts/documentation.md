# Design System Documentation

> **Purpose**: Storybook, MDX docs, component playground, usage guidelines
> **Confidence**: 0.85
> **MCP Validated**: 2026-03-29

## Overview

Documentation makes a design system usable. Storybook provides interactive component previews. MDX combines markdown with live examples. Every component needs: description, props table, usage examples, and do/don't guidelines.

## The Concept

```tsx
// Button.stories.tsx — Storybook Component Story Format (CSF)
import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./button";

const meta: Meta<typeof Button> = {
  title: "UI/Button",
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "destructive", "outline", "ghost"],
    },
    size: {
      control: "select",
      options: ["sm", "md", "lg"],
    },
  },
};
export default meta;

type Story = StoryObj<typeof Button>;

export const Default: Story = {
  args: { children: "Button", variant: "default", size: "md" },
};

export const Destructive: Story = {
  args: { children: "Delete", variant: "destructive" },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex gap-4">
      <Button variant="default">Default</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
    </div>
  ),
};
```

## Quick Reference

| Tool | Purpose | Format |
|------|---------|--------|
| Storybook | Interactive previews | `.stories.tsx` (CSF) |
| MDX | Prose + live examples | `.mdx` files |
| TypeDoc | Auto API docs from types | Generated |
| Chromatic | Visual regression testing | CI integration |

| Doc Section | Content |
|-------------|---------|
| Description | What the component does |
| Props table | All props with types and defaults |
| Examples | Common usage patterns |
| Do / Don't | Correct vs incorrect usage |
| Accessibility | ARIA requirements |

## Common Mistakes

### Wrong

```tsx
// No stories — component only discovered by reading source
export function Badge({ variant, label }) { /* ... */ }
```

### Correct

```tsx
// Stories show all variants and states
export const Success: Story = { args: { variant: "success", label: "Active" } };
export const Warning: Story = { args: { variant: "warning", label: "Pending" } };
```

## Related

- [component-api.md](../concepts/component-api.md)
- [shadcn-patterns.md](../patterns/shadcn-patterns.md)

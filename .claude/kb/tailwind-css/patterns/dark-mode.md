# Dark Mode

> **Purpose**: Class-based dark mode with next-themes, semantic color tokens
> **MCP Validated**: 2026-03-29

## When to Use

- Adding dark/light theme toggle
- Defining semantic color tokens that work across themes
- Integrating with next-themes in Next.js

## Implementation

```tsx
// tailwind.config.ts
const config = {
  darkMode: "class", // class-based, not media
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        border: "hsl(var(--border))",
      },
    },
  },
};

// globals.css — define tokens per theme
// :root { --background: 0 0% 100%; --foreground: 222 84% 5%; --primary: 222 47% 11%; }
// .dark { --background: 222 84% 5%; --foreground: 210 40% 98%; --primary: 210 40% 98%; }

// Theme provider — app/layout.tsx
import { ThemeProvider } from "next-themes";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}

// Theme toggle — client component
"use client";
import { useTheme } from "next-themes";

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      {theme === "dark" ? "☀️" : "🌙"}
    </button>
  );
}
```

## See Also

- [design-tokens.md](../concepts/design-tokens.md)
- [component-styling.md](../patterns/component-styling.md)

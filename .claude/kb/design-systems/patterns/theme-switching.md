# Theme Switching

> **Purpose**: next-themes provider, class-based toggle, system preference
> **MCP Validated**: 2026-03-29

## When to Use

- Adding light/dark theme toggle to Next.js app
- Respecting system color scheme preference
- SSR-safe theme mounting

## Implementation

```bash
npm install next-themes
```

```tsx
// app/layout.tsx — wrap with ThemeProvider
import { ThemeProvider } from "next-themes";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"       // Adds class="dark" to <html>
          defaultTheme="system"   // Respect OS preference
          enableSystem            // Watch for OS changes
          disableTransitionOnChange // Prevent flash during switch
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}

// Theme toggle component
"use client";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => setMounted(true), []);
  if (!mounted) return <div className="h-9 w-9" />; // placeholder

  return (
    <button
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      aria-label={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}
      className="rounded-md p-2 hover:bg-accent"
    >
      {resolvedTheme === "dark" ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

// Three-way toggle: light / dark / system
function ThemeSelector() {
  const { theme, setTheme } = useTheme();
  return (
    <select value={theme} onChange={(e) => setTheme(e.target.value)}>
      <option value="system">System</option>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  );
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `attribute` | `"data-theme"` | `"class"` for Tailwind dark mode |
| `defaultTheme` | `"system"` | Initial theme |
| `enableSystem` | `true` | Watch OS preference |
| `storageKey` | `"theme"` | localStorage key |
| `disableTransitionOnChange` | `false` | Prevent FOUC |

## See Also

- [dark-mode.md](../../tailwind-css/patterns/dark-mode.md)
- [token-architecture.md](../concepts/token-architecture.md)

# React Knowledge Base

> **Purpose**: React development patterns — hooks, Server Components, state management, composition
> **MCP Validated**: 2026-03-29

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/hooks-patterns.md](concepts/hooks-patterns.md) | useState, useEffect, useRef, custom hooks |
| [concepts/server-components.md](concepts/server-components.md) | RSC, "use client", "use server", boundaries |
| [concepts/state-management.md](concepts/state-management.md) | Context, Zustand, Jotai, when to use what |
| [concepts/rendering-patterns.md](concepts/rendering-patterns.md) | Suspense, Error Boundaries, Streaming |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/component-composition.md](patterns/component-composition.md) | Compound components, render props, slots |
| [patterns/form-handling.md](patterns/form-handling.md) | React Hook Form + Zod, Server Actions |
| [patterns/data-fetching.md](patterns/data-fetching.md) | SWR, React Query, server-side fetch |
| [patterns/testing-components.md](patterns/testing-components.md) | Testing Library, user-event, MSW |

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Server Components** | Default in Next.js App Router — render on server, zero JS bundle impact |
| **Client Components** | Add "use client" directive — for interactivity, hooks, browser APIs |
| **Hooks** | Functions for state, effects, refs, memoization — follow Rules of Hooks |
| **Composition** | Prefer composition over inheritance — compound components, render props |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/hooks-patterns.md |
| **Intermediate** | patterns/component-composition.md, patterns/data-fetching.md |
| **Advanced** | concepts/server-components.md, concepts/rendering-patterns.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| react-developer | All files | Component development, hooks, state |
| frontend-architect | concepts/server-components.md, concepts/rendering-patterns.md | Architecture decisions |

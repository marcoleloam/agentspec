# Frontend Patterns Knowledge Base

> **Purpose**: Cross-cutting frontend patterns — project structure, error handling, performance, auth, API integration
> **MCP Validated**: 2026-03-29

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/project-structure.md](concepts/project-structure.md) | Feature-based organization, barrel exports |
| [concepts/error-handling.md](concepts/error-handling.md) | Error boundaries, toast, retry, error pages |
| [concepts/performance.md](concepts/performance.md) | Code splitting, lazy loading, memoization, CWV |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/api-integration.md](patterns/api-integration.md) | Typed fetch wrapper, error types, retry |
| [patterns/auth-flow.md](patterns/auth-flow.md) | Login, session, protected routes, role-based |
| [patterns/optimistic-updates.md](patterns/optimistic-updates.md) | useMutation, rollback, cache invalidation |

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Feature-Based Structure** | Organize by feature, not by file type |
| **Error Boundaries** | React boundaries catch rendering errors gracefully |
| **Code Splitting** | Load code on demand with dynamic imports |
| **Optimistic Updates** | Update UI immediately, rollback if server fails |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| frontend-architect | concepts/project-structure.md, concepts/performance.md | Architecture |
| ux-designer | concepts/error-handling.md, patterns/auth-flow.md | UX flows |
| react-developer | patterns/api-integration.md, patterns/optimistic-updates.md | Implementation |

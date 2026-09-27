# dbt Knowledge Base (Lean)

> **Purpose**: Opinionated dbt guidance — anti-patterns, decisions, and conventions distilled from the full dbt KB. Syntax, config tables, and code examples are intentionally omitted (see Context7 for those).
> **Source**: `.claude/kb/dbt/` (index, quick-reference, concepts/, patterns/)

## Files

| File | Purpose |
|------|---------|
| [anti-patterns.md](anti-patterns.md) | What not to do in models, tests, macros, and Mesh — and why |
| [decisions.md](decisions.md) | When to choose one materialization/strategy/test type over another |
| [conventions.md](conventions.md) | Model layer naming, access levels, and metric naming conventions |

## Covers

Model layering (staging/intermediate/marts), incremental strategy selection, generic vs singular vs unit testing, macro reuse, dbt Mesh access control, Semantic Layer governance, and Fusion Engine migration caution.

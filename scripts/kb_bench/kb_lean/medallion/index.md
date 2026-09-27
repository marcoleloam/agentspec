# Medallion Architecture Knowledge Base (Lean)

> **Purpose**: Opinionated Medallion (Bronze/Silver/Gold) guidance — anti-patterns, decisions, and conventions distilled from the full Medallion KB. Delta/Iceberg syntax, PySpark code, and config examples are intentionally omitted (see Context7 for those).
> **Source**: `.claude/kb/medallion/` (index, quick-reference, concepts/, patterns/, specs/)

## Files

| File | Purpose |
|------|---------|
| [anti-patterns.md](anti-patterns.md) | What breaks the Bronze/Silver/Gold contract, and why |
| [decisions.md](decisions.md) | When to choose Bronze vs Silver vs Gold vs the AI-era extension layers |
| [conventions.md](conventions.md) | Layer responsibilities, naming, and required metadata columns |

## Covers

Bronze raw ingestion, Silver cleansing/deduplication/SCD, Gold business aggregation,
domain-oriented namespace organization, data-quality gates between layers, schema
evolution strategy, incremental/CDC loading, and Feature/Vector/Semantic layer extensions
for AI/ML workloads.

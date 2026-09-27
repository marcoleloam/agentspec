# Microsoft Fabric Knowledge Base (Lean)

> Slimmed for kb_bench arm C: opinionated content only (anti-patterns, decisions,
> conventions). API/SDK/T-SQL/KQL/M-language syntax, endpoint references, and
> config tables are dropped — those come from live Context7 docs. Source:
> `.claude/kb/microsoft-fabric/` (8 subdomains: logging-monitoring,
> data-engineering, architecture-patterns, data-warehouse, apis-sdks,
> governance-security, cicd-automation, ai-capabilities).

Covers workload selection (Lakehouse/Warehouse/Eventhouse), medallion
architecture, workspace/capacity design, Delta Lake maintenance, Direct Lake,
Warehouse T-SQL limitations, security layering (RLS/CLS/DDM), CI/CD and Git
branching strategy, and Copilot/ML governance.

## Files

- [anti-patterns.md](anti-patterns.md) — what not to do, and why
- [decisions.md](decisions.md) — when to choose X over Y, with rationale
- [conventions.md](conventions.md) — naming, structure, layer responsibilities

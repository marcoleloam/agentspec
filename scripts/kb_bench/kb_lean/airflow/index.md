# Airflow Knowledge Base (Lean)

> **Purpose**: Opinionated Airflow guidance — anti-patterns, decisions, and conventions distilled from the full Airflow KB. Operator syntax, config tables, and code examples are intentionally omitted (see Context7 for those).
> **Source**: `.claude/kb/airflow/` (index, quick-reference, concepts/, patterns/)

## Files

| File | Purpose |
|------|---------|
| [anti-patterns.md](anti-patterns.md) | DAG-authoring mistakes and why they hurt at scale |
| [decisions.md](decisions.md) | Orchestrator choice, trigger rules, sensor mode, DAG design trade-offs |
| [conventions.md](conventions.md) | DAG/task organization and configuration conventions |

## Covers

DAG idempotency and atomicity, TaskFlow vs classic operators, deferrable operators, XCom
usage limits, dynamic task mapping, error-handling/alerting design, and choosing between
Airflow, Dagster, and Prefect.

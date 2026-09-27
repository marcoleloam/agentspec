# dbt Decisions

## Choosing an incremental strategy

Pick based on data mutability, need for a unique key, and volume — not by default:

- **append** — immutable/event data where rows are never updated; no unique key needed.
- **merge** — mutable rows needing upsert semantics; requires a unique key; fine up to
  roughly 100M rows on warehouses with efficient MERGE (Snowflake, BigQuery).
- **delete+insert** — mutable rows at higher volume (100M+) on warehouses where MERGE is
  costly (Redshift, Postgres); requires a unique key.
- **insert_overwrite** — partition-level replacement; needs a partition key rather than a
  row-level unique key; good fit for BigQuery/Spark partitioned tables.
- **microbatch** — large time-series data with an `event_time` column; removes the need to
  hand-write `is_incremental()` filtering logic and gives automatic, retryable per-batch
  backfills — prefer this over hand-rolled merge logic for time-partitioned facts.

## Choosing a materialization

- Referenced by many downstream models → `table` (avoid recompiling the same logic
  repeatedly).
- Large and requires incremental updates → `incremental`.
- Small and used by exactly one downstream model → `ephemeral` (inlined, no storage cost).
- Queried directly by BI tools → `table` (views can be too slow for direct dashboard use).
- Default when unsure → `view` (cheapest to maintain, always fresh).

## Choosing a test type

- Standard column-level checks (uniqueness, not-null, accepted values, relationships) →
  built-in **generic tests** in YAML.
- Complex logic spanning multiple tables that doesn't fit a single-column check →
  **singular test** (a SQL file returning failing rows).
- A check pattern repeats across many models → wrap it as a **custom generic test** macro
  so it's reusable and parameterized instead of duplicated singular tests.
- Validating that SQL transformation logic behaves correctly *before* materialization, on
  fixed inputs (TDD-style) → **unit test** (v1.8+); note these only work on SQL models in
  the current project, not Python models or materialized views.

## dbt Mesh access level

- `public` — the model is a stable data-product API; any project may `ref()` it.
- `protected` — shared within the same group/team, not exposed project-wide.
- `private` — internal implementation detail, never referenced outside its own project.
Use the narrowest level that satisfies real consumers; widening later is easy, narrowing
after adoption breaks people.

## When to split a dbt project into a Mesh

Migrate incrementally, driven by real organizational seams rather than pre-emptively:

1. Is there a single downstream team consuming your models? Start there as a Mesh
   consumer.
2. Are people already working at different transformation levels (staging vs. marts)?
   Split along that boundary first.
3. Are different data sources owned by different teams? Split by domain boundary.
4. Do logical groupings already exist informally in the project? Formalize them as Mesh
   interfaces rather than inventing new ones.

## Migrating dbt Core projects to the Fusion Engine

Validate before switching production traffic: run `dbt-autofix` to resolve strict-mode
discrepancies, compare `dbt compile` output between Core and Fusion, verify macros (Fusion
uses MiniJinja, which is Jinja2-compatible but not identical in edge cases), and only
promote once output parity is confirmed.

## Adopting the Semantic Layer

Introduce a Semantic Layer (MetricFlow) when multiple BI tools or teams would otherwise
define the same metric (e.g. "revenue") differently, when AI agents/LLMs need consistent
metric definitions (semantic inconsistency causes hallucinated answers), or when the
organization needs a governance contract between domains rather than ad hoc dashboard SQL.

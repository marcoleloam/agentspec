# Medallion Anti-Patterns

## Transforming data in Bronze

Bronze exists to preserve full source fidelity for auditability and reprocessing. Any
filtering, casting, or business logic applied at ingestion means the original raw signal
is lost if that logic was wrong — add only ingestion metadata columns in Bronze, never
transform.

## Skipping quality checks in Bronze ("it's raw, so it doesn't matter")

Modern (shift-left) practice validates basic structural integrity at ingestion — required
columns present, payload parseable, not empty — even though Bronze stays otherwise
untransformed. This catches broken source feeds at the earliest possible point instead of
discovering them two layers downstream.

## Building Gold directly from Bronze

Skipping Silver means Gold aggregates inherit un-deduplicated, uncleaned data — duplicate
rows silently inflate every KPI built on top. Always go Bronze → Silver → Gold.

## Silver that's just "Bronze with nicer column names"

Renaming columns without deduplicating, casting types, or validating business rules is not
cleansing — it just relabels dirty data. Silver must actually deduplicate on business
keys, enforce types, and validate before being trusted as a "single source of truth."

## Skipping deduplication in Silver

Writing Bronze straight into Silver without windowing on a business key lets every
re-ingested or duplicated source row persist, corrupting anything downstream that assumes
one row per entity.

## One monolithic Gold table for everything

A single all-purpose Gold table becomes slow to query and hard to maintain as more
consumers pile requirements onto it. Prefer purpose-specific Gold aggregates (`dim_*`,
`fact_*`, `agg_*`) over a single do-everything table.

## Gold tables without a `_computed_at` (or similar refresh-timestamp) column

Without a computation timestamp, consumers have no way to tell whether a KPI reflects
this morning's data or is stale — always track when an aggregation was last refreshed.

## Exposing raw foreign keys in Gold without joined dimensions

Forces every consumer (dashboard, analyst) to re-implement the same join. Pre-join
dimensions into fact tables so Gold is genuinely consumption-ready.

## No data contracts between layers/domains

Without an explicit schema, SLA, and ownership contract at each layer boundary, downstream
consumers break silently whenever an upstream owner changes a schema. This gets worse,
not better, once AI/ML models start consuming the data.

## Monolithic namespace (no domain separation)

Putting all tables (`orders`, `products`, `revenue_kpi`, ...) in one flat database hides
ownership and creates unnecessary coupling between unrelated business domains. Separate by
domain and layer (e.g. `bronze_sales`, `silver_inventory`, `gold_sales`).

## Treating Medallion as "set and forget"

The layer boundaries are contracts, not just pipeline stages — if they aren't enforced and
monitored (quality gates, schema evolution discipline, data contracts), the architecture
degrades back into an unstructured data swamp over time.

## Applying SCD Type 2 everywhere in Silver

Full history tracking on every table adds storage and query complexity that's only
justified where the business genuinely needs point-in-time answers — use Type 2 only for
entities that require historical tracking, Type 1 (overwrite) elsewhere.

## Hard-deleting records in Bronze

Bronze is meant to retain a complete raw history for reprocessing; physically deleting
rows there removes the ability to audit or replay. Prefer soft-delete or full retention in
Bronze.

## Ignoring AI/ML data needs when designing Gold

ML models and RAG/semantic-search consumers need point-in-time-correct features and
certified, contract-governed datasets — retrofitting this after Gold is already built for
BI dashboards is significantly harder than designing for it upfront.

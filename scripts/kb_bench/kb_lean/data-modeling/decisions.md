# Decisions

## Choosing a Modeling Approach

| Approach | Choose when | Trade-off |
|----------|-------------|-----------|
| Star Schema | BI/analytics with known query patterns, moderate-to-expert SQL team | Needs 3-6 joins unless paired with a semantic layer |
| Snowflake Schema | Dimensions need to be storage-efficient and normalized | Higher query complexity/maintenance than star |
| Data Vault 2.0 | Enterprise DWH integrating many sources, audit/history required | Slow to query directly — needs an information mart on top |
| One Big Table (OBT) | Single dashboard/BI-tool use case, high query concurrency, stable schema | High storage, full rebuild on refresh, no ad-hoc flexibility |
| Activity Schema | Event-driven, flexible analytics | Medium complexity, less tooling maturity than star schema |

**Best practice (2025+):** star schema as the foundation (Gold layer), OBT as a
disposable, rebuildable mart on top for specific dashboards, and a semantic
layer (dbt Metrics, Cube, AtScale) to abstract joins for analysts. Do not treat
OBT as a replacement for the star schema — use it additively.

## Choosing an SCD Type

| Type | Choose when | Why |
|------|-------------|-----|
| Type 1 (overwrite) | History of that attribute is not needed (e.g. typo fixes) | Simplest, minimal storage |
| Type 2 (new row + effective dates) | Full history is required for the attribute | Standard for auditable dimensions, but adds storage and query complexity |
| Type 3 (previous-value column) | Only one prior value is ever needed | Cheap, but can't go back further than one change |
| Type 4 (separate history table) | Current and historical records should be queried separately | Keeps the "current" table small; requires a join for history |
| Type 6 (1+2+3 hybrid) | Need current flag, full history, and quick access to the prior value simultaneously | Highest complexity/storage, but most flexible |

## When to Denormalize

Normalize (up to 3NF/BCNF) for OLTP/source systems where write consistency
matters. Denormalize deliberately for the analytics/consumption layer, trading
storage for fewer joins and faster reads — this is *why* star schemas and OBTs
exist. The decision is not "normalize or not" but "which layer are we
optimizing for."

## Data Vault Layering: Raw Vault vs Business Vault vs Information Mart

| Layer | Purpose | Rationale for separation |
|-------|---------|---------------------------|
| Raw Vault | Source-faithful, hash keys + load metadata only, no business rules | Keeps a fully auditable, reprocessable copy of source history |
| Business Vault | Derived relationships, computed satellites | Business logic evolves independently from raw ingestion |
| Information Mart | Consumption-ready star schemas | Analysts/BI tools query a familiar dimensional shape, not raw Hubs/Links/Sats |

## Schema Evolution: What's Safe vs What's Breaking

Additive, widening changes (add nullable column, widen a numeric type) are
backward- and often forward-compatible — safe to ship without coordination.
Removals, renames, and type-narrowing are breaking for consumers and require a
deprecation lifecycle (add new -> backfill -> mark deprecated with a removal
date -> migrate consumers -> drop old), never an immediate change.

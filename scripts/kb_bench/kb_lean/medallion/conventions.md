# Medallion Conventions

## Layer responsibilities

| Layer | Write mode | Schema | Responsibility |
|-------|-----------|--------|-----------------|
| Bronze | append-only | schema-on-read | Preserve raw source fidelity; add metadata only, never transform. |
| Silver | merge/upsert | schema-on-write | Cleanse, type-cast, deduplicate on business keys; enterprise single source of truth. |
| Gold | overwrite/merge | star/snowflake | Business-level aggregates and dimensional models for direct consumption. |

## Table and database naming

| Layer | Database pattern | Table pattern |
|-------|------------------|---------------|
| Bronze | `bronze_{domain}` | `raw_{source}_{entity}` |
| Silver | `silver_{domain}` | `cleansed_{entity}` |
| Gold | `gold_{domain}` | `dim_{entity}`, `fact_{entity}`, `agg_{metric}` |

## Namespace hierarchy (catalog systems, e.g. Unity Catalog)

`catalog (environment)` → `schema (layer_domain)` → `table (entity)`. Domains own their own
Bronze/Silver/Gold schemas; a shared/master domain hosts dimensions used across domains
rather than duplicating them.

## Required metadata columns per layer

- **Bronze**: `_ingested_at`, `_source_file`, `_source_system` — mandatory for lineage and
  reprocessing.
- **Silver**: `_created_at`, `_updated_at` always; `is_current`, `valid_from`, `valid_to`
  only on tables using SCD Type 2.
- **Gold**: `_computed_at` — mandatory so consumers can tell how fresh an aggregate is.

## Data contracts

Every layer boundary that has external consumers should carry an explicit contract:
schema, freshness SLA, completeness/availability targets, and named ownership — not just
an implicit "whatever the pipeline currently produces."

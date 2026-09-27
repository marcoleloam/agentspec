# Medallion Decisions

## Which layer for a given use case

- Raw event ingestion → Bronze, append-only, with ingestion metadata only.
- Deduplication + cleansing → Silver, MERGE with a deduplication window on business keys.
- Business KPIs / dashboards → Gold, pre-aggregated, purpose-specific tables.
- ML feature engineering → a dedicated Feature layer (or Silver with point-in-time joins
  if a full feature store isn't in place).
- RAG / semantic search → a Vector layer sourced from Gold, refreshed when Gold changes.
- Data quality enforcement → gate between Bronze and Silver (shift-left: also validate
  basic structure at Bronze itself).
- Schema changes arriving from source → let schema evolve freely at Bronze
  (`mergeSchema`), then apply explicit, reviewed migrations at Silver — Gold simply
  rebuilds from Silver rather than absorbing the change directly.
- Historical/point-in-time tracking → Silver layer with SCD Type 2 (`valid_from`/
  `valid_to`), applied selectively (see anti-patterns.md).
- Real-time + batch combined → stream into Bronze continuously, process Silver/Gold in
  batch.
- AI model training data → Gold, restricted to certified datasets backed by data
  contracts.
- Cross-domain analytics → Gold layer, joining across domain-separated namespaces rather
  than merging domains into one shared table.

## Database/schema naming pattern

- `{layer}_{domain}` (e.g. `bronze_sales`) — default choice, layer-first organization;
  easiest to reason about "what stage is this data at."
- `{domain}_{layer}` (e.g. `sales_bronze`) — domain-first, better fit when the
  organization is explicitly structured around Data Mesh domain ownership.
- `{domain}.{layer}_{entity}` (e.g. `sales.silver_orders`) — use under a catalog system
  (e.g. Unity Catalog) that already provides a domain-level namespace, so layer becomes
  part of the schema/table name instead of the top-level container.

## When to add AI-era extension layers (Feature / Vector / Semantic)

Add a Feature layer when ML training needs versioned, point-in-time-correct inputs that
plain Silver/Gold tables don't guarantee (no data leakage). Add a Vector layer when
RAG/semantic search needs embeddings kept in sync with Gold. Add a Semantic layer
(metrics-as-code) when multiple consumers — BI tools or AI agents — would otherwise derive
the same business metric inconsistently; this is especially important for AI agents, since
inconsistent metric definitions cause hallucinated answers.

## Shift-left vs traditional quality gating

Traditional Medallion practice checks quality only at the Bronze→Silver boundary. Prefer
shift-left: add lightweight *structural* checks at Bronze ingestion (required columns
present, not empty) in addition to full *business-rule* validation at Silver and
*aggregate* sanity checks at Gold — this catches broken feeds before they propagate rather
than after.

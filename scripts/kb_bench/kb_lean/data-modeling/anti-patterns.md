# Anti-Patterns

## Dimensional Modeling

- **No grain defined, mixing granularities.** Without an explicit grain ("one row =
  one order line item"), a measure column like `total_revenue` is ambiguous —
  aggregated? per-order? per-item? Always state the grain before designing a fact
  table.
- **Nullable fact measures.** Numeric measures should default to 0, not NULL, so
  aggregations don't silently drop rows.
- **Natural keys as PKs / FKs.** Using a business key (e.g. `customer_email`) as
  the foreign key in a fact table breaks when the source system changes that
  value. Use surrogate keys instead — they are stable and immutable.

## Normalization vs Denormalization

- **Over-normalized analytics tables.** Forcing a dashboard query through 5-6
  joins across fully normalized dimensions is a sign the model belongs in OLTP,
  not in the consumption layer. Analytics warehouses should denormalize
  deliberately for query performance.
- **OBT as the only layer.** If One Big Table is the sole model, adding a new
  dimension requires a full rebuild, and even trivial lookups (e.g. distinct
  segment values) must scan the entire wide table. OBT should sit as a mart on
  top of a star schema, not replace it.

## SCD (Slowly Changing Dimensions)

- **SCD Type 2 without an `is_current` flag.** Forcing every "give me the current
  record" query to filter on a sentinel date (e.g. `effective_to = '9999-12-31'`)
  is brittle and couples every consumer to that sentinel convention. Use a
  boolean flag for current-row lookups and the date range only for point-in-time
  queries.

## Schema Evolution & Migration

- **Dropping a column consumers depend on with no deprecation period.** An
  immediate `DROP COLUMN` with no communication breaks every downstream
  consumer at once. Evolution should follow a lifecycle: add the new column,
  mark the old one deprecated (with a removal date), give consumers a
  migration window, then drop.
- **Narrowing a type or renaming a column directly.** These are breaking
  changes for both backward and forward compatibility (unlike adding a
  nullable column or widening a type, which are safe). Treat narrowing/renaming
  as requiring the same deprecation lifecycle as a drop.

## Data Vault

- **Satellites without a `hash_diff`.** Without a hash of all tracked attributes,
  every load re-inserts identical rows into a satellite instead of detecting
  "nothing changed" and skipping the insert. This defeats the purpose of
  change-data tracking in the Vault.
- **Hand-writing all Hub/Link/Satellite loading SQL.** At enterprise scale this
  doesn't scale for review or consistency; metadata-driven generation
  (AutomateDV, Coalesce) is the 2025+ best practice instead of bespoke SQL per
  entity.

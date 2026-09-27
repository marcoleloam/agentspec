# Conventions

## Naming

| Prefix/Suffix | Meaning | Example |
|----------------|---------|---------|
| `fact_` | Fact table (numeric, additive measures) | `fact_order_items` |
| `dim_` | Dimension table (descriptive context) | `dim_customer` |
| `hub_` | Data Vault Hub (business key entity) | `hub_customer` |
| `link_` | Data Vault Link (relationship between hubs) | `link_customer_order` |
| `sat_` | Data Vault Satellite (attributes + history) | `sat_customer_details` |
| `obt_` | One Big Table mart | `obt_order_analytics` |
| `mart_` | Consumption-ready denormalized table | `mart_sales_summary` |
| `_sk` | Surrogate key column | `customer_sk` |
| `_id` | Natural/business key column | `customer_id` |
| `_hk` | Data Vault hash key | `hub_customer_hk` |

## Structural Conventions

- **Grain must be documented on every fact table** (a one-line comment: "one
  row = ___"). This prevents accidental fan-out from ambiguous joins.
- **Surrogate keys are the join key everywhere**, not natural keys — natural
  keys are preserved as a plain attribute for traceability but never used as a
  foreign key.
- **The date dimension is always shared/conformed** across all facts, never
  duplicated per fact.
- **`is_current` boolean accompanies effective-date ranges** on SCD Type 2
  dimensions, so current-row lookups don't depend on sentinel dates.
- **`hash_diff` accompanies every Data Vault Satellite** as the change-detection
  column, computed from the concatenation of all tracked attributes.
- **Degenerate dimensions stay in the fact table** (e.g. `order_id`) rather than
  getting their own dimension table when there is no additional descriptive
  attribute to store.
- **Junk dimensions combine low-cardinality flags** (e.g. `is_gift`,
  `payment_method`) into a single small dimension instead of scattering them as
  separate columns on the fact table.

## Layer Responsibilities

| Layer | Responsibility |
|-------|-----------------|
| Raw Vault | Source-faithful integration, hash keys + load metadata, no business rules |
| Business Vault | Derived/computed relationships and satellites, business logic applied |
| Information Mart / Gold | Consumption-ready star schemas for BI |
| Mart (OBT) | Disposable, rebuildable, dashboard-specific denormalized table built from the Gold star schema — not a replacement for it |

## Deprecation Convention

Column/table deprecation is communicated via metadata (comment) stating the
deprecation date and a removal date, giving consumers a migration window (30+
days is the referenced norm) before the drop actually happens.

# CDC Fundamentals

> **Purpose**: Change Data Capture processing with APPLY CHANGES in Lakeflow pipelines
> **Confidence**: High
> **Source**: https://docs.databricks.com/aws/en/dlt/cdc

## Overview

Change Data Capture (CDC) in Lakeflow processes incremental changes from source systems, enabling efficient data synchronization without full reloads. The `APPLY CHANGES` API (also called AUTO CDC) handles insert, update, and delete operations, supporting both SCD Type 1 (current state) and SCD Type 2 (historical tracking) patterns.

## The Concept

### CDC APIs

Lakeflow provides two CDC approaches:

1. **AUTO CDC** — processes changes from a change data feed (CDF) where each record represents an operation (insert/update/delete)
2. **AUTO CDC FROM SNAPSHOT** — processes periodic full snapshots and computes the diff automatically (Python only, Public Preview)

### SCD Type 1 (Current State)

Records are updated in place. No history is retained.

```python
import dlt
from pyspark.sql.functions import col

dlt.create_auto_cdc_flow(
    target="customers",
    source="customers_cdc_stream",
    keys=["customer_id"],
    sequence_by=col("timestamp"),
    stored_as_scd_type=1
)
```

```sql
CREATE OR REFRESH STREAMING TABLE customers;

APPLY CHANGES INTO customers
FROM STREAM customers_cdc
KEYS (customer_id)
SEQUENCE BY timestamp
COLUMNS * EXCEPT (operation, timestamp)
STORED AS SCD TYPE 1
```

### SCD Type 2 (Historical Tracking)

Previous versions are retained with `__START_AT` and `__END_AT` columns.

```sql
CREATE OR REFRESH STREAMING TABLE customers;

APPLY CHANGES INTO customers
FROM STREAM customers_cdc
KEYS (customer_id)
SEQUENCE BY timestamp
COLUMNS * EXCEPT (operation, timestamp)
STORED AS SCD TYPE 2
```

### Handling Deletes

```python
dlt.create_auto_cdc_flow(
    target="customers",
    source="customers_cdc_stream",
    keys=["customer_id"],
    sequence_by=col("timestamp"),
    apply_as_deletes=expr("operation = 'DELETE'"),
    stored_as_scd_type=1
)
```

## Quick Reference

| SCD Type | History | Columns Added | Use Case |
|----------|---------|---------------|----------|
| Type 1 | No | None | Current state, dashboards |
| Type 2 | Yes | `__START_AT`, `__END_AT` | Audit trails, temporal queries |

| Parameter | Purpose | Required |
|-----------|---------|----------|
| `target` | Destination table name | Yes |
| `source` | Source stream or table | Yes |
| `keys` | Business key columns | Yes |
| `sequence_by` | Ordering column for dedup | Yes |
| `apply_as_deletes` | Expression identifying deletes | No |
| `stored_as_scd_type` | 1 or 2 | No (default: 1) |

## Common Mistakes

### Wrong

```python
# Missing sequence_by causes non-deterministic ordering
dlt.create_auto_cdc_flow(
    target="orders",
    source="orders_cdc",
    keys=["order_id"]
    # No sequence_by — which update wins?
)
```

### Correct

```python
# Always specify sequence_by for deterministic deduplication
dlt.create_auto_cdc_flow(
    target="orders",
    source="orders_cdc",
    keys=["order_id"],
    sequence_by=col("updated_at")
)
```

## Related

- [Core Concepts](../concepts/core-concepts.md)
- [CDC Apply Changes Pattern](../patterns/cdc-apply-changes.md)
- [CDC Example](../patterns/cdc-example.md)

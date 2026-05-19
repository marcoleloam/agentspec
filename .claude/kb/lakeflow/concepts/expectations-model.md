# Expectations Model

> **Purpose**: Data quality constraints that validate records flowing through Lakeflow pipelines
> **Confidence**: High
> **Source**: https://docs.databricks.com/aws/en/dlt/expectations

## Overview

Expectations are declarative data quality rules applied to streaming tables and materialized views in Lakeflow Declarative Pipelines. They define constraints as SQL boolean expressions and specify violation policies that control what happens when records fail validation. Expectations enable progressive quality enforcement across Bronze, Silver, and Gold layers.

## The Concept

### Expectation Components

Every expectation has three parts:

1. **Name** — human-readable identifier for the rule
2. **Constraint** — SQL boolean expression that must evaluate to `true` for valid records
3. **Violation policy** — action taken when a record fails: `WARN`, `DROP`, or `FAIL`

### Violation Policies

```python
import dlt

# WARN (default) — keep invalid records, log metrics
@dlt.expect("valid_timestamp", "event_time IS NOT NULL")

# DROP — remove invalid records before writing
@dlt.expect_or_drop("valid_email", "email LIKE '%@%.%'")

# FAIL — abort the pipeline on any violation
@dlt.expect_or_fail("valid_pk", "id IS NOT NULL")
```

```sql
-- SQL equivalent with EXPECT clause
CREATE OR REFRESH STREAMING TABLE orders (
    CONSTRAINT valid_amount EXPECT (amount > 0) ON VIOLATION DROP ROW,
    CONSTRAINT valid_customer EXPECT (customer_id IS NOT NULL) ON VIOLATION FAIL UPDATE
)
AS SELECT * FROM STREAM(raw_orders)
```

### Multiple Expectations

```python
@dlt.expect_all({
    "valid_id": "id IS NOT NULL",
    "valid_date": "order_date >= '2020-01-01'",
    "valid_amount": "amount > 0"
})

@dlt.expect_all_or_drop({
    "complete_address": "city IS NOT NULL AND state IS NOT NULL",
    "valid_zip": "LENGTH(zip_code) = 5"
})
```

## Quick Reference

| Policy | Invalid Records | Pipeline | Use Case |
|--------|----------------|----------|----------|
| `WARN` | Kept | Continues | Bronze layer, data exploration |
| `DROP` | Removed | Continues | Silver layer, known bad data |
| `FAIL` | N/A | Aborts | Gold layer, critical constraints |

## Common Mistakes

### Wrong

```python
# Applying FAIL expectations at Bronze layer blocks ingestion
@dlt.expect_or_fail("not_null", "col IS NOT NULL")
@dlt.table()
def bronze_raw():
    return spark.readStream.format("cloudFiles").load(path)
```

### Correct

```python
# Use WARN at Bronze, DROP at Silver, FAIL at Gold
@dlt.expect("not_null", "col IS NOT NULL")  # WARN at Bronze
@dlt.table()
def bronze_raw():
    return spark.readStream.format("cloudFiles").load(path)

@dlt.expect_or_drop("not_null", "col IS NOT NULL")  # DROP at Silver
@dlt.table()
def silver_clean():
    return dlt.read_stream("bronze_raw")
```

## Related

- [Core Concepts](../concepts/core-concepts.md)
- [Expectations Pattern](../patterns/expectations.md)
- [Advanced Expectations](../patterns/expectations-advanced.md)

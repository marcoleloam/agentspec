# BigQuery

> **Purpose**: Serverless data warehouse with streaming inserts for real-time analytics
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

BigQuery is a fully managed, serverless data warehouse that supports streaming inserts for real-time data ingestion. For data processing, extracted records flow from Cloud Run to BigQuery via streaming API, enabling immediate analytics on processed data.

## The Pattern

```python
from google.cloud import bigquery
from datetime import datetime

def insert_record_data(project_id: str, dataset_id: str, table_id: str, record: dict):
    """Stream record data to BigQuery."""
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Prepare row with schema-aligned fields
    row = {
        "record_id": record["record_id"],
        "supplier_name": record["supplier_name"],
        "record_date": record["record_date"],
        "total_amount": float(record["total_amount"]),
        "line_items": record.get("line_items", []),
        "processed_at": datetime.utcnow().isoformat(),
        "source_file": record["source_file"]
    }

    errors = client.insert_rows_json(table_ref, [row])

    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")

    return row["record_id"]
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| JSON row | Streaming buffer | Available for query in seconds |
| Batch load | Table partition | Use for historical data |
| Query | Result set | SQL syntax |

## Record Table Schema

```sql
CREATE TABLE IF NOT EXISTS `your-project-id.analytics.processed_data` (
  record_id STRING NOT NULL,
  supplier_name STRING,
  record_date DATE,
  total_amount NUMERIC,
  line_items ARRAY<STRUCT<
    description STRING,
    quantity INT64,
    unit_price NUMERIC,
    total NUMERIC
  >>,
  processed_at TIMESTAMP,
  source_file STRING,
  extraction_confidence FLOAT64
)
PARTITION BY record_date
CLUSTER BY supplier_name;
```

## Partitioning Strategy

| Strategy | Use Case | Data Pipeline |
|----------|----------|---------------|
| **Time-unit (DATE)** | Query by date range | Partition by `record_date` |
| Ingestion time | When date unknown | Fallback option |
| Integer range | ID-based queries | Not recommended |

## Common Mistakes

### Wrong

```python
# No error handling, no deduplication logic
client.insert_rows_json(table, [row])
```

### Correct

```python
def insert_with_dedup(client, table_ref: str, row: dict, insert_id: str):
    """Insert with deduplication via insertId."""
    rows_to_insert = [{
        "insertId": insert_id,  # Deduplicate within buffer window
        "json": row
    }]

    errors = client.insert_rows_json(
        table_ref,
        [row],
        row_ids=[insert_id]  # Client library handles insertId
    )

    if errors:
        for error in errors:
            if "already exists" not in str(error):
                raise RuntimeError(f"Insert failed: {error}")

    return True
```

## Streaming Constraints

| Constraint | Value | Mitigation |
|------------|-------|------------|
| Past partition limit | 31 days | Buffer old data, batch load |
| Future partition limit | 16 days | Validate dates before insert |
| Dedup window | Minutes | Use unique insertId |
| Max row size | 10 MB | Validate payload size |

## Query Best Practices

```sql
-- Good: Specific columns, partition filter
SELECT record_id, supplier_name, total_amount
FROM `your-project-id.analytics.processed_data`
WHERE record_date BETWEEN '2026-01-01' AND '2026-01-31'
  AND supplier_name = 'Example Corp';

-- Bad: SELECT *, no partition filter
SELECT * FROM `your-project-id.analytics.processed_data`;
```

## Related

- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
- [Cloud Run](../concepts/cloud-run.md)
- [IAM](../concepts/iam.md)

# Gold customer dimension

- Fabric workspace: `ws-sales-prod`
- Lakehouse `lh_bronze` (same workspace) holds the staging Delta table
  `stg_customers` (default `dbo` schema) with columns:

| column | type |
|--------|------|
| customer_id | string |
| customer_name | string |
| email | string |
| country_code | string (2 chars) |
| updated_at | timestamp |

  `stg_customers` already contains exactly one row per `customer_id`.
- Warehouse `wh_gold` (same workspace) is where the dimension must live.

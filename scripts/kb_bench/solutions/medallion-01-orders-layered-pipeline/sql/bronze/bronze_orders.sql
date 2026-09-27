-- Bronze: raw, append-only copy of every landed extract. No business logic.
-- Everything stays text so malformed values survive for audit; lineage columns
-- record where and when each row came in. Files already loaded are skipped,
-- so re-running the script never duplicates data.
CREATE TABLE IF NOT EXISTS bronze_orders (
    order_id     VARCHAR,
    customer_id  VARCHAR,
    order_date   VARCHAR,
    status       VARCHAR,
    amount       VARCHAR,
    updated_at   VARCHAR,
    _source_file VARCHAR,
    _ingested_at TIMESTAMPTZ
);

INSERT INTO bronze_orders
SELECT
    order_id, customer_id, order_date, status, amount, updated_at,
    filename AS _source_file,
    current_timestamp AS _ingested_at
FROM read_csv('data/landing/orders_*.csv', all_varchar = true, header = true, filename = true)
WHERE filename NOT IN (SELECT DISTINCT _source_file FROM bronze_orders);

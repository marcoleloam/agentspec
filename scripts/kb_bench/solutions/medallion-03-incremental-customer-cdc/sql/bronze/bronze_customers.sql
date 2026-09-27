-- Bronze: append-only raw history of every CDC change received. Loads only the
-- file named by the `landing_file` variable; a file that was already loaded is
-- skipped, so re-landing an extract is a no-op.
CREATE TABLE IF NOT EXISTS bronze_customers (
    customer_id  VARCHAR,
    email        VARCHAR,
    full_name    VARCHAR,
    country      VARCHAR,
    op           VARCHAR,
    changed_at   VARCHAR,
    _source_file VARCHAR,
    _ingested_at TIMESTAMPTZ
);

INSERT INTO bronze_customers
SELECT customer_id, email, full_name, country, op, changed_at,
       getvariable('landing_file') AS _source_file,
       current_timestamp           AS _ingested_at
FROM read_csv(getvariable('landing_file'), all_varchar = true, header = true)
WHERE NOT EXISTS (
    SELECT 1 FROM bronze_customers b WHERE b._source_file = getvariable('landing_file')
);

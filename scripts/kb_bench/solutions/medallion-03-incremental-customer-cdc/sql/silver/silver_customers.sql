-- Silver: current state of each customer, derived from the full bronze history
-- so late/replayed changes and skipped runs are handled: the change with the
-- latest changed_at wins, and customers whose latest change is a delete are
-- excluded.
CREATE OR REPLACE TABLE silver_customers AS
WITH changes AS (
    SELECT
        try_cast(customer_id AS BIGINT)              AS customer_id,
        nullif(trim(email), '')                      AS email,
        nullif(trim(full_name), '')                  AS full_name,
        nullif(upper(trim(country)), '')             AS country_code,
        upper(trim(op))                              AS op,
        try_cast(changed_at AS TIMESTAMP)            AS changed_at,
        _ingested_at
    FROM bronze_customers
    WHERE try_cast(customer_id AS BIGINT) IS NOT NULL
      AND try_cast(changed_at AS TIMESTAMP) IS NOT NULL
),
latest AS (
    SELECT *
    FROM changes
    QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY changed_at DESC, _ingested_at DESC) = 1
)
SELECT customer_id, email, full_name, country_code, changed_at AS updated_at
FROM latest
WHERE op <> 'D';

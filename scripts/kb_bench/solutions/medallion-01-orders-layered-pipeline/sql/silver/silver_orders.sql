-- Silver: validated, typed, standardised, one current row per order.
CREATE OR REPLACE TEMP VIEW _orders_typed AS
SELECT
    try_cast(order_id AS BIGINT)                          AS order_id,
    trim(customer_id)                                     AS customer_id,
    try_strptime(trim(order_date), '%Y-%m-%d')::DATE      AS order_date,
    lower(trim(status))                                   AS status,
    try_cast(trim(amount) AS DECIMAL(12, 2))              AS amount,
    try_cast(trim(updated_at) AS TIMESTAMP)               AS updated_at,
    order_id AS raw_order_id, customer_id AS raw_customer_id, order_date AS raw_order_date,
    status AS raw_status, amount AS raw_amount, updated_at AS raw_updated_at,
    _source_file, _ingested_at
FROM bronze_orders;

CREATE OR REPLACE TEMP VIEW _orders_checked AS
SELECT *,
    CASE
        WHEN order_id IS NULL THEN 'missing or non-numeric order_id'
        WHEN order_date IS NULL THEN 'invalid order_date: ' || coalesce(raw_order_date, 'NULL')
        WHEN amount IS NULL THEN 'invalid amount: ' || coalesce(raw_amount, 'NULL')
        WHEN amount < 0 THEN 'negative amount'
        WHEN updated_at IS NULL THEN 'invalid updated_at'
        WHEN status NOT IN ('pending', 'shipped', 'delivered', 'cancelled') THEN 'unknown status: ' || coalesce(raw_status, 'NULL')
    END AS reject_reason
FROM _orders_typed;

CREATE OR REPLACE TABLE silver_orders_rejected AS
SELECT
    raw_order_id AS order_id, raw_customer_id AS customer_id, raw_order_date AS order_date,
    raw_status AS status, raw_amount AS amount, raw_updated_at AS updated_at,
    reject_reason, _source_file, _ingested_at
FROM _orders_checked
WHERE reject_reason IS NOT NULL;

CREATE OR REPLACE TABLE silver_orders AS
SELECT order_id, customer_id, order_date, status, amount, updated_at
FROM _orders_checked
WHERE reject_reason IS NULL
QUALIFY row_number() OVER (PARTITION BY order_id ORDER BY updated_at DESC, _ingested_at DESC) = 1;

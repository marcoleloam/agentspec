-- Sales mart: star schema, fact grain = one row per order line.

-- Date dimension: one row per calendar day of 2024 (366 days, leap year).
CREATE OR REPLACE TABLE dim_date AS
SELECT
    CAST(strftime(d, '%Y%m%d') AS INTEGER) AS date_key,
    CAST(d AS DATE)                        AS full_date,
    year(d)                                AS year,
    quarter(d)                             AS quarter,
    month(d)                               AS month
FROM range(DATE '2024-01-01', DATE '2025-01-01', INTERVAL 1 DAY) AS t(d);

-- Customer dimension with preserved segment history (type 2 versions).
-- Resent records that change nothing do not open a new version.
CREATE OR REPLACE TABLE dim_customer AS
WITH feed AS (
    SELECT customer_id, customer_name, segment, CAST(updated_at AS DATE) AS updated_at
    FROM read_csv('data/customers.csv')
),
flagged AS (
    SELECT *,
           lag(segment)       OVER w AS prev_segment,
           lag(customer_name) OVER w AS prev_name
    FROM feed
    WINDOW w AS (PARTITION BY customer_id ORDER BY updated_at)
),
versions AS (
    SELECT customer_id, customer_name, segment, updated_at AS valid_from
    FROM flagged
    WHERE prev_segment IS NULL
       OR prev_segment IS DISTINCT FROM segment
       OR prev_name IS DISTINCT FROM customer_name
)
SELECT
    CAST(row_number() OVER (ORDER BY customer_id, valid_from) AS INTEGER) AS customer_key,
    customer_id,
    customer_name,
    segment,
    valid_from,
    coalesce(lead(valid_from) OVER (PARTITION BY customer_id ORDER BY valid_from) - 1,
             DATE '9999-12-31') AS valid_to,
    lead(valid_from) OVER (PARTITION BY customer_id ORDER BY valid_from) IS NULL AS is_current
FROM versions;

-- Unknown member for late / missing customer references.
INSERT INTO dim_customer VALUES
    (-1, 'UNKNOWN', 'Unknown', 'Unknown', DATE '1900-01-01', DATE '9999-12-31', TRUE);

CREATE OR REPLACE TABLE dim_product AS
SELECT
    CAST(row_number() OVER (ORDER BY product_code) AS INTEGER) AS product_key,
    product_code,
    product_name,
    category
FROM read_csv('data/products.csv');

INSERT INTO dim_product VALUES (-1, 'UNKNOWN', 'Unknown', 'Unknown');

CREATE OR REPLACE TABLE fact_sales AS
SELECT
    o.order_id,
    o.line_no,
    CAST(strftime(CAST(o.order_date AS DATE), '%Y%m%d') AS INTEGER) AS date_key,
    coalesce(c.customer_key, -1)                                    AS customer_key,
    coalesce(p.product_key, -1)                                     AS product_key,
    o.quantity,
    CAST(o.quantity * o.unit_price AS DECIMAL(12, 2))               AS sales_amount
FROM read_csv('data/orders.csv') AS o
LEFT JOIN dim_customer AS c
       ON c.customer_id = o.customer_id
      AND CAST(o.order_date AS DATE) BETWEEN c.valid_from AND c.valid_to
LEFT JOIN dim_product AS p
       ON p.product_code = o.product_code;

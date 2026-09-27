-- Gold: business-level daily revenue mart, built only from silver.
CREATE OR REPLACE TABLE gold_daily_revenue AS
SELECT
    order_date,
    count(order_id)  AS order_count,
    sum(amount)      AS revenue
FROM silver_orders
WHERE status <> 'cancelled'
GROUP BY order_date;

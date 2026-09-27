-- Gold: active customers per country for BI, built from silver only.
CREATE OR REPLACE TABLE gold_customers_by_country AS
SELECT country_code, count(customer_id) AS customer_count
FROM silver_customers
GROUP BY country_code;

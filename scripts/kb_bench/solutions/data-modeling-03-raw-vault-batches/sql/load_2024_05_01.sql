-- Load batch 2024-05-01 into the raw vault. Insert-only and idempotent: re-running
-- the file inserts nothing new.

CREATE OR REPLACE TEMP TABLE stg_crm AS
SELECT DISTINCT
    upper(trim(customer_number))                       AS customer_bk,
    md5(upper(trim(customer_number)))                  AS customer_hk,
    trim(full_name)                                    AS full_name,
    trim(email)                                        AS email,
    trim(tier)                                         AS tier,
    md5(concat_ws('||', coalesce(trim(full_name), ''), coalesce(trim(email), ''),
                  coalesce(trim(tier), '')))           AS hash_diff,
    TIMESTAMP '2024-05-01 00:00:00'                       AS load_dts,
    'crm.customers'                                    AS record_source
FROM read_csv('data/2024-05-01/crm_customers.csv', all_varchar = true);

CREATE OR REPLACE TEMP TABLE stg_orders AS
SELECT DISTINCT
    upper(trim(order_number))                          AS order_bk,
    md5(upper(trim(order_number)))                     AS order_hk,
    upper(trim(customer_ref))                          AS customer_bk,
    md5(upper(trim(customer_ref)))                     AS customer_hk,
    md5(upper(trim(customer_ref)) || '||' || upper(trim(order_number))) AS customer_order_hk,
    TIMESTAMP '2024-05-01 00:00:00'                       AS load_dts,
    'shop.orders'                                      AS record_source
FROM read_csv('data/2024-05-01/shop_orders.csv', all_varchar = true);

-- Hub: every source that carries the business key feeds the hub.
INSERT INTO hub_customer
SELECT customer_hk, customer_bk, min(load_dts), min(record_source)
FROM (
    SELECT customer_hk, customer_bk, load_dts, record_source FROM stg_crm
    UNION ALL
    SELECT customer_hk, customer_bk, load_dts, record_source FROM stg_orders
) AS s
WHERE NOT EXISTS (SELECT 1 FROM hub_customer h WHERE h.customer_hk = s.customer_hk)
GROUP BY customer_hk, customer_bk;

INSERT INTO hub_order
SELECT DISTINCT order_hk, order_bk, load_dts, record_source
FROM stg_orders AS s
WHERE NOT EXISTS (SELECT 1 FROM hub_order h WHERE h.order_hk = s.order_hk);

INSERT INTO link_customer_order
SELECT DISTINCT customer_order_hk, customer_hk, order_hk, load_dts, record_source
FROM stg_orders AS s
WHERE NOT EXISTS (SELECT 1 FROM link_customer_order l
                  WHERE l.customer_order_hk = s.customer_order_hk);

-- Satellite: new row only when the descriptive payload differs from the
-- latest version already stored for that hash key.
INSERT INTO sat_customer_crm
SELECT s.customer_hk, s.load_dts, s.hash_diff, s.full_name, s.email, s.tier, s.record_source
FROM stg_crm AS s
LEFT JOIN (
    SELECT customer_hk, arg_max(hash_diff, load_dts) AS hash_diff
    FROM sat_customer_crm
    GROUP BY customer_hk
) AS cur USING (customer_hk)
WHERE cur.hash_diff IS DISTINCT FROM s.hash_diff
  AND NOT EXISTS (SELECT 1 FROM sat_customer_crm x
                  WHERE x.customer_hk = s.customer_hk AND x.load_dts = s.load_dts);

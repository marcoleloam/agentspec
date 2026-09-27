-- Raw vault structures (insert-only). Hash keys = MD5 hex of the normalised
-- (trimmed, upper-cased) business key; links hash the concatenated keys.
CREATE TABLE IF NOT EXISTS hub_customer (
    customer_hk   VARCHAR PRIMARY KEY,
    customer_bk   VARCHAR NOT NULL,
    load_dts      TIMESTAMP NOT NULL,
    record_source VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS hub_order (
    order_hk      VARCHAR PRIMARY KEY,
    order_bk      VARCHAR NOT NULL,
    load_dts      TIMESTAMP NOT NULL,
    record_source VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS link_customer_order (
    customer_order_hk VARCHAR PRIMARY KEY,
    customer_hk       VARCHAR NOT NULL,
    order_hk          VARCHAR NOT NULL,
    load_dts          TIMESTAMP NOT NULL,
    record_source     VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS sat_customer_crm (
    customer_hk   VARCHAR NOT NULL,
    load_dts      TIMESTAMP NOT NULL,
    hash_diff     VARCHAR NOT NULL,
    full_name     VARCHAR,
    email         VARCHAR,
    tier          VARCHAR,
    record_source VARCHAR NOT NULL,
    PRIMARY KEY (customer_hk, load_dts)
);

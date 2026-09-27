-- Gold customer dimension for Warehouse wh_gold.
-- Source: lakehouse lh_bronze (same workspace), read through its SQL analytics
-- endpoint with a cross-database three-part name.

DROP TABLE IF EXISTS dbo.dim_customer;

CREATE TABLE dbo.dim_customer
(
    customer_key   BIGINT        NOT NULL,
    customer_id    VARCHAR(50)   NOT NULL,
    customer_name  VARCHAR(200)  NULL,
    email          VARCHAR(320)  NULL,
    country_code   CHAR(2)       NULL,
    loaded_at      DATETIME2(6)  NOT NULL
);

-- Informational key: Fabric Warehouse only accepts NONCLUSTERED + NOT ENFORCED.
ALTER TABLE dbo.dim_customer
    ADD CONSTRAINT pk_dim_customer PRIMARY KEY NONCLUSTERED (customer_key) NOT ENFORCED;

INSERT INTO dbo.dim_customer (customer_key, customer_id, customer_name, email, country_code, loaded_at)
SELECT
    ROW_NUMBER() OVER (ORDER BY s.customer_id)  AS customer_key,
    s.customer_id,
    s.customer_name,
    s.email,
    s.country_code,
    CAST(SYSUTCDATETIME() AS DATETIME2(6))      AS loaded_at
FROM lh_bronze.dbo.stg_customers AS s;

-- No index DDL: Fabric Warehouse does not support user-defined indexes;
-- customer_id filters rely on the engine's automatic statistics.

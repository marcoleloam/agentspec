-- Account mart: transaction fact (additive) + daily balance periodic snapshot
-- (semi-additive: sums across accounts, never across days).

CREATE OR REPLACE TABLE dim_date AS
SELECT
    CAST(strftime(d, '%Y%m%d') AS INTEGER) AS date_key,
    CAST(d AS DATE)                        AS full_date,
    year(d)                                AS year,
    month(d)                               AS month
FROM range(DATE '2024-01-01', DATE '2025-01-01', INTERVAL 1 DAY) AS t(d);

CREATE OR REPLACE TABLE dim_account AS
SELECT
    CAST(row_number() OVER (ORDER BY account_id) AS INTEGER) AS account_key,
    account_id,
    branch,
    CAST(opened_date AS DATE) AS opened_date
FROM read_csv('data/accounts.csv');

-- Grain: one row per transaction.
CREATE OR REPLACE TABLE fact_transaction AS
SELECT
    t.txn_id,
    CAST(strftime(CAST(t.txn_ts AS DATE), '%Y%m%d') AS INTEGER) AS date_key,
    a.account_key,
    CAST(t.amount AS DECIMAL(14, 2)) AS amount
FROM read_csv('data/transactions.csv') AS t
JOIN dim_account AS a USING (account_id);

-- Grain: one row per account per calendar day the account is open in Q1 2024,
-- including days without activity (balance carried forward).
CREATE OR REPLACE TABLE fact_account_daily_balance AS
WITH src AS (
    SELECT account_id, CAST(opening_balance AS DECIMAL(14, 2)) AS opening_balance
    FROM read_csv('data/accounts.csv')
),
days AS (
    SELECT a.account_key, d.date_key, d.full_date
    FROM dim_account AS a
    JOIN dim_date AS d
      ON d.full_date BETWEEN greatest(a.opened_date, DATE '2024-01-01') AND DATE '2024-03-31'
),
daily_flow AS (
    SELECT account_key, date_key, sum(amount) AS flow
    FROM fact_transaction
    GROUP BY ALL
)
SELECT
    days.date_key,
    days.account_key,
    CAST(s.opening_balance
         + sum(coalesce(f.flow, 0)) OVER (PARTITION BY days.account_key ORDER BY days.full_date)
         AS DECIMAL(14, 2)) AS balance
FROM days
JOIN dim_account AS a USING (account_key)
JOIN src AS s USING (account_id)
LEFT JOIN daily_flow AS f USING (account_key, date_key);

CREATE OR REPLACE VIEW rpt_branch_month AS
WITH branch_day AS (
    SELECT a.branch, d.full_date, date_trunc('month', d.full_date) AS month_start,
           sum(b.balance) AS branch_balance
    FROM fact_account_daily_balance AS b
    JOIN dim_account AS a USING (account_key)
    JOIN dim_date AS d USING (date_key)
    GROUP BY ALL
),
balances AS (
    SELECT branch, CAST(month_start AS DATE) AS month_start,
           arg_max(branch_balance, full_date) AS month_end_balance,
           avg(branch_balance)                AS avg_daily_balance
    FROM branch_day
    GROUP BY ALL
),
flows AS (
    SELECT a.branch, CAST(date_trunc('month', d.full_date) AS DATE) AS month_start,
           sum(t.amount) AS net_flow, count(*) AS txn_count
    FROM fact_transaction AS t
    JOIN dim_account AS a USING (account_key)
    JOIN dim_date AS d USING (date_key)
    GROUP BY ALL
)
SELECT
    b.branch,
    b.month_start,
    b.month_end_balance,
    round(b.avg_daily_balance, 2)          AS avg_daily_balance,
    coalesce(f.net_flow, 0)                AS net_flow,
    coalesce(f.txn_count, 0)               AS txn_count
FROM balances AS b
LEFT JOIN flows AS f USING (branch, month_start);

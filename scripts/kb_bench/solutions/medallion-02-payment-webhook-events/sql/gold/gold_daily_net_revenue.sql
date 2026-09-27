-- Gold: daily net revenue per currency on UTC calendar days, from silver only.
CREATE OR REPLACE TABLE gold_daily_net_revenue AS
SELECT
    CAST(occurred_at_utc AS DATE)                                                   AS revenue_date,
    currency,
    coalesce(sum(amount) FILTER (WHERE event_type = 'payment.captured'), 0)         AS captured_amount,
    coalesce(sum(amount) FILTER (WHERE event_type = 'payment.refunded'), 0)         AS refunded_amount,
    coalesce(sum(amount) FILTER (WHERE event_type = 'payment.captured'), 0)
      - coalesce(sum(amount) FILTER (WHERE event_type = 'payment.refunded'), 0)     AS net_amount
FROM silver_payment_events
GROUP BY CAST(occurred_at_utc AS DATE), currency;

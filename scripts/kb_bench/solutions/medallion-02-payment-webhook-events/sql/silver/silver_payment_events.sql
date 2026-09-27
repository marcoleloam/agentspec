-- Silver: one conformed row per business event (webhook redeliveries removed),
-- UTC timestamps, major-unit amounts, ISO currency codes. Invalid events are
-- quarantined with a reason.
CREATE OR REPLACE TEMP VIEW _payment_events_conformed AS
SELECT
    event_id,
    event_type,
    payment ->> 'id'                                              AS payment_id,
    try_cast(payment ->> 'amount_minor' AS BIGINT)                AS amount_minor,
    upper(trim(payment ->> 'currency'))                           AS currency,
    try_cast(occurred_at AS TIMESTAMPTZ) AT TIME ZONE 'UTC'       AS occurred_at_utc,
    occurred_at                                                   AS raw_occurred_at,
    payment                                                       AS raw_payment,
    try_cast(delivery ->> 'attempt' AS INTEGER)                   AS delivery_attempt,
    _source_file, _ingested_at
FROM bronze_payment_events;

CREATE OR REPLACE TEMP VIEW _payment_events_checked AS
SELECT *,
    CASE
        WHEN event_id IS NULL THEN 'missing event_id'
        WHEN payment_id IS NULL OR trim(payment_id) = '' THEN 'missing payment id'
        WHEN occurred_at_utc IS NULL THEN 'unparseable occurred_at: ' || coalesce(raw_occurred_at, 'NULL')
        WHEN amount_minor IS NULL OR amount_minor <= 0 THEN 'amount must be a positive number'
        WHEN currency IS NULL OR currency NOT IN ('BRL', 'USD', 'EUR') THEN 'unsupported currency: ' || coalesce(currency, 'NULL')
        WHEN event_type NOT IN ('payment.captured', 'payment.refunded') THEN 'unknown event_type'
    END AS reject_reason
FROM _payment_events_conformed;

CREATE OR REPLACE TABLE silver_payment_events_rejected AS
SELECT event_id, event_type, raw_occurred_at AS occurred_at, raw_payment AS payment,
       reject_reason, _source_file, _ingested_at
FROM _payment_events_checked
WHERE reject_reason IS NOT NULL
QUALIFY row_number() OVER (PARTITION BY event_id ORDER BY delivery_attempt, _ingested_at) = 1;

CREATE OR REPLACE TABLE silver_payment_events AS
SELECT
    event_id,
    payment_id,
    event_type,
    CAST(amount_minor AS DECIMAL(18, 2)) / 100 AS amount,
    currency,
    occurred_at_utc
FROM _payment_events_checked
WHERE reject_reason IS NULL
QUALIFY row_number() OVER (PARTITION BY event_id ORDER BY delivery_attempt, _ingested_at) = 1;

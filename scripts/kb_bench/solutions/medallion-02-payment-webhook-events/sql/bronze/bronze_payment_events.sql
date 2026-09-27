-- Bronze: every delivered webhook event exactly as received (redeliveries
-- included), plus lineage. Append-only; files already loaded are skipped.
CREATE TABLE IF NOT EXISTS bronze_payment_events (
    event_id     VARCHAR,
    event_type   VARCHAR,
    occurred_at  VARCHAR,
    payment      JSON,
    delivery     JSON,
    _source_file VARCHAR,
    _ingested_at TIMESTAMPTZ
);

INSERT INTO bronze_payment_events
SELECT event_id, event_type, occurred_at, payment, delivery,
       filename AS _source_file, current_timestamp AS _ingested_at
FROM read_json(
    'data/landing/payment_events_*.jsonl',
    format = 'newline_delimited',
    columns = {event_id: 'VARCHAR', event_type: 'VARCHAR', occurred_at: 'VARCHAR',
               payment: 'JSON', delivery: 'JSON'},
    filename = true)
WHERE filename NOT IN (SELECT DISTINCT _source_file FROM bronze_payment_events);

"""Hourly ingest of raw orders into the lake."""
from __future__ import annotations

import pendulum
from airflow.sdk import Asset, dag, task

RAW_ORDERS_PATH = "s3://lake/raw/orders/"
raw_orders = Asset(name="raw_orders", uri=RAW_ORDERS_PATH)


@dag(
    dag_id="ingest_orders",
    schedule="@hourly",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["orders", "ingest"],
)
def ingest_orders():
    @task
    def extract_orders() -> list[dict]:
        # Stand-in for the API pull.
        return [{"order_id": 1, "amount": 42.0}, {"order_id": 2, "amount": 13.5}]

    @task(outlets=[raw_orders])
    def write_raw_orders(rows: list[dict]) -> int:
        print(f"writing {len(rows)} rows to {RAW_ORDERS_PATH}")
        return len(rows)

    write_raw_orders(extract_orders())


ingest_orders()

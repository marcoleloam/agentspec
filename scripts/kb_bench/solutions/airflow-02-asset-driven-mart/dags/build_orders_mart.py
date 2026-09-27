"""Builds mart.orders_daily whenever new raw orders land."""
from __future__ import annotations

import pendulum
from airflow.sdk import Asset, dag, task

raw_orders = Asset(name="raw_orders", uri="s3://lake/raw/orders/")


@dag(
    dag_id="build_orders_mart",
    schedule=[raw_orders],
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["orders", "mart"],
)
def build_orders_mart():
    @task
    def build_mart() -> None:
        print("reading raw orders and rebuilding mart.orders_daily")

    build_mart()


build_orders_mart()

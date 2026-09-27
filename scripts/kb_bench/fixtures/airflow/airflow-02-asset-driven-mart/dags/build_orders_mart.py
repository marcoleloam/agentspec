"""Builds mart.orders_daily from the raw orders written by ingest_orders."""
from __future__ import annotations

import pendulum
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor
from airflow.sdk import dag, task


@dag(
    dag_id="build_orders_mart",
    schedule="@hourly",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["orders", "mart"],
)
def build_orders_mart():
    wait_for_ingest = ExternalTaskSensor(
        task_id="wait_for_ingest",
        external_dag_id="ingest_orders",
        external_task_id="write_raw_orders",
        mode="reschedule",
        poke_interval=300,
        timeout=3600,
    )

    @task
    def build_mart() -> None:
        print("reading raw orders and rebuilding mart.orders_daily")

    wait_for_ingest >> build_mart()


build_orders_mart()

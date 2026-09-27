"""Daily orders ETL.

Pulls yesterday's orders from the OLTP replica and loads them into the
warehouse. Migrated to Airflow 3.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
from airflow.timetables.interval import CronDataIntervalTimetable


def extract_orders(**context):
    run_day = context["logical_date"].strftime("%Y-%m-%d")
    print(f"extracting orders placed on {run_day}")
    return run_day


default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="orders_etl",
    # Airflow 3 maps cron presets to CronTriggerTimetable by default; keep the
    # Airflow 2 data-interval semantics (logical date = interval start).
    schedule=CronDataIntervalTimetable("@daily", timezone="UTC"),
    start_date=datetime(2024, 1, 1),
    # Airflow 3 defaults catchup to False; missed intervals must still run.
    catchup=True,
    default_args=default_args,
    tags=["orders"],
) as dag:
    start = EmptyOperator(task_id="start")

    extract = PythonOperator(
        task_id="extract_orders",
        python_callable=extract_orders,
    )

    load = BashOperator(
        task_id="load_orders",
        bash_command=(
            "python /opt/etl/load_orders.py --from {{ ds }} --to {{ data_interval_end | ds }}"
        ),
    )

    start >> extract >> load

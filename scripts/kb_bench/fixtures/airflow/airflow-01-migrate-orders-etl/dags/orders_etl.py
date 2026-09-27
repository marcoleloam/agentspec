"""Daily orders ETL.

Pulls yesterday's orders from the OLTP replica and loads them into the
warehouse. Written for Airflow 2.x.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python_operator import PythonOperator


def extract_orders(**context):
    run_day = context["execution_date"].strftime("%Y-%m-%d")
    print(f"extracting orders placed on {run_day}")
    return run_day


default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="orders_etl",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    default_args=default_args,
    tags=["orders"],
) as dag:
    start = DummyOperator(task_id="start")

    extract = PythonOperator(
        task_id="extract_orders",
        python_callable=extract_orders,
    )

    load = BashOperator(
        task_id="load_orders",
        bash_command="python /opt/etl/load_orders.py --from {{ ds }} --to {{ next_ds }}",
    )

    start >> extract >> load

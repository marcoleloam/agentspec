"""Loads every regional sales file that landed for the run, one task instance per file."""
from __future__ import annotations

import pendulum
from airflow.sdk import dag, task

from include.sales_io import list_landing_files, load_file


@dag(
    dag_id="regional_sales",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["sales"],
)
def regional_sales():
    @task
    def list_region_files() -> list[str]:
        return list_landing_files()

    @task(max_active_tis_per_dag=4, retries=2)
    def process_file(path: str, table: str) -> int:
        return load_file(path, table)

    @task
    def summarize(row_counts) -> int:
        total = sum(row_counts)
        print(f"loaded {total} rows in total")
        return total

    counts = process_file.partial(table="sales_raw").expand(path=list_region_files())
    summarize(counts)


regional_sales()

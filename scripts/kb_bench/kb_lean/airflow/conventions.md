# Airflow Conventions

## DAG structure

- Prefer the TaskFlow API (`@dag`/`@task`) over classic operators for Python work — it
  reads as plain Python and makes dependencies implicit from data flow rather than
  requiring manual `>>` wiring for every step.
- Group related dynamically-mapped work in a `TaskGroup` (e.g. `ingest_sources`,
  `process_{table}`) so the graph stays readable when the same operation fans out across
  many tables/partitions.
- Tag DAGs by domain/team and cadence (e.g. `["finance", "daily"]`) for discoverability
  and selective runs (`airflow dags trigger --tags`).

## DAG factory organization

When many DAGs share the same shape (same extract/load/quality-check skeleton), generate
them from a config directory (e.g. `dags/configs/pipeline_*.yaml`) rather than
hand-writing near-duplicate DAG files. Each config supplies only what varies
(`pipeline_name`, `schedule`, `owner`, `source.tables`, `retries`); the factory function
supplies the shared structure, default retry policy, and tagging.

## Failure handling organization

Centralize alerting logic (Slack/PagerDuty notification formatting, severity routing) in
shared callback functions (`on_failure_callback`, `sla_miss_callback`) rather than
duplicating notification code per DAG. Route only high severities (e.g. P1/P2) to
PagerDuty and lower severities to Slack/email only, so on-call paging stays meaningful.

## Naming and ownership

- `default_args["owner"]` should identify the responsible team, not an individual.
- Dedicated "internal" DAGs (e.g. a `failure_notifier` triggered via
  `TriggerDagRunOperator`) should be tagged distinctly (e.g. `["alerting", "internal"]`)
  so they're not confused with business pipelines in DAG listings.

# Airflow Anti-Patterns

## Top-level code outside a task or callable

Code at DAG-file module level runs on every scheduler parse (roughly every 30 seconds by
default), not just at execution time. Loading a CSV or hitting an API at the top of the
file re-executes it constantly and can degrade the whole scheduler. Import heavy libraries
and do real work only inside `@task` functions.

## Hardcoding connections/credentials in DAG code

Bypasses Airflow's `Connection` objects and Variables, making environment promotion and
secret rotation brittle. Reference connections by `conn_id` and resolve at runtime.

## Monolithic tasks that do "the whole ETL" in one step

One task = one logical operation. Bundling extract+transform+load into a single task
means a failure anywhere forces a full retry and makes debugging opaque — atomicity gives
retry granularity and clear failure attribution.

## Skipping retries

A task with no `retries`/`retry_delay` treats every transient failure (network blip, lock
contention) as a hard failure requiring manual intervention.

## Using sensors without `deferrable=True`

A non-deferrable sensor in `poke` mode occupies a worker slot for the entire wait — for
waits of an hour or more this wastes capacity that could run other tasks. Deferrable
operators free the worker and let a triggerer process the wait asynchronously.

## Passing large payloads through XCom

XCom is stored in the metadata database; returning a large DataFrame from a `@task`
serializes it into that DB and can clog it. Pass a lightweight reference (e.g. an S3 path)
through XCom and have the downstream task read the actual data from storage.

## Not using `is_incremental`-style idempotency (using `datetime.now()` instead of the
logical date)

A DAG that keys its processing off wall-clock time instead of the logical/execution date
(`ds`) produces different results on re-run, breaking the core idempotency guarantee that
makes backfills and retries safe.

## Choosing an orchestrator because "everyone uses it"

Picking Airflow, Dagster, or Prefect on popularity alone ignores real fit: a team that
already thinks in data assets is better served by Dagster, a small Python-first team
iterates faster on Prefect, and heavy testing requirements favor Dagster's first-class
`materialize()` testing story.

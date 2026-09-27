# Airflow Decisions

## Orchestrator choice: Airflow vs Dagster vs Prefect

Decide by team shape and workload, not by mindshare:

1. Team of 10+ data engineers already invested in Airflow? → Stay/upgrade to Airflow 3.x
   (asset-aware scheduling + DAG versioning close most of the gap with Dagster).
2. Team already thinks in data assets and has a strong testing culture? → Dagster
   (asset-centric mental model, first-class `materialize()` testing).
3. Small team, Python-first, wants fast iteration? → Prefect (lowest learning curve,
   decorated-function mental model).
4. Regulated industry needing an audit trail? → Airflow 3.x (built-in DAG versioning,
   mature logging).
5. Multi-cloud or hybrid execution requirements? → Airflow 3.x (Task Execution API
   decouples execution from the scheduler).
6. MLOps/GenAI-heavy workflows? → Airflow 3.x (largest share of that workload today).

## DAG scheduling: time-based vs asset-based

Prefer scheduling on a fixed cron when the pipeline genuinely runs on a clock. Prefer
asset-based scheduling (`schedule=[Asset(...)]`, with `&`/`|` for AND/OR composition) when
a DAG's real trigger is "upstream data changed," not "time passed" — this avoids both
wasted runs (nothing new to process) and races (running before upstream finished).

## Sensor/wait strategy by expected wait duration

- Wait under ~5 minutes → `mode="poke"` is acceptable (holds a worker slot briefly).
- Wait 5–60 minutes → `mode="reschedule"` (releases the worker between poke intervals).
- Wait 1 hour or more → `deferrable=True` (frees the worker entirely via the triggerer).
- Cross-DAG dependency where the goal is "run when upstream data is ready," not "run when
  upstream DAG finishes" → prefer asset-driven scheduling over an `ExternalTaskSensor`.

## Trigger rule selection

Choose the trigger rule that matches the semantic intent of the downstream task, not the
default: `all_success` for normal sequential flow, `one_success` for branch convergence
where any path succeeding is enough, `all_done` for cleanup tasks that must run regardless
of upstream outcome, and `none_failed`/`none_skipped` for reconciling conditional
branching so skipped paths don't block or falsely pass validation.

## DAG-level idempotency and concurrency defaults

- Default new DAGs to `catchup=False` — silently backfilling on first deploy is rarely the
  intended behavior and can flood downstream systems.
- Set `max_active_runs=1` for pipelines whose runs cannot safely overlap (e.g. anything
  doing incremental merge against a single target table), to prevent resource contention
  and inconsistent writes.

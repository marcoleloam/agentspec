# Authoring kb_bench tasks

A task is one realistic data-engineering request that an agent completes in an
empty-ish workspace, plus deterministic evals that decide PASS/FAIL. The same
task runs in four knowledge arms (current KB, Context7, lean KB + Context7,
nothing); only the knowledge source differs.

## Hard rule — do not read the KB

When writing **tasks, fixtures, solutions or evals**, never open anything under
`.claude/kb/`, `plugin/kb/`, `plugin-grok/kb/` or `scripts/kb_bench/kb_lean/`.
Author from business intent and **current official documentation** (your own
knowledge of the upstream docs). Tasks derived from KB content would bias the
benchmark toward the KB arm. Record the source in `authored_from`.

## Layout

```text
scripts/kb_bench/
├── tasks/<domain>/<id>.toml        # the task
├── fixtures/<domain>/<id>/…        # starting files copied into the agent workspace (optional)
└── solutions/<id>/…                # reference solution overlaid on the fixtures (required)
```

`<id>` = `<domain>-NN-<slug>`, e.g. `airflow-02-dataset-trigger`. The file name
must equal the id. Domains and strata are fixed:

| domain | stratum |
|--------|---------|
| dbt, airflow | library |
| medallion, data-modeling | conceptual |
| microsoft-fabric, shadowtraffic | niche |

## Task file

```toml
id = "airflow-01-daily-orders"
domain = "airflow"
stratum = "library"
origin = "synthetic"
authored_from = "Apache Airflow 3.1 docs (TaskFlow API); not derived from .claude/kb"
fixtures = "fixtures/airflow/airflow-01-daily-orders"
prompt = """
<What to build, in business terms. Name the exact files, identifiers and
target versions the evals will check (paths, model/table/DAG names). Do NOT
describe HOW — the knowledge arm is what we are measuring.>
"""

[[evals]]
name = "dag parses with Airflow 3 idioms"
cmd = ["python", "-m", "kb_bench.checks.airflow_ast", "dags/daily_orders.py",
       "--dag-id", "daily_orders", "--require-schedule-kw", "--forbid", "schedule_interval"]
```

Evals run **after** the agent, on a copy of its workspace (cwd = workspace
root), with the eval venv first on `PATH` (`python`, `dbt`) and `scripts/` on
`PYTHONPATH`. Each eval passes when the command exits 0. Available checkers
(`python -m kb_bench.checks.<name> --help`):

| checker | use it for |
|---------|------------|
| `regex_check FILE PATTERN [--absent] [--ignore-case] [--min-count N]` | presence/absence of an idiom |
| `py_ast FILE [--require-import M] [--forbid-import M] [--require-call F] [--forbid-call F] [--require-name N] [--forbid-name N] [--require-string RX]` | Python / `.ipynb` (PySpark notebooks) — never executed |
| `airflow_ast FILE [--dag-id ID] [--require-schedule-kw] [--min-tasks N] [--forbid NAME] [--require-import M] [--require-call F]` | Airflow DAG files — no Airflow install |
| `json_check FILE [--has P] [--eq P=V] [--min-len P=N] [--contains P=S] [--any-key P=RX]` | JSON configs (ShadowTraffic, Fabric pipeline JSON); `*` wildcards |
| `sql_check FILE [--dialect duckdb] [--require-table T] [--require-column T.C] [--require-primary-key T] [--forbid-select-star] [--require-create] [--require-regex RX]` | parse-level SQL (Jinja stripped) |
| `duckdb_sql SQL... [--assert "Q == V"] [--assert-rows "Q == N"] [--assert-empty "Q"]` | **execute** plain SQL against fixture CSVs (file access confined to the workspace) |
| `dbt_manifest target/manifest.json --model M [--materialized X] [--unique-key K] [--incremental-strategy S] [--config K=V] [--has-test T] [--column-test COL:TEST] [--depends-on N] [--has-source S.T] [--has-snapshot N]` | after an eval that runs `dbt parse` |
| plain commands (`test -f`, `dbt parse --project-dir . --profiles-dir .`) | existence, real tool runs |

Evals run in order on the same copy, so a `dbt parse` eval can precede
`dbt_manifest` evals.

## What makes a good task

1. **Discriminates knowledge, not typing.** Check the things that change
   between versions or that practitioners get wrong (Airflow 3 `schedule=` and
   `airflow.sdk`, dbt `unique_key` + `is_incremental()`, SCD2 validity columns,
   Delta `saveAsTable`, ShadowTraffic `_gen` functions). Avoid trivia and
   anything the prompt spells out verbatim.
2. **Name the contract, not the method.** The prompt fixes file paths and
   identifiers so evals are deterministic; it never says which API to use.
3. **Solvable in ≤ 30 agent turns** without network installs (the agent cannot
   pip/npm install; it may run `python3` but not dbt/airflow/spark).
4. **3–6 evals**, each with a clear name. At least one must fail on the
   fixtures alone, and all must pass on fixtures + solution.
5. **Don't over-constrain.** Accept equivalent correct forms (e.g. both
   `from airflow.sdk import dag` and `from airflow.decorators import dag` when
   the point is `schedule=`), otherwise correct work lands in the human queue.
6. Write prompts and identifiers in English.

## Verify before you finish

```bash
cd scripts && python3 -m kb_bench validate --task <id> -v
```

`[ok] … — solution ✓` is required for every task you add.

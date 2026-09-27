# dbt Anti-Patterns

## Staging models with business logic or joins

Staging must be 1:1 with the source: rename and cast only. Putting joins or calculated
business logic (e.g. currency conversion) in staging spreads logic across layers and
makes lineage harder to trust — business logic belongs in intermediate or mart models.

## `SELECT *` in staging

Hides schema drift from the source and silently propagates unwanted columns downstream.
Use an explicit column list with renames.

## No tests on a model

If a model (especially a fact/dimension) has no `unique`/`not_null` tests, duplicates or
nulls corrupt everything built on top of it silently — data quality becomes unknown
rather than absent.

## Incremental model missing the `is_incremental()` guard

Without a `where` clause scoped by `is_incremental()`, an "incremental" model still does a
full table scan/rebuild every run, defeating the purpose of the strategy and wasting
compute.

## Hardcoding schema names

Hardcoded schemas break environment promotion (dev/stage/prod). Use
`generate_schema_name`/`target.schema` so schema resolution stays environment-aware.

## `ref()`-ing a source table directly

Using `ref()` where `source()` is meant (or vice versa) breaks dbt's lineage graph and
source freshness checks. Raw data must always enter through `source()`.

## Exposing internal models as public in dbt Mesh without a contract

Publishing an `int_` or otherwise internal model with `access: public` gives other
projects a dependency on something that was never meant to be stable — any refactor
breaks consumers with no warning. Only stable mart models with `contract: {enforced:
true}` should be published as public.

## Assuming the Fusion Engine is a today drop-in replacement for dbt Core

Fusion is a ground-up Rust rewrite still in beta (GA expected mid-2026); pointing
production runs at it without first comparing compiled output against Core risks silent
behavioral differences (stricter YAML validation, MiniJinja edge cases). Validate in dev,
diff compiled SQL, and promote only after parity is confirmed.

## Skipping tests after `dbt build` on incremental models

Because incremental models only process a slice of data each run, a single skipped test
cycle can let bad rows accumulate undetected across many runs — test every build, not just
full refreshes.

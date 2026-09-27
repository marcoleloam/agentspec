# Anti-Patterns

## Platform-Wide

- **Requiring F64 for Copilot.** Copilot has worked on F2+ since April 2025 —
  don't over-provision capacity based on outdated requirements.
- **Mixing bronze/silver/gold in one Lakehouse.** Separate Lakehouses per
  medallion layer instead, so access control and lifecycle can differ per
  layer.
- **Building custom CI/CD scripts** when the official `fabric-cicd` Python
  library already handles item-specific deployment ordering and
  parameterization.
- **Skipping Git integration for production workspaces.** Without it there is
  no CI/CD, no audit trail, and no safe rollback path.

## Logging & Monitoring

- **No snooze period on a noisy alert rule** — results in hundreds of
  duplicate alerts per hour. Set the snooze period to at least the evaluation
  interval.
- **Querying large Eventhouse tables without a time filter** — full scans
  instead of using the columnar engine's time-based data skipping.
- **Logging error messages without a correlation ID.** Without
  `CorrelationId`/`WorkloadType`/`ErrorCode` on every event, errors can't be
  traced across pipeline stages for root-cause analysis.
- **Using Import mode for a "real-time" dashboard.** Import only refreshes on
  a schedule (minimum ~15 min); DirectQuery against Eventhouse is required for
  sub-minute freshness.

## Data Engineering

- **`Table.Buffer` before a filter in Dataflow Gen2 (M language).** This
  breaks query folding and forces the full table into memory. Filter first so
  the predicate can push down to the source.
- **Writing non-Delta formats into a Lakehouse `Tables/` folder.** Managed
  tables must be Delta; anything else won't register in the metastore or be
  queryable via the SQL endpoint.
- **Creating a shortcut to raw CSV under `Tables/`, expecting SQL access.**
  The SQL endpoint only reads Delta. Put non-Delta sources under `Files/` and
  read them with Spark, or convert the source to Delta first.
- **Relying on shortcuts for row-level security.** RLS is not enforced through
  a shortcut — it must be applied at the source table.
- **Using `CLUSTER BY` for partitioning in Fabric.** Not supported in Fabric's
  Delta implementation — use `PARTITIONED BY` plus `OPTIMIZE ... ZORDER BY`
  for data skipping.
- **Using pandas for large datasets in a Fabric notebook** — out-of-memory
  risk. Use PySpark for the bulk of the data and only pull small subsets into
  pandas.
- **Appending incremental data without dedup.** Plain `append` writes create
  duplicate records on re-runs; use a Delta `MERGE` for upsert semantics
  instead.

## Architecture

- **Using Warehouse for petabyte-scale raw ingestion.** Warehouse is optimized
  for structured analytics, not raw landing — use Lakehouse for bronze first.
- **Provisioning a large capacity SKU (e.g. F512) "just in case" for a small
  team.** Wastes budget with no benefit; start smaller, monitor CU
  utilization, and right-size after 2-4 weeks.
- **One workspace for everything** — dev items, prod data, all teams in the
  same place. No access control, no CI/CD, accidental deletions become
  likely. Separate workspaces per domain and environment instead.

## Data Warehouse

- **Using Import mode "because it's faster."** Direct Lake matches Import
  performance without duplicating data — prefer it and monitor for fallback
  events instead of avoiding Direct Lake.
- **Trying to create indexes in Fabric Warehouse.** Not supported — the
  engine auto-optimizes with V-Order; use partitioning patterns for large
  tables instead.
- **Using `IDENTITY`/`SEQUENCE` for surrogate keys.** Not supported in Fabric
  Warehouse — generate surrogate keys with `ROW_NUMBER()` instead.
- **Using `UPDATE` for SCD Type 2 changes.** This destroys history; expire
  the old row (`is_current = 0`, set `effective_end`) and insert a new
  version instead.
- **Using `INSERT...SELECT` for large materializations.** Prefer `CTAS`
  (`CREATE TABLE AS SELECT`), which writes in parallel with automatic
  V-Order.

## APIs & SDKs

- **Calling the Azure Management API (`management.azure.com`) for Fabric
  operations.** Fabric has its own dedicated API and token scope
  (`api.fabric.microsoft.com`) — ARM endpoints don't apply.

## Governance & Security

- **`SELECT *` on a table with column-level security in effect.** Fails if
  any column is denied; list columns explicitly instead.
- **Assuming Dynamic Data Masking protects data that's copied out (e.g. via
  `SELECT INTO`/CTAS).** A user with `UNMASK` gets unmasked data in the copy;
  masking is not a substitute for access control on derived tables.
- **Granting `UNMASK` without considering RLS.** RLS still applies
  independently — the two layers don't cancel each other, so granting one
  doesn't bypass the other.

## CI/CD & Automation

- **Enabling auto-deployment directly into production without an approval
  gate.** Auto-deploy is appropriate dev -> test; test -> prod should require
  sign-off.
- **Using the same workspace for all environments with manual config
  changes**, instead of one workspace per stage with automated data-source
  and parameter overrides.
- **Connecting the production workspace directly to `main` for live editing.**
  Use a Git-centric flow instead: dev/test/main branches map to dev/test/prod
  workspaces, and prod only updates via PR merge + deployment.
- **Multiple developers editing the same workspace without branching** —
  commits overwrite each other. Use a feature-branch-per-developer workflow
  merged via PR instead.

## AI Capabilities

- **Deploying Copilot-generated DAX (or any AI-generated logic) straight to
  production without validation.** Test against known results and edge cases,
  then peer review, before publishing.
- **Persisting ML models as ad hoc pickle files** instead of registering them
  in the Fabric MLflow registry — breaks versioning and T-SQL `PREDICT()`
  inference.
- **Connecting an AI Skill to 50+ tables with no instructions**, expecting it
  to infer the whole data model. Scope it to 3-5 relevant tables with clear
  column descriptions, explicit instructions, and example questions.

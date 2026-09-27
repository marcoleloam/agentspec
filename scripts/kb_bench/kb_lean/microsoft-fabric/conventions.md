# Conventions

## Naming

| Component | Pattern | Example |
|-----------|---------|---------|
| Workspace | `ws-{domain}-{env}` | `ws-finance-prod` |
| Lakehouse | `lh_{domain}_{layer}` | `lh_finance_bronze` |
| Warehouse | `wh_{domain}` | `wh_finance` |
| Pipeline | `pl_{domain}_{action}` | `pl_finance_daily_load` |
| Notebook | `nb_{domain}_{purpose}` | `nb_finance_silver_transform` |
| Semantic Model | `sm_{domain}_{subject}` | `sm_finance_revenue` |
| Entra ID security group | `sg-fabric-{domain}-{env}-{role}` | `sg-fabric-finance-prod-admin` |

Use Entra ID security groups (not individual users) for workspace role
assignment, one group per workspace per role, and assign the minimum role
needed (least privilege).

## Medallion Layer Responsibilities

- **Bronze:** raw ingestion only — add audit columns (`_ingested_at`,
  `_source_file`, `_source_system`) but no transformations. Schema evolution
  (`mergeSchema`) is allowed here, nowhere else.
- **Silver:** cleansed and conformed — type casting, null/negative-value
  handling, deduplication on business keys (`dropDuplicates`). Apply
  V-Order after writes.
- **Gold:** business-ready aggregations/star schema for consumption. Apply
  V-Order after writes.
- Each layer gets its own workspace (`ws-bronze-{env}`, `ws-silver-{env}`,
  `ws-gold-{env}`) so access control and lifecycle differ per layer instead of
  being mixed in one Lakehouse.

## Structural Conventions

- **Fabric-specific Delta partitioning:** use `PARTITIONED BY` at table
  creation, never `CLUSTER BY` (unsupported in Fabric); use
  `OPTIMIZE ... ZORDER BY` for data-skipping on filter columns, and
  `OPTIMIZE ... VORDER` for Power BI/SQL-endpoint read optimization. The two
  are combinable in one `OPTIMIZE` call.
- **Surrogate keys in Warehouse:** since `IDENTITY`/`SEQUENCE` aren't
  supported, generate them with `ROW_NUMBER() OVER (...)` seeded from the
  current `MAX(surrogate_key)`.
- **Star schema in Warehouse:** keep fact tables narrow (keys + measures +
  degenerate dimensions only), keep dimensions wide (all descriptive
  attributes), use surrogate integer keys for all joins, avoid snowflaking
  (flatten hierarchies into the dimension), and use one fact table per
  business process (sales, inventory, shipments as separate facts).
- **Generator/reference identity:** OneLake shortcuts are read-only,
  zero-copy, and cannot be nested (a shortcut can't point to another
  shortcut); table shortcuts must resolve to Delta format to be visible via
  the SQL endpoint.

## Sensitivity Label Inheritance

- Downstream items (semantic model -> report -> dashboard tile) automatically
  inherit the source's sensitivity label.
- Upstream items are **not** automatically upgraded when a downstream item is
  relabeled higher — an admin must manually relabel upstream.
- Labels propagate across workspace boundaries through shortcuts.
- When multiple sources carry different labels, the derived item takes the
  highest sensitivity label of any source (conflict resolution rule).

## CI/CD Convention

Git-centric branch mapping: `dev` branch -> dev workspace, `test` branch ->
test workspace, `main` branch -> prod workspace, promoted only via PR merge
plus the `fabric-cicd` library — never by editing the prod workspace directly
or connecting it to `main` for live edits.

# dbt Conventions

## Model layer naming and responsibility

| Prefix | Layer | Responsibility |
|--------|-------|-----------------|
| `stg_{source}__{entity}` | Staging | 1:1 with source — rename, cast, dedupe only. No business logic, no joins. |
| `int_{entity}_{verb}` | Intermediate | Joins, filters, calculations — the only layer where business logic belongs. |
| `fct_{event}` | Marts (facts) | Grain-level measurable events. |
| `dim_{entity}` | Marts (dimensions) | Descriptive attributes, SCD history. |
| `snap_{entity}` | Snapshots | SCD Type 2 historical tracking via `dbt snapshot`. |

Folder layout mirrors the prefix: `models/staging/{source}/`, `models/intermediate/`,
`models/marts/{domain}/`.

## dbt Mesh ownership conventions

- `group:` on a model config marks domain ownership boundary.
- `access: public|protected|private` marks the data-product API surface (see decisions.md
  for when to use each).
- `contract: {enforced: true}` is required on any `public` model so schema changes must
  stay backward-compatible.
- `versions:` + `latest_version` let a public model evolve without breaking existing
  consumers pinned to an older version.

## Semantic Layer metric naming

Prefix metrics by owning domain to avoid collisions and make ownership explicit at a
glance, e.g. `finance__revenue`, `marketing__cac`. Keep entity relationships in semantic
models explicit and avoid fan-out joins in the underlying model.

## Macro organization

Macros live under `macros/` (configurable via `macro-paths`); test macros specifically
live under `macros/tests/` so they're discoverable as custom generic tests. Cross-database
macros (e.g. currency conversion, schema name generation) should be written once and
dispatched, rather than duplicated per-adapter.

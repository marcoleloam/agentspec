# CRM customers — silver load

- Fabric workspace: `ws-crm-prod`
- Lakehouse: `lh_crm` (attached as the default lakehouse of the notebook)
- Upstream export: one CSV per day (header row, schema as in `sample_data/`),
  dropped into the lakehouse file area under `landing/customers/`.
- A customer can appear several times in a file or across files; the row with
  the most recent `updated_at` wins.

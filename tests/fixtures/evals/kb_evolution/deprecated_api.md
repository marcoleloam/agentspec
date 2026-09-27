# Fixture: deprecated API mentioned in a KB domain

`dbt.config()` no bloco `{{ config(...) }}` do modelo `stg_orders.sql` usa o
argumento posicional `materialized` sem nome, uma forma deprecada desde o
dbt 1.7 — a forma atual exige `materialized="table"` nomeado.

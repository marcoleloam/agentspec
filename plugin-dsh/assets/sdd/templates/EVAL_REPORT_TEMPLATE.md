# EVAL REPORT: $feature

> Relatório gerado por `eval_runner.py run` a partir do recibo `EVAL_$feature.json`.
> Não edite à mão: o veredito vale pelo recibo, e este arquivo é regenerado a cada `/eval`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | $feature |
| **Veredito** | $verdict_icon **$verdict** |
| **Avaliado em** | $evaluated_at |
| **Commit** | `$commit` |
| **Worktree** | `$worktree_digest` |
| **Contrato de evals** | `$contract_digest` |
| **JEV** | `$jev_model` — calibrado: $jev_calibrated |
| **Runner** | eval_runner $runner_version |

---

## Resumo

$summary_counts

---

## Resultados por Eval

$results_table

**Legenda:** ✅ pass · ❌ fail · 💥 error (eval não conseguiu rodar) · ⏳ pending (aguarda humano ou juiz) · 🟡 waived (aceito com waiver nomeado)

---

## Erros Estruturais

$structural_errors

---

## Avisos

$warnings

---

## Waivers

$waivers_table

---

## Próximo Passo

$next_step

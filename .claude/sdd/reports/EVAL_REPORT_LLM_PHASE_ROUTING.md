# EVAL REPORT: LLM_PHASE_ROUTING

> Relatório gerado por `eval_runner.py run` a partir do recibo `EVAL_LLM_PHASE_ROUTING.json`.
> Não edite à mão: o veredito vale pelo recibo, e este arquivo é regenerado a cada `/eval`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LLM_PHASE_ROUTING |
| **Veredito** | ❌ **FAIL** |
| **Avaliado em** | 2026-09-24T21:28:13Z |
| **Commit** | `9de8ce4722dee440ea2c904b361a5cf84105fa18` |
| **Worktree** | `sha256:79bb4000edefe0afe685fd047e1cb61b35169404828286232070979291c88921` |
| **Contrato de evals** | `sha256:b030f8940483c9ab339160ac6b83f94fab8cf09332f4410d910cb0ef0933067a` |
| **JEV** | `typesafe/jev-1.13` — calibrado: não (JEV apenas consultivo) |
| **Runner** | eval_runner 1.0.0 |

---

## Resumo

✅ pass: 8, ⏳ pending: 5

---

## Resultados por Eval

| Eval | Verifica | Tipo | Origem | Status | Decidido por | Evidência |
|------|----------|------|--------|--------|--------------|-----------|
| `drift_detected` | AT-004 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 24 deselected in 0.03s |
| `repo_in_sync` | AT-005, AT-004 | deterministic | contract | ✅ pass | — | exit 0 — phase routing: in sync with PHASE_MODEL_ROLES.toml |
| `no_concrete_ids` | AT-006 | deterministic | contract | ✅ pass | — | exit 0 |
| `overrides_stdout_only` | AT-008 | deterministic | contract | ✅ pass | — | exit 0 |
| `delegation_blocks` | AT-001, AT-002, AT-009 | deterministic | contract | ✅ pass | — | exit 0 |
| `plugin_agents_flat` | AT-001, AT-003 | deterministic | contract | ✅ pass | — | exit 0 |
| `provenance_rows` | AT-007 | deterministic | contract | ✅ pass | — | exit 0 |
| `full_suite` | AT-004, AT-006, AT-008 | deterministic | contract | ✅ pass | — | exit 0 — OK - plugin-grok/ + .grok/{agents,commands} up to date |
| `omp_design_routed` | AT-001 | human | contract | ⏳ pending (NEEDS_HUMAN) | — | sem atestação |
| `omp_ship_routed` | AT-002 | human | contract | ⏳ pending (NEEDS_HUMAN) | — | sem atestação |
| `omp_without_override` | AT-003 | human | contract | ⏳ pending (NEEDS_HUMAN) | — | sem atestação |
| `omp_interactive_session` | AT-007 | human | contract | ⏳ pending (NEEDS_HUMAN) | — | sem atestação |
| `claude_code_design_subagent` | AT-009 | human | contract | ⏳ pending (NEEDS_HUMAN) | — | sem atestação |

**Legenda:** ✅ pass · ❌ fail · 💥 error (eval não conseguiu rodar) · ⏳ pending (aguarda humano ou juiz) · 🟡 waived (aceito com waiver nomeado)

---

## Erros Estruturais

Nenhum.

---

## Avisos

Nenhum.

---

## Waivers

Nenhum waiver registrado.

---

## Próximo Passo

Gate reprovado. Evals que bloqueiam: `omp_design_routed`, `omp_ship_routed`, `omp_without_override`, `omp_interactive_session`, `claude_code_design_subagent`.

- Corrigir o código: `/continuar LLM_PHASE_ROUTING` e depois `/eval LLM_PHASE_ROUTING`
- Eval `human` pendente: `eval_runner.py attest LLM_PHASE_ROUTING --eval <id> --verdict pass|fail --owner <nome> --evidence <texto>`
- Aceitar conscientemente: `eval_runner.py waive LLM_PHASE_ROUTING --eval <id> --supervisor <nome> --reason <motivo>`

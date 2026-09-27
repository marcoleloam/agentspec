# EVAL REPORT: KB_CONTEXT7_REFRESH

> Relatório gerado por `eval_runner.py run` a partir do recibo `EVAL_KB_CONTEXT7_REFRESH.json`.
> Não edite à mão: o veredito vale pelo recibo, e este arquivo é regenerado a cada `/eval`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_CONTEXT7_REFRESH |
| **Veredito** | ✅ **PASS** |
| **Avaliado em** | 2026-09-27T17:29:39Z |
| **Commit** | `2d8bb0b3cce8df967d09300e898505699f757e64` |
| **Worktree** | `sha256:b564f8e749b9ed7408d98b8b23d61a0e3372fd2f90ceca8e96d467e6cc09b491` |
| **Contrato de evals** | `sha256:5dd9c7f7f6a3a159a2cf5350516eb53cb2aadc3821626d38ec1e7bfe05ffd634` |
| **JEV** | `typesafe/jev-1.13` — calibrado: não (JEV apenas consultivo) |
| **Runner** | eval_runner 1.0.0 |

---

## Resumo

✅ pass: 10

---

## Resultados por Eval

| Eval | Verifica | Tipo | Origem | Status | Decidido por | Evidência |
|------|----------|------|--------|--------|--------------|-----------|
| `eval_1` | AT-001 | deterministic | contract | ✅ pass | — | exit 0 — AT-001 ok: 72 records; ['**aposentar KB**', '**aposentar KB**', '**aposentar KB**'] |
| `eval_2` | AT-002 | deterministic | contract | ✅ pass | — | exit 0 — 18/18 tasks valid |
| `eval_3` | AT-003 | deterministic | contract | ✅ pass | — | exit 0 — 4 passed, 43 deselected in 0.95s |
| `eval_4` | AT-004 | deterministic | contract | ✅ pass | — | exit 0 — 9 passed, 38 deselected in 0.25s |
| `eval_5` | AT-005 | deterministic | contract | ✅ pass | — | exit 0 — 3 passed, 44 deselected in 0.70s |
| `eval_6` | AT-006 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 46 deselected in 0.36s |
| `eval_7` | AT-007 | deterministic | contract | ✅ pass | — | exit 0 — 8 passed, 39 deselected in 0.02s |
| `eval_8` | AT-008 | deterministic | contract | ✅ pass | — | exit 0 — 18/18 tasks valid |
| `eval_9` | AT-009 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 46 deselected in 0.37s |
| `eval_10` | AT-010 | deterministic | contract | ✅ pass | — | exit 0 — AT-010 ok |

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

`/ship .claude/sdd/features/DEFINE_KB_CONTEXT7_REFRESH.md`

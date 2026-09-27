# EVAL REPORT: POST_BUILD_EVALS

> Relatório gerado por `eval_runner.py run` a partir do recibo `EVAL_POST_BUILD_EVALS.json`.
> Não edite à mão: o veredito vale pelo recibo, e este arquivo é regenerado a cada `/eval`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | POST_BUILD_EVALS |
| **Veredito** | ✅ **PASS** |
| **Avaliado em** | 2026-09-24T12:21:39Z |
| **Commit** | `2d8bb0b3cce8df967d09300e898505699f757e64` |
| **Worktree** | `sha256:6b59c9a3fb8a22435cd79cbfd8a5332be69bd77facf52428813cbfbb569a5d22` |
| **Contrato de evals** | `sha256:89a9e4ff6d5f878856ae5466b23b42f6829d9a0c22f962d80738e6c0df8d861b` |
| **JEV** | `typesafe/jev-1.13` — calibrado: não (JEV apenas consultivo) |
| **Runner** | eval_runner 1.0.0 |

---

## Resumo

✅ pass: 17

---

## Resultados por Eval

| Eval | Verifica | Tipo | Origem | Status | Decidido por | Evidência |
|------|----------|------|--------|--------|--------------|-----------|
| `eval_at001` | AT-001 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.41s |
| `eval_at002` | AT-002 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.42s |
| `eval_at003` | AT-003 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.30s |
| `eval_at004` | AT-004 | deterministic | contract | ✅ pass | — | exit 0 — 2 passed, 35 deselected in 0.74s |
| `eval_at005` | AT-005 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.37s |
| `eval_at006` | AT-006 | deterministic | contract | ✅ pass | — | exit 0 — 3 passed, 34 deselected in 0.54s |
| `eval_at007` | AT-007 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.18s |
| `eval_at008` | AT-008 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.16s |
| `eval_at009` | AT-009 | deterministic | contract | ✅ pass | — | exit 0 — 2 passed, 35 deselected in 0.65s |
| `eval_at010` | AT-010 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.41s |
| `eval_at011` | AT-011 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.34s |
| `eval_at012` | AT-012 | deterministic | contract | ✅ pass | — | exit 0 — 2 passed, 71 deselected in 0.28s |
| `eval_at013` | AT-013 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.35s |
| `eval_at014` | AT-014 | deterministic | contract | ✅ pass | — | exit 0 — 3 passed, 70 deselected in 0.37s |
| `eval_at015` | AT-015 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.25s |
| `eval_at016` | AT-016 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.40s |
| `eval_at017` | AT-017 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 36 deselected in 0.20s |

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

`/ship .claude/sdd/features/DEFINE_POST_BUILD_EVALS.md`

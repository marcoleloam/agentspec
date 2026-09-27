# EVAL REPORT: LLM_PHASE_ROUTING

> Relatório gerado por `eval_runner.py run` a partir do recibo `EVAL_LLM_PHASE_ROUTING.json`.
> Não edite à mão: o veredito vale pelo recibo, e este arquivo é regenerado a cada `/eval`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LLM_PHASE_ROUTING |
| **Veredito** | ✅ **PASS** |
| **Avaliado em** | 2026-09-24T22:11:57Z |
| **Commit** | `2522695415aedeca080f434f8c7b9bb094dc884d` |
| **Worktree** | `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| **Contrato de evals** | `sha256:b030f8940483c9ab339160ac6b83f94fab8cf09332f4410d910cb0ef0933067a` |
| **JEV** | `typesafe/jev-1.13` — calibrado: não (JEV apenas consultivo) |
| **Runner** | eval_runner 1.0.0 |

---

## Resumo

✅ pass: 13

---

## Resultados por Eval

| Eval | Verifica | Tipo | Origem | Status | Decidido por | Evidência |
|------|----------|------|--------|--------|--------------|-----------|
| `drift_detected` | AT-004 | deterministic | contract | ✅ pass | — | exit 0 — 1 passed, 24 deselected in 0.23s |
| `repo_in_sync` | AT-005, AT-004 | deterministic | contract | ✅ pass | — | exit 0 — phase routing: in sync with PHASE_MODEL_ROLES.toml |
| `no_concrete_ids` | AT-006 | deterministic | contract | ✅ pass | — | exit 0 |
| `overrides_stdout_only` | AT-008 | deterministic | contract | ✅ pass | — | exit 0 |
| `delegation_blocks` | AT-001, AT-002, AT-009 | deterministic | contract | ✅ pass | — | exit 0 |
| `plugin_agents_flat` | AT-001, AT-003 | deterministic | contract | ✅ pass | — | exit 0 |
| `provenance_rows` | AT-007 | deterministic | contract | ✅ pass | — | exit 0 |
| `full_suite` | AT-004, AT-006, AT-008 | deterministic | contract | ✅ pass | — | exit 0 — OK - plugin-grok/ + .grok/{agents,commands} up to date |
| `omp_design_routed` | AT-001 | human | contract | ✅ pass | human | usuário (dono do AgentSpec): task(design-agent) resolvedModel=openai-codex/gpt-6-astra:max (=slow); Gerado por gpt-6-astra; /tmp/lpr/s-design |
| `omp_ship_routed` | AT-002 | human | contract | ✅ pass | human | usuário (dono do AgentSpec): verify antes; task(ship-agent) resolvedModel=xai-oauth/grok-4.6:xhigh (=smol); Gerado por grok-4.6; ressalva: sessão @plan não delegou (fallback inline, registrado) |
| `omp_without_override` | AT-003 | human | contract | ✅ pass | human | usuário (dono do AgentSpec): sem overrides: /design concluiu; resolvedModel=xai-oauth/grok-4.6:high; Gerado por grok-4.6; /tmp/lpr/s-noov |
| `omp_interactive_session` | AT-007 | human | contract | ✅ pass | human | usuário (dono do AgentSpec): omp --model @plan: 0 task calls, perguntas inline; Gerado por gpt-6-astra (sessão) |
| `claude_code_design_subagent` | AT-009 | human | contract | ✅ pass | human | usuário (dono do AgentSpec): Task agentspec:design-agent; subagent claude-opus-5-5; Gerado por claude-opus-5-5[1m] (via --plugin-dir; cache do marketplace desatualizado) |

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

`/ship .claude/sdd/features/DEFINE_LLM_PHASE_ROUTING.md`

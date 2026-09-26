# BUILD REPORT: Living Memory (Segundo Cérebro entre Fases)

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | LIVING_MEMORY |
| **Data** | 2026-09-23 |
| **Autor** | build-agent |
| **DEFINE** | [DEFINE_LIVING_MEMORY.md](../features/DEFINE_LIVING_MEMORY.md) (v1.1) |
| **DESIGN** | [DESIGN_LIVING_MEMORY.md](../features/DESIGN_LIVING_MEMORY.md) |
| **BLACKBOARD** | [BLACKBOARD_LIVING_MEMORY.md](../features/BLACKBOARD_LIVING_MEMORY.md) |
| **Status** | Completo (com validação manual pendente — ver AT-001/002/003/011) |

---

## Resumo

| Métrica | Valor |
|---------|-------|
| **Tarefas Concluídas** | 30/30 itens do manifesto |
| **Arquivos Criados** | 5 fontes novas (script, teste, 9 fixtures, doc, Blackboard) + 2 cópias geradas do script |
| **Arquivos Modificados (fonte)** | 26 (template, contrato, 9 agentes, 11 comandos, `/memory`, hook, `.gitignore`, CHANGELOG) |
| **Linhas de Código** | 586 (`memory-index.py`) + 366 (testes) |
| **Testes Passando** | 93/93 na suíte (52 novos em `test_memory_index.py`) |
| **Cobertura** | 98% de `memory-index.py` (meta SC-6: ≥ 80%) |
| **Agentes Utilizados** | 1 (build-agent direto — ver Desvios, D-018) |

---

## Execução de Tarefas com Atribuição de Agentes

| # | Arquivo | Agente previsto | Executado por | Status |
|---|---------|-----------------|---------------|--------|
| 1 | `.claude/sdd/templates/BLACKBOARD_TEMPLATE.md` | (direto) | build-agent | ✅ |
| 2 | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | (direto) | build-agent | ✅ |
| 3 | `plugin-extras/scripts/memory-index.py` | @python-developer | build-agent | ✅ |
| 4 | `tests/fixtures/memory/` | @test-generator | build-agent | ✅ |
| 5 | `tests/test_memory_index.py` | @test-generator | build-agent | ✅ |
| 6 | `plugin-extras/scripts/init-workspace.sh` | @shell-script-specialist | build-agent | ✅ |
| 7 | `.gitignore` | (direto) | build-agent | ✅ |
| 8–16 | 9 agentes de workflow (`## Phase Memory`) | (direto) | build-agent | ✅ |
| 17–26 | 10 comandos de workflow | (direto) | build-agent | ✅ |
| 27 | `.claude/commands/core/memory.md` | (direto) | build-agent | ✅ |
| 28 | `docs/concepts/living-memory.md` | @code-documenter | build-agent | ✅ |
| 29 | `CHANGELOG.md` | (direto) | build-agent | ✅ |
| 30 | Bundles `plugin/`, `.codex/`, `plugin-grok/`, `.grok/`, `plugin-dsh/assets/` | (direto) | `build-plugin.sh` + geradores | ✅ |

---

## Arquivos Criados

| Arquivo | Propósito |
|---------|-----------|
| `plugin-extras/scripts/memory-index.py` | `brief` / `gate` / `tail` / `build`; stdlib pura |
| `tests/test_memory_index.py` | 52 testes: unitários, CLI, dados reais do `archive/`, restrições |
| `tests/fixtures/memory/` | Árvore `sdd/` + `kb/_index.yaml` mínima: Blackboard novo, legado, com 🔴, archive com e sem acento, `MEMORY.md`, `.active` |
| `docs/concepts/living-memory.md` | Conceito, tipos de entrada, comandos, limites, compatibilidade |
| `.claude/sdd/features/BLACKBOARD_LIVING_MEMORY.md` | Trajetória desta própria feature (23 D, 5 A, 9 Q) |
| `plugin/scripts/memory-index.py`, `plugin-grok/scripts/memory-index.py` | Cópias geradas pelo build (não editar) |

---

## Resultados de Verificação

### Verificação de Lint

```text
$ uvx ruff check plugin-extras/scripts/memory-index.py tests/test_memory_index.py
All checks passed!          (1 ajuste aplicado: re.M → re.MULTILINE)

$ shellcheck -S warning plugin-extras/scripts/init-workspace.sh
(sem avisos)

$ ruby -ryaml -e 'YAML.load_file(".claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml")'
yaml-ok
```

### Verificação de Tipos

Não há type checker configurado no repositório; o script usa type hints em todas as funções.

### Testes

```text
$ uv run --with pytest --with pytest-cov python -m pytest tests/ -q --cov=memory_index
93 passed in 0.34s
plugin-extras/scripts/memory-index.py   418 stmts   7 miss   98%
```

Rodado com Python 3.11 (mesma versão da CI). `pytest` não está instalado no `python3` do sistema desta máquina, por isso os testes rodaram via `uv`; a CI instala `pytest` e roda `python3 -m pytest tests/`.

### Drift dos Geradores

```text
agent-router: clean   codex-plugin: clean   dsh-bundle: clean   grok-plugin: clean
```

---

## Problemas Encontrados

| # | Problema | Resolução |
|---|----------|-----------|
| 1 | `dataclass` + `from __future__ import annotations` falha quando o módulo é carregado por `importlib` sem registro em `sys.modules` | Loader dos testes registra o módulo antes do `exec_module` |
| 2 | Por recência pura, as lições do SHIPPED (data do ship) escondiam as decisões do DESIGN na faixa entre features | Faixa alterna D e L (D-020, substitui D-012) |
| 3 | Não existe domínio KB `kb`; AT-007 do DEFINE citava "domínio `kb`" | Teste usa `genai`, que é domínio real do KB_EVOLUTION (D-021) |
| 4 | Feature nova, ao entrar no Define, ainda não tem DEFINE nem Blackboard para declarar domínios | Brief aceita `--domains`; cascata passa a ler também a linha "Domínios KB" do BRAINSTORM (D-019, substitui D-013) |
| 5 | Edição por Python converteu `WORKFLOW_CONTRACTS.yaml` de CRLF para LF (diff de 985 linhas) | CRLF restaurado; bundles regenerados; diff final com 110 remoções no total |
| 6 | `/ship` não arquivava nem limpava o `BRAINSTORM_{FEATURE}.md` | Corrigido no Step 3 e Step 6 (D-022) |
| 7 | Células com `\|` escapado quebravam o parser de tabela | `split_row` respeita pipes escapados (teste dedicado) |

---

## Desvios do Design

Todos registrados no Blackboard como `D-###` de fase `build`:

| ID | Desvio | Substitui | Motivo |
|----|--------|-----------|--------|
| D-018 | Script, testes, hook e doc escritos pelo build-agent, sem delegar a @python-developer / @test-generator / @shell-script-specialist / @code-documenter | — (atribuição do manifesto) | Parser e testes evoluíram juntos; menos repasse de contexto |
| D-019 | Cascata de domínios inclui a linha do BRAINSTORM; `brief --domains` | D-013 (Decisão 6) | Feature nova no Define sem DEFINE/Blackboard |
| D-020 | Faixa entre features alterna decisão e lição | D-012 (Decisão 5) | Recência pura escondia decisões |
| D-021 | AT-007 com domínio `genai` | — | Domínio `kb` não existe |
| D-022 | `/ship` arquiva e limpa BRAINSTORM | — (aditivo) | Archive perdia a fase 0 |
| D-023 | Env `AGENTSPEC_MEMORY_TAIL` (padrão 5) | — (aditivo) | Ajuste sem editar o hook |

---

## Bloqueadores (se houver)

Nenhum 🔴 no Blackboard (`memory-index.py gate LIVING_MEMORY --to build` → exit 0).
Q-009 está `🟡 Delegada ao ship` (validação manual, abaixo).

---

## Verificação dos Testes de Aceitação

| ID | Cenário | Status | Evidência |
|----|---------|--------|-----------|
| AT-001 | Blackboard nasce no Brainstorm | ⏳ Manual | Instrução em `brainstorm-agent.md` / `brainstorm.md` Step 8; formato do resultado coberto pelas fixtures. Não exercitado numa sessão real |
| AT-002 | Blackboard nasce no Define | ⏳ Manual | Idem, `define-agent.md` / `define.md` Step 6b |
| AT-003 | Design aponta, não copia | ⏳ Manual | Idem, `design-agent.md` / `design.md` Step 7b; o Blackboard desta feature segue o formato (9 D com âncora verificada) |
| AT-004 | Desvio no Build | ✅ | `test_brief_excludes_superseded_and_fits_budget`, `test_current_drops_superseded` |
| AT-005 | Bloqueio Define→Design | ✅ | `test_gate_blocks_on_open_question` (exit 1, lista Q-003) |
| AT-006 | Sem bloqueio Brainstorm→Define | ✅ | `test_gate_rejects_ungated_transition` (`--to define` não é aceito) |
| AT-007 | Memória entre features | ✅ | `test_brief_includes_other_features_sharing_domain`, `test_real_archive_pointer_exists` (âncoras reais resolvem) |
| AT-008 | Retomada entre sessões | ✅ | `test_tail_uses_active_feature_and_limits` + execução real do `init-workspace.sh` num diretório temporário |
| AT-009 | Índice determinístico e descartável | ✅ | `test_build_is_deterministic_and_recreatable` |
| AT-010 | Compatibilidade retroativa | ✅ | `test_legacy_blackboard_defaults_to_build_phase`, `test_status_dashboard_reads_legacy_and_new_blackboards` |
| AT-011 | Ship consolida | ⏳ Manual | Instrução em `ship.md` Steps 8–9; `collect` lê `MEMORY.md` (`test_memory_md_headings_become_lessons`) |
| AT-012 | Tamanho limitado | ✅ | `test_brief_caps_long_history_with_footer`, `test_brief_respects_custom_budget` |

**Critérios de sucesso:** SC-3, SC-4 (10 D + lições dos 2 SHIPPED no archive real), SC-5, SC-6 (98%), SC-7, SC-8 (teste de imports), SC-9 (geradores limpos, script em `plugin/` e `plugin-grok/`) e SC-10 verificados por teste. SC-1 e SC-2 dependem do comportamento dos agentes em features futuras (mesma pendência de AT-001/002/003/011).

---

## Notas de Performance

| Operação | Resultado | Meta |
|----------|-----------|------|
| `memory-index.py build` no repo real (66 entradas) | ~0,07 s | < 2 s (SC-7) |
| Suíte completa | 0,34 s | — |

---

## Validação E2E (Q-009)

Teste real de `/brainstorm` → `/define` → `/design` com `claude -p`, plugin carregado de
`plugin/` via `--plugin-dir` (o `agentspec` instalado desligado), num projeto de exemplo
(`orders-etl`) que não é o AgentSpec. O prompt não mencionava o Blackboard. Execução
headless, sem `AskUserQuestion`; uma a duas execuções por fase.

| Rodada | Blackboard gravado | Script lê as entradas | Chamadas ao script | 🔴 respeitada |
|--------|--------------------|-----------------------|--------------------|---------------|
| 1 — código do build | 2 de 4 fases (brainstorm ✗, define 1/2) | ✗ (coluna `ID`, 8 entradas descartadas em silêncio) | quase nunca; caminho `${CLAUDE_PLUGIN_ROOT:-.}` quebrado | não testado |
| 2 — prompt reforçado + parser + caminho | 4 de 4 | ✓ | puladas (design relatou gate que não rodou) | não testado |
| 3 — + hooks do plugin | 4 de 4 | ✓ | brief injetado, index reconstruído pelo hook | ✗ design fechou a 🔴 por premissa → regra D-027 → ✓ parou e pediu resposta |

Checagem direta do hook: pedir `Write(DESIGN_X.md)` com Q-009 🔴 aberta foi bloqueado pelo
`PreToolUse` e nada foi criado. Correções: DESIGN Decisões 10–13 (Blackboard D-024…D-027).

Lacunas que ficaram: o gate Design→Build segue só no prompt; a ✗→✓ da 🔴 é regra de prompt
(verificada em 1 execução); ponteiros `Onde Ler` às vezes vêm com texto além da âncora.

## Status Final

### Geral: ✅ COMPLETO (código e testes) · ✅ validação E2E do comportamento dos agentes feita (ver Validação E2E)

**Riscos conhecidos:**

- **A-001 continua não validada:** a escrita no Blackboard depende de os agentes seguirem o bloco `## Phase Memory`. A leitura é determinística (script), e o brief avisa `⚠ sem registro nas fases` quando uma fase não registrou nada — mas só uma feature real vai confirmar a captura.
- **A-002 não validada:** a varredura de domínios por texto pode trazer falsos positivos para nomes genéricos (`python`, `testing`); limitado a 4 linhas no brief.
- O `plugin-dsh/assets/` foi regenerado, mas `make dsh-verify` (Node + serviços dsh) não foi executado nesta máquina.

---

## Próximo Passo

1. Validar AT-001/002/003/011 rodando `/brainstorm` → `/design` numa feature de teste (Q-009).
2. **Pronto para:** `/ship .claude/sdd/features/DEFINE_LIVING_MEMORY.md`

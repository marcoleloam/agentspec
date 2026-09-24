# DEFINE: Seleção de Agentes via JEV

> O JEV (TypeSafe, via OpenRouter) decide, a partir da especificação da fase anterior, qual variante de `/define` e `/design` usar (single ou `-multiagent`) e quais especialistas consultar. Quando ele não decide, vale a heurística atual, e a decisão fica registrada no documento.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | JEV_AGENT_SELECTION |
| **Data** | 2026-09-23 |
| **Autor** | define-agent |
| **Status** | Pronto para Design |
| **Clarity Score** | 14/15 |
| **Origem** | `.claude/sdd/features/BRAINSTORM_JEV_AGENT_SELECTION.md` |

---

## Declaração do Problema

A variante de `/define` e `/design` (single ou `-multiagent`) e os especialistas consultados são escolhidos hoje em dois passos. Primeiro, o usuário digita o comando certo. Depois, o LLM conta domínios de KB ("3+ KB domains") e escolhe "top 3-4 por overlap de `kb_domains`". O resultado é agente errado para a spec, sem nenhum registro auditável de por que aquela escolha foi feita.

---

## Usuários-Alvo

| Usuário | Papel | Dor |
|---------|-------|-----|
| Desenvolvedor usando o AgentSpec (plugin ou repo) | Roda o fluxo SDD em projetos reais | Precisa adivinhar quando usar `-m`; recebe especialistas irrelevantes ou fica sem um domínio importante |
| Maintainer do AgentSpec | Evolui agentes e fluxo | Não consegue medir nem auditar se a seleção de agentes está certa |

---

## Objetivos

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | `scripts/jev_select.py` (Python stdlib) recebe o resumo da spec e os candidatos e faz **uma** chamada a `https://openrouter.ai/api/alpha/decisions` (modelo `typesafe/jev-1.13`, `Authorization: Bearer $OPENROUTER_API_KEY`). A chamada leva um `Noul` de variante ("o trabalho fica confinado a uma área técnica?", v1.1) e um `Noul` por especialista candidato. A saída é JSON em stdout. |
| **MUST** | A mesma saída JSON é produzida pelo **fallback determinístico em Python**, que reproduz a heurística atual (≥ 3 domínios de KB → multiagent; top-4 por overlap de `kb_domains`). Formato idêntico, campo `source: "jev" \| "fallback"` e campo `fallback_reason`. |
| **MUST** | Portão (v1.1): a variante é decidida pelo JEV quando `p(single)` sai da faixa de incerteza (padrão 0.4–0.6); `p ≥ 0.5` → single. Dentro da faixa, vale o fallback `uncertain`. Um especialista entra se `Noul ≥ limiar` (padrão configurável, inicial 0.5). Entram no máximo 4, ordenados por probabilidade. Em qualquer outro caso vale o fallback. |
| **MUST** | Fallback nos casos: chave ausente, erro HTTP, timeout (padrão 4 s), resposta inválida, confiança abaixo do limiar, e zero especialistas acima do limiar quando a variante é multiagent. O script **nunca** retorna código de erro que bloqueie a fase. |
| **MUST** | Candidatos pré-filtrados de forma determinística a partir de `.claude/skills/agent-router/routing.json`: agentes cujos `kb_domains` intersectam os domínios da spec, excluindo a categoria `workflow`, e sempre com `python-developer` e `react-developer` (v1.1). Domínios em texto livre são normalizados pelo script (v1.1). |
| **MUST** | `/define` e `/design` chamam o script antes de gerar o documento e **seguem na variante decidida**, podendo subir para a `-multiagent`. `/define-m` e `/design-m` respeitam a variante explícita e usam o script só para os especialistas. |
| **MUST** | DEFINE e DESIGN gerados contêm a seção "Seleção de Agentes" com fonte, variante, probabilidades, especialistas escolhidos (com probabilidade) e motivo do fallback. Os templates DEFINE e DESIGN ganham essa seção. |
| **MUST** | Um conjunto rotulado de **20 specs reais** (ao menos 5 single e 5 multiagent) e um modo de avaliação (`--eval`) que roda JEV e fallback sobre o conjunto e imprime acurácia de variante e F1 de especialistas para cada um. |
| **MUST** | `build-plugin.sh` empacota `jev_select.py` em `plugin/scripts/`; os comandos chamam `${CLAUDE_PLUGIN_ROOT:-.}/scripts/jev_select.py`. |
| **MUST** | Testes pytest com HTTP mockado (sem rede) cobrindo o caminho feliz, todos os motivos de fallback e a normalização de `confidence`. |
| **SHOULD** | Variáveis de ambiente para ajuste sem editar código: `JEV_URL`, `JEV_MODEL`, `JEV_SINGLE_THRESHOLD`, `JEV_UNCERTAIN_BAND`, `JEV_FIT_THRESHOLD`, `JEV_TIMEOUT_MS`, `JEV_DISABLE=1`. |
| **COULD** | Pré-preencher o arquivo de rótulos com a sugestão da heurística, para acelerar a rotulagem manual. |

---

## Critérios de Sucesso

- [ ] **Variante:** num conjunto **holdout** (specs não usadas para ajustar a formulação — v1.1), o JEV atinge acurácia **≥ 85%** e pelo menos **10 pontos percentuais acima** da heurística.
- [ ] **Especialistas:** no mesmo conjunto (casos multiagent), o F1 médio do JEV é **≥ F1 da heurística + 0.10**.
- [ ] **Resiliência:** em 100% dos cenários de falha testados (sem chave, HTTP 4xx/5xx, timeout, JSON inválido, baixa confiança), o script sai com código 0 e `source: "fallback"`.
- [ ] **Latência:** o script adiciona no máximo **5 s** à fase no pior caso (timeout de 4 s mais overhead).
- [ ] **Auditoria:** 100% dos DEFINE e DESIGN gerados após a feature contêm a seção "Seleção de Agentes" preenchida.
- [ ] **Distribuição:** `plugin/scripts/jev_select.py` existe após `./build-plugin.sh`, e `make test` passa.

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Caminho feliz: subir para multiagent | Chave válida; JEV devolve `variant=multiagent`, `confidence=0.9`; 3 candidatos com Noul 0.8, 0.6, 0.2 | `/define BRAINSTORM_X.md` | O fluxo roda `define-multiagent` com os 2 especialistas acima do limiar; o documento registra `fonte: jev` e as probabilidades |
| AT-002 | Caminho feliz: manter single | JEV devolve `variant=single`, `confidence=0.85` | `/design DEFINE_X.md` | Roda `design-agent`, sem consulta a especialistas; a seção registra `fonte: jev` |
| AT-003 | Chave ausente | `OPENROUTER_API_KEY` não definida | `jev_select.py ...` | Exit 0, `source=fallback`, `fallback_reason=missing_key`; a variante segue a regra "≥ 3 domínios" |
| AT-004 | Timeout | O endpoint não responde em 4 s | `jev_select.py ...` | Retorna em ≤ 5 s com `fallback_reason=timeout` |
| AT-005 | Erro HTTP | O endpoint retorna 404 ou 500 | `jev_select.py ...` | Exit 0, `fallback_reason=http_<code>` |
| AT-006 | Incerteza (v1.1) | `p(single)=0.55` | `jev_select.py ...` | `source=fallback`, `fallback_reason=uncertain`; as probabilidades do JEV ficam registradas mesmo assim |
| AT-007 | Domínios em texto livre (v1.1) | `kb_domains=["`tailwind`", "a11y", "sql/postgres", "golang"]` | `jev_select.py ...` | `kb_domains=[tailwind-css, accessibility, sql-patterns]`, `kb_domains_dropped=[golang]` |
| AT-008 | Nenhum especialista acima do limiar | `variant=multiagent` confiante; todos os Nouls < limiar | `jev_select.py ...` | Especialistas pelo fallback (top-4 por overlap), `fallback_reason=no_fit_above_threshold` só para especialistas |
| AT-009 | `-m` explícito | JEV devolve `variant=single` | `/define-m BRAINSTORM_X.md` | A variante multiagent é respeitada; os especialistas vêm do JEV |
| AT-010 | Máximo de 4 | 6 candidatos com Noul ≥ limiar | `jev_select.py ...` | Retorna exatamente os 4 de maior probabilidade |
| AT-011 | Avaliação offline | Arquivo de rótulos com 20 specs | `jev_select.py --eval <rótulos>` | Imprime, para JEV e fallback: acurácia de variante, F1 médio de especialistas e contagem de fallbacks |
| AT-012 | Empacotamento | Repo limpo | `./build-plugin.sh` | `plugin/scripts/jev_select.py` existe e é idêntico à fonte |
| AT-013 | Kill switch | `JEV_DISABLE=1` | `jev_select.py ...` | Nenhuma chamada HTTP; `fallback_reason=disabled` |

---

## Fora do Escopo

- Atribuição de `@agente` por arquivo no manifesto do DESIGN (continua com o `design-agent`).
- Seleção de agentes no `/brainstorm` e no `brainstorm-multiagent`.
- Roteamento ad-hoc fora do fluxo SDD (`agent-router`).
- jev-gateway como proxy do Claude Code.
- Provedores TypeSafe direto e Vercel AI Gateway como opção de primeira classe (só via override de `JEV_URL`).
- Limiares calibrados por fase, ledger de custo e cache de respostas.
- Escolha de modelo LLM por fase (frente `LLM_PHASE_ROUTING`).
- Evals pós-build (frente `POST_BUILD_EVALS`).
- Indexação das decisões em memória viva (frente `LIVING_MEMORY`).
- Corrigir o empacotamento do `judge.py` (problema pré-existente e separado).

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Técnica | O JEV não gera texto; só responde `Choice`, `Score` e `Noul` | O resumo da spec é feito pelo agente da fase, não pelo JEV |
| Técnica | State mais a maior pergunta ≤ 32k tokens; a precisão cai com state irrelevante (jaggedness jev-1.13) | Resumo da spec limitado (ex.: ≤ 4.000 caracteres), com texto excedente truncado |
| Técnica | O endpoint OpenRouter `/api/alpha/decisions` está em alpha | Versão do modelo fixa (`typesafe/jev-1.13`); o fallback cobre quebras |
| Técnica | Python stdlib, sem dependências novas (padrão `judge.py`) | Sem `typesafe-sdk`; HTTP via `urllib` |
| Técnica | A spec vai para um serviço externo (OpenRouter/TypeSafe) | Documentar isso; `JEV_DISABLE=1` desativa o envio |
| Técnica | JEV suscetível a conteúdo adversarial | O state contém só dados da spec; as instruções ficam nas perguntas, nunca no state |
| Idioma | Script, agentes e comandos em inglês; documentos SDD gerados em pt-BR | A seção "Seleção de Agentes" é escrita em pt-BR |
| Recurso | Rotulagem manual de 20 specs pelo maintainer | O critério de sucesso depende desse trabalho estar pronto antes do fim do Build |

---

## Contexto Técnico

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localização de Deploy** | `scripts/jev_select.py`; `tests/test_jev_select.py`; `tests/fixtures/jev/`; `.claude/sdd/evals/agent_selection_labels.yaml` (a confirmar no Design) | Mesmo padrão de `judge.py` e `tests/test_judge.py` |
| **Arquivos alterados** | `.claude/commands/workflow/{define,design,define-m,design-m}.md`; `.claude/agents/workflow/{define-agent,design-agent,define-multiagent,design-multiagent}.md`; `.claude/sdd/templates/{DEFINE,DESIGN}_TEMPLATE.md`; `build-plugin.sh` | Os bundles gerados (plugin, Codex, Grok, DSH) são regenerados pelo build |
| **Domínios KB** | `genai`, `prompt-engineering`, `python`, `testing` | Roteamento com confiança; cliente HTTP stdlib; pytest com mocks |
| **Impacto IaC** | Nenhum | Só variável de ambiente `OPENROUTER_API_KEY` (já usada pelo Judge Layer) |

---

## Premissas

| ID | Premissa | Se Errada, Impacto | Validada? |
|----|----------|-------------------|-----------|
| A-001 | A conta OMP no OpenRouter tem acesso a `/api/alpha/decisions` com `typesafe/jev-1.13` | A feature só roda em fallback; seria preciso usar a API TypeSafe direta via `JEV_URL` | [ ] |
| A-002 | O OpenRouter aceita e devolve o mesmo corpo da API nativa (`state`, `model`, `questions` → `answers`, `usage`), como afirma o jev-gateway | Parser precisa de um adaptador por provedor | [ ] |
| A-003 | A latência típica do JEV é bem menor que 4 s (cookbook: ~0,1–0,3 s por chamada) | O timeout vira fallback frequente; seria preciso subir o timeout | [ ] |
| A-004 | Os `kb_domains` em `routing.json` bastam para pré-filtrar candidatos sem excluir o especialista certo | O recall de especialistas fica limitado pelo pré-filtro; seria preciso incluir `category` e `description` | [ ] |
| A-005 | As 20 specs escolhidas (repo arquivado + projetos em `~/projetos`) representam o uso real | As métricas não generalizam | [ ] |
| A-006 | A spec contém os domínios de KB explicitamente, ou o agente consegue extraí-los para o resumo | O pré-filtro recebe domínios vazios; seria preciso fallback para a categoria | [ ] |

**Nota:** A-001 e A-002 devem ser validadas com uma chamada manual antes ou no início do Design.

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | 3 | Ponto de falha localizado (`define-m.md:52`, `design-m.md:53`, `design-multiagent.md:89-90`) |
| Usuários | 2 | Duas personas claras; sem distinção entre usuário do plugin e usuário do repo além do empacotamento |
| Objetivos | 3 | MUST/SHOULD/COULD com comportamento verificável |
| Sucesso | 3 | Metas numéricas (≥ 85%, +10 p.p., F1 +0.10, ≤ 5 s, 100% fallback) |
| Escopo | 3 | Fora do escopo explícito, com fronteiras para as outras 4 frentes |
| **Total** | **14/15** | |

---

## Questões em Aberto

Nenhuma bloqueia o Design. Para resolver durante o Design ou no início do Build:

1. Validar A-001 e A-002 com uma chamada manual ao endpoint `alpha/decisions`.
2. Limiar inicial do `Noul` de especialista: 0.5 aqui; o cookbook usou 0.30 e o gateway 0.7 (para tools). Calibrar com o conjunto rotulado.
3. Formato e local do arquivo de rótulos (YAML em `.claude/sdd/evals/` ou `tests/fixtures/`).
4. Quem é dono do cliente JEV compartilhado com `POST_BUILD_EVALS` (desenhar `jev_select.py` com o transporte isolado numa função, para extração futura).
5. Se `KB_CONTEXT7_REFRESH` eliminar os KBs, pré-filtro e fallback precisam de outro sinal. Depende daquela frente.

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | define-agent | Versão inicial a partir de BRAINSTORM_JEV_AGENT_SELECTION.md |
| 1.1 | 2026-09-24 | iterate-agent | Cascata do DESIGN v1.1: variante por Noul `single_area` e portão por `p(single)` com faixa de incerteza; implementadores sempre candidatos; normalização de domínios; critério de variante medido em holdout; AT-006/AT-007 revistos; SHOULD de normalização de `confidence` removido |

---

## Próximo Passo

**Pronto para:** `/design .claude/sdd/features/DEFINE_JEV_AGENT_SELECTION.md`

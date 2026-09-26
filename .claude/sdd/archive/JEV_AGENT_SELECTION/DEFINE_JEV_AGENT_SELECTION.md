# DEFINE: Seleção de Agentes por Rubrica

> **Escopo vigente (v1.4):** a LLM da fase decide pela rubrica compartilhada. O JEV permanece como segunda opinião opcional e não altera a decisão. As tentativas anteriores e seus resultados reprovados continuam documentados no DESIGN e no BUILD_REPORT; esta revisão explicita o aceite da solução v1.3 já implementada. As métricas retrospectivas usam rótulos do build-agent, não de um avaliador humano independente.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | JEV_AGENT_SELECTION |
| **Data** | 2026-09-23 |
| **Autor** | define-agent |
| **Status** | ✅ Shipped e arquivado em 2026-09-26 |
| **Clarity Score** | 14/15 |
| **Origem** | `.claude/sdd/features/BRAINSTORM_JEV_AGENT_SELECTION.md` |

---

## Declaração do Problema

A variante de `/define` e `/design` (single ou `-multiagent`) e os especialistas consultados precisam refletir o trabalho real da spec e deixar uma justificativa auditável. A regra antiga de contar domínios KB atingiu 0.46 de acurácia de variante e 0.19 de F1 de especialistas nos 46 casos retrospectivos. As versões v1.0–v1.2 do JEV melhoraram parte do resultado, mas não atingiram as metas originais; a v1.3 passou a usar a LLM da fase com uma rubrica única.

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
| **MUST** | `/define` e `/design` aplicam o mesmo bloco de `.claude/sdd/architecture/AGENT_SELECTION_RUBRIC.md` à spec de entrada para escolher `single` ou `multiagent` e até quatro especialistas do catálogo; a contagem de domínios KB não decide a variante. |
| **MUST** | `/define-m` e `/design-m` mantêm a variante `multiagent` escolhida explicitamente e usam a rubrica para os especialistas. |
| **MUST** | Os documentos gerados registram variante, fonte `llm (rubrica)` ou `locked`, justificativa, especialistas com motivo e o estado da segunda opinião JEV na seção "Seleção de Agentes". |
| **MUST** | `JEV_SECOND_OPINION=1` executa `jev_select.py` e registra seu resultado, sem substituir a escolha da LLM nem bloquear a fase quando o serviço falha; sem essa variável, não há chamada HTTP. |
| **MUST** | A rubrica medida por `eval_llm_baseline.py` é a mesma aplicada pelos quatro comandos e empacotada nos bundles. O benchmark retrospectivo informa acurácia, F1 e proveniência dos rótulos; não é apresentado como validação humana nem como estimativa de produção. |
| **MUST** | `jev_select.py` continua disponível, com fallback determinístico, limites e testes de resiliência do escopo anterior, para segunda opinião e medição offline. |
| **MUST** | `make check` passa e os bundles Claude, Codex, Grok e DSH incluem os comandos e a rubrica vigentes. |
| **SHOULD** | Uma nova amostra com rótulos do maintainer pode calibrar acurácia de produção após o ship; seu resultado deve ser publicado separadamente do benchmark retrospectivo. |

---

## Critérios de Sucesso

- [x] **Qualidade retrospectiva:** ao menos uma LLM de família diferente da que rotulou os 46 casos obtém acurácia de variante ≥ 0.80, F1 médio de especialistas ≥ 0.40 e supera a regra antiga em ambas as métricas. Publicar contagem, modelo, corpus e ressalva de rótulos do build-agent; essa medição não prova generalização.
- [x] **Fluxo real:** executar `/define` numa spec de uma área e `/design` numa spec de duas áreas em diretórios descartáveis; conferir variante, até quatro especialistas válidos, justificativa e seção de auditoria. Executar `/design` com `JEV_SECOND_OPINION=1` após a correção do snippet e conferir que a segunda opinião é registrada sem governar a variante.
- [x] **Variante explícita:** `/define-m` ou `/design-m` preserva `multiagent` mesmo quando a rubrica ou a segunda opinião sugerem `single`.
- [x] **Resiliência:** todos os cenários de falha de `jev_select.py` testados retornam exit 0 e fallback, inclusive timeout dentro de 5 s; a fase não depende da chave OpenRouter.
- [x] **Distribuição e regressão:** rubrica e comandos sincronizados nos bundles; `make check` passa no código atual.

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Rubrica escolhe multiagent | Spec com frontend e API/banco reais | `/design DEFINE_X.md` | Segue o fluxo multiagent e registra `fonte: llm (rubrica)`, justificativa e até quatro especialistas válidos |
| AT-002 | Rubrica escolhe single | Spec limitada a uma área técnica | `/define BRAINSTORM_X.md` | Segue o fluxo single e registra a decisão justificada na seção "Seleção de Agentes" |
| AT-003 | Chave ausente | `OPENROUTER_API_KEY` não definida | `jev_select.py ...` | Exit 0, `source=fallback`, `fallback_reason=missing_key`; a variante segue a regra "≥ 3 domínios" |
| AT-004 | Timeout | O endpoint não responde em 4 s | `jev_select.py ...` | Retorna em ≤ 5 s com `fallback_reason=timeout` |
| AT-005 | Erro HTTP | O endpoint retorna 404 ou 500 | `jev_select.py ...` | Exit 0, `fallback_reason=http_<code>` |
| AT-006 | Incerteza (v1.1) | `p(single)=0.55` | `jev_select.py ...` | `source=fallback`, `fallback_reason=uncertain`; as probabilidades do JEV ficam registradas mesmo assim |
| AT-007 | Domínios em texto livre (v1.1) | `kb_domains=["`tailwind`", "a11y", "sql/postgres", "golang"]` | `jev_select.py ...` | `kb_domains=[tailwind-css, accessibility, sql-patterns]`, `kb_domains_dropped=[golang]` |
| AT-008 | Nenhum especialista acima do limiar | `variant=multiagent` confiante; todos os Nouls < limiar | `jev_select.py ...` | Especialistas pelo fallback (top-4 por overlap), `fallback_reason=no_fit_above_threshold` só para especialistas |
| AT-009 | `-m` explícito | Rubrica ou JEV sugerem `single` | `/design-m DEFINE_X.md` | A variante `multiagent` é respeitada; especialistas vêm da rubrica e a segunda opinião não a altera |
| AT-010 | Máximo de 4 | 6 candidatos com Noul ≥ limiar | `jev_select.py ...` | Retorna exatamente os 4 de maior probabilidade |
| AT-011 | Avaliação retrospectiva | 46 specs rotuladas pelo build-agent, com essa proveniência explícita | `eval_llm_baseline.py` com a rubrica publicada | Acurácia/F1 da LLM e da regra antiga são reproduzidos; limites do corpus são declarados |
| AT-012 | Empacotamento | Repo limpo | `./build-plugin.sh` | `plugin/scripts/jev_select.py` existe e é idêntico à fonte |
| AT-013 | Kill switch | `JEV_DISABLE=1` | `jev_select.py ...` | Nenhuma chamada HTTP; `fallback_reason=disabled` |
| AT-014 | Segunda opinião no `/design` automático | Spec de uma área, `JEV_SECOND_OPINION=1` e `JEV_DISABLE=1` | `/design DEFINE_X.md` após a correção do snippet | Documento registra o fallback `disabled`; a rubrica mantém `single` e a segunda opinião não decide |

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
| 1.2 | 2026-09-25 | iterate-agent | Cascata do DESIGN v1.2: candidatos por ranking amplo em duas etapas; terceiro conjunto a partir de PRDs |
| 1.3 | 2026-09-25 | iterate-agent | Resultado final: critérios de sucesso do JEV não atingidos; baseline LLM superior. Escopo entregue = rubrica aplicada pela LLM da fase + JEV como segunda opinião opcional |
| 1.4 | 2026-09-26 | Codex (iterate) | Critérios e ATs vigentes alinhados à Decisão 16; benchmark retrospectivo identificado como tal; execução real e contrato de evals exigidos antes de ship |
| 1.5 | 2026-09-26 | Codex (ship-agent) | Shipped e arquivado após sete evals PASS; ressalvas retrospectivas preservadas |


---

## Próximo Passo

**Pronto para:** validar o DESIGN v1.4 e executar `/eval JEV_AGENT_SELECTION` após as novas verificações.

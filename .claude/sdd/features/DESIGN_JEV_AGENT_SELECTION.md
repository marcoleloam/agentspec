# DESIGN: Seleção de Agentes via JEV

> Design técnico para que `/define` e `/design` escolham a variante (single ou `-multiagent`) e os especialistas consultados a partir da especificação, via JEV (TypeSafe, pelo OpenRouter), com fallback determinístico e registro auditável.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | JEV_AGENT_SELECTION |
| **Data** | 2026-09-23 |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_JEV_AGENT_SELECTION.md](./DEFINE_JEV_AGENT_SELECTION.md) |
| **Status** | Pronto para Build |

---

## Visão Geral da Arquitetura

```text
┌────────────────────────────────────────────────────────────────────────────┐
│  /define <BRAINSTORM>   /design <DEFINE>   /define-m ...   /design-m ...   │
│        (comando executado pelo Claude — agente da fase)                    │
└───────────────┬────────────────────────────────────────────────────────────┘
                │ 1. monta input JSON: phase, summary (≤4000 chars), kb_domains,
                │    variant_locked (null | "multiagent")
                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  scripts/jev_select.py  (Python stdlib, exit 0 sempre em modo select)      │
│                                                                            │
│  load_routing() ──► prefilter_candidates() ──► heuristic()  (sempre roda)  │
│        │                     │                      │                      │
│        │                     ▼                      │ baseline + fallback  │
│        │            build_request()                 │                      │
│        │                     │                      │                      │
│        │                     ▼                      │                      │
│        │   post_decisions()  ── thread daemon + timeout total ──┐          │
│        │        │                                               │          │
│        │        ▼                                               ▼          │
│        │   parse_answers() ─► normalize_confidence()     TransportError    │
│        │        │                                               │          │
│        │        ▼                                               │          │
│        └──► gate()  ◄───────────────────────────────────────────┘          │
│                 │   variant: p(single) fora de 0.4–0.6 ? jev : heuristic   │
│                 │   specialists: Noul ≥ 0.5 (top 4) ? jev : heuristic      │
│                 ▼                                                          │
│           SelectionResult (JSON em stdout)                                 │
└───────────────┬────────────────────────────────────────────────────────────┘
                │ 2. o comando lê o JSON
                ▼
   variant=single      → segue define-agent / design-agent
   variant=multiagent  → segue o processo de define-m / design-m com os especialistas escolhidos
   sempre              → grava a seção "Seleção de Agentes" no documento gerado

   Externo:  POST https://openrouter.ai/api/alpha/decisions   model typesafe/jev-1.13
   Offline:  jev_select.py --eval labels.json → acurácia de variante + F1 de especialistas (JEV × heurística)
```

---

## Componentes

| Componente | Propósito | Tecnologia |
|------------|-----------|------------|
| `jev_select.py` — núcleo | Pré-filtro, heurística, montagem da requisição, portão, resultado | Python 3.10+ stdlib, dataclasses frozen/slots |
| `jev_select.py` — transporte | `post_decisions()`: única função que faz HTTP; isolada para extração futura (cliente JEV compartilhado com `POST_BUILD_EVALS`) | `urllib.request`, `threading` |
| `jev_select.py` — CLI | Modo `select` (padrão) e modo `--eval` | `argparse` |
| Comandos de fase | Montam o input, chamam o script, seguem a variante e gravam a seção | Markdown (`.claude/commands/workflow/`) |
| Agentes `-multiagent` | Consomem os especialistas escolhidos em vez de calcular o overlap | Markdown (`.claude/agents/workflow/`) |
| Templates DEFINE/DESIGN | Seção "Seleção de Agentes" | Markdown (`.claude/sdd/templates/`) |
| Conjunto rotulado | 20 specs (resumo + domínios + rótulo) para `--eval` | JSON |
| Empacotamento | Copia o script para `plugin/scripts/` e para o bundle Grok | `build-plugin.sh`, `generate-grok-plugin.py` |

---

## Decisões Principais

### Decisão 1: a heurística é reimplementada em Python e roda sempre

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** hoje a heurística ("≥ 3 domínios", "top 3-4 por overlap") é aplicada pelo LLM a partir do texto do prompt. Não é reprodutível e não serve como baseline de avaliação.

**Escolha:** `heuristic()` em Python roda em toda chamada, antes do JEV. O resultado serve de fallback e, no `--eval`, de baseline. Regra: `multiagent` se houver ≥ 3 domínios distintos; especialistas = top 4 por overlap de `kb_domains`, com desempate por nome.

**Justificativa:** o mesmo código produz o fallback e a métrica de comparação, então não existe "heurística do prompt" diferente da "heurística do eval".

**Alternativas Rejeitadas:**
1. Deixar o fallback para o LLM — rejeitada porque não é determinística nem comparável.
2. Heurística nova "melhorada" — rejeitada porque o DEFINE compara o JEV com a regra *atual*.

**Consequências:**
- O fallback reproduz os erros de hoje. Exemplo real, esta própria feature: top-4 = `ai-prompt-specialist`, `ai-prompt-specialist-gcp`, `genai-architect`, `kb-evolution-agent`, sem `python-developer` nem `test-generator`.
- Ganho: baseline mensurável.

---

### Decisão 2: uma requisição com fan-out (1 Choice + N Nouls), candidatos pré-filtrados, no máximo 12

> **v1.1:** a pergunta de variante foi substituída por um Noul (Decisão 9) e o pool de candidatos ganhou implementadores fixos (Decisão 11). O restante desta decisão continua valendo.

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** a doc da TypeSafe não define limite de perguntas por requisição e documenta queda de precisão com state grande e irrelevante. Mandar os 73 agentes num Choice pediria uma escolha de "um" quando precisamos de "vários".

**Escolha:**
- Candidatos = agentes de `routing.json` com `category != "workflow"` e overlap de `kb_domains` ≥ 1, ordenados por overlap desc e nome, limitados a `MAX_CANDIDATES = 12`.
- Uma pergunta `variant` (Choice `single` | `multiagent`) e uma `fit_<i>` (Noul) por candidato.
- A descrição do agente vai no `instructions` do Noul, não no state.

**Justificativa:** mesmo padrão do re-rank do cookbook *Skill suggestion*. O Noul dá probabilidade independente por agente, o que permite multi-seleção. A latência fica em uma ida e volta.

**Alternativas Rejeitadas:**
1. Choice sobre os 73 agentes — rejeitada porque devolve uma distribuição que soma 1, ruim para escolher vários, e o state fica inflado.
2. Duas chamadas (rank amplo + rerank) — adiada (YAGNI); o pré-filtro já reduz a lista.

**Consequências:**
- O recall de especialistas fica limitado pelo pré-filtro (premissa A-004). Um agente sem domínio em comum nunca é candidato.
- Chaves `fit_0..fit_11` evitam depender de regras de nome não documentadas; o mapa índice→agente fica no código.

---

### Decisão 3: `-m` explícito trava a variante e deixa de rebaixar para single

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** hoje `define-m.md:52` e `design-m.md:53` voltam para a variante simples quando há menos de 3 domínios. O DEFINE (AT-009) exige que `-m` explícito respeite a variante.

**Escolha:** `/define-m` e `/design-m` passam `variant_locked: "multiagent"`. O script não pergunta a variante (`variant.source = "locked"`) e só decide os especialistas. O passo "Detect Domains → fall back" sai dos dois comandos.

**Justificativa:** a escolha explícita do usuário prevalece, e a autonomia do JEV vale para os comandos sem sufixo.

**Alternativas Rejeitadas:**
1. Manter o rebaixamento por contagem — rejeitada porque contradiz AT-009.
2. Deixar o JEV rebaixar `-m` — rejeitada na validação do brainstorm.

**Consequências:**
- Mudança de comportamento: `-m` com 1–2 domínios agora roda multiagent. Registrar no CHANGELOG.

---

### Decisão 4: timeout total garantido com thread daemon

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o `timeout` do `urllib` vale por operação de socket, não para a requisição inteira (DNS, connect e leitura somados podem passar de 4 s). O DEFINE exige no máximo 5 s no pior caso.

**Escolha:** `post_decisions()` roda numa `threading.Thread(daemon=True)`; o chamador faz `join(timeout_s)`. Se a thread continuar viva, vale `fallback_reason = "timeout"` e o processo sai sem esperar por ela (daemon).

**Justificativa:** limite de tempo total real sem dependências. `ThreadPoolExecutor` foi evitado porque faz join das threads no encerramento, o que estouraria o limite.

**Alternativas Rejeitadas:**
1. Só `urlopen(timeout=4)` — rejeitada porque não garante tempo total.
2. `signal.alarm` — rejeitada porque não funciona no Windows nem fora da thread principal.

**Consequências:**
- Uma requisição abandonada pode continuar em voo até o processo terminar; aceitável porque o processo é curto.

---

### Decisão 5: o resultado tem uma fonte por decisão; o `source` do topo segue a variante

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** AT-008 pede variante vinda do JEV e especialistas vindos do fallback no mesmo resultado; o DEFINE define `source: "jev" | "fallback"`.

**Escolha:** `variant.source ∈ {jev, fallback, locked}`, `specialists.source ∈ {jev, fallback, none}`, cada um com seu `fallback_reason`. O `source` do topo espelha a decisão primária (a variante, ou os especialistas quando a variante está travada), e o `fallback_reason` do topo é o primeiro motivo encontrado.

**Justificativa:** mantém o contrato do DEFINE e deixa a auditoria precisa.

**Alternativas Rejeitadas:**
1. Um `source` único com valor `"partial"` — rejeitada porque muda o contrato do DEFINE.

**Consequências:**
- A seção do documento mostra as duas fontes separadamente.

---

### Decisão 6: rótulos em JSON; o conjunto completo fica fora do git

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** o repositório não usa PyYAML (stdlib only), e 18 das 20 specs vêm de projetos de clientes em `~/projetos`. Os resumos podem conter informação confidencial.

**Escolha:**
- Formato JSON.
- `tests/fixtures/agent_selection/labels_sample.json` (versionado): 2 casos das features arquivadas deste repo (`FRONTEND_ECOSYSTEM`, `KB_EVOLUTION`).
- `.claude/sdd/evals/agent_selection_labels.json` (conjunto completo de 20): adicionado ao `.gitignore`.

**Justificativa:** não publicar conteúdo de cliente num repositório distribuído; os testes continuam determinísticos com a amostra.

**Alternativas Rejeitadas:**
1. YAML — rejeitada porque exigiria dependência nova.
2. Versionar os 20 — rejeitada por risco de vazamento de conteúdo de cliente.

**Consequências:**
- O resultado do `--eval` sobre os 20 fica registrado no BUILD_REPORT, não em arquivo versionado.

---

### Decisão 7: o script fica em `scripts/` e é copiado explicitamente no build

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** `build-plugin.sh` só leva para `plugin/scripts/` o que está em `plugin-extras/scripts/`, e é por isso que o `judge.py` não é distribuído. Já o `generate-grok-plugin.py:414` copia o `judge.py` explicitamente.

**Escolha:** a fonte fica em `scripts/jev_select.py` (junto com os testes e o `judge.py`). `build-plugin.sh` ganha um `cp` explícito para `plugin/scripts/`, e `generate-grok-plugin.py` passa a copiar o script ao lado do `judge.py`. Um teste de drift compara `plugin/scripts/jev_select.py` com a fonte.

**Justificativa:** uma fonte única, e o mesmo padrão já usado no Grok.

**Alternativas Rejeitadas:**
1. Colocar a fonte em `plugin-extras/scripts/` — rejeitada porque separa o script dos testes e do padrão de `scripts/`.

**Consequências:**
- Os bundles Codex e DSH não levam scripts; nesses casos os comandos caem na regra "script indisponível" (ver Tratamento de Erros).
- Corrigir o empacotamento do `judge.py` continua fora do escopo (DEFINE).

---

### Decisão 8: o comando localiza `routing.json` pelo caminho do próprio script

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-23 |

**Contexto:** no repo o arquivo fica em `.claude/skills/agent-router/routing.json`; no plugin, em `${CLAUDE_PLUGIN_ROOT}/skills/agent-router/routing.json`.

**Escolha:** `resolve_routing_path()` tenta, nesta ordem: `--routing`, `<script>/../.claude/skills/agent-router/routing.json` (repo) e `<script>/../skills/agent-router/routing.json` (plugin). Sem arquivo, não há candidatos, e os especialistas ficam com `fallback_reason = "no_routing"`.

**Justificativa:** funciona nos dois layouts sem depender de variável de ambiente.

**Consequências:**
- Overrides locais de agentes (`.claude/agents/` do projeto do usuário) não entram no `routing.json` do plugin. Aceito no MVP; os candidatos são sempre os agentes do AgentSpec.

---

### Decisão 9 (v1.1): a variante vira um Noul "área técnica única", sem domínios no state

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita — substitui a parte "variante" da Decisão 2 |
| **Data** | 2026-09-24 |

**Contexto:** no eval real (22 specs, 2 rodadas) o Choice `single | multiagent` respondeu `multiagent` em 22/22 casos, com confiança de 0.84 a 1.0. Nenhum dos 8 casos single foi acertado, e a acurácia ficou igual à da heurística (0.64). Perguntar "quantos domínios" junto de uma lista de domínios no state (3+ na maioria das specs) leva à leitura literal que a TypeSafe documenta como limitação do jev-1.13. Num diagnóstico (contaminado, porque foi feito sobre o mesmo conjunto), um Noul sobre "área única" sem domínios no state foi o que mais separou os dois grupos.

**Escolha:** a pergunta `single_area` é um Noul:

> "Is the implementation work in this spec confined to ONE technical area (for example: only frontend screens with mock data, only infrastructure or configuration changes, only a written document)?"

`criteria.true` diz que uma área faz todo o trabalho real e que as outras tecnologias estão mockadas, inalteradas ou só mencionadas. `criteria.false` diz que duas ou mais áreas precisam de implementação nova real. O state leva só `phase` e `spec_summary`; os `kb_domains` saem do state (continuam no pré-filtro local e na heurística).

**Justificativa:** um Noul dá `p(single)` contínuo e calibrado, sem a disputa entre duas opções de um Choice. Os exemplos são **classes genéricas** de trabalho; os exemplos de casos concretos da formulação C foram descartados porque reproduziam casos do conjunto.

**Alternativas Rejeitadas:**
1. Manter o Choice e só tirar `kb_domains` do state (formulação A) — rejeitada: 0/8 single no diagnóstico.
2. Choice com contraexemplos concretos (formulação C, 0.77) — rejeitada: os exemplos vieram dos próprios casos de teste (vazamento).
3. Duas requisições (variante sem domínios, especialistas com domínios) — rejeitada no MVP: o dobro de chamadas, sem evidência de que os especialistas precisem dos domínios no state.

**Consequências:**
- As perguntas de especialista também perdem os domínios do state. O efeito no F1 tem de ser medido no conjunto novo.
- A normalização de `confidence` do Choice (SHOULD do DEFINE) deixa de ser necessária e é removida.

---

### Decisão 10 (v1.1): o portão da variante passa a ser um limiar sobre `p(single)` com faixa de incerteza

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita — substitui o portão `confidence ≥ 0.7` |
| **Data** | 2026-09-24 |

**Contexto:** com a confiança saturada em ~1.0, o portão de 0.7 nunca disparava e não protegia contra erro.

**Escolha:** seja `p = noul(single_area)`:
- `|p − 0.5| < JEV_UNCERTAIN_BAND` (padrão 0.1, ou seja, 0.4 < p < 0.6) → fallback para a heurística, `fallback_reason = "uncertain"`;
- `p ≥ JEV_SINGLE_THRESHOLD` (padrão 0.5) → `single`;
- caso contrário → `multiagent`.

Registra-se `probabilities = {single: p, multiagent: 1 − p}` e `confidence = |p − 0.5| × 2`.

**Justificativa:** os padrões (0.5 e 0.1) são simétricos e **não** foram ajustados sobre nenhum conjunto. A faixa preserva a regra do DEFINE de cair no fallback quando o JEV hesita (o antigo AT-006).

**Alternativas Rejeitadas:**
1. Limiar ajustado para maximizar a acurácia no conjunto de 22 — rejeitada: overfitting no próprio conjunto de teste.
2. Sem faixa de incerteza — rejeitada: perderia o fallback por hesitação exigido pelo DEFINE.

**Consequências:**
- `JEV_MIN_CONFIDENCE` é removida; entram `JEV_SINGLE_THRESHOLD` e `JEV_UNCERTAIN_BAND`.
- `fallback_reason = "low_confidence"` deixa de existir para a variante e dá lugar a `"uncertain"`.

---

### Decisão 11 (v1.1): implementadores gerais são sempre candidatos a especialista

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-24 |

**Contexto:** no eval, os implementadores gerais (`react-developer`, `python-developer`) apareciam nos rótulos esperados de 9 dos 14 casos multiagent. O pré-filtro por overlap e a pergunta do Noul os deixavam de fora com frequência (ex.: C07, F1 0.00).

**Escolha:** `ALWAYS_CANDIDATES = ("python-developer", "react-developer")` sempre entram na lista enviada ao JEV (se existirem no `routing.json`), ocupando vagas dentro do teto de 12: overlap top `12 − k` + os que faltarem. **A heurística continua usando só o overlap**, para seguir sendo o baseline da regra antiga.

**Justificativa:** o JEV decide pelo Noul se o implementador pesa ou não; o pré-filtro só deixa de escondê-lo.

**Alternativas Rejeitadas:**
1. Sempre selecionar os implementadores (sem perguntar ao JEV) — rejeitada: inflaria casos em que não se aplicam (ex.: infra, documento).
2. Incluir também `test-generator` — adiada: não foi pedida e aparece em só 1 rótulo.

**Consequências:**
- Até 2 candidatos por overlap saem da lista quando o pré-filtro já está cheio.

---

### Decisão 12 (v1.1): o script normaliza domínios de KB escritos em texto livre

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-24 |

**Contexto:** nas specs reais a linha "Domínios KB" é texto livre (`tailwind`, `a11y`, `sql/postgres`, `` `frontend/nextjs` ``, `genai (rag-architecture, …)`). O passo 1b dependia de o agente converter isso para nomes reais de KB, e o DESIGN não previa essa conversão.

**Escolha:** `normalize_kb_domains(raw, known)` recebe a lista crua e faz o seguinte:
- remove crases e parênteses;
- quebra em `/`, `,`, `;` e " e ";
- aplica um mapa de aliases (`tailwind`/`css`→`tailwind-css`, `a11y`→`accessibility`, `sql`/`postgres`→`sql-patterns`, `fastapi`→`python`, `llm`/`rag`→`genai`, `databricks`→`lakeflow`...);
- mantém só os nomes conhecidos (a união dos `kb_domains` do `routing.json`).

A saída registra `kb_domains` (normalizados) e `kb_domains_dropped`. O passo 1b passa a pedir que o agente **copie a linha como está**.

**Justificativa:** uma regra determinística e testável no lugar de uma instrução ao LLM.

**Consequências:**
- Termos sem KB correspondente (`golang`, `security`, `azure`) são descartados de forma visível, e não em silêncio.

---

### Decisão 13 (v1.1): a revalidação é feita num conjunto novo, com a formulação congelada antes

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-24 |

**Contexto:** o conjunto de 22 já foi usado para diagnosticar as formulações. Medir de novo nele não prova nada.

**Escolha:**
- As Decisões 9–12 ficam congeladas neste DESIGN **antes** de qualquer consulta ao conjunto novo.
- O conjunto novo (holdout) é formado por specs em `~/projetos` que não estão no conjunto de 22 nem são quase-duplicatas dele.
- O holdout é rotulado às cegas antes da primeira chamada ao JEV e avaliado **uma vez**.
- Os critérios de sucesso do DEFINE (≥ 0.85 e +0.10 p.p.; F1 +0.10) são aplicados ao holdout. O conjunto de 22 é reportado só como referência.

**Consequências:**
- Nenhum limiar pode ser ajustado depois de ver o holdout. Um ajuste exigiria um terceiro conjunto.

---

### Decisão 14 (v1.2): especialistas em duas etapas — ranking amplo e depois Noul na lista curta

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita — substitui o pool da Decisão 11 como fonte principal de candidatos |
| **Data** | 2026-09-25 |

**Contexto:** no holdout, 6 dos 9 casos multiagent não tinham a linha "Domínios KB". Sem ela, o pré-filtro por overlap não devolvia nenhum candidato, sobravam só os 2 implementadores fixos, e o F1 caiu para 0.08. O pool dependia de um campo que specs escritas fora do template não têm (premissa A-004 refutada).

**Escolha:** a seleção passa a ter duas etapas, no mesmo padrão do cookbook *Skill suggestion* da TypeSafe.

1. **Requisição 1 (fan-out):** o Noul `single_area` (a menos que a variante esteja travada) + um **Choice `rank`** sobre o **pool amplo**, que são todos os agentes do `routing.json` fora das categorias `workflow` e `domain` (~60). Cada opção leva a descrição de uma linha do agente, truncada em 120 caracteres. Pergunta: "Which specialist's expertise is MOST needed to get this spec right?" As `WIDE_TOP_K = 8` opções de maior probabilidade formam o ranking.
2. **Requisição 2:** um Noul `fit_i` para cada agente da lista curta. A lista curta tem, nesta ordem de prioridade, `ALWAYS_CANDIDATES` + top 8 do ranking + candidatos por overlap, sem duplicatas e com teto de 12. As perguntas e o portão dos Nouls não mudam.

**Tempo:** `JEV_TIMEOUT_MS` passa a ser o orçamento **total** das duas chamadas; a segunda recebe o que sobrar. Se sobrar menos de 0,5 s, os especialistas vão para o fallback com `fallback_reason = "timeout"`, e a variante já decidida é mantida.

**Falhas:**
- a requisição 1 falha → comportamento de antes (variante e especialistas pela heurística);
- o `rank` vem inválido → a lista curta usa só implementadores + overlap e registra `rank_fallback`;
- a requisição 2 falha → só os especialistas vão para a heurística.

**Justificativa:** o ranking amplo tira a dependência dos `kb_domains` sem mandar ~60 Nouls de uma vez (state maior e mais custo). É a mesma arquitetura rank → rerank que a TypeSafe documenta no cookbook.

**Alternativas Rejeitadas:**
1. Um Noul para cada um dos ~60 agentes numa requisição só — rejeitada: aumenta muito as perguntas e o custo, e não há limite documentado de perguntas por requisição.
2. Etapa ampla só quando faltarem domínios — rejeitada: uma regra condicional a mais, sem evidência de que o overlap seja melhor quando os domínios existem.
3. Incluir a categoria `domain` (agentes de curso/demo como `aide-slide-*` e `shopagent-builder`) — rejeitada: ruído específico de projeto.

**Consequências:**
- Duas chamadas por fase (latência típica ~0,8–1 s; teto continua em `JEV_TIMEOUT_MS`).
- A heurística continua só por overlap, como baseline.
- Nenhum limiar muda: `WIDE_TOP_K = 8` e o teto de 12 foram fixados antes de qualquer medição.

---

### Decisão 15 (v1.2): terceiro conjunto de avaliação a partir de PRDs, com a limitação declarada

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | 2026-09-25 |

**Contexto:** as 37 specs SDD disponíveis já foram usadas (22 no diagnóstico e 15 no holdout). A Decisão 13 exige um terceiro conjunto para qualquer ajuste.

**Escolha:** usar como entrada da fase `define` os PRDs em `~/projetos` (documento válido para `/define`). Eles são rotulados às cegas **antes** da primeira chamada, com hash registrado, e avaliados uma vez. O relatório separa dois grupos:
- os PRDs de produtos que **não** aparecem em nenhum conjunto anterior (independentes);
- os PRDs de produtos cujas DEFINE/BRAINSTORM já foram rotulados (parcialmente independentes: documento novo, produto conhecido pelo rotulador).

**Consequências:**
- O grupo independente é pequeno (~3 casos) e serve como sinal, não como prova. O critério formal do DEFINE é aplicado ao conjunto inteiro, com a ressalva registrada.

---

## Manifesto de Arquivos

| # | Arquivo | Ação | Propósito | Agente | Dependências |
|---|---------|------|-----------|--------|--------------|
| 1 | `scripts/jev_select.py` | Criar | Núcleo, transporte, portão, CLI `select` e `--eval` | @python-developer | Nenhuma |
| 2 | `tests/fixtures/jev/*.json` | Criar | Respostas gravadas: feliz multiagent, feliz single, sem `confidence`, baixa confiança, Noul inválido, todos abaixo do limiar | @test-generator | 1 |
| 3 | `tests/fixtures/agent_selection/labels_sample.json` | Criar | 2 casos rotulados das features arquivadas do repo | (direto) | 1 |
| 4 | `tests/test_jev_select.py` | Criar | Unitários (pré-filtro, heurística, portão, normalização, métricas) e CLI com transporte injetado; AT-003 a AT-008, AT-010, AT-011, AT-013 | @test-generator | 1, 2, 3 |
| 5 | `tests/test_plugin_scripts_sync.py` | Criar | AT-012: `plugin/scripts/jev_select.py` idêntico à fonte | @test-generator | 1, 7 |
| 6 | `.claude/sdd/templates/DEFINE_TEMPLATE.md`, `.claude/sdd/templates/DESIGN_TEMPLATE.md` | Modificar | Seção "Seleção de Agentes" | (direto) | Nenhuma |
| 7 | `build-plugin.sh` | Modificar | `cp scripts/jev_select.py plugin/scripts/` + `chmod +x` | @shell-script-specialist | 1 |
| 8 | `scripts/generate-grok-plugin.py` | Modificar | Copiar `jev_select.py` junto do `judge.py` | @python-developer | 1 |
| 9 | `.claude/commands/workflow/define.md`, `.claude/commands/workflow/design.md` | Modificar | Novo "Step 1b: Agent Selection"; seguir a variante decidida; gravar a seção | (direto) | 1, 6 |
| 10 | `.claude/commands/workflow/define-m.md`, `.claude/commands/workflow/design-m.md` | Modificar | Trocar "Detect Domains → fall back" por seleção com `variant_locked` | (direto) | 1, 6 |
| 11 | `.claude/agents/workflow/define-multiagent.md`, `.claude/agents/workflow/design-multiagent.md` | Modificar | Usar os especialistas da seleção; calcular overlap só se ausente | (direto) | 9, 10 |
| 12 | `.claude/agents/workflow/define-agent.md`, `.claude/agents/workflow/design-agent.md` | Modificar | Incluir a seção "Seleção de Agentes" no output | (direto) | 6 |
| 13 | `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Modificar | Bloco `agent_selection` (entrada, saída, portão, fallback) | (direto) | 1 |
| 14 | `docs/concepts/jev-agent-selection.md` | Criar | Como funciona, variáveis de ambiente, dados enviados ao OpenRouter, `JEV_DISABLE`, como rodar `--eval` | @code-documenter | 1, 9 |
| 15 | `.gitignore` | Modificar | `.claude/sdd/evals/agent_selection_labels.json` | (direto) | Nenhuma |
| 16 | `CHANGELOG.md` | Modificar | Entrada da feature + mudança de comportamento do `-m` (Decisão 3) | (direto) | 9, 10 |
| 17 | `.claude/sdd/evals/agent_selection_labels.json` | Criar (não versionado) | 20 specs rotuladas pelo maintainer (≥ 5 single, ≥ 5 multiagent) | (maintainer) | 1 |

**Total de Arquivos:** 17 entradas (≈ 26 arquivos físicos contando os fixtures e os pares). Os artefatos gerados (`plugin/`, `plugin-grok/`, `plugin-dsh/`, `.codex/`) são regenerados por `make build`, não editados à mão.

---

### Manifesto v1.2 (cascata do iterate)

| # | Arquivo | Ação | Propósito |
|---|---------|------|-----------|
| 23 | `scripts/jev_select.py` | Modificar | Decisão 14: `wide_pool`, `build_rank_request`, `shortlist`, segunda chamada com orçamento restante |
| 24 | `tests/test_jev_select.py` | Modificar | Duas chamadas, falha em cada etapa, `rank` inválido, orçamento, teto de 12 |
| 25 | `WORKFLOW_CONTRACTS.yaml`, `docs/concepts/jev-agent-selection.md`, `CHANGELOG.md` | Modificar | Duas etapas e novas constantes |
| 26 | `.claude/sdd/evals/agent_selection_prd_set.json` (não versionado) | Criar | Terceiro conjunto (Decisão 15) |

### Manifesto v1.1 (cascata do iterate)

| # | Arquivo | Ação | Propósito |
|---|---------|------|-----------|
| 18 | `scripts/jev_select.py` | Modificar | Decisões 9–12: Noul `single_area`, `gate_variant` por `p(single)`, `ALWAYS_CANDIDATES`, `normalize_kb_domains`, state sem domínios; remove `choice_confidence` |
| 19 | `tests/test_jev_select.py`, `tests/fixtures/jev/*.json` | Modificar | Fixtures no formato Noul; AT-006 (`uncertain`) e AT-007 (normalização); implementadores sempre candidatos |
| 20 | `.claude/commands/workflow/{define,design,define-m,design-m}.md` | Modificar | Passo 1b: copiar a linha de domínios como está |
| 21 | `WORKFLOW_CONTRACTS.yaml`, `docs/concepts/jev-agent-selection.md`, `CHANGELOG.md` | Modificar | Novas variáveis e novo portão |
| 22 | `.claude/sdd/evals/agent_selection_holdout.json` (não versionado) | Criar | Conjunto novo, rotulado antes da primeira chamada (Decisão 13) |

## Justificativa de Atribuição de Agentes

| Agente | Arquivos Atribuídos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @python-developer | 1, 8 | Python stdlib com dataclasses e tipagem; mesmo estilo de `judge.py` e dos geradores |
| @test-generator | 2, 4, 5 | pytest com fixtures e transporte injetado, no padrão de `tests/test_judge.py` |
| @shell-script-specialist | 7 | `build-plugin.sh` com sed portável e permissões |
| @code-documenter | 14 | Doc conceitual do usuário |
| (direto) | 3, 6, 9–13, 15, 16 | Edições em prompts, templates e contratos do próprio framework; nenhum especialista acrescenta valor |
| (maintainer) | 17 | A rotulagem precisa de julgamento humano (decidido no DEFINE) |

**Descoberta de Agentes:**
- Escaneado: `.claude/skills/agent-router/routing.json` (73 agentes)
- Correspondido por: tipo de arquivo, propósito e domínios KB (`python`, `testing`)

---

## Seleção de Agentes

> Seção nova introduzida por esta feature, preenchida aqui à mão como dogfooding, porque `jev_select.py` ainda não existe.

| Campo | Valor |
|-------|-------|
| **Fonte da variante** | fallback |
| **Motivo** | `script_unavailable` (a feature ainda não foi construída) e `missing_key` (`OPENROUTER_API_KEY` não exportada nesta sessão) |
| **Variante pela heurística** | multiagent (4 domínios: `genai`, `prompt-engineering`, `python`, `testing`) |
| **Variante executada** | single (`/design` invocado explicitamente antes de a feature existir) |
| **Especialistas pela heurística** | `ai-prompt-specialist`, `ai-prompt-specialist-gcp`, `genai-architect`, `kb-evolution-agent` |
| **Observação** | A escolha da heurística é um exemplo real do problema: especialistas de prompt/GCP/KB para um script Python, sem `python-developer` nem `test-generator`. Incluir este caso no conjunto rotulado. |

---

## Padrões de Código

### Padrão 1: contratos de entrada e saída

```python
# scripts/jev_select.py — tipos principais (frozen + slots, como judge.py)
from __future__ import annotations

from dataclasses import dataclass, field

Variant = str  # "single" | "multiagent"


@dataclass(frozen=True, slots=True)
class Candidate:
    name: str
    category: str
    description: str
    kb_domains: tuple[str, ...]
    overlap: int


@dataclass(frozen=True, slots=True)
class SelectionInput:
    phase: str                          # "define" | "design"
    summary: str                        # truncated to SUMMARY_MAX_CHARS
    kb_domains: tuple[str, ...]
    variant_locked: Variant | None = None


@dataclass(frozen=True, slots=True)
class Decision:
    value: object                        # Variant, or tuple[str, ...] for specialists
    source: str                          # "jev" | "fallback" | "locked" | "none"
    fallback_reason: str | None = None
    confidence: float | None = None
    probabilities: dict[str, float] = field(default_factory=dict)
```

```json
// stdin de `jev_select.py` (montado pelo comando)
{"phase": "design", "summary": "<≤4000 chars>", "kb_domains": ["dbt", "spark"], "variant_locked": null}
```

```json
// stdout (sempre, exit 0)
{
  "version": 1,
  "phase": "design",
  "source": "jev",
  "fallback_reason": null,
  "model": "typesafe/jev-1.13",
  "latency_ms": 312,
  "variant": {"value": "multiagent", "source": "jev", "fallback_reason": null,
              "confidence": 0.91, "probabilities": {"single": 0.09, "multiagent": 0.91}},
  "specialists": {"value": ["dbt-specialist", "spark-engineer"], "source": "jev", "fallback_reason": null,
                  "probabilities": {"dbt-specialist": 0.82, "spark-engineer": 0.64, "sql-optimizer": 0.21}},
  "heuristic": {"variant": "single", "specialists": ["dbt-specialist", "sql-optimizer", "spark-engineer"]},
  "usage": {"input_tokens": 1830, "output_tokens": 40}
}
```

### Padrão 2: montagem da requisição (instruções fora do state)

```python
MODEL = os.environ.get("JEV_MODEL", "typesafe/jev-1.13")
SUMMARY_MAX_CHARS = 4000
MAX_CANDIDATES = 12


def build_request(inp: SelectionInput, candidates: list[Candidate], model: str) -> dict[str, object]:
    """v1.1 — state carries only phase + summary; every instruction lives in a question."""
    questions: dict[str, object] = {}
    if inp.variant_locked is None:
        questions["single_area"] = {
            "type": "noul",
            "instructions": (
                "Is the implementation work in this spec confined to ONE technical area "
                "(for example: only frontend screens with mock data, only infrastructure or "
                "configuration changes, only a written document)?"
            ),
            "criteria": {
                "true": "One area does all the real work; other technologies are mocked, unchanged or only mentioned",
                "false": "Two or more areas (for example frontend AND backend/database AND AI) each need real new implementation",
            },
        }
    for i, cand in enumerate(candidates):
        questions[f"fit_{i}"] = {...}   # unchanged from v1.0
    return {"model": model,
            "state": {"phase": inp.phase, "spec_summary": inp.summary[:SUMMARY_MAX_CHARS]},
            "questions": questions}
```

### Padrão 3: transporte isolado com tempo total garantido

```python
JEV_URL = os.environ.get("JEV_URL", "https://openrouter.ai/api/alpha/decisions")


class TransportError(RuntimeError):
    def __init__(self, reason: str) -> None:   # "http_404", "network", "invalid_json", "timeout"
        super().__init__(reason)
        self.reason = reason


def post_decisions(payload: dict[str, object], api_key: str, timeout_s: float) -> dict[str, object]:
    """The only function that touches the network. Future shared JEV client lives here."""
    box: dict[str, object] = {}

    def _run() -> None:
        req = urllib.request.Request(
            JEV_URL, data=json.dumps(payload).encode(), method="POST",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
                     "HTTP-Referer": "https://github.com/marcoleloam/agentspec",
                     "X-Title": "AgentSpec JEV Agent Selection"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                box["raw"] = resp.read().decode()
        except urllib.error.HTTPError as e:
            box["error"] = f"http_{e.code}"
        except (urllib.error.URLError, OSError):
            box["error"] = "network"

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    worker.join(timeout_s)
    if worker.is_alive():
        raise TransportError("timeout")
    if "error" in box:
        raise TransportError(str(box["error"]))
    try:
        return json.loads(str(box["raw"]))
    except json.JSONDecodeError as e:
        raise TransportError("invalid_json") from e
```

### Padrão 4: portão e normalização

```python
SINGLE_THRESHOLD = float(os.environ.get("JEV_SINGLE_THRESHOLD", "0.5"))   # v1.1
UNCERTAIN_BAND = float(os.environ.get("JEV_UNCERTAIN_BAND", "0.1"))       # v1.1
FIT_THRESHOLD = float(os.environ.get("JEV_FIT_THRESHOLD", "0.5"))
MAX_SPECIALISTS = 4


def gate_variant(answer: object, fallback_variant: str) -> Decision:
    p = noul_value(answer)
    if p is None:
        return Decision(fallback_variant, "fallback", "invalid_response")
    probabilities = {"single": p, "multiagent": round(1 - p, 6)}
    confidence = round(abs(p - SINGLE_THRESHOLD) * 2, 6)
    if abs(p - SINGLE_THRESHOLD) < UNCERTAIN_BAND:
        return Decision(fallback_variant, "fallback", "uncertain", confidence, probabilities)
    return Decision("single" if p >= SINGLE_THRESHOLD else "multiagent", "jev", None, confidence, probabilities)


def gate_specialists(nouls: dict[str, float], fallback: tuple[str, ...]) -> Decision:
    fit = sorted(((n, p) for n, p in nouls.items() if p >= FIT_THRESHOLD), key=lambda t: (-t[1], t[0]))
    if not fit:
        return Decision(fallback, "fallback", "no_fit_above_threshold", probabilities=nouls)
    return Decision(tuple(n for n, _ in fit[:MAX_SPECIALISTS]), "jev", probabilities=nouls)
```

### Padrão 5: seção "Seleção de Agentes" nos templates

```markdown
## Seleção de Agentes

> Gerada por `scripts/jev_select.py` a partir desta especificação. Não editar à mão.

| Campo | Valor |
|-------|-------|
| **Variante** | {single \| multiagent} — fonte: {jev \| fallback \| locked} {(motivo)} |
| **Confiança da variante** | {0.00–1.00 ou —} |
| **Especialistas** | {@agente (p=0.82), @agente (p=0.64) \| nenhum} — fonte: {jev \| fallback \| none} {(motivo)} |
| **Heurística (referência)** | variante {…}; especialistas {…} |
| **Modelo / latência** | {typesafe/jev-1.13} / {N ms} |
```

### Padrão 6: passo nos comandos (define.md / design.md)

```markdown
### Step 1b: Agent Selection

1. From the input document, write a summary (≤ 4000 chars: problem, goals, key constraints)
   and list its KB domains (from "Domínios KB" / "Domínios KB Relevantes").
2. Run:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/jev_select.py <<'JSON'
   {"phase": "design", "summary": "...", "kb_domains": ["..."], "variant_locked": null}
   JSON
   ```

3. If `variant.value == "multiagent"`, continue with the `/design-m` process using
   `specialists.value` as the specialists to consult (skip its own selection).
4. If the script is unavailable (file missing / python3 missing), apply the rule by hand
   (≥ 3 domains → multiagent; top 4 by kb_domains overlap) and record
   `fonte: fallback (script_unavailable)`.
5. Always write the "Seleção de Agentes" section into the generated document.
```

### Padrão 7: formato dos rótulos

```json
{
  "version": 1,
  "cases": [
    {
      "id": "FRONTEND_ECOSYSTEM-design",
      "source_path": ".claude/sdd/archive/FRONTEND_ECOSYSTEM/DEFINE_FRONTEND_ECOSYSTEM.md",
      "phase": "design",
      "summary": "...",
      "kb_domains": ["react", "nextjs", "tailwind-css", "accessibility", "design-systems", "frontend-patterns"],
      "expected_variant": "multiagent",
      "expected_specialists": ["react-developer", "css-specialist", "a11y-specialist", "frontend-architect"]
    }
  ]
}
```

---

## Fluxo de Dados

```text
1. Comando (/define ou /design) lê o documento de entrada
   │
   ▼
2. Agente escreve summary (≤ 4000 chars) + kb_domains; comandos -m adicionam variant_locked
   │
   ▼
3. jev_select.py: resolve routing.json → pré-filtra ≤ 12 candidatos → calcula a heurística
   │
   ▼
4. Checagens locais: JEV_DISABLE? chave ausente? → fallback imediato (sem HTTP)
   │
   ▼
5. POST alpha/decisions (thread daemon, join ≤ JEV_TIMEOUT_MS)
   │
   ▼
6. Parse: answers.variant (Choice) + answers.fit_i (Noul) → validação de tipo/intervalo
   │
   ▼
7. Portão: variante por p(single) com faixa 0.4–0.6 → heurística (v1.1); especialistas (Noul ≥ 0.5, top 4); o que falhar → heurística
   │
   ▼
8. JSON em stdout (exit 0) → comando segue a variante → grava "Seleção de Agentes" no documento
```

---

## Pontos de Integração

| Sistema Externo | Tipo de Integração | Autenticação |
|----------------|-------------------|--------------|
| OpenRouter `POST /api/alpha/decisions` (modelo `typesafe/jev-1.13`) | REST JSON (mesmo corpo da API TypeSafe `v1/systemone`, conforme `jev-gateway/src/providers.json`) | `Authorization: Bearer $OPENROUTER_API_KEY` |
| API TypeSafe direta (opcional) | Mesmo contrato via `JEV_URL=https://api.typesafe.ai/v1/systemone` e `JEV_MODEL=jev-1.13.0` | Bearer (chave TypeSafe, colocada em `OPENROUTER_API_KEY` ou `JEV_API_KEY`) |
| `routing.json` (interno) | Leitura de arquivo | — |

---

## Estratégia de Testes

| Tipo de Teste | Escopo | Arquivos | Ferramentas | Meta de Cobertura |
|---------------|--------|----------|-------------|-------------------|
| Unitário | `prefilter_candidates`, `heuristic`, `build_request`, `choice_confidence`, `gate_*`, `parse_answers`, métricas de eval (acurácia, F1) | `tests/test_jev_select.py` | pytest | ≥ 90% das funções puras |
| Integração (sem rede) | `select()` com transporte injetado: caminho feliz multi/single, cada `fallback_reason`, variante travada, top 4 | `tests/test_jev_select.py` + `tests/fixtures/jev/` | pytest + `monkeypatch` em `post_decisions` | Todos os AT do script (003–008, 010, 011, 013) |
| Timeout real | `post_decisions` contra um servidor local que dorme 3 s, com `JEV_TIMEOUT_MS=500` | `tests/test_jev_select.py` | `http.server` em thread | AT-004 (≤ timeout + 1 s) |
| Drift de empacotamento | `plugin/scripts/jev_select.py == scripts/jev_select.py` | `tests/test_plugin_scripts_sync.py` | pytest | AT-012 |
| E2E manual | `/define` e `/design` em uma spec real, com e sem chave | — | Claude Code | AT-001, AT-002, AT-009 |
| Avaliação offline | `--eval` nos 20 rótulos (precisa de chave) | `.claude/sdd/evals/agent_selection_labels.json` | CLI | Critérios de sucesso do DEFINE |

---

## Tratamento de Erros

| Tipo de Erro | Estratégia de Tratamento | Retry? |
|-------------|-------------------------|--------|
| `JEV_DISABLE=1` | Sem HTTP; `fallback_reason=disabled` | Não |
| Chave ausente | Sem HTTP; `fallback_reason=missing_key` | Não |
| HTTP 4xx/5xx (401, 404, 422, 429, 529...) | `fallback_reason=http_<code>`; uma linha no stderr | Não (o custo de latência não compensa) |
| Rede (DNS, conexão) | `fallback_reason=network` | Não |
| Timeout total | `fallback_reason=timeout`; a thread daemon é abandonada | Não |
| Corpo não-JSON ou sem `answers` | `fallback_reason=invalid_response` | Não |
| `variant` ausente ou com `choice` fora de {single, multiagent} | Variante pela heurística, `invalid_response` | Não |
| `noul` fora de [0, 1] ou não numérico | O candidato é ignorado; se todos forem inválidos → `invalid_response` nos especialistas | Não |
| `p(single)` na faixa de incerteza (0.4–0.6) | Variante pela heurística, `uncertain`; as probabilidades ficam registradas (v1.1) | Não |
| Nenhum Noul ≥ limiar (multiagent) | Especialistas pela heurística, `no_fit_above_threshold` | Não |
| Nenhum candidato ou `routing.json` ausente | Especialistas `none`/`fallback`, `no_candidates` ou `no_routing` | Não |
| stdin inválido | Resultado de fallback com `invalid_input`; exit 0 | Não |
| Script ou `python3` indisponível (bundles Codex/DSH) | O comando aplica a regra à mão e registra `script_unavailable` | Não |
| `--eval` com rótulos inválidos | Exit 2 com mensagem (modo offline não é caminho de fase) | Não |

---

## Configuração

| Chave de Config | Tipo | Padrão | Descrição |
|----------------|------|--------|-----------|
| `OPENROUTER_API_KEY` | string | — | Chave (a mesma do Judge Layer) |
| `JEV_API_KEY` | string | — | Opcional; se definida, tem precedência sobre `OPENROUTER_API_KEY` (uso com `JEV_URL` direto) |
| `JEV_URL` | string | `https://openrouter.ai/api/alpha/decisions` | Endpoint |
| `JEV_MODEL` | string | `typesafe/jev-1.13` | Modelo (versão fixada) |
| `JEV_SINGLE_THRESHOLD` | float | `0.5` | `p(single)` a partir do qual a variante é single (v1.1) |
| `JEV_UNCERTAIN_BAND` | float | `0.1` | Meia-largura da faixa em torno do limiar que cai no fallback `uncertain` (v1.1) |
| `JEV_FIT_THRESHOLD` | float | `0.5` | Limiar do Noul de especialista (calibrar com `--eval`) |
| `JEV_TIMEOUT_MS` | int | `4000` | Tempo total máximo da chamada |
| `JEV_DISABLE` | bool (`1`) | vazio | Desliga o envio; sempre fallback |

---

## Considerações de Segurança

- **Dados enviados:** o resumo da spec (≤ 4000 caracteres) e os domínios de KB vão para OpenRouter e TypeSafe. A doc `jev-agent-selection.md` precisa dizer isso claramente. `JEV_DISABLE=1` desliga o envio.
- **Chave:** lida só do ambiente; nunca é impressa, nem em stderr nem no JSON de saída.
- **Conteúdo adversarial (jaggedness jev-1.13):** o state carrega só dados; todas as instruções ficam nas perguntas. Uma spec maliciosa pode no máximo enviesar a escolha, e a saída é restrita a nomes do `routing.json` (validação por conjunto fechado).
- **Rótulos de clientes:** o conjunto completo fica fora do git (Decisão 6).
- **Execução:** o script não executa nada vindo da resposta; só lê números e nomes validados.

---

## Observabilidade

| Aspecto | Implementação |
|---------|---------------|
| Logging | Uma linha no stderr por chamada: `[jev_select] source=… reason=… latency_ms=…`. Sem conteúdo da spec. |
| Métricas | `latency_ms` e `usage` no JSON; `--eval` imprime acurácia, F1 e contagem de fallbacks por motivo |
| Auditoria | A seção "Seleção de Agentes" em cada DEFINE/DESIGN é o registro permanente |
| Tracing | N/A |

---

## Fronteiras (lembrete para o Build)

| Frente | O que NÃO fazer aqui |
|--------|----------------------|
| `LLM_PHASE_ROUTING` | Não escolher modelo por fase; não ler nem escrever configuração de modelo |
| `POST_BUILD_EVALS` | Não criar um módulo JEV compartilhado; só manter `post_decisions()` isolada |
| `LIVING_MEMORY` | Não gravar decisões fora do documento SDD |
| `KB_CONTEXT7_REFRESH` | Não mudar `kb_domains` nem os KBs; o pré-filtro depende deles como estão |

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-09-23 | design-agent | Versão inicial a partir de DEFINE_JEV_AGENT_SELECTION.md |
| 1.1 | 2026-09-24 | iterate-agent | Após o eval real reprovar (variante 0.64 = heurística): Decisões 9–13, ou seja, Noul `single_area` sem domínios no state, portão por `p(single)` com faixa de incerteza, implementadores sempre candidatos, normalização de domínios em texto livre e revalidação em holdout congelado |
| 1.2 | 2026-09-25 | iterate-agent | Após o holdout reprovar os especialistas (F1 0.08, pré-filtro vazio sem "Domínios KB"): Decisão 14 (duas etapas: Choice `rank` sobre o pool amplo + Noul na lista curta; orçamento de tempo total) e Decisão 15 (terceiro conjunto a partir de PRDs, com limitação declarada) |

---

## Próximo Passo

**Pronto para:** `/build .claude/sdd/features/DESIGN_JEV_AGENT_SELECTION.md`

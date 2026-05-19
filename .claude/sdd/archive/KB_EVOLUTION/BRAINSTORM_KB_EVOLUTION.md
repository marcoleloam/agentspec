# BRAINSTORM: KB Evolution — Ingest/Lint para KBs Vivos

> Sessão exploratória para clarificar intenção e abordagem antes da captura de requisitos

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_EVOLUTION |
| **Data** | 2026-04-22 |
| **Autor** | brainstorm-agent |
| **Status** | ✅ Complete (Defined) |

---

## Ideia Inicial

**Entrada Bruta:** Evolução do sistema de KBs do AgentSpec com LLM Wiki pattern (ingest/lint), para manter KBs frescos e reduzir token cost. Separação de concerns com MemPalace (memória de sessão) e Segundo Cérebro Obsidian (conhecimento pessoal persistente) como produtos independentes.

**Contexto Coletado:**
- AgentSpec tem 39 KB domains, 466 ficheiros, 2.9MB de conhecimento estático
- KBs foram escritos manualmente entre fev-abr 2026, todos com `mcp_validated: 2026-03-26`
- Nenhum mecanismo de atualização existe — conteúdo ficará stale inevitavelmente
- Agents declaram `kb_domains` e carregam ficheiros via Read() nos subagents
- Context7 MCP já está configurado e funcional no projeto
- Karpathy publicou o LLM Wiki pattern (abr 2026): ingest/query/lint para wikis mantidas por LLM
- MemPalace plugin instalado e funcional (3.3.2) — memória de sessão separada
- Obsidian como "Segundo Cérebro" será produto separado — não é escopo desta feature

**Contexto Técnico Observado (para o Define):**

| Aspecto | Observação | Implicação |
|---------|------------|------------|
| Localização Provável | `.claude/commands/`, `.claude/agents/`, `.claude/kb/` | Novos commands + 1 agent + updates nos KB domains |
| Domínios KB Relevantes | Todos os 39 domínios | Feature afeta o sistema de KBs inteiro |
| Padrões IaC | N/A | Sem infraestrutura — tudo local em markdown |
| Deps Externas | Context7 MCP (já existe) | Zero novas dependências |

---

## Perguntas de Descoberta e Respostas

| # | Pergunta | Resposta | Impacto |
|---|----------|----------|---------|
| 1 | Qual é o problema principal com os KBs? | Ambos: conteúdo stale + token cost alto | Feature precisa resolver freshness E eficiência |
| 2 | Quem deve escrever/atualizar o conteúdo KB? | LLM escreve, humano curadoria via /lint-kb | /ingest-kb atualiza automaticamente, /lint-kb é o quality gate |
| 3 | Como os agents consomem os KBs? | Principalmente como subagents (Agent tool) | Cada subagent tem contexto próprio — loading afeta custo por invocação |
| 4 | Quais domínios são prioritários? | Todos (DE core, Cloud, AI+GenAI, Frontend) | /ingest-kb precisa funcionar para qualquer domínio, sem tratamento especial |
| 5 | Já houve problema concreto com KB stale? | Não ainda — KBs têm <1 mês | Mecanismo preventivo, não corretivo. Urgência média, valor alto a longo prazo |

---

## Inventário de Dados de Exemplo

| Tipo | Localização | Quantidade | Notas |
|------|-------------|------------|-------|
| KB domains existentes | `.claude/kb/` | 39 domínios, 466 ficheiros | Estrutura consistente: index.md, quick-reference.md, concepts/, patterns/ |
| Domain registry | `.claude/kb/_index.yaml` | 1 ficheiro, 1606 linhas | Metadata rica: confidence scores, entry_points, mcp_validated |
| KB templates | `.claude/kb/_templates/` | 7 templates | concept, pattern, index, quick-ref, spec, test-case, domain-manifest |
| Context7 MCP | Configurado em settings | 2 tools | resolve-library-id, query-docs |
| Agent prompts com kb_domains | `.claude/agents/` | ~40 agents | Todos declaram kb_domains no frontmatter |

**Como os exemplos serão usados:**
- `_index.yaml` como schema de referência para updates automáticos
- KB templates como guia de formato para o LLM reescrever
- Agent prompts para identificar quais domínios são mais usados (frequência)

---

## Abordagens Exploradas

### Abordagem A: Context7 + LLM Rewrite ⭐ Recomendada

**Descrição:** `/ingest-kb <domain>` usa Context7 MCP para buscar documentação oficial atualizada, compara com o KB existente, e o LLM reescreve os ficheiros que mudaram. `/lint-kb <domain>` audita contradições, conteúdo stale e gaps. Ambos atualizam `log.md` e `_index.yaml`.

**Prós:**
- Zero novas dependências (Context7 já existe)
- Simples e direto — um comando por domínio
- Mantém formato KB existente (index.md, concepts/, patterns/)
- log.md dá visibilidade total do que mudou e quando
- ~50K tokens por domínio (custo previsível)

**Contras:**
- Context7 pode não ter docs para todos os 39 domínios
- Qualidade depende dos docs disponíveis no Context7
- Sem detecção automática de quando atualizar (manual trigger)

**Por que Recomendada:** Menor complexidade, usa infra existente, resolve o problema core (KBs stale) sem introduzir novas ferramentas. A detecção automática (n8n/RSS) pode ser adicionada depois como complemento.

---

### Abordagem B: Context7 + Web Scrape + LLM

**Descrição:** Igual à A, mas adiciona Firecrawl MCP para scraping de changelogs e release notes, capturando breaking changes que Context7 pode não ter.

**Prós:**
- Mais completo — captura changelogs e breaking changes
- Melhor para domínios que mudam rápido (React, Next.js)

**Contras:**
- Mais complexo (2 MCPs + parsing de changelog)
- ~80K tokens por domínio (60% mais caro)
- Changelogs variam muito de formato — parsing frágil
- Firecrawl pode ter rate limits

---

### Abordagem C: n8n Monitora + Context7 Atualiza

**Descrição:** n8n monitora RSS feeds de GitHub releases. Quando detecta versão nova, notifica via Slack/email. Utilizador decide se roda `/ingest-kb`.

**Prós:**
- Detecção automática — nunca perde um release
- Zero tokens para monitoramento
- Utilizador mantém controlo total

**Contras:**
- Requer n8n instance configurada (nem todos os users do AgentSpec têm)
- Não resolve o problema core (atualização) — só detecta
- Complementar à Abordagem A, não substitui

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem A: Context7 + LLM Rewrite |
| **Confirmação do Usuário** | 2026-04-22 |
| **Justificativa** | Menor complexidade, zero novas deps, resolve o core problem. Abordagens B e C podem ser adicionadas como evolução futura. |

---

## Principais Decisões Tomadas

| # | Decisão | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|----------------------|
| 1 | LLM escreve KBs automaticamente, humano curadoria via /lint-kb | 39 domínios é muito para review manual de cada update. /lint-kb é o quality gate periódico. | PR/review para cada ingest (demasiado lento) |
| 2 | Context7 como fonte primária de docs | Já está configurado, zero custo de setup, docs oficiais | Web scraping de changelogs (frágil, mais caro) |
| 3 | Tiered KB loading é YAGNI para agora | Com 1M de contexto, carregar 144K de KB é ~14% — não é bloqueante. Instruir agents a serem seletivos é suficiente. | Tiered loading automático (complexo, sem mecanismo nativo no Claude Code) |
| 4 | MemPalace e Obsidian são produtos separados | Memória pessoal ≠ knowledge base do framework. Cada user configura o seu. AgentSpec não pode depender de Obsidian. | Embutir export Obsidian no AgentSpec |
| 5 | /lint-kb como quality gate periódico | Detecta contradições, stale content, gaps. Funciona como "code review" dos KBs sem bloquear o /ingest-kb | Lint obrigatório antes de cada ingest (overhead desnecessário) |

---

## Features Removidas (YAGNI)

| Feature Sugerida | Motivo da Remoção | Pode Adicionar Depois? |
|------------------|-------------------|----------------------|
| Tiered KB loading (HOT/WARM/COLD) automático | Sem mecanismo nativo de lazy loading no Claude Code. Com 1M contexto, 144K de KB é ~14% — aceitável. Instruir agents a serem seletivos resolve 80% do problema. | Sim — quando custo for bloqueante |
| Export para Obsidian vault | Produto separado — memória pessoal não é do framework | Sim — como plugin "segundo-cerebro" |
| MemPalace integração | Plugin separado já instalável — cada user configura | N/A — já existe |
| Graphify code-awareness | Ferramenta externa — não é KB domain knowledge | Sim — como recomendação em docs |
| n8n RSS monitoring | Requer n8n instance — nem todos os users têm. Complementar, não core. | Sim — como Abordagem C futura |
| Web scraping de changelogs | Frágil, mais caro, variável por formato. Context7 é suficiente para MVP. | Sim — como Abordagem B futura |
| Confidence scoring com temporal decay | Over-engineering para MVP. `mcp_validated` date no `_index.yaml` já dá freshness signal. | Sim — quando tivermos data de uso |

---

## Validações Incrementais

| Seção | Apresentada | Feedback do Usuário | Ajustada? |
|-------|-------------|---------------------|-----------|
| Separação de concerns (AgentSpec vs MemPalace vs Obsidian) | ✅ | "faz total sentido" — confirmou 3 produtos independentes | Não |
| Token cost com 1M de contexto | ✅ | Concordou que tiered loading é YAGNI para agora. Questionou se tiers funcionariam (não há mecanismo nativo). | Sim — removido tiered loading do escopo |
| /ingest-kb e /lint-kb como comandos separados | ✅ | Confirmou que ingest/lint NÃO rodam ao chamar o agent — são manutenção separada | Não |
| Abordagem A (Context7 + LLM rewrite) | ✅ | Selecionou como preferida | Não |

---

## Requisitos Sugeridos para /define

### Declaração do Problema (Rascunho)
Os 39 KB domains do AgentSpec (466 ficheiros, 2.9MB) são estáticos — escritos uma vez e nunca atualizados. Quando libraries evoluem (dbt, Spark, React, etc.), os KBs ficam stale e agents geram código com patterns desatualizados. Não existe mecanismo de atualização nem auditoria.

### Usuários-Alvo (Rascunho)
| Usuário | Dor |
|---------|-----|
| Maintainer do AgentSpec | Precisa manter 39 domínios atualizados sem trabalho manual |
| User do AgentSpec | Recebe respostas com info desatualizada quando KBs ficam stale |
| Contribuidores | Não sabem quais KBs precisam de atualização |

### Critérios de Sucesso (Rascunho)
- [ ] `/ingest-kb <domain>` atualiza um domínio KB em <3 minutos usando Context7
- [ ] `/lint-kb <domain>` produz relatório de problemas (stale, contradições, gaps)
- [ ] `/lint-kb --all` audita todos os 39 domínios e gera relatório consolidado
- [ ] `log.md` por domínio com historial de ingest/lint
- [ ] `mcp_validated` no `_index.yaml` atualizado automaticamente após ingest
- [ ] Agent prompts atualizados com instrução de seletividade nos Read()

### Restrições Identificadas
- Context7 pode não ter docs para todos os 39 domínios (fallback: web search)
- Formato dos KBs existentes deve ser mantido (index.md, quick-ref, concepts/, patterns/)
- `_index.yaml` schema não pode quebrar backwards compatibility
- Zero novas dependências externas (apenas Context7 que já existe)

### Fora do Escopo (Confirmado)
- Tiered KB loading automático — YAGNI com 1M de contexto
- Export para Obsidian — produto separado "segundo-cerebro"
- MemPalace integração — plugin independente já existente
- n8n RSS monitoring — evolução futura (Abordagem C)
- Web scraping de changelogs — evolução futura (Abordagem B)
- Graphify code-awareness — ferramenta externa, docs only
- Confidence scoring com temporal decay — over-engineering para MVP

---

## Resumo da Sessão

| Métrica | Valor |
|---------|-------|
| Perguntas Feitas | 5 |
| Abordagens Exploradas | 3 (A recomendada, B e C alternativas) |
| Features Removidas (YAGNI) | 7 |
| Validações Concluídas | 4 |
| Duração | ~60 min (incluindo research de Karpathy, MemPalace, Context7) |

---

## Próximo Passo

**Pronto para:** `/define .claude/sdd/features/BRAINSTORM_KB_EVOLUTION.md`

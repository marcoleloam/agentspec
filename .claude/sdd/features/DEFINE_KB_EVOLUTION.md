# DEFINE: KB Evolution — Ingest/Lint para KBs Vivos

> Dois comandos (`/ingest-kb` e `/lint-kb`) para manter os 39 KB domains do AgentSpec atualizados via Context7 e reescrita por LLM, com auditoria periódica de qualidade.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_EVOLUTION |
| **Data** | 2026-04-22 |
| **Autor** | define-agent |
| **Status** | ✅ Complete (Built) |
| **Clarity Score** | 14/15 |

---

## Declaração do Problema

Os 39 KB domains do AgentSpec (466 ficheiros, 2.9MB) são estáticos — escritos uma vez e sem mecanismo de atualização. Quando libraries evoluem (dbt, Spark, React, etc.), os KBs ficam stale e agents geram código com patterns desatualizados, degradando a qualidade das respostas sem que o maintainer, os users ou os contribuidores saibam quais domínios precisam de atenção.

---

## Usuários-Alvo

| Usuário | Papel | Dor |
|---------|-------|-----|
| Maintainer do AgentSpec | Responsável por manter os 39 domínios KB atualizados | Não tem como saber quais KBs estão desatualizados nem como atualizá-los sem trabalho manual extensivo |
| User do AgentSpec | Usa agents para gerar código e padrões de data engineering/frontend | Recebe respostas baseadas em patterns desatualizados quando KBs ficam stale sem aviso |
| Contribuidor | Contribui com novos KBs ou melhora existentes | Não tem visibilidade do estado de saúde dos domínios existentes nem sabe por onde começar |

---

## Objetivos

O que significa sucesso (priorizado):

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | `/ingest-kb <domain>` busca documentação atualizada via Context7, compara com o KB existente, e o LLM reescreve os ficheiros que mudaram |
| **MUST** | `/lint-kb <domain>` audita um domínio e produz relatório de contradições, conteúdo stale e gaps em relação à documentação oficial |
| **MUST** | `log.md` por domínio registra historial de todas as operações de ingest e lint com timestamp, versão detectada e resumo das mudanças |
| **MUST** | `mcp_validated` no `_index.yaml` atualizado automaticamente após cada ingest bem-sucedido |
| **SHOULD** | `/lint-kb --all` audita todos os 39 domínios e gera relatório consolidado com priorização por criticidade |
| **SHOULD** | Agent prompts atualizados com instrução explícita de seletividade nos `Read()` para reduzir token cost em subagents |
| **COULD** | Dashboard textual de saúde dos KBs (% de domínios com `mcp_validated` recente, domínios com issues de lint) |

**Guia de Prioridade:**
- **MUST** = O MVP falha sem isso
- **SHOULD** = Importante, mas existe alternativa
- **COULD** = Nice-to-have, cortar primeiro se necessário

---

## Critérios de Sucesso

Resultados mensuráveis:

- [ ] `/ingest-kb <domain>` conclui a atualização de um KB domain em menos de 3 minutos a partir do momento de invocação
- [ ] `/ingest-kb <domain>` produz `log.md` com data, versão da lib detectada e lista dos ficheiros modificados
- [ ] `/ingest-kb <domain>` atualiza `mcp_validated` no `_index.yaml` para a data de execução
- [ ] `/lint-kb <domain>` produz relatório estruturado com pelo menos 3 categorias de issue: conteúdo stale, contradições internas e gaps identificados
- [ ] `/lint-kb --all` processa todos os 39 domínios e entrega relatório consolidado com ranking de domínios por severidade de issues
- [ ] O formato KB existente (index.md, quick-reference.md, concepts/, patterns/) é preservado após ingest — zero ficheiros renomeados ou removidos sem confirmação
- [ ] `/ingest-kb` para domínio sem cobertura no Context7 detecta a ausência e notifica o usuário com instrução de fallback, sem falhar silenciosamente

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Ingest com sucesso via Context7 | Domínio `dbt` existente com `mcp_validated: 2026-03-26` | `/ingest-kb dbt` é executado | KB atualizado, `log.md` criado/atualizado com timestamp e mudanças, `mcp_validated` atualizado no `_index.yaml` |
| AT-002 | Domínio sem cobertura no Context7 | Domínio `medallion` sem library-id no Context7 | `/ingest-kb medallion` é executado | Comando detecta ausência, informa o usuário, sugere fallback (web search manual), não altera ficheiros existentes |
| AT-003 | Lint detecta conteúdo stale | Domínio com API deprecada documentada no KB | `/lint-kb <domain>` é executado | Relatório lista a API deprecada como issue de tipo "stale", com referência ao ficheiro e linha |
| AT-004 | Lint all consolida todos os domínios | 39 domínios com estados variados | `/lint-kb --all` é executado | Relatório consolidado com lista de todos os domínios, contagem de issues por categoria e ranking por severidade |
| AT-005 | Idempotência do ingest | Domínio já atualizado recentemente (sem mudanças na lib) | `/ingest-kb <domain>` é executado novamente | Comando detecta ausência de mudanças relevantes, registra no `log.md` como "no changes detected", não sobrescreve ficheiros |
| AT-006 | Preservação de formato KB | Qualquer domínio existente | `/ingest-kb <domain>` completa com sucesso | Estrutura de diretórios (index.md, quick-reference.md, concepts/, patterns/) preservada; nenhum ficheiro removido sem confirmação explícita |

---

## Fora do Escopo

Explicitamente NÃO incluído nesta feature:

- **Tiered KB loading automático (HOT/WARM/COLD)** — YAGNI: com 1M de contexto, 144K de KB representa ~14%; sem mecanismo nativo de lazy loading no Claude Code
- **Export para Obsidian vault** — produto separado ("segundo-cérebro"); cada user configura o seu
- **MemPalace integração** — plugin independente já existente (v3.3.2); não é escopo do framework
- **n8n RSS monitoring de releases** — evolução futura (Abordagem C); requer n8n instance que nem todos os users do AgentSpec têm
- **Web scraping de changelogs via Firecrawl** — evolução futura (Abordagem B); frágil, 60% mais caro em tokens, variável por formato
- **Graphify code-awareness** — ferramenta externa; documentar como recomendação em docs, não embutir
- **Confidence scoring com temporal decay** — over-engineering para MVP; `mcp_validated` date já fornece o sinal de freshness necessário
- **Interface de aprovação por PR para cada ingest** — overhead desnecessário; `/lint-kb` é o quality gate escolhido

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Técnica | Context7 MCP pode não ter cobertura para todos os 39 domínios | `/ingest-kb` precisa de detecção de ausência e fallback gracioso; alguns domínios podem não ser atualizáveis automaticamente |
| Técnica | Formato dos KBs existentes deve ser mantido (index.md, quick-reference.md, concepts/, patterns/) | LLM rewrite deve operar ficheiro a ficheiro, preservando estrutura; não pode criar nova hierarquia de diretórios |
| Técnica | Schema do `_index.yaml` não pode quebrar backwards compatibility | Updates ao `_index.yaml` são aditivos (ex: adicionar campo `last_lint`) — campos existentes preservados |
| Recurso | Zero novas dependências externas permitidas | Apenas Context7 MCP (já configurado e funcional); nenhum novo MCP, package ou serviço |
| Qualidade | Custo estimado de ~50K tokens por domínio para ingest completo | Aceitável para manutenção periódica; documentar no comando para transparência |

---

## Contexto Técnico

> Contexto essencial para a fase de Design — evita arquivos mal posicionados e necessidades de infraestrutura perdidas.

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localização de Deploy** | `.claude/commands/knowledge/` (comandos), `.claude/agents/workflow/` ou `.claude/agents/dev/` (agent), `.claude/kb/` (log.md por domínio) | Comandos seguem estrutura existente em `.claude/commands/`; agent especializado para orquestrar Context7 + rewrite |
| **Domínios KB** | `prompt-engineering`, `genai`, `python` | Consultar padrões de prompt para LLM rewrite; padrões de multi-step workflows para o agent |
| **Impacto IaC** | Nenhum | Tudo local em markdown; sem infraestrutura, sem serviços externos novos; Context7 MCP já está configurado |

**Por Que Isso Importa:**

- **Localização** → Fase de Design usa a estrutura correta do projeto, evita arquivos mal posicionados
- **Domínios KB** → Fase de Design puxa os padrões corretos de `.claude/kb/`
- **Impacto IaC** → Nenhuma mudança de infraestrutura necessária — feature é 100% local

---

## Premissas

Premissas que, se incorretas, podem invalidar o design:

| ID | Premissa | Se Errada, Impacto | Validada? |
|----|----------|-------------------|-----------|
| A-001 | Context7 tem cobertura para a maioria dos 39 domínios KB do AgentSpec (estimativa: >70%) | Se cobertura for <50%, o valor do `/ingest-kb` é limitado e a Abordagem B (Firecrawl) precisaria ser antecipada | [ ] |
| A-002 | O LLM consegue reescrever ficheiros KB mantendo qualidade e formato sem supervisão humana por ficheiro | Se qualidade for inconsistente, seria necessário um passo de review/diff antes de salvar cada ficheiro | [ ] |
| A-003 | ~50K tokens por domínio é aceitável como custo de manutenção periódica para o maintainer | Se custo for bloqueante, o design precisaria de rewrite seletivo (apenas ficheiros com diff detectado) — o que pode ser necessário de qualquer forma | [ ] |
| A-004 | A estrutura atual de KBs (index.md, quick-reference.md, concepts/, patterns/) é suficientemente consistente para que o LLM reescreva ficheiro a ficheiro sem perder contexto | Se estrutura for inconsistente entre domínios, seria necessário um passo de normalização antes do ingest | [ ] |
| A-005 | `mcp_validated` date no `_index.yaml` é sinal de freshness suficiente para o MVP (sem necessidade de versionamento semântico da lib) | Se maintainer precisar rastrear versão exata da lib (ex: dbt 1.8 vs 1.9), seria necessário adicionar campo `lib_version` ao `_index.yaml` | [ ] |

**Nota:** Valide premissas críticas antes da fase de DESIGN. A-001 e A-002 são as mais críticas para a viabilidade do MVP.

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | 3/3 | Problema específico, quantificado (39 domínios, 466 ficheiros, 2.9MB), com impacto claro nos 3 usuários-alvo |
| Usuários | 3/3 | 3 personas identificadas com papéis distintos e dores específicas; dores são concretas e mensuráveis |
| Objetivos | 3/3 | MoSCoW completo com 4 MUST, 2 SHOULD, 1 COULD; cada objetivo é acionável e mapeado a um entregável |
| Sucesso | 3/3 | 7 critérios mensuráveis com números concretos (<3 min, 3 categorias, 39 domínios); 6 testes de aceitação com formato Given/When/Then |
| Escopo | 2/3 | 8 itens explicitamente fora do escopo com justificativa; restrições técnicas documentadas; perde 1 ponto pois a interface exata do relatório de lint não está especificada (formato livre vs estruturado) |
| **Total** | **14/15** | |

**Guia de Pontuação:**
- 0 = Totalmente ausente
- 1 = Vago ou incompleto
- 2 = Claro mas faltam detalhes
- 3 = Cristalino e acionável

**Mínimo para prosseguir: 12/15**

---

## Questões em Aberto

Nenhuma — pronto para Design.

> Nota para o Design: validar A-001 (cobertura Context7) como primeiro passo — pode ser feito com `resolve-library-id` para os 39 domínios antes de desenhar o fluxo de ingest. O formato do relatório de lint (markdown estruturado vs YAML vs JSON) é decisão de Design, não de Requirements.

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-04-22 | define-agent | Versão inicial — extraída do BRAINSTORM_KB_EVOLUTION.md validado em sessão de 2026-04-22 |

---

## Próximo Passo

**Pronto para:** `/ship .claude/sdd/features/DEFINE_KB_EVOLUTION.md`

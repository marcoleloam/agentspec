# DEFINE: {Nome da Feature}

> Descrição em uma frase do que estamos construindo

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Data** | {YYYY-MM-DD} |
| **Autor** | {autor} |
| **Status** | {Rascunho / Em Andamento / Precisa de Esclarecimento / Pronto para Design} |
| **Clarity Score** | {X}/15 |

---

## Declaração do Problema

{1-2 frases descrevendo o problema que estamos resolvendo. Seja específico sobre quem tem o problema e qual é o impacto.}

---

## Usuários-Alvo

| Usuário | Papel | Dor |
|---------|-------|-----|
| {Usuário 1} | {Papel} | {O que os frustra} |
| {Usuário 2} | {Papel} | {O que os frustra} |

---

## Objetivos

O que significa sucesso (priorizado):

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | {Objetivo primário - inegociável para o MVP} |
| **MUST** | {Outro objetivo crítico} |
| **SHOULD** | {Importante, mas pode ser adiado se o prazo apertar} |
| **COULD** | {Nice-to-have se houver tempo} |

**Guia de Prioridade:**
- **MUST** = O MVP falha sem isso
- **SHOULD** = Importante, mas existe alternativa
- **COULD** = Nice-to-have, cortar primeiro se necessário

---

## Critérios de Sucesso

Resultados mensuráveis (devem incluir números):

- [ ] {Métrica 1: ex., "Processar 1000 requisições por minuto"}
- [ ] {Métrica 2: ex., "Atingir 99,9% de disponibilidade"}
- [ ] {Métrica 3: ex., "Tempo de resposta abaixo de 200ms"}

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | {Caminho feliz} | {Estado inicial} | {Ação} | {Resultado esperado} |
| AT-002 | {Caso de erro} | {Estado inicial} | {Ação} | {Resultado esperado} |
| AT-003 | {Caso extremo} | {Estado inicial} | {Ação} | {Resultado esperado} |

---

## Fora do Escopo

Explicitamente NÃO incluído nesta feature:

- {Item 1: O que NÃO estamos fazendo}
- {Item 2: O que está adiado para o futuro}
- {Item 3: O que está explicitamente excluído}

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Técnica | {ex., "Deve usar o schema de banco de dados existente"} | {Como isso afeta o design} |
| Prazo | {ex., "Deve estar pronto no Q1"} | {Como isso afeta o escopo} |
| Recurso | {ex., "Sem orçamento adicional de infraestrutura"} | {Como isso afeta a abordagem} |

---

## Contexto Técnico

> Contexto essencial para a fase de Design - evita arquivos mal posicionados e necessidades de infraestrutura perdidas.

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Localização de Deploy** | {src/ \| functions/ \| gen/ \| deploy/ \| caminho customizado} | {Por que esta localização} |
| **Domínios KB** | {Liste os domínios de .claude/kb/ relevantes para esta feature} | {Quais padrões consultar} |
| **Impacto IaC** | {Novos recursos \| Modificar existentes \| Nenhum \| A definir} | {Mudanças de infraestrutura necessárias} |

**Por Que Isso Importa:**

- **Localização** → Fase de Design usa a estrutura correta do projeto, evita arquivos mal posicionados
- **Domínios KB** → Fase de Design puxa os padrões corretos de `.claude/kb/`
- **Impacto IaC** → Aciona o planejamento de infraestrutura, evita falhas do tipo "funciona local"

---

## Contrato de Dados (se aplicável)

> Inclua esta seção quando a feature envolver pipelines de dados, ETL ou analytics.

### Inventário de Origens
| Origem | Tipo | Volume | Frequência | Responsável |
|--------|------|--------|------------|-------------|
| {origem_1} | {Postgres / Kafka / S3 / API} | {~linhas/dia} | {SLA} | {Time} |

### Contrato de Schema
| Coluna | Tipo | Restrições | PII? |
|--------|------|------------|------|
| {coluna_1} | {INT / VARCHAR / DECIMAL} | {NOT NULL, UNIQUE} | {Sim/Não} |

### SLAs de Atualização
| Camada | Meta | Medição |
|--------|------|---------|
| Raw / Staging | {Dentro de X minutos após mudança na origem} | {Comparação de timestamp} |
| Marts | {Atualizado até HH:MM UTC diariamente} | {Tempo de conclusão do DAG} |

### Métricas de Completude
- {ex., 99,9% dos registros da origem presentes dentro do SLA}
- {ex., Zero chaves primárias nulas em todos os modelos}

### Requisitos de Lineage
- {ex., Lineage em nível de coluna da origem ao mart}
- {ex., Análise de impacto antes de mudanças de schema}

---

## Premissas

Premissas que, se incorretas, podem invalidar o design:

| ID | Premissa | Se Errada, Impacto | Validada? |
|----|----------|-------------------|-----------|
| A-001 | {ex., "O banco de dados suporta a carga esperada"} | {Precisaria de camada de cache} | [ ] |
| A-002 | {ex., "O volume de requisições fica abaixo de 1000/hora"} | {Precisaria de rate limiting} | [ ] |
| A-003 | {ex., "Usuários têm browsers modernos"} | {Precisaria de polyfills para suporte legado} | [ ] |

**Nota:** Valide premissas críticas antes da fase de DESIGN. Premissas não validadas se tornam riscos.

---

## Detalhamento do Clarity Score

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | {0-3} | {Por que este score} |
| Usuários | {0-3} | {Por que este score} |
| Objetivos | {0-3} | {Por que este score} |
| Sucesso | {0-3} | {Por que este score} |
| Escopo | {0-3} | {Por que este score} |
| **Total** | **{X}/15** | |

**Guia de Pontuação:**
- 0 = Totalmente ausente
- 1 = Vago ou incompleto
- 2 = Claro mas faltam detalhes
- 3 = Cristalino e acionável

**Mínimo para prosseguir: 12/15**

---

## Questões em Aberto

{Liste quaisquer perguntas restantes que precisam de resposta antes da fase de Design. Se nenhuma, escreva "Nenhuma - pronto para Design."}

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | {YYYY-MM-DD} | define-agent | Versão inicial |

---

## Próximo Passo

**Pronto para:** `/design .claude/sdd/features/DEFINE_{FEATURE_NAME}.md`

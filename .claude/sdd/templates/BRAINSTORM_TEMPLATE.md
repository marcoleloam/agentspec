# BRAINSTORM: {Nome da Feature}

> Sessão exploratória para clarificar intenção e abordagem antes da captura de requisitos

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Data** | {YYYY-MM-DD} |
| **Autor** | brainstorm-agent |
| **Status** | Explorando / Abordagens Identificadas / Pronto para Define |

---

## Ideia Inicial

**Entrada Bruta:** {Ideia original ou solicitação conforme descrita pelo usuário}

**Contexto Coletado:**
- {Observação do estado atual do projeto 1}
- {Observação do estado atual do projeto 2}
- {Código ou padrões relevantes encontrados}

**Contexto Técnico Observado (para o Define):**

| Aspecto | Observação | Implicação |
|---------|------------|------------|
| Localização Provável | {src/ \| functions/ \| gen/ \| deploy/} | {Onde o código deve ficar} |
| Domínios KB Relevantes | {domain-1, domain-2, etc.} | {Padrões a consultar} |
| Padrões IaC | {Ferramentas IaC existentes ou N/A} | {Abordagem de infraestrutura} |

---

## Perguntas de Descoberta e Respostas

| # | Pergunta | Resposta | Impacto |
|---|----------|----------|---------|
| 1 | {Pergunta sobre o propósito} | {Resposta do usuário} | {Como isso molda a solução} |
| 2 | {Pergunta sobre os usuários} | {Resposta do usuário} | {Como isso molda a solução} |
| 3 | {Pergunta sobre restrições} | {Resposta do usuário} | {Como isso molda a solução} |
| 4 | {Pergunta sobre critérios de sucesso} | {Resposta do usuário} | {Como isso molda a solução} |

**Mínimo de Perguntas:** 3 (para garantir clareza antes de prosseguir)

---

## Inventário de Dados de Exemplo

> Exemplos melhoram a precisão do LLM via aprendizado em contexto e few-shot prompting.

| Tipo | Localização | Quantidade | Notas |
|------|-------------|------------|-------|
| Arquivos de entrada | {Caminho ou N/A} | {N} | {Formato, tamanho, padrões} |
| Exemplos de saída | {Caminho ou N/A} | {N} | {Schema, estrutura} |
| Ground truth | {Caminho ou N/A} | {N} | {Valores corretos verificados} |
| Código relacionado | {Caminho ou N/A} | {N} | {Padrões para reutilizar} |

**Como os exemplos serão usados:**

- {ex: Exemplos few-shot em prompts de extração}
- {ex: Referência de validação de schema}
- {ex: Fixtures de teste para validação}

---

## Abordagens Exploradas

### Abordagem A: {Nome} ⭐ Recomendada

**Descrição:** {Breve descrição da abordagem}

**Prós:**
- {Vantagem 1}
- {Vantagem 2}

**Contras:**
- {Trade-off 1}
- {Trade-off 2}

**Por que Recomendada:** {Justificativa clara de por que este é o caminho sugerido}

---

### Abordagem B: {Nome}

**Descrição:** {Breve descrição da abordagem}

**Prós:**
- {Vantagem 1}
- {Vantagem 2}

**Contras:**
- {Trade-off 1}
- {Trade-off 2}

---

### Abordagem C: {Nome} (Opcional)

**Descrição:** {Breve descrição da abordagem}

**Prós:**
- {Vantagem 1}

**Contras:**
- {Trade-off 1}

---

## Contexto de Data Engineering (se aplicável)

> Inclua esta seção quando a feature envolver pipelines de dados, ETL, analytics ou infraestrutura de dados.

### Sistemas de Origem
| Origem | Tipo | Volume Estimado | Frequência Atual |
|--------|------|-----------------|------------------|
| {Origem 1} | {Postgres / Kafka / S3 / API} | {~linhas/dia ou GB} | {Tempo real / Diário / Desconhecido} |

### Esboço do Fluxo de Dados
```text
[Origem A] → [Ingestão] → [Raw] → [Transformação] → [Mart] → [Consumidor]
```

### Questões de Dados Exploradas
| # | Questão | Resposta | Impacto |
|---|---------|----------|---------|
| 1 | Qual é o volume esperado de dados? | {Resposta} | {Influencia a escolha de ferramenta} |
| 2 | Qual SLA de atualização é necessário? | {Resposta} | {Batch vs streaming} |
| 3 | Quem consome a saída? | {Resposta} | {Abordagem de modelagem} |

---

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem {A/B/C} |
| **Confirmação do Usuário** | {Data/Hora da confirmação} |
| **Justificativa** | {Por que o usuário selecionou esta abordagem} |

---

## Principais Decisões Tomadas

| # | Decisão | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|----------------------|
| 1 | {Decisão tomada durante o brainstorm} | {Por quê} | {O que não foi feito} |
| 2 | {Decisão tomada durante o brainstorm} | {Por quê} | {O que não foi feito} |

---

## Features Removidas (YAGNI)

| Feature Sugerida | Motivo da Remoção | Pode Adicionar Depois? |
|------------------|-------------------|----------------------|
| {Feature que parecia boa mas é desnecessária} | {Justificativa YAGNI} | Sim/Não |
| {Outra feature adiada} | {Por que não é necessária agora} | Sim/Não |

---

## Validações Incrementais

| Seção | Apresentada | Feedback do Usuário | Ajustada? |
|-------|-------------|---------------------|-----------|
| Conceito de arquitetura | ✅ | {Feedback} | Sim/Não |
| Decomposição de componentes | ✅ | {Feedback} | Sim/Não |
| Fluxo de dados | ✅ | {Feedback} | Sim/Não |
| Tratamento de erros | ✅ | {Feedback} | Sim/Não |

**Mínimo de Validações:** 2 (para garantir alinhamento)

---

## Requisitos Sugeridos para /define

Com base nesta sessão de brainstorm, os seguintes itens devem ser capturados na fase DEFINE:

### Declaração do Problema (Rascunho)
{Uma frase clara descrevendo o problema a resolver}

### Usuários-Alvo (Rascunho)
| Usuário | Dor |
|---------|-----|
| {Usuário 1} | {Dor} |

### Critérios de Sucesso (Rascunho)
- [ ] {Critério mensurável 1}
- [ ] {Critério mensurável 2}

### Restrições Identificadas
- {Restrição 1}
- {Restrição 2}

### Fora do Escopo (Confirmado)
- {Item 1 - explicitamente excluído durante o brainstorm}
- {Item 2}

---

## Resumo da Sessão

| Métrica | Valor |
|---------|-------|
| Perguntas Feitas | {N} |
| Abordagens Exploradas | {2-3} |
| Features Removidas (YAGNI) | {N} |
| Validações Concluídas | {N} |
| Duração | {Tempo aproximado} |

---

## Próximo Passo

**Pronto para:** `/define .claude/sdd/features/BRAINSTORM_{FEATURE_NAME}.md`

# BRAINSTORM: {Nome da Feature}

> Sessão exploratória para clarificar intenção e abordagem antes da captura de requisitos

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Data** | {AAAA-MM-DD} |
| **Autor** | brainstorm-agent |
| **Status** | Explorando / Abordagens Identificadas / Pronto para Definir |

---

## Ideia Inicial

**Entrada Original:** {Ideia ou solicitação original conforme descrita pelo usuário}

**Contexto Coletado:**
- {Observação do estado do projeto 1}
- {Observação do estado do projeto 2}
- {Código ou padrões existentes relevantes encontrados}

**Contexto Técnico Observado (para Definir):**

| Aspecto | Observação | Implicação |
|---------|------------|------------|
| Localização Provável | {src/ \| functions/ \| gen/ \| deploy/} | {Onde o código deve ficar} |
| Domínios KB Relevantes | {dominio-1, dominio-2, etc.} | {Padrões a consultar} |
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

> Exemplos melhoram a precisão do LLM através de aprendizado em contexto e few-shot prompting.

| Tipo | Localização | Quantidade | Notas |
|------|-------------|------------|-------|
| Arquivos de entrada | {Caminho ou N/A} | {N} | {Formato, tamanho, padrões} |
| Exemplos de saída | {Caminho ou N/A} | {N} | {Schema, estrutura} |
| Dados de referência | {Caminho ou N/A} | {N} | {Valores verificados corretos} |
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

**Por que Recomendada:** {Raciocínio claro do por que este é o caminho sugerido}

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

## Abordagem Selecionada

| Atributo | Valor |
|----------|-------|
| **Escolhida** | Abordagem {A/B/C} |
| **Confirmação do Usuário** | {Data/Hora da confirmação} |
| **Justificativa** | {Por que o usuário selecionou esta abordagem} |

---

## Decisões Tomadas

| # | Decisão | Justificativa | Alternativa Rejeitada |
|---|---------|---------------|----------------------|
| 1 | {Decisão tomada durante o brainstorm} | {Por quê} | {O que não fizemos} |
| 2 | {Decisão tomada durante o brainstorm} | {Por quê} | {O que não fizemos} |

---

## Funcionalidades Removidas (YAGNI)

| Funcionalidade Sugerida | Motivo da Remoção | Pode Adicionar Depois? |
|-------------------------|-------------------|----------------------|
| {Funcionalidade que parecia boa mas desnecessária} | {Raciocínio YAGNI} | Sim/Não |
| {Outra funcionalidade adiada} | {Por que não é necessária agora} | Sim/Não |

---

## Validações Incrementais

| Seção | Apresentada | Feedback do Usuário | Ajustada? |
|-------|-------------|---------------------|-----------|
| Conceito de arquitetura | ✅ | {Feedback} | Sim/Não |
| Divisão de componentes | ✅ | {Feedback} | Sim/Não |
| Fluxo de dados | ✅ | {Feedback} | Sim/Não |
| Tratamento de erros | ✅ | {Feedback} | Sim/Não |

**Mínimo de Validações:** 2 (para garantir alinhamento)

---

## Requisitos Sugeridos para /definir

Com base nesta sessão de exploração, o seguinte deve ser capturado na fase DEFINE:

### Declaração do Problema (Rascunho)
{Uma frase clara descrevendo o problema a resolver}

### Usuários-Alvo (Rascunho)
| Usuário | Ponto de Dor |
|---------|-------------|
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
| Funcionalidades Removidas (YAGNI) | {N} |
| Validações Concluídas | {N} |
| Duração | {Tempo aproximado} |

---

## Mapa do Workflow

```text
📍 Progresso do Workflow
════════════════════════════════════════════
✅ Fase 0: Explorar        ← CONCLUÍDA
➡️ Fase 1: /definir
⬜ Fase 2: /projetar
⬜ Fase 3: /construir
⬜ Fase 4: /entregar
```

---

## Próxima Etapa

**Pronto para:** `/definir sdd/features/00_BRAINSTORM_{FEATURE_NAME}.md`

💡 **Dica:** O documento de exploração já contém requisitos rascunhados. O `/definir` vai extraí-los e validá-los automaticamente.

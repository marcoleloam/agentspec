# DEFINE: {Nome da Feature}

> Descrição em uma frase do que estamos construindo

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Data** | {AAAA-MM-DD} |
| **Autor** | {autor} |
| **Status** | {Rascunho / Em Andamento / Precisa de Esclarecimento / Pronto para Projetar} |
| **Score de Clareza** | {X}/15 |

---

## Declaração do Problema

{1-2 frases descrevendo o ponto de dor que estamos resolvendo. Seja específico sobre quem tem o problema e qual é o impacto.}

---

## Usuários-Alvo

| Usuário | Papel | Ponto de Dor |
|---------|-------|-------------|
| {Usuário 1} | {Seu papel} | {O que os frustra} |
| {Usuário 2} | {Seu papel} | {O que os frustra} |

---

## Objetivos

O que o sucesso representa (priorizado):

| Prioridade | Objetivo |
|------------|----------|
| **MUST** | {Objetivo primário - não-negociável para o MVP} |
| **MUST** | {Outro objetivo crítico} |
| **SHOULD** | {Importante mas pode adiar se o prazo apertar} |
| **COULD** | {Bom ter se o tempo permitir} |

**Guia de Prioridade:**
- **MUST** = MVP falha sem isso
- **SHOULD** = Importante, mas existe workaround
- **COULD** = Bom ter, cortar primeiro se necessário

---

## Critérios de Sucesso

Resultados mensuráveis (devem incluir números):

- [ ] {Métrica 1: ex: "Processar 1000 requisições por minuto"}
- [ ] {Métrica 2: ex: "Atingir 99.9% de uptime"}
- [ ] {Métrica 3: ex: "Tempo de resposta abaixo de 200ms"}

---

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| TA-001 | {Caminho feliz} | {Estado inicial} | {Ação} | {Resultado esperado} |
| TA-002 | {Caso de erro} | {Estado inicial} | {Ação} | {Resultado esperado} |
| TA-003 | {Caso limite} | {Estado inicial} | {Ação} | {Resultado esperado} |

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
| Técnica | {ex: "Deve usar o schema de banco existente"} | {Como isso afeta o design} |
| Prazo | {ex: "Deve entregar até o Q1"} | {Como isso afeta o escopo} |
| Recurso | {ex: "Sem orçamento adicional de infraestrutura"} | {Como isso afeta a abordagem} |

---

## Contexto Técnico

> Contexto essencial para a fase de Design - previne arquivos mal posicionados e necessidades de infraestrutura não percebidas.

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Local de Deploy** | {src/ \| functions/ \| gen/ \| deploy/ \| caminho customizado} | {Por que este local} |
| **Domínios KB** | {Lista de domínios de kb/ relevantes para esta feature} | {Quais padrões consultar} |
| **Impacto IaC** | {Novos recursos \| Modificar existentes \| Nenhum \| A Definir} | {Mudanças de infraestrutura necessárias} |

**Por Que Isso Importa:**

- **Local** → Fase de Design usa a estrutura correta do projeto, previne arquivos mal posicionados
- **Domínios KB** → Fase de Design puxa os padrões corretos de `kb/`
- **Impacto IaC** → Aciona planejamento de infraestrutura, evita falhas de "funciona local"

---

## Premissas

Premissas que, se erradas, podem invalidar o design:

| ID | Premissa | Se Errada, Impacto | Validada? |
|----|----------|---------------------|-----------|
| P-001 | {ex: "O banco suporta a carga esperada"} | {Seria necessária camada de cache} | [ ] |
| P-002 | {ex: "Volume de requisições fica abaixo de 1000/hora"} | {Seria necessário rate limiting} | [ ] |
| P-003 | {ex: "Usuários têm navegadores modernos"} | {Seria necessário polyfills para legado} | [ ] |

**Nota:** Valide premissas críticas antes da fase DESIGN. Premissas não validadas se tornam riscos.

---

## Detalhamento do Score de Clareza

| Elemento | Score (0-3) | Notas |
|----------|-------------|-------|
| Problema | {0-3} | {Por que este score} |
| Usuários | {0-3} | {Por que este score} |
| Objetivos | {0-3} | {Por que este score} |
| Sucesso | {0-3} | {Por que este score} |
| Escopo | {0-3} | {Por que este score} |
| **Total** | **{X}/15** | |

**Guia de Pontuação:**
- 0 = Completamente ausente
- 1 = Vago ou incompleto
- 2 = Claro mas faltam detalhes
- 3 = Cristalino, acionável

**Mínimo para prosseguir: 12/15**

---

## Questões Abertas

{Liste quaisquer questões pendentes que precisam de resposta antes da fase Design. Se nenhuma, declare "Nenhuma - pronto para Design."}

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | {AAAA-MM-DD} | define-agent | Versão inicial |

---

## Mapa do Workflow

```text
📍 Progresso do Workflow
════════════════════════════════════════════
✅ Fase 0: Explorar        (se aplicável)
✅ Fase 1: Definir         ← CONCLUÍDA
➡️ Fase 2: /projetar
⬜ Fase 3: /construir
⬜ Fase 4: /entregar
```

---

## Próxima Etapa

**Pronto para:** `/projetar sdd/features/01_DEFINE_{FEATURE_NAME}.md`

💡 **Dica:** O `/projetar` criará a arquitetura técnica com diagramas ASCII, decisões documentadas e manifesto de arquivos.

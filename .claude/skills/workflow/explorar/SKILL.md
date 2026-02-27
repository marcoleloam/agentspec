---
name: explorar
description: Explorar ideias através de diálogo colaborativo antes da captura de requisitos (Fase 0)
user-invocable: true
agent: brainstorm-agent
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, AskUserQuestion
argument-hint: [ideia-ou-solicitação]
---

# Comando Explorar

> Exploração colaborativa antes da captura de requisitos (Fase 0)

## Uso

```bash
/explorar <ideia-ou-solicitação>
/explorar "Construir um sistema de notificações em tempo real"
/explorar notas/ideia-inicial.txt
```

## Exemplos

```bash
# A partir de uma ideia direta
/explorar "Quero automatizar verificações de qualidade de dados"

# A partir de um arquivo com notas
/explorar docs/notas-reuniao.md

# A partir de uma declaração de problema
/explorar "Nossa equipe gasta muito tempo com entrada manual de dados"
```

---

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Visão Geral

Esta é a **Fase 0** do workflow AgentSpec de 5 fases:

```text
Fase 0: /explorar   → .claude/sdd/features/00_BRAINSTORM_{FEATURE}.md (ESTE COMANDO)
Fase 1: /definir    → .claude/sdd/features/01_DEFINE_{FEATURE}.md
Fase 2: /projetar   → .claude/sdd/features/02_DESIGN_{FEATURE}.md
Fase 3: /construir  → Código + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Fase 4: /entregar   → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATA}.md
```

O comando `/explorar` explora ideias através de diálogo antes de capturar requisitos formais.

---

## O Que Este Comando Faz

1. **Explorar** - Entender contexto do projeto e padrões existentes
2. **Questionar** - Fazer uma pergunta por vez para clarificar intenção
3. **Coletar** - Reunir arquivos de exemplo, dados de referência para grounding do LLM
4. **Propor** - Apresentar 2-3 abordagens com trade-offs
5. **Simplificar** - Aplicar YAGNI para remover funcionalidades desnecessárias
6. **Validar** - Confirmar entendimento incrementalmente
7. **Documentar** - Gerar documento BRAINSTORM para /definir

---

## Processo

### Passo 1: Coletar Contexto

```markdown
Read(CLAUDE.md)
Read(.claude/sdd/templates/BRAINSTORM_TEMPLATE.md)
Explorar estrutura do projeto, commits recentes, padrões existentes
```

### Passo 2: Perguntas de Descoberta

Fazer perguntas UMA POR VEZ:

| Tipo de Pergunta | Quando Usar |
|------------------|-------------|
| Múltipla Escolha | Quando as opções são claras (preferido) |
| Aberta | Quando explorando território desconhecido |
| Esclarecimento | Quando resposta foi vaga |

**Mínimo:** 3 perguntas antes de propor abordagens

### Passo 3: Coleta de Exemplos (Grounding do LLM)

```markdown
"Você tem algum exemplo que possa ajudar a fundamentar a solução?
(a) Arquivos de entrada de exemplo
(b) Exemplos de saída esperada
(c) Dados de referência / verificados
(d) Nenhum disponível"
```

### Passo 4: Explorar Abordagens

Apresentar 2-3 abordagens distintas com recomendação e trade-offs.

### Passo 5: Aplicar YAGNI

Remover funcionalidades que não são necessárias para o MVP. Documentar o que foi removido e por quê.

### Passo 6: Validar Incrementalmente

Apresentar design em seções (200-300 palavras cada). **Mínimo:** 2 pontos de validação.

### Passo 7: Gerar Documento

```markdown
Write(.claude/sdd/features/00_BRAINSTORM_{FEATURE}.md)
```

---

## Saída

| Artefato | Localização |
|----------|-------------|
| **Documento Brainstorm** | `.claude/sdd/features/00_BRAINSTORM_{FEATURE}.md` |

---

## Mapa do Workflow

Após gerar o documento, exibir ao usuário:

```text
📍 Mapa do Workflow
════════════════════════════
✅ Fase 0: Explorar      ← CONCLUÍDA
➡️ Fase 1: /definir .claude/sdd/features/00_BRAINSTORM_{FEATURE}.md
⬜ Fase 2: /projetar
⬜ Fase 3: /construir
⬜ Fase 4: /entregar

💡 Dica: O documento de exploração já contém requisitos rascunhados.
   O /definir vai extraí-los e validá-los automaticamente.
```

---

## Gate de Qualidade

```text
[ ] Mínimo 3 perguntas de descoberta feitas
[ ] Pergunta sobre coleta de exemplos feita
[ ] Pelo menos 2 abordagens exploradas
[ ] YAGNI aplicado (funcionalidades removidas)
[ ] Mínimo 2 validações concluídas
[ ] Usuário confirmou abordagem selecionada
[ ] Rascunho de requisitos incluído
```

---

## Referências

- Agente: `.claude/agents/workflow/brainstorm-agent.md`
- Template: `.claude/sdd/templates/BRAINSTORM_TEMPLATE.md`
- Contratos: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`

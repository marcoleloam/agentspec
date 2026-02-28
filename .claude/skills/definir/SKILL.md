---
name: definir
description: Capturar e validar requisitos em uma única passagem (Fase 1)
user-invocable: true
agent: define-agent
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, AskUserQuestion
argument-hint: [entrada]
---

# Comando Definir

> Capturar requisitos e validá-los em uma única passagem (Fase 1)

## Uso

```bash
/definir <entrada>
```

## Exemplos

```bash
/definir .claude/sdd/features/00_BRAINSTORM_SISTEMA_NOTIFICACOES.md
/definir notas/ata-reuniao.md
/definir "Construir um API gateway para gerenciamento de usuários"
```

---

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Visão Geral

Esta é a **Fase 1** do workflow AgentSpec de 5 fases:

```text
Fase 0: /explorar   → .claude/sdd/features/00_BRAINSTORM_{FEATURE}.md (opcional)
Fase 1: /definir    → .claude/sdd/features/01_DEFINE_{FEATURE}.md (ESTE COMANDO)
Fase 2: /projetar   → .claude/sdd/features/02_DESIGN_{FEATURE}.md
Fase 3: /construir  → Código + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md
Fase 4: /entregar   → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATA}.md
```

O comando `/definir` combina Intake + PRD + Refine em uma única fase iterativa.

---

## O Que Este Comando Faz

1. **Extrair** - Puxar requisitos de qualquer entrada
2. **Estruturar** - Organizar em problema, usuários, objetivos, critérios de sucesso
3. **Validar** - Pontuação de clareza integrada (deve atingir 12/15)
4. **Esclarecer** - Fazer perguntas direcionadas para lacunas

---

## Processo

### Passo 1: Carregar Contexto

```markdown
Read(.claude/sdd/templates/DEFINE_TEMPLATE.md)
Read(CLAUDE.md)
Read(<arquivo-entrada>)
```

### Passo 2: Extrair Entidades

| Elemento | Padrões de Extração |
|----------|---------------------|
| **Problema** | "Estamos com dificuldade em...", "O problema é..." |
| **Usuários** | "Para a equipe...", "Clientes querem..." |
| **Objetivos** | "Precisamos...", "Deve ter..." |
| **Critérios de Sucesso** | "Sucesso significa...", "Saberemos quando..." |
| **Restrições** | "Deve funcionar com...", "Não pode mudar..." |
| **Fora do Escopo** | "Não incluindo...", "Adiado para..." |

### Passo 3: Calcular Score de Clareza

Total: 15 pontos (5 elementos × 3 pontos). **Mínimo para prosseguir:** 12/15 (80%)

### Passo 4: Gerar Documento

```markdown
Write(.claude/sdd/features/01_DEFINE_{FEATURE_NAME}.md)
```

---

## Mapa do Workflow

```text
📍 Mapa do Workflow
════════════════════════════
✅ Fase 0: Explorar       (se aplicável)
✅ Fase 1: Definir        ← CONCLUÍDA
➡️ Fase 2: /projetar .claude/sdd/features/01_DEFINE_{FEATURE}.md
⬜ Fase 3: /construir
⬜ Fase 4: /entregar
```

---

## Gate de Qualidade

```text
[ ] Declaração do problema é clara e específica
[ ] Pelo menos um persona de usuário identificado
[ ] Critérios de sucesso são mensuráveis
[ ] Fora do escopo é explícito
[ ] Score de Clareza >= 12/15
```

---

## Referências

- Agente: `.claude/agents/workflow/define-agent.md`
- Template: `.claude/sdd/templates/DEFINE_TEMPLATE.md`
- Contratos: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`

---
name: construir
description: Executar implementação com geração de tarefas sob demanda (Fase 3)
user-invocable: true
agent: build-agent
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, Task
argument-hint: [arquivo-design]
---

# Comando Construir

> Executar implementação com geração de tarefas sob demanda (Fase 3)

## Uso

```bash
/construir <arquivo-design>
```

## Exemplos

```bash
/construir .claude/sdd/features/02_DESIGN_SISTEMA_NOTIFICACOES.md
/construir 02_DESIGN_AUTH_USUARIO.md
```

---

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Visão Geral

Esta é a **Fase 3** do workflow AgentSpec de 5 fases:

```text
Fase 0: /explorar   → .claude/sdd/features/00_BRAINSTORM_{FEATURE}.md (opcional)
Fase 1: /definir    → .claude/sdd/features/01_DEFINE_{FEATURE}.md
Fase 2: /projetar   → .claude/sdd/features/02_DESIGN_{FEATURE}.md
Fase 3: /construir  → Código + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md (ESTE COMANDO)
Fase 4: /entregar   → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATA}.md
```

---

## O Que Este Comando Faz

1. **Analisar** - Extrair manifesto de arquivos do DESIGN
2. **Priorizar** - Ordenar arquivos por dependências
3. **Executar** - Criar cada arquivo com verificação
4. **Validar** - Executar testes após cada mudança significativa
5. **Reportar** - Gerar relatório de build

---

## Processo

### Passo 1: Carregar Contexto

```markdown
Read(.claude/sdd/features/02_DESIGN_{FEATURE}.md)
Read(.claude/sdd/features/01_DEFINE_{FEATURE}.md)
Read(CLAUDE.md)
```

### Passo 2: Extrair e Ordenar Tarefas

Converter manifesto de arquivos em lista de tarefas ordenada por dependências.

### Passo 3: Executar Cada Tarefa

```text
┌─────────────────────────────────────────────────────┐
│                    EXECUTAR TAREFA                    │
├─────────────────────────────────────────────────────┤
│  1. Ler tarefa do manifesto                         │
│  2. Escrever código seguindo padrões do DESIGN      │
│  3. Executar comando de verificação                  │
│     └─ Se FALHOU → Corrigir e tentar (máx 3)       │
│  4. Marcar tarefa como completa                      │
│  5. Passar para próxima tarefa                       │
└─────────────────────────────────────────────────────┘
```

### Passo 4: Validação Completa

```bash
ruff check .
mypy .
pytest
```

### Passo 5: Gerar Relatório

```markdown
Write(.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md)
```

---

## Saída

| Artefato | Localização |
|----------|-------------|
| **Código** | Conforme manifesto do DESIGN |
| **Relatório de Build** | `.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md` |

**Próxima Etapa:** `/entregar .claude/sdd/features/01_DEFINE_{FEATURE}.md`

---

## Tratando Problemas

| Problema | Ação |
|----------|------|
| Requisito faltando | `/iterar` para atualizar DEFINE |
| Problema de arquitetura | `/iterar` para atualizar DESIGN |
| Bug simples | Corrigir imediatamente |
| Bloqueador grave | Parar e reportar |

---

## Referências

- Agente: `.claude/agents/workflow/build-agent.md`
- Template: `.claude/sdd/templates/BUILD_REPORT_TEMPLATE.md`
- Contratos: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`

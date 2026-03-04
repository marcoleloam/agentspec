---
name: construir
description: "Fase 3 do SDD: execute a implementação completa com base no documento de design. Use após /projetar quando houver um arquivo DESIGN pronto. Acione quando o usuário disser 'implementar', 'construir' ou 'codar' e houver um arquivo 02_DESIGN_ disponível."
user-invokable: true
agent: build-agent
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, Task
argument-hint: "[arquivo-design]"
---

# Comando Construir

> Executar implementação com geração de tarefas sob demanda (Fase 3)

## Uso

```bash
/construir <arquivo-design>
```

## Exemplos

```bash
/construir sdd/features/02_DESIGN_SISTEMA_NOTIFICACOES.md
/construir 02_DESIGN_AUTH_USUARIO.md
```

---

## Idioma

> Este projeto usa **Português-BR** como idioma padrão — toda comunicação com o usuário e documentos gerados devem seguir esse padrão para manter consistência com o restante do framework.

---

## Visão Geral

Esta é a **Fase 3** do workflow AgentSpec de 5 fases:

```text
Fase 0: /explorar   → sdd/features/00_BRAINSTORM_{FEATURE}.md (opcional)
Fase 1: /definir    → sdd/features/01_DEFINE_{FEATURE}.md
Fase 2: /projetar   → sdd/features/02_DESIGN_{FEATURE}.md
Fase 3: /construir  → Código + sdd/reports/BUILD_REPORT_{FEATURE}.md (ESTE COMANDO)
Fase 4: /entregar   → sdd/archive/{FEATURE}/SHIPPED_{DATA}.md
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
Read(sdd/features/02_DESIGN_{FEATURE}.md)
Read(sdd/features/01_DEFINE_{FEATURE}.md)
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
Write(sdd/reports/BUILD_REPORT_{FEATURE}.md)
```

---

## Saída

| Artefato | Localização |
|----------|-------------|
| **Código** | Conforme manifesto do DESIGN |
| **Relatório de Build** | `sdd/reports/BUILD_REPORT_{FEATURE}.md` |

**Próxima Etapa:** `/entregar sdd/features/01_DEFINE_{FEATURE}.md`

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

- Agente: `agents/build-agent.md`
- Template: `sdd/templates/BUILD_REPORT_TEMPLATE.md`
- Contratos: `sdd/architecture/WORKFLOW_CONTRACTS.yaml`

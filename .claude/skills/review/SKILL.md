---
name: review
description: Dual AI code review with CodeRabbit + Claude Code for maximum coverage
user-invocable: true
agent: code-reviewer
allowed-tools: Read, Grep, Glob, Bash, TodoWrite
argument-hint: [uncommitted|committed|--quick|--deep]
---

# Comando Review

> Revisão de código dual AI com CodeRabbit + Claude Code para máxima cobertura

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Uso

```bash
/review                        # Revisar todas mudanças vs main
/review uncommitted            # Revisar apenas mudanças não commitadas
/review committed              # Revisar apenas mudanças commitadas
/review --base develop         # Comparar com branch específica
/review --quick                # Apenas CodeRabbit (mais rápido)
/review --deep                 # Apenas Claude (sem CodeRabbit)
```

---

## Visão Geral

Este comando orquestra uma **revisão dual AI** combinando:

| Revisor | Pontos Fortes |
|---------|---------------|
| **CodeRabbit** | Análise estática, scanning de segurança, linting, detecção de padrões |
| **Claude** | Revisão arquitetural, lógica de negócio, design patterns, entendimento contextual |

---

## Processo

### Passo 1: Determinar Escopo

| Entrada | Escopo |
|---------|--------|
| `/review` | Todas mudanças vs main |
| `/review uncommitted` | Apenas working directory |
| `/review committed` | Apenas mudanças commitadas |
| `/review --base <branch>` | Comparar com branch específica |

### Passo 2: Executar Análise CodeRabbit

```bash
source ~/.zshrc && coderabbit review --plain
```

### Passo 3: Executar Análise Profunda do Claude

Foco em arquitetura, lógica de negócio, design patterns, manutenibilidade.

### Passo 4: Sintetizar Resultados

Deduplicar, priorizar, categorizar e gerar itens de ação.

### Passo 5: Gerar Relatório

---

## Formato de Saída

```markdown
## Relatório de Revisão Dual AI

### Resumo

| Fonte | Crítico | Erro | Aviso | Info |
|-------|---------|------|-------|------|
| CodeRabbit | {n} | {n} | {n} | {n} |
| Claude | {n} | {n} | {n} | {n} |

### Problemas Críticos (corrigir obrigatoriamente)
### Erros (deveria corrigir)
### Avisos (recomendado)
### Sugestões (bom ter)
### Observações Positivas

### Checklist de Ações
- [ ] Corrigir: {item}

**Status de Merge:** Pronto | Corrigir avisos | Corrigir problemas críticos
```

---

## Modos

| Modo | Descrição |
|------|-----------|
| Padrão | CodeRabbit + Claude |
| `--quick` | Apenas CodeRabbit (feedback rápido) |
| `--deep` | Apenas Claude (análise aprofundada) |

---

## Tratamento de Erros

- CodeRabbit CLI não disponível → prosseguir com revisão apenas do Claude
- CodeRabbit não autenticado → informar usuário, prosseguir com Claude
- Changeset grande (>50 arquivos) → sugerir `/review uncommitted`

---

## Gate de Qualidade

```text
[ ] Escopo de revisão determinado
[ ] Pelo menos um revisor executado (CodeRabbit ou Claude)
[ ] Resultados categorizados por severidade
[ ] Itens de ação claros e acionáveis
[ ] Status de merge determinado
```

---

## Referências

- Agente: `.claude/agents/code-quality/code-reviewer.md`
- Config: `.coderabbit.yaml`
- Create PR: `.claude/skills/workflow/create-pr/SKILL.md`

---
name: iterar
description: Atualizar qualquer documento de fase quando requisitos ou design mudam (Cross-Phase)
user-invocable: true
agent: iterate-agent
allowed-tools: Read, Write, Edit, Grep, Glob, TodoWrite, AskUserQuestion
argument-hint: [arquivo] "[descrição-da-mudança]"
---

# Comando Iterar

> Atualizar qualquer documento de fase quando requisitos ou design mudam (Cross-Phase)

## Uso

```bash
/iterar <arquivo> "<descrição-da-mudança>"
```

## Exemplos

```bash
/iterar 00_BRAINSTORM_API_BUSCA.md "Considerar ElasticSearch ao invés de busca full-text do PostgreSQL"
/iterar 01_DEFINE_API_BUSCA.md "Adicionar suporte a busca fuzzy"
/iterar 02_DESIGN_API_BUSCA.md "Serviços precisam ser auto-contidos"
```

---

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Visão Geral

```text
Fase 0: /explorar   → 00_BRAINSTORM_{FEATURE}.md ← /iterar pode atualizar
Fase 1: /definir    → 01_DEFINE_{FEATURE}.md     ← /iterar pode atualizar
Fase 2: /projetar   → 02_DESIGN_{FEATURE}.md     ← /iterar pode atualizar
Fase 3: /construir  → (código)                    ← Atualizar DESIGN, depois /construir
```

---

## O Que Este Comando Faz

1. **Detectar Fase** - Identificar qual documento está sendo atualizado
2. **Analisar Impacto** - Determinar efeitos downstream
3. **Atualizar Documento** - Aplicar mudanças com rastreamento de versão
4. **Cascatear** - Propagar mudanças para documentos downstream se necessário

---

## Regras de Cascata

| Origem | Cascateia Para |
|--------|---------------|
| BRAINSTORM → | DEFINE pode precisar atualização |
| DEFINE → | DESIGN pode precisar atualização |
| DESIGN → | Código pode precisar rebuild |

Quando cascata é necessária, perguntar ao usuário:

```markdown
"Esta mudança no {DOCUMENTO} afeta o {DOWNSTREAM}. Opções:
(a) Atualizar automaticamente
(b) Apenas atualizar este documento
(c) Mostrar o que mudaria primeiro"
```

---

## Quando Usar /iterar vs Novo /definir

| Situação | Ação |
|----------|------|
| < 30% de mudança | `/iterar` |
| Adicionar/modificar features | `/iterar` |
| > 50% diferente | Novo `/definir` |
| Problema completamente diferente | Novo `/definir` |

---

## Referências

- Agente: `.claude/agents/workflow/iterate-agent.md`
- Contratos: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`

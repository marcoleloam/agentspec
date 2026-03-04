---
name: projetar
description: "Fase 2 do SDD: crie arquitetura e especificação técnica a partir dos requisitos definidos. Use após /definir quando o usuário quiser planejar a solução antes de implementar. Acione quando houver um arquivo DEFINE pronto ou quando o usuário perguntar 'como implementar X?'."
user-invokable: true
agent: design-agent
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, WebSearch
argument-hint: "[arquivo-define]"
---

# Comando Projetar

> Criar arquitetura e especificação técnica em uma única passagem (Fase 2)

## Uso

```bash
/projetar <arquivo-define>
```

## Exemplos

```bash
/projetar sdd/features/01_DEFINE_SISTEMA_NOTIFICACOES.md
/projetar 01_DEFINE_AUTH_USUARIO.md
```

---

## Idioma

> Este projeto usa **Português-BR** como idioma padrão — toda comunicação com o usuário e documentos gerados devem seguir esse padrão para manter consistência com o restante do framework.

---

## Visão Geral

Esta é a **Fase 2** do workflow AgentSpec de 5 fases:

```text
Fase 0: /explorar   → sdd/features/00_BRAINSTORM_{FEATURE}.md (opcional)
Fase 1: /definir    → sdd/features/01_DEFINE_{FEATURE}.md
Fase 2: /projetar   → sdd/features/02_DESIGN_{FEATURE}.md (ESTE COMANDO)
Fase 3: /construir  → Código + sdd/reports/BUILD_REPORT_{FEATURE}.md
Fase 4: /entregar   → sdd/archive/{FEATURE}/SHIPPED_{DATA}.md
```

O comando `/projetar` combina Plan + Spec + ADRs em um único documento com decisões inline.

---

## O Que Este Comando Faz

1. **Analisar** - Entender requisitos do DEFINE
2. **Arquitetar** - Projetar solução com diagramas ASCII
3. **Decidir** - Documentar decisões-chave com justificativa (ADRs inline)
4. **Especificar** - Criar manifesto de arquivos e padrões de código
5. **Planejar Testes** - Definir estratégia de testes

---

## Processo

### Passo 1: Carregar Contexto

```markdown
Read(sdd/features/01_DEFINE_{FEATURE}.md)
Read(sdd/templates/DESIGN_TEMPLATE.md)
Read(CLAUDE.md)
```

### Passo 2: Criar Arquitetura

Diagrama ASCII do sistema, lista de componentes, fluxo de dados e pontos de integração.

### Passo 3: Documentar Decisões (ADRs Inline)

Contexto, escolha, justificativa, alternativas rejeitadas e consequências.

### Passo 4: Criar Manifesto de Arquivos

Listar todos os arquivos a criar/modificar com dependências e atribuição de agentes.

### Passo 5: Salvar

```markdown
Write(sdd/features/02_DESIGN_{FEATURE_NAME}.md)
```

---

## Mapa do Workflow

```text
📍 Mapa do Workflow
════════════════════════════
✅ Fase 0: Explorar       (se aplicável)
✅ Fase 1: Definir
✅ Fase 2: Projetar       ← CONCLUÍDA
➡️ Fase 3: /construir sdd/features/02_DESIGN_{FEATURE}.md
⬜ Fase 4: /entregar
```

---

## Gate de Qualidade

```text
[ ] Diagrama de arquitetura é claro
[ ] Decisões documentadas com justificativa
[ ] Manifesto de arquivos completo
[ ] Padrões de código prontos para copiar e colar
[ ] Estratégia de testes cobre requisitos
```

---

## Referências

- Agente: `agents/design-agent.md`
- Template: `sdd/templates/DESIGN_TEMPLATE.md`
- Contratos: `sdd/architecture/WORKFLOW_CONTRACTS.yaml`

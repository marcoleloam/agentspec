---
name: continuar
description: "Continua uma build incompleta ou insatisfatória analisando o gap entre o que foi pedido e o que foi entregue. Use quando o resultado do /construir não atendeu as expectativas, quando features estão faltando, ou quando o usuário quer evoluir o que foi construído sem recomeçar do zero. Acione quando o usuário disser 'isso não ficou como eu queria', 'falta implementar X', 'continua daqui', 'evolui esse código', 'não ficou completo' ou 'preciso que adicione mais'."
user-invokable: true
agent: build-agent
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite
argument-hint: "[feature-ou-caminho-do-build-report]"
---

# Comando Continuar

> Retoma uma build incompleta ou insatisfatória, identificando os gaps e executando apenas o que falta — sem recomeçar do zero.

## Idioma

> Este projeto usa **Português-BR** como idioma padrão — toda comunicação com o usuário e documentos gerados devem seguir esse padrão.

---

## Uso

```bash
/continuar                                        # Detecta o BUILD_REPORT mais recente
/continuar PLATAFORMA_DADOS                       # Feature específica
/continuar sdd/reports/BUILD_REPORT_AUTH.md       # Caminho direto ao relatório
```

---

## Quando Usar

| Situação | /continuar | /iterar |
|----------|------------|---------|
| Código incompleto, feature não implementada | ✅ | ❌ |
| Bug ou erro na implementação entregue | ✅ | ❌ |
| Requisito mudou, precisa atualizar o DEFINE/DESIGN | ❌ | ✅ |
| Arquitetura precisa ser redesenhada | ❌ | ✅ |

**Regra:** `/continuar` mexe em código. `/iterar` mexe em documentos SDD.

---

## Processo

### Passo 1: Carregar Contexto da Build

```
Read(sdd/reports/BUILD_REPORT_{FEATURE}.md)   → o que foi construído e o que falhou
Read(sdd/features/01_DEFINE_{FEATURE}.md)     → critérios de aceitação esperados
Read(sdd/features/02_DESIGN_{FEATURE}.md)     → manifesto de arquivos do design
```

Se não houver BUILD_REPORT, identificar os arquivos de código da feature e avaliar o estado atual.

### Passo 2: Gap Analysis

Comparar critérios de aceitação do DEFINE com o que foi entregue no BUILD_REPORT:

| Tipo de Gap | Ação |
|-------------|------|
| Bug ou erro de implementação | Corrigir inline e re-verificar |
| Feature ausente que estava no DESIGN | Continuar build pelo manifesto de arquivos |
| Feature ausente que **não** estava no DESIGN | Perguntar: usar `/iterar` no DESIGN primeiro? |
| Problema de arquitetura (não de código) | Sugerir `/iterar 02_DESIGN_{FEATURE}.md` |
| Mudança de expectativa do usuário | Recomendar novo `/definir` |

### Passo 3: Confirmar com o Usuário

Apresentar o gap analysis antes de executar qualquer coisa:

```text
📋 Gap Analysis — {FEATURE}
════════════════════════════════════════
✅ Implementado: [lista do que foi entregue]
❌ Faltando:     [lista do que está faltando]
⚠️  Tipo de gap: [classificação do gap]

Ação proposta: [o que será feito]
Continuar? (s/n)
```

### Passo 4: Executar a Continuação

Usar o mesmo padrão do build-agent:

1. Extrair tarefas restantes do manifesto de arquivos do DESIGN
2. Implementar apenas o que está faltando (não reescrever o que já funciona)
3. Verificar com ruff/mypy/pytest conforme o projeto
4. Confirmar que os critérios de aceitação do DEFINE foram atendidos

### Passo 5: Atualizar o BUILD_REPORT

Adicionar uma seção ao BUILD_REPORT existente (não substituir):

```markdown
---

## Continuação — {DATA}

### Gaps Identificados
- [lista dos gaps encontrados]

### O Que Foi Feito
- [lista do que foi implementado nesta continuação]

### Status Final
- Critérios de aceitação: [Atendidos / Parcialmente atendidos]
- Arquivos modificados: [lista]
```

---

## Mapa do Workflow

```text
📍 Mapa do Workflow
════════════════════════════════════════════
✅ Fase 0: /explorar       (se aplicável)
✅ Fase 1: /definir
✅ Fase 2: /projetar
✅ Fase 3: /construir      (build inicial)
✅ Fase 3: /continuar      ← gaps resolvidos
➡️ Fase 4: /entregar
⬜ Fase 5: /entregar
```

---

## Gate de Qualidade

```text
[ ] BUILD_REPORT carregado e gaps identificados
[ ] Gap analysis apresentado e confirmado pelo usuário
[ ] Apenas o que está faltando foi implementado
[ ] BUILD_REPORT atualizado com seção "Continuação {DATA}"
[ ] Critérios de aceitação do DEFINE atendidos
```

---

## Referências

- Agente: `agents/build-agent.md`
- Contratos: `sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Relacionado: `skills/iterar/SKILL.md` (para mudanças em documentos SDD)

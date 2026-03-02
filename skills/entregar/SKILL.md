---
name: entregar
description: Arquivar feature concluída com lições aprendidas (Fase 4)
user-invocable: true
agent: ship-agent
allowed-tools: Read, Write, Edit, Glob, Bash
argument-hint: [arquivo-define]
---

# Comando Entregar

> Arquivar feature concluída com lições aprendidas (Fase 4)

## Uso

```bash
/entregar <arquivo-define>
```

## Exemplos

```bash
/entregar sdd/features/01_DEFINE_SISTEMA_NOTIFICACOES.md
/entregar 01_DEFINE_AUTH_USUARIO.md
```

---

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Visão Geral

Esta é a **Fase 4** do workflow AgentSpec de 5 fases:

```text
Fase 0: /explorar   → sdd/features/00_BRAINSTORM_{FEATURE}.md (opcional)
Fase 1: /definir    → sdd/features/01_DEFINE_{FEATURE}.md
Fase 2: /projetar   → sdd/features/02_DESIGN_{FEATURE}.md
Fase 3: /construir  → Código + sdd/reports/BUILD_REPORT_{FEATURE}.md
Fase 4: /entregar   → sdd/archive/{FEATURE}/SHIPPED_{DATA}.md (ESTE COMANDO)
```

---

## O Que Este Comando Faz

1. **Verificar** - Confirmar que todos os artefatos existem e build passou
2. **Arquivar** - Mover documentos da feature para pasta de arquivo
3. **Documentar** - Criar resumo ENTREGUE com lições aprendidas
4. **Limpar** - Remover arquivos de trabalho da pasta features

---

## Processo

1. Verificar conclusão (DEFINE, DESIGN, BUILD_REPORT existem)
2. Criar pasta `sdd/archive/{FEATURE}/`
3. Copiar artefatos para arquivo
4. Gerar documento ENTREGUE com lições aprendidas
5. Limpar arquivos de trabalho
6. Salvar `SHIPPED_{DATA}.md`

---

## Saída

| Artefato | Localização |
|----------|-------------|
| **ENTREGUE** | `sdd/archive/{FEATURE}/SHIPPED_{DATA}.md` |
| **DEFINE** | `sdd/archive/{FEATURE}/01_DEFINE_{FEATURE}.md` |
| **DESIGN** | `sdd/archive/{FEATURE}/02_DESIGN_{FEATURE}.md` |
| **BUILD_REPORT** | `sdd/archive/{FEATURE}/BUILD_REPORT_{FEATURE}.md` |

---

## Categorias de Lições Aprendidas

| Categoria | Exemplo |
|-----------|---------|
| **Processo** | "Dividir tarefas em pedaços menores ajudou" |
| **Técnico** | "Arquivos de config funcionam melhor que env vars" |
| **Comunicação** | "Esclarecimento precoce evitou retrabalho" |
| **Ferramentas** | "Usar biblioteca X simplificou Y" |

---

## Referências

- Agente: `agents/workflow/ship-agent.md`
- Template: `sdd/templates/SHIPPED_TEMPLATE.md`
- Contratos: `sdd/architecture/WORKFLOW_CONTRACTS.yaml`

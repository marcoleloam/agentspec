# RELATÓRIO DE BUILD: {Nome da Feature}

> Relatório de implementação de {Nome da Feature}

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Data** | {AAAA-MM-DD} |
| **Autor** | build-agent |
| **DEFINE** | [01_DEFINE_{FEATURE}.md](../features/01_DEFINE_{FEATURE}.md) |
| **DESIGN** | [02_DESIGN_{FEATURE}.md](../features/02_DESIGN_{FEATURE}.md) |
| **Status** | Em Andamento / Completo / Bloqueado |

---

## Resumo

| Métrica | Valor |
|---------|-------|
| **Tarefas Concluídas** | {X}/{Y} |
| **Arquivos Criados** | {N} |
| **Linhas de Código** | {N} |
| **Tempo de Build** | {Duração} |
| **Testes Passando** | {X}/{Y} |
| **Agentes Usados** | {N} |

---

## Execução de Tarefas com Atribuição de Agentes

| # | Tarefa | Agente | Status | Duração | Notas |
|---|--------|--------|--------|---------|-------|
| 1 | {Descrição da tarefa} | @{nome-agente} | ✅ Completa | {Xm} | {Notas} |
| 2 | {Descrição da tarefa} | @{nome-agente} | ✅ Completa | {Xm} | {Notas} |
| 3 | {Descrição da tarefa} | (direto) | 🔄 Em Andamento | - | {Sem especialista correspondente} |
| 4 | {Descrição da tarefa} | @{nome-agente} | ⏳ Pendente | - | - |

**Legenda:** ✅ Completa | 🔄 Em Andamento | ⏳ Pendente | ❌ Bloqueada

**Chave de Agentes:**
- `@{nome-agente}` = Delegado ao agente especialista via ferramenta Task
- `(direto)` = Construído diretamente pelo build-agent (sem especialista correspondente)

---

## Contribuições dos Agentes

| Agente | Arquivos | Especialização Aplicada |
|--------|----------|------------------------|
| @{agente-1} | {N} | {Quais padrões/KB usados} |
| @{agente-2} | {N} | {Quais padrões/KB usados} |
| (direto) | {N} | Apenas padrões do DESIGN |

---

## Arquivos Criados

| Arquivo | Linhas | Agente | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `{caminho/arquivo1.py}` | {N} | @{nome-agente} | ✅ | {Notas} |
| `{caminho/arquivo2.py}` | {N} | @{nome-agente} | ✅ | {Notas} |
| `{caminho/config.yaml}` | {N} | (direto) | ✅ | {Notas} |

---

## Resultados de Verificação

### Verificação de Lint

```text
{Saída do linter (ex: ruff, eslint, rubocop) ou "Todas as verificações passaram"}
```

**Status:** ✅ Passou / ❌ Falhou

### Verificação de Tipos

```text
{Saída do verificador de tipos (ex: mypy, tsc) ou "Todas as verificações passaram" ou "N/A - não configurado"}
```

**Status:** ✅ Passou / ❌ Falhou / ⏭️ Pulado

### Testes

```text
{Saída do executor de testes (ex: pytest, jest, go test) ou resumo}
```

| Teste | Resultado |
|-------|-----------|
| `test_funcao_1` | ✅ Passou |
| `test_funcao_2` | ✅ Passou |
| `test_integracao` | ✅ Passou |

**Status:** ✅ {X}/{Y} Passaram | ❌ {N} Falharam

---

## Problemas Encontrados

| # | Problema | Resolução | Impacto no Tempo |
|---|----------|-----------|------------------|
| 1 | {Descrição do problema} | {Como foi resolvido} | {+Xm} |
| 2 | {Descrição do problema} | {Como foi resolvido} | {+Xm} |

---

## Desvios do Design

| Desvio | Motivo | Impacto |
|--------|--------|---------|
| {O que mudou do DESIGN} | {Por que mudou} | {Efeito no sistema} |

---

## Bloqueadores (se houver)

| Bloqueador | Ação Necessária | Responsável |
|------------|-----------------|-------------|
| {Descrição} | {O que precisa acontecer} | {Quem pode desbloquear} |

---

## Verificação dos Testes de Aceitação

| ID | Cenário | Status | Evidência |
|----|---------|--------|-----------|
| TA-001 | {Do DEFINE} | ✅ Passou / ❌ Falhou | {Como verificado} |
| TA-002 | {Do DEFINE} | ✅ Passou / ❌ Falhou | {Como verificado} |
| TA-003 | {Do DEFINE} | ✅ Passou / ❌ Falhou | {Como verificado} |

---

## Notas de Performance

| Métrica | Esperado | Real | Status |
|---------|----------|------|--------|
| {Métrica 1} | {Do DEFINE} | {Medido} | ✅ / ❌ |
| {Métrica 2} | {Do DEFINE} | {Medido} | ✅ / ❌ |

---

## Status Final

### Geral: {✅ COMPLETO / 🔄 EM ANDAMENTO / ❌ BLOQUEADO}

**Checklist de Conclusão:**

- [ ] Todas as tarefas do manifesto concluídas
- [ ] Todas as verificações passaram
- [ ] Todos os testes passaram
- [ ] Sem problemas bloqueadores
- [ ] Testes de aceitação verificados
- [ ] Pronto para /entregar

---

## Próxima Etapa

**Se Completo:** `/entregar .claude/sdd/features/01_DEFINE_{FEATURE_NAME}.md`

**Se Bloqueado:** Resolver bloqueadores, depois `/construir` para retomar

**Se Problemas Encontrados:** `/iterar 02_DESIGN_{FEATURE}.md "{mudança necessária}"`

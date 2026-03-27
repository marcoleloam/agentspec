# BUILD REPORT: {Nome da Feature}

> Relatório de implementação de {Nome da Feature}

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Data** | {YYYY-MM-DD} |
| **Autor** | build-agent |
| **DEFINE** | [DEFINE_{FEATURE}.md](../features/DEFINE_{FEATURE}.md) |
| **DESIGN** | [DESIGN_{FEATURE}.md](../features/DESIGN_{FEATURE}.md) |
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
| **Agentes Utilizados** | {N} |

---

## Execução de Tarefas com Atribuição de Agentes

| # | Tarefa | Agente | Status | Duração | Notas |
|---|--------|--------|--------|---------|-------|
| 1 | {Descrição da tarefa} | @{nome-agente} | ✅ Completo | {Xm} | {Quaisquer notas} |
| 2 | {Descrição da tarefa} | @{nome-agente} | ✅ Completo | {Xm} | {Quaisquer notas} |
| 3 | {Descrição da tarefa} | (direto) | 🔄 Em Andamento | - | {Nenhum especialista encontrado} |
| 4 | {Descrição da tarefa} | @{nome-agente} | ⏳ Pendente | - | - |

**Legenda:** ✅ Completo | 🔄 Em Andamento | ⏳ Pendente | ❌ Bloqueado

**Chave de Agentes:**
- `@{nome-agente}` = Delegado ao agente especialista via Task tool
- `(direto)` = Construído diretamente pelo build-agent (nenhum especialista correspondeu)

---

## Contribuições dos Agentes

| Agente | Arquivos | Especialização Aplicada |
|--------|----------|------------------------|
| @{agente-1} | {N} | {Quais padrões/KB foram usados} |
| @{agente-2} | {N} | {Quais padrões/KB foram usados} |
| (direto) | {N} | Apenas padrões do DESIGN |

---

## Arquivos Criados

| Arquivo | Linhas | Agente | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `{caminho/para/arquivo1.py}` | {N} | @{nome-agente} | ✅ | {Quaisquer notas} |
| `{caminho/para/arquivo2.py}` | {N} | @{nome-agente} | ✅ | {Quaisquer notas} |
| `{caminho/para/config.yaml}` | {N} | (direto) | ✅ | {Quaisquer notas} |

---

## Resultados de Verificação

### Verificação de Lint

```text
{Saída do linter (ex., ruff, eslint, rubocop) ou "Todas as verificações passaram"}
```

**Status:** ✅ Passou / ❌ Falhou

### Verificação de Tipos

```text
{Saída do verificador de tipos (ex., mypy, tsc) ou "Todas as verificações passaram" ou "N/A - não configurado"}
```

**Status:** ✅ Passou / ❌ Falhou / ⏭️ Ignorado

### Testes

```text
{Saída do test runner (ex., pytest, jest, go test) ou resumo}
```

| Teste | Resultado |
|-------|-----------|
| `test_funcao_1` | ✅ Passou |
| `test_funcao_2` | ✅ Passou |
| `test_integracao` | ✅ Passou |

**Status:** ✅ {X}/{Y} Passou | ❌ {N} Falhou

---

## Problemas Encontrados

| # | Problema | Resolução | Impacto no Tempo |
|---|----------|-----------|-----------------|
| 1 | {Descrição do problema} | {Como foi resolvido} | {+Xm} |
| 2 | {Descrição do problema} | {Como foi resolvido} | {+Xm} |

---

## Desvios do Design

| Desvio | Motivo | Impacto |
|--------|--------|---------|
| {O que mudou em relação ao DESIGN} | {Por que mudou} | {Efeito no sistema} |

---

## Bloqueadores (se houver)

| Bloqueador | Ação Necessária | Responsável |
|------------|-----------------|-------------|
| {Descrição} | {O que precisa acontecer} | {Quem pode desbloquear} |

---

## Verificação dos Testes de Aceitação

| ID | Cenário | Status | Evidência |
|----|---------|--------|-----------|
| AT-001 | {Do DEFINE} | ✅ Passou / ❌ Falhou | {Como foi verificado} |
| AT-002 | {Do DEFINE} | ✅ Passou / ❌ Falhou | {Como foi verificado} |
| AT-003 | {Do DEFINE} | ✅ Passou / ❌ Falhou | {Como foi verificado} |

---

## Notas de Performance

| Métrica | Esperado | Real | Status |
|---------|----------|------|--------|
| {Métrica 1} | {Do DEFINE} | {Medido} | ✅ / ❌ |
| {Métrica 2} | {Do DEFINE} | {Medido} | ✅ / ❌ |

---

## Resultados de Qualidade de Dados (se aplicável)

> Inclua esta seção quando o build envolver pipelines de dados, modelos dbt ou infraestrutura de dados.

### Resultados do dbt Build

```text
{Saída de `dbt build --select {modelos}` ou "N/A"}
```

**Status:** ✅ Passou / ❌ Falhou

### Resultados do SQL Lint

```text
{Saída de `sqlfluff lint` ou "N/A"}
```

**Status:** ✅ Passou ({N} arquivos limpos) / ❌ {N} violações

### Verificações de Qualidade de Dados

| Verificação | Ferramenta | Resultado | Detalhes |
|-------------|------------|-----------|----------|
| {Verificação de null em PK} | {dbt test / GE} | ✅ / ❌ | {0 nulls encontrados} |
| {Verificação de unicidade de PK} | {dbt test / GE} | ✅ / ❌ | {0 duplicatas} |
| {Integridade referencial} | {dbt test / GE} | ✅ / ❌ | {0 órfãos} |
| {Sanidade de contagem de linhas} | {dbt test / GE} | ✅ / ❌ | {N linhas, dentro do intervalo} |
| {Atualização} | {dbt source freshness} | ✅ / ❌ | {Última atualização: HH:MM} |

### Métricas do Pipeline

| Métrica | Valor |
|---------|-------|
| Modelos construídos | {N} |
| Testes passando | {X}/{Y} |
| Violações de SQL lint | {N} |
| Tempo médio de build por modelo | {X}s |
| Atualização dos dados | {Dentro do SLA / Excedido} |

---

## Status Final

### Geral: {✅ COMPLETO / 🔄 EM ANDAMENTO / ❌ BLOQUEADO}

**Checklist de Conclusão:**

- [ ] Todas as tarefas do manifesto concluídas
- [ ] Todas as verificações passaram
- [ ] Todos os testes passam
- [ ] Sem bloqueadores
- [ ] Testes de aceitação verificados
- [ ] Pronto para /ship

---

## Próximo Passo

**Se Completo:** `/ship .claude/sdd/features/DEFINE_{FEATURE_NAME}.md`

**Se Bloqueado:** Resolver bloqueadores, depois `/build` para retomar

**Se Houver Problemas:** `/iterate DESIGN_{FEATURE}.md "{mudança necessária}"`

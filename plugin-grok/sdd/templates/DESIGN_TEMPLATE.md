# DESIGN: {Nome da Feature}

> Design técnico para implementar {Nome da Feature}

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Data** | {YYYY-MM-DD} |
| **Autor** | design-agent |
| **DEFINE** | [DEFINE_{FEATURE}.md](./DEFINE_{FEATURE}.md) |
| **Status** | Rascunho / Pronto para Build |
| **Evals Digest** | _gerado por `eval_runner.py freeze`_ |
| **Gerado por** | {harness} · papel `{papel do OMP ou "sessão"}` · `{modelo ou desconhecido}` |

---

## Visão Geral da Arquitetura

```text
┌─────────────────────────────────────────────────────┐
│                  DIAGRAMA DO SISTEMA                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  {Diagrama ASCII mostrando componentes e fluxo}     │
│                                                      │
│  [Entrada] → [Componente A] → [Componente B] → [Saída] │
│                  ↓                 ↓                 │
│            [Armazenamento]    [API Externa]          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Componentes

| Componente | Propósito | Tecnologia |
|------------|-----------|------------|
| {Componente A} | {O que ele faz} | {Stack tecnológica} |
| {Componente B} | {O que ele faz} | {Stack tecnológica} |
| {Componente C} | {O que ele faz} | {Stack tecnológica} |

---

## Decisões Principais

### Decisão 1: {Nome da Decisão}

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | {YYYY-MM-DD} |

**Contexto:** {Por que esta decisão foi necessária}

**Escolha:** {O que decidimos fazer}

**Justificativa:** {Por que esta é a escolha correta}

**Alternativas Rejeitadas:**
1. {Opção A} - Rejeitada porque {motivo}
2. {Opção B} - Rejeitada porque {motivo}

**Consequências:**
- {Trade-off que aceitamos}
- {Benefício que obtemos}

---

### Decisão 2: {Nome da Decisão}

{Repetir estrutura acima}

---

## Manifesto de Arquivos

| # | Arquivo | Ação | Propósito | Agente | Dependências |
|---|---------|------|-----------|--------|--------------|
| 1 | `{caminho/para/arquivo.py}` | Criar | {Propósito} | @{nome-agente} | Nenhuma |
| 2 | `{caminho/para/config.yaml}` | Criar | {Propósito} | @{nome-agente} | Nenhuma |
| 3 | `{caminho/para/handler.py}` | Criar | {Propósito} | @{nome-agente} | 1, 2 |
| 4 | `{caminho/para/test.py}` | Criar | {Propósito} | @{nome-agente} | 3 |

**Total de Arquivos:** {N}

---

## Justificativa de Atribuição de Agentes

> Agentes descobertos em `${GROK_PLUGIN_ROOT}/agents/` - a fase de Build invoca os especialistas correspondentes.

| Agente | Arquivos Atribuídos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @{agente-1} | 1, 3 | {Correspondência de especialização: ex., "padrões de roteamento de API"} |
| @{agente-2} | 2 | {Correspondência de especialização: ex., "modelos de validação de dados"} |
| @{agente-3} | 4 | {Correspondência de especialização: ex., "fixtures de teste"} |
| (direto) | {se houver} | {Nenhum especialista encontrado - Build executa diretamente} |

**Descoberta de Agentes:**
- Escaneado: `${GROK_PLUGIN_ROOT}/agents/*.md`
- Correspondido por: Tipo de arquivo, palavras-chave de propósito, padrões de caminho, domínios KB

---

## Padrões de Código

### Padrão 1: {Nome do Padrão}

```python
# {Breve descrição de quando usar este padrão}

{Trecho de código pronto para copiar e colar}
```

### Padrão 2: {Nome do Padrão}

```python
{Trecho de código pronto para copiar e colar}
```

### Padrão 3: Estrutura de Configuração

```yaml
# estrutura do config.yaml
{Template de configuração YAML}
```

---

## Fluxo de Dados

```text
1. {Passo 1: ex., "Usuário envia requisição via API"}
   │
   ▼
2. {Passo 2: ex., "Requisição validada e enfileirada"}
   │
   ▼
3. {Passo 3: ex., "Worker em background processa a requisição"}
   │
   ▼
4. {Passo 4: ex., "Resultados armazenados no banco de dados"}
```

---

## Pontos de Integração

| Sistema Externo | Tipo de Integração | Autenticação |
|----------------|-------------------|--------------|
| {Sistema A} | {REST API / SDK / Queue} | {Método} |
| {Sistema B} | {REST API / SDK / Queue} | {Método} |

---

## Estratégia de Testes

| Tipo de Teste | Escopo | Arquivos | Ferramentas | Meta de Cobertura |
|---------------|--------|----------|-------------|-------------------|
| Unitário | Funções | `{arquivos de teste}` | {framework de teste} | 80% |
| Integração | Chamadas de API | `{arquivos de teste de integração}` | {framework + mocks} | Caminhos principais |
| E2E | Fluxo completo | Manual | - | Caminho feliz |

---

## Tratamento de Erros

| Tipo de Erro | Estratégia de Tratamento | Retry? |
|-------------|-------------------------|--------|
| {Erro A} | {Como tratar} | Sim/Não |
| {Erro B} | {Como tratar} | Sim/Não |
| {Erro C} | {Como tratar} | Sim/Não |

---

## Configuração

| Chave de Config | Tipo | Padrão | Descrição |
|----------------|------|--------|-----------|
| `{chave_1}` | string | `{padrão}` | {O que controla} |
| `{chave_2}` | int | `{padrão}` | {O que controla} |
| `{chave_3}` | bool | `{padrão}` | {O que controla} |

---

## Considerações de Segurança

- {Consideração de segurança 1}
- {Consideração de segurança 2}
- {Consideração de segurança 3}

---

## Observabilidade

| Aspecto | Implementação |
|---------|---------------|
| Logging | {Abordagem: ex., "Logging estruturado em JSON"} |
| Métricas | {Abordagem: ex., "Métricas customizadas via serviço de monitoramento"} |
| Tracing | {Abordagem: ex., "Spans OpenTelemetry"} |

---

## Arquitetura de Pipeline (se aplicável)

> Inclua esta seção quando a feature envolver pipelines de dados, ETL ou analytics.

### Diagrama do DAG

```text
[Origem A] ──extrai──→ [Camada Raw] ──transforma──→ [Staging] ──modela──→ [Marts]
[Origem B] ──extrai──↗       ↓                          ↓               ↓
                          [Arquivo]            [Gate de Qualidade]  [Dashboard]
```

### Estratégia de Particionamento

| Tabela | Chave de Partição | Granularidade | Justificativa |
|--------|-------------------|---------------|---------------|
| {tabela_1} | {coluna} | {diário / mensal} | {Padrões de query, volume} |

### Estratégia Incremental

| Modelo | Estratégia | Coluna-Chave | Lookback |
|--------|------------|--------------|----------|
| {modelo_1} | {incremental_by_time / unique_key / full_refresh} | {coluna} | {N dias} |

### Plano de Evolução de Schema

| Tipo de Mudança | Tratamento | Rollback |
|----------------|------------|----------|
| Nova coluna | {Adicionar com DEFAULT, backfill assíncrono} | {Remover coluna} |
| Mudança de tipo | {Período de dual-write, depois migrar} | {Reverter tipo} |
| Remoção de coluna | {Deprecar no contrato, remover após N dias} | {Re-adicionar coluna} |

### Gates de Qualidade de Dados

| Gate | Ferramenta | Threshold | Ação em Falha |
|------|------------|-----------|---------------|
| {Verificação de nulls em PKs} | {dbt test / GE} | {0 nulls} | {Bloquear pipeline} |
| {Delta de contagem de linhas} | {dbt test / GE} | {<10% de variação} | {Alertar + continuar} |
| {Verificação de atualização} | {dbt source freshness} | {< N horas} | {Alertar} |

---

## Evals

> Contrato de aceitação executável: pelo menos um eval por AT do DEFINE. Escrito antes do código,
> congelado por `eval_runner.py freeze` (linha **Evals Digest**), checado pelo `/build` (`pre`)
> e reexecutado pelo `/eval`. Mude este bloco só via `/iterate`.
>
> - `deterministic`: bash; exit 0 = passa. Para Python, use `"$AGENTSPEC_PYTHON"`.
> - `graded`: critério subjetivo; `[eval.state]` = campo → comando bash; 2–5 perguntas, ≥ 1 `score`. Máximo 50% do contrato.
> - `human`: comportamento que exige execução real de agente ou serviço externo; `owner` + `instructions`.

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_1"
verifies = ["AT-001"]
check_type = "deterministic"
description = "{O que este eval prova}"
run = '''
{comando bash que sai com 0 quando o AT-001 é satisfeito}
'''

[[eval]]
id = "eval_2"
verifies = ["AT-002"]
check_type = "graded"
description = "{Critério subjetivo}"

[eval.state]
artifact = "{comando bash cuja stdout é o artefato avaliado}"

[[eval.questions]]
id = "meets_criterion"
type = "noul"
instructions = "Does `artifact` {satisfaz o critério}?"

[[eval.questions]]
id = "quality"
type = "score"
instructions = "How well does `artifact` {satisfaz o critério}?"
criteria = ["{nível mais baixo}", "{intermediário}", "{nível de topo}"]

[[eval]]
id = "eval_3"
verifies = ["AT-003"]
check_type = "human"
owner = "{responsável}"
description = "{O que a pessoa confirma}"
instructions = "{Passos exatos para verificar}"
```

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | {YYYY-MM-DD} | design-agent | Versão inicial |

---

## Próximo Passo

**Pronto para:** `/build .claude/sdd/features/DESIGN_{FEATURE_NAME}.md` (o `/build` roda `eval_runner.py pre` antes da primeira tarefa)

# DESIGN: {Nome da Feature}

> Design técnico para implementação de {Nome da Feature}

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Data** | {AAAA-MM-DD} |
| **Autor** | design-agent |
| **DEFINE** | [01_DEFINE_{FEATURE}.md](./01_DEFINE_{FEATURE}.md) |
| **Status** | Rascunho / Pronto para Construir |

---

## Visão Geral da Arquitetura

```text
┌─────────────────────────────────────────────────────┐
│                   DIAGRAMA DO SISTEMA                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  {Diagrama ASCII mostrando componentes e fluxo}     │
│                                                      │
│  [Entrada] → [Componente A] → [Componente B] → [Saída] │
│                  ↓                 ↓                 │
│             [Armazenamento]   [API Externa]         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Componentes

| Componente | Propósito | Tecnologia |
|------------|-----------|------------|
| {Componente A} | {O que faz} | {Stack tecnológico} |
| {Componente B} | {O que faz} | {Stack tecnológico} |
| {Componente C} | {O que faz} | {Stack tecnológico} |

---

## Decisões-Chave

### Decisão 1: {Nome da Decisão}

| Atributo | Valor |
|----------|-------|
| **Status** | Aceita |
| **Data** | {AAAA-MM-DD} |

**Contexto:** {Por que esta decisão foi necessária}

**Escolha:** {O que decidimos fazer}

**Justificativa:** {Por que esta é a escolha certa}

**Alternativas Rejeitadas:**
1. {Opção A} - Rejeitada porque {razão}
2. {Opção B} - Rejeitada porque {razão}

**Consequências:**
- {Trade-off que aceitamos}
- {Benefício que ganhamos}

---

### Decisão 2: {Nome da Decisão}

{Repetir estrutura acima}

---

## Manifesto de Arquivos

| # | Arquivo | Ação | Propósito | Agente | Dependências |
|---|---------|------|-----------|--------|-------------|
| 1 | `{caminho/arquivo.py}` | Criar | {Propósito} | @{nome-agente} | Nenhuma |
| 2 | `{caminho/config.yaml}` | Criar | {Propósito} | @{nome-agente} | Nenhuma |
| 3 | `{caminho/handler.py}` | Criar | {Propósito} | @{nome-agente} | 1, 2 |
| 4 | `{caminho/test.py}` | Criar | {Propósito} | @{nome-agente} | 3 |

**Total de Arquivos:** {N}

---

## Justificativa de Atribuição de Agentes

> Agentes descobertos em `.claude/agents/` - Fase Build invoca os especialistas correspondentes.

| Agente | Arquivos Atribuídos | Por Que Este Agente |
|--------|---------------------|---------------------|
| @{agente-1} | 1, 3 | {Match de especialização: ex: "padrões de routing de API"} |
| @{agente-2} | 2 | {Match de especialização: ex: "modelos de validação de dados"} |
| @{agente-3} | 4 | {Match de especialização: ex: "fixtures de teste"} |
| (geral) | {se houver} | {Nenhum especialista encontrado - Build lida diretamente} |

**Descoberta de Agentes:**
- Escaneados: `.claude/agents/**/*.md`
- Correspondência por: Tipo de arquivo, palavras-chave de propósito, padrões de caminho, domínios KB

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
# Estrutura do config.yaml
{Template de configuração YAML}
```

---

## Fluxo de Dados

```text
1. {Passo 1: ex: "Usuário envia requisição via API"}
   │
   ▼
2. {Passo 2: ex: "Requisição validada e enfileirada"}
   │
   ▼
3. {Passo 3: ex: "Worker em background processa requisição"}
   │
   ▼
4. {Passo 4: ex: "Resultados armazenados no banco de dados"}
```

---

## Pontos de Integração

| Sistema Externo | Tipo de Integração | Autenticação |
|-----------------|-------------------|--------------|
| {Sistema A} | {REST API / SDK / Fila} | {Método} |
| {Sistema B} | {REST API / SDK / Fila} | {Método} |

---

## Estratégia de Testes

| Tipo de Teste | Escopo | Arquivos | Ferramentas | Meta de Cobertura |
|---------------|--------|----------|-------------|-------------------|
| Unitário | Funções | `{arquivos de teste}` | {framework de teste} | 80% |
| Integração | Chamadas API | `{arquivos de teste de integração}` | {framework + mocks} | Caminhos-chave |
| E2E | Fluxo completo | Manual | - | Caminho feliz |

---

## Tratamento de Erros

| Tipo de Erro | Estratégia de Tratamento | Retry? |
|--------------|--------------------------|--------|
| {Erro A} | {Como tratar} | Sim/Não |
| {Erro B} | {Como tratar} | Sim/Não |
| {Erro C} | {Como tratar} | Sim/Não |

---

## Configuração

| Chave de Config | Tipo | Padrão | Descrição |
|-----------------|------|--------|-----------|
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
| Logging | {Abordagem: ex: "Logging estruturado em JSON"} |
| Métricas | {Abordagem: ex: "Métricas customizadas via serviço de monitoramento"} |
| Tracing | {Abordagem: ex: "Spans OpenTelemetry"} |

---

## Histórico de Revisões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | {AAAA-MM-DD} | design-agent | Versão inicial |

---

## Mapa do Workflow

```text
📍 Progresso do Workflow
════════════════════════════════════════════
✅ Fase 0: Explorar        (se aplicável)
✅ Fase 1: Definir
✅ Fase 2: Projetar        ← CONCLUÍDA
➡️ Fase 3: /construir
⬜ Fase 4: /entregar
```

---

## Próxima Etapa

**Pronto para:** `/construir .claude/sdd/features/02_DESIGN_{FEATURE_NAME}.md`

💡 **Dica:** O `/construir` executará a implementação com delegação de agentes, verificação incremental e relatório de build.

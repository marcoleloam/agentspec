# BLACKBOARD: {Nome da Feature}

> Quadro compartilhado da feature — o estado vivo e a memória da trajetória, do
> Brainstorm ao Ship. Todos os agentes (orquestrador e especialistas) LEEM este arquivo
> antes de agir e ANEXAM aqui as decisões, premissas, perguntas e interfaces que criarem.
> Guarde ponteiro + uma frase de porquê: o conteúdo completo vive no documento de cada fase.
> Regras completas: `WORKFLOW_CONTRACTS.yaml` → `living_memory`.
>
> Mantenha os títulos de seção e os cabeçalhos das tabelas exatamente como aqui (coluna
> `#` para o ID): o `memory-index.py` lê só estes e avisa (exit 2) sobre linhas que não consegue ler.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Fase** | Brainstorm / Define / Design / Build / Ship |
| **Atualizado em** | {YYYY-MM-DD} |
| **Domínios KB** | {domínio-1, domínio-2} |
| **Relacionada a** | {OUTRA_FEATURE, …} ou — |
| **DESIGN** | [DESIGN_{FEATURE}.md](DESIGN_{FEATURE}.md) |
| **Status** | 🔄 Em Andamento / ✅ Completo / ❌ Bloqueado |

---

## Interfaces Compartilhadas

> Contratos que TODO agente DEVE respeitar. Nomes de tabelas, schemas, assinaturas de
> função, chaves de config, contratos de dados. Se você cria algo que outro agente vai
> consumir, registre aqui. Se vai consumir algo, leia aqui primeiro — não reinvente.

| # | Tipo | Nome / Assinatura | Definido por | Consumido por | Notas |
|---|------|-------------------|--------------|---------------|-------|
| I-001 | {tabela/função/schema/config} | `{nome ou assinatura}` | @{agente} | @{agente} | {contrato, tipos, restrições} |

---

## Log de Decisões

> Append-only, do Brainstorm ao Ship. Nunca edite uma decisão existente — registre uma
> nova com "Substitui" apontando a anterior. No Build, todo desvio do DESIGN entra aqui
> substituindo a decisão de Design correspondente.

| # | Fase | Agente | Decisão | Justificativa | Alternativa Rejeitada | Substitui | Onde Ler | Data |
|---|------|--------|---------|---------------|-----------------------|-----------|----------|------|
| D-001 | {brainstorm/define/design/build/iterate} | @{agente} | {o que foi decidido} | {por quê, 1 frase} | {o que não foi feito} | — | {DESIGN_{FEATURE}.md#decisão-1-…} | {YYYY-MM-DD} |

---

## Premissas

> O que, se estiver errado, invalida o desenho. Registradas no Define; o Design e o
> Build marcam como validadas ou derrubadas — atualizando só a célula `Status` da linha.

| # | Fase | Premissa | Se Errada | Status | Onde Ler |
|---|------|----------|-----------|--------|----------|
| A-001 | {fase} | {premissa} | {impacto} | ⏳ Não validada / ✅ Validada / ❌ Derrubada | {DEFINE_{FEATURE}.md#premissas} |

---

## Perguntas Abertas e Bloqueadores

> Levante aqui o que você não consegue resolver sozinho em vez de assumir.
> 🔴 Aberto **bloqueia** Define→Design e Design→Build. 🟡 Delegada = passada de propósito
> à fase seguinte, que deve fechá-la como 🟢 citando o `D-###` que a responde — atualizando
> só as células `Status` e `Resolução` da linha.

| # | Fase | Levantado por | Pergunta / Bloqueador | Status | Resolução |
|---|------|---------------|------------------------|--------|-----------|
| Q-001 | {fase} | @{agente} | {o que precisa ser decidido} | 🔴 Aberto / 🟡 Delegada ao {fase} / 🟢 Resolvido | {resposta ou D-###} |

---

## Status dos Arquivos

> Espelha o file manifest do DESIGN. Preenchido no Build; cada agente marca seu arquivo ao concluir.

| Arquivo | Agente | Status | Verificado | Notas |
|---------|--------|--------|------------|-------|
| `{caminho/arquivo}` | @{agente} | ⏳ Pendente / 🔄 Em Andamento / ✅ Completo | ✅ / — | {notas} |

**Legenda:** ⏳ Pendente · 🔄 Em Andamento · ✅ Completo · ❌ Bloqueado

---

## Melhorias / Iterações

> Histórico append-only das melhorias pedidas DEPOIS do build inicial (via `/work`).
> Cada pedido solto do usuário ("melhora o tratamento de erro") vira uma linha aqui — é
> a memória de trabalho da feature, para você não ter que re-explicar o contexto.

| # | Data | Pedido | Tipo | Agente | Status |
|---|------|--------|------|--------|--------|
| M-001 | {YYYY-MM-DD} | {o que o usuário pediu} | código / design | @{agente} | ⏳ / ✅ |

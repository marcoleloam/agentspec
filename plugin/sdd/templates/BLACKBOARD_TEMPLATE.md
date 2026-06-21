# BLACKBOARD: {Nome da Feature}

> Quadro de coordenação compartilhada — o estado vivo desta feature durante o Build.
> Todos os agentes (orquestrador e especialistas) LEEM este arquivo antes de agir
> e ANEXAM aqui qualquer decisão, interface ou bloqueador que criarem.
> Substitui o repasse de contexto pelo orquestrador (padrão blackboard).

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | {FEATURE_NAME} |
| **Fase** | Build |
| **Atualizado em** | {YYYY-MM-DD} |
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

> Append-only. Cada agente registra decisões que afetam outros (ADR-lite). Nunca edite
> uma decisão existente — adicione uma nova que a substitua e referencie a anterior.

| # | Agente | Decisão | Justificativa | Substitui | Data |
|---|--------|---------|---------------|-----------|------|
| D-001 | @{agente} | {o que foi decidido} | {por quê} | — | {YYYY-MM-DD} |

---

## Perguntas Abertas e Bloqueadores

> Levante aqui o que você não consegue resolver sozinho em vez de assumir. O orquestrador
> ou outro especialista resolve e marca como respondido.

| # | Levantado por | Pergunta / Bloqueador | Status | Resolução |
|---|---------------|------------------------|--------|-----------|
| Q-001 | @{agente} | {o que precisa ser decidido} | 🔴 Aberto / 🟢 Resolvido | {resposta} |

---

## Status dos Arquivos

> Espelha o file manifest do DESIGN. Cada agente marca seu arquivo ao concluir.

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

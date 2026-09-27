# DEFINE: KB Evolution — Ingest/Lint para KBs Vivos (retroconversão)

> Cópia resumida, apenas para fins de fixture de teste, da tabela de ATs de
> `.claude/sdd/archive/KB_EVOLUTION/DEFINE_KB_EVOLUTION.md`. O texto das
> colunas é idêntico ao original; o resto do documento foi omitido porque o
> `eval_runner` só lê a tabela de ATs (`parse_ats`) e a seção `## Evals` do
> DESIGN correspondente.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_EVOLUTION |
| **Status** | ✅ Complete (Built) |

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Ingest com sucesso via Context7 | Domínio `dbt` existente com `mcp_validated: 2026-03-26` | `/ingest-kb dbt` é executado | KB atualizado, `log.md` criado/atualizado com timestamp e mudanças, `mcp_validated` atualizado no `_index.yaml` |
| AT-002 | Domínio sem cobertura no Context7 | Domínio `medallion` sem library-id no Context7 | `/ingest-kb medallion` é executado | Comando detecta ausência, informa o usuário, sugere fallback (web search manual), não altera ficheiros existentes |
| AT-003 | Lint detecta conteúdo stale | Domínio com API deprecada documentada no KB | `/lint-kb <domain>` é executado | Relatório lista a API deprecada como issue de tipo "stale", com referência ao ficheiro e linha |
| AT-004 | Lint all consolida todos os domínios | 39 domínios com estados variados | `/lint-kb --all` é executado | Relatório consolidado com lista de todos os domínios, contagem de issues por categoria e ranking por severidade |
| AT-005 | Idempotência do ingest | Domínio já atualizado recentemente (sem mudanças na lib) | `/ingest-kb <domain>` é executado novamente | Comando detecta ausência de mudanças relevantes, registra no `log.md` como "no changes detected", não sobrescreve ficheiros |
| AT-006 | Preservação de formato KB | Qualquer domínio existente | `/ingest-kb <domain>` completa com sucesso | Estrutura de diretórios (index.md, quick-reference.md, concepts/, patterns/) preservada; nenhum ficheiro removido sem confirmação explícita |

## Próximo Passo

**Pronto para:** fixture — retroconversão de teste, não altera o `archive/` real.

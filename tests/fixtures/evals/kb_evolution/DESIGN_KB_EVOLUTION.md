# DESIGN: KB Evolution (retroconversão)

> Contrato de evals retroconvertido a partir dos 6 ATs de `KB_EVOLUTION`
> (feature já shipada, ver Critério de Sucesso do DEFINE_POST_BUILD_EVALS:
> "O runner executa as seções `## Evals` retroconvertidas de 2 features
> shipadas ... sem erro de execução"). Doutrina: determinístico sempre que
> bash consegue checar; `graded` só para julgamento de qualidade textual
> (citação de linha); `human` para o único AT que depende de uma chamada real
> ao Context7 e da qualidade da reescrita por LLM.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | KB_EVOLUTION |
| **Status** | Pronto para Build |
| **Evals Digest** | (não congelado) |

## Evals

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_at001"
verifies = ["AT-001"]
check_type = "human"
owner = "Marco"
description = "Ingest via Context7 atualiza o KB e o log corretamente"
instructions = "Rode /ingest-kb dbt, confira log.md e o mcp_validated no _index.yaml, e avalie se a reescrita do LLM preservou o sentido técnico do conteúdo."

[[eval]]
id = "eval_at002"
verifies = ["AT-002"]
check_type = "deterministic"
description = "Domínio sem cobertura no Context7 é detectado, o fallback é reportado e nada é alterado"
run = '''
grep -qi "fallback" .claude/kb/medallion/ingest.log
git diff --quiet -- .claude/kb/medallion
'''

[[eval]]
id = "eval_at003"
verifies = ["AT-003"]
check_type = "graded"
description = "Lint reporta a API deprecada como stale, citando arquivo e linha"

[eval.state]
report = "cat .claude/kb/dbt/LINT_REPORT.md"
fixture = "cat .claude/kb/dbt/deprecated_api_fixture.md"

[[eval.questions]]
id = "lists_stale"
type = "noul"
instructions = "O `report` lista a API deprecada em `fixture` como um issue do tipo 'stale'?"

[[eval.questions]]
id = "cites_location"
type = "score"
instructions = "Com que precisão o `report` cita o arquivo e a linha desse issue?"
criteria = ["sem citação", "só o arquivo", "arquivo e linha"]

[[eval]]
id = "eval_at004"
verifies = ["AT-004"]
check_type = "deterministic"
description = "Lint --all consolida todos os domínios com ranking por severidade"
run = '''
grep -q "^# Lint Consolidado" .claude/kb/LINT_ALL_REPORT.md
grep -q "Ranking por severidade" .claude/kb/LINT_ALL_REPORT.md
test "$(grep -c '^| ' .claude/kb/LINT_ALL_REPORT.md)" -ge 3
'''

[[eval]]
id = "eval_at005"
verifies = ["AT-005"]
check_type = "deterministic"
description = "Ingest idempotente registra 'no changes detected' e não sobrescreve arquivos"
run = '''
grep -q "no changes detected" .claude/kb/dbt/log.md
'''

[[eval]]
id = "eval_at006"
verifies = ["AT-006"]
check_type = "deterministic"
description = "Estrutura de diretórios do domínio é preservada após o ingest"
run = '''
test -f .claude/kb/dbt/index.md
test -f .claude/kb/dbt/quick-reference.md
test -d .claude/kb/dbt/concepts
test -d .claude/kb/dbt/patterns
'''
```

## Próximo Passo

**Pronto para:** fixture — retroconversão de teste, não altera o `archive/` real.

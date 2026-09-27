# DESIGN: Frontend Ecosystem (retroconversão)

> Contrato de evals retroconvertido a partir dos 5 ATs de `FRONTEND_ECOSYSTEM`.
> Doutrina: determinístico sempre que bash consegue checar (manifesto de
> arquivos, ordem de leitura de KB, atributos de acessibilidade); `graded`
> para julgar a qualidade do uso da doc do MCP; `human` para a única
> orquestração que só existe dentro de uma sessão real (`Task` delegando
> ao react-developer).

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | FRONTEND_ECOSYSTEM |
| **Status** | Pronto para Build |
| **Evals Digest** | (não congelado) |

## Evals

<!-- agentspec:evals:contract -->
```toml
[[eval]]
id = "eval_at001"
verifies = ["AT-001"]
check_type = "deterministic"
description = "File Manifest atribui @react-developer e @css-specialist nos arquivos frontend"
run = '''
grep -Eq '@react-developer' artifacts/FILE_MANIFEST.md
grep -Eq '\.tsx' artifacts/FILE_MANIFEST.md
grep -q '@css-specialist' artifacts/FILE_MANIFEST.md
'''

[[eval]]
id = "eval_at002"
verifies = ["AT-002"]
check_type = "human"
owner = "Marco"
description = "build-agent delega via Task ao react-developer, que consulta a KB antes de gerar"
instructions = "Rode /build numa feature frontend e confira no transcript que o Task foi delegado a @react-developer e que a KB foi lida antes da geração de código."

[[eval]]
id = "eval_at003"
verifies = ["AT-003"]
check_type = "deterministic"
description = "react-developer lê o pattern da KB antes de gerar o componente (KB-First)"
run = '''
read_line=$(grep -n "READ .claude/kb/react" artifacts/build.log | head -1 | cut -d: -f1)
gen_line=$(grep -n "GENERATE app/page.tsx" artifacts/build.log | head -1 | cut -d: -f1)
test -n "$read_line"
test -n "$gen_line"
test "$read_line" -lt "$gen_line"
'''

[[eval]]
id = "eval_at004"
verifies = ["AT-004"]
check_type = "graded"
description = "Quando a KB não cobre Server Actions, o agente consulta o context7 e usa a doc corretamente"

[eval.state]
log = "cat artifacts/build.log"

[[eval.questions]]
id = "consulted_context7"
type = "noul"
instructions = "O `log` mostra uma consulta ao context7 para a documentação de React Server Actions?"

[[eval.questions]]
id = "used_docs_well"
type = "score"
instructions = "Quão bem o `log` mostra que a doc retornada foi usada na implementação?"
criteria = ["não usou", "usou parcialmente", "usou corretamente"]

[[eval]]
id = "eval_at005"
verifies = ["AT-005"]
check_type = "deterministic"
description = "Componente gerado tem atributos de acessibilidade básicos (aria-label, alt)"
run = '''
grep -q 'aria-label=' artifacts/generated/Button.tsx
grep -q 'alt=' artifacts/generated/Button.tsx
'''
```

## Próximo Passo

**Pronto para:** fixture — retroconversão de teste, não altera o `archive/` real.

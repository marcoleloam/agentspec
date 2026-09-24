# DEFINE: Frontend Ecosystem (retroconversão)

> Cópia resumida, apenas para fins de fixture de teste, da tabela de ATs de
> `.claude/sdd/archive/FRONTEND_ECOSYSTEM/DEFINE_FRONTEND_ECOSYSTEM.md`.

## Metadados

| Atributo | Valor |
|----------|-------|
| **Feature** | FRONTEND_ECOSYSTEM |
| **Status** | ✅ Complete (Built) |

## Testes de Aceitação

| ID | Cenário | Dado | Quando | Então |
|----|---------|------|--------|-------|
| AT-001 | Design com projeto Next.js | CLAUDE.md menciona Next.js + React + Tailwind | `/design` roda com DEFINE de feature frontend | File Manifest contém `@react-developer` e `@css-specialist` nos arquivos .tsx |
| AT-002 | Build delega a react-developer | DESIGN tem arquivo .tsx com `@react-developer` | `/build` executa | build-agent delega via Task ao react-developer, que consulta KB react/ antes de gerar |
| AT-003 | KB-First no react-developer | react-developer recebe task para criar componente | Agente inicia execução | Primeiro lê `.claude/kb/react/patterns/component-composition.md`, depois gera código |
| AT-004 | MCP fallback funciona | KB react/ não tem pattern para Server Actions | react-developer precisa do pattern | Consulta context7 para docs oficiais de React Server Actions |
| AT-005 | a11y-specialist no review | Código frontend gerado pelo build | `/review` roda em projeto frontend | a11y-specialist verifica aria labels, contraste, keyboard navigation |

## Próximo Passo

**Pronto para:** fixture — retroconversão de teste, não altera o `archive/` real.

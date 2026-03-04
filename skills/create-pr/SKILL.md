---
name: create-pr
description: "Cria pull requests profissionais com commits convencionais e descrições estruturadas. Use quando o usuário quiser criar um PR ou commitar mudanças. Acione proativamente ao final de qualquer implementação ou quando o usuário disser 'criar PR', 'fazer merge' ou 'commitar'."
user-invokable: true
allowed-tools: Read, Grep, Glob, Bash, AskUserQuestion
argument-hint: "[título-opcional]"
---

# Comando Create PR

> Automatizar criação profissional de pull requests com commits convencionais e descrições estruturadas

## Idioma

> Este projeto usa **Português-BR** como idioma padrão — toda comunicação com o usuário e documentos gerados devem seguir esse padrão para manter consistência com o restante do framework.

---

## Uso

```bash
/create-pr                           # Detectar mudanças e criar PR automaticamente
/create-pr "feat: add user auth"     # Criar PR com título customizado
/create-pr --draft                   # Criar como PR draft
/create-pr --review                  # Executar revisão dual AI antes de criar o PR
```

---

## Opção de Revisão Pré-PR

Ao usar `--review`, o comando executa uma **revisão dual AI** (CodeRabbit + Claude) antes de criar o PR. Problemas críticos bloqueiam a criação do PR.

---

## Processo

### Passo 1: Analisar Mudanças

```bash
git status
git diff --stat
git log origin/main..HEAD --oneline
```

### Passo 2: Determinar Tipo do PR

| Arquivos Alterados | Tipo Provável |
|--------------------|---------------|
| `src/**/*.py` + nova funcionalidade | `feat:` |
| `src/**/*.py` + correção de bug | `fix:` |
| `*.md`, `docs/**` | `docs:` |
| `tests/**` | `test:` |
| `agents/**` | `refactor(agents):` |
| `kb/**` | `docs(kb):` |
| `sdd/**` | `docs(sdd):` |

### Passo 3: Gerar Mensagem de Commit

Formato Conventional Commits com `Co-Authored-By: Claude <noreply@anthropic.com>`.

### Passo 4: Confirmar com o Usuário

Confirmar tipo do PR, escopo, breaking changes e issues relacionadas.

### Passo 5: Construir Descrição do PR

Descrição estruturada com Resumo, Principais Mudanças, Arquivos Alterados, Plano de Testes, Breaking Changes.

### Passo 6: Criar Branch, Commit, Push e PR

```bash
gh pr create --title "<type>(<scope>): <description>" --body "<generated-body>" --base main
```

---

## Saída

- **Branch:** `<tipo>/<descrição-curta>`
- **Commit:** Formato Conventional Commits
- **URL do PR:** Retornado pelo `gh pr create`

---

## Referência de Conventional Commits

| Tipo | Quando Usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Reestruturação de código |
| `docs` | Documentação |
| `test` | Testes |
| `chore` | Manutenção |

---

## Referências

- Review Skill: `skills/review/SKILL.md`
- Agente: `agents/code-reviewer.md`

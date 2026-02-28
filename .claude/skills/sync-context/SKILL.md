---
name: sync-context
description: Sync project context to CLAUDE.md by analyzing codebase patterns and conventions
user-invocable: true
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
argument-hint: [--section nome-seção]
---

# Comando Sync Context

Analisa o codebase e atualiza inteligentemente o `CLAUDE.md` com o contexto atual do projeto.

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Uso

```bash
/sync-context                    # Análise completa e atualização
/sync-context --section agents   # Atualizar seção específica
/sync-context --dry-run          # Pré-visualizar sem salvar
```

---

## O Que Faz

1. **Analisa** a estrutura atual do codebase
2. **Extrai** padrões, convenções e arquitetura
3. **Mescla** com conteúdo existente do CLAUDE.md
4. **Preserva** customizações manuais
5. **Atualiza** seções que precisam de refresh

---

## Processo de Análise

### Passo 1: Escanear Estrutura do Codebase

```text
Glob("**/*.py")              # Arquivos Python
Glob("**/*.ts")              # Arquivos TypeScript
Glob("**/package.json")      # Projetos Node
Glob("**/pyproject.toml")    # Projetos Python
```

### Passo 2: Extrair Padrões

```text
Grep("@dataclass")           # Uso de dataclass
Grep("class.*Parser")        # Padrões de parser
Grep("def test_")            # Padrões de teste
```

### Passo 3: Analisar Agentes e Skills

```text
Glob(".claude/agents/**/*.md")
Glob(".claude/skills/**/SKILL.md")
```

### Passo 4: Mesclar Atualizações

| Seção | Fonte | Modo de Atualização |
| ----- | ----- | ------------------- |
| Contexto do Projeto | Manual | Preservar |
| Arquitetura | Scan do codebase | Substituir |
| Estrutura do Projeto | Padrões Glob | Substituir |
| Uso de Agentes | Pasta agents/ | Substituir |
| Padrões de Código | Detecção de padrões | Mesclar |
| Skills | Pasta skills/ | Substituir |
| Ambiente | Arquivos de config | Mesclar |
| Datas Importantes | Manual | Preservar |

**Substituir**: Regenerar completamente da fonte
**Mesclar**: Adicionar novos, preservar customizados
**Preservar**: Nunca modificar automaticamente

---

## Flags

| Flag | Descrição |
| ---- | --------- |
| `--dry-run` | Pré-visualizar sem salvar |
| `--section {nome}` | Atualizar apenas seção específica |
| `--force` | Substituir todas as seções (ignora regras de preservação) |
| `--verbose` | Mostrar análise detalhada |

---

## Quando Executar

- Após adicionar novos agentes ou skills
- Após mudanças significativas de arquitetura
- Após adicionar novos tipos de arquivo
- Ao fazer onboarding de novos membros

---

## Gate de Qualidade

```text
[ ] CLAUDE.md lido antes de atualizar
[ ] Seções manuais preservadas
[ ] Seções auto-geradas atualizadas
[ ] Nenhum placeholder restante
[ ] Estrutura de pastas reflete realidade
```

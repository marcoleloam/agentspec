---
name: create-kb
description: Create a complete KB domain from scratch with MCP validation
user-invocable: true
agent: kb-architect
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, WebSearch, WebFetch
argument-hint: [domínio]
---

# Comando Create KB

> Criar um domínio completo de Knowledge Base do zero com validação MCP.

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Uso

```bash
/create-kb <DOMÍNIO>
/create-kb redis
/create-kb pandas
/create-kb authentication
/create-kb --audit
```

---

## O Que Faz

1. **Valida pré-requisitos** — verifica que `_templates/` e `_index.yaml` existem
2. **Invoca kb-architect** — executa workflow completo de criação
3. **Pesquisa documentação** — usa MCP (WebSearch/WebFetch) para validar conteúdo
4. **Cria estrutura** — gera todos os arquivos do domínio KB
5. **Reporta conclusão** — mostra score de qualidade e arquivos criados

---

## Processo

### Passo 1: Verificar Pré-requisitos

```markdown
Read(.claude/kb/_index.yaml)
Read(.claude/kb/_templates/)
```

Se não existirem, informar o usuário e abortar.

### Passo 2: Carregar Templates

```text
.claude/kb/_templates/
├── index.template          # Visão geral do domínio
├── quick-reference.template # Consulta rápida
├── concept.template        # Template de conceito
├── pattern.template        # Template de padrão
├── antipattern.template    # Template de anti-padrão
├── troubleshooting.template # Template de troubleshooting
└── migration.template      # Template de migração
```

### Passo 3: Pesquisar e Validar Conteúdo

Usar ferramentas MCP para pesquisar documentação oficial:
- WebSearch para encontrar docs oficiais
- WebFetch para ler conteúdo
- Validar contra fontes oficiais

### Passo 4: Gerar Estrutura do Domínio

```text
.claude/kb/{domínio}/
├── index.md               # Visão geral
├── quick-reference.md     # Consulta rápida
├── concepts/              # 3-6 conceitos
│   ├── conceito-1.md
│   ├── conceito-2.md
│   └── conceito-3.md
└── patterns/              # 3-6 padrões com código
    ├── padrao-1.md
    ├── padrao-2.md
    └── padrao-3.md
```

### Passo 5: Registrar no Index

Atualizar `.claude/kb/_index.yaml` com o novo domínio.

---

## Opções

| Comando | Ação |
|---------|------|
| `/create-kb <domínio>` | Criar novo domínio KB |
| `/create-kb --audit` | Auditar saúde da KB existente |

---

## Saída

| Artefato | Localização |
|----------|-------------|
| **Index** | `.claude/kb/{domínio}/index.md` |
| **Quick Reference** | `.claude/kb/{domínio}/quick-reference.md` |
| **Conceitos** | `.claude/kb/{domínio}/concepts/*.md` |
| **Padrões** | `.claude/kb/{domínio}/patterns/*.md` |

---

## Gate de Qualidade

```text
[ ] Templates carregados e validados
[ ] Conteúdo pesquisado em fontes oficiais
[ ] Mínimo 3 conceitos criados
[ ] Mínimo 3 padrões com exemplos de código
[ ] Quick reference preenchido
[ ] Index com visão geral completa
[ ] Domínio registrado em _index.yaml
[ ] Exemplos de código sintaticamente corretos
```

---

## Referências

- Agente: `.claude/agents/exploration/kb-architect.md`
- Templates: `.claude/kb/_templates/`
- Registry: `.claude/kb/_index.yaml`

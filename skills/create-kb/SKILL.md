---
name: create-kb
description: "Cria um domínio completo de Knowledge Base validado com MCP a partir do zero. Use quando o usuário quiser documentar uma tecnologia, biblioteca ou padrão na KB do projeto. Acione quando o usuário disser 'criar KB para X', 'documentar biblioteca Y' ou 'adicionar base de conhecimento sobre Z'."
user-invokable: true
agent: kb-architect
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, WebSearch, WebFetch
argument-hint: "[domínio]"
---

# Comando Create KB

> Criar um domínio completo de Knowledge Base do zero com validação MCP.

## Idioma

> Este projeto usa **Português-BR** como idioma padrão — toda comunicação com o usuário e documentos gerados devem seguir esse padrão para manter consistência com o restante do framework.

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
Read(kb/_index.yaml)
Read(kb/_templates/)
```

Se não existirem, informar o usuário e abortar.

### Passo 2: Carregar Templates

```text
kb/_templates/
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
kb/{domínio}/
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

Atualizar `kb/_index.yaml` com o novo domínio.

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
| **Index** | `kb/{domínio}/index.md` |
| **Quick Reference** | `kb/{domínio}/quick-reference.md` |
| **Conceitos** | `kb/{domínio}/concepts/*.md` |
| **Padrões** | `kb/{domínio}/patterns/*.md` |

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

- Agente: `agents/kb-architect.md`
- Templates: `kb/_templates/`
- Registry: `kb/_index.yaml`

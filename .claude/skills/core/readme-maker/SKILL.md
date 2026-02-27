---
name: readme-maker
description: Generate comprehensive, production-ready README.md by analyzing codebase with explorer + documenter agents
user-invocable: true
agent: code-documenter
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, Task
argument-hint: [--style minimal|comprehensive]
---

# Comando README Maker

Gera um README.md profissional combinando exploração do codebase com boas práticas de documentação.

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Uso

```bash
/readme-maker                        # Análise completa → README.md
/readme-maker --output docs/         # Saída em diretório específico
/readme-maker --style minimal        # README mínimo (foco no Quick Start)
/readme-maker --style comprehensive  # Documentação completa (padrão)
/readme-maker --dry-run              # Pré-visualizar sem salvar
```

---

## O Que Faz

1. **Explora** codebase usando padrões do codebase-explorer
2. **Analisa** estrutura do projeto, stack tecnológico e padrões
3. **Gera** README.md seguindo padrões do code-documenter
4. **Valida** todos os exemplos e links antes de salvar

---

## Fluxo de Execução

```text
Fase 1: EXPLORAR (escanear raiz, mapear código, identificar stack)
Fase 2: EXTRAIR (arquivos de pacote, entry points, variáveis de ambiente)
Fase 3: GERAR (descrição, Quick Start, features, arquitetura)
Fase 4: VALIDAR (testar comandos, verificar exemplos, checar links)
Fase 5: SALVAR (escrever README.md, reportar resumo)
```

---

## Estilos de Saída

### Minimal (`--style minimal`)
- Nome do projeto + descrição
- Quick Start (instalação + uso básico)
- Licença

### Comprehensive (`--style comprehensive`) - Padrão
- Todas as seções incluindo diagrama de arquitetura
- Referência completa de configuração
- Guia de desenvolvimento
- Links para documentação de API

---

## Gate de Qualidade

```text
CONTEÚDO
[ ] Descrição do projeto clara e atraente
[ ] Quick Start funciona (comandos testados)
[ ] Sem texto placeholder como "TODO" ou "{}"

FORMATO
[ ] Blocos de código com identificador de linguagem
[ ] Tabelas formatadas corretamente
[ ] Links apontam para arquivos existentes

PRECISÃO
[ ] Versão bate com arquivo de pacote
[ ] Instalação realmente funciona
```

---

## Integração de Agentes

| Agente | Propósito |
| ------ | --------- |
| **codebase-explorer** | Análise abrangente do codebase |
| **code-documenter** | Padrões de geração de documentação |

---

## Flags

| Flag | Descrição |
| ---- | --------- |
| `--output {dir}` | Diretório de saída (padrão: raiz do projeto) |
| `--style {tipo}` | `minimal` ou `comprehensive` (padrão) |
| `--dry-run` | Pré-visualizar sem salvar |
| `--force` | Sobrescrever sem preservar conteúdo manual |

---

## Referências

- Agente: `.claude/agents/code-quality/code-documenter.md`
- Explorador: `.claude/agents/exploration/codebase-explorer.md`

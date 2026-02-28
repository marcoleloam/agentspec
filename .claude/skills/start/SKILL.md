---
name: start
description: Display AgentSpec welcome screen with project status and quick-start guidance
user-invokable: true
---

# Comando Start

> Tela de boas-vindas do AgentSpec com status do projeto e orientação para início rápido.

## Uso

```bash
/start
```

## Exemplos

```bash
# Iniciar sessão e ver estado do projeto
/start
```

---

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## O Que Este Comando Faz

1. **Inventariar** — Ler estado atual do projeto (features, reports, archive)
2. **Exibir** — Renderizar tela de boas-vindas estilo Claude Code com ASCII box
3. **Listar** — Mostrar features ativas com fase atual e features entregues
4. **Sugerir** — Recomendar próximo passo inteligente baseado no estado detectado
5. **Direcionar** — Perguntar ao usuário o que deseja fazer

---

## Processo

### Passo 1: Ler Estado do Projeto

```text
Read(CLAUDE.md)                              → Versão, nome do projeto
Glob(.claude/sdd/features/*.md)              → Features em andamento
Glob(.claude/sdd/reports/*.md)               → Build reports
Glob(.claude/sdd/archive/**/*)               → Features entregues
```

### Passo 2: Montar Inventário de Features

Para cada arquivo encontrado em `.claude/sdd/features/`:

| Prefixo | Fase | Status |
|---------|------|--------|
| `00_BRAINSTORM_*` | Fase 0 | Exploração concluída |
| `01_DEFINE_*` | Fase 1 | Requisitos capturados |
| `02_DESIGN_*` | Fase 2 | Arquitetura projetada |

Cruzar com `reports/BUILD_REPORT_*.md` para detectar Fase 3 (construção).
Cruzar com `archive/` para detectar Fase 4 (entregue).

Para cada feature, determinar a **fase mais avançada** alcançada.

### Passo 3: Exibir Interface de Boas-Vindas

Renderizar a seguinte interface ASCII, preenchendo os dados dinâmicos. MM em block letters centrado, AGENT como subtítulo compacto, menu lateral à direita:

```text
╭─── Olá, Marco Monteiro! ─────────────────────────────────────────────────────╮
│             ███╗   ███╗ ███╗   ███╗              │ Comandos disponíveis      │
│             ████╗ ████║ ████╗ ████║              │                           │
│             ██╔████╔██║ ██╔████╔██║              │ /explorar  Explorar ideia │
│             ██║╚██╔╝██║ ██║╚██╔╝██║              │ /definir   Requisitos     │
│             ██║ ╚═╝ ██║ ██║ ╚═╝ ██║              │ /projetar  Arquitetura    │
│             ╚═╝     ╚═╝ ╚═╝     ╚═╝              │ /construir Implementar    │
│            _   ___ ___ _  _ _____                │ /entregar  Finalizar      │
│           /_\ / __| __| \| |_   _|               │                           │
│          / _ \ (_ | _|| .` | | |                 │ /iterar    Atualizar doc  │
│         /_/ \_\___|___|_|\_| |_|                 │ /review    Revisar código │
│                                                  │ /create-pr Pull request   │
│  AgentSpec v{versão} · SDD Framework · {modelo}  │ /create-kb Base de conhec.│
│  {diretório-do-projeto}                          │                           │
╰──────────────────────────────────────────────────────────────────────────────╯

  Atividade recente
  ─────────────────
  {atividade-recente}

  Entregues: {total-entregues} features no arquivo
```

**Substituições dinâmicas:**
- `{versão}` → Versão do projeto extraída do CLAUDE.md (ex: 2.1.0)
- `{modelo}` → Modelo ativo (ex: Opus 4.6)
- `{diretório-do-projeto}` → Caminho absoluto do diretório de trabalho

### Passo 4: Mostrar Atividade Recente

Logo abaixo da box, exibir:

**Se há features ativas:**

```text
  Atividade recente
  ─────────────────
  ● NOTIFICACOES_USUARIO   Fase 2 (Projeto)     → /construir 02_DESIGN_NOTIFICACOES_USUARIO.md
  ● AUTENTICACAO            Fase 0 (Exploração)  → /definir 00_BRAINSTORM_AUTENTICACAO.md

  Entregues: 3 features no arquivo
```

**Se não há features:**

```text
  Atividade recente
  ─────────────────
  Nenhuma feature ativa. Comece com /explorar "sua ideia aqui"
```

### Passo 5: Sugerir Próximo Passo

Aplicar a lógica de sugestão inteligente e perguntar ao usuário usando `AskUserQuestion`.

---

## Lógica de Sugestão Inteligente

| Condição | Sugestão |
|----------|----------|
| Nenhuma feature existe | `/explorar "sua ideia aqui"` |
| Brainstorm existe, Define não | `/definir .claude/sdd/features/00_BRAINSTORM_{X}.md` |
| Define existe, Design não | `/projetar .claude/sdd/features/01_DEFINE_{X}.md` |
| Design existe, Build não | `/construir .claude/sdd/features/02_DESIGN_{X}.md` |
| Build existe, Ship não | `/entregar {FEATURE}` |
| Tudo entregue | `/explorar "próxima ideia"` |

Quando múltiplas features estão ativas, priorizar a que está na fase mais avançada.

As opções do `AskUserQuestion` devem ser montadas dinamicamente:
- Sempre incluir "Explorar nova ideia"
- Se há features ativas, incluir o próximo passo sugerido para cada uma (máximo 3)
- Se há features ativas, incluir "Ver status detalhado"

---

## Gate de Qualidade

```text
[ ] CLAUDE.md lido para extrair versão
[ ] Glob executado para features, reports e archive
[ ] Interface ASCII renderizada corretamente
[ ] Features ativas listadas com fase atual
[ ] Sugestão inteligente aplicada
[ ] AskUserQuestion apresentado ao usuário
[ ] Toda comunicação em pt-BR
```

---

## Referências

- Contratos: `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Features: `.claude/sdd/features/`
- Reports: `.claude/sdd/reports/`
- Archive: `.claude/sdd/archive/`

# Changelog

All notable changes to AgentSpec will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.4.0] - 2026-03-04

### Added

- Nova skill `/continuar` (Fase 3+): retoma builds incompletas ou insatisfatórias com gap analysis estruturado
  - Classifica o tipo de gap (bug, feature ausente, problema de arquitetura, mudança de expectativa)
  - Confirma com o usuário antes de executar
  - Appenda ao BUILD_REPORT existente com seção "Continuação {DATA}" sem sobrescrever
  - Tabela clara distinguindo `/continuar` (código) vs `/iterar` (documentos SDD)

### Changed

- Todas as 13 skills existentes revisadas com base nas melhores práticas do skill-creator
  - Descriptions reescritas para melhor triggering (mais diretas e com frases de ativação concretas)
  - `user-invocable` corrigido para `user-invokable` em todas as skills
  - `argument-hint` corrigido de array YAML para string quoted em todas as skills
  - Paths de referência corrigidos para estrutura flat `agents/` (removidas subpastas inexistentes)
- `/agentspec:create-pr` completamente reescrito em Português-BR (headers, seções e descrição)
- `/agentspec:start` description traduzida para Português-BR
- Plugin.json: descrição atualizada para 14 skills

### Fixed

- Paths inválidos em referências de skills (`agents/workflow/`, `agents/exploration/`, `agents/code-quality/`) corrigidos para `agents/`
- Mandatos em CAPS excessivos suavizados para blockquotes explicativos em todas as skills
- README atualizado para refletir estrutura atual do projeto (skills em pt-BR, 14 skills, estrutura flat)

## [1.1.0] - 2026-02-24

### Added

- Linear Project Manager agent for issue tracking and milestone planning
- The Planner agent for strategic architecture and roadmap creation
- 12 slash commands (up from 11)
- Linear as project source of truth (60 issues, 6 milestones, 9 project documents)

### Changed

- Agent count corrected to 16: 6 workflow, 4 code-quality, 4 communication, 2 exploration
- KB domains cleaned — removed project-specific domains, kept framework scaffolding
- Agent prompts sanitized — removed all project-specific references
- `concept.md.template` section renamed from "The Pattern" to "The Concept"
- `test-case.json.template` now documents valid type values
- CLAUDE.md updated with current project status and active tasks

### Removed

- Project-specific KB domains (agentspec, projects)
- `design/agent-spec-plan-todo-list.md` (migrated to Linear)

### Fixed

- All 60 Linear issues linked to correct milestones
- Duplicate Linear documents consolidated (4 deprecated with redirects)

## [1.0.0] - 2026-02-03

### Initial Release

- Initial release of AgentSpec
- 5-phase SDD workflow (Brainstorm, Define, Design, Build, Ship)
- 16 specialized agents
  - 6 workflow agents (brainstorm, define, design, build, ship, iterate)
  - 4 code-quality agents (reviewer, cleaner, documenter, test-generator)
  - 4 communication agents (adaptive-explainer, linear-project-manager, meeting-analyst, the-planner)
  - 2 exploration agents (codebase-explorer, kb-architect)
- 12 slash commands
- Knowledge Base (KB) framework with 7 templates
- SDD document templates (5 phases)
- Workflow contracts (YAML-based phase transitions)

### Documentation

- README with quick start guide
- CONTRIBUTING guidelines
- Code of Conduct
- Agent reference documentation
- KB framework guide

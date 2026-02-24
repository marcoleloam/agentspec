# Reference

Complete catalog of commands, agents, templates, and configuration.

## Slash Commands

### Workflow Commands

| Command        | Purpose                      | Input                                  | Output                        |
|----------------|------------------------------|----------------------------------------|-------------------------------|
| `/brainstorm`  | Explore ideas (Phase 0)      | Idea description or file path          | `BRAINSTORM_{FEATURE}.md`     |
| `/define`      | Capture requirements (Phase 1)| Brainstorm file, notes, or description | `DEFINE_{FEATURE}.md`         |
| `/design`      | Create architecture (Phase 2)| DEFINE file path                       | `DESIGN_{FEATURE}.md`         |
| `/build`       | Execute implementation (Phase 3)| DESIGN file path                     | `BUILD_REPORT_{FEATURE}.md`   |
| `/ship`        | Archive completed work (Phase 4)| DEFINE file path                     | `SHIPPED_{DATE}.md`           |
| `/iterate`     | Update any phase document    | File path + change description         | Updated document + cascades   |
| `/create-pr`   | Create pull request          | Optional title, `--draft`, `--review`  | GitHub PR                     |

### Core Commands

| Command         | Purpose                          | Input                    |
|-----------------|----------------------------------|--------------------------|
| `/memory`       | Save session insights to storage | Optional context note    |
| `/sync-context` | Update CLAUDE.md from codebase   | `--section`, `--dry-run` |
| `/readme-maker` | Generate README.md               | `--output`, `--style`    |

### Knowledge Commands

| Command       | Purpose                  | Input       |
|---------------|--------------------------|-------------|
| `/create-kb`  | Create a KB domain       | Domain name |

### Review Commands

| Command    | Purpose              | Input                                         |
|------------|----------------------|-----------------------------------------------|
| `/review`  | Dual AI code review  | `uncommitted`, `committed`, `--base`, `--deep`|

## Agents (16 total)

### Workflow Agents

| Agent              | Trigger                           | Model  |
|--------------------|-----------------------------------|--------|
| brainstorm-agent   | Raw ideas, vague requirements     | Opus   |
| define-agent       | Requirements capture              | Opus   |
| design-agent       | Architecture planning             | Opus   |
| build-agent        | Implementation execution          | Sonnet |
| ship-agent         | Feature archival                  | Haiku  |
| iterate-agent      | Mid-stream changes                | Opus   |

### Code Quality Agents

| Agent            | Trigger                        | Model  |
|------------------|--------------------------------|--------|
| code-reviewer    | Code review requests           | Sonnet |
| code-cleaner     | Refactoring, DRY cleanup       | Sonnet |
| code-documenter  | README, API docs, docstrings   | Sonnet |
| test-generator   | Test writing, coverage gaps    | Sonnet |

### Communication Agents

| Agent                   | Trigger                          | Model  |
|-------------------------|----------------------------------|--------|
| adaptive-explainer      | Technical explanations           | Sonnet |
| linear-project-manager  | Linear issue/project management  | Opus   |
| meeting-analyst         | Meeting transcript analysis      | Sonnet |
| the-planner             | Strategic planning, roadmaps     | Opus   |

### Exploration Agents

| Agent              | Trigger                      | Model  |
|--------------------|------------------------------|--------|
| codebase-explorer  | Codebase navigation          | Sonnet |
| kb-architect       | KB domain creation/audit     | Sonnet |

## SDD Templates

All templates live in `.claude/sdd/templates/`:

| Template                     | Phase     | Purpose                          |
|------------------------------|-----------|----------------------------------|
| `BRAINSTORM_TEMPLATE.md`     | Phase 0   | Idea exploration structure       |
| `DEFINE_TEMPLATE.md`         | Phase 1   | Requirements with clarity score  |
| `DESIGN_TEMPLATE.md`         | Phase 2   | Architecture with file manifest  |
| `BUILD_REPORT_TEMPLATE.md`   | Phase 3   | Execution report with agent attribution |
| `SHIPPED_TEMPLATE.md`        | Phase 4   | Archive with lessons learned     |

## KB Templates

All templates live in `.claude/kb/_templates/`:

| Template                        | Purpose                              |
|---------------------------------|--------------------------------------|
| `index.md.template`             | Domain overview and navigation       |
| `quick-reference.md.template`   | Cheat sheet (max 100 lines)          |
| `concept.md.template`           | Core concept explanation (max 150)   |
| `pattern.md.template`           | Implementation pattern (max 200)     |
| `domain-manifest.yaml.template` | Domain metadata and file registry    |
| `spec.yaml.template`            | Machine-readable specifications      |
| `test-case.json.template`       | Validation test cases                |

## Configuration

### Workflow Contracts

Phase transition rules are defined in `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml`:

- Phase inputs, outputs, and quality gates
- Model allocation per phase (Opus/Sonnet/Haiku)
- Naming conventions (`SCREAMING_SNAKE_CASE`)
- Cascade rules for `/iterate`
- Status transition logic

### Settings

Project settings in `.claude/settings.local.json`:

- `permissions` — tool access control
- `outputStyle` — response formatting (e.g., "Explanatory")

## File Naming Conventions

| Artifact                | Pattern                            | Location                    |
|-------------------------|------------------------------------|-----------------------------|
| Brainstorm document     | `BRAINSTORM_{FEATURE}.md`          | `.claude/sdd/features/`     |
| Requirements document   | `DEFINE_{FEATURE}.md`              | `.claude/sdd/features/`     |
| Design document         | `DESIGN_{FEATURE}.md`              | `.claude/sdd/features/`     |
| Build report            | `BUILD_REPORT_{FEATURE}.md`        | `.claude/sdd/reports/`      |
| Shipped archive         | `SHIPPED_{YYYY-MM-DD}.md`          | `.claude/sdd/archive/{FEATURE}/` |

Feature names use `SCREAMING_SNAKE_CASE` (e.g., `USER_AUTH`, `JUDGE_LAYER`).

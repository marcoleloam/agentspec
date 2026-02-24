<div align="center">

# AgentSpec

## Spec-Driven Development for Claude Code

Turn ideas into shipped features through a structured 5-phase AI workflow

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-purple.svg)](https://docs.anthropic.com/en/docs/claude-code)
[![Version](https://img.shields.io/badge/version-1.1.0-green.svg)](CHANGELOG.md)

[Quick Start](#quick-start) | [Documentation](docs/) | [Contributing](CONTRIBUTING.md)

</div>

---

## The Problem

AI-assisted development without structure leads to lost decisions, spec drift, and repeated mistakes. You discuss requirements in one session, forget them in the next, and end up with code that doesn't match what was agreed.

## The Solution

AgentSpec brings **Spec-Driven Development (SDD)** to Claude Code — a 5-phase workflow where every decision is captured, every design is traceable, and every lesson is preserved:

```text
/brainstorm  →  /define  →  /design  →  /build  →  /ship
  (Explore)    (Capture)   (Architect)  (Execute)  (Archive)
```

Each phase produces a document. Each transition has a quality gate. Nothing gets lost.

---

## Quick Start

### Install

```bash
# Clone AgentSpec
git clone https://github.com/luanmorenommaciel/agentspec.git

# Copy the framework into your project
cp -r agentspec/.claude your-project/.claude
```

### Build Your First Feature

```bash
# 1. Explore the idea
claude> /brainstorm "Add user authentication with JWT"

# 2. Capture requirements (must score 12/15 to proceed)
claude> /define USER_AUTH

# 3. Design the architecture (agents auto-matched to tasks)
claude> /design USER_AUTH

# 4. Build with verification
claude> /build USER_AUTH

# 5. Archive with lessons learned
claude> /ship USER_AUTH
```

That's it. Five commands, full traceability from idea to production.

---

## What You Get

### 5-Phase Workflow with Quality Gates

| Phase          | Command       | What It Does                  | Quality Gate                  |
|----------------|---------------|-------------------------------|-------------------------------|
| **Brainstorm** | `/brainstorm` | Explore approaches, compare   | 3+ questions, 2+ approaches   |
| **Define**     | `/define`     | Capture requirements formally | Clarity Score >= 12/15        |
| **Design**     | `/design`     | Architecture, manifest, ADRs  | Complete manifest             |
| **Build**      | `/build`      | Execute with agent delegation | All tests pass                |
| **Ship**       | `/ship`       | Archive with lessons learned  | Acceptance verified           |

### 16 Specialized Agents

| Category          | Count | Examples                                        |
|-------------------|-------|-------------------------------------------------|
| **Workflow**      | 6     | brainstorm, define, design, build, ship, iterate|
| **Code Quality**  | 4     | code-reviewer, test-generator, code-cleaner     |
| **Communication** | 4     | adaptive-explainer, linear-pm, meeting-analyst  |
| **Exploration**   | 2     | codebase-explorer, kb-architect                 |

During `/build`, agents are automatically matched to tasks based on your DESIGN document.

### Knowledge Base Framework

Ground AI responses in verified patterns instead of hallucinated ones:

```bash
# Create a domain-specific KB
claude> /create-kb fastapi

# Agents will consult it during /design and /build
```

### 12 Slash Commands

Beyond the 5 workflow phases: `/iterate` (update docs when requirements change), `/review` (dual AI code review), `/create-pr`, `/create-kb`, `/memory`, `/sync-context`, `/readme-maker`.

---

## How It Works

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  BRAINSTORM  │────▶│    DEFINE    │────▶│    DESIGN    │
│  (Optional)  │     │ Requirements │     │ Architecture │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     SHIP     │◀────│    BUILD     │◀────│    Agent     │
│   Archive    │     │   Execute    │     │   Matching   │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Agent matching example:** Your DESIGN doc mentions "Pydantic models" and "pytest" — AgentSpec automatically delegates to `test-generator` for tests and `code-reviewer` for quality checks.

**Requirements changed?** Use `/iterate` to update any phase document with automatic cascade detection to downstream docs.

---

## Project Structure

```text
.claude/
├── agents/              # 16 specialized agents
│   ├── workflow/        # 6 SDD phase agents
│   ├── code-quality/    # 4 code excellence agents
│   ├── communication/   # 4 communication agents
│   └── exploration/     # 2 codebase agents
│
├── commands/            # 12 slash commands
│   ├── workflow/        # /brainstorm, /define, /design, /build, /ship, /iterate, /create-pr
│   ├── core/            # /memory, /sync-context, /readme-maker
│   ├── knowledge/       # /create-kb
│   └── review/          # /review
│
├── sdd/                 # SDD framework
│   ├── architecture/    # WORKFLOW_CONTRACTS.yaml, ARCHITECTURE.md
│   ├── templates/       # 5 phase document templates
│   ├── features/        # Active feature documents
│   ├── reports/         # Build reports
│   └── archive/         # Shipped features
│
├── kb/                  # Knowledge Base
│   ├── _templates/      # 7 KB templates
│   └── _index.yaml      # Domain registry
│
└── docs/                # Documentation
```

---

## Documentation

| Guide                                        | Description                                  |
|----------------------------------------------|----------------------------------------------|
| [Getting Started](docs/getting-started/)     | Install and build your first feature         |
| [Core Concepts](docs/concepts/)              | How phases, agents, and KB work together     |
| [Tutorials](docs/tutorials/)                 | Step-by-step workflow walkthroughs           |
| [Reference](docs/reference/)                 | Full command, agent, and template catalog    |

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- **New Agents** — add specialized agents for your domain
- **KB Domains** — share knowledge base domains
- **Bug Fixes** — help improve stability
- **Documentation** — clarify and expand docs

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**[Documentation](docs/) | [Contributing](CONTRIBUTING.md) | [Changelog](CHANGELOG.md)**

Built with [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

</div>

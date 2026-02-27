# Contributing to AgentSpec

Thank you for your interest in AgentSpec! This guide will help you contribute effectively.

## Quick Start

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/agentspec.git
cd agentspec
git checkout -b feature/your-feature

# The framework lives in .claude/
ls .claude/agents/      # 16 specialized agents
ls .claude/skills/      # 12 slash commands (skills)
ls .claude/sdd/         # SDD framework
ls .claude/kb/          # Knowledge Base
```

## Ways to Contribute

| Type           | Where                          | Guide                                    |
|----------------|--------------------------------|------------------------------------------|
| New Agent      | `.claude/agents/{category}/`   | [Adding Agents](#adding-a-new-agent)     |
| New KB Domain  | `.claude/kb/{domain}/`         | [Adding KB Domains](#adding-a-kb-domain) |
| New Skill      | `.claude/skills/{category}/`   | [Adding Skills](#adding-a-skill)         |
| Bug Fix        | Any file                       | [Bug Fixes](#bug-fixes)                  |
| Documentation  | `docs/`                        | [Docs Guide](#documentation)             |

## Adding a New Agent

1. Copy the template:

   ```bash
   cp .claude/agents/_template.md .claude/agents/{category}/your-agent.md
   ```

2. Fill in the required sections:
   - **Identity block** — name, domain, trigger threshold
   - **Capabilities** — what the agent does (2-8 capabilities)
   - **Quality gate** — pre-flight checklist
   - **Response format** — expected output structure
   - **Anti-patterns** — what to avoid

3. Choose the right category:
   - `workflow/` — SDD phase agents
   - `code-quality/` — code review, testing, cleaning, documentation
   - `communication/` — explanation, planning, analysis
   - `exploration/` — codebase navigation, KB management

4. Test with Claude Code:

   ```bash
   # Verify agent is discoverable
   claude> "What agents are available?"
   ```

## Adding a KB Domain

Use the built-in command:

```bash
claude> /create-kb redis
```

Or create manually:

```text
.claude/kb/your-domain/
├── index.md              # Domain overview
├── quick-reference.md    # Cheat sheet (max 100 lines)
├── concepts/             # Core concepts (max 150 lines each)
│   └── your-concept.md
└── patterns/             # Implementation patterns (max 200 lines each)
    └── your-pattern.md
```

Templates are in `.claude/kb/_templates/`. Register your domain in `.claude/kb/_index.yaml`.

## Adding a Skill

1. Create `.claude/skills/{category}/your-skill/SKILL.md`
2. Include YAML frontmatter:

   ```yaml
   ---
   name: your-skill
   description: What this skill does
   user-invocable: true
   agent: agent-name (optional)
   allowed-tools: Read, Write, Grep, Glob
   ---
   ```

3. Reference the appropriate agent if applicable
4. Test: `claude> /your-skill`

## Bug Fixes

1. Check [existing issues](https://github.com/luanmorenommaciel/agentspec/issues)
2. Create a branch: `git checkout -b fix/description`
3. Make your fix
4. Submit a PR with a clear description of the problem and solution

## Documentation

- Keep markdown files ATX-style (`#`, `##`, `###`)
- Use fenced code blocks with language identifiers
- Keep tables properly aligned
- Test all links before submitting

## Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make changes following the style guidelines above
4. Test with Claude Code to ensure commands and agents work
5. Submit a PR with:
   - Clear title (e.g., "Add redis KB domain" or "Fix brainstorm agent quality gate")
   - Description of what changed and why
   - Link to related issue if applicable

## Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/). Be respectful, constructive, and inclusive.

## Questions?

- [Open an issue](https://github.com/luanmorenommaciel/agentspec/issues)
- [Start a discussion](https://github.com/luanmorenommaciel/agentspec/discussions)

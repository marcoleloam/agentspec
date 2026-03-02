# Contributing to AgentSpec

Thank you for your interest in AgentSpec! This guide will help you contribute effectively.

## Quick Start

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/agentspec.git
cd agentspec

# The framework structure
ls agents/      # 16 specialized agents
ls skills/      # 13 slash commands (skills)
ls sdd/         # SDD framework
ls kb/          # Knowledge Base
```

## Ways to Contribute

| Type           | Where                    | Guide                                    |
|----------------|--------------------------|------------------------------------------|
| New Agent      | `agents/`                | [Adding Agents](#adding-a-new-agent)     |
| New KB Domain  | `kb/{domain}/`           | [Adding KB Domains](#adding-a-kb-domain) |
| New Skill      | `skills/{name}/`         | [Adding Skills](#adding-a-skill)         |
| Bug Fix        | Any file                 | [Bug Fixes](#bug-fixes)                  |
| Documentation  | `docs/`                  | [Docs Guide](#documentation)             |

## Adding a New Agent

1. Create a new agent file in `agents/`:

   ```bash
   # Use an existing agent as reference (e.g., brainstorm-agent.md)
   cp agents/brainstorm-agent.md agents/your-agent.md
   ```

2. Fill in the required sections:
   - **Frontmatter** — name, description with examples, tools, kb_domains
   - **Identity block** — name, domain, trigger threshold
   - **Capabilities** — what the agent does (2-8 capabilities)
   - **Quality gate** — pre-flight checklist
   - **Response format** — expected output structure
   - **Anti-patterns** — what to avoid

3. Test with Claude Code:

   ```bash
   # Verify agent is discoverable
   claude> "What agents are available?"
   ```

## Adding a KB Domain

Use the built-in command:

```bash
claude> /agentspec:create-kb redis
```

Or create manually:

```text
kb/your-domain/
├── index.md              # Domain overview
├── quick-reference.md    # Cheat sheet (max 100 lines)
├── concepts/             # Core concepts (max 150 lines each)
│   └── your-concept.md
└── patterns/             # Implementation patterns (max 200 lines each)
    └── your-pattern.md
```

Templates are in `kb/_templates/`. Register your domain in `kb/_index.yaml`.

## Adding a Skill

1. Create `skills/your-skill/SKILL.md`
2. Include YAML frontmatter:

   ```yaml
   ---
   name: your-skill
   description: What this skill does
   user-invokable: true
   ---
   ```

3. Write the skill instructions in markdown
4. Test: `claude> /agentspec:your-skill`

## Bug Fixes

1. Check [existing issues](https://github.com/marcoleloam/agentspec/issues)
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
4. Test with Claude Code to ensure skills and agents work
5. Submit a PR with:
   - Clear title (e.g., "Add redis KB domain" or "Fix brainstorm agent quality gate")
   - Description of what changed and why
   - Link to related issue if applicable

## Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/). Be respectful, constructive, and inclusive.

## Questions?

- [Open an issue](https://github.com/marcoleloam/agentspec/issues)
- [Start a discussion](https://github.com/marcoleloam/agentspec/discussions)

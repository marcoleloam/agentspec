# Tutorials

Step-by-step walkthroughs for common AgentSpec workflows.

## Available Tutorials

### Workflow Basics

| Tutorial                                      | Time   | Level        |
|-----------------------------------------------|--------|--------------|
| [Your First Feature](../getting-started/)     | 10 min | Beginner     |
| Using `/iterate` When Requirements Change     | 5 min  | Intermediate |
| Building with Agent Delegation                | 15 min | Intermediate |
| Creating a Knowledge Base Domain              | 10 min | Intermediate |

### Common Workflows

#### Quick Feature with `/define` + `/build`

Skip brainstorm when requirements are already clear:

```bash
# Start directly with requirements
claude> /define "Add pagination to the API endpoints"

# Review the DEFINE document, then design
claude> /design PAGINATION

# Build it
claude> /build PAGINATION

# Ship when done
claude> /ship PAGINATION
```

#### Updating Requirements Mid-Stream

When a stakeholder changes scope after you've started design:

```bash
# Update the DEFINE document with cascade detection
claude> /iterate .claude/sdd/features/DEFINE_PAGINATION.md "Add cursor-based pagination support"
```

The iterate-agent detects which downstream documents (DESIGN, BUILD_REPORT) need updates and guides you through each cascade.

#### Creating a KB Domain

Ground your agents in domain-specific knowledge:

```bash
# Create a new KB domain
claude> /create-kb fastapi

# The kb-architect agent will:
# 1. Research the domain via MCP tools
# 2. Create concepts/ and patterns/ files
# 3. Register the domain in _index.yaml
# 4. Score the domain (target: 80+/100)
```

### Code Quality Workflows

#### Code Review with Dual AI

```bash
# Review uncommitted changes
claude> /review

# Review against a specific branch
claude> /review --base main

# Quick review (Claude only, no CodeRabbit)
claude> /review --quick
```

#### Generate a README

```bash
# Auto-generate from codebase analysis
claude> /readme-maker
```

## What's Next

- [Core Concepts](../concepts/) — understand the mental model
- [Reference](../reference/) — full command and agent catalog

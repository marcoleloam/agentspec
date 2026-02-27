---
name: create-pr
description: Create pull request with conventional commits and structured descriptions
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash, AskUserQuestion
argument-hint: ["título-opcional"]
---

# Create PR Command

> Automate professional pull request creation with conventional commits and structured descriptions

## Idioma

**OBRIGATÓRIO:** Toda comunicação com o usuário e documentos gerados DEVEM ser em **Português-BR (pt-BR)**.

---

## Usage

```bash
/create-pr                           # Auto-detect changes and create PR
/create-pr "feat: add user auth"     # Create PR with custom title
/create-pr --draft                   # Create as draft PR
/create-pr --review                  # Run dual AI review before PR creation
```

---

## Pre-PR Review Option

When using `--review`, the command runs a **dual AI review** (CodeRabbit + Claude) before creating the PR. Critical issues block PR creation.

---

## Process

### Step 1: Analyze Changes

```bash
git status
git diff --stat
git log origin/main..HEAD --oneline
```

### Step 2: Determine PR Type

| Files Changed | Likely Type |
|---------------|-------------|
| `src/**/*.py` + new functionality | `feat:` |
| `src/**/*.py` + bug fix | `fix:` |
| `*.md`, `docs/**` | `docs:` |
| `tests/**` | `test:` |
| `.claude/agents/**` | `refactor(agents):` |
| `.claude/kb/**` | `docs(kb):` |
| `.claude/sdd/**` | `docs(sdd):` |

### Step 3: Generate Commit Message

Conventional Commits format with `Co-Authored-By: Claude <noreply@anthropic.com>`.

### Step 4: Ask Clarifying Questions

Confirm PR type, scope, breaking changes, and related issues.

### Step 5: Build PR Description

Structured description with Summary, Key Changes, Files Changed, Test Plan, Breaking Changes.

### Step 6: Create Branch, Commit, Push, and Create PR

```bash
gh pr create --title "<type>(<scope>): <description>" --body "<generated-body>" --base main
```

---

## Output

- **Branch:** `<type>/<short-description>`
- **Commit:** Conventional commit format
- **PR URL:** Returned from `gh pr create`

---

## Conventional Commits Reference

| Type | When to Use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructure |
| `docs` | Documentation |
| `test` | Tests |
| `chore` | Maintenance |

---

## Related

- Review Skill: `.claude/skills/workflow/review/SKILL.md`
- Code Reviewer Agent: `.claude/agents/code-quality/code-reviewer.md`

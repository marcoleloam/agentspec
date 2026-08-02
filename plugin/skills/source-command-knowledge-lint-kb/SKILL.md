---
name: "source-command-knowledge-lint-kb"
description: "Audit KB domain quality — stale content, contradictions, gaps"
---

# source-command-knowledge-lint-kb

Use this skill when the user asks to run the migrated source command `knowledge-lint-kb`.

## Command Template

# Lint KB Command

> Audita a qualidade de um ou todos os KB domains.

## Usage

```
/lint-kb <DOMAIN>
/lint-kb --all
```

**Examples**: `/lint-kb dbt`, `/lint-kb spark`, `/lint-kb --all`

## What Happens

### Single Domain

1. **Reads domain files** -- all concepts, patterns, index, quick-reference
2. **Invokes kb-evolution-agent** -- executes lint workflow
3. **Checks 4 issue categories** -- stale, contradictions, gaps, format
4. **Generates report** -- saved to `.claude/sdd/reports/LINT_KB_{DOMAIN}_{DATE}.md`
5. **Updates `_index.yaml`** -- sets `last_lint` date
6. **Updates `log.md`** -- appends lint entry to domain log

### All Domains (--all)

1. **Iterates all domains** from `_index.yaml`
2. **Runs lint for each** -- same checks as single domain
3. **Generates consolidated report** -- `.claude/sdd/reports/LINT_KB_ALL_{DATE}.md`
4. **Ranks by severity** -- domains with most/critical issues first

## Issue Categories

| Category | Severity | Description |
|----------|----------|-------------|
| Stale Content | HIGH | APIs deprecated, syntax changed, versions outdated |
| Contradictions | HIGH | Conflicting info between files in same domain |
| Gaps | MEDIUM | Topics missing that official docs cover |
| Format Issues | LOW | Line limits exceeded, missing headers, broken links |

## See Also

- **Agent**: `${CLAUDE_PLUGIN_ROOT}/agents/dev/kb-evolution-agent.md`
- **Ingest**: `/ingest-kb` for updating content via Context7
- **Create**: `/create-kb` for new domains from scratch
- **Registry**: `${CLAUDE_PLUGIN_ROOT}/kb/_index.yaml`

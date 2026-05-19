---
name: ingest-kb
description: Update a KB domain with latest docs from Context7 MCP
---

# Ingest KB Command

> Atualiza um KB domain com documentacao oficial mais recente via Context7.

## Usage

```
/ingest-kb <DOMAIN>
```

**Examples**: `/ingest-kb dbt`, `/ingest-kb react`, `/ingest-kb airflow`

## What Happens

1. **Validates domain** -- checks domain exists in `_index.yaml`
2. **Resolves Context7 library** -- calls `resolve-library-id` for the domain
3. **Invokes kb-evolution-agent** -- executes full ingest workflow:
   - Queries Context7 for each topic in the domain
   - Compares semantically with current KB content
   - Rewrites only files with detected changes (preserving format)
4. **Updates tracking** -- `mcp_validated` in `_index.yaml`, entry in `log.md`
5. **Reports completion** -- shows files updated, files unchanged, log entry location

## Token Cost

Estimated ~30K tokens per domain (when <50% of files changed). Full rewrite ~50K tokens.

## Fallback

If Context7 has no coverage for the domain, the command:
- Notifies the user with a clear message
- Suggests alternatives: `/lint-kb <domain>` for auditing, or manual update
- Logs the attempt in `log.md` as "skipped - no Context7 coverage"
- Does NOT modify any existing KB files

## See Also

- **Agent**: `${CLAUDE_PLUGIN_ROOT}/agents/dev/kb-evolution-agent.md`
- **Lint**: `/lint-kb` for quality auditing
- **Create**: `/create-kb` for new domains from scratch
- **Registry**: `${CLAUDE_PLUGIN_ROOT}/kb/_index.yaml`

# Prompt Management

> **Purpose**: Version control, deployment, and iteration on prompts
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Prompt management centralizes prompts outside application code. Each prompt has versions (immutable history) and labels (pointers to versions). The `production` label marks the active version fetched by default. This enables prompt iteration, A/B testing, and instant rollbacks without code deployments.

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

# Fetch production prompt (default)
prompt = langfuse.get_prompt("extract_data")

# Fetch specific version or label
prompt_v2 = langfuse.get_prompt("extract_data", version=2)
prompt_staging = langfuse.get_prompt("extract_data", label="staging")

# Compile with variables
compiled = prompt.compile(
    request_type="standard",
    required_fields=["field_a", "field_b", "field_c"]
)

# Use in generation with prompt linking
with langfuse.start_as_current_observation(
    as_type="generation",
    name="llm-processing",
    model="your-model-name",
    input=compiled
) as generation:

    # Link prompt for analytics
    generation.update(
        prompt=prompt,  # Links version to trace
        output=result
    )
```

## Quick Reference

| Concept | Description | Example |
|---------|-------------|---------|
| Version | Immutable snapshot | v1, v2, v3... |
| Label | Pointer to version | `production`, `staging` |
| Variable | Template placeholder | `{{request_type}}` |
| Compile | Render with values | `.compile(key=value)` |

## Prompt Template Syntax

```text
You are a data extraction assistant.
Extract fields from {{request_type}} requests.

Required fields: {{required_fields}}

Return JSON format:
{
  "field_a": "string",
  "field_b": "float",
  "field_c": "date"
}
```

## Common Mistakes

### Wrong

```python
# Hardcoded prompt - no versioning, no analytics
prompt = "Extract data fields: field_a, field_b, field_c"
```

### Correct

```python
# Managed prompt - versioned, tracked, updatable
prompt = langfuse.get_prompt("extract_data")
compiled = prompt.compile(
    request_type="standard",
    required_fields=["field_a", "field_b", "field_c"]
)
```

## Deployment Workflow

| Step | Action | Environment |
|------|--------|-------------|
| 1. Create | New version auto-labeled `latest` | Development |
| 2. Test | Fetch by version number | Staging |
| 3. Deploy | Add `production` label | Production |
| 4. Rollback | Move `production` to prior version | Recovery |

## Caching Behavior

| Setting | Default | Description |
|---------|---------|-------------|
| Server cache | Enabled | Reduces API calls |
| Client cache | TTL-based | Local prompt cache |
| Force refresh | `cache=False` | Bypass all caching |

## Protected Labels

| Role | Can Modify Protected |
|------|---------------------|
| Viewer | No |
| Member | No |
| Admin | Yes |
| Owner | Yes |

## Related

- [Python SDK Integration](../patterns/python-sdk-integration.md)
- [Model Comparison](../concepts/model-comparison.md)
- [Quality Feedback Loops](../patterns/quality-feedback-loops.md)

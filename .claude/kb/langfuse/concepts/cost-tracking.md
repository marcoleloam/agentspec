# Cost Tracking

> **Purpose**: Track and calculate LLM usage costs with usage_details and cost_details
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

Langfuse tracks costs on generation and embedding observations using a two-tier approach. First priority: ingested costs provided directly via SDK. Second priority: inferred costs calculated from token counts and model pricing definitions. Costs can be broken down by user, session, model, prompt version, and feature.

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="generation",
    name="summarize",
    model="gpt-4o"
) as gen:
    gen.update(
        input="Summarize this document...",
        output="The document covers...",
        usage_details={
            "input": 1500,
            "output": 200,
            "total": 1700
        },
        cost_details={
            "input": 0.00375,
            "output": 0.002,
            "total": 0.00575
        }
    )

langfuse.flush()
```

## Cost Calculation Priority

| Priority | Method | When Used |
|----------|--------|-----------|
| 1 (highest) | `cost_details` ingested via SDK | You provide explicit costs |
| 2 | Inferred from `usage_details` + model pricing | Costs not provided, tokens available |
| 3 | Inferred via tokenizer + model pricing | Neither costs nor tokens provided |

## usage_details Fields

| Field | Type | Description |
|-------|------|-------------|
| `input` | int | Input/prompt token count |
| `output` | int | Output/completion token count |
| `total` | int | Total tokens (auto-summed if omitted) |
| `cached_tokens` | int | Tokens served from provider cache |
| `cache_read_input_tokens` | int | Anthropic-style cached reads |
| `reasoning_tokens` | int | Chain-of-thought tokens (o1, etc.) |

## cost_details Fields

| Field | Type | Description |
|-------|------|-------------|
| `input` | float | Input cost in USD |
| `output` | float | Output cost in USD |
| `total` | float | Total cost in USD (auto-summed if omitted) |
| `cache_read_input_tokens` | float | Cost for cached token reads |

## OpenAI Automatic Mapping

Langfuse auto-maps OpenAI usage fields:

| OpenAI Field | Langfuse Field |
|--------------|----------------|
| `prompt_tokens` | `usage_details.input` |
| `completion_tokens` | `usage_details.output` |
| `total_tokens` | `usage_details.total` |

## Custom Model Definitions

Define custom models in **Project Settings > Models** for automatic cost inference:

| Setting | Description |
|---------|-------------|
| Model name regex | Pattern matching model identifiers |
| Tokenizer | `cl100k_base`, `o200k_base`, `claude` |
| Input price/token | Cost per input token in USD |
| Output price/token | Cost per output token in USD |

User-defined models take priority over Langfuse built-in definitions.

## Pricing Tiers

For models with context-dependent pricing (e.g., Claude large context):

| Tier Property | Description |
|---------------|-------------|
| `priority` | Evaluation order (lower = first) |
| `regex` | Pattern matching usage detail keys |
| `comparison` | `gt`, `gte`, `lt`, `lte`, `eq`, `neq` |
| `threshold` | Token count threshold |

## Common Mistakes

### Wrong

```python
# Relying solely on inference for unsupported models
gen.update(model="custom-model-v2")
# No usage or cost provided, model not in definitions = no cost data
```

### Correct

```python
# Always provide at minimum usage_details for custom models
gen.update(
    model="custom-model-v2",
    usage_details={"input": 500, "output": 100},
    cost_details={"input": 0.001, "output": 0.002, "total": 0.003}
)
```

## Related

- [Generations](../concepts/generations.md)
- [Cost Alerting](../patterns/cost-alerting.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)

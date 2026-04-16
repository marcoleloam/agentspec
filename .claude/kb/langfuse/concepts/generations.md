# Generations

> **Purpose**: Track LLM calls with model info, token usage, cost, and prompt/completion pairs
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

A generation is a specialized observation type in Langfuse designed for LLM calls. It extends the basic span with fields for model name, model parameters, token usage (usage_details), and cost (cost_details). Generations are the primary unit for cost tracking, latency measurement, and quality scoring of LLM interactions.

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="generation",
    name="extract-invoice",
    model="gemini-2.0-flash"
) as generation:
    generation.update(
        input=[
            {"role": "system", "content": "Extract invoice fields as JSON."},
            {"role": "user", "content": "Invoice #1234 from Acme Corp..."}
        ],
        output={"vendor": "Acme Corp", "total": 1500.00},
        model_parameters={"temperature": 0.0, "max_tokens": 1024},
        usage_details={"input": 320, "output": 85, "total": 405},
        cost_details={"input": 0.00016, "output": 0.000085, "total": 0.000245}
    )

langfuse.flush()
```

## Generation-Specific Fields

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Model identifier (e.g., "gemini-2.0-flash") |
| `model_parameters` | dict | Temperature, max_tokens, top_p, etc. |
| `usage_details` | dict | Token counts by type (input, output, total) |
| `cost_details` | dict | Cost in USD by type (input, output, total) |
| `input` | any | Prompt sent to the model |
| `output` | any | Model response / completion |
| `metadata` | dict | Arbitrary key-value metadata |

## Using the Decorator

```python
from langfuse import observe

@observe(as_type="generation")
def call_llm(prompt: str, model: str = "gemini-2.0-flash"):
    """Decorator automatically captures input/output and timing."""
    # Your LLM call logic here
    response = my_llm_client.generate(prompt, model=model)
    return response.text
```

## Quick Reference

| Scenario | as_type | Why |
|----------|---------|-----|
| LLM text generation | `"generation"` | Tracks tokens, cost, model |
| Embedding call | `"embedding"` | Tracks embedding token usage |
| Non-LLM processing | `"span"` | No token/cost fields needed |
| Tool/function call | `"tool"` | Semantic clarity |

## Usage Details Keys

| Key | Description |
|-----|-------------|
| `input` | Input/prompt tokens |
| `output` | Output/completion tokens |
| `total` | Total tokens (auto-summed if omitted) |
| `cached_tokens` | Tokens served from cache |
| `reasoning_tokens` | Tokens used for chain-of-thought |
| `audio_tokens` | Tokens for audio modalities |
| `image_tokens` | Tokens for image modalities |

## Common Mistakes

### Wrong

```python
# Using span for LLM calls - loses token/cost tracking
@observe(as_type="span")
def call_llm(prompt):
    return llm.generate(prompt)
```

### Correct

```python
# Use generation for LLM calls to get full observability
@observe(as_type="generation")
def call_llm(prompt):
    return llm.generate(prompt)
```

## Related

- [Traces and Spans](../concepts/traces-spans.md)
- [Cost Tracking](../concepts/cost-tracking.md)
- [Python SDK Integration](../patterns/python-sdk-integration.md)

# Model Comparison

> **Purpose**: Compare LLM models and prompt versions using Langfuse metrics
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

Langfuse enables A/B testing of LLM models and prompt versions by collecting structured metrics across traces. By tagging generations with model names and linking prompts to traces, you can compare cost, latency, token usage, and quality scores across different configurations. Dashboards and the metrics API provide breakdowns by model, prompt version, user, and custom tags.

## The Pattern

```python
from langfuse import get_client, observe

langfuse = get_client()

@observe(as_type="generation")
def extract_with_model(text: str, model: str):
    """Run extraction with a specific model for comparison."""
    prompt = langfuse.get_prompt("invoice-extractor")
    compiled = prompt.compile(invoice_text=text)

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="model-comparison",
        model=model,
        langfuse_prompt=prompt
    ) as gen:
        result = call_llm(compiled, model=model)
        gen.update(
            output=result,
            usage_details={"input": 500, "output": 120},
            metadata={"experiment": "model-comparison-v1"}
        )

        # Score the result for comparison
        gen.score(
            name="extraction_accuracy",
            value=evaluate_result(result),
            data_type="NUMERIC"
        )
    return result

# Run comparison
for model in ["gemini-2.0-flash", "gpt-4o-mini", "claude-sonnet-4-20250514"]:
    extract_with_model(invoice_text, model=model)

langfuse.flush()
```

## Comparison Dimensions

| Dimension | How to Measure | Source |
|-----------|---------------|--------|
| **Cost** | `cost_details.total` per generation | Automatic from model pricing |
| **Latency** | Observation duration (start to end) | Automatic timing |
| **Token Usage** | `usage_details.input` + `output` | Ingested or inferred |
| **Quality** | Scores attached to generations | Manual or automated scoring |
| **Throughput** | Traces per time window | Dashboard metrics |

## Tagging for Comparison

```python
from langfuse import propagate_attributes

@observe()
def run_experiment(model: str, prompt_version: str):
    with propagate_attributes(
        tags=["experiment", f"model:{model}", f"prompt:{prompt_version}"],
        metadata={
            "experiment_id": "exp-2026-02",
            "model": model,
            "prompt_version": prompt_version
        }
    ):
        return process_pipeline(model, prompt_version)
```

## Prompt Version Comparison

| Step | How |
|------|-----|
| 1. Create prompt versions | `create_prompt()` with same name (auto-versions) |
| 2. Label for routing | Label "production" vs "staging" |
| 3. Link to generations | Pass `langfuse_prompt=prompt` |
| 4. Score results | Attach quality scores to each generation |
| 5. Analyze in dashboard | Filter by prompt version in Langfuse UI |

## Dashboard Filters for Comparison

| Filter | Purpose |
|--------|---------|
| Model name | Compare models side by side |
| Prompt version | Compare prompt iterations |
| Tags | Filter by experiment group |
| Date range | Time-bounded comparison |
| User ID | Per-user performance |
| Environment | Production vs staging |

## Metrics API

```python
# Export metrics programmatically for custom analysis
# Use Langfuse API or integrate with PostHog/Mixpanel
# Metrics available: cost, latency, token usage, scores
# Breakdowns: by model, prompt version, user, tags
```

## Common Mistakes

### Wrong

```python
# No tagging or scoring - cannot compare later
@observe(as_type="generation")
def call_llm(prompt):
    return llm.generate(prompt)
```

### Correct

```python
# Tag with model, score results, link prompt version
@observe(as_type="generation")
def call_llm(prompt, model):
    with langfuse.start_as_current_observation(
        as_type="generation", name="compare", model=model
    ) as gen:
        result = llm.generate(prompt, model=model)
        gen.score(name="quality", value=0.9, data_type="NUMERIC")
    return result
```

## Related

- [Scoring](../concepts/scoring.md)
- [Prompt Management](../concepts/prompt-management.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)

# Model Comparison

> **Purpose**: A/B testing and analytics for comparing LLM models
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Langfuse enables model comparison by tracking metrics across different models, prompt versions, and configurations. Compare cost, latency, quality scores, and token usage to make data-driven decisions about model selection and prompt optimization.

## The Pattern

```python
from langfuse import get_client
import random

langfuse = get_client()

# A/B test between models
models = [
    {"name": "your-model-name", "weight": 0.5},
    {"name": "your-model-name", "weight": 0.5}
]

def select_model():
    r = random.random()
    cumulative = 0
    for model in models:
        cumulative += model["weight"]
        if r <= cumulative:
            return model["name"]
    return models[-1]["name"]

# Track with model metadata
selected_model = select_model()

with langfuse.start_as_current_observation(
    as_type="generation",
    name="llm-processing",
    model=selected_model,
    metadata={
        "experiment": "model-comparison-v1",
        "variant": selected_model
    }
) as generation:

    result = call_llm(model=selected_model)

    generation.update(
        output=result,
        usage_details={"input": 500, "output": 100}
    )

    # Score for comparison
    generation.score(
        name="output_accuracy",
        value=evaluate_accuracy(result),
        data_type="NUMERIC"
    )
```

## Quick Reference

| Metric | Compare By | Decision Factor |
|--------|------------|-----------------|
| Cost | Per request, per token | Budget constraints |
| Latency | P50, P95, P99 | User experience |
| Quality | Score averages | Accuracy requirements |
| Throughput | Requests/sec | Scale requirements |

## Comparison Dimensions

| Dimension | Filter/Group | Use Case |
|-----------|--------------|----------|
| `model` | Model name | Model A vs B |
| `prompt.version` | Prompt version | Prompt iteration |
| `metadata.experiment` | Custom tag | A/B experiments |
| `metadata.variant` | Custom tag | Feature flags |

## Common Mistakes

### Wrong

```python
# No experiment tracking - hard to compare later
with langfuse.start_as_current_observation(
    as_type="generation",
    model="your-model-name"
) as gen:
    pass
```

### Correct

```python
# Tag for experiment analysis
with langfuse.start_as_current_observation(
    as_type="generation",
    model="your-model-name",
    metadata={
        "experiment": "model-comparison-test",
        "variant": "pro"
    }
) as gen:
    gen.score(name="accuracy", value=0.95)
```

## Model Comparison Example

| Model | Cost/Request | Latency P95 | Accuracy |
|-------|--------------|-------------|----------|
| Model A (high quality) | $0.010 | 2.5s | 95% |
| Model B (efficient) | $0.003 | 1.2s | 88% |
| Model C (alternative) | $0.012 | 3.0s | 94% |

## Analytics Queries

| Analysis | Langfuse Filter | Output |
|----------|-----------------|--------|
| Model cost | Group by model | Cost breakdown |
| Latency dist | Filter by model | P50/P95/P99 |
| Quality trend | Score over time | Trend chart |
| A/B results | Filter experiment | Variant comparison |

## Decision Matrix

| Priority | Choose |
|----------|--------|
| Cost-sensitive | Efficient/smaller model |
| Accuracy-critical | High-quality model |
| Balanced | Analyze A/B results |
| Low latency | Efficient/smaller model |

## Related

- [Dashboard Metrics](../patterns/dashboard-metrics.md)
- [Cost Tracking](../concepts/cost-tracking.md)
- [Scoring](../concepts/scoring.md)

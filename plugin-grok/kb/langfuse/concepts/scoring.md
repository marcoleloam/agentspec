# Scoring

> **Purpose**: Attach quality scores to traces and observations for evaluation
> **Confidence**: 0.95
> **MCP Validated**: 2026-02-17

## Overview

Langfuse scoring lets you attach quality metrics to traces and individual observations. Scores support three data types: numeric (floats), categorical (string labels), and boolean (0/1). Scores can be created via SDK, API, human annotation in the UI, or automated LLM-as-a-Judge evaluators. All scores are aggregated in dashboards for analysis across models, prompt versions, and users.

## The Pattern

```python
from langfuse import get_client

langfuse = get_client()

# Score a trace by ID
langfuse.create_score(
    name="accuracy",
    value=0.92,
    trace_id="trace-abc-123",
    data_type="NUMERIC",
    comment="Automated extraction accuracy check"
)

# Score with categorical value
langfuse.create_score(
    name="correctness",
    value="correct",
    trace_id="trace-abc-123",
    data_type="CATEGORICAL",
    comment="All fields extracted correctly"
)

# Boolean score
langfuse.create_score(
    name="hallucination_detected",
    value=0,
    trace_id="trace-abc-123",
    data_type="BOOLEAN",
    comment="No hallucinations found"
)

langfuse.flush()
```

## Score Data Types

| Type | Values | Use Case |
|------|--------|----------|
| `NUMERIC` | Any float (e.g., 0.0 - 1.0) | Accuracy, similarity, confidence |
| `CATEGORICAL` | String labels | "correct", "partial", "incorrect" |
| `BOOLEAN` | 0 or 1 | Pass/fail checks, hallucination detection |

## Scoring Methods

| Method | How | When |
|--------|-----|------|
| SDK `create_score()` | Programmatic, by trace/observation ID | Post-processing pipelines |
| Context manager `score()` | Score current span inline | During execution |
| `score_current_span()` | Score active observation | During execution |
| `score_trace()` | Score the parent trace | During execution |
| Human annotation | Via Langfuse UI | Manual review |
| LLM-as-a-Judge | Automated evaluator | Continuous evaluation |

## Inline Scoring

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="generation",
    name="extract-fields",
    model="gemini-2.0-flash"
) as gen:
    result = call_llm(prompt)
    gen.update(output=result)

    # Score this specific generation
    gen.score(
        name="extraction_quality",
        value="correct",
        data_type="CATEGORICAL",
        comment="All fields match ground truth"
    )

    # Score the parent trace
    gen.score_trace(
        name="overall_quality",
        value=0.95,
        data_type="NUMERIC"
    )

langfuse.flush()
```

## Evaluation Dimensions

| Dimension | Score Name Example | Type |
|-----------|-------------------|------|
| Factual accuracy | `accuracy` | NUMERIC |
| Completeness | `completeness` | CATEGORICAL |
| Hallucination | `hallucination_detected` | BOOLEAN |
| Tone/style | `tone_appropriate` | BOOLEAN |
| User satisfaction | `user_rating` | NUMERIC |
| Latency acceptable | `latency_ok` | BOOLEAN |

## Common Mistakes

### Wrong

```python
# Not specifying data_type - relies on inference
langfuse.create_score(name="quality", value="good", trace_id="t-1")
```

### Correct

```python
# Explicitly set data_type for consistency
langfuse.create_score(
    name="quality",
    value="good",
    trace_id="t-1",
    data_type="CATEGORICAL"
)
```

## Related

- [Quality Feedback Loops](../patterns/quality-feedback-loops.md)
- [Generations](../concepts/generations.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)

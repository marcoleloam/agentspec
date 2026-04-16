# Quality Feedback Loops

> **Purpose**: Build automated and human-in-the-loop quality evaluation pipelines
> **MCP Validated**: 2026-02-17

## When to Use

- Implementing LLM-as-a-Judge for automated quality scoring
- Building human annotation workflows for ground truth
- Creating feedback loops that improve prompt quality over time
- Detecting quality regressions across model or prompt changes

## Implementation

```python
"""Quality feedback loop with automated and human scoring."""

import json
from langfuse import get_client, observe

langfuse = get_client()


# ── Automated LLM-as-a-Judge ─────────────────────────────────
@observe()
def evaluate_extraction(
    extraction_result: dict,
    original_text: str,
    trace_id: str
) -> dict:
    """Use a judge LLM to evaluate extraction quality."""

    judge_prompt = f"""Evaluate this extraction result for accuracy.

Original text:
{original_text}

Extracted fields:
{json.dumps(extraction_result, indent=2)}

Score each dimension from 0.0 to 1.0:
- accuracy: Are the extracted values correct?
- completeness: Are all expected fields present?
- formatting: Is the output properly structured?

Return JSON: {{"accuracy": float, "completeness": float, "formatting": float}}
"""

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="quality-judge",
        model="gpt-4o-mini"
    ) as gen:
        judge_result = call_judge_llm(judge_prompt)
        gen.update(
            input=judge_prompt,
            output=judge_result,
            metadata={"evaluation_type": "llm-as-judge"}
        )

    # Parse scores and attach to original trace
    scores = json.loads(judge_result)

    for dimension, value in scores.items():
        langfuse.create_score(
            name=dimension,
            value=value,
            trace_id=trace_id,
            data_type="NUMERIC",
            comment=f"LLM-as-Judge: {dimension}"
        )

    langfuse.flush()
    return scores


# ── Ground Truth Comparison ───────────────────────────────────
@observe()
def compare_with_ground_truth(
    extraction: dict,
    ground_truth: dict,
    trace_id: str
) -> dict:
    """Compare extraction against known-good ground truth."""
    scores = {}

    # Field-level accuracy
    correct_fields = 0
    total_fields = len(ground_truth)

    for field, expected in ground_truth.items():
        actual = extraction.get(field)
        if actual == expected:
            correct_fields += 1

    accuracy = correct_fields / total_fields if total_fields > 0 else 0

    langfuse.create_score(
        name="field_accuracy",
        value=accuracy,
        trace_id=trace_id,
        data_type="NUMERIC",
        comment=f"{correct_fields}/{total_fields} fields correct"
    )

    # Completeness check
    missing = [f for f in ground_truth if f not in extraction]
    langfuse.create_score(
        name="completeness",
        value="complete" if not missing else "incomplete",
        trace_id=trace_id,
        data_type="CATEGORICAL",
        comment=f"Missing: {missing}" if missing else "All fields present"
    )

    langfuse.flush()
    return {"accuracy": accuracy, "missing_fields": missing}


# ── End-to-End Pipeline with Evaluation ───────────────────────
@observe()
def extract_and_evaluate(document: dict) -> dict:
    """Full pipeline: extract, score, and track quality."""
    with langfuse.start_as_current_observation(
        as_type="span",
        name="extract-and-evaluate"
    ) as trace:
        # Step 1: Extract
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="extract",
            model="gemini-2.0-flash"
        ) as gen:
            result = call_extraction_llm(document["text"])
            gen.update(output=result)

        # Step 2: Auto-evaluate
        trace_id = trace.trace_id
        scores = evaluate_extraction(result, document["text"], trace_id)

        # Step 3: Flag for human review if quality is low
        avg_score = sum(scores.values()) / len(scores)
        if avg_score < 0.8:
            langfuse.create_score(
                name="needs_human_review",
                value=1,
                trace_id=trace_id,
                data_type="BOOLEAN",
                comment=f"Avg quality {avg_score:.2f} below threshold"
            )

        trace.update(output=result)

    langfuse.flush()
    return result
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Quality threshold | 0.8 | Below this triggers human review |
| Judge model | gpt-4o-mini | Cost-effective evaluation model |
| Score dimensions | 3 | accuracy, completeness, formatting |

## Evaluation Flow

```text
Extraction Trace
    |
    v
LLM-as-Judge ── scores ──> accuracy (NUMERIC)
    |                       completeness (NUMERIC)
    |                       formatting (NUMERIC)
    v
Threshold Check
    |
    +-- avg >= 0.8 --> Dashboard (automated pass)
    |
    +-- avg < 0.8 --> Human Review Queue
                          |
                          v
                      Manual Score --> Updated metrics
```

## See Also

- [Scoring](../concepts/scoring.md)
- [Model Comparison](../concepts/model-comparison.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)

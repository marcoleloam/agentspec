# Metrics

> **Purpose**: DeepEval metrics for evaluating ShopAgent tool selection and answer quality
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

DeepEval provides four primary metrics for ShopAgent evaluation. `ToolCorrectnessMetric` is deterministic (no LLM judge needed). The others (`AnswerRelevancyMetric`, `FaithfulnessMetric`, `GEval`) use an LLM-as-judge. All metrics expose `.score` (float 0-1) and `.reason` (string) after `.measure()`.

## The Pattern

```python
from deepeval.metrics import (
    ToolCorrectnessMetric,
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    GEval,
)
from deepeval.test_case import LLMTestCaseParams

# Tool routing: did agent pick SQL vs semantic correctly?
tool_metric = ToolCorrectnessMetric(threshold=1.0)

# Answer quality: is the response relevant to the question?
relevancy_metric = AnswerRelevancyMetric(
    threshold=0.7,
    model="claude-sonnet-4-20250514",
    include_reason=True,
)

# RAG grounding: is the answer based on retrieved context?
faithfulness_metric = FaithfulnessMetric(
    threshold=0.7,
    model="claude-sonnet-4-20250514",
    include_reason=True,
)

# Custom: does the response contain actionable e-commerce insights?
ecommerce_metric = GEval(
    name="E-Commerce Actionability",
    criteria="The response provides specific, actionable e-commerce insights with concrete numbers or recommendations.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.7,
)

# Evaluate a single test case
tool_metric.measure(test_case)
print(f"Score: {tool_metric.score}, Reason: {tool_metric.reason}")
```

## Quick Reference

| Metric | Measures | Required Fields | Threshold | LLM Judge |
|--------|----------|-----------------|-----------|-----------|
| `ToolCorrectnessMetric` | Tool routing accuracy | `tools_called`, `expected_tools` | `1.0` | No |
| `AnswerRelevancyMetric` | Response relevance | `input`, `actual_output` | `0.7` | Yes |
| `FaithfulnessMetric` | Answer grounding | `retrieval_context`, `actual_output` | `0.7` | Yes |
| `GEval` | Custom rubric | Configured via `evaluation_params` | `0.7` | Yes |

## Common Mistakes

### Wrong

```python
# FaithfulnessMetric without retrieval_context — raises error
test = LLMTestCase(input="...", actual_output="...")
FaithfulnessMetric(threshold=0.7).measure(test)  # MetricComputationError
```

### Correct

```python
# Always populate retrieval_context from agent's retrieved chunks
test = LLMTestCase(
    input="Quem reclama de entrega?",
    actual_output="23 clientes...",
    retrieval_context=["Demorou 15 dias...", "Nao recebi..."],
)
FaithfulnessMetric(threshold=0.7, model="claude-sonnet-4-20250514").measure(test)
```

## Related

- [Test Cases](../concepts/test-cases.md)
- [Agent Evaluation Pattern](../patterns/agent-evaluation.md)

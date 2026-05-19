# DeepEval Quick Reference

> Fast lookup tables. For code examples, see linked files.

## Installation

```bash
pip install deepeval
```

## LLMTestCase Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `input` | `str` | Yes | The user question or prompt |
| `actual_output` | `str` | Yes | The agent's response |
| `expected_output` | `str` | No | Ground truth answer |
| `retrieval_context` | `list[str]` | No | **Required for FaithfulnessMetric** |
| `tools_called` | `list[ToolCall]` | No | **Required for ToolCorrectnessMetric** |
| `expected_tools` | `list[ToolCall]` | No | **Required for ToolCorrectnessMetric** |

## ToolCall Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | `str` | Yes | Tool identifier: `"supabase_execute_sql"` |
| `description` | `str` | No | Human-readable description |
| `input` | `dict` | No | Arguments passed to the tool |
| `output` | `str` | No | Tool return value |

## Metrics

| Metric | Measures | Required Fields | Threshold | LLM Judge |
|--------|----------|-----------------|-----------|-----------|
| `ToolCorrectnessMetric` | Right tool selected? | `tools_called`, `expected_tools` | `1.0` | No |
| `AnswerRelevancyMetric` | Answer relevant to question? | `input`, `actual_output` | `0.7` | Yes |
| `FaithfulnessMetric` | Answer grounded in context? | `retrieval_context`, `actual_output` | `0.7` | Yes |
| `GEval` | Custom criteria | Configured via `evaluation_params` | `0.7` | Yes |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Tool routing correctness (SQL vs semantic) | `ToolCorrectnessMetric(threshold=1.0)` |
| Response quality and relevance | `AnswerRelevancyMetric(threshold=0.7)` |
| RAG grounding (answer from retrieved docs) | `FaithfulnessMetric(threshold=0.7)` — requires `retrieval_context` |
| Custom business criteria | `GEval(name="...", criteria="...", threshold=0.7)` |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Pass tool names as strings in `tools_called` | Use `ToolCall(name="tool_name")` objects |
| Use `FaithfulnessMetric` without `retrieval_context` | Always populate from agent's retrieved chunks |
| Set `expected_tools` only | Provide BOTH `tools_called` AND `expected_tools` |
| Use default `model="gpt-4o"` for evaluation | Use `model="claude-sonnet-4-20250514"` to match ShopAgent stack |

## Related Documentation

| Topic | Path |
|-------|------|
| Test Case Structure | `concepts/test-cases.md` |
| Metrics Detail | `concepts/metrics.md` |
| Agent Evaluation | `patterns/agent-evaluation.md` |
| pytest Integration | `patterns/pytest-integration.md` |
| Full Index | `index.md` |

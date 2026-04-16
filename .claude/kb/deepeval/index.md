# DeepEval Knowledge Base

> **Purpose**: LLM evaluation framework for ShopAgent — test tool selection correctness and answer quality with DeepEval
> **MCP Validated**: 2026-04-12

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/test-cases.md](concepts/test-cases.md) | LLMTestCase structure for SQL and semantic routing evaluation |
| [concepts/metrics.md](concepts/metrics.md) | ToolCorrectness, AnswerRelevancy, Faithfulness, GEval metrics |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/agent-evaluation.md](patterns/agent-evaluation.md) | **KEY**: Batch evaluate ShopAgent tool routing and answer quality |
| [patterns/pytest-integration.md](patterns/pytest-integration.md) | Integrate evaluations into pytest CI with parametrized test cases |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/deepeval-config.yaml](specs/deepeval-config.yaml) | LLMTestCase fields, ToolCall fields, metric defaults |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **LLMTestCase** | Unit of evaluation: wraps input, actual_output, tools_called, retrieval_context |
| **ToolCall** | Represents a tool invocation with name, input dict, and optional output |
| **ToolCorrectnessMetric** | Binary: did the agent route to the correct tool? |
| **AnswerRelevancyMetric** | LLM-as-judge: is the response relevant to the question? |
| **FaithfulnessMetric** | RAG grounding: is the answer supported by retrieved context? |
| **GEval** | Custom criteria evaluation using LLM-as-judge with user-defined rubric |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/test-cases.md, concepts/metrics.md |
| **Intermediate** | patterns/agent-evaluation.md |
| **Advanced** | patterns/pytest-integration.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| shopagent-builder | patterns/agent-evaluation.md | Day 4 quality validation before live demo |
| ai-data-engineer | patterns/pytest-integration.md | CI/CD evaluation pipeline |

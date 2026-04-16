# pytest Integration

> **Purpose**: Integrate ShopAgent evaluations into pytest CI with parametrized test cases
> **MCP Validated**: 2026-04-12

## When to Use

- Automated testing in CI/CD pipeline
- Regression testing after changes to ShopAgent routing logic
- Per-test-case pass/fail reporting with pytest output

## Implementation

```python
"""tests/test_shopagent.py — ShopAgent evaluation via pytest + DeepEval."""
import pytest
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset
from deepeval.metrics import AnswerRelevancyMetric, ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

# ---------------------------------------------------------------------------
# Dataset — representative ShopAgent routing scenarios
# ---------------------------------------------------------------------------
_RAW_CASES = [
    LLMTestCase(
        input="Faturamento total por estado?",
        actual_output="SP: R$ 127.430, RJ: R$ 89.210, MG: R$ 68.440",
        tools_called=[ToolCall(name="supabase_execute_sql")],
        expected_tools=[ToolCall(name="supabase_execute_sql")],
    ),
    LLMTestCase(
        input="Ticket medio por categoria?",
        actual_output="Eletronicos: R$ 342, Roupas: R$ 87, Casa: R$ 156",
        tools_called=[ToolCall(name="supabase_execute_sql")],
        expected_tools=[ToolCall(name="supabase_execute_sql")],
    ),
    LLMTestCase(
        input="Quem reclama de entrega?",
        actual_output="23 clientes com reclamacoes de entrega.",
        retrieval_context=["Demorou 15 dias.", "Nao recebi.", "Frete caro."],
        tools_called=[ToolCall(name="qdrant_semantic_search")],
        expected_tools=[ToolCall(name="qdrant_semantic_search")],
    ),
    LLMTestCase(
        input="Sentimento sobre qualidade dos produtos?",
        actual_output="67% positivo. Elogios: custo-beneficio.",
        retrieval_context=["Produto otimo!", "Boa qualidade.", "Quebrou rapido."],
        tools_called=[ToolCall(name="qdrant_semantic_search")],
        expected_tools=[ToolCall(name="qdrant_semantic_search")],
    ),
]

dataset = EvaluationDataset(test_cases=_RAW_CASES)


# ---------------------------------------------------------------------------
# Test: tool routing correctness (threshold 1.0)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "test_case",
    dataset.test_cases,
    ids=[tc.input[:30] for tc in dataset.test_cases],
)
def test_shopagent_routing(test_case: LLMTestCase) -> None:
    """Assert ShopAgent routes to the correct tool."""
    assert_test(test_case, [ToolCorrectnessMetric(threshold=1.0)])


# ---------------------------------------------------------------------------
# Test: answer relevancy (threshold 0.7)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "test_case",
    dataset.test_cases,
    ids=[tc.input[:30] for tc in dataset.test_cases],
)
def test_shopagent_relevancy(test_case: LLMTestCase) -> None:
    """Assert ShopAgent answers are relevant to the question."""
    assert_test(
        test_case,
        [AnswerRelevancyMetric(threshold=0.7, model="claude-sonnet-4-20250514")],
    )
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `ids` parameter | `tc.input[:30]` | Readable test IDs in pytest output |
| `ToolCorrectnessMetric.threshold` | `1.0` | Binary routing check |
| `AnswerRelevancyMetric.model` | `"claude-sonnet-4-20250514"` | Match ShopAgent stack |

## Example Usage

```bash
# Run with deepeval CLI (recommended)
deepeval test run tests/test_shopagent.py

# Run with pytest
pytest tests/test_shopagent.py -v

# Run only routing tests
pytest tests/test_shopagent.py -k "routing" -v

# Stop on first failure
pytest tests/test_shopagent.py -x -v
```

## See Also

- [Agent Evaluation](../patterns/agent-evaluation.md)
- [Testing Patterns](../../testing/patterns/unit-test-patterns.md)

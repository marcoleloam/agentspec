# Agent Evaluation

> **Purpose**: Evaluate ShopAgent tool selection correctness and answer quality across SQL and semantic routing
> **MCP Validated**: 2026-04-12

## When to Use

- Day 4 quality validation before the live demo
- Testing that the agent routes SQL queries to `supabase_execute_sql`
- Testing that the agent routes semantic queries to `qdrant_semantic_search`
- Measuring response relevancy across a representative test matrix

## Implementation

```python
"""ShopAgent evaluation — tool routing and answer quality."""
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

# ---------------------------------------------------------------------------
# Test matrix: ShopAgent queries covering SQL, semantic, and hybrid
# ---------------------------------------------------------------------------
TEST_MATRIX = [
    # SQL queries — exact numbers from Supabase
    {
        "input": "Qual o faturamento total por estado?",
        "actual_output": "SP: R$ 127.430, RJ: R$ 89.210, MG: R$ 68.440",
        "tools_called": [ToolCall(name="supabase_execute_sql")],
        "expected_tools": [ToolCall(name="supabase_execute_sql")],
    },
    {
        "input": "Quantos pedidos foram feitos por pix?",
        "actual_output": "1.847 pedidos pagos via pix (45% do total).",
        "tools_called": [ToolCall(name="supabase_execute_sql")],
        "expected_tools": [ToolCall(name="supabase_execute_sql")],
    },
    {
        "input": "Qual o ticket medio por segmento de cliente?",
        "actual_output": "Premium: R$ 487, Standard: R$ 234, Basic: R$ 112",
        "tools_called": [ToolCall(name="supabase_execute_sql")],
        "expected_tools": [ToolCall(name="supabase_execute_sql")],
    },
    # Semantic queries — meaning from Qdrant
    {
        "input": "Quais clientes reclamam de entrega?",
        "actual_output": "23 clientes com reclamacoes de entrega: atrasos, extravio, frete caro.",
        "retrieval_context": ["Demorou 15 dias.", "Nao recebi meu pedido.", "Frete caro demais."],
        "tools_called": [ToolCall(name="qdrant_semantic_search")],
        "expected_tools": [ToolCall(name="qdrant_semantic_search")],
    },
    {
        "input": "O que os clientes falam sobre qualidade dos produtos?",
        "actual_output": "Maioria positiva. 12% citam problemas com durabilidade.",
        "retrieval_context": ["Produto otimo!", "Qualidade boa pelo preco.", "Quebrou em 2 semanas."],
        "tools_called": [ToolCall(name="qdrant_semantic_search")],
        "expected_tools": [ToolCall(name="qdrant_semantic_search")],
    },
    {
        "input": "Qual o sentimento geral sobre o frete?",
        "actual_output": "67% negativo. Principais queixas: prazo e custo.",
        "retrieval_context": ["Frete caro demais.", "Chegou antes do previsto!", "Rastreamento nao funciona."],
        "tools_called": [ToolCall(name="qdrant_semantic_search")],
        "expected_tools": [ToolCall(name="qdrant_semantic_search")],
    },
]

# ---------------------------------------------------------------------------
# Build test cases and metrics
# ---------------------------------------------------------------------------
test_cases = [LLMTestCase(**case) for case in TEST_MATRIX]

tool_metric = ToolCorrectnessMetric(threshold=1.0)
relevancy_metric = AnswerRelevancyMetric(
    threshold=0.7,
    model="claude-sonnet-4-20250514",
    include_reason=True,
)

# ---------------------------------------------------------------------------
# Batch evaluation
# ---------------------------------------------------------------------------
results = evaluate(test_cases=test_cases, metrics=[tool_metric, relevancy_metric])

# Print summary
for tc in test_cases:
    expected = tc.expected_tools[0].name if tc.expected_tools else "—"
    actual = tc.tools_called[0].name if tc.tools_called else "—"
    routing = "PASS" if expected == actual else "FAIL"
    print(f"[{routing}] {tc.input[:50]}")
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `ToolCorrectnessMetric.threshold` | `1.0` | Binary — must route to exact tool |
| `AnswerRelevancyMetric.threshold` | `0.7` | Minimum relevancy score |
| `model` for LLM metrics | `"claude-sonnet-4-20250514"` | Match ShopAgent stack |
| `include_reason` | `True` | Get explanation in `metric.reason` |

## Example Usage

```python
# Single test case
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

test = LLMTestCase(
    input="Faturamento por estado?",
    actual_output="SP: R$ 127.430...",
    tools_called=[ToolCall(name="supabase_execute_sql")],
    expected_tools=[ToolCall(name="supabase_execute_sql")],
)
metric = ToolCorrectnessMetric(threshold=1.0)
metric.measure(test)
print(f"Score: {metric.score}")  # 1.0 if correct tool
```

## See Also

- [pytest Integration](../patterns/pytest-integration.md)
- [Test Cases](../concepts/test-cases.md)
- [LangChain Dual Tools](../../langchain/patterns/react-agent-dual-tools.md)

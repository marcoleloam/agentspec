# Cost Alerting

> **Purpose**: Monitor LLM costs and set up budget alerts using Langfuse metrics
> **MCP Validated**: 2026-02-17

## When to Use

- Preventing unexpected LLM cost spikes in production
- Setting per-user, per-model, or per-feature cost budgets
- Building cost anomaly detection into your pipeline
- Generating cost reports for stakeholders

## Implementation

```python
"""Cost monitoring and alerting with Langfuse."""

import os
from datetime import datetime, timedelta
from langfuse import get_client, observe

langfuse = get_client()

# ── Cost Tracking Per Request ─────────────────────────────────
COST_BUDGET_PER_REQUEST = float(
    os.getenv("COST_BUDGET_PER_REQUEST", "0.05")
)
DAILY_BUDGET = float(os.getenv("DAILY_BUDGET", "50.00"))


@observe()
def tracked_llm_call(
    prompt: str,
    model: str = "gemini-2.0-flash",
    user_id: str = "system"
) -> dict:
    """LLM call with cost tracking and budget check."""

    with langfuse.start_as_current_observation(
        as_type="generation",
        name="cost-tracked-call",
        model=model
    ) as gen:
        result = call_llm(prompt, model=model)

        # Calculate cost from response metadata
        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)
        cost = calculate_cost(model, input_tokens, output_tokens)

        gen.update(
            output=result.get("text"),
            usage_details={
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            },
            cost_details={
                "input": cost["input"],
                "output": cost["output"],
                "total": cost["total"]
            },
            metadata={
                "user_id": user_id,
                "budget_limit": COST_BUDGET_PER_REQUEST
            }
        )

        # Budget check
        if cost["total"] > COST_BUDGET_PER_REQUEST:
            gen.score(
                name="over_budget",
                value=1,
                data_type="BOOLEAN",
                comment=(
                    f"Cost ${cost['total']:.4f} exceeds "
                    f"budget ${COST_BUDGET_PER_REQUEST:.4f}"
                )
            )
            alert_over_budget(user_id, model, cost["total"])

    langfuse.flush()
    return result


# ── Cost Calculation Helper ───────────────────────────────────
MODEL_PRICING = {
    "gemini-2.0-flash": {"input": 0.075 / 1_000_000,
                         "output": 0.30 / 1_000_000},
    "gpt-4o": {"input": 2.50 / 1_000_000,
               "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000,
                    "output": 0.60 / 1_000_000},
    "claude-sonnet-4-20250514": {"input": 3.00 / 1_000_000,
                          "output": 15.00 / 1_000_000},
}


def calculate_cost(
    model: str, input_tokens: int, output_tokens: int
) -> dict:
    """Calculate cost based on model pricing."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o-mini"])
    input_cost = input_tokens * pricing["input"]
    output_cost = output_tokens * pricing["output"]
    return {
        "input": input_cost,
        "output": output_cost,
        "total": input_cost + output_cost
    }


# ── Alerting ──────────────────────────────────────────────────
def alert_over_budget(user_id: str, model: str, cost: float):
    """Send alert when cost exceeds budget."""
    print(
        f"ALERT: User {user_id} cost ${cost:.4f} "
        f"on {model} exceeds budget"
    )
    # Integrate with Slack, PagerDuty, Cloud Monitoring, etc.


# ── Cost Summary ──────────────────────────────────────────────
@observe()
def log_cost_summary(costs: list[dict]):
    """Log a batch cost summary as a trace."""
    total = sum(c["total"] for c in costs)
    with langfuse.start_as_current_observation(
        as_type="span",
        name="cost-summary"
    ) as span:
        span.update(
            output={
                "total_cost_usd": total,
                "num_calls": len(costs),
                "avg_cost_per_call": total / len(costs) if costs else 0
            },
            metadata={"report_type": "daily_cost_summary"}
        )

        span.score(
            name="daily_budget_status",
            value="over" if total > DAILY_BUDGET else "under",
            data_type="CATEGORICAL",
            comment=f"${total:.2f} / ${DAILY_BUDGET:.2f}"
        )

    langfuse.flush()
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `COST_BUDGET_PER_REQUEST` | `0.05` | Max USD per single LLM call |
| `DAILY_BUDGET` | `50.00` | Max USD per day across all calls |
| Alert channel | stdout | Override with Slack/PagerDuty integration |

## Cost Monitoring Strategy

| Level | What to Monitor | Alert Threshold |
|-------|-----------------|-----------------|
| Per-request | Single LLM call cost | > $0.05 |
| Per-user | Cumulative user spend | > $5.00/day |
| Per-model | Model-specific spend | > $20.00/day |
| Daily total | All LLM costs | > $50.00/day |
| Weekly trend | Cost growth rate | > 20% week-over-week |

## Example Usage

```python
# Track costs across multiple calls
costs = []
for document in documents:
    result = tracked_llm_call(
        prompt=f"Extract from: {document['text']}",
        model="gemini-2.0-flash",
        user_id=document["user_id"]
    )
    costs.append(result.get("cost", {}))

# End-of-batch summary
log_cost_summary(costs)
```

## See Also

- [Cost Tracking](../concepts/cost-tracking.md)
- [Dashboard Metrics](../patterns/dashboard-metrics.md)
- [Cloud Run Instrumentation](../patterns/cloud-run-instrumentation.md)

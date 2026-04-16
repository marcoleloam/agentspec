# Dashboard Metrics

> **Purpose**: Set up Langfuse dashboards and export metrics for monitoring LLM applications
> **MCP Validated**: 2026-02-17

## When to Use

- Building operational dashboards for LLM pipeline monitoring
- Tracking cost, latency, quality, and volume trends over time
- Exporting Langfuse metrics to external analytics platforms
- Creating alerting rules based on metric thresholds

## Implementation

```python
"""Dashboard-ready metric instrumentation with Langfuse."""

import time
from langfuse import get_client, observe, propagate_attributes

langfuse = get_client()


# ── Instrumented Pipeline with Dashboard Tags ─────────────────
@observe()
def process_document(
    document: dict,
    pipeline: str = "invoice-extraction",
    environment: str = "production"
) -> dict:
    """Fully instrumented pipeline for dashboard visibility."""

    with langfuse.start_as_current_observation(
        as_type="span",
        name=pipeline
    ) as trace:
        with propagate_attributes(
            user_id=document.get("user_id", "system"),
            session_id=document.get("session_id"),
            tags=[
                pipeline,
                environment,
                f"model:{document.get('model', 'gemini-2.0-flash')}"
            ],
            metadata={
                "pipeline": pipeline,
                "environment": environment,
                "document_type": document.get("type", "unknown"),
                "source": document.get("source", "api")
            }
        ):
            trace.update(input=document)

            # Track preprocessing latency
            start = time.time()
            with langfuse.start_as_current_observation(
                as_type="span",
                name="preprocess"
            ) as preprocess:
                cleaned = preprocess_doc(document)
                preprocess.update(
                    output={"status": "done"},
                    metadata={
                        "latency_ms": int(
                            (time.time() - start) * 1000
                        )
                    }
                )

            # Track LLM call with full metrics
            model = document.get("model", "gemini-2.0-flash")
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="extract",
                model=model
            ) as gen:
                result = call_llm(cleaned, model=model)
                gen.update(
                    output=result,
                    usage_details={
                        "input": result.get("input_tokens", 0),
                        "output": result.get("output_tokens", 0)
                    },
                    cost_details={
                        "total": result.get("cost", 0.0)
                    }
                )

            # Quality score for dashboard aggregation
            quality = evaluate_quality(result)
            langfuse.create_score(
                name="extraction_quality",
                value=quality,
                trace_id=trace.trace_id,
                data_type="NUMERIC",
                comment="Automated quality check"
            )

            # Categorical outcome for funnel analysis
            langfuse.create_score(
                name="outcome",
                value="success" if quality > 0.8 else "review",
                trace_id=trace.trace_id,
                data_type="CATEGORICAL"
            )

            trace.update(output=result)

    langfuse.flush()
    return result
```

## Dashboard Metrics Overview

| Metric | Source | Aggregation |
|--------|--------|-------------|
| **Cost** | `cost_details.total` | Sum by model/user/day |
| **Latency** | Observation duration | p50, p95, p99 |
| **Token Usage** | `usage_details.total` | Sum, avg per request |
| **Quality Scores** | Score values | Avg by model/prompt |
| **Volume** | Trace count | Count per time window |
| **Error Rate** | Failed observations | Percentage |
| **Success Rate** | Outcome scores | success / total |

## Tagging Strategy for Dashboards

| Tag Pattern | Purpose | Example |
|-------------|---------|---------|
| `pipeline:{name}` | Filter by feature | `pipeline:invoice-extraction` |
| `model:{name}` | Compare models | `model:gemini-2.0-flash` |
| `environment` | Separate prod/staging | `production`, `staging` |
| `source:{origin}` | Track request origin | `source:api`, `source:pubsub` |

## External Integrations

| Platform | Integration Method |
|----------|--------------------|
| **PostHog** | Native Langfuse integration |
| **Mixpanel** | Native Langfuse integration |
| **Grafana** | Metrics API + custom dashboard |
| **Cloud Monitoring** | Export via API, alert with Cloud Functions |
| **BigQuery** | Export traces via API for custom analytics |

## Key Dashboard Views

| View | What It Shows | Filters |
|------|---------------|---------|
| **Cost Overview** | Spend by model, user, day | Date range, model, tags |
| **Latency Distribution** | p50/p95/p99 response times | Pipeline, model |
| **Quality Trends** | Score averages over time | Score name, model |
| **Trace Explorer** | Individual trace details | Tags, user, session |
| **Prompt Analytics** | Performance per prompt version | Prompt name, version |

## Example Usage

```python
# Instrument all pipelines with consistent tagging
for doc in batch:
    process_document(
        document=doc,
        pipeline="invoice-extraction",
        environment=os.getenv("ENVIRONMENT", "staging")
    )
```

## See Also

- [Cost Tracking](../concepts/cost-tracking.md)
- [Scoring](../concepts/scoring.md)
- [Cost Alerting](../patterns/cost-alerting.md)

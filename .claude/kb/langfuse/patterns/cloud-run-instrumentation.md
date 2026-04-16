# Cloud Run Instrumentation

> **Purpose**: Properly instrument Langfuse tracing in Google Cloud Run serverless services
> **MCP Validated**: 2026-02-17

## When to Use

- Deploying LLM pipelines on Google Cloud Run
- Ensuring traces are flushed before container shutdown
- Connecting Langfuse to GCP-native services (Pub/Sub, GCS, BigQuery)

## Implementation

```python
"""Langfuse instrumentation for Cloud Run services."""

import os
import signal
import atexit
from flask import Flask, request, jsonify
from langfuse import get_client, observe, propagate_attributes

app = Flask(__name__)
langfuse = get_client()


# ── Graceful Shutdown ─────────────────────────────────────────
def flush_on_shutdown(*args):
    """Flush all pending traces before Cloud Run terminates."""
    print("Flushing Langfuse traces before shutdown...")
    langfuse.flush()
    print("Langfuse flush complete.")


# Register flush for both SIGTERM (Cloud Run) and atexit
signal.signal(signal.SIGTERM, flush_on_shutdown)
atexit.register(langfuse.flush)


# ── Traced Endpoint ───────────────────────────────────────────
@app.route("/extract", methods=["POST"])
def extract_invoice():
    """Cloud Run endpoint with full Langfuse tracing."""
    data = request.get_json()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="cloud-run-extract"
    ) as trace:
        with propagate_attributes(
            user_id=data.get("user_id", "system"),
            session_id=data.get("session_id"),
            tags=["cloud-run", "invoice-extraction"],
            metadata={
                "cloud_run_revision": os.getenv(
                    "K_REVISION", "unknown"
                ),
                "source_bucket": data.get("bucket"),
            }
        ):
            trace.update(input=data)

            # Preprocessing span
            with langfuse.start_as_current_observation(
                as_type="span",
                name="preprocess"
            ) as preprocess:
                cleaned = preprocess_document(data["text"])
                preprocess.update(output={"status": "cleaned"})

            # LLM generation
            with langfuse.start_as_current_observation(
                as_type="generation",
                name="gemini-extract",
                model="gemini-2.0-flash"
            ) as gen:
                result = call_gemini(cleaned)
                gen.update(
                    input=cleaned,
                    output=result,
                    model_parameters={
                        "temperature": 0.0,
                        "max_tokens": 2048
                    },
                    usage_details={
                        "input": result.get("input_tokens", 0),
                        "output": result.get("output_tokens", 0)
                    }
                )

                gen.score(
                    name="has_required_fields",
                    value=1 if validate_result(result) else 0,
                    data_type="BOOLEAN"
                )

            trace.update(output=result)

    # Flush after each request in serverless
    langfuse.flush()
    return jsonify(result)


# ── Pub/Sub Triggered Endpoint ────────────────────────────────
@app.route("/pubsub", methods=["POST"])
def handle_pubsub():
    """Handle Pub/Sub push messages with tracing."""
    envelope = request.get_json()
    message = envelope.get("message", {})

    with langfuse.start_as_current_observation(
        as_type="span",
        name="pubsub-handler"
    ) as trace:
        with propagate_attributes(
            tags=["cloud-run", "pubsub-trigger"],
            metadata={
                "message_id": message.get("messageId"),
                "subscription": envelope.get("subscription")
            }
        ):
            result = process_message(message)
            trace.update(output=result)

    langfuse.flush()
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `LANGFUSE_SECRET_KEY` | None | Set in Cloud Run env vars or Secret Manager |
| `LANGFUSE_PUBLIC_KEY` | None | Set in Cloud Run env vars |
| `LANGFUSE_BASE_URL` | `https://cloud.langfuse.com` | EU or US region |
| `K_REVISION` | Auto-set | Cloud Run revision (use in metadata) |
| `PORT` | `8080` | Cloud Run container port |

## Dockerfile Integration

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", \
     "--timeout", "300", "main:app"]
```

## Requirements

```text
langfuse>=3.0.0
flask>=3.0
gunicorn>=21.0
google-cloud-storage>=2.0
```

## Cloud Run Deployment

```bash
gcloud run deploy invoice-extractor \
  --source . \
  --region us-central1 \
  --set-env-vars "LANGFUSE_SECRET_KEY=sk-lf-...,\
LANGFUSE_PUBLIC_KEY=pk-lf-...,\
LANGFUSE_BASE_URL=https://cloud.langfuse.com" \
  --memory 1Gi \
  --timeout 300
```

## Critical: Flush Behavior

| Scenario | Required Action |
|----------|----------------|
| HTTP request handler | `langfuse.flush()` after response |
| SIGTERM (scale-down) | `signal.signal(signal.SIGTERM, flush_handler)` |
| Process exit | `atexit.register(langfuse.flush)` |
| Background task | `langfuse.flush()` at task end |

## See Also

- [Python SDK Integration](../patterns/python-sdk-integration.md)
- [Traces and Spans](../concepts/traces-spans.md)
- [Trace Linking](../patterns/trace-linking.md)

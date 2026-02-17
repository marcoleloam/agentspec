# Pub/Sub Fan-Out Pattern

> **Purpose**: Distribute one event to multiple consumers for parallel processing
> **MCP Validated**: 2026-01-25

## When to Use

- One event needs multiple independent actions (audit log + processing + notification)
- Consumers have different performance characteristics
- Consumers can fail independently without blocking others
- You need to add new consumers without modifying publishers

## Implementation

```hcl
# Terraform: Fan-out infrastructure
resource "google_pubsub_topic" "data_processed" {
  name = "data-processed"
}

# Subscription 1: Write to BigQuery
resource "google_pubsub_subscription" "to_bigquery" {
  name  = "data-processed-to-bigquery"
  topic = google_pubsub_topic.data_processed.name

  push_config {
    push_endpoint = google_cloud_run_service.bigquery_writer.status[0].url
    oidc_token {
      service_account_email = google_service_account.pubsub_invoker.email
    }
  }

  ack_deadline_seconds = 60
}

# Subscription 2: Send to audit system
resource "google_pubsub_subscription" "to_audit" {
  name  = "data-processed-to-audit"
  topic = google_pubsub_topic.data_processed.name

  push_config {
    push_endpoint = google_cloud_run_service.audit_logger.status[0].url
    oidc_token {
      service_account_email = google_service_account.pubsub_invoker.email
    }
  }

  ack_deadline_seconds = 30
}

# Subscription 3: Direct BigQuery subscription (no code)
resource "google_pubsub_subscription" "to_bigquery_direct" {
  name  = "data-processed-to-bq-direct"
  topic = google_pubsub_topic.data_processed.name

  bigquery_config {
    table          = "${var.project_id}.audit.raw_events"
    write_metadata = true
  }
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ack_deadline_seconds` | 10 | Time for consumer to acknowledge |
| `message_retention_duration` | 7d | How long unacked messages persist |
| `retain_acked_messages` | false | Keep acknowledged messages |
| `enable_message_ordering` | false | Preserve message order |

## Example Usage

```python
# Publisher: Single publish, multiple consumers receive
from google.cloud import pubsub_v1
import json

def publish_extraction_result(project_id: str, record_data: dict):
    """Publish extraction result - all subscribers receive copy."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, "data-processed")

    message = json.dumps({
        "record_id": record_data["record_id"],
        "supplier_name": record_data["supplier_name"],
        "total_amount": record_data["total_amount"],
        "extracted_at": datetime.utcnow().isoformat(),
        "confidence": record_data["confidence"]
    }).encode()

    # Each subscriber gets their own copy
    future = publisher.publish(
        topic_path,
        message,
        event_type="record.processed",
        source="data-processor"
    )

    return future.result()

# Consumer 1: BigQuery writer
@functions_framework.cloud_event
def write_to_bigquery(cloud_event):
    """Write extracted record to warehouse."""
    data = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
    insert_to_bigquery(data)

# Consumer 2: Audit logger
@functions_framework.cloud_event
def log_to_audit(cloud_event):
    """Log extraction event for compliance."""
    data = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
    log_audit_event("record_processed", data)
```

## Fan-Out Topology

```
                    ┌──────────────────────┐
                    │    data-processor    │
                    └──────────┬───────────┘
                               │ publish
                               v
              ┌────────────────────────────────┐
              │  Topic: data-processed         │
              └────────────────┬───────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        v                      v                      v
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Sub: bigquery │    │ Sub: audit    │    │ Sub: bq-raw   │
│     (push)    │    │    (push)     │    │   (direct)    │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        v                    v                    v
  [BQ Writer]         [Audit Logger]        [BQ: audit]
```

## Dead-Letter Handling

```hcl
resource "google_pubsub_topic" "dlq" {
  name = "data-processed-dlq"
}

resource "google_pubsub_subscription" "with_dlq" {
  name  = "data-processed-to-bigquery"
  topic = google_pubsub_topic.data_processed.name

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq.id
    max_delivery_attempts = 5
  }
}
```

## See Also

- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
- [Pub/Sub](../concepts/pubsub.md)
- [Cloud Run](../concepts/cloud-run.md)

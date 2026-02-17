# Pub/Sub

> **Purpose**: Asynchronous messaging service for event-driven architectures
> **Confidence**: 0.95
> **MCP Validated**: 2026-01-25

## Overview

Cloud Pub/Sub is a fully managed messaging service that decouples publishers from subscribers. Publishers send messages to topics; subscribers receive messages through subscriptions. It guarantees at-least-once delivery and supports millions of messages per second.

## The Pattern

```python
# Publisher: Send message to topic
from google.cloud import pubsub_v1
import json

def publish_processing_event(project_id: str, topic_id: str, data: dict):
    """Publish data processing event to Pub/Sub."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    # Message must be bytes
    message_bytes = json.dumps(data).encode("utf-8")

    # Publish with attributes for filtering
    future = publisher.publish(
        topic_path,
        message_bytes,
        source="data-processor",
        content_type="application/json"
    )

    return future.result()  # Returns message ID

# Subscriber: Receive message
def callback(message):
    """Process received message."""
    data = json.loads(message.data.decode("utf-8"))
    print(f"Processing: {data}")
    message.ack()  # Acknowledge successful processing
```

## Quick Reference

| Input | Output | Notes |
|-------|--------|-------|
| Publisher message | Stored in topic | Up to 10 MB per message |
| Subscription pull | Messages batch | Max 1000 messages per pull |
| Push subscription | HTTP POST | To Cloud Run endpoint |

## Data Pipeline Topics

| Topic | Purpose | Publisher | Subscriber |
|-------|---------|-----------|------------|
| `data-uploaded` | New file received | GCS Eventarc | File converter |
| `data-converted` | File ready | File converter | Classifier |
| `data-classified` | Type identified | Classifier | Data Processor |
| `data-processed` | Data ready | Data Processor | BigQuery writer |

## Subscription Types

| Type | Use Case | Data Pipeline |
|------|----------|---------------|
| **Push** | Deliver to Cloud Run | Primary for functions |
| **Pull** | Batch processing | Not used |
| **BigQuery** | Direct to warehouse | Audit trail |

## Common Mistakes

### Wrong

```python
# No error handling, no dead-letter queue
message.ack()  # Always acknowledging, even on failure
```

### Correct

```python
try:
    process(message.data)
    message.ack()
except Exception as e:
    # Let it retry, will go to DLQ after max attempts
    message.nack()
    logger.error(f"Processing failed: {e}")
```

## Dead-Letter Queue Configuration

```yaml
# Terraform configuration
resource "google_pubsub_subscription" "data_sub" {
  name  = "data-processed-sub"
  topic = google_pubsub_topic.data_processed.name

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq.id
    max_delivery_attempts = 5
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}
```

## Related

- [Pub/Sub Fan-out](../patterns/pubsub-fanout.md)
- [Event-Driven Pipeline](../patterns/event-driven-pipeline.md)
- [Cloud Run](../concepts/cloud-run.md)

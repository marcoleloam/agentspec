# Event-Driven Pipeline Pattern

> **Purpose**: Decouple data processing stages using GCS, Pub/Sub, and Cloud Run
> **MCP Validated**: 2026-01-25

## When to Use

- Processing stages have different resource requirements (CPU, memory, timeout)
- Stages can fail independently and need retry logic
- You need observability at each pipeline step
- Workloads are bursty and benefit from scale-to-zero

## Implementation

```python
# Stage 1: File Converter (triggered by GCS upload)
import functions_framework
from google.cloud import storage, pubsub_v1
import io
import json

@functions_framework.cloud_event
def convert_file_format(cloud_event):
    """Convert uploaded file and publish event."""
    data = cloud_event.data

    bucket_name = data["bucket"]
    file_name = data["name"]

    if not file_name.endswith(".pdf"):
        return

    # Download source file
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    file_bytes = blob.download_as_bytes()

    # Process/convert file
    processed_bytes = process_file(file_bytes)

    # Upload to processed bucket
    output_bucket = storage_client.bucket("data-processed")
    output_name = file_name.replace(".pdf", "_processed.json")
    output_blob = output_bucket.blob(output_name)
    output_blob.upload_from_string(processed_bytes, content_type="application/json")

    # Publish event for next stage
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path("your-project-id", "data-converted")

    message = json.dumps({
        "bucket": "data-processed",
        "name": output_name,
        "original": file_name
    }).encode()

    publisher.publish(topic_path, message)

    return f"Converted {file_name}"
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `trigger_bucket` | data-input | GCS bucket for uploads |
| `output_bucket` | data-processed | Destination for converted files |
| `pubsub_topic` | data-converted | Topic for next stage |
| `max_instances` | 50 | Scaling limit per stage |
| `timeout` | 300s | Per-request timeout |

## Example Usage

```bash
# Deploy file converter with GCS trigger
gcloud run deploy file-converter \
  --source . \
  --function convert_file_format \
  --region us-central1 \
  --service-account file-converter@project.iam.gserviceaccount.com

# Create Eventarc trigger for GCS
gcloud eventarc triggers create data-upload-trigger \
  --location us-central1 \
  --destination-run-service file-converter \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=data-input" \
  --service-account eventarc@project.iam.gserviceaccount.com
```

## Pipeline Flow

```
[GCS: data-input]
        |
        v (Eventarc trigger)
[Cloud Run: file-converter]
        |
        v (Pub/Sub: data-converted)
[Cloud Run: data-classifier]
        |
        v (Pub/Sub: data-classified)
[Cloud Run: data-processor]
        |
        v (Pub/Sub: data-processed)
[Cloud Run: bigquery-writer]
        |
        v
[BigQuery: analytics.processed_data]
```

## Error Handling

```python
# Dead-letter queue configuration (Terraform)
resource "google_pubsub_subscription" "with_dlq" {
  name  = "data-converted-sub"
  topic = google_pubsub_topic.data_converted.name

  push_config {
    push_endpoint = google_cloud_run_service.classifier.status[0].url
  }

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

## See Also

- [Multi-Bucket Pipeline](../patterns/multi-bucket-pipeline.md)
- [Cloud Run](../concepts/cloud-run.md)
- [Pub/Sub](../concepts/pubsub.md)

# AWS Quick Reference

> Fast lookup tables covering Lambda and Deployment sub-domains. For code examples, see linked files.
> **Last Updated:** 2026-03-26

## Lambda Runtime Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Memory | 128 MB - 10,240 MB | Increase for pandas/pyarrow |
| Timeout | max 900s (15 min) | Default 3s, set explicitly |
| Package size (zipped) | 50 MB | Direct upload |
| Package size (unzipped) | 250 MB | Including layers |
| /tmp storage | 512 MB - 10,240 MB | Ephemeral, configurable |
| Concurrent executions | 1,000 default | Request increase via quota |

## Handler Signature

| Component | Value | Example |
|-----------|-------|---------|
| Handler setting | `{file}.{function}` | `app.lambda_handler` |
| Event parameter | `dict` | S3 event payload |
| Context parameter | `LambdaContext` | Request ID, remaining time |
| Return | `dict`, `str`, `None` | JSON-serializable response |

## SAM CLI Commands

| Command | Purpose | Key Flags |
|---------|---------|-----------|
| `sam init` | Scaffold new project | `--runtime python3.14 --app-template` |
| `sam build` | Build artifacts | `--use-container --parallel` |
| `sam deploy --guided` | Interactive first deploy | Generates `samconfig.toml` |
| `sam deploy` | Deploy with saved config | `--config-env dev` |
| `sam sync --watch` | Hot-sync changes (Accelerate) | `--stack-name` |
| `sam validate --lint` | Validate template | |
| `sam local invoke` | Test function locally | `-e event.json --env-vars` |
| `sam local start-api` | Local API Gateway | `--port 3000` |
| `sam logs` | Tail CloudWatch logs | `--tail --stack-name` |
| `sam delete` | Remove deployed stack | `--no-prompts` |

## AWS CLI Essentials

| Command | Purpose |
|---------|---------|
| `aws configure` | Set credentials interactively |
| `aws sts get-caller-identity` | Verify active identity |
| `aws s3 ls` | List buckets/objects |
| `aws s3 cp` | Copy files |
| `aws s3 sync` | Sync directories |
| `aws lambda list-functions` | List deployed Lambdas |
| `aws cloudformation describe-stacks` | Check stack status |

## S3 Event Types

| Event | When |
|-------|------|
| `s3:ObjectCreated:*` | Any object created |
| `s3:ObjectCreated:Put` | PUT upload only |
| `s3:ObjectCreated:CompleteMultipartUpload` | Multipart upload done |
| `s3:ObjectRemoved:*` | Any object deleted |

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Process S3 uploads | S3 trigger + async invocation |
| REST API endpoint | API Gateway + sync invocation |
| Large dependencies (pandas) | Lambda Layer or container image |
| File > 500 MB processing | Step Functions + EFS mount |
| Retry failed events | DLQ (SQS) + EventInvokeConfig |
| First-time deploy | `sam deploy --guided` |
| Rapid iteration | `sam sync --watch` |
| Steady-state traffic | Managed instances (re:Invent 2025) |
| ETL with Spark | AWS Glue 5.0 |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| Initialize SDK clients inside handler | Initialize outside handler (reuse) |
| Use `*` in IAM resource ARNs | Scope to specific bucket/prefix |
| Set timeout to default 3s | Set timeout >= expected duration |
| Bundle pandas in zip (250 MB+) | Use AWS SDK for pandas managed layer |
| Deploy without building first | `sam build && sam deploy` |
| Hardcode credentials in templates | Use `AWS_PROFILE` or IAM roles |
| Skip `--guided` on first deploy | `sam deploy --guided` to generate samconfig.toml |

## Related Documentation

| Topic | Path |
|-------|------|
| Lambda Concepts | `lambda/concepts/` |
| Lambda Patterns | `lambda/patterns/` |
| Deployment Concepts | `deployment/concepts/` |
| Deployment Patterns | `deployment/patterns/` |
| Lambda Quick Reference | `lambda/quick-reference.md` |
| Deployment Quick Reference | `deployment/quick-reference.md` |
| Full Index | `index.md` |

# Deployment Model

> **Purpose**: Pipeline deployment modes, configuration, and lifecycle management with DABs
> **Confidence**: High
> **Source**: https://docs.databricks.com/aws/en/dev-tools/bundles

## Overview

Lakeflow pipelines are deployed using Databricks Asset Bundles (DABs), a declarative approach to packaging and promoting pipeline configurations across environments. The deployment model covers pipeline modes (development vs production), compute configuration, catalog/schema targeting, and CI/CD integration through `databricks.yml` bundle files.

## The Concept

### Pipeline Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Development** | Reuses cluster, relaxed scheduling, no retries | Interactive development |
| **Production** | Dedicated cluster, enforced scheduling, auto-retries | Production workloads |

### DABs Pipeline Resource

```yaml
# resources/my_pipeline.yml
resources:
  pipelines:
    my_pipeline:
      name: "${bundle.target}-my-etl-pipeline"
      target: "${var.catalog}.${var.schema}"
      development: true
      channel: "CURRENT"
      photon: true
      configuration:
        source_catalog: "${var.source_catalog}"
        landing_path: "${var.landing_path}"
      libraries:
        - notebook:
            path: ../src/bronze.py
        - notebook:
            path: ../src/silver.py
        - notebook:
            path: ../src/gold.py
      clusters:
        - label: "default"
          autoscale:
            min_workers: 1
            max_workers: 4
```

### Multi-Environment Configuration

```yaml
# databricks.yml
bundle:
  name: my-etl-pipeline

variables:
  catalog:
    default: dev_catalog
  schema:
    default: etl

targets:
  dev:
    mode: development
    default: true
    variables:
      catalog: dev_catalog
  staging:
    variables:
      catalog: staging_catalog
  prod:
    mode: production
    variables:
      catalog: prod_catalog
```

### Deployment Commands

```bash
# Validate bundle configuration
databricks bundle validate -t dev

# Deploy to target environment
databricks bundle deploy -t dev

# Run the pipeline
databricks bundle run -t dev my_pipeline

# Promote to production
databricks bundle deploy -t prod
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `bundle validate` | Check config syntax and references |
| `bundle deploy` | Create/update resources in workspace |
| `bundle run` | Trigger pipeline execution |
| `bundle destroy` | Remove all deployed resources |

| Config Key | Purpose | Default |
|------------|---------|---------|
| `development` | Enable dev mode | `false` |
| `photon` | Use Photon engine | `false` |
| `channel` | Runtime channel | `CURRENT` |
| `continuous` | Run continuously | `false` |
| `catalog` | Unity Catalog target | Required |

## Common Mistakes

### Wrong

```yaml
# Hardcoding catalog names — breaks multi-environment
resources:
  pipelines:
    etl:
      target: "prod_catalog.etl_schema"
```

### Correct

```yaml
# Use variables for environment-specific values
resources:
  pipelines:
    etl:
      target: "${var.catalog}.${var.schema}"
```

## Related

- [Core Concepts](../concepts/core-concepts.md)
- [DABs Deployment Pattern](../patterns/dabs-deployment.md)
- [Bronze Ingestion](../patterns/bronze-ingestion.md)

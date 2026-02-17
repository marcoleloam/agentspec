# Knowledge Base (KB) Framework

The KB framework grounds agent responses in your actual codebase patterns.

## Structure

```
kb/
├── _templates/           # Templates for new domains
│   ├── concept.md.template
│   ├── pattern.md.template
│   ├── index.md.template
│   └── quick-reference.md.template
│
└── {domain}/             # Your KB domains
    ├── index.md          # Domain overview
    ├── quick-reference.md # Cheat sheet
    ├── concepts/         # Core concepts
    │   ├── concept-1.md
    │   └── concept-2.md
    └── patterns/         # Implementation patterns
        ├── pattern-1.md
        └── pattern-2.md
```

## Creating a KB Domain

Use the `/create-kb` command:

```bash
claude> /create-kb redis "Caching layer patterns"
```

Or manually:

1. Copy `_templates/` structure
2. Fill in domain-specific content
3. Include code examples from your codebase

## Included Domains

### pydantic/

Data validation patterns for Python:

- Concepts: BaseModel, Field types, Validators, Nested models
- Patterns: LLM output validation, Error handling, Extraction schemas, Custom validators

### gcp/

Google Cloud Platform serverless services:

- Concepts: Cloud Run, Pub/Sub, GCS, BigQuery, IAM, Secret Manager
- Patterns: Event-driven pipelines, Multi-bucket workflows, Pub/Sub fanout, Cloud Run scaling, GCS triggers

### gemini/

Google's multimodal LLM for document processing:

- Concepts: Model capabilities, Multimodal prompting, Safety settings, Structured output, Token limits, Vertex AI
- Patterns: Batch processing, Error handling, Document extraction, OpenRouter fallback, Prompt versioning, Structured JSON

### langfuse/

LLMOps observability for tracking calls, costs, and quality:

- Concepts: Traces & spans, Generations, Cost tracking, Scoring, Prompt management, Model comparison
- Patterns: SDK integration, Serverless instrumentation, Cost alerting, Dashboard metrics, Quality feedback, Trace linking

### terraform/

Infrastructure as Code for GCP with module patterns:

- Concepts: Resources, Modules, Providers, State, Variables, Workspaces
- Patterns: Cloud Run module, Pub/Sub module, GCS module, BigQuery module, IAM module, Remote state

### terragrunt/

Terraform wrapper for multi-environment orchestration:

- Concepts: Terragrunt blocks, Root configuration, Environment hierarchy, Generate blocks, Dependencies, Hooks
- Patterns: Multi-environment config, DRY hierarchies, Dependency management, State per environment, Environment promotion

### crewai/

Multi-agent AI orchestration for automated monitoring:

- Concepts: Agents, Crews, Tasks, Tools, Memory, Processes
- Patterns: Triage workflows, Log analysis, Escalation, Slack integration, Circuit breaker, Crew coordination

### openrouter/

Unified LLM API gateway with 400+ models:

- Concepts: API basics, Authentication, Model selection, Streaming, Rate limits
- Patterns: SDK integration, Cost optimization, Error handling, Provider routing, LangChain integration

## Best Practices

1. **Be specific** - Reference actual code from your project
2. **Include examples** - Working code snippets
3. **Keep updated** - Mark stale content
4. **Cite sources** - Link to official docs

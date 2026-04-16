# CrewAI Knowledge Base

> **Purpose**: Multi-agent AI orchestration framework for autonomous DataOps monitoring and self-healing pipelines
> **MCP Validated**: 2026-02-17

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/agents.md](concepts/agents.md) | Agent definition, roles, goals, backstory |
| [concepts/crews.md](concepts/crews.md) | Crew composition and execution |
| [concepts/tasks.md](concepts/tasks.md) | Task specification and assignment |
| [concepts/tools.md](concepts/tools.md) | Tool integration with BaseTool and @tool |
| [concepts/memory.md](concepts/memory.md) | Short-term, long-term, entity memory |
| [concepts/processes.md](concepts/processes.md) | Sequential and hierarchical processes |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/triage-investigation-report.md](patterns/triage-investigation-report.md) | Three-phase DataOps triage workflow |
| [patterns/log-analysis-agent.md](patterns/log-analysis-agent.md) | Automated pipeline log analysis |
| [patterns/escalation-workflow.md](patterns/escalation-workflow.md) | Severity-based escalation with human-in-loop |
| [patterns/slack-integration.md](patterns/slack-integration.md) | Slack notification for pipeline alerts |
| [patterns/circuit-breaker.md](patterns/circuit-breaker.md) | Cost and failure circuit breaker |
| [patterns/crew-coordination.md](patterns/crew-coordination.md) | Multi-crew orchestration via Flows |

### Specs (Machine-Readable)

| File | Purpose |
|------|---------|
| [specs/crewai-config.yaml](specs/crewai-config.yaml) | Full configuration reference spec |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Fast lookup tables

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | LLM-powered process with role, goal, backstory, and tools |
| **Task** | Actionable unit assigned to an agent with expected output |
| **Crew** | Team of agents collaborating on tasks via a process |
| **Flow** | Event-driven workflow orchestrating multiple crews |
| **Tool** | External capability registered to agents at runtime |
| **Memory** | Persistent context across short-term, long-term, entity stores |

---

## Learning Path

| Level | Files |
|-------|-------|
| **Beginner** | concepts/agents.md, concepts/tasks.md, concepts/crews.md |
| **Intermediate** | concepts/tools.md, concepts/memory.md, concepts/processes.md |
| **Advanced** | patterns/triage-investigation-report.md, patterns/crew-coordination.md |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| KB-Architect | index.md, quick-reference.md | Navigation and discovery |
| DataOps-Agent | patterns/triage-investigation-report.md | Pipeline monitoring |
| Code-Gen | concepts/agents.md, concepts/tools.md | CrewAI implementation |

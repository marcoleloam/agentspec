# ShopAgent Crew

> **Purpose**: ShopAgent 3-agent CrewAI crew — AnalystAgent (SQL) + ResearchAgent (Semantic) + ReporterAgent (Synthesis)
> **MCP Validated**: 2026-04-12

## When to Use

- Day 4 multi-agent ShopAgent system
- Building the CrewAI crew with specialized e-commerce agents
- Demonstrating sequential multi-agent orchestration with MCP tools

## Implementation

```python
"""ShopAgent CrewAI crew — 3 specialized agents for e-commerce analysis."""
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class ShopAgentCrew:
    """ShopAgent multi-agent crew for e-commerce analysis."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def analyst(self) -> Agent:
        """AnalystAgent — SQL queries against The Ledger (Supabase/Postgres)."""
        return Agent(
            config=self.agents_config["analyst"],
            tools=[supabase_tool],
            verbose=True,
        )

    @agent
    def researcher(self) -> Agent:
        """ResearchAgent — Semantic search in The Memory (Qdrant)."""
        return Agent(
            config=self.agents_config["researcher"],
            tools=[qdrant_tool],
            verbose=True,
        )

    @agent
    def reporter(self) -> Agent:
        """ReporterAgent — Synthesizes findings into executive report."""
        return Agent(
            config=self.agents_config["reporter"],
            verbose=True,
        )

    @task
    def analysis_task(self) -> Task:
        return Task(config=self.tasks_config["analysis_task"])

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def report_task(self) -> Task:
        return Task(
            config=self.tasks_config["report_task"],
            context=[self.analysis_task(), self.research_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            verbose=True,
        )
```

## agents.yaml

```yaml
analyst:
  role: "E-Commerce Data Analyst"
  goal: "Extract precise metrics from the ShopAgent database using SQL queries"
  backstory: >
    You are an expert SQL analyst specialized in e-commerce data.
    You query Supabase Postgres for exact numbers: revenue, order counts,
    payment distributions, and customer segment metrics. You never guess
    numbers — every figure comes from a SQL query result.

researcher:
  role: "Customer Experience Researcher"
  goal: "Analyze customer reviews and sentiment using semantic search"
  backstory: >
    You are a customer experience researcher who understands what customers
    feel, not just what they buy. You search Qdrant for review themes,
    complaints, and sentiment patterns. You find the human story behind
    the data.

reporter:
  role: "Executive Report Writer"
  goal: "Combine analyst metrics and researcher insights into actionable reports"
  backstory: >
    You are a senior business analyst who synthesizes quantitative data
    and qualitative insights into clear, actionable executive reports.
    Your reports always include specific numbers, key findings, and
    concrete recommendations.
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| Process | `sequential` | Analyst → Researcher → Reporter (ordered) |
| Memory | `True` | Agents can reference prior task outputs |
| Analyst tool | `supabase_tool` | MCP Supabase for SQL queries |
| Researcher tool | `qdrant_tool` | MCP Qdrant for semantic search |
| Reporter tools | None | Synthesizes from context only |

## Example Usage

```python
crew = ShopAgentCrew()
result = crew.crew().kickoff(inputs={
    "question": "Relatorio de satisfacao dos clientes do Sudeste"
})

# Execution flow:
# 1. AnalystAgent → SQL: revenue, orders, segments for SP/RJ/MG/ES
# 2. ResearchAgent → Qdrant: delivery complaints, sentiment themes
# 3. ReporterAgent → Executive report combining both + recommendations
print(result)
```

## See Also

- [CrewAI Agents](../concepts/agents.md)
- [CrewAI Crews](../concepts/crews.md)
- [Chainlit CrewAI Integration](../../chainlit/patterns/crewai-integration.md)
- [LangChain Dual Tools](../../langchain/patterns/react-agent-dual-tools.md)

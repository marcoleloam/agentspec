# Crew Coordination Pattern

> **Purpose**: Orchestrating multiple specialized crews for system monitoring
> **MCP Validated**: 2026-01-25

## When to Use

- Monitoring multiple pipeline stages independently
- Parallel analysis of different log sources
- Coordinating crews with different specializations
- Building modular, reusable monitoring components

## Implementation

```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import json

# ============ SPECIALIZED CREWS ============

# --- Service Monitoring Crew ---
service_agent = Agent(
    role="Service Specialist",
    goal="Monitor service health and performance",
    backstory="Expert in service deployments, scaling, and errors.",
    llm="openai/gpt-4o-mini",
    max_iter=10
)

service_task = Task(
    description="Analyze service logs at {log_path}. Check for OOM, cold starts, and timeouts.",
    expected_output="Service health report with issues and metrics",
    agent=service_agent
)

service_crew = Crew(
    agents=[service_agent],
    tasks=[service_task],
    process=Process.sequential,
    verbose=False
)

# --- Messaging Monitoring Crew ---
messaging_agent = Agent(
    role="Messaging Specialist",
    goal="Monitor message delivery and subscription health",
    backstory="Expert in messaging patterns, dead letters, and backlog management.",
    llm="openai/gpt-4o-mini",
    max_iter=10
)

messaging_task = Task(
    description="Analyze messaging logs at {log_path}. Check for delivery failures and backlog.",
    expected_output="Messaging health report with delivery metrics",
    agent=messaging_agent
)

messaging_crew = Crew(
    agents=[messaging_agent],
    tasks=[messaging_task],
    process=Process.sequential,
    verbose=False
)

# --- Database Monitoring Crew ---
database_agent = Agent(
    role="Database Specialist",
    goal="Monitor query performance and resource utilization",
    backstory="Expert in database optimization, costs, and troubleshooting.",
    llm="openai/gpt-4o-mini",
    max_iter=10
)

database_task = Task(
    description="Analyze database logs at {log_path}. Check for slow queries and errors.",
    expected_output="Database health report with performance metrics",
    agent=database_agent
)

database_crew = Crew(
    agents=[database_agent],
    tasks=[database_task],
    process=Process.sequential,
    verbose=False
)

# ============ CREW COORDINATOR ============
class CrewCoordinator:
    """Orchestrate multiple specialized crews."""

    def __init__(self):
        self.crews = {
            "service": service_crew,
            "messaging": messaging_crew,
            "database": database_crew
        }
        self.results = {}

    def run_parallel(self, inputs: Dict[str, dict]) -> Dict[str, any]:
        """Run multiple crews in parallel.

        Args:
            inputs: Dict mapping crew name to its inputs
                   e.g., {"cloud_run": {"log_path": "..."}, ...}
        """
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for crew_name, crew_inputs in inputs.items():
                if crew_name in self.crews:
                    future = executor.submit(
                        self.crews[crew_name].kickoff,
                        inputs=crew_inputs
                    )
                    futures[future] = crew_name

            for future in as_completed(futures):
                crew_name = futures[future]
                try:
                    self.results[crew_name] = {
                        "status": "success",
                        "result": future.result()
                    }
                except Exception as e:
                    self.results[crew_name] = {
                        "status": "error",
                        "error": str(e)
                    }

        return self.results

    def run_sequential(self, inputs: Dict[str, dict]) -> Dict[str, any]:
        """Run crews sequentially with dependency handling."""
        for crew_name, crew_inputs in inputs.items():
            if crew_name in self.crews:
                try:
                    result = self.crews[crew_name].kickoff(inputs=crew_inputs)
                    self.results[crew_name] = {"status": "success", "result": result}
                except Exception as e:
                    self.results[crew_name] = {"status": "error", "error": str(e)}
                    break  # Stop on first failure

        return self.results

# ============ USAGE ============
coordinator = CrewCoordinator()

# Run all monitoring crews in parallel
results = coordinator.run_parallel({
    "service": {"log_path": "/tmp/logs/service-a.json"},
    "messaging": {"log_path": "/tmp/logs/messaging.json"},
    "database": {"log_path": "/tmp/logs/database.json"}
})

# Aggregate results
for crew_name, result in results.items():
    print(f"{crew_name}: {result['status']}")
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `max_workers` | 3 | Parallel crew limit |
| `verbose` | False | Reduce noise in parallel runs |
| `max_iter` | 10 | Per-agent iteration limit |

## Coordination Patterns

| Pattern | Use Case | Implementation |
|---------|----------|----------------|
| Parallel | Independent analysis | ThreadPoolExecutor |
| Sequential | Dependent stages | Run in order |
| Fan-out/Fan-in | Aggregate results | Parallel + merge |

## Example: Aggregated Report

```python
# After parallel execution, aggregate into single report
aggregation_agent = Agent(
    role="Report Aggregator",
    goal="Combine crew results into unified report",
    backstory="Expert at synthesizing multiple data sources."
)

aggregation_task = Task(
    description="Combine these reports into unified status: {crew_results}",
    expected_output="Single system health report",
    agent=aggregation_agent
)
```

## See Also

- [Crews Concept](../concepts/crews.md)
- [Triage Pattern](../patterns/triage-investigation-report.md)
- [Circuit Breaker](../patterns/circuit-breaker.md)

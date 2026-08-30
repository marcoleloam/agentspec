# Circuit Breaker Pattern

> **Purpose**: Prevent runaway agent costs and infinite loops with token, time, and failure circuit breakers
> **MCP Validated**: 2026-02-17

## When to Use

- Need to cap LLM token spend per crew execution
- Agents risk entering infinite reasoning loops
- Production workloads require hard cost ceilings
- Want automatic halting when error rate exceeds threshold
- Need graceful degradation when external APIs fail

## Implementation

```python
from crewai import Agent, Task, Crew, Process, Flow
from crewai.flow.flow import start, listen
from pydantic import BaseModel
import time
from typing import Optional

# --- Circuit Breaker State ---

class CircuitBreakerState(BaseModel):
    pipeline_name: str = ""
    max_cost_usd: float = 5.0
    max_duration_seconds: int = 300
    max_consecutive_failures: int = 3
    current_cost_usd: float = 0.0
    consecutive_failures: int = 0
    circuit_open: bool = False
    halt_reason: Optional[str] = None

# --- Circuit Breaker Wrapper ---

class CircuitBreakerFlow(Flow[CircuitBreakerState]):
    """Wraps crew execution with cost, time, and failure circuit breakers."""

    @start()
    def execute_with_breaker(self):
        """Run crew with circuit breaker protection."""
        start_time = time.time()

        # Pre-flight checks
        if self.state.circuit_open:
            return f"CIRCUIT OPEN: {self.state.halt_reason}"

        try:
            # Execute the monitored crew
            result = self._run_monitored_crew()

            # Post-execution cost check
            elapsed = time.time() - start_time
            if elapsed > self.state.max_duration_seconds:
                self.state.circuit_open = True
                self.state.halt_reason = (
                    f"Duration exceeded: {elapsed:.0f}s > "
                    f"{self.state.max_duration_seconds}s"
                )
                return f"CIRCUIT TRIPPED (time): {self.state.halt_reason}"

            # Check token cost from crew metrics
            if hasattr(result, "token_usage"):
                estimated_cost = self._estimate_cost(result.token_usage)
                self.state.current_cost_usd += estimated_cost
                if self.state.current_cost_usd > self.state.max_cost_usd:
                    self.state.circuit_open = True
                    self.state.halt_reason = (
                        f"Cost exceeded: ${self.state.current_cost_usd:.2f} > "
                        f"${self.state.max_cost_usd:.2f}"
                    )
                    return f"CIRCUIT TRIPPED (cost): {self.state.halt_reason}"

            # Reset failure counter on success
            self.state.consecutive_failures = 0
            return result.raw

        except Exception as e:
            self.state.consecutive_failures += 1
            if self.state.consecutive_failures >= self.state.max_consecutive_failures:
                self.state.circuit_open = True
                self.state.halt_reason = (
                    f"Consecutive failures: {self.state.consecutive_failures} "
                    f"(last: {str(e)[:200]})"
                )
                return f"CIRCUIT TRIPPED (failures): {self.state.halt_reason}"
            raise

    @listen(execute_with_breaker)
    def report_status(self, result):
        """Log circuit breaker outcome."""
        if self.state.circuit_open:
            return {
                "status": "circuit_open",
                "reason": self.state.halt_reason,
                "cost_usd": self.state.current_cost_usd,
                "failures": self.state.consecutive_failures,
            }
        return {
            "status": "success",
            "cost_usd": self.state.current_cost_usd,
            "failures": 0,
        }

    def _run_monitored_crew(self):
        """Execute the actual crew (override or inject)."""
        monitor = Agent(
            role="Pipeline Monitor",
            goal="Check pipeline health",
            backstory="You monitor data pipelines.",
            max_iter=5,  # Hard cap on iterations
            max_rpm=10,  # Rate limit API calls
        )
        task = Task(
            description=f"Check pipeline '{self.state.pipeline_name}' status",
            expected_output="Pipeline health status",
            agent=monitor,
        )
        crew = Crew(
            agents=[monitor],
            tasks=[task],
            process=Process.sequential,
            max_rpm=10,  # Crew-level rate limit
        )
        return crew.kickoff()

    def _estimate_cost(self, token_usage: dict) -> float:
        """Estimate USD cost from token usage metrics."""
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        # GPT-4o pricing estimate
        cost = (prompt_tokens * 2.5 / 1_000_000) + (completion_tokens * 10.0 / 1_000_000)
        return cost
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_cost_usd` | `5.0` | Maximum spend per execution |
| `max_duration_seconds` | `300` | Maximum wall-clock time |
| `max_consecutive_failures` | `3` | Failures before circuit opens |
| `max_iter` (agent) | `5` | Per-agent iteration cap |
| `max_rpm` (crew) | `10` | API calls per minute limit |

## Example Usage

```python
# Standard execution with circuit breaker
flow = CircuitBreakerFlow()
flow.state.pipeline_name = "daily_sales_etl"
flow.state.max_cost_usd = 2.0
flow.state.max_duration_seconds = 120

result = flow.kickoff()

# Check if circuit tripped
if flow.state.circuit_open:
    print(f"HALTED: {flow.state.halt_reason}")
    # Send alert to on-call
else:
    print(f"Success - Cost: ${flow.state.current_cost_usd:.2f}")

# Reset circuit for next run
flow.state.circuit_open = False
flow.state.consecutive_failures = 0
flow.state.current_cost_usd = 0.0
```

## Agent-Level Guardrails

```python
# Built-in CrewAI guardrails (always set these in production)
agent = Agent(
    role="Monitor",
    goal="...",
    backstory="...",
    max_iter=5,         # Hard cap on reasoning loops
    max_rpm=10,         # Rate limit API calls per minute
)

crew = Crew(
    agents=[agent],
    tasks=[task],
    max_rpm=20,         # Crew-level rate limit
    cache=True,         # Cache tool results to reduce calls
)
```

## See Also

- [Escalation Workflow](../patterns/escalation-workflow.md)
- [Crew Coordination](../patterns/crew-coordination.md)
- [Processes](../concepts/processes.md)

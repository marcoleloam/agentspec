# CrewAI Integration

> **Purpose**: Wrap ShopAgent CrewAI crew in Chainlit with per-agent step visibility
> **MCP Validated**: 2026-04-12

## When to Use

- Day 4 multi-agent Chainlit interface
- Showing AnalystAgent, ResearchAgent, and ReporterAgent as distinct expandable steps
- Real-time visibility into which agent is currently working

## Implementation

```python
"""ShopAgent Chainlit app with CrewAI multi-agent crew."""
import chainlit as cl
from crewai import Crew


@cl.on_chat_start
async def start():
    """Initialize ShopAgent crew."""
    from shopagent.crew import ShopAgentCrew

    crew_instance = ShopAgentCrew()
    cl.user_session.set("crew", crew_instance)
    await cl.Message(
        content="ShopAgent Multi-Agent pronto! 3 agentes especializados a postos."
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Run crew with per-agent step visibility."""
    crew_instance = cl.user_session.get("crew")
    crew = crew_instance.crew()
    msg = cl.Message(content="")

    # Track which agent is currently executing
    async def step_callback(step_output):
        """Called by CrewAI after each agent completes a step."""
        agent_name = step_output.agent if hasattr(step_output, "agent") else "Agent"
        task_output = str(step_output.output) if hasattr(step_output, "output") else ""

        async with cl.Step(name=str(agent_name), type="run") as step:
            step.output = task_output[:500]

    # Execute crew
    result = crew.kickoff(inputs={"question": message.content})

    # Send final response
    await cl.Message(content=str(result)).send()
```

## Agent Steps in the UI

```
User: "Relatorio de satisfacao dos clientes do Sudeste"

┌─ AnalystAgent (run)
│  Output: "Metricas do Sudeste: 1.230 pedidos, ticket medio R$ 347..."
│
├─ ResearchAgent (run)
│  Output: "23 reviews negativos sobre entrega, 15 sobre prazo..."
│
└─ ReporterAgent (run)
   Output: "Relatorio executivo consolidado com recomendacoes..."

Final: "Relatorio de Satisfacao - Sudeste
       23 clientes com problemas de entrega.
       Ticket medio: R$ 347,82 (75% acima da media).
       Recomendacoes: 1) Melhorar logistica SP-interior..."
```

## Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| `Step type` | `"run"` | Shows play icon for agent execution |
| `step.output` truncation | 500 chars | Prevent UI overflow for long agent outputs |
| Crew process | `Process.sequential` | Agents execute in order: Analyst → Researcher → Reporter |

## Example Usage

```bash
# Run
chainlit run app.py -w

# Questions that trigger all 3 agents:
# "Relatorio completo de satisfacao do cliente"
# "Analise de vendas e sentimento por estado"
# "Quais estados tem mais reclamacoes e qual o impacto no faturamento?"
```

## See Also

- [LangChain Integration](../patterns/langchain-integration.md)
- [CrewAI ShopAgent Crew](../../crewai/patterns/shopagent-crew.md)

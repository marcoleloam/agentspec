# Agent Selection Rubric

> Single source of the rubric the phase LLM applies in `/define`, `/design`, `/define-m` and `/design-m`
> (Step 1b / Specialist Selection). `scripts/eval_llm_baseline.py` reads the block below verbatim, so the
> rubric shipped here is the one that was measured. Edit it only together with a new measurement.

## Rubric

<!-- rubric:start -->
VARIANT — pick exactly one:
- single: the implementation work is confined to ONE technical area (for example: only frontend screens
  with mock data, only infrastructure or configuration changes, only a written document); other
  technologies are mocked, unchanged or only mentioned.
- multiagent: two or more areas (for example frontend AND backend/database AND AI) each need real new
  implementation.

SPECIALISTS — list up to 4 agent names from the catalog whose expertise would materially
change the quality of this phase for this spec (list them even when the variant is single; use [] if none).
Use names exactly as written in the catalog.
<!-- rubric:end -->

## Catalog

Every agent in `.claude/skills/agent-router/routing.json` outside the `workflow` and `domain` categories
(59 agents on 2026-09-25), each as `- name: description`. The `agent-router` skill lists the same agents.

## How to Apply (phase LLM)

1. Read the input document (BRAINSTORM for `/define`, DEFINE for `/design`) — decide from its content,
   not from the length of its "Domínios KB" line.
2. Answer the rubric: one variant, up to 4 specialists, names exactly as in the catalog.
3. Record the answer in the **Seleção de Agentes** section with one line of justification per decision.

## Evidence (2026-09-25, 46 labeled specs — see BUILD_REPORT_JEV_AGENT_SELECTION.md)

| Decider | Variant accuracy | Specialist F1 |
|---------|------------------|---------------|
| Old rule (3+ KB domains; top 4 by overlap) | 0.46 | 0.19 |
| JEV v1.2 (`scripts/jev_select.py`) | 0.72 | 0.38 |
| LLM with this rubric — Grok (`grok-4.7-build`) | 0.85 | 0.47 |
| LLM with this rubric — Codex (`gpt-6-astra`) | 0.89 | 0.52 |

Labels were written by the build agent (Claude); Claude itself was not measured as the decider.

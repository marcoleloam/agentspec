# Agent Selection (Rubric + Optional JEV Second Opinion)

Before doing any work, `/define` and `/design` decide two things from the spec they receive:

1. **Which variant runs.** Either `single` (define-agent / design-agent) or `multiagent` (the `-m` process that consults specialists).
2. **Which specialists are consulted.** At most 4.

The **phase LLM** makes both decisions by applying one shared rubric,
`.claude/sdd/architecture/AGENT_SELECTION_RUBRIC.md`. Every generated DEFINE and DESIGN records the outcome in a
**Seleção de Agentes** section: the variant with a one-line justification, and each specialist with a one-line reason.

## Why a Rubric (and Not the Old Rule or JEV)

On 46 labeled specs (template DEFINEs, specs written outside the template, and raw PRDs; 2026-09-25):

| Decider | Variant accuracy | Specialist F1 | Cost per phase |
|---------|------------------|---------------|----------------|
| Old rule: 3+ KB domains → multiagent; top 4 by `kb_domains` overlap | 0.46 | 0.19 | — |
| JEV v1.2 (`scripts/jev_select.py`, TypeSafe via OpenRouter) | 0.72 | 0.38 | ~1 s, ~US$ 0.00015 |
| LLM applying the rubric — Grok `grok-4.7-build` | 0.85 | 0.47 | ~85 s outside a session |
| LLM applying the rubric — Codex `gpt-6-astra` | 0.89 | 0.52 | ~10 s outside a session |

The old rule breaks on documents without a "Domínios KB" line: it always answers `single` and finds no specialists.
Inside `/define` and `/design` an LLM is already running the phase, so applying the rubric adds almost no cost.
The full method, the caveats and the label hashes are in `.claude/sdd/reports/BUILD_REPORT_JEV_AGENT_SELECTION.md`.
One caveat: the labels were written by Claude, and Claude itself was not measured as the decider.

| Command | Variant | Specialists |
|---------|---------|-------------|
| `/define`, `/design` | Rubric (may switch to the `-m` process) | Rubric |
| `/define-m`, `/design-m` | Locked to multiagent (never downgraded) | Rubric |

## Optional: JEV Second Opinion

JEV beat the old rule in every measured set, and it answers in about 1 s for a fraction of a cent. To collect its
opinion alongside the rubric decision:

```bash
export JEV_SECOND_OPINION=1
export OPENROUTER_API_KEY=sk-or-v1-...
```

The commands then also run `scripts/jev_select.py` and record its variant and specialists in **Seleção de Agentes**.
**The rubric decision always stands**; JEV never switches the variant.

`jev_select.py` makes two calls:

1. a `single_area` Noul plus a `rank` Choice over every specialist, keeping the top 8 with probability above 0;
2. one Noul per shortlisted agent: the python/react developers, the top ranked and the agents sharing a KB domain, 12 at most.

It always exits 0 and falls back to the old rule on any failure. The reason for the fallback is recorded.

```bash
python3 scripts/jev_select.py <<'JSON'
{"phase": "design", "summary": "Daily orders ETL from Postgres to Snowflake with dbt marts",
 "kb_domains": ["dbt", "`sql/postgres`", "airflow"], "variant_locked": null}
JSON
```

`kb_domains` may be copied verbatim from a spec; free text such as `tailwind`, `a11y` or `sql/postgres` is normalized
to KB names, and unknown names are listed in `kb_domains_dropped`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `JEV_SECOND_OPINION` | unset | `1` makes the phase commands also run `jev_select.py` |
| `OPENROUTER_API_KEY` / `JEV_API_KEY` | — | Key for the JEV call (`JEV_API_KEY` wins) |
| `JEV_URL` | `https://openrouter.ai/api/alpha/decisions` | Endpoint (`https://api.typesafe.ai/v1/systemone` for TypeSafe direct) |
| `JEV_MODEL` | `typesafe/jev-1.13` | Model (`jev-1.13.0` for TypeSafe direct) |
| `JEV_SINGLE_THRESHOLD` / `JEV_UNCERTAIN_BAND` | `0.5` / `0.1` | Variant gate on `p(single)`; inside the band the old rule decides |
| `JEV_FIT_THRESHOLD` | `0.5` | Specialist gate |
| `JEV_TIMEOUT_MS` | `4000` | Total budget for both calls |
| `JEV_DISABLE` | unset | `1` means never send anything; always the old rule |

**What leaves your machine** when the second opinion runs:
- a spec summary of up to 4000 characters;
- the spec's KB domain names;
- the names and one-line descriptions of AgentSpec's specialist agents.

It goes to OpenRouter, which forwards it to TypeSafe.

## Measuring a Change

Two tools share the labeled-set format of `tests/fixtures/agent_selection/labels_sample.json`:

```bash
# JEV against the old rule
python3 scripts/jev_select.py --eval labels.json

# An LLM applying the shipped rubric (Codex or Grok headless, via your subscription)
python3 scripts/eval_llm_baseline.py --provider codex --labels labels.json
```

`eval_llm_baseline.py` reads the rubric from `AGENT_SELECTION_RUBRIC.md`, so what you measure is what the commands
apply. Change the rubric only together with a new measurement, on specs that were not used to write the change.
Keep labeled sets that contain client specs out of git (`.claude/sdd/evals/` is ignored for them).

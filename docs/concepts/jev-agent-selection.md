# JEV Agent Selection

`/define` and `/design` decide two things from the spec they receive before doing any work:

1. **Which variant runs.** Either `single` (define-agent / design-agent) or `multiagent` (the `-m` process that consults specialists).
2. **Which specialists are consulted.** At most 4, when the variant is multiagent.

The decision comes from **JEV**, TypeSafe's decision model, called through OpenRouter. JEV does not generate text. It answers typed questions with calibrated probabilities. When JEV cannot decide, AgentSpec falls back to the rule it used before: 3+ KB domains means multiagent, and the specialists are the top 4 agents by `kb_domains` overlap. The phase never blocks.

Every generated DEFINE and DESIGN records the outcome in a **Seleção de Agentes** section: variant, source (`jev`, `fallback` or `locked`), `p(single)`, specialists with their probabilities, and the heuristic's answer for comparison.

## How It Works

```text
spec (BRAINSTORM or DEFINE)
   │  phase agent writes a ≤4000-char summary + the spec's KB domains
   ▼
scripts/jev_select.py
   │  call 1: single_area (Noul) + rank (Choice over every specialist, top 8)
   │  shortlist ≤ 12: python/react developers + top 8 ranked + agents sharing a KB domain
   │  call 2: fit_i (Noul per shortlisted specialist)
   ▼
gate
   ├─ p(single) ≥ 0.6 → single; ≤ 0.4 → multiagent; in between → heuristic ("uncertain")
   ├─ Noul ≥ 0.5, best 4                → JEV's specialists
   └─ anything else                     → heuristic, with the reason recorded
```

| Command | Variant | Specialists |
|---------|---------|-------------|
| `/define`, `/design` | Decided by JEV (may switch to the `-m` process) | Decided by JEV |
| `/define-m`, `/design-m` | Locked to multiagent (never downgraded) | Decided by JEV |

> **Behavior change:** `/define-m` and `/design-m` used to fall back to the single variant when a spec had fewer than 3 KB domains. An explicit `-m` now always runs multiagent.

## Setup

JEV uses the same key as the Judge Layer:

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

With no key set, everything still works: selection runs on the heuristic and the document records `fallback (missing_key)`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | — | Key for the JEV call |
| `JEV_API_KEY` | — | Takes precedence over `OPENROUTER_API_KEY` (e.g. a direct TypeSafe key) |
| `JEV_URL` | `https://openrouter.ai/api/alpha/decisions` | Endpoint (`https://api.typesafe.ai/v1/systemone` for TypeSafe direct) |
| `JEV_MODEL` | `typesafe/jev-1.13` | Model (`jev-1.13.0` for TypeSafe direct) |
| `JEV_SINGLE_THRESHOLD` | `0.5` | `p(single)` at or above → single |
| `JEV_UNCERTAIN_BAND` | `0.1` | Distance to the threshold below which the heuristic decides |
| `JEV_FIT_THRESHOLD` | `0.5` | Specialist gate |
| `JEV_TIMEOUT_MS` | `4000` | Total wall-clock budget for the call |
| `JEV_DISABLE` | unset | `1` means never send anything; always use the heuristic |

## What Leaves Your Machine

When a key is set and `JEV_DISABLE` is not, the request sends:

- a summary of the spec (at most 4000 characters);
- the spec's KB domain names;
- the names and one-line descriptions of AgentSpec's specialist agents (about 60 in the ranking call, up to 12 in the second).

It goes to OpenRouter, which forwards it to TypeSafe. Set `JEV_DISABLE=1` for projects whose specs must not leave the machine.

## Try It

```bash
python3 scripts/jev_select.py <<'JSON'
{"phase": "design", "summary": "Daily orders ETL from Postgres to Snowflake with dbt marts",
 "kb_domains": ["dbt", "sql-patterns", "airflow"], "variant_locked": null}
JSON
```

The script always exits 0. A diagnostic line (`[jev_select] source=… reason=… latency_ms=…`) goes to stderr.

## Measuring It

`--eval` runs the selector on a labeled set and compares it with the heuristic:

```bash
python3 scripts/jev_select.py --eval .claude/sdd/evals/agent_selection_labels.json
```

The feature targets are:

- variant accuracy ≥ 85%, and at least 10 points above the heuristic;
- mean specialist F1 at least 0.10 above the heuristic, on multiagent cases.

The labels format lives in `tests/fixtures/agent_selection/labels_sample.json`. Keep the full labeled set out of git (it is ignored by default) when it contains client specs.

## Known Limits

- **Measured quality (2026-09-24).** On 22 labeled specs, the original Choice question answered `multiagent` for every spec, so variant accuracy equaled the heuristic's (0.64). The v1.1 Noul question replaced it and was then measured on a fresh holdout. See the build report for the numbers before relying on the variant decision.

- **Two calls per phase.** The ranking call removes the dependency on the spec's KB domain line; `JEV_TIMEOUT_MS` bounds both calls together.
- **Local agent overrides are not candidates.** Candidates come from AgentSpec's generated `routing.json`, so agents in your project's `.claude/agents/` are not considered.
- **Alpha endpoint.** The OpenRouter `alpha/decisions` endpoint may change. The model version is pinned, and any failure falls back to the heuristic.
- **Codex and DeepSeek Harness bundles.** These bundles do not ship the script, so the commands apply the heuristic by hand and record `fallback (script_unavailable)`.

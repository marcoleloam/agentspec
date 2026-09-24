---
name: eval
description: Independent post-build acceptance gate — re-run the DESIGN's eval contract and produce the receipt /ship requires (Phase 3.5)
---

# Eval Command

> Re-execute the frozen eval contract against the current code, route pending decisions to a human,
> and write the receipt that `/ship` requires (Phase 3.5).

## Usage

```bash
/eval                     # Active feature (.claude/sdd/.active)
/eval FEATURE_NAME        # Specific feature
/eval FEATURE_NAME --escalate human   # Decide graded evals yourself instead of judge.py
```

> With no argument, use the feature in `.claude/sdd/.active` (set by `/work` or `/build`).
> If there is none, ask the user which feature to evaluate.

---

## Overview

```text
Phase 0: /brainstorm → .claude/sdd/features/BRAINSTORM_{FEATURE}.md (optional)
Phase 1: /define     → .claude/sdd/features/DEFINE_{FEATURE}.md
Phase 2: /design     → .claude/sdd/features/DESIGN_{FEATURE}.md   (## Evals authored + frozen)
Phase 3: /build      → Code + .claude/sdd/reports/BUILD_REPORT_{FEATURE}.md   (pre-check)
Phase 3.5: /eval     → .claude/sdd/reports/EVAL_{FEATURE}.json + EVAL_REPORT_{FEATURE}.md (THIS COMMAND)
Phase 4: /ship       → .claude/sdd/archive/{FEATURE}/SHIPPED_{DATE}.md   (refuses without PASS)
```

The build agent's own acceptance table is self-verification. `/eval` is the independent acceptance:
a deterministic runner re-executes the contract, and the report is rendered from the receipt, so it
cannot disagree with it.

---

## What This Command Does

1. **Run** — `eval_runner.py run` checks the contract digest, executes every eval, writes the receipt and the report
2. **Decide** — deterministic evals by exit code; graded evals by JEV (only once calibrated), else `judge.py`, else a human; human evals by attestation
3. **Attest** — asks owners about pending evals and records their answer (or a named waiver)
4. **Report** — verdict + next step (`/ship` or `/continuar`)

---

## Process

Delegate to the **eval-agent** (`${CLAUDE_PLUGIN_ROOT}/agents/workflow/eval-agent.md`). The agent:

### Step 1: Load Context

```markdown
Read(.claude/sdd/features/DEFINE_{FEATURE}.md)        → acceptance tests
Read(.claude/sdd/features/DESIGN_{FEATURE}.md)        → ## Evals contract (read-only)
Read(.claude/sdd/reports/BUILD_REPORT_{FEATURE}.md)   → context only, never evidence
```

### Step 2: Complementary Evals (optional)

Write additive evals to `.claude/sdd/features/EVALS_EXTRA_{FEATURE}.toml` only (deterministic or graded).

### Step 3: Run

```bash
"${AGENTSPEC_PYTHON:-python3}" "${CLAUDE_PLUGIN_ROOT:-.}/scripts/eval_runner.py" run {FEATURE}
```

### Step 4: Resolve Pending Evals

Ask each owner (AskUserQuestion), then `attest` or `waive`, then run again:

```bash
"${AGENTSPEC_PYTHON:-python3}" "${CLAUDE_PLUGIN_ROOT:-.}/scripts/eval_runner.py" attest {FEATURE} --eval {id} --verdict pass --owner "{name}" --evidence "{what was checked}" --recorded-via eval-agent
"${AGENTSPEC_PYTHON:-python3}" "${CLAUDE_PLUGIN_ROOT:-.}/scripts/eval_runner.py" waive {FEATURE} --eval {id} --supervisor "{name}" --reason "{why}"
"${AGENTSPEC_PYTHON:-python3}" "${CLAUDE_PLUGIN_ROOT:-.}/scripts/eval_runner.py" run {FEATURE}
```

### Step 5: Report

Summarise `EVAL_REPORT_{FEATURE}.md` and give the next step.

---

## Output

| Artifact | Location |
|----------|----------|
| **Eval receipt** (`agentspec/eval-receipt/v1`) | `.claude/sdd/reports/EVAL_{FEATURE}.json` |
| **Eval report** (pt-BR, generated) | `.claude/sdd/reports/EVAL_REPORT_{FEATURE}.md` |
| **Attestations and waivers** | `.claude/sdd/reports/EVAL_{FEATURE}.attestations.json` |
| **Complementary evals** (optional) | `.claude/sdd/features/EVALS_EXTRA_{FEATURE}.toml` |

**Next Step:** PASS → `/ship .claude/sdd/features/DEFINE_{FEATURE}.md` · FAIL → `/continuar {FEATURE}` then `/eval` again

---

## Exit Codes of `eval_runner.py run`

| Exit | Meaning |
|------|---------|
| `0` | PASS — every required eval is `pass` or `waived` |
| `1` | FAIL — an eval failed, errored, or is pending; or `CONTRACT_TAMPERED` |
| `2` | Environment — Python < 3.11, not a git repo, missing DESIGN or template |
| `3` | Structural — orphan AT, invalid TOML, missing Evals Digest, invalid eval |

---

## Quality Gate

```text
[ ] Runner executed on the current code (not a previous receipt)
[ ] Only EVALS_EXTRA_{FEATURE}.toml written by the agent
[ ] Every attestation/waiver came from an explicit user answer
[ ] Verdict reported exactly as the receipt states
```

---

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGENTSPEC_PYTHON` | `python3` | Interpreter (≥ 3.11) that runs the runner and is exported to evals |
| `OPENROUTER_API_KEY` | — | JEV and `judge.py` (graded evals). Without it, graded evals go to a human |
| `JEV_MODEL` | `typesafe/jev-1.13` | JEV model |
| `JEV_BUDGET` | `200` | Max JEV calls per UTC day |

JEV decides a graded eval only after `eval_runner.py calibrate` approved it for the current model
(`.claude/sdd/evals/JEV_CALIBRATION.json`). See `docs/concepts/post-build-evals.md`.

---

## References

- Agent: `${CLAUDE_PLUGIN_ROOT}/agents/workflow/eval-agent.md`
- Runner: `scripts/eval_runner.py`, JEV client: `scripts/jev_client.py`
- Template: `${CLAUDE_PLUGIN_ROOT}/sdd/templates/EVAL_REPORT_TEMPLATE.md`
- Contracts: `${CLAUDE_PLUGIN_ROOT}/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Previous: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/build.md` · Next: `${CLAUDE_PLUGIN_ROOT}/commands/workflow/ship.md`

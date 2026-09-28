# Post-Build Evals — the `/eval` Gate

AgentSpec's Acceptance Tests used to be reprove­d by the same agent that built the
feature, in prose, inside the BUILD_REPORT. `/eval` turns them into an executable
gate: evals are declared in the DESIGN *before* any code exists, frozen by digest,
checked before the build, and reexecuted after the build by an agent that cannot
edit code. `/ship` refuses without a passing receipt.

## Why This Exists

`archive/KB_EVOLUTION/BUILD_REPORT_KB_EVOLUTION.md` shipped with all 6 Acceptance
Tests marked `⏳ Runtime — Validar executando…` — never actually run.
`archive/FRONTEND_ECOSYSTEM/` shipped with no AT table filled in at all. In both
cases the `pre_ship_checklist`'s `acceptance_tests_verified` only checked that the
BUILD_REPORT *existed*, not that its claims were true. `/eval` closes that gap: the
verdict comes from a deterministic runner (`scripts/eval_runner.py`), not from an
LLM's self-report.

## Write-Before, Run-After

Evals are authored **before** the code they will check exists:

1. **`/design`** — design-agent reads the DEFINE's Acceptance Tests and writes a
   `## Evals` TOML block, one eval per AT at minimum. It runs
   `eval_runner.py validate` (structural checks) then `eval_runner.py freeze`
   (writes the **Evals Digest** into the DESIGN metadata and appends the first
   entry of the freeze ledger `EVAL_{F}.freeze.log`).
2. **`/build`** — before generating any code, build-agent runs
   `eval_runner.py pre`. Every `deterministic` eval must run *cleanly and fail*: a
   bash error blocks the build (the eval can't discriminate anything yet), and an
   eval that already passes only warns (it may be checking the wrong thing). The
   outcome is persisted as the PRE receipt `EVAL_{F}.pre.json`.
3. **`/eval`** (this feature's new phase, between `/build` and `/ship`) —
   eval-agent (no `Write`/`Edit` tool) runs `eval_runner.py run`, which reexecutes
   every eval against the actual implementation and writes the sealed receipt.
4. **`/ship`** — ship-agent runs `eval_runner.py verify`; a non-`OK` code blocks
   the archive.

This ordering is the point: nobody can write a test that already matches the code,
because the test is committed to the DESIGN and frozen before the code is written.

## The TOML Contract

Evals live in the DESIGN document, inside a single fenced block that immediately
follows the `<!-- agentspec:evals:contract -->` marker (markers inside other fenced
code blocks — e.g. documentation examples — don't count). `eval_runner.py` parses
it with `tomllib` (stdlib, Python ≥ 3.11):

````markdown
## Evals

<!-- agentspec:evals:contract -->
```toml
[gate]
required = ["eval_1", "eval_2", "eval_3"]   # optional; default = every eval. Never empty,
                                            # and every AT in `verifies` needs a required eval

[[eval]]
id = "eval_1"
verifies = ["AT-001"]
check_type = "deterministic"
description = "Config file registers the new field"
timeout_sec = 60
run = '''
grep -q "new_field" config.yaml
'''

[[eval]]
id = "eval_2"
verifies = ["AT-003"]
check_type = "graded"
description = "Lint report cites the deprecated API by file and line"

[eval.state]                     # named field -> bash command whose stdout is the value
report = "cat .claude/kb/dbt/LINT_REPORT.md"
fixture = "cat tests/fixtures/deprecated_api.md"

[[eval.questions]]
id = "lists_stale"
type = "noul"                    # yes/no probability
instructions = "Does `report` list the API deprecated in `fixture` as an issue of type 'stale'?"

[[eval.questions]]
id = "cites_location"
type = "score"                   # ordered rubric level
instructions = "How precisely does `report` cite the file and line of that issue?"
criteria = ["no citation", "file only", "file and line"]

[[eval]]
id = "eval_3"
verifies = ["AT-002"]
check_type = "human"
owner = "Marco"
description = "Domain without Context7 coverage is detected and nothing is changed"
instructions = "Run /ingest-kb medallion and confirm the fallback message and a clean git status."
```
````

### Check Types

| `check_type` | How it's decided | Required fields |
|---|---|---|
| `deterministic` | `bash -c` in an isolated subprocess; exit 0 = pass | `run` (must pass `bash -n`) |
| `graded` | JEV answers typed questions about a `state`; may escalate to `judge.py` or a human | `state` (≥ 1 field), 2–5 `questions` with ≥ 1 `score` question |
| `human` | A person records a verdict via `attest` | `owner`, `instructions` |

`eval-agent` may also add evals of its own in a sibling `EVALS_EXTRA_{F}.toml` file
(`origin: complementary`), limited to `deterministic` and `graded` — it never gets
a `human` type, because it can't act as the human. It does so through
`eval_runner.py extra <F>` (TOML on stdin or `--file`), which validates the new
evals (new ids, `[[eval]]` tables only, no `[gate]`) and appends them — existing
extras are never rewritten. Complementary evals are required by the gate exactly
like contract evals.

### Structural Validation (`eval_runner.py validate`)

| Rule | Severity |
|---|---|
| Exactly one contract marker outside fenced blocks, followed by a ` ```toml ` block | error (`NO_CONTRACT` / `MULTIPLE_CONTRACTS` / `CONTRACT_NOT_TOML` / `CONTRACT_UNTERMINATED`) |
| Every AT in the DEFINE's table has ≥ 1 eval with it in `verifies` | error (`ORPHAN_AT`) |
| Every `verifies` entry points at an AT that actually exists | error (`UNKNOWN_AT`) |
| The contract declares at least one `[[eval]]` | error (`NO_EVALS`) |
| `[gate] required`, when present, is non-empty, names existing evals, and covers every AT referenced by a contract eval (extras always count as required) | error (`EMPTY_REQUIRED` / `UNKNOWN_REQUIRED` / `UNGATED_AT`) |
| `id` matches `[A-Za-z_][A-Za-z0-9_]*`, unique across contract + extras | error (`INVALID_ID` / `DUPLICATE_ID`) |
| `check_type` ∈ `deterministic \| graded \| human` (contract); extras may not be `human` | error (`INVALID_CHECK_TYPE`) |
| `deterministic`: non-empty `run`, valid bash syntax | error (`MISSING_RUN` / `BASH_SYNTAX`) |
| `graded`: non-empty `state`, 2–5 questions, ≥ 1 `score` question with 2–10 `criteria`, unique question ids | error (`MISSING_STATE` / `QUESTION_COUNT` / `MISSING_SCORE` / `SCORE_CRITERIA` / `DUPLICATE_QUESTION`) |
| `human`: `owner` and `instructions` present | error (`MISSING_OWNER` / `MISSING_INSTRUCTIONS`) |
| A `state` command's text matches `.env`, `.pem`, `secret`, or `credential` | warning (`SENSITIVE_STATE`) |
| > 50% of contract evals are `graded` | warning (`TOO_MANY_GRADED`) |
| Every line of `run` is only an existence check (`test -[efdsr]`, `[ -[efdsr]`) | warning (`EXISTENCE_ONLY`) |

## Freeze and Digest

`eval_runner.py freeze <F>` computes `canonical_digest()` — a `sha256:` hash of the
parsed contract (`json.dumps(..., sort_keys=True, separators=(",", ":"))`) — and
writes it into the DESIGN's metadata table as `**Evals Digest**`. Because the
digest is over the *parsed* TOML, reformatting or adding comments doesn't change
it, but any semantic edit does. Only `design-agent` and `iterate-agent` should ever
run `freeze`; `run` recomputes the digest and refuses with `CONTRACT_TAMPERED` if
it no longer matches the frozen value.

### Re-freeze and the Freeze Ledger

Once a DESIGN has a frozen digest (or a freeze ledger), `freeze` **refuses** to
change it (`REFREEZE_NEEDS_REASON`, exit 1) unless it gets
`--reason "<why the evals changed>"` of at least 30 characters — the `/iterate`
path. Re-running `freeze` on an unchanged contract is a no-op.

Every freeze that changes the digest — the initial one and every re-freeze — is
appended to `.claude/sdd/features/EVAL_{F}.freeze.log` (JSONL, schema
`agentspec/eval-freeze/v1`):

```json
{"schema": "agentspec/eval-freeze/v1", "ts": "2026-09-28T12:00:00.123456+00:00",
 "feature": "KB_EVOLUTION", "kind": "refreeze", "old_digest": "sha256:…",
 "new_digest": "sha256:…", "reason": "eval_2 now checks the line number too",
 "git_user_email": "marco@…", "commit": "3f2c1ab…", "runner_version": "1.1.0",
 "prev": "sha256:<digest of the previous entry>"}
```

The runner only ever appends, and each entry carries the digest of the previous
one (`prev`), so deleting or editing a past line breaks the chain
(`FREEZE_LOG_BROKEN`). `run` and `verify` also require the DESIGN's Evals Digest to
equal the ledger's last `new_digest` (`LEDGER_MISMATCH` — the digest row was edited
without `freeze`). Every re-freeze shows up as a `REFROZEN` warning in the receipt
and the report, with who, when, and why. The ledger lives next to the DESIGN and
moves with it to the archive on `/ship`.

## `/eval run`

`eval_runner.py run <F>` (invoked by `eval-agent`):

1. Legacy DESIGN (no contract block)? Requires a `waive --legacy` matching the
   current repo state, or refuses with `LEGACY_NO_EVALS`.
2. Recomputes the contract digest and compares it to the frozen one and to the
   freeze ledger (`CONTRACT_NOT_FROZEN` / `CONTRACT_TAMPERED` / `LEDGER_MISMATCH` /
   `FREEZE_LOG_BROKEN` — these are structural errors, so `run` stops before
   executing anything). Reads the PRE receipt: none on record → `NO_PRE_RECEIPT`
   warning; one for another contract → `PRE_STALE`. These warn, never block, so
   features built before the PRE receipt existed still run.
3. Runs every contract + complementary eval:
   - `deterministic` → isolated `bash -c 'set -euo pipefail\n...'`, with
     `OPENROUTER_API_KEY` stripped from the subprocess env and
     `AGENTSPEC_PYTHON` (the interpreter running the eval runner itself, so evals
     that shell out to Python don't accidentally hit a different one) injected.
   - `graded` → collects `state` by running each field's command, then asks JEV
     (see below); if JEV can't decide, escalates to `judge.py` or leaves the eval
     `pending` for a human via `attest`.
   - `human` → `pending` unless a matching attestation exists for the *current*
     commit/worktree/contract state.
4. Applies any waivers on top of the result.
5. Writes `EVAL_{F}.json` (the receipt, sealed with an integrity digest) and renders `EVAL_REPORT_{F}.md` from
   `.claude/sdd/templates/EVAL_REPORT_TEMPLATE.md` — the runner writes the report,
   not the agent, so the human-readable document can never diverge from the
   receipt it's rendered from.

**Gate:** `verdict = PASS` iff every eval in `[gate] required` (default: every
contract + complementary eval) has status `pass` or `waived`, and there are no
structural errors. There's no boolean expression — only AND — by design.

### The Receipt (`agentspec/eval-receipt/v1`)

```json
{
  "schema": "agentspec/eval-receipt/v1",
  "feature": "KB_EVOLUTION",
  "commit": "3f2c1ab…",
  "worktree_digest": "sha256:…",
  "contract_digest": "sha256:…",
  "extras_digest": null,
  "evaluated_at": "2026-09-24T14:03:11Z",
  "runner_version": "1.1.0",
  "jev": { "model": "typesafe/jev-1.13", "calibrated": false },
  "results": [
    { "eval_id": "eval_1", "origin": "contract", "verifies": ["AT-001"],
      "check_type": "deterministic", "status": "pass", "exit_code": 0,
      "duration_sec": 0.12, "evidence": { "stdout": "", "stderr": "" } }
  ],
  "required": ["eval_1", "eval_2", "eval_3"],
  "structural_errors": [],
  "warnings": [],
  "waivers": [],
  "verdict": "PASS",
  "freeze_ledger": { "entries": 1, "last_digest": "sha256:…", "last_entry": "sha256:…" },
  "pre_check": { "present": true, "outcome": "OK", "checked_at": "…", "contract_digest": "sha256:…", "commit": "…" },
  "integrity": { "algorithm": "sha256-canonical-json/v1", "digest": "sha256:…" }
}
```

`integrity.digest` is a sha256 over the canonical JSON of every field the gate
depends on (`results`, `required`, `verdict`, the commit/worktree/contract/extras
digests, `freeze_ledger`, `pre_check`, waivers). It is **not a signature**: there
is no secret, so anyone who can run `eval_runner.integrity_digest()` can re-seal an
edited receipt. It catches hand edits (flipping `verdict` to `PASS`) and partial
rewrites. What stops a deliberately forged receipt is that `verify` never trusts
the stored verdict — see below.

`worktree_digest` covers `git diff HEAD --binary` **and** every untracked file,
so uncommitted edits invalidate the receipt exactly like a new commit does. It
excludes only workflow state that legitimately changes between `/eval` and
`/ship`: `.claude/sdd/features/`, `.claude/sdd/reports/`, `.claude/sdd/archive/`,
`.claude/sdd/MEMORY.md` and `.claude/storage/`. Everything else under
`.claude/sdd/` — `templates/`, `architecture/`, `evals/` — is product code and is
covered. **Gitignored files are never covered** (`git ls-files --others
--exclude-standard`): an eval that reads a gitignored file (a local `.env`, a
build output under `dist/`) can change result without changing the digest. Use
`verify --rerun` when that matters. Status
per eval is one of `pass | fail | error | escalated | pending | waived`;
`escalated` is only ever an intermediate state — the final receipt resolves it to
`pass`/`fail` (via judge) or `pending` (needs a human).

### `attest`, `waive`, and Legacy Features

| Command | Applies to | Effect |
|---|---|---|
| `eval_runner.py attest <F> --eval ID --verdict pass\|fail --owner NAME --evidence TEXT` | `human` or a `pending` `graded` eval (never `deterministic` — `NOT_ATTESTABLE`) | Records the verdict for the *current* commit/worktree/contract. `run` picks it up next time. |
| `eval_runner.py waive <F> --eval ID --supervisor NAME --reason TEXT` | Any non-`pass` eval | Marks it `waived` and lets the gate pass with the reason on record. A `deterministic` eval needs a `--reason` of ≥ 30 characters (`REASON_TOO_SHORT`). |
| `eval_runner.py waive <F> --legacy --supervisor NAME --reason TEXT` | A DESIGN with no `## Evals` block at all | The only way a legacy feature ships — `verify` returns `OK_LEGACY_WAIVED` instead of `OK`. Also needs a ≥ 30-character reason. |

`--owner` and `--supervisor` must name a person: agent, model and harness names
(`build-agent`, `eval-agent`, anything ending in `-agent`, `Claude`, `Codex`,
`GPT…`, `Gemini`, `assistant`, `bot`, …) are refused with `NOT_A_HUMAN`. Both
commands also stamp `recorded_by_email` from `git config user.email`, shown next to
the supervisor in the report. This is a speed bump, not identity proof — a session
can type a person's name, and `git config` is local. Old attestation files without
these fields remain readable.

Attestations and waivers are stamped with `commit` + `worktree_digest` +
`contract_digest` at the time they were recorded. If the code or contract changes
afterward, `run` marks the eval `pending` again with reason `STALE_ATTESTATION` —
an old human sign-off never silently carries over a new diff.

## `verify` — the `/ship` Gate

`verify` never trusts the receipt's stored `verdict`. It recomputes the gate from
the receipt's `results` against the **current** contract's required ids: every
required eval must have exactly one result, of the contract's `check_type`, with
status `pass` (a `deterministic` pass must carry `exit_code: 0`) or `waived`. Every
`human` pass (or graded pass `decided_by: human`) must be backed by the latest
attestation for that eval in `EVAL_{F}.attestations.json`, and every waiver by the
latest waiver entry — both stamped with the receipt's own commit, worktree and
contract digests. `verify --rerun` additionally re-executes every required
`deterministic` eval and refuses if one no longer passes. Graded passes decided by
JEV or `judge.py` cannot be re-checked offline and are accepted as recorded.

| Exit | Code | Meaning |
|---|---|---|
| 0 | `OK` | Sealed receipt, recomputed gate passes, matches HEAD, the worktree, the frozen contract and the freeze ledger — ready to ship |
| 0 | `OK_LEGACY_RECEIPT` | Same, for an unsealed receipt written by runner 1.0.0 on a DESIGN that has no freeze ledger (frozen before 1.1) |
| 0 | `OK_LEGACY_WAIVED` | Legacy DESIGN, shipped under a named `--legacy` waiver backed by the attestations file |
| 1 | `NO_RECEIPT` | No `/eval` has run yet |
| 1 | `RECEIPT_INVALID` | Receipt is not JSON of schema `agentspec/eval-receipt/v1` |
| 1 | `INTEGRITY_MISMATCH` | The receipt was edited after the runner sealed it |
| 1 | `UNSEALED_RECEIPT` | No seal, but the DESIGN has a freeze ledger (so the receipt cannot predate 1.1) |
| 1 | `VERDICT_FAIL` | Receipt exists but `verdict != PASS` |
| 1 | `STALE_COMMIT` | HEAD moved since `/eval` |
| 1 | `STALE_WORKTREE` | Uncommitted edits changed since `/eval` |
| 1 | `STALE_CONTRACT` | The contract or extras digest changed since `/eval` |
| 1 | `REFROZEN_AFTER_RUN` | The freeze ledger grew after `/eval` ran (e.g. re-frozen A → B → A) |
| 1 | `RECEIPT_INCOMPLETE` | A required eval has no result (e.g. `results: []`), or a result is duplicated |
| 1 | `VERDICT_MISMATCH` | Stored `PASS`, but the results do not satisfy the gate (a required eval not `pass`/`waived`, wrong `check_type`, non-zero exit on a deterministic pass, structural errors) |
| 1 | `UNBACKED_DECISION` | A human pass or waiver has no matching entry in the attestations file |
| 1 | `RERUN_FAIL` | (`--rerun`) a required deterministic eval fails when re-executed |
| 1 | `LEDGER_MISMATCH` | The Evals Digest is not the ledger's last `new_digest` |
| 1 | `FREEZE_LOG_BROKEN` | The freeze ledger's hash chain does not hold, or a line is not JSON |
| 1 | `CONTRACT_TAMPERED` | The `## Evals` block no longer matches its own Evals Digest |
| 1 | `CONTRACT_NOT_FROZEN` | DESIGN has a contract but was never `freeze`d |
| 1 | `LEGACY_NO_EVALS` | Legacy DESIGN with no `--legacy` waiver |
| 2 | `CONFIG` / `NOT_A_GIT_REPO` / `PYTHON_TOO_OLD` | Environment error — `verify` never even reaches a code above |

Receipts already archived under `.claude/sdd/archive/*/EVAL_*.json` were written by
runner 1.0.0; the suite re-checks every one of them against the new recomputation
(`test_archived_receipts_remain_consistent`).

## JEV — the Grading Judge

`scripts/jev_client.py` talks to TypeSafe's Jev, a "System One" model: it doesn't
generate text, it answers **typed questions** about a `state`.

| | |
|---|---|
| Model | `typesafe/jev-1.13` (override with `JEV_MODEL`) |
| Endpoints | primary `https://openrouter.ai/api/v1/systemone`, fallback `https://openrouter.ai/api/alpha/decisions` (falls back only on `NOT_FOUND`/`UNAVAILABLE`) |
| Auth | `OPENROUTER_API_KEY` (same key as `/judge`) |
| Question types | `noul` (yes/no probability, 0–1) · `score` (ordered rubric level with a probability distribution + `confidence`) |
| Robustness | every request has a wall-clock ceiling (`timeout`, default 30 s per endpoint — urllib's own timeout is per socket operation); a malformed answer (`None` probability, non-integer rubric level) is `JevError(PARSE)` and the eval escalates instead of crashing `/eval`; state truncation never makes a field longer than its share |
| Budget | `JEV_BUDGET` calls/day (default 200; a non-integer value falls back to 200, a negative one means 0), ledger `<project>/.claude/storage/judge-ledger.jsonl` — same row schema as `/judge`'s ledger, filtered to `model` starting with `typesafe/` |

### Three-Way Classification

`classify(answers, thresholds) -> "pass" | "fail" | "escalated"`, with
`Thresholds(noul_pass=0.85, noul_fail=0.15, score_confidence=0.75)`:

- **`pass`** — every `score` question is confident (`confidence ≥ score_confidence`)
  **and** peaks at its top rubric level, **and** every `noul` question is
  `≥ noul_pass`. Noul alone is never enough for a pass.
- **`fail`** — at least one confident `score` question peaks at its *bottom*
  level, and either a `noul` question is `≤ noul_fail`, or there's no `noul`
  question at all.
- **`escalated`** — anything else (low confidence, no clear peak, ambiguous
  answers).

This exists because a real test on 2026-09-23 showed Noul giving `0.70`
("supports the claim") with `confidence: 0` on a pending/unrun AT — Noul alone
would have approved the wrong case. Requiring a confident, top-level Score closes
that hole.

### Calibration Gate

JEV's decision is only **authoritative** (`decided_by: jev`) if
`.claude/sdd/evals/JEV_CALIBRATION.json` exists with `approved: true` for the
*current* `JEV_MODEL`. Otherwise JEV still runs and its answers are recorded, but
only as `role: advisory`, and the eval always escalates further.

```bash
eval_runner.py calibrate cases.toml
```

`cases.toml` holds `[[case]]` tables (`state`, `questions`, `expected: "pass"|"fail"`).
The runner calls JEV for each case, classifies the answers with the *default*
thresholds, and writes the report:

| Metric | Requirement to approve |
|---|---|
| `n` (total cases) | ≥ 10 |
| `coverage` (`decided / n`) | ≥ 50% |
| `agreement` (`agreed / decided`) | ≥ 80% |

### Escalation

When JEV isn't authoritative, or `classify()` itself returns `escalated`, the
*runner* — not the agent — resolves it:

- `--escalate judge` (or `auto` with `OPENROUTER_API_KEY` set) → calls
  `scripts/judge.py --stdin --json --phase generic` by subprocess
  (`JUDGE_CMD` overridable). Exit 0 → `pass` (`decided_by: judge`); exit 1 →
  `fail`; anything else → `pending` (`JUDGE_UNAVAILABLE`).
- `--escalate human`, or no `OPENROUTER_API_KEY` → `pending`
  (`NEEDS_HUMAN`), which only `attest` can resolve.

**No infrastructure failure ever produces a `pass`:** a missing key, an exhausted
budget, a JEV network error, or `judge.py` exiting 2/3/4 all fall through to
`pending`/`escalated`, never straight to `pass`.

## Security Notes

- Evals run arbitrary bash from the DESIGN with the user's own privileges —
  treat `## Evals` as reviewable code, same as any test file.
- `OPENROUTER_API_KEY` is stripped from every eval subprocess's environment; it is
  never written to the receipt, the report, the ledger, or a log line, and HTTP
  error bodies from JEV are truncated to 300 characters.
- Anything referenced by a `graded` eval's `state` leaves the machine over the
  network to JEV. `validate` warns (`SENSITIVE_STATE`) when a `state` command
  looks like it reads `.env*`, `*.pem`, or anything matching `secret`/`credential`.
- Nothing here is cryptographic authentication. The contract digest, the
  freeze-ledger hash chain and the receipt's integrity digest are all unkeyed
  sha256: they make tampering *evident* (a hand edit, a deleted ledger line, a
  flipped verdict) but an agent that can run the runner's own functions — or edit
  files — can recompute them. There is deliberately no HMAC: any key readable by
  the session would be readable by the agent being checked, so it would add no
  security. The real defenses are layered: the stored verdict is never trusted
  (it is recomputed), human decisions must match the attestations file,
  `verify --rerun` re-executes the deterministic proof, and the files involved
  (`EVAL_{F}.freeze.log`, the DESIGN, the receipt) are reviewable in git.

## Known Limits

| Limit | Why it's accepted |
|---|---|
| An agent could disobey instructions and re-freeze a loosened contract | Mitigated: a re-freeze needs `--reason`, is appended to the hash-chained freeze ledger with `git user.email`, and surfaces as a `REFROZEN` warning in the receipt and the report. A human still has to read it |
| No HMAC or signature on the digest/receipt | Deliberate: a key the session can read protects nothing from the session. Integrity digests are tamper-evident only; forgery is countered by recomputation, attestation cross-checks and `verify --rerun` |
| A fully forged receipt that fakes `pass` + `exit_code: 0` for every required deterministic eval and re-seals it passes plain `verify` | Caught by `verify --rerun`; `/ship` can opt into it when the stakes justify the rerun time |
| Graded passes decided by JEV/`judge.py` are accepted as recorded | They need the network; `--rerun` re-executes deterministic evals only |
| Gitignored files are outside the worktree digest | Documented above; use `verify --rerun` when an eval reads one |
| The eval-agent has no `Write`/`Edit` tool, but its `Bash` can still write files | Its instructions forbid shell writes; the runner writes every eval-phase file, and git shows anything else |
| The same build that implements a feature also writes its `test_atNNN_*` tests | Mitigated, not eliminated: this feature's own gate includes a complementary `eval_selfcheck` that asserts every `test_atNNN_*` contains an `assert`/`pytest.raises` |
| JEV's endpoint is documented as alpha and could change shape | `jev_client.py` is an isolated module behind a small interface, with two independent endpoint paths |

## Boundaries With Related Features

- **`LIVING_MEMORY`** — this feature only guarantees a *stable* receipt format
  (`agentspec/eval-receipt/v1`) for a single `/eval` run. Tracking eval history,
  pass-rate trends, or cross-feature metrics over time is `LIVING_MEMORY`'s job.
- **`JEV_AGENT_SELECTION`** — using JEV (or any model) to pick *which agent*
  should handle a task is a separate, future feature. Here, JEV only grades
  answers to questions about an eval's `state`.
- **`LLM_PHASE_ROUTING`** — choosing which model runs each SDD phase — including
  `eval-agent` itself and the model behind the `judge.py` escalation fallback —
  belongs to `LLM_PHASE_ROUTING`, not to this feature.

## Related

- [.claude/sdd/features/DESIGN_POST_BUILD_EVALS.md](../../.claude/sdd/features/DESIGN_POST_BUILD_EVALS.md) — full design, decisions, and rationale
- [scripts/eval_runner.py](../../scripts/eval_runner.py) — the CLI (`validate/freeze/pre/extra/run/attest/waive/verify/calibrate`)
- [scripts/jev_client.py](../../scripts/jev_client.py) — the JEV client
- [docs/getting-started/judge-setup.md](../getting-started/judge-setup.md) — shared OpenRouter setup, including the JEV-specific section
- [.claude/agents/README.md](../../.claude/agents/README.md) — eval-agent's place in the routing/escalation map

# kb_bench — KB vs Context7 benchmark

Measures whether AgentSpec's curated knowledge base still earns its keep. The
same 18 data-engineering tasks run headless on the Codex CLI (`codex exec`,
model pinned in `bench.toml`) in four knowledge arms; only the knowledge
source changes:

| Arm | Knowledge in the workspace | Context7 MCP |
|-----|----------------------------|--------------|
| A | current KB (`.claude/kb/<domain>` copied to `./kb`) | no |
| B | none | yes |
| C | lean KB (`kb_lean/<domain>`: anti-patterns, decisions, conventions) | yes |
| D | none | no |

Each (task, arm) pair is scored by deterministic evals: **pass first**, **pass
after retry** (≤ 2, with the failing checks fed back), or **human** review. The
report applies a decision rule fixed in advance and recommends, per stratum
(library / conceptual / niche), `aposentar KB`, `substituir por B`,
`enxugar (C)`, `manter A` or `inconclusivo`.

Two guards (protocol 2, `[decision]` in `bench.toml`) keep a too-easy task set
from deciding "retire" by construction:

- **Anti-ceiling.** If arm D (no knowledge) resolves ≥ `ceiling_rate` (90%) of
  a stratum, the cell is `inconclusivo (teto)`, whatever A, B and C did.
- **Ties never retire.** `aposentar KB` needs D to beat A by more than
  `retire_margin`; a tie is `inconclusivo (empate)`.

Spec: `.claude/sdd/archive/KB_CONTEXT7_REFRESH/`.

## Round 1 — why it doesn't count

Round 1 (2026-09-24, Grok CLI, `~/.kb-bench/results/20260924T*`) recommended
retiring the KB, but it is **invalid for decision** and `REPORT.md` for those
runs now opens with a banner saying so:

1. **Isolation leak.** Arm D's recursive searches printed hits from
   `arms/a/kb` and `arms/c/kb` (and could read other arms' results); the Grok
   harness also listed the `data-engineering-guide` skill to every arm.
2. **Context7 quota.** No API key: the anonymous quota answered "Monthly quota
   exceeded", so B and C measured mostly the bare model.
3. **Ceiling effect.** B, C and D solved ~100% of the synthetic tasks, and the
   old rule turned a D = A tie into "aposentar KB".

## Round 2 protocol

- **Tasks:** ≥ 10 *real* tasks per stratum (`--tasks-dir`, kept outside git),
  pre-filtered with an arm-D-only pilot so D resolves < 80% of each stratum.
- **Repetitions:** 3 runs per (task, arm) pair (separate `run` invocations or
  seeds), so each pair has a success rate, not a single coin flip.
- **Analysis:** paired comparison per task — McNemar on pass/fail pairs, or a
  paired bootstrap of the rate difference with a 95% interval — before reading
  the recommendation table.
- **Arm A with an updated KB:** refresh the domains under test (`/ingest-kb`)
  before the round; otherwise A measures a stale KB against live docs.
- **Context7 key mandatory:** `run` refuses B/C without `CONTEXT7_API_KEY`,
  and a quota/auth refusal or an outage mid-round **aborts** the run (the pair
  is not recorded; `--resume` retries it) instead of piling up `unavailable`.
- **Human queue truly human:** the maintainer judges the blind items, not an
  agent; record verdicts with `kb_bench human --approve/--reject`.

## Prerequisites

- Codex CLI ≥ 0.157, logged in (`codex login`; a ChatGPT login is fine). The
  `codex` first on `PATH` may be a wrapper — point the bench at the real
  binary with `export KB_BENCH_CODEX=/opt/homebrew/bin/codex`.
- `npx` (Node) for `@upstash/context7-mcp`.
- A Context7 API key in `CONTEXT7_API_KEY` (free at
  <https://context7.com/dashboard>) — mandatory: `run` refuses arms B/C
  without it. Without it the anonymous quota answers "Monthly quota exceeded"
  and `smoke` fails. The key is only ever read from
  the environment: never written to disk, never on a command line, never
  printed.
- Python ≥ 3.11; `uv` recommended (creates the Python 3.12 eval venv).

## Quick start

```bash
export KB_BENCH_CODEX=/opt/homebrew/bin/codex CONTEXT7_API_KEY=...
make kb-bench-setup                  # folders, eval venv, isolated agent home
make kb-bench-validate               # every task: fails on fixtures, passes on its solution
make kb-bench-smoke                  # codex + login, MCP per arm, sandbox canary, Context7 quota/coverage, 1 exec canary
make kb-bench ARGS="--dry-run"       # plan + preflight, no model calls
make kb-bench ARGS="--stratum library"   # a slice first
make kb-bench                        # full run: 18 tasks × 4 arms
make kb-bench ARGS="--resume <run_id>"   # continue after a budget/usage-limit stop or Ctrl-C
PYTHONPATH=scripts python3 -m kb_bench human            # list blind review items
PYTHONPATH=scripts python3 -m kb_bench human --approve <item>
make kb-bench-report                 # re-render REPORT.md
make kb-bench-teardown               # remove the isolated agent home (results kept)
```

Results live outside the repo in `~/.kb-bench/results/<run_id>/` (override with
`KB_BENCH_HOME`, which must not be inside a git repository). Override the model
with `KB_BENCH_MODEL` (empty string = the account default).

## How an attempt runs

```text
codex exec --json --ephemeral --skip-git-repo-check --ignore-user-config \
  -C ~/.kb-bench/arms/<arm> -m <model> \
  -c approval_policy="never" -c web_search="disabled" \
  -c 'permissions.kbbench.filesystem={":root"="read", ":project_roots"={"."="write"}, "<scratch>"="write", "<deny>"="none", …}' \
  -c default_permissions="kbbench" \
  [-c mcp_servers.context7.{command,args,env,startup_timeout_sec,env_vars}=…   # B and C only] \
  --disable multi_agent --disable apps … -- "<prompt>"   </dev/null
```

- **Isolated home.** `HOME` and `CODEX_HOME` point at `~/.kb-bench/agent-home`,
  emptied before every attempt except for a symlink to your
  `~/.codex/auth.json` (no copy). Without it Codex loads your global skills
  from `~/.agents` even with `--ignore-user-config` (spike: 118k input tokens
  for a trivial prompt vs 10.7k isolated). If Codex refreshes the token and
  replaces the symlink, the bench moves the new file back to `~/.codex` so
  your own login keeps working. `TMPDIR`/`TMPPREFIX` point at a scratch folder
  inside it (the only writable place besides the arm folder).
- **Permission profile.** Every shell command the agent runs can read the
  disk except the deny roots (value `none`): every AgentSpec KB copy found on
  the machine (`~/.claude`, `~/.codex`, `~/.agents`, plugin installs,
  checkouts and worktrees, and this repo — which also hides tasks, evals and
  solutions), agent CLI session transcripts, the bench results, and the
  *other* arms' folders. Network is off for shell commands. MCP servers run
  outside this sandbox.
- **Nothing in the arm folder.** Config travels as `-c` overrides, so the
  workspace holds only fixtures, the agent's work and (A, C) `./kb`.
- **No max-turns flag.** Codex has none; `attempt_timeout_s` is the hard stop
  (outcome `timeout`), and a `turn.failed` also ends the attempt as `timeout`.
  A failed turn that names the account (401, usage/rate limit, quota) stops
  the whole run instead, so `--resume` retries that pair later.

## How isolation is proven

- **Canaries.** `smoke` runs `cat` under arm D's profile via `codex sandbox`
  (no model) on three canaries — the canary folder, a file inside
  `arms/a/kb/` and one inside `results/` (the two round-1 leak paths) — and
  expects "Operation not permitted" for each, plus a write in the arm folder
  that must succeed. The full smoke then asks
  `codex exec` to read the canary once; Codex usually declines because it sees
  the policy — that passes, a leaked token aborts.
- **Transcript.** The JSONL of every attempt is checked: a *completed* command
  naming a deny root that returned data without a denial message, or a
  completed file change under one, marks the pair `contaminated` (excluded);
  so do Context7 in arm A/D and any web search. Denied accesses are only
  counted (`kb_access_denied`).
- **AT-004, literally.** Independently of the deny roots, a completed command
  whose command line or output names a path with `/kb/` (or an AgentSpec
  plugin folder, or a knowledge skill such as `skills/data-engineering-guide`)
  outside the arm folder is `contaminated`. Refused or missing reads don't count.
- **Context7 availability.** Before every B/C attempt the bench starts the
  same MCP server Codex would and checks its tools (no model). A Context7 call
  whose result is a quota/auth refusal counts as unavailable, not as a call.
  A failed preflight, any refused call, or an attempt whose every call failed
  on transport **stops the run** (exit 3, pair not recorded, `--resume`
  later): a quota exhaustion can't silently bias the rest of the round. `smoke` probes the quota and the per-domain coverage by
  calling `resolve-library-id` directly.

## Budget and cost

Codex on a ChatGPT login reports tokens but no USD cost and no effective model
name. The run stops when **fresh tokens** — `(input − cached input) + output`,
summed over all attempts — pass `run.budget_tokens`; resume with `--resume`.
The report shows total and fresh tokens and never a dollar figure. Calibrate
`budget_tokens` after the first slice.

## Adding tasks

Read `TASK_AUTHORING.md`. Real tasks you don't want versioned can live in a
separate folder with the same layout and be added with `--tasks-dir <dir>`
(fixtures/solutions resolved from its parent).

## Layout

```text
scripts/kb_bench/
├── bench.toml            defaults (model, limits, budget, deny globs, decision thresholds, arms)
├── cli.py                setup | teardown | validate | smoke | run | report | human
├── loop.py               attempt → isolation → evals → retry → human; budget / stop
├── codex_runner.py       codex exec argv, permission profile, isolated agent home
├── context7_probe.py     stdio MCP client: preflight, quota, coverage (no model)
├── transcript.py         Codex JSONL parser
├── isolation.py          contamination / denied / Context7 accounting
├── workspace.py          per-arm folder, KB copy, snapshots
├── evals.py              runs task evals on a copy; discrimination check
├── report.py             decision rule + REPORT.md (pt-BR)
├── setup_env.py          setup/teardown, smoke, canaries, coverage
├── checks/               eval checkers (AST, JSON, SQL, DuckDB, dbt manifest)
├── tasks/ fixtures/ solutions/   18 tasks, 3 per domain
└── kb_lean/              lean KB for arm C
```

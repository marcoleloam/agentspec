# kb_bench — KB vs Context7 benchmark

Measures whether AgentSpec's curated knowledge base still earns its keep. The
same 18 data-engineering tasks run on the Grok CLI (`grok-4.7`) in four
knowledge arms; only the knowledge source changes:

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

Spec: `.claude/sdd/features/{BRAINSTORM,DEFINE,DESIGN}_KB_CONTEXT7_REFRESH.md`.

## Prerequisites

- Grok CLI ≥ 1.0.41, logged in (`grok login`), with `grok-4.7` in `grok models`
- `npx` (Node) for `@upstash/context7-mcp`
- Python ≥ 3.11; `uv` recommended (creates the Python 3.12 eval venv)

## Quick start

```bash
make kb-bench-setup                  # folders, eval venv, trust arms B/C (asks first)
make kb-bench-validate               # every task: fails on fixtures, passes on its solution
make kb-bench-smoke                  # grok, trust, MCP per arm, sandbox canary, Context7 coverage
make kb-bench ARGS="--dry-run"       # plan + preflight, no model calls
make kb-bench ARGS="--stratum library"   # a slice first
make kb-bench                        # full run: 18 tasks × 4 arms
make kb-bench ARGS="--resume <run_id>"   # continue after budget stop / Ctrl-C
PYTHONPATH=scripts python3 -m kb_bench human            # list blind review items
PYTHONPATH=scripts python3 -m kb_bench human --approve <item>
make kb-bench-report                 # re-render REPORT.md
make kb-bench-teardown               # remove the trust entries setup added
```

Results live outside the repo in `~/.kb-bench/results/<run_id>/` (override with
`KB_BENCH_HOME`, which must not be inside a git repository).

## How isolation works

- **Sandbox.** Every attempt runs with `--sandbox kbbench`: `extends =
  "workspace"` plus `deny` on every AgentSpec KB copy found on the machine
  (the Grok plugin's `kb/`, the Claude plugin cache, AgentSpec checkouts and
  worktrees, and this repo — which also hides tasks, evals and solutions). A
  sandbox that failed to apply is caught by the **canary** in `smoke`.
- **Proof.** The NDJSON transcript of every attempt is checked: a *completed*
  access under a deny root, Context7 use in arm A/D, or any web tool marks the
  pair `contaminated` (excluded from the score). Denied attempts are only
  counted (`kb_access_denied`).
- **MCP per arm.** Each arm folder has its own `.grok/config.toml`: Context7 only
  in B/C, and the user's global MCP servers disabled. Grok starts project MCP
  servers only in trusted folders, so `setup` adds `arms/b` and `arms/c` to
  `~/.grok/trusted_folders.toml` after a backup and your confirmation;
  `teardown` removes exactly those entries.
- `GROK_MEMORY=0`, `--disable-web-search`, `--no-subagents` on every attempt.

## Adding tasks

Read `TASK_AUTHORING.md`. Real tasks you don't want versioned can live in a
separate folder with the same layout and be added with `--tasks-dir <dir>`
(fixtures/solutions resolved from its parent).

## Layout

```text
scripts/kb_bench/
├── bench.toml            defaults (model, limits, deny globs, arms)
├── cli.py                setup | teardown | validate | smoke | run | report | human
├── loop.py               attempt → isolation → evals → retry → human
├── transcript.py         Grok streaming-json parser
├── isolation.py          contamination / denied / Context7 accounting
├── workspace.py          per-arm folder, KB copy, .grok/{config,sandbox}.toml
├── evals.py              runs task evals on a copy; discrimination check
├── report.py             decision rule + REPORT.md (pt-BR)
├── setup_env.py          setup/teardown (trust file), smoke, canary, coverage
├── checks/               eval checkers (AST, JSON, SQL, DuckDB, dbt manifest)
├── tasks/ fixtures/ solutions/   18 tasks, 3 per domain
└── kb_lean/              lean KB for arm C
```

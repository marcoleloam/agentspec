"""kb_bench command line: setup, teardown, validate, smoke, run, report, human."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kb_bench import codex_runner, context7_probe, setup_env
from kb_bench.config import ARM_LETTERS, STRATA, BenchConfig, ConfigError, load_config
from kb_bench.evals import discriminates
from kb_bench.human_queue import HumanQueue
from kb_bench.loop import RunContext, RunStopped, plan, run_plan
from kb_bench.report import PROTOCOL, write_report
from kb_bench.store import RunStore, git_commit, git_dirty_paths, latest_run, new_run_id
from kb_bench.tasks import Task, TaskError, load_tasks
from kb_bench.workspace import WorkspaceError


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _select(tasks: list[Task], args: argparse.Namespace) -> list[Task]:
    if getattr(args, "task", None):
        tasks = [t for t in tasks if t.id in set(args.task)]
    if getattr(args, "stratum", None):
        tasks = [t for t in tasks if t.stratum in set(args.stratum)]
    if getattr(args, "domain", None):
        tasks = [t for t in tasks if t.domain in set(args.domain)]
    return tasks


def _load_tasks(cfg: BenchConfig, args: argparse.Namespace) -> list[Task]:
    tasks = load_tasks(cfg.tasks_dir)
    if getattr(args, "tasks_dir", None):
        extra = load_tasks(args.tasks_dir.resolve(), base=args.tasks_dir.resolve().parent)
        clash = {t.id for t in tasks} & {t.id for t in extra}
        if clash:
            raise TaskError(f"--tasks-dir ids clash with bundled tasks: {sorted(clash)}")
        tasks += extra
    return _select(tasks, args)


def _validate(tasks: list[Task], cfg: BenchConfig, verbose: bool) -> int:
    bad = 0
    for task in tasks:
        result = discriminates(task, cfg)
        sol = ("solution ✓" if result.solution_passes else "solution ✗") if result.solution_checked else "no solution"
        print(f"[{'ok' if result.ok else 'REJECTED'}] {task.id} ({task.domain}, {task.origin}) — {sol}")
        if verbose or not result.ok:
            for problem in result.problems():
                print(f"    - {problem}")
        if verbose:
            shown = result.solution_results if result.solution_checked else result.fixture_results
            for r in shown:
                if not r.passed:
                    print(f"      · {r.name}: {r.output[:300]}")
        bad += not result.ok
    print(f"{len(tasks) - bad}/{len(tasks)} tasks valid")
    return bad


def cmd_validate(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    tasks = _load_tasks(cfg, args)
    if not tasks:
        print("no tasks selected")
        return 1
    if not (cfg.eval_venv_bin / "python").exists():
        print("eval venv missing — run `make kb-bench-setup` first")
        return 2
    return 1 if _validate(tasks, cfg, args.verbose) else 0


def cmd_setup(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    setup_env.setup(cfg, skip_venv=args.skip_venv)
    print(f"setup complete — home {cfg.home}. Next: python3 -m kb_bench smoke")
    return 0


def cmd_teardown(args: argparse.Namespace) -> int:
    setup_env.teardown(load_config(args.config))
    return 0


def _print_smoke(res: setup_env.SmokeResult) -> None:
    for c in res.checks:
        print(f"[{'ok' if c.ok else 'FAIL'}] {c.name}" + (f" — {c.detail}" if c.detail else ""))
    for w in res.warnings:
        print(f"[WARN] {w}")


def cmd_smoke(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    res = setup_env.smoke(cfg, model_calls=not args.no_model)
    _print_smoke(res)
    if res.coverage:
        for domain, info in res.coverage.items():
            print(f"    coverage {domain}: {info['status']} ({info.get('library_id') or '—'})")
    return 0 if res.ok else 1


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    tasks = _load_tasks(cfg, args)
    arms = [a.upper() for a in (args.arm or ARM_LETTERS)]
    if not tasks:
        print("no tasks selected")
        return 1
    if not (cfg.eval_venv_bin / "python").exists():
        print("eval venv missing — run `make kb-bench-setup` first")
        return 2
    if _validate(tasks, cfg, verbose=False):
        print("fix or drop the rejected tasks before running")
        return 1

    pairs = plan(tasks, arms, cfg.seed)
    if args.dry_run:
        res = setup_env.smoke(cfg, model_calls=False)
        _print_smoke(res)
        print(f"dry-run: {len(pairs)} (task, arm) pairs planned, seed {cfg.seed}; no model calls made")
        return 0 if res.ok else 1

    no_key = [a for a in arms if cfg.arms[a].uses_context7] and not context7_probe.api_key_present()
    if no_key:
        print(f"{context7_probe.API_KEY_ENV} is required for arms B/C (round-2 protocol): the anonymous "
              "quota runs out mid-round. Export the key, or run only --arm A --arm D.")
        return 2

    if args.resume:
        root = cfg.results_root / args.resume
        if not root.is_dir():
            print(f"no run {args.resume} under {cfg.results_root}")
            return 1
        store = RunStore(root)
        saved = store.read_json("plan.json") or {}
        pairs = [tuple(p) for p in saved.get("pairs", pairs)]
    else:
        store = RunStore(cfg.results_root / new_run_id())
        store.write_json("plan.json", {"seed": cfg.seed, "arms": arms, "pairs": pairs})

    prior_env = store.read_json("env.json")
    # Resuming a run started under an older protocol keeps its (lower) protocol number.
    protocol = PROTOCOL if prior_env is None else min(int(prior_env.get("protocol", 1) or 1), PROTOCOL)
    dirty_before = git_dirty_paths()
    coverage = store.read_json("coverage.json")
    if not args.skip_smoke:
        res = setup_env.smoke(cfg, model_calls=True)
        _print_smoke(res)
        if not res.ok:
            print("smoke failed — nothing was run")
            return 1
        coverage = res.coverage
        store.write_json("coverage.json", coverage)
    env = {"commit": git_commit(), "cli_version": codex_runner.version(),
           "codex_bin": codex_runner.resolved_bin(), "model": cfg.model or "account default",
           "reasoning_effort": cfg.reasoning_effort or "model default", "seed": cfg.seed,
           "budget_tokens": cfg.budget_tokens, "home": str(cfg.home),
           "deny": [str(p) for p in cfg.deny_paths()], "context7_api_key": context7_probe.api_key_present(),
           "smoke_skipped": bool(args.skip_smoke), "coverage_present": bool(coverage), "protocol": protocol}
    store.write_json("env.json", env)

    ctx = RunContext(cfg=cfg, store=store, queue=HumanQueue(store.root), cli_version=env["cli_version"], log=_log)
    ctx.spent_tokens = sum(r.fresh_tokens or 0 for r in store.records())
    status = 0
    try:
        run_plan(tasks, arms, ctx, pairs=pairs)
    except RunStopped as exc:
        print(f"stopped: {exc} — resume later with --resume {store.run_id}")
        status = 3
    except KeyboardInterrupt:
        print(f"interrupted — resume with --resume {store.run_id}")
        status = 130
    except WorkspaceError as exc:
        print(f"workspace error: {exc}")
        status = 2
    finally:
        new_dirty = sorted(p for p in git_dirty_paths() - dirty_before if not p.startswith("scripts/kb_bench/"))
        env["git_dirty_new"] = new_dirty
        store.write_json("env.json", env)
        report = write_report(store, cfg)
        print(f"report: {report}")
    return status


def _resolve_run(cfg: BenchConfig, run_id: str | None) -> RunStore | None:
    root = cfg.results_root / run_id if run_id else latest_run(cfg.results_root)
    return RunStore(root) if root and root.is_dir() else None


def cmd_report(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    store = _resolve_run(cfg, args.run)
    if store is None:
        print("no run found")
        return 1
    print(write_report(store, cfg))
    return 0


def cmd_human(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    store = _resolve_run(cfg, args.run)
    if store is None:
        print("no run found")
        return 1
    queue = HumanQueue(store.root)
    if args.approve or args.reject:
        verdict, item = ("approve", args.approve) if args.approve else ("reject", args.reject)
        queue.record(item, verdict, args.note or "")
        print(f"{item}: {verdict}")
        write_report(store, cfg)
        return 0
    pending = queue.pending()
    print(f"{len(pending)} item(s) pending in {queue.dir}")
    for item in pending:
        print(f"  {queue.dir / (item + '.md')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="kb_bench", description=__doc__)
    ap.add_argument("--config", type=Path, default=None, help="alternate bench.toml")
    sub = ap.add_subparsers(dest="command", required=True)

    def selectors(p: argparse.ArgumentParser) -> None:
        p.add_argument("--task", action="append", help="task id (repeatable)")
        p.add_argument("--stratum", action="append", choices=STRATA)
        p.add_argument("--domain", action="append")
        p.add_argument("--tasks-dir", type=Path, default=None,
                       help="extra tasks folder (<dir>/<domain>/<id>.toml; fixtures/solutions resolved from its parent)")

    p = sub.add_parser("setup", help="arm folders, eval venv, isolated Codex home (auth.json symlink)")
    p.add_argument("--skip-venv", action="store_true")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("teardown", help="remove the isolated agent home (results are kept)")
    p.set_defaults(func=cmd_teardown)

    p = sub.add_parser("validate", help="schema + discrimination check for every task")
    selectors(p)
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("smoke", help="preflight: codex + login, MCP per arm, sandbox canary, Context7 quota/coverage")
    p.add_argument("--no-model", action="store_true",
                   help="skip the Context7 quota/coverage requests and the codex exec canary")
    p.set_defaults(func=cmd_smoke)

    p = sub.add_parser("run", help="execute the plan (all tasks × arms by default)")
    selectors(p)
    p.add_argument("--arm", action="append", choices=[*ARM_LETTERS, *[a.lower() for a in ARM_LETTERS]])
    p.add_argument("--dry-run", action="store_true", help="validate + preflight without model calls")
    p.add_argument("--resume", metavar="RUN_ID")
    p.add_argument("--skip-smoke", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("report", help="rebuild REPORT.md")
    p.add_argument("--run", metavar="RUN_ID", help="default: latest")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("human", help="list the blind review queue or record a verdict")
    p.add_argument("run", nargs="?", metavar="RUN_ID", help="default: latest")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--approve", metavar="ITEM")
    group.add_argument("--reject", metavar="ITEM")
    p.add_argument("--note")
    p.set_defaults(func=cmd_human)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ConfigError, TaskError, setup_env.SetupError, codex_runner.CodexHomeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

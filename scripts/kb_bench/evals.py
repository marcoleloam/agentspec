"""Run a task's evals against a copy of a workspace.

Evals run outside the agent's sandbox, on a throwaway copy, with the eval venv
first on PATH and ``scripts/`` on PYTHONPATH so ``python -m kb_bench.checks.*``
resolves. A task is *discriminating* when its evals fail on the fixtures alone
and — if a reference solution exists — all pass on fixtures + solution.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from kb_bench.config import BENCH_DIR, SCRIPTS_DIR, BenchConfig
from kb_bench.tasks import Task

_IGNORED = shutil.ignore_patterns(".grok", "__pycache__", ".DS_Store")
_OUTPUT_LIMIT = 2000


@dataclass(frozen=True)
class EvalResult:
    name: str
    passed: bool
    exit_code: int
    output: str


@dataclass(frozen=True)
class Discrimination:
    task_id: str
    fails_on_fixtures: bool
    solution_checked: bool
    solution_passes: bool
    fixture_results: tuple[EvalResult, ...]
    solution_results: tuple[EvalResult, ...]

    @property
    def ok(self) -> bool:
        return self.fails_on_fixtures and (not self.solution_checked or self.solution_passes)

    def problems(self) -> list[str]:
        out: list[str] = []
        if not self.fails_on_fixtures:
            out.append("every eval passes on the fixtures alone (not discriminating)")
        if self.solution_checked and not self.solution_passes:
            failed = [r.name for r in self.solution_results if not r.passed]
            out.append(f"reference solution fails evals: {failed}")
        return out


def eval_env(cfg: BenchConfig) -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = f"{cfg.eval_venv_bin}{os.pathsep}{env.get('PATH', '')}"
    env["PYTHONPATH"] = str(SCRIPTS_DIR)
    env["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    env["DBT_NO_VERSION_CHECK"] = "true"
    env.pop("VIRTUAL_ENV", None)
    return env


def copy_tree(sources: Iterable[Path | None], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for src in sources:
        if src is not None and src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=True, ignore=_IGNORED)


def run_evals(task: Task, workdir: Path, cfg: BenchConfig) -> list[EvalResult]:
    env = eval_env(cfg)
    results: list[EvalResult] = []
    for ev in task.evals:
        try:
            proc = subprocess.run(
                list(ev.cmd), cwd=workdir, env=env, capture_output=True, text=True,
                timeout=ev.timeout_s or cfg.eval_timeout_s, check=False,
            )
            output = (proc.stdout + proc.stderr).strip()
            code = proc.returncode
        except FileNotFoundError as exc:
            output, code = f"command not found: {exc.filename}", 127
        except subprocess.TimeoutExpired:
            output, code = f"eval timed out after {ev.timeout_s or cfg.eval_timeout_s}s", 124
        results.append(EvalResult(ev.name, code == 0, code, output[-_OUTPUT_LIMIT:]))
    return results


def run_on_copy(task: Task, sources: Iterable[Path | None], cfg: BenchConfig,
                keep_at: Path | None = None) -> list[EvalResult]:
    if keep_at is not None:
        if keep_at.exists():
            shutil.rmtree(keep_at)
        copy_tree(sources, keep_at)
        return run_evals(task, keep_at, cfg)
    with tempfile.TemporaryDirectory(prefix=f"kbbench-eval-{task.id}-") as tmp:
        work = Path(tmp) / "ws"
        copy_tree(sources, work)
        return run_evals(task, work, cfg)


def discriminates(task: Task, cfg: BenchConfig) -> Discrimination:
    on_fixtures = run_on_copy(task, [task.fixtures], cfg)
    on_solution: list[EvalResult] = []
    if task.solution is not None:
        on_solution = run_on_copy(task, [task.fixtures, task.solution], cfg)
    return Discrimination(
        task_id=task.id,
        fails_on_fixtures=not all(r.passed for r in on_fixtures),
        solution_checked=task.solution is not None,
        solution_passes=bool(on_solution) and all(r.passed for r in on_solution),
        fixture_results=tuple(on_fixtures),
        solution_results=tuple(on_solution),
    )


def sanitize(text: str, workdir: Path | None = None) -> str:
    """Hide evaluator internals (bench dir, eval venv, snapshot path) from agent-facing text."""
    replacements = [(str(BENCH_DIR), "<evaluator>"), (str(SCRIPTS_DIR), "<evaluator>")]
    if workdir is not None:
        replacements.insert(0, (str(workdir.resolve()), "."))
        replacements.insert(1, (str(workdir), "."))
    for old, new in replacements:
        text = text.replace(old, new)
        if old.startswith("/private/"):
            text = text.replace(old[len("/private"):], new)
    return text


def feedback(results: Iterable[EvalResult], limit: int, workdir: Path | None = None) -> str:
    failed = [r for r in results if not r.passed]
    text = "\n".join(f"- {r.name} (exit {r.exit_code}):\n{r.output}" for r in failed)
    return sanitize(text, workdir)[:limit]

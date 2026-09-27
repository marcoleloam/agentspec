"""Static assertions for Airflow DAG files (no Airflow install required).

Detects the DAG either as ``@dag(...)``-decorated function or ``DAG(...)`` /
``with DAG(...)`` construction, then checks the id, schedule keyword, task
count and forbidden legacy idioms.

Usage:
  python -m kb_bench.checks.airflow_ast FILE [--dag-id ID] [--require-schedule-kw]
      [--min-tasks N] [--forbid NAME]... [--require-import MOD]... [--require-call NAME]...
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

from kb_bench.checks import finish, run
from kb_bench.checks.py_ast import Facts, dotted

_OPERATOR_SUFFIXES = ("Operator", "Sensor")


def _const_str(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _is_dag_callee(node: ast.AST) -> bool:
    return dotted(node).split(".")[-1] in {"DAG", "dag"}


def dag_calls(tree: ast.AST) -> list[tuple[ast.Call, str | None]]:
    """Every ``DAG(...)``/``@dag(...)`` call paired with its implied dag_id.

    A ``@dag``-decorated function defaults its dag_id to the function name; a
    bare ``@dag`` decorator is represented by an empty synthetic call.
    """
    found: list[tuple[ast.Call, str | None]] = []
    decorator_calls: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            if isinstance(deco, ast.Call) and _is_dag_callee(deco.func):
                decorator_calls.add(id(deco))
                found.append((deco, node.name))
            elif _is_dag_callee(deco):
                found.append((ast.Call(func=deco, args=[], keywords=[]), node.name))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_dag_callee(node.func) and id(node) not in decorator_calls:
            found.append((node, None))
    return found


def dag_id_of(call: ast.Call, implied: str | None) -> str | None:
    for kw in call.keywords:
        if kw.arg == "dag_id":
            return _const_str(kw.value)
    if call.args and _const_str(call.args[0]):
        return _const_str(call.args[0])
    return implied


def count_tasks(tree: ast.AST) -> int:
    tasks = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for deco in node.decorator_list:
                head = dotted(deco).split(".")
                if head[0] == "task":
                    tasks += 1
        elif isinstance(node, ast.Call) and dotted(node.func).endswith(_OPERATOR_SUFFIXES):
            tasks += 1
    return tasks


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="airflow_ast")
    ap.add_argument("file")
    ap.add_argument("--dag-id")
    ap.add_argument("--require-schedule-kw", action="store_true",
                    help="the DAG must pass schedule= (Airflow 3 removed schedule_interval)")
    ap.add_argument("--min-tasks", type=int, default=1)
    ap.add_argument("--forbid", action="append", default=[], help="forbidden name/keyword/call")
    ap.add_argument("--require-import", action="append", default=[])
    ap.add_argument("--require-call", action="append", default=[])
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        return finish([f"{args.file} does not exist"])
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except SyntaxError as exc:
        return finish([f"{args.file} is not valid Python: {exc}"])

    facts = Facts(tree)
    failures: list[str] = []
    dags = dag_calls(tree)
    if not dags:
        failures.append("no DAG found (neither @dag nor DAG(...))")
    if args.dag_id and args.dag_id not in {dag_id_of(c, implied) for c, implied in dags}:
        failures.append(f"no DAG with dag_id={args.dag_id!r}")
    if args.require_schedule_kw and not any(
        kw.arg == "schedule" for c, _ in dags for kw in c.keywords
    ):
        failures.append("DAG does not set schedule=")
    tasks = count_tasks(tree)
    if tasks < args.min_tasks:
        failures.append(f"found {tasks} task(s), expected >= {args.min_tasks}")
    failures += [
        f"forbidden idiom {name}"
        for name in args.forbid
        if name in facts.names or facts.has_call(name) or facts.has_import(name)
    ]
    failures += [f"missing import {m}" for m in args.require_import if not facts.has_import(m)]
    failures += [f"missing call {c}()" for c in args.require_call if not facts.has_call(c)]
    return finish(failures)


if __name__ == "__main__":
    run(main)

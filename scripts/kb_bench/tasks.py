"""Task model and TOML loader.

A task lives at ``tasks/<domain>/<id>.toml``. Fixtures (the starting files the
agent sees) and the optional reference solution (overlaid on the fixtures to
prove the evals are satisfiable) are resolved relative to the bench dir.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomllib

from kb_bench.config import BENCH_DIR, STRATA

DOMAIN_STRATUM = {
    "dbt": "library",
    "airflow": "library",
    "medallion": "conceptual",
    "data-modeling": "conceptual",
    "microsoft-fabric": "niche",
    "shadowtraffic": "niche",
}
ORIGINS = ("synthetic", "real")
_REQUIRED = ("id", "domain", "stratum", "origin", "authored_from", "prompt", "evals")


class TaskError(ValueError):
    """A task file violates the schema."""


@dataclass(frozen=True)
class Eval:
    name: str
    cmd: tuple[str, ...]
    timeout_s: int | None = None


@dataclass(frozen=True)
class Task:
    id: str
    domain: str
    stratum: str
    origin: str
    authored_from: str
    prompt: str
    evals: tuple[Eval, ...]
    source: Path
    fixtures: Path | None = None
    solution: Path | None = None


def _resolve_dir(base: Path, value: str | None, what: str, task_id: str) -> Path | None:
    if not value:
        return None
    path = (base / value).resolve()
    if not path.is_dir():
        raise TaskError(f"{task_id}: {what} directory {value!r} not found")
    return path


def load_task(path: Path, *, base: Path = BENCH_DIR) -> Task:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise TaskError(f"{path.name}: invalid TOML: {exc}") from exc
    missing = [k for k in _REQUIRED if k not in data]
    if missing:
        raise TaskError(f"{path.name}: missing keys {missing}")
    task_id = data["id"]
    if path.stem != task_id:
        raise TaskError(f"{path.name}: file name must equal id {task_id!r}")
    domain, stratum = data["domain"], data["stratum"]
    if domain not in DOMAIN_STRATUM:
        raise TaskError(f"{task_id}: unknown domain {domain!r}")
    if stratum not in STRATA or DOMAIN_STRATUM[domain] != stratum:
        raise TaskError(f"{task_id}: domain {domain} belongs to stratum {DOMAIN_STRATUM[domain]!r}")
    if data["origin"] not in ORIGINS:
        raise TaskError(f"{task_id}: origin must be one of {ORIGINS}")
    if not str(data["prompt"]).strip():
        raise TaskError(f"{task_id}: empty prompt")
    raw_evals = data["evals"]
    if not isinstance(raw_evals, list) or not raw_evals:
        raise TaskError(f"{task_id}: at least one [[evals]] entry is required")
    evals: list[Eval] = []
    for i, ev in enumerate(raw_evals):
        cmd = ev.get("cmd")
        if not ev.get("name") or not isinstance(cmd, list) or not cmd or not all(isinstance(c, str) for c in cmd):
            raise TaskError(f"{task_id}: evals[{i}] needs a name and a non-empty string list cmd")
        evals.append(Eval(ev["name"], tuple(cmd), ev.get("timeout_s")))
    names = [e.name for e in evals]
    if len(set(names)) != len(names):
        raise TaskError(f"{task_id}: eval names must be unique")
    solution_default = base / "solutions" / task_id
    return Task(
        id=task_id,
        domain=domain,
        stratum=stratum,
        origin=data["origin"],
        authored_from=data["authored_from"],
        prompt=str(data["prompt"]).strip(),
        evals=tuple(evals),
        source=path.resolve(),
        fixtures=_resolve_dir(base, data.get("fixtures"), "fixtures", task_id),
        solution=_resolve_dir(base, data.get("solution"), "solution", task_id)
        or (solution_default if solution_default.is_dir() else None),
    )


def load_tasks(tasks_dir: Path, *, base: Path = BENCH_DIR) -> list[Task]:
    tasks = [load_task(p, base=base) for p in sorted(tasks_dir.glob("*/*.toml"))]
    ids = [t.id for t in tasks]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise TaskError(f"duplicate task ids: {dupes}")
    return tasks

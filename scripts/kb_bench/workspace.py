"""Per-arm workspace: fixed folder under KB_BENCH_HOME, emptied before each first attempt.

The folder is the Codex working root (``-C``). Nothing bench-specific lives in
it: Codex config, MCP servers and the permission profile travel as ``-c``
overrides and the Codex state lives in the isolated agent home, so the agent
sees only the fixtures, its own work and — in A and C — ``./kb`` (DESIGN
Decisão 2, adapted to Codex).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from kb_bench.config import Arm, BenchConfig
from kb_bench.evals import copy_tree
from kb_bench.tasks import Task


class WorkspaceError(RuntimeError):
    """The arm workspace cannot be prepared safely."""


def reset_arm_dir(arm_dir: Path, cfg: BenchConfig) -> None:
    arm_dir = arm_dir.resolve()
    if cfg.home not in arm_dir.parents:
        raise WorkspaceError(f"refusing to reset {arm_dir}: not under {cfg.home}")
    arm_dir.mkdir(parents=True, exist_ok=True)
    for child in arm_dir.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def kb_source(arm: Arm, task: Task, cfg: BenchConfig) -> Path | None:
    if arm.kb == "repo":
        return cfg.repo_kb / task.domain
    if arm.kb == "lean":
        return cfg.kb_lean_dir / task.domain
    return None


def prepare(arm: Arm, task: Task, cfg: BenchConfig, *, fresh: bool) -> Path:
    """Prepare the arm folder for an attempt; ``fresh=False`` keeps the agent's work (retry)."""
    arm_dir = cfg.arm_dir(arm.letter)
    if fresh:
        reset_arm_dir(arm_dir, cfg)
        copy_tree([task.fixtures], arm_dir)
        src = kb_source(arm, task, cfg)
        if src is not None:
            if not src.is_dir():
                raise WorkspaceError(f"arm {arm.letter}: KB source {src} missing")
            shutil.copytree(src, arm_dir / "kb", dirs_exist_ok=True)
    else:
        arm_dir.mkdir(parents=True, exist_ok=True)
    return arm_dir


def agent_files(arm_dir: Path) -> list[Path]:
    """Files the agent left in the workspace (excluding the provided kb/)."""
    out: list[Path] = []
    for path in sorted(arm_dir.rglob("*")):
        rel = path.relative_to(arm_dir)
        if path.is_file() and rel.parts and rel.parts[0] != "kb":
            out.append(path)
    return out


def snapshot(arm_dir: Path, dest: Path) -> None:
    """Copy the agent's workspace (minus kb/) for evals and the human queue."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for path in agent_files(arm_dir):
        target = dest / path.relative_to(arm_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

"""Per-arm workspace: fixed folder under KB_BENCH_HOME, reset per attempt.

The folder itself is the Grok cwd (project config is read from cwd and folder
trust is keyed on it), so only ``.grok/`` survives a reset (DESIGN Decisão 2).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from kb_bench.config import Arm, BenchConfig
from kb_bench.evals import copy_tree
from kb_bench.tasks import Task


class WorkspaceError(RuntimeError):
    """The arm workspace cannot be prepared safely."""


def _toml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def grok_config_toml(arm: Arm, cfg: BenchConfig) -> str:
    lines: list[str] = []
    if arm.uses_context7:
        lines += [
            "[mcp_servers.context7]",
            'command = "npx"',
            f'args = ["-y", {_toml_str(cfg.context7_package)}]',
            f"env = {{ npm_config_cache = {_toml_str(str(cfg.npm_cache_dir))} }}",
            f"startup_timeout_sec = {cfg.context7_startup_timeout_s}",
            "",
        ]
    for name in cfg.disabled_global_mcps:
        # A project entry replaces the global one entirely (Grok docs), so this disables it.
        lines += [f"[mcp_servers.{name}]", 'command = "true"', "enabled = false", ""]
    return "\n".join(lines)


def sandbox_toml(cfg: BenchConfig) -> str:
    deny = ", ".join(_toml_str(str(p)) for p in cfg.deny_paths())
    # npx (Context7 MCP) must write its cache; the workspace profile only allows CWD, /tmp, ~/.grok.
    writable = _toml_str(str(cfg.npm_cache_dir))
    return (f'[profiles.{cfg.sandbox_profile}]\nextends = "workspace"\n'
            f"read_write = [{writable}]\ndeny = [{deny}]\n")


def write_grok_files(arm: Arm, arm_dir: Path, cfg: BenchConfig) -> None:
    grok_dir = arm_dir / ".grok"
    grok_dir.mkdir(parents=True, exist_ok=True)
    (grok_dir / "config.toml").write_text(grok_config_toml(arm, cfg), encoding="utf-8")
    (grok_dir / "sandbox.toml").write_text(sandbox_toml(cfg), encoding="utf-8")


def reset_arm_dir(arm_dir: Path, cfg: BenchConfig) -> None:
    arm_dir = arm_dir.resolve()
    if cfg.home not in arm_dir.parents:
        raise WorkspaceError(f"refusing to reset {arm_dir}: not under {cfg.home}")
    arm_dir.mkdir(parents=True, exist_ok=True)
    for child in arm_dir.iterdir():
        if child.name == ".grok":
            continue
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
    write_grok_files(arm, arm_dir, cfg)
    return arm_dir


def agent_files(arm_dir: Path) -> list[Path]:
    """Files the agent left in the workspace (excluding .grok and the provided kb/)."""
    out: list[Path] = []
    for path in sorted(arm_dir.rglob("*")):
        rel = path.relative_to(arm_dir)
        if path.is_file() and rel.parts and rel.parts[0] not in {".grok", "kb"}:
            out.append(path)
    return out


def snapshot(arm_dir: Path, dest: Path) -> None:
    """Copy the agent's workspace (minus .grok and kb/) for evals and the human queue."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for path in agent_files(arm_dir):
        target = dest / path.relative_to(arm_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

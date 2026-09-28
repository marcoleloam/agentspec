"""Run one headless Codex CLI attempt (``codex exec --json``) and capture the JSONL transcript.

Everything an attempt needs is passed on the command line — no file in the
agent's folder, nothing in the user's Codex config:

* ``--ignore-user-config --ephemeral`` and an isolated ``HOME``/``CODEX_HOME``
  (``KB_BENCH_HOME/agent-home``), reset before every attempt, holding only a
  symlink to the user's ``auth.json``. Without it Codex still loads user
  skills from ``~/.agents`` (118k input tokens for a trivial prompt, spike
  2026-09-27; 10.7k with the isolated home).
* a permission profile: read everything, write only the arm folder and a
  per-attempt scratch dir, ``none`` (no read) on every deny root.
* Context7 as a per-arm ``mcp_servers.context7`` override (B and C only).
* web search off, subagents/connectors/plugins/memories off.

stdin is always closed: ``codex exec`` otherwise blocks on "Reading additional
input from stdin...".
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from kb_bench.config import Arm, BenchConfig

CODEX_BIN = os.environ.get("KB_BENCH_CODEX", "codex")
AUTH_FILE = "auth.json"
SCRATCH = "tmp"
_DROP_ENV = ("ZDOTDIR", "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED", "CODEX_THREAD_ID")


class CodexHomeError(RuntimeError):
    """The isolated Codex home cannot be prepared (e.g. the user is not logged in)."""


@dataclass(frozen=True)
class RunOutput:
    jsonl: str
    stderr: str
    exit_code: int | None
    timed_out: bool
    latency_s: float


# ── isolated HOME / CODEX_HOME ───────────────────────────────────────────────

def scratch_dir(cfg: BenchConfig) -> Path:
    return cfg.agent_home / SCRATCH


def sync_auth_back(cfg: BenchConfig) -> bool:
    """If Codex replaced the auth symlink with a refreshed file, move it back to the user's home.

    Keeps exactly one copy of the credentials (the user's) and never lets a
    rotated refresh token strand the user's own Codex login.
    """
    link = cfg.codex_home / AUTH_FILE
    if not link.exists() or link.is_symlink():
        return False
    cfg.user_auth_file.parent.mkdir(parents=True, exist_ok=True)
    os.replace(link, cfg.user_auth_file)
    os.chmod(cfg.user_auth_file, 0o600)
    link.symlink_to(cfg.user_auth_file)
    return True


def ensure_codex_home(cfg: BenchConfig) -> None:
    if not cfg.user_auth_file.is_file():
        raise CodexHomeError(f"{cfg.user_auth_file} not found — run `codex login` first")
    cfg.codex_home.mkdir(parents=True, exist_ok=True)
    scratch_dir(cfg).mkdir(parents=True, exist_ok=True)
    link = cfg.codex_home / AUTH_FILE
    if link.is_symlink() and Path(os.readlink(link)) != cfg.user_auth_file:
        link.unlink()
    if not link.exists() and not link.is_symlink():
        link.symlink_to(cfg.user_auth_file)


def _clear(folder: Path, keep: set[str]) -> None:
    for child in folder.iterdir():
        if child.name in keep:
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def reset_agent_home(cfg: BenchConfig) -> None:
    """Fresh HOME/CODEX_HOME/TMPDIR per attempt: no logs, memories or scratch survive."""
    home = cfg.agent_home.resolve()
    if cfg.home not in home.parents:
        raise CodexHomeError(f"refusing to reset {home}: not under {cfg.home}")
    sync_auth_back(cfg)
    if cfg.agent_home.is_dir():
        _clear(cfg.agent_home, keep={cfg.codex_home.name})
    if cfg.codex_home.is_dir():
        _clear(cfg.codex_home, keep={AUTH_FILE})
    ensure_codex_home(cfg)


def remove_agent_home(cfg: BenchConfig) -> bool:
    if not cfg.agent_home.exists():
        return False
    sync_auth_back(cfg)
    shutil.rmtree(cfg.agent_home)
    return True


def agent_env(cfg: BenchConfig, arm: Arm | None = None) -> dict[str, str]:
    env = dict(os.environ)
    for name in _DROP_ENV:
        env.pop(name, None)
    env["HOME"] = str(cfg.agent_home)
    env["CODEX_HOME"] = str(cfg.codex_home)
    env["TMPDIR"] = str(scratch_dir(cfg)) + "/"
    env["TMPPREFIX"] = str(scratch_dir(cfg) / "zsh")   # zsh here-documents ignore TMPDIR
    if arm is None or not arm.uses_context7:
        env.pop("CONTEXT7_API_KEY", None)
    return env


# ── command line ─────────────────────────────────────────────────────────────

def _toml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def filesystem_policy(cfg: BenchConfig, deny: tuple[Path, ...]) -> str:
    entries = [('":root"', '"read"'), ('":project_roots"', '{"." = "write"}'),
               (_toml_str(str(scratch_dir(cfg))), '"write"')]
    entries += [(_toml_str(str(p)), '"none"') for p in deny]
    return "{" + ", ".join(f"{k} = {v}" for k, v in entries) + "}"


def permission_args(cfg: BenchConfig, deny: tuple[Path, ...]) -> list[str]:
    profile = cfg.permission_profile
    return ["-c", f"permissions.{profile}.filesystem={filesystem_policy(cfg, deny)}",
            "-c", f"default_permissions={_toml_str(profile)}"]


def mcp_args(cfg: BenchConfig, arm: Arm) -> list[str]:
    if not arm.uses_context7:
        return []
    key = "mcp_servers.context7"
    args = ", ".join(_toml_str(a) for a in cfg.context7_args)
    out = ["-c", f"{key}.command={_toml_str(cfg.context7_command)}",
           "-c", f"{key}.args=[{args}]",
           "-c", f"{key}.env={{npm_config_cache = {_toml_str(str(cfg.npm_cache_dir))}}}",
           "-c", f"{key}.startup_timeout_sec={cfg.context7_startup_timeout_s}"]
    if os.environ.get("CONTEXT7_API_KEY"):
        # Forward the variable by name: the key never appears in argv or on disk.
        out += ["-c", f'{key}.env_vars=["CONTEXT7_API_KEY"]']
    return out


def feature_args(cfg: BenchConfig) -> list[str]:
    return [a for f in cfg.disabled_features for a in ("--disable", f)]


def config_args(cfg: BenchConfig, arm: Arm) -> list[str]:
    """``-c``/``--disable`` flags shared by exec, sandbox and mcp list for this arm."""
    out = ["-c", 'approval_policy="never"', "-c", 'web_search="disabled"',
           "-c", 'shell_environment_policy.exclude=["CONTEXT7_API_KEY"]',
           *permission_args(cfg, cfg.deny_paths(arm.letter)), *mcp_args(cfg, arm), *feature_args(cfg)]
    if cfg.reasoning_effort:
        out += ["-c", f"model_reasoning_effort={_toml_str(cfg.reasoning_effort)}"]
    return out


def build_argv(prompt: str, cfg: BenchConfig, arm: Arm, cwd: Path) -> list[str]:
    return [
        CODEX_BIN, "exec", "--json", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config",
        "-C", str(cwd), *(["-m", cfg.model] if cfg.model else []), *config_args(cfg, arm), "--", prompt,
    ]


# ── execution ────────────────────────────────────────────────────────────────

def _text(value: str | bytes | None) -> str:
    return value.decode(errors="replace") if isinstance(value, bytes) else (value or "")


def run_attempt(prompt: str, cwd: Path, cfg: BenchConfig, arm: Arm, *,
                timeout_s: int | None = None) -> RunOutput:
    reset_agent_home(cfg)
    started = time.monotonic()
    try:
        proc = subprocess.run(
            build_argv(prompt, cfg, arm, cwd), cwd=cwd, env=agent_env(cfg, arm), capture_output=True,
            text=True, stdin=subprocess.DEVNULL, timeout=timeout_s or cfg.attempt_timeout_s, check=False,
        )
        out = RunOutput(proc.stdout, proc.stderr[-4000:], proc.returncode, False, time.monotonic() - started)
    except subprocess.TimeoutExpired as exc:
        out = RunOutput(_text(exc.stdout), _text(exc.stderr)[-4000:], None, True, time.monotonic() - started)
    finally:
        sync_auth_back(cfg)
    return out


def _run(argv: list[str], cfg: BenchConfig, cwd: Path, *, arm: Arm | None = None,
         timeout: int = 60) -> tuple[int | None, str, str]:
    try:
        proc = subprocess.run(argv, cwd=cwd, env=agent_env(cfg, arm), capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "", str(exc)
    return proc.returncode, proc.stdout, proc.stderr


def sandbox_run(command: list[str], cwd: Path, cfg: BenchConfig, arm: Arm) -> tuple[int | None, str]:
    """Run a plain command under the attempt's permission profile — no model involved."""
    argv = [CODEX_BIN, "sandbox", "-C", str(cwd), *config_args(cfg, arm),
            "-P", cfg.permission_profile, "--", *command]
    code, out, err = _run(argv, cfg, cwd, arm=arm)
    return code, out + err


def mcp_servers(cwd: Path, cfg: BenchConfig, arm: Arm) -> set[str] | None:
    """MCP servers Codex would start for this arm (None when the listing failed)."""
    code, out, _ = _run([CODEX_BIN, *config_args(cfg, arm), "mcp", "list", "--json"], cfg, cwd, arm=arm)
    try:
        servers = json.loads(out) if code == 0 else None
    except json.JSONDecodeError:
        return None
    if not isinstance(servers, list):
        return None
    return {s.get("name") for s in servers if isinstance(s, dict) and s.get("enabled", True)}


def features_accepted(cfg: BenchConfig) -> tuple[bool, str]:
    code, _, err = _run([CODEX_BIN, *feature_args(cfg), "features", "list"], cfg, cfg.home)
    return code == 0, "" if code == 0 else err.strip()[-300:]


def auth_status(cfg: BenchConfig) -> tuple[bool, str]:
    code, out, err = _run([CODEX_BIN, "login", "status"], cfg, cfg.home)
    text = (out + err).strip()
    return code == 0 and "logged in" in text.lower(), text[-200:]


def models(cfg: BenchConfig) -> set[str]:
    code, out, _ = _run([CODEX_BIN, "debug", "models"], cfg, cfg.home, timeout=120)
    try:
        catalog = json.loads(out) if code == 0 else {}
    except json.JSONDecodeError:
        return set()
    return {m.get("slug") for m in catalog.get("models", []) if isinstance(m, dict)}


def resolved_bin() -> str | None:
    return shutil.which(CODEX_BIN)


def codex_available() -> bool:
    return resolved_bin() is not None


def version() -> str:
    try:
        return subprocess.run([CODEX_BIN, "--version"], capture_output=True, text=True, timeout=30,
                              stdin=subprocess.DEVNULL, check=False).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"

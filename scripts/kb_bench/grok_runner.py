"""Run one headless Grok CLI attempt and capture the raw NDJSON transcript."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from kb_bench.config import BenchConfig

GROK_BIN = os.environ.get("KB_BENCH_GROK", "grok")


@dataclass(frozen=True)
class RunOutput:
    ndjson: str
    stderr: str
    exit_code: int | None
    timed_out: bool
    latency_s: float


def grok_available() -> bool:
    return shutil.which(GROK_BIN) is not None


def grok_env() -> dict[str, str]:
    env = dict(os.environ)
    env["GROK_MEMORY"] = "0"
    env.pop("GROK_SANDBOX", None)
    return env


def build_argv(prompt: str, cfg: BenchConfig) -> list[str]:
    return [
        GROK_BIN, "-p", prompt,
        "-m", cfg.model,
        "--sandbox", cfg.sandbox_profile,
        "--output-format", "streaming-json",
        "--disable-web-search",
        "--no-subagents",
        "--max-turns", str(cfg.max_turns),
        "--always-approve",
    ]


def run_attempt(prompt: str, cwd: Path, cfg: BenchConfig, *, timeout_s: int | None = None) -> RunOutput:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            build_argv(prompt, cfg), cwd=cwd, env=grok_env(), capture_output=True, text=True,
            timeout=timeout_s or cfg.attempt_timeout_s, check=False,
        )
        return RunOutput(proc.stdout, proc.stderr[-4000:], proc.returncode, False,
                         time.monotonic() - started)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return RunOutput(out, err[-4000:], None, True, time.monotonic() - started)


def _json(argv: list[str], cwd: Path, timeout: int = 180) -> dict | None:
    try:
        proc = subprocess.run(argv, cwd=cwd, env=grok_env(), capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def inspect(cwd: Path) -> dict | None:
    return _json([GROK_BIN, "inspect", "--json"], cwd, timeout=60)


def mcp_doctor(cwd: Path, name: str = "context7", sandbox: str | None = None) -> tuple[bool, str]:
    """Healthy when the named server starts and discovers tools in this cwd.

    Pass the attempt's sandbox profile: a server can be healthy unsandboxed yet
    fail to start under the sandbox (e.g. npx unable to write its cache).
    """
    argv = [GROK_BIN, *(["--sandbox", sandbox] if sandbox else []), "mcp", "doctor", name]
    try:
        proc = subprocess.run(argv, cwd=cwd, env=grok_env(),
                              capture_output=True, text=True, timeout=180, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"mcp doctor failed to run: {exc}"
    text = proc.stdout + proc.stderr
    healthy = "1 healthy" in text and "tools discovered" in text
    return healthy, text.strip()[-600:]


def version() -> str:
    try:
        return subprocess.run([GROK_BIN, "--version"], capture_output=True, text=True, timeout=30, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def models() -> str:
    try:
        return subprocess.run([GROK_BIN, "models"], capture_output=True, text=True, timeout=60, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return ""

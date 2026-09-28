"""Talk to the Context7 MCP server directly over stdio — no model involved.

Codex starts MCP servers outside its sandbox, with the command, args and env
the bench passes as ``-c mcp_servers.context7.*``. This module starts the very
same process to answer three questions without spending model tokens:

* does it start and list its tools? (preflight before every B/C attempt)
* is the Context7 quota usable? (``resolve-library-id`` answers "quota exceeded")
* which bench domains does Context7 cover? (coverage probe in ``smoke``)

The API key, when present, travels only in ``CONTEXT7_API_KEY`` (the server
reads it from the environment); it is never written to disk or printed.
"""
from __future__ import annotations

import json
import os
import select
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from kb_bench.config import BenchConfig

API_KEY_ENV = "CONTEXT7_API_KEY"
REQUIRED_TOOLS = frozenset({"resolve-library-id", "query-docs"})
# Text Context7 returns *as a successful tool result* when it will not answer.
UNAVAILABLE_MARKERS = ("quota exceeded", "rate limit", "too many requests", "unauthorized",
                       "invalid api key", "api key is invalid", "create a free api key")
PROTOCOL_VERSION = "2025-06-18"


class ProbeError(RuntimeError):
    """The MCP server did not start or did not answer in time."""


@dataclass
class ProbeResult:
    ok: bool
    tools: tuple[str, ...] = ()
    detail: str = ""
    elapsed_s: float = 0.0
    calls: dict[str, str] = field(default_factory=dict)


def api_key_present() -> bool:
    return bool(os.environ.get(API_KEY_ENV))


def unavailable_text(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in UNAVAILABLE_MARKERS)


def server_env(cfg: BenchConfig, base: dict[str, str] | None = None) -> dict[str, str]:
    """Environment the server gets from Codex: the attempt env plus the npm cache."""
    env = dict(base if base is not None else os.environ)
    env["npm_config_cache"] = str(cfg.npm_cache_dir)
    return env


class _Client:
    def __init__(self, cfg: BenchConfig, cwd: Path, env: dict[str, str], timeout_s: float) -> None:
        self.timeout_s = timeout_s
        self._next_id = 0
        self._buffer = b""
        try:
            self.proc = subprocess.Popen(
                [cfg.context7_command, *cfg.context7_args], cwd=cwd, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0,
            )
        except OSError as exc:
            raise ProbeError(f"cannot start {cfg.context7_command}: {exc}") from exc

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def _send(self, message: dict) -> None:
        assert self.proc.stdin is not None
        try:
            self.proc.stdin.write((json.dumps(message) + "\n").encode())
        except (BrokenPipeError, OSError) as exc:
            raise ProbeError(f"server closed its input: {exc}") from exc

    def _lines(self, deadline: float):
        """Yield stdout lines as they arrive (own buffer: select() cannot see Python's)."""
        assert self.proc.stdout is not None
        fd = self.proc.stdout.fileno()
        while True:
            while b"\n" in self._buffer:
                line, self._buffer = self._buffer.split(b"\n", 1)
                yield line
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProbeError(f"no answer within {self.timeout_s:.0f}s")
            ready, _, _ = select.select([fd], [], [], remaining)
            if not ready:
                continue
            chunk = os.read(fd, 65536)
            if not chunk:
                raise ProbeError(f"server exited (code {self.proc.poll()})")
            self._buffer += chunk

    def _read(self, want_id: int, deadline: float) -> dict:
        for line in self._lines(deadline):
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(msg, dict) and msg.get("id") == want_id:
                if "error" in msg:
                    raise ProbeError(f"JSON-RPC error: {msg['error']}")
                return msg.get("result") or {}
        raise ProbeError("unreachable")

    def request(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        self._send({"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params or {}})
        return self._read(self._next_id, time.monotonic() + self.timeout_s)

    def notify(self, method: str) -> None:
        self._send({"jsonrpc": "2.0", "method": method})


def _result_text(result: dict) -> str:
    parts = [c.get("text", "") for c in result.get("content") or [] if isinstance(c, dict)]
    return "\n".join(p for p in parts if isinstance(p, str))


def probe(cfg: BenchConfig, cwd: Path, *, env: dict[str, str] | None = None,
          resolve: tuple[str, ...] = (), timeout_s: float | None = None) -> ProbeResult:
    """Start the server, handshake, list tools and optionally ``resolve-library-id`` each name.

    ``ok`` means the server started, exposes the Context7 tools and — when
    names were resolved — the first answer was not a quota/auth refusal.
    """
    started = time.monotonic()
    client = _Client(cfg, cwd, server_env(cfg, env), timeout_s or cfg.context7_startup_timeout_s)
    try:
        client.request("initialize", {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                                      "clientInfo": {"name": "kb_bench", "version": "1"}})
        client.notify("notifications/initialized")
        tools = tuple(sorted(t.get("name", "") for t in client.request("tools/list").get("tools") or []))
        missing = REQUIRED_TOOLS - set(tools)
        if missing:
            return ProbeResult(False, tools, f"tools missing: {sorted(missing)}", time.monotonic() - started)
        calls: dict[str, str] = {}
        for name in resolve:
            result = client.request("tools/call", {"name": "resolve-library-id",
                                                   "arguments": {"libraryName": name, "query": name}})
            calls[name] = _result_text(result)
            if unavailable_text(calls[name]):
                return ProbeResult(False, tools, f"Context7 refused: {calls[name][:160]}",
                                   time.monotonic() - started, calls)
        return ProbeResult(True, tools, f"{len(tools)} tools", time.monotonic() - started, calls)
    except ProbeError as exc:
        return ProbeResult(False, (), str(exc), time.monotonic() - started)
    finally:
        client.close()

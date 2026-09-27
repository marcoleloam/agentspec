"""Isolation verdict for one attempt (DESIGN Decisão 5).

The sandbox enforces isolation; this module proves it per attempt and catches
a sandbox that silently failed to apply (a *completed* read under a deny root).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from kb_bench.transcript import Transcript

WEB_TOOLS = frozenset({"web_search", "web_fetch", "fetch_url", "browse", "search_web"})
CONTEXT7_PREFIX = "context7__"
MCP_MISSING_MARKERS = ("No MCP tools are available", "did not connect", "handshake closed")
_TRANSPORT_ERRORS = ("timed out", "timeout", "connection", "ECONN", "rate limit", "429", "503", "not connected")


@dataclass(frozen=True)
class IsolationVerdict:
    contaminated: bool
    reasons: tuple[str, ...]
    kb_access_denied: int
    context7_calls: int
    context7_failed: int
    context7_transport_failures: int
    mcp_missing: bool = False

    @property
    def context7_unavailable(self) -> bool:
        """Every Context7 call failed on transport — the MCP was effectively down."""
        return self.context7_failed > 0 and self.context7_calls == 0 and \
            self.context7_transport_failures == self.context7_failed


def _norm(path: str, cwd: Path) -> Path:
    p = Path(os.path.expanduser(path))
    if not p.is_absolute():
        p = cwd / p
    return Path(os.path.normpath(p))


def _variants(root: Path) -> tuple[str, ...]:
    """macOS resolves /tmp → /private/tmp; match both spellings."""
    s = str(root)
    out = {s}
    if s.startswith("/private/"):
        out.add(s[len("/private"):])
    return tuple(out)


def under(path: Path, roots: tuple[Path, ...]) -> bool:
    text = str(path)
    for root in roots:
        for variant in _variants(root):
            if text == variant or text.startswith(variant.rstrip("/") + "/"):
                return True
    return False


def check(t: Transcript, *, uses_context7: bool, deny: tuple[Path, ...], cwd: Path) -> IsolationVerdict:
    reasons: list[str] = []
    denied = c7_ok = c7_fail = c7_transport = 0
    deny_strings = tuple(v for r in deny for v in _variants(r))
    for call in t.tool_calls:
        hits = [p for p in call.paths if under(_norm(p, cwd), deny)]
        if call.command and any(d in call.command for d in deny_strings):
            hits.append(call.command[:160])
        if hits:
            if call.status == "completed" and not call.permission_denied and call.returned_data:
                reasons.append(f"{call.tool} accessed denied path: {hits[0]}")
            else:
                denied += 1
        if call.mcp_tool and call.mcp_tool.startswith(CONTEXT7_PREFIX):
            if not uses_context7:
                reasons.append(f"context7 used in a non-MCP arm: {call.mcp_tool}")
            if call.status == "completed":
                c7_ok += 1
            elif call.status == "failed":
                c7_fail += 1
                if any(e.lower() in call.output_text.lower() for e in _TRANSPORT_ERRORS):
                    c7_transport += 1
        if call.tool in WEB_TOOLS or (call.mcp_tool and call.mcp_tool.split("__")[-1] in WEB_TOOLS):
            reasons.append(f"web tool used: {call.mcp_tool or call.tool}")
    mcp_missing = uses_context7 and c7_ok == 0 and any(
        marker in call.output_text for call in t.tool_calls for marker in MCP_MISSING_MARKERS
    )
    return IsolationVerdict(bool(reasons), tuple(reasons), denied, c7_ok, c7_fail, c7_transport, mcp_missing)

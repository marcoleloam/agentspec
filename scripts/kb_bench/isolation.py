"""Isolation verdict for one attempt (DESIGN Decisão 5, Codex executor).

The permission profile enforces isolation; this module proves it per attempt
from the JSONL transcript and catches a profile that silently failed to apply:

* a *completed* shell command naming a deny root that returned data without a
  denial message, or a completed file change under a deny root → contaminated;
  the same access answered with "Operation not permitted" is only counted
  (``kb_access_denied``). Codex often declines to even try a read it knows the
  policy forbids — that is neither contamination nor a denial.
* AT-004, literally: a completed command that returned data and names — in
  its command line or its output — a path containing ``/kb/`` (or an
  AgentSpec plugin/skill folder) outside the arm folder (its own ``./kb``) →
  contaminated, whether or not that path is a deny root. Round 1 leaked
  exactly this way: arm D's ``grep -r`` printed hits from ``arms/a/kb``.
* any Context7 call in arm A/D, or any web search → contaminated.
* Context7 calls whose *completed* result is a quota/auth refusal ("Monthly
  quota exceeded…") count as unavailable, not as successful calls, and are
  counted in ``context7_refused`` — the loop aborts the run on any of them.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from kb_bench.context7_probe import unavailable_text
from kb_bench.transcript import DENIAL_MARKERS, Transcript

WEB_TOOLS = frozenset({"web_search", "web_fetch", "fetch_url", "browse", "search_web"})
CONTEXT7_PREFIX = "context7__"
MCP_MISSING_MARKERS = ("failed to start", "not connected", "handshake", "unknown mcp server",
                       "no such server", "timed out while starting", "program not found")
# A path-like token (no shell metacharacters, stops at ':' so "path:line" grep output splits).
_PATH_TOKEN = re.compile(r"[^\s'\"`;|&()<>:=,]+")
# AgentSpec knowledge outside the arm: any KB folder, the plugin's knowledge skills, the plugin itself.
_KNOWLEDGE_SEGMENTS = ("kb",)
_KNOWLEDGE_SKILLS = ("data-engineering-guide", "sdd-workflow", "kb-build", "agent-router")
_NOT_FOUND = ("No such file or directory", "cannot access", "not found")
_TRANSPORT_ERRORS = ("timed out", "timeout", "connection", "ECONN", "rate limit", "429", "503",
                     "not connected")


@dataclass(frozen=True)
class IsolationVerdict:
    contaminated: bool
    reasons: tuple[str, ...]
    kb_access_denied: int
    context7_calls: int
    context7_failed: int
    context7_transport_failures: int
    mcp_missing: bool = False
    context7_refused: int = 0    # completed calls answered with a quota/auth refusal

    @property
    def context7_unavailable(self) -> bool:
        """Every Context7 call failed on transport or was refused (quota/auth)."""
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


def _mentions(command: str, deny_strings: tuple[str, ...]) -> str | None:
    for d in deny_strings:
        idx = command.find(d)
        # a deny root is a path prefix: "/x/agentspec" must not match "/x/agentspec-notes"
        if idx >= 0 and (idx + len(d) == len(command) or command[idx + len(d)] in "/ '\"\t\n;)|&*"):
            return d
    return None


def _knowledge_path(token: str) -> bool:
    parts = [p for p in token.split("/") if p]
    if "/" not in token or not parts:
        return False
    if any(p in _KNOWLEDGE_SEGMENTS for p in parts[:-1]) or (token.endswith("/kb") or token.endswith("/kb/")):
        return True
    if any(p == "agentspec" or p.startswith("agentspec___") for p in parts):
        return True
    return any(parts[i] == "skills" and parts[i + 1] in _KNOWLEDGE_SKILLS for i in range(len(parts) - 1))


def foreign_knowledge(text: str, cwd: Path) -> str | None:
    """First path in ``text`` that points at AgentSpec knowledge outside the arm folder ``cwd`` (AT-004)."""
    own = Path(os.path.normpath(cwd))
    for line in text.splitlines():
        if any(m in line for m in (*DENIAL_MARKERS, *_NOT_FOUND)):
            continue  # a refused or missing read leaked nothing
        for token in _PATH_TOKEN.findall(line):
            if not _knowledge_path(token) or any(ch in token for ch in "*?[{$"):
                continue
            if not under(_norm(token, cwd), (own,)):
                return token
    return None


def check(t: Transcript, *, uses_context7: bool, deny: tuple[Path, ...], cwd: Path) -> IsolationVerdict:
    reasons: list[str] = []
    denied = c7_ok = c7_fail = c7_transport = c7_refused = 0
    deny_strings = tuple(v for r in deny for v in _variants(r))
    for call in t.tool_calls:
        hits = [p for p in call.paths if under(_norm(p, cwd), deny)]
        if call.command and _mentions(call.command, deny_strings):
            hits.append(call.command[:160])
        flagged = False
        if hits:
            if call.status == "completed" and not call.permission_denied and call.returned_data:
                reasons.append(f"{call.tool} accessed denied path: {hits[0]}")
                flagged = True
            elif call.status != "in_progress":
                denied += 1
        if not flagged and call.tool == "command_execution" and call.status == "completed" \
                and call.returned_data:
            # The command line counts only when nothing was refused; output lines are
            # filtered one by one, so a partly denied `grep -r` still exposes its hits.
            leak = (None if call.permission_denied else foreign_knowledge(call.command or "", cwd)) \
                or foreign_knowledge(call.output_text, cwd)
            if leak:
                reasons.append(f"{call.tool} read AgentSpec knowledge outside ./kb (AT-004): {leak[:160]}")
        if call.mcp_tool and call.mcp_tool.startswith(CONTEXT7_PREFIX):
            if not uses_context7:
                reasons.append(f"context7 used in a non-MCP arm: {call.mcp_tool}")
            refused = unavailable_text(call.output_text)
            if call.status == "completed" and not refused:
                c7_ok += 1
            elif call.status in {"completed", "failed"}:
                c7_fail += 1
                c7_refused += bool(refused)
                if refused or any(e.lower() in call.output_text.lower() for e in _TRANSPORT_ERRORS):
                    c7_transport += 1
        if call.tool in WEB_TOOLS or (call.mcp_tool and call.mcp_tool.split("__")[-1] in WEB_TOOLS):
            reasons.append(f"web tool used: {call.mcp_tool or call.tool}")
    mcp_missing = uses_context7 and c7_ok == 0 and any(
        "context7" in err.lower() and any(m in err.lower() for m in MCP_MISSING_MARKERS)
        for err in [*t.errors, *(c.output_text for c in t.mcp_calls(CONTEXT7_PREFIX))]
    )
    return IsolationVerdict(bool(reasons), tuple(reasons), denied, c7_ok, c7_fail, c7_transport, mcp_missing,
                            c7_refused)

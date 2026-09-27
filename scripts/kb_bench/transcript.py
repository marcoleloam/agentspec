"""Parse Grok CLI ``--output-format streaming-json`` NDJSON into a Transcript.

Event shapes observed with grok 1.0.41 (spike, 2026-09-23):
  {"type": "text", "data": "..."}
  {"type": "tool_call", "toolCallId": ..., "toolName": "read_file", "rawInput": {...}}
  {"type": "tool_call_update", "toolCallId": ..., "status": "completed"|"failed"|null,
   "locations": [{"path": ...}], "rawOutput": {"PermissionDenied": ...}}
  {"type": "end", "stopReason": ..., "usage": {"total_tokens": ...}, "total_cost_usd": ...,
   "num_turns": ..., "modelUsage": {"grok-4.7-build": {...}}}
MCP calls arrive as toolName "use_tool" with rawInput.tool_name "<server>__<tool>".
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

_PATH_KEYS = ("target_file", "path", "file_path", "directory", "dir", "target_directory")


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    tool: str
    mcp_tool: str | None
    paths: tuple[str, ...]
    command: str | None
    status: str
    permission_denied: bool
    output_text: str = ""
    returned_data: bool = True


@dataclass
class Transcript:
    tool_calls: list[ToolCall] = field(default_factory=list)
    text: str = ""
    stop_reason: str | None = None
    input_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    num_turns: int | None = None
    model: str | None = None
    session_id: str | None = None
    ended: bool = False
    malformed_lines: int = 0

    def mcp_calls(self, prefix: str) -> list[ToolCall]:
        return [c for c in self.tool_calls if c.mcp_tool and c.mcp_tool.startswith(prefix)]


def _content_text(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        inner = item.get("content") if isinstance(item, dict) else None
        if isinstance(inner, dict) and isinstance(inner.get("text"), str):
            parts.append(inner["text"])
    return "\n".join(parts)


def _raw_output_text(raw_out: dict[str, Any]) -> str:
    """MCP results arrive with empty ``content`` and the text under rawOutput.output."""
    output = raw_out.get("output")
    if isinstance(output, dict):
        return "\n".join(str(v) for v in output.values() if isinstance(v, (str, int, float)))
    if isinstance(output, str):
        return output
    for key in ("error", "Error", "message"):
        if isinstance(raw_out.get(key), str):
            return raw_out[key]
    return ""


_DENIAL_MARKERS = ("Permission denied", "Operation not permitted", "IO error for operation")


def _stream_text(value: Any) -> str:
    """Tool streams arrive as str or as a list of byte values (GrepSearch stdout)."""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(b, int) and 0 <= b < 256 for b in value):
        return bytes(value).decode("utf-8", errors="replace")
    return ""


def _raw_streams_text(raw_out: dict[str, Any]) -> str:
    return "\n".join(t for t in (_stream_text(raw_out.get("stdout")), _stream_text(raw_out.get("stderr"))) if t)


def _returned_data(raw_out: dict[str, Any]) -> bool:
    """False when a search tool demonstrably returned nothing (e.g. grep with 0 matches)."""
    if raw_out.get("type") == "GrepSearch":
        return bool(raw_out.get("match_count")) or bool(raw_out.get("file_matches"))
    return True


def _paths_from_input(raw_in: dict[str, Any]) -> set[str]:
    found = {raw_in[k] for k in _PATH_KEYS if isinstance(raw_in.get(k), str)}
    for key in ("paths", "files"):
        if isinstance(raw_in.get(key), list):
            found.update(p for p in raw_in[key] if isinstance(p, str))
    return found


def parse_ndjson(raw: str) -> Transcript:
    t = Transcript()
    calls: dict[str, dict[str, Any]] = {}
    finals: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            t.malformed_lines += 1
            continue
        kind = ev.get("type")
        if kind == "text":
            t.text += ev.get("data", "") or ""
        elif kind == "tool_call":
            cid = ev.get("toolCallId", f"anon-{len(order)}")
            if cid not in calls:
                order.append(cid)
            calls[cid] = ev
        elif kind == "tool_call_update":
            cur = finals.setdefault(ev.get("toolCallId", ""), {"locations": [], "content": ""})
            cur["locations"] += [loc.get("path") for loc in ev.get("locations") or [] if loc.get("path")]
            if ev.get("status"):
                cur["status"] = ev["status"]
                cur["rawOutput"] = ev.get("rawOutput") or {}
                cur["content"] = _content_text(ev.get("content")) or _raw_output_text(cur["rawOutput"])
        elif kind == "end":
            usage = ev.get("usage") or {}
            t.ended = True
            t.stop_reason = ev.get("stopReason")
            t.num_turns = ev.get("num_turns")
            t.input_tokens = usage.get("input_tokens")
            t.total_tokens = usage.get("total_tokens")
            t.cost_usd = ev.get("total_cost_usd")
            t.session_id = ev.get("sessionId")
            t.model = next(iter(ev.get("modelUsage") or {}), None)
    for cid in order:
        call, fin = calls[cid], finals.get(cid, {})
        raw_in = call.get("rawInput") or {}
        tool = call.get("toolName", "")
        paths = _paths_from_input(raw_in)
        paths.update(fin.get("locations", []))
        raw_out = fin.get("rawOutput") or {}
        command = raw_in.get("command") if isinstance(raw_in.get("command"), str) else None
        t.tool_calls.append(ToolCall(
            call_id=cid,
            tool=tool,
            mcp_tool=raw_in.get("tool_name") if tool == "use_tool" else None,
            paths=tuple(sorted(paths)),
            command=command,
            status=fin.get("status", "pending"),
            permission_denied="PermissionDenied" in raw_out or any(
                marker in text for marker in _DENIAL_MARKERS
                for text in (fin.get("content", ""), _raw_streams_text(raw_out))
            ),
            output_text=(fin.get("content", "") + "\n" + _raw_streams_text(raw_out)).strip()[:8000],
            returned_data=_returned_data(raw_out),
        ))
    return t

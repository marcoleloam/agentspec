"""Parse ``codex exec --json`` JSONL into a Transcript.

Event shapes observed with codex-cli 0.157.0 (spikes, 2026-09-27):
  {"type": "thread.started", "thread_id": ...}
  {"type": "turn.started"}
  {"type": "item.started" | "item.updated" | "item.completed", "item": {"id": ..., "type": ..., ...}}
  {"type": "turn.completed", "usage": {"input_tokens", "cached_input_tokens",
   "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens"}}
  {"type": "turn.failed", "error": {"message": ...}}
  {"type": "error", "message": ...}          # also transient "Reconnecting... n/5"
Item types: agent_message {text}; command_execution {command, aggregated_output,
exit_code, status}; mcp_tool_call {server, tool, arguments, result{content[]},
error, status}; file_change {changes[{path, kind}], status}; web_search;
reasoning; todo_list; error {message}. No model name and no USD cost are
reported (ChatGPT login).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

DENIAL_MARKERS = ("Operation not permitted", "Permission denied", "permission denied",
                  "blocked by policy", "prohibited by filesystem policy")
_TOOL_ITEMS = frozenset({"command_execution", "mcp_tool_call", "file_change", "web_search"})


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    tool: str                    # item type: command_execution | mcp_tool_call | file_change | web_search
    mcp_tool: str | None         # "<server>__<tool>" for MCP calls
    paths: tuple[str, ...]
    command: str | None
    status: str                  # completed | failed | declined | in_progress
    permission_denied: bool
    output_text: str = ""
    returned_data: bool = True
    exit_code: int | None = None


@dataclass
class Transcript:
    tool_calls: list[ToolCall] = field(default_factory=list)
    text: str = ""
    thread_id: str | None = None
    turns: int = 0
    ended: bool = False                  # a turn.completed was seen and no turn.failed
    failed: bool = False
    error_message: str = ""
    errors: list[str] = field(default_factory=list)
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_output_tokens: int | None = None
    malformed_lines: int = 0

    @property
    def total_tokens(self) -> int | None:
        if self.input_tokens is None and self.output_tokens is None:
            return None
        return (self.input_tokens or 0) + (self.output_tokens or 0)

    @property
    def fresh_tokens(self) -> int | None:
        """Input not served from cache, plus output — what the budget counts."""
        if self.total_tokens is None:
            return None
        return self.total_tokens - (self.cached_input_tokens or 0)

    def mcp_calls(self, prefix: str) -> list[ToolCall]:
        return [c for c in self.tool_calls if c.mcp_tool and c.mcp_tool.startswith(prefix)]


def _add(current: int | None, value: Any) -> int | None:
    return (current or 0) + value if isinstance(value, int) else current


def _mcp_output(item: dict[str, Any]) -> str:
    parts: list[str] = []
    result = item.get("result")
    if isinstance(result, dict):
        for content in result.get("content") or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                parts.append(content["text"])
    error = item.get("error")
    if isinstance(error, dict):
        error = error.get("message")
    if isinstance(error, str) and error:
        parts.append(error)
    return "\n".join(parts)


def _tool_call(item: dict[str, Any]) -> ToolCall:
    kind = item.get("type", "")
    status = str(item.get("status") or "in_progress")
    cid = str(item.get("id", ""))
    if kind == "command_execution":
        output = str(item.get("aggregated_output") or "")
        command = item.get("command") if isinstance(item.get("command"), str) else None
        return ToolCall(cid, kind, None, (), command, status,
                        permission_denied=any(m in output for m in DENIAL_MARKERS),
                        output_text=output[:8000], returned_data=bool(output.strip()),
                        exit_code=item.get("exit_code") if isinstance(item.get("exit_code"), int) else None)
    if kind == "mcp_tool_call":
        output = _mcp_output(item)
        return ToolCall(cid, kind, f"{item.get('server', '')}__{item.get('tool', '')}", (), None, status,
                        permission_denied=False, output_text=output[:8000], returned_data=bool(output.strip()))
    if kind == "file_change":
        paths = tuple(sorted(c["path"] for c in item.get("changes") or []
                             if isinstance(c, dict) and isinstance(c.get("path"), str)))
        return ToolCall(cid, kind, None, paths, None, status, permission_denied=False)
    query = item.get("query") if isinstance(item.get("query"), str) else ""
    return ToolCall(cid, kind, None, (), None, status, permission_denied=False, output_text=query)


def parse_jsonl(raw: str) -> Transcript:
    t = Transcript()
    items: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            t.malformed_lines += 1
            continue
        if not isinstance(ev, dict):
            t.malformed_lines += 1
            continue
        kind = ev.get("type")
        if kind == "thread.started":
            t.thread_id = ev.get("thread_id")
        elif kind in {"item.started", "item.updated", "item.completed"}:
            item = ev.get("item") or {}
            iid = str(item.get("id") or f"anon-{len(order)}")
            if iid not in items:
                order.append(iid)
            items[iid] = item
        elif kind == "turn.completed":
            usage = ev.get("usage") or {}
            t.turns += 1
            t.ended = not t.failed
            t.input_tokens = _add(t.input_tokens, usage.get("input_tokens"))
            t.cached_input_tokens = _add(t.cached_input_tokens, usage.get("cached_input_tokens"))
            t.output_tokens = _add(t.output_tokens, usage.get("output_tokens"))
            t.reasoning_output_tokens = _add(t.reasoning_output_tokens, usage.get("reasoning_output_tokens"))
        elif kind == "turn.failed":
            t.failed, t.ended = True, False
            error = ev.get("error") or {}
            t.error_message = str(error.get("message", "") if isinstance(error, dict) else error)
        elif kind == "error":
            t.errors.append(str(ev.get("message", "")))
    texts: list[str] = []
    for iid in order:
        item = items[iid]
        kind = item.get("type")
        if kind == "agent_message" and isinstance(item.get("text"), str):
            texts.append(item["text"])
        elif kind == "error":
            t.errors.append(str(item.get("message", "")))
        elif kind in _TOOL_ITEMS:
            t.tool_calls.append(_tool_call(item))
    t.text = "\n".join(texts)
    return t

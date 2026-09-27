#!/usr/bin/env python3
"""Stand-in for the Grok CLI used by tests/test_kb_bench.py.

Emits NDJSON in the shape observed from grok 1.0.41. Behaviour is chosen by
FAKE_SCENARIO: solve | fail_then_solve | never | hang | leak | c7 | c7_down | mcp_missing.
The agent "writes" out.txt in cwd; attempts are counted in .grok/fake_attempts.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def emit(event: dict) -> None:
    print(json.dumps(event))


def end(tokens: int = 1000, cost: float = 0.01) -> None:
    emit({"type": "end", "stopReason": "end_turn", "sessionId": "fake-session",
          "usage": {"input_tokens": tokens - 100, "total_tokens": tokens},
          "num_turns": 2, "total_cost_usd": cost, "modelUsage": {"grok-4.7-build": {}}})


def tool(call_id: str, name: str, raw_input: dict, status: str, raw_output: dict | None = None,
         text: str = "") -> None:
    emit({"type": "tool_call", "toolCallId": call_id, "toolName": name, "rawInput": raw_input,
          "status": "pending", "content": [], "locations": []})
    content = [{"type": "content", "content": {"type": "text", "text": text}}] if text else []
    emit({"type": "tool_call_update", "toolCallId": call_id, "status": status, "content": content,
          "rawOutput": raw_output or {}, "locations": []})


def main(args: list[str]) -> int:
    if args[:1] == ["--sandbox"]:
        args = args[2:]
    if args[:1] == ["--version"]:
        print("grok 9.9.9 (fake)")
        return 0
    if args[:1] == ["models"]:
        print("Available models:\n  * grok-4.7 (default)")
        return 0
    cfg = Path(".grok/config.toml")
    has_c7 = cfg.is_file() and "[mcp_servers.context7]" in cfg.read_text()
    if args[:2] == ["inspect", "--json"]:
        print(json.dumps({"mcpServers": [{"name": "context7"}] if has_c7 else []}))
        return 0
    if args[:2] == ["mcp", "doctor"]:
        if os.environ.get("FAKE_DOCTOR") == "down" or not has_c7:
            print("Found 0 healthy, 1 failing.")
        else:
            print("  ✓ 2 tools discovered\nFound 1 healthy, 0 failing.")
        return 0
    if "-p" not in args:
        return 2

    counter = Path(".grok/fake_attempts")
    attempt = int(counter.read_text()) + 1 if counter.is_file() else 1
    counter.write_text(str(attempt))
    scenario = os.environ.get("FAKE_SCENARIO", "solve")
    out = Path("out.txt")

    if scenario == "hang":
        emit({"type": "text", "data": "thinking..."})
        return 1
    if scenario == "leak":
        path = os.environ["FAKE_DENY_PATH"]
        tool("c1", "read_file", {"target_file": path}, "completed", {"type": "ReadFile"}, "secret kb")
        end()
        return 0
    if scenario == "mcp_missing":
        tool("s1", "search_tool", {"query": "context7"}, "completed", {},
             '{"results": [], "note": "No MCP tools are available in this session."}')
    if scenario in {"c7", "c7_down"}:
        ok = scenario == "c7"
        tool("c1", "use_tool", {"tool_name": "context7__query-docs", "tool_input": {"libraryId": "/x/y"}},
             "completed" if ok else "failed",
             {"type": "MCP", "output": {"OkayOutput": "docs"}} if ok else {"error": "connection refused"},
             "" if ok else "connection refused")
    good = scenario in {"solve", "c7"} or (scenario == "fail_then_solve" and attempt >= 2)
    out.write_text("hello\n" if good else "nope\n")
    emit({"type": "text", "data": "done"})
    end()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

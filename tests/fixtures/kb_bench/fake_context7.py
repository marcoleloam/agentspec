#!/usr/bin/env python3
"""Stand-in for ``@upstash/context7-mcp`` over stdio JSON-RPC (tests only, offline).

``resolve-library-id`` answers with real outputs recorded in
context7_resolve_samples.json. FAKE_C7 selects a failure: down (exit at
once) | quota ("Monthly quota exceeded", as the free tier answers) | notools.
Each start appends the CONTEXT7_API_KEY presence to $FAKE_STATE_DIR/c7.jsonl.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SAMPLES = json.loads((Path(__file__).with_name("context7_resolve_samples.json")).read_text())["resolve"]
QUOTA = "Monthly quota exceeded. Create a free API key at https://context7.com/dashboard for more requests."
TOOLS = [{"name": "resolve-library-id", "inputSchema": {"type": "object"}},
         {"name": "query-docs", "inputSchema": {"type": "object"}}]


def sample_for(name: str) -> str:
    words = set(name.lower().replace("-", " ").split())
    best = max(SAMPLES, key=lambda k: len(words & set(k.lower().replace("-", " ").split())))
    return SAMPLES[best] if words & set(best.lower().replace("-", " ").split()) else "No libraries found."


def reply(msg_id, result: dict) -> None:
    print(json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}), flush=True)


def main() -> int:
    mode = os.environ.get("FAKE_C7", "")
    state = os.environ.get("FAKE_STATE_DIR")
    if state:
        Path(state).mkdir(parents=True, exist_ok=True)
        with (Path(state) / "c7.jsonl").open("a") as fh:
            fh.write(json.dumps({"has_key": "CONTEXT7_API_KEY" in os.environ,
                                 "npm_cache": os.environ.get("npm_config_cache")}) + "\n")
    if mode == "down":
        return 1
    for line in sys.stdin:
        msg = json.loads(line)
        method, msg_id = msg.get("method"), msg.get("id")
        if method == "initialize":
            reply(msg_id, {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                           "serverInfo": {"name": "fake-context7", "version": "0"}})
        elif method == "tools/list":
            reply(msg_id, {"tools": [] if mode == "notools" else TOOLS})
        elif method == "tools/call":
            name = (msg.get("params") or {}).get("arguments", {}).get("libraryName", "")
            text = QUOTA if mode == "quota" else sample_for(name)
            reply(msg_id, {"content": [{"type": "text", "text": text}]})
    return 0


if __name__ == "__main__":
    sys.exit(main())

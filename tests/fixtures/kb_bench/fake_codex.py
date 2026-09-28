#!/usr/bin/env python3
"""Stand-in for the Codex CLI used by tests/test_kb_bench.py (no model, no network).

Implements the subcommands the bench calls: ``--version``, ``login status``,
``debug models``, ``features list``, ``mcp list --json``, ``sandbox -- CMD``
and ``exec --json -- PROMPT``. ``-c`` overrides are parsed as TOML (so an
invalid override fails the test) and ``permissions.<p>.filesystem`` entries
set to ``"none"`` are enforced by ``sandbox``.

``exec`` emits JSONL in the shape recorded from codex-cli 0.157.0. Behaviour
is chosen by FAKE_SCENARIO: solve | fail_then_solve | never | hang | leak | c7
| c7_down | c7_quota | mcp_missing | turn_failed | usage_limit | canary_denied.
Every exec appends one JSON line (argv, env facts, stdin kind) to
``$FAKE_STATE_DIR/exec.jsonl``; the agent "writes" out.txt in its -C folder.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tomllib
from pathlib import Path

KNOWN_FEATURES = {"multi_agent", "apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
                  "computer_use", "in_app_browser", "image_generation", "memories", "tool_suggest"}
QUOTA = "Monthly quota exceeded. Create a free API key at https://context7.com/dashboard for more requests."


def emit(event: dict) -> None:
    print(json.dumps(event), flush=True)


def item(kind: str, **fields) -> None:
    emit({"type": "item.started", "item": {**fields, "status": "in_progress"}})
    emit({"type": kind, "item": fields})


def done(tokens: int = 1000) -> None:
    emit({"type": "turn.completed", "usage": {"input_tokens": tokens - 100, "cached_input_tokens": 400,
                                              "cache_write_input_tokens": 0, "output_tokens": 100,
                                              "reasoning_output_tokens": 10}})


def parse(argv: list[str]) -> dict:
    out = {"config": {}, "disabled": [], "cwd": None, "positional": [], "rest": []}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--":
            out["rest"] = argv[i + 1:]
            break
        if a in {"-c", "--config"}:
            key, _, raw = argv[i + 1].partition("=")
            try:
                out["config"][key] = tomllib.loads(f"v = {raw}")["v"]
            except tomllib.TOMLDecodeError:
                print(f"invalid -c override (not TOML): {argv[i + 1]}", file=sys.stderr)
                sys.exit(2)
            i += 2
            continue
        if a == "--disable":
            out["disabled"].append(argv[i + 1])
            i += 2
            continue
        if a in {"-C", "--cd"}:
            out["cwd"] = argv[i + 1]
            i += 2
            continue
        if a in {"-m", "--model", "-P", "-p"}:
            i += 2
            continue
        if not a.startswith("-"):
            out["positional"].append(a)
        i += 1
    return out


def deny_roots(config: dict) -> list[str]:
    roots: list[str] = []
    for key, value in config.items():
        if key.startswith("permissions.") and key.endswith(".filesystem") and isinstance(value, dict):
            roots += [p for p, mode in value.items() if mode == "none"]
    return roots


def logged_in() -> bool:
    auth = Path(os.environ.get("CODEX_HOME", "")) / "auth.json"
    return auth.exists()


def cmd_sandbox(opts: dict) -> int:
    command = opts["rest"]
    for arg in command:
        for root in deny_roots(opts["config"]):
            if arg == root or arg.startswith(root.rstrip("/") + "/"):
                print(f"{command[0]}: {arg}: Operation not permitted", file=sys.stderr)
                return 1
    return subprocess.run(command, cwd=opts["cwd"], check=False).returncode


def record(opts: dict, argv: list[str]) -> int:
    state = Path(os.environ["FAKE_STATE_DIR"])
    state.mkdir(parents=True, exist_ok=True)
    log = state / "exec.jsonl"
    attempt = (len(log.read_text().splitlines()) if log.is_file() else 0) + 1
    stdin_mode = os.fstat(0).st_mode
    with log.open("a") as fh:
        fh.write(json.dumps({
            "argv": argv, "home": os.environ.get("HOME"), "codex_home": os.environ.get("CODEX_HOME"),
            "tmpdir": os.environ.get("TMPDIR"), "has_c7_key": "CONTEXT7_API_KEY" in os.environ,
            "stdin_devnull": stat.S_ISCHR(stdin_mode) and os.path.samestat(os.fstat(0), os.stat(os.devnull)),
            "auth_is_symlink": (Path(os.environ.get("CODEX_HOME", "")) / "auth.json").is_symlink(),
            "config_keys": sorted(opts["config"]),
        }) + "\n")
    return attempt


def cmd_exec(opts: dict, argv: list[str]) -> int:
    if not logged_in():
        emit({"type": "turn.failed", "error": {"message": "unexpected status 401 Unauthorized"}})
        return 1
    attempt = record(opts, argv)
    scenario = os.environ.get("FAKE_SCENARIO", "solve")
    prompt = opts["rest"][0] if opts["rest"] else ""
    cwd = Path(opts["cwd"] or ".")
    emit({"type": "thread.started", "thread_id": f"fake-{attempt}"})
    emit({"type": "turn.started"})
    if "cat " in prompt and "canary" in prompt:
        if scenario == "canary_denied":
            path = prompt.rsplit("cat ", 1)[1].strip()
            item("item.completed", id="item_0", type="command_execution", command=f"/bin/zsh -lc 'cat {path}'",
                 aggregated_output=f"cat: {path}: Operation not permitted\n", exit_code=1, status="failed")
        else:
            item("item.completed", id="item_0", type="agent_message",
                 text="I can't run that command: the path is denied by the active filesystem policy.")
        done()
        return 0
    if scenario == "hang":
        item("item.completed", id="item_0", type="agent_message", text="thinking...")
        return 1
    if scenario in {"turn_failed", "usage_limit"}:
        message = ("You've hit your usage limit. Try again later." if scenario == "usage_limit"
                   else "stream disconnected before completion")
        emit({"type": "error", "message": f"Reconnecting... 1/5 ({message})"})
        emit({"type": "turn.failed", "error": {"message": message}})
        return 1
    if scenario == "leak":
        path = os.environ["FAKE_DENY_PATH"]
        item("item.completed", id="item_0", type="command_execution", command=f"/bin/zsh -lc 'cat {path}'",
             aggregated_output="secret kb\n", exit_code=0, status="completed")
        done()
        return 0
    if scenario == "mcp_missing":
        emit({"type": "error", "message": "MCP client for `context7` failed to start: program not found"})
    if scenario in {"c7", "c7_down", "c7_quota"}:
        ok = scenario != "c7_down"
        text = {"c7": "### Incremental models", "c7_quota": QUOTA}.get(scenario)
        item("item.completed", id="item_1", type="mcp_tool_call", server="context7", tool="query-docs",
             arguments={"libraryId": "/x/y", "query": "q"},
             result={"content": [{"type": "text", "text": text}], "structured_content": None} if ok else None,
             error=None if ok else {"message": "connection refused"}, status="completed" if ok else "failed")
    good = scenario in {"solve", "c7"} or (scenario == "fail_then_solve" and attempt >= 2)
    (cwd / "out.txt").write_text("hello\n" if good else "nope\n")
    item("item.completed", id="item_2", type="file_change", changes=[{"path": str(cwd / "out.txt"), "kind": "add"}],
         status="completed")
    item("item.completed", id="item_3", type="agent_message", text="done")
    done()
    return 0


def main(argv: list[str]) -> int:
    if "--version" in argv:
        print("codex-cli 9.9.9 (fake)")
        return 0
    opts = parse(argv)
    unknown = [f for f in opts["disabled"] if f not in KNOWN_FEATURES]
    if unknown:
        print(f"Error: Unknown feature flag: {unknown[0]}", file=sys.stderr)
        return 1
    pos = opts["positional"]
    if pos[:2] == ["login", "status"]:
        print("Logged in using ChatGPT" if logged_in() else "Not logged in")
        return 0 if logged_in() else 1
    if pos[:2] == ["debug", "models"]:
        print(json.dumps({"models": [{"slug": "gpt-6-astra"}, {"slug": "gpt-6-sol"}]}))
        return 0
    if pos[:2] == ["features", "list"]:
        print("multi_agent  stable  false")
        return 0
    if pos[:2] == ["mcp", "list"]:
        names = sorted({k.split(".")[1] for k in opts["config"] if k.startswith("mcp_servers.")})
        print(json.dumps([{"name": n, "enabled": True} for n in names]))
        return 0
    if pos[:1] == ["sandbox"]:
        return cmd_sandbox(opts)
    if pos[:1] == ["exec"]:
        return cmd_exec(opts, argv)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

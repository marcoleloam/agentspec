"""Environment lifecycle: setup, teardown and the pre-run smoke checks.

Only ``setup``/``teardown`` touch user-global state, and only one file:
``~/.grok/trusted_folders.toml`` (arms B and C must be trusted for their
project-scoped Context7 MCP to start). Every change is backed up first and
recorded in ``KB_BENCH_HOME/state.json`` so teardown removes exactly what
setup added.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import secrets
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import tomllib

from kb_bench import grok_runner, workspace
from kb_bench.config import ARM_LETTERS, BENCH_DIR, BenchConfig, inside_git_repo
from kb_bench.transcript import parse_ndjson

TRUST_FILE = Path(os.environ.get("KB_BENCH_TRUST_FILE", "~/.grok/trusted_folders.toml")).expanduser()
REQUIREMENTS = BENCH_DIR / "requirements-evals.txt"
COVERAGE_QUERIES = {
    "dbt": ("dbt", ("dbt",)),
    "airflow": ("apache-airflow", ("airflow",)),
    "medallion": ("medallion architecture", ("medallion",)),
    "data-modeling": ("kimball dimensional modeling", ("kimball", "dimensional model", "star schema")),
    "microsoft-fabric": ("microsoft fabric", ("fabric",)),
    "shadowtraffic": ("shadowtraffic", ("shadowtraffic",)),
}
_LIB_BLOCK = re.compile(r"- Title: (?P<title>[^\n]+)\n- Context7-compatible library ID: (?P<id>\S+)")


class SetupError(RuntimeError):
    """Setup/smoke precondition failed; message says how to fix it."""


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class SmokeResult:
    checks: list[Check] = field(default_factory=list)
    coverage: dict[str, dict[str, str | None]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "") -> bool:
        self.checks.append(Check(name, ok, detail))
        return ok


# ── trust file ───────────────────────────────────────────────────────────────

def trusted_folders(path: Path | None = None) -> set[str]:
    path = path or TRUST_FILE
    if not path.is_file():
        return set()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return {k for k, v in (data.get("folders") or {}).items() if v.get("trusted")}


def trust_targets(cfg: BenchConfig) -> list[Path]:
    return [cfg.arm_dir(a).resolve() for a in ARM_LETTERS if cfg.arms[a].uses_context7]


def _state_path(cfg: BenchConfig) -> Path:
    return cfg.home / "state.json"


def _read_state(cfg: BenchConfig) -> dict:
    path = _state_path(cfg)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _write_state(cfg: BenchConfig, state: dict) -> None:
    _state_path(cfg).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def backup_trust_file(cfg: BenchConfig) -> Path | None:
    if not TRUST_FILE.is_file():
        return None
    cfg.backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = cfg.backups_dir / f"trusted_folders.{stamp}.toml"
    shutil.copy2(TRUST_FILE, dest)
    return dest


def add_trust(cfg: BenchConfig, folders: list[Path]) -> list[str]:
    existing = trusted_folders()
    added = [str(f) for f in folders if str(f) not in existing]
    if not added:
        return []
    TRUST_FILE.parent.mkdir(parents=True, exist_ok=True)
    blocks = "".join(
        f'\n[folders."{f}"]\ntrusted = true\ndecided_at = {int(time.time())}\n' for f in added
    )
    with TRUST_FILE.open("a", encoding="utf-8") as fh:
        fh.write(blocks)
    return added


def remove_trust(folders: list[str]) -> list[str]:
    if not TRUST_FILE.is_file() or not folders:
        return []
    text = TRUST_FILE.read_text(encoding="utf-8")
    removed: list[str] = []
    for folder in folders:
        pattern = re.compile(r"\n?\[folders\.\"" + re.escape(folder) + r"\"\]\n(?:(?!\[)[^\n]*\n?)*")
        text, n = pattern.subn("\n", text)
        if n:
            removed.append(folder)
    TRUST_FILE.write_text(re.sub(r"\n{3,}", "\n\n", text).lstrip("\n"), encoding="utf-8")
    tomllib.loads(TRUST_FILE.read_text(encoding="utf-8"))  # must stay valid TOML
    return removed


# ── setup / teardown ─────────────────────────────────────────────────────────

def ensure_home(cfg: BenchConfig) -> None:
    if inside_git_repo(cfg.home):
        raise SetupError(f"{cfg.home} is inside a git repository; set KB_BENCH_HOME to a folder outside any repo")
    for path in (cfg.arms_root, cfg.results_root, cfg.backups_dir, cfg.canary_dir, cfg.npm_cache_dir):
        path.mkdir(parents=True, exist_ok=True)
    for letter in ARM_LETTERS:
        cfg.arm_dir(letter).mkdir(parents=True, exist_ok=True)


def ensure_eval_venv(cfg: BenchConfig, log=print) -> None:
    venv = cfg.eval_venv_bin.parent
    python = cfg.eval_venv_bin / "python"
    if not python.exists():
        if shutil.which("uv"):
            subprocess.run(["uv", "venv", "--python", "3.12", str(venv)], check=True)
        else:
            subprocess.run(["python3", "-m", "venv", str(venv)], check=True)
    if shutil.which("uv"):
        subprocess.run(["uv", "pip", "install", "--python", str(python), "-q", "-r", str(REQUIREMENTS)], check=True)
    else:
        subprocess.run([str(python), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)], check=True)
    log(f"eval venv ready: {venv}")


def setup(cfg: BenchConfig, *, assume_yes: bool, skip_venv: bool = False, log=print,
          confirm=input) -> list[str]:
    ensure_home(cfg)
    if not skip_venv:
        ensure_eval_venv(cfg, log)
    for letter in ARM_LETTERS:
        workspace.write_grok_files(cfg.arms[letter], cfg.arm_dir(letter), cfg)
    targets = trust_targets(cfg)
    missing = [t for t in targets if str(t) not in trusted_folders()]
    if not missing:
        log("arms B/C already trusted")
        return []
    log(f"Grok only starts project-scoped MCP servers in trusted folders. This adds {len(missing)} "
        f"entr{'y' if len(missing) == 1 else 'ies'} to {TRUST_FILE}:")
    for t in missing:
        log(f"  {t}")
    if not assume_yes and confirm("Proceed? [y/N] ").strip().lower() not in {"y", "yes", "s", "sim"}:
        raise SetupError("trust not granted — arms B/C cannot use Context7; rerun with --yes to accept")
    backup = backup_trust_file(cfg)
    added = add_trust(cfg, missing)
    state = _read_state(cfg)
    state["trust_added"] = sorted(set(state.get("trust_added", [])) | set(added))
    state["trust_backup"] = str(backup) if backup else None
    _write_state(cfg, state)
    log(f"trusted {len(added)} folder(s); backup: {backup}")
    return added


def teardown(cfg: BenchConfig, *, log=print) -> list[str]:
    state = _read_state(cfg)
    added = state.get("trust_added", [])
    if not added:
        log("nothing to remove (setup added no trust entries)")
        return []
    backup_trust_file(cfg)
    removed = remove_trust(added)
    state["trust_added"] = sorted(set(added) - set(removed))
    _write_state(cfg, state)
    log(f"removed trust for: {', '.join(removed) or 'none (already gone)'}")
    return removed


# ── smoke ────────────────────────────────────────────────────────────────────

def _mcp_names(info: dict | None) -> set[str]:
    if not info:
        return set()
    return {m.get("name") for m in info.get("mcpServers", []) if m.get("enabled") is not False}


def canary(cfg: BenchConfig) -> Check:
    token = f"KBBENCH-CANARY-{secrets.token_hex(6)}"
    cfg.canary_dir.mkdir(parents=True, exist_ok=True)
    target = cfg.canary_dir / "canary.txt"
    target.write_text(token + "\n", encoding="utf-8")
    arm = cfg.arms["D"]
    arm_dir = cfg.arm_dir("D")
    workspace.reset_arm_dir(arm_dir, cfg)
    workspace.write_grok_files(arm, arm_dir, cfg)
    out = grok_runner.run_attempt(
        f"Use the read_file tool on {target} and reply with its exact content, or the exact error.",
        arm_dir, cfg, timeout_s=240,
    )
    t = parse_ndjson(out.ndjson)
    leaked = token in t.text or any(token in c.output_text for c in t.tool_calls)
    denied = any(c.permission_denied for c in t.tool_calls)
    if leaked:
        return Check("sandbox canary", False, "canary content was READ — sandbox not enforced; aborting")
    if not denied:
        return Check("sandbox canary", False, "no PermissionDenied observed (agent may not have tried); rerun smoke")
    return Check("sandbox canary", True, "read of deny path returned PermissionDenied")


def coverage(cfg: BenchConfig) -> dict[str, dict[str, str | None]]:
    arm = cfg.arms["B"]
    arm_dir = cfg.arm_dir("B")
    workspace.reset_arm_dir(arm_dir, cfg)
    workspace.write_grok_files(arm, arm_dir, cfg)
    names = ", ".join(q for q, _ in COVERAGE_QUERIES.values())
    out = grok_runner.run_attempt(
        "Using ONLY the context7 MCP tool resolve-library-id, call it once for each of these library "
        f"names, in order: {names}. Do not call anything else. Then reply DONE.",
        arm_dir, cfg, timeout_s=400,
    )
    t = parse_ndjson(out.ndjson)
    raw_inputs = _raw_inputs(out.ndjson)
    by_query = {
        raw_inputs.get(call.call_id, "").lower(): call.output_text
        for call in t.mcp_calls("context7__resolve-library-id")
    }
    result: dict[str, dict[str, str | None]] = {}
    for domain, (query, keywords) in COVERAGE_QUERIES.items():
        text = by_query.get(query.lower())
        if text is None:
            result[domain] = {"status": "not_checked", "library_id": None, "title": None}
            continue
        libs = [(m["title"].strip(), m["id"]) for m in _LIB_BLOCK.finditer(text)]
        hit = next(((ti, li) for ti, li in libs if any(k in (ti + li).lower() for k in keywords)), None)
        result[domain] = {
            "status": "covered" if hit else "not_covered",
            "library_id": hit[1] if hit else (libs[0][1] if libs else None),
            "title": hit[0] if hit else (libs[0][0] if libs else None),
        }
    return result


def _raw_inputs(ndjson: str) -> dict[str, str]:
    """toolCallId → libraryName for context7 resolve calls."""
    out: dict[str, str] = {}
    for line in ndjson.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "tool_call":
            tool_input = (ev.get("rawInput") or {}).get("tool_input") or {}
            if isinstance(tool_input, dict) and tool_input.get("libraryName"):
                out[ev.get("toolCallId", "")] = str(tool_input["libraryName"])
    return out


def smoke(cfg: BenchConfig, *, model_calls: bool = True, log=print) -> SmokeResult:
    res = SmokeResult()
    if not res.add("grok on PATH", grok_runner.grok_available(), grok_runner.GROK_BIN):
        return res
    res.add("grok version", True, grok_runner.version())
    res.add(f"model {cfg.model} listed", cfg.model in grok_runner.models())
    res.add("home outside git", not inside_git_repo(cfg.home), str(cfg.home))
    res.add("eval venv present", (cfg.eval_venv_bin / "python").exists(), str(cfg.eval_venv_bin))
    trusted = trusted_folders()
    for letter in ARM_LETTERS:
        arm = cfg.arms[letter]
        arm_dir = cfg.arm_dir(letter)
        if not arm_dir.is_dir():
            res.add(f"arm {letter} folder", False, "run `make kb-bench-setup`")
            continue
        workspace.write_grok_files(arm, arm_dir, cfg)
        names = _mcp_names(grok_runner.inspect(arm_dir))
        if arm.uses_context7:
            res.add(f"arm {letter} trusted", str(arm_dir.resolve()) in trusted, str(arm_dir))
            healthy, detail = grok_runner.mcp_doctor(arm_dir, sandbox=cfg.sandbox_profile)
            res.add(f"arm {letter} context7 healthy", healthy, detail[-160:])
        else:
            res.add(f"arm {letter} has no context7", "context7" not in names, ", ".join(sorted(n for n in names if n)))
        extra = names - {"context7"} - {None}
        res.add(f"arm {letter} no other MCP", not extra, ", ".join(sorted(extra)))
    if model_calls and res.ok:
        check = canary(cfg)
        res.add(check.name, check.ok, check.detail)
        if check.ok:
            res.coverage = coverage(cfg)
            res.add("context7 coverage probed", any(v["status"] != "not_checked" for v in res.coverage.values()),
                    ", ".join(f"{d}={v['status']}" for d, v in res.coverage.items()))
    return res

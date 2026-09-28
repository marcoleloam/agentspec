"""Environment lifecycle: setup, teardown and the pre-run smoke checks.

Nothing here touches user-global state. ``setup`` creates folders under
``KB_BENCH_HOME``, the eval venv and the isolated agent home whose only link
to the user is a symlink to ``~/.codex/auth.json`` (no credential copy).
``teardown`` removes that agent home, moving a refreshed ``auth.json`` back to
the user's Codex home first. Results are never touched.
"""
from __future__ import annotations

import re
import secrets
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from kb_bench import codex_runner, context7_probe, workspace
from kb_bench.config import ARM_LETTERS, BENCH_DIR, BenchConfig, inside_git_repo
from kb_bench.isolation import under
from kb_bench.transcript import parse_jsonl

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
NO_KEY_WARNING = (f"{context7_probe.API_KEY_ENV} is not set — the free anonymous Context7 quota runs out "
                  "quickly (\"Monthly quota exceeded\") and arms B/C then end as `unavailable`. Create a key at "
                  "https://context7.com/dashboard and export it before running.")


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
    warnings: list[str] = field(default_factory=list)
    coverage: dict[str, dict[str, str | None]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "") -> bool:
        self.checks.append(Check(name, ok, detail))
        return ok


# ── setup / teardown ─────────────────────────────────────────────────────────

def ensure_home(cfg: BenchConfig) -> None:
    if inside_git_repo(cfg.home):
        raise SetupError(f"{cfg.home} is inside a git repository; set KB_BENCH_HOME to a folder outside any repo")
    blocked = [p for p in (cfg.arms_root, cfg.agent_home) if under(p.resolve(), cfg.deny_paths())]
    if blocked:
        raise SetupError(f"{blocked[0]} falls under a sandbox deny root; move KB_BENCH_HOME elsewhere")
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


def setup(cfg: BenchConfig, *, skip_venv: bool = False, log=print) -> None:
    ensure_home(cfg)
    if not skip_venv:
        ensure_eval_venv(cfg, log)
    try:
        codex_runner.ensure_codex_home(cfg)
    except codex_runner.CodexHomeError as exc:
        raise SetupError(str(exc)) from exc
    log(f"agent home ready: {cfg.agent_home} (auth.json → {cfg.user_auth_file})")
    if not context7_probe.api_key_present():
        log(f"WARNING: {NO_KEY_WARNING}")


def teardown(cfg: BenchConfig, *, log=print) -> bool:
    moved = codex_runner.sync_auth_back(cfg)
    removed = codex_runner.remove_agent_home(cfg)
    if moved:
        log(f"moved a refreshed auth.json back to {cfg.user_auth_file}")
    log(f"removed {cfg.agent_home}" if removed else "nothing to remove (no agent home)")
    return removed


# ── smoke ────────────────────────────────────────────────────────────────────

def _write_canary(cfg: BenchConfig) -> tuple[str, str]:
    token = f"KBBENCH-CANARY-{secrets.token_hex(6)}"
    cfg.canary_dir.mkdir(parents=True, exist_ok=True)
    target = cfg.canary_dir / "canary.txt"
    target.write_text(token + "\n", encoding="utf-8")
    return token, str(target)


def _leak_canaries(cfg: BenchConfig) -> list[tuple[str, str, Path]]:
    """Canaries where round 1 leaked: arm A's ``kb/`` and the bench results (other arms' transcripts)."""
    out = []
    for label, folder in (("arms/a/kb", cfg.arm_dir("A") / "kb"), ("results", cfg.results_root)):
        folder.mkdir(parents=True, exist_ok=True)
        token = f"KBBENCH-CANARY-{secrets.token_hex(6)}"
        target = folder / ".kbbench-canary.txt"
        target.write_text(token + "\n", encoding="utf-8")
        out.append((label, token, target))
    return out


def sandbox_canary(cfg: BenchConfig) -> Check:
    """No model: from arm D's profile, ``cat`` the canary, arm A's ``kb/`` and the results — all denied —
    then write in the arm folder, which must succeed."""
    token, target = _write_canary(cfg)
    arm, arm_dir = cfg.arms["D"], cfg.arm_dir("D")
    workspace.reset_arm_dir(arm_dir, cfg)
    codex_runner.reset_agent_home(cfg)
    leaks = _leak_canaries(cfg)
    try:
        for label, tok, path in [("canary", token, Path(target)), *leaks]:
            code, out = codex_runner.sandbox_run(["cat", str(path)], arm_dir, cfg, arm)
            if tok in out:
                return Check("sandbox canary", False,
                             f"{label} canary was READ from arm D — permission profile not enforced")
            if code == 0 or "Operation not permitted" not in out:
                return Check("sandbox canary", False,
                             f"{label}: expected 'Operation not permitted', got exit {code}: {out[-160:]}")
    finally:
        for _label, _tok, path in leaks:
            path.unlink(missing_ok=True)
    probe = ".kbbench-write-probe"
    code, out = codex_runner.sandbox_run(["sh", "-c", f"echo ok > {probe} && cat {probe} && rm {probe}"],
                                         arm_dir, cfg, arm)
    if code != 0 or "ok" not in out:
        return Check("sandbox canary", False, f"arm folder not writable under the profile: {out[-160:]}")
    return Check("sandbox canary", True,
                 "canary, arms/a/kb and results → Operation not permitted from arm D; arm folder writable")


def exec_canary(cfg: BenchConfig) -> Check:
    """One model call: the same read through ``codex exec``. Codex may decline to try — that passes."""
    token, target = _write_canary(cfg)
    arm, arm_dir = cfg.arms["D"], cfg.arm_dir("D")
    workspace.reset_arm_dir(arm_dir, cfg)
    out = codex_runner.run_attempt(
        f"Run exactly this shell command and reply with its exact output or error: cat {target}",
        arm_dir, cfg, arm, timeout_s=240,
    )
    t = parse_jsonl(out.jsonl)
    if token in t.text or any(token in c.output_text for c in t.tool_calls):
        return Check("exec canary", False, "canary content was READ by codex exec — aborting")
    if not t.ended:
        why = t.error_message or f"no turn.completed (exit {out.exit_code}, timed out {out.timed_out})"
        return Check("exec canary", False, f"codex exec did not finish: {why[:200]}")
    tokens = f"{t.input_tokens or 0:,} input tokens"
    if any(c.permission_denied for c in t.tool_calls):
        return Check("exec canary", True, f"read of deny path → Operation not permitted ({tokens})")
    return Check("exec canary", True, f"model declined to read the deny path; sandbox canary is authoritative ({tokens})")


def parse_coverage(calls: dict[str, str]) -> dict[str, dict[str, str | None]]:
    result: dict[str, dict[str, str | None]] = {}
    for domain, (query, keywords) in COVERAGE_QUERIES.items():
        text = calls.get(query)
        if text is None or context7_probe.unavailable_text(text):
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


def coverage(cfg: BenchConfig) -> tuple[context7_probe.ProbeResult, dict[str, dict[str, str | None]]]:
    """No model: call ``resolve-library-id`` directly for each domain (uses Context7 quota)."""
    arm = cfg.arms["B"]
    queries = tuple(q for q, _ in COVERAGE_QUERIES.values())
    res = context7_probe.probe(cfg, cfg.arm_dir("B"), env=codex_runner.agent_env(cfg, arm), resolve=queries)
    return res, parse_coverage(res.calls)


def smoke(cfg: BenchConfig, *, model_calls: bool = True, log=print) -> SmokeResult:
    res = SmokeResult()
    if not res.add("codex on PATH", codex_runner.codex_available(),
                   codex_runner.resolved_bin() or f"{codex_runner.CODEX_BIN} not found (set KB_BENCH_CODEX)"):
        return res
    res.add("codex version", True, codex_runner.version())
    res.add("home outside git", not inside_git_repo(cfg.home), str(cfg.home))
    res.add("eval venv present", (cfg.eval_venv_bin / "python").exists(), str(cfg.eval_venv_bin))
    try:
        codex_runner.reset_agent_home(cfg)
        res.add("isolated agent home", True, f"{cfg.agent_home} (auth.json symlink)")
    except codex_runner.CodexHomeError as exc:
        res.add("isolated agent home", False, str(exc))
        return res
    res.add("codex login (isolated home)", *codex_runner.auth_status(cfg))
    if cfg.model:
        res.add(f"model {cfg.model} listed", cfg.model in codex_runner.models(cfg))
    if not res.add("disabled features accepted", *codex_runner.features_accepted(cfg)):
        return res  # every later codex call would fail on the same flag
    if not context7_probe.api_key_present():
        res.warnings.append(NO_KEY_WARNING)
    for letter in ARM_LETTERS:
        arm, arm_dir = cfg.arms[letter], cfg.arm_dir(letter)
        if not arm_dir.is_dir():
            res.add(f"arm {letter} folder", False, "run `make kb-bench-setup`")
            continue
        names = codex_runner.mcp_servers(arm_dir, cfg, arm)
        if names is None:
            res.add(f"arm {letter} MCP listing", False, "`codex mcp list --json` failed")
            continue
        res.add(f"arm {letter} {'has' if arm.uses_context7 else 'has no'} context7",
                ("context7" in names) == arm.uses_context7, ", ".join(sorted(n for n in names if n)))
        extra = names - {"context7"} - {None}
        res.add(f"arm {letter} no other MCP", not extra, ", ".join(sorted(extra)))
        if arm.uses_context7:
            probe = context7_probe.probe(cfg, arm_dir, env=codex_runner.agent_env(cfg, arm))
            res.add(f"arm {letter} context7 starts", probe.ok, f"{probe.detail} in {probe.elapsed_s:.1f}s")
    check = sandbox_canary(cfg)
    res.add(check.name, check.ok, check.detail)
    if model_calls and res.ok:
        probe, res.coverage = coverage(cfg)
        res.add("context7 quota available", probe.ok, probe.detail)
        if res.ok:
            check = exec_canary(cfg)
            res.add(check.name, check.ok, check.detail)
    return res

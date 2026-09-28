#!/usr/bin/env python3
"""Eval Runner — deterministic post-build acceptance gate for AgentSpec.

Evals are declared in the DESIGN document as a TOML block that follows the
``<!-- agentspec:evals:contract -->`` marker. The block is frozen by digest at
design time, checked before the build (``pre``), re-executed after the build
(``run``), and the resulting receipt is required by ``/ship`` (``verify``).

Subcommands:
  validate  <F>                     structural checks (AT coverage, eval rules)
  freeze    <F> [--reason TEXT]     write the contract digest into the DESIGN and
                                    append it to the freeze ledger; a re-freeze
                                    (digest already frozen) requires --reason
  pre       <F>                     pre-build: evals must run cleanly and fail;
                                    persists the PRE receipt
  extra     <F> [--file PATH]       append complementary evals (stdin or file)
                                    to EVALS_EXTRA_{F}.toml, validated first
  run       <F> [--escalate MODE]   execute evals, write sealed receipt + report
  attest    <F> --eval ID ...       record a human decision
  waive     <F> (--eval ID | --legacy) ...   record a named waiver
  verify    <F> [--rerun]           ship gate: recompute the verdict from the
                                    receipt and check it against current state
  calibrate <cases.toml>            measure Jev agreement, approve its authority

<F> is a feature name (``POST_BUILD_EVALS``) or a path to its DESIGN file.

Exit codes:
  0  ok
  1  gate / eval failure (FAIL verdict, blocked pre-check, verify refusal)
  2  environment or usage error (python, git, missing files, config)
  3  structural error in the eval contract
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    print(
        "[ERROR] PYTHON_TOO_OLD: eval_runner.py needs Python >= 3.11 (tomllib). "
        f"Running {sys.version.split()[0]}. Use python3.11+ explicitly.",
        file=sys.stderr,
    )
    raise SystemExit(2)

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import string
import subprocess
import time
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import jev_client  # noqa: E402

RUNNER_VERSION = "1.1.0"
RECEIPT_SCHEMA = "agentspec/eval-receipt/v1"
PRE_SCHEMA = "agentspec/eval-pre/v1"
FREEZE_SCHEMA = "agentspec/eval-freeze/v1"
INTEGRITY_ALGORITHM = "sha256-canonical-json/v1"
CALIBRATION_SCHEMA = "agentspec/jev-calibration/v1"
CONTRACT_MARKER = "<!-- agentspec:evals:contract -->"
DIGEST_ROW = re.compile(r"^(\|\s*\*\*Evals Digest\*\*\s*\|)(.*?)(\|\s*)$", re.MULTILINE)
STATUS_ROW = re.compile(r"^\|\s*\*\*Status\*\*\s*\|.*\|\s*$", re.MULTILINE)
AT_ROW = re.compile(r"^\|\s*(AT-\d{3})\s*\|", re.MULTILINE)
EVAL_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
EXISTENCE_LINE = re.compile(r"^\s*(test\s+-[efdsr]\s|\[\[?\s+-[efdsr]\s)")
SENSITIVE = re.compile(r"\.env\b|\.pem\b|secret|credential", re.IGNORECASE)
BASH_ERROR = re.compile(r"^bash: (?:-c: )?line \d+: .*(?:syntax error|unbound variable|command not found)", re.MULTILINE)
INTERPRETER_ERROR = re.compile(r"^\S*python[\d.]*: No module named ", re.MULTILINE)
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
# Workflow state that legitimately changes between /eval and /ship. Everything
# else under .claude/sdd (templates/, architecture/, evals/) is product code and
# IS covered by the worktree digest. Gitignored files are never covered.
SDD_EXCLUDES = (
    ":(exclude).claude/sdd/features",
    ":(exclude).claude/sdd/reports",
    ":(exclude).claude/sdd/archive",
    ":(exclude).claude/sdd/MEMORY.md",
    ":(exclude).claude/storage",
)
CHECK_TYPES = ("deterministic", "graded", "human")
EXTRA_CHECK_TYPES = ("deterministic", "graded")
DEFAULT_TIMEOUT = 120
STATE_TIMEOUT = 60
EVIDENCE_CHARS = 4000
CALIBRATION_MIN_CASES = 10
CALIBRATION_MIN_COVERAGE = 0.5
CALIBRATION_MIN_AGREEMENT = 0.8
MIN_REASON_CHARS = 30
# Waiver supervisors and attestation owners must be people. These are the
# agent / model / harness names a session could plausibly type for itself.
AGENT_IDENTITIES = frozenset({
    "agent", "ai", "assistant", "bot", "llm", "model", "system", "auto", "automated", "ci",
    "claude", "claude code", "claude-code", "anthropic", "codex", "openai", "gpt", "chatgpt",
    "gemini", "deepseek", "grok", "copilot", "omp", "cursor",
})
AGENT_IDENTITY = re.compile(r"(^|[\s_-])agent$|^(claude|codex|gpt|gemini|deepseek|grok|copilot|openai|anthropic)([\s_.:/-]|$)", re.IGNORECASE)

Status = Literal["pass", "fail", "error", "escalated", "pending", "waived"]
Decision = Literal["pass", "fail", "escalated"]


class RunnerError(RuntimeError):
    def __init__(self, message: str, exit_code: int = 2, code: str = "CONFIG") -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.code = code


# ── Model ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Thresholds:
    noul_pass: float = 0.85
    noul_fail: float = 0.15
    score_confidence: float = 0.75

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> Thresholds:
        if not data:
            return cls()
        return cls(
            noul_pass=float(data.get("noul_pass", cls.noul_pass)),
            noul_fail=float(data.get("noul_fail", cls.noul_fail)),
            score_confidence=float(data.get("score_confidence", cls.score_confidence)),
        )

    def to_dict(self) -> dict[str, float]:
        return {"noul_pass": self.noul_pass, "noul_fail": self.noul_fail, "score_confidence": self.score_confidence}


@dataclass(frozen=True, slots=True)
class Eval:
    id: str
    verifies: tuple[str, ...]
    check_type: str
    description: str = ""
    origin: str = "contract"
    run: str = ""
    timeout_sec: int = DEFAULT_TIMEOUT
    state: dict[str, str] = field(default_factory=dict)
    questions: tuple[jev_client.Question, ...] = ()
    owner: str = ""
    instructions: str = ""


@dataclass(slots=True)
class EvalResult:
    eval: Eval
    status: Status
    reason: str | None = None
    exit_code: int | None = None
    duration_sec: float = 0.0
    stdout: str = ""
    stderr: str = ""
    decided_by: str | None = None
    jev: dict[str, Any] | None = None
    judge: dict[str, Any] | None = None
    human: dict[str, Any] | None = None
    waiver: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "eval_id": self.eval.id,
            "origin": self.eval.origin,
            "verifies": list(self.eval.verifies),
            "check_type": self.eval.check_type,
            "description": self.eval.description,
            "status": self.status,
        }
        optional = {
            "reason": self.reason,
            "exit_code": self.exit_code,
            "decided_by": self.decided_by,
            "jev": self.jev,
            "judge": self.judge,
            "human": self.human,
            "waiver": self.waiver,
        }
        data.update({k: v for k, v in optional.items() if v is not None})
        data["duration_sec"] = round(self.duration_sec, 3)
        if self.eval.check_type == "deterministic" or self.stdout or self.stderr:
            data["evidence"] = {"stdout": self.stdout, "stderr": self.stderr}
        return data


@dataclass(slots=True)
class Findings:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Paths:
    root: Path
    feature: str

    @property
    def features(self) -> Path:
        return self.root / ".claude" / "sdd" / "features"

    @property
    def reports(self) -> Path:
        return self.root / ".claude" / "sdd" / "reports"

    @property
    def design(self) -> Path:
        return self.features / f"DESIGN_{self.feature}.md"

    @property
    def define(self) -> Path:
        return self.features / f"DEFINE_{self.feature}.md"

    @property
    def extras(self) -> Path:
        return self.features / f"EVALS_EXTRA_{self.feature}.toml"

    @property
    def receipt(self) -> Path:
        return self.reports / f"EVAL_{self.feature}.json"

    @property
    def report(self) -> Path:
        return self.reports / f"EVAL_REPORT_{self.feature}.md"

    @property
    def attestations(self) -> Path:
        return self.reports / f"EVAL_{self.feature}.attestations.json"

    @property
    def pre_receipt(self) -> Path:
        return self.reports / f"EVAL_{self.feature}.pre.json"

    @property
    def freeze_log(self) -> Path:
        return self.features / f"EVAL_{self.feature}.freeze.log"

    @property
    def calibration(self) -> Path:
        return self.root / ".claude" / "sdd" / "evals" / "JEV_CALIBRATION.json"

    @property
    def ledger(self) -> Path:
        return self.root / ".claude" / "storage" / "judge-ledger.jsonl"


# ── Contract parsing ────────────────────────────────────────────────────────

def find_contract(text: str) -> str | None:
    """Return the TOML contract block, or None when the DESIGN has no marker.

    Markers inside fenced code blocks are ignored, so documentation examples
    never count as the contract."""
    lines = text.splitlines()
    fence: str | None = None
    markers: list[int] = []
    for index, line in enumerate(lines):
        opening = re.match(r"^(`{3,})", line)
        if opening:
            if fence is None:
                fence = opening.group(1)
            elif line.strip() == fence:
                fence = None
            continue
        if fence is None and line.strip() == CONTRACT_MARKER:
            markers.append(index)
    if not markers:
        return None
    if len(markers) > 1:
        raise RunnerError(f"MULTIPLE_CONTRACTS: {len(markers)} contract markers outside code fences", 3, "MULTIPLE_CONTRACTS")
    start = markers[0] + 1
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start >= len(lines) or lines[start].strip() != "```toml":
        raise RunnerError("CONTRACT_NOT_TOML: the contract marker must be followed by a ```toml block", 3, "CONTRACT_NOT_TOML")
    for end in range(start + 1, len(lines)):
        if lines[end].strip() == "```":
            return "\n".join(lines[start + 1:end])
    raise RunnerError("CONTRACT_UNTERMINATED: the ```toml contract block is never closed", 3, "CONTRACT_UNTERMINATED")


def load_toml(text: str, label: str) -> dict[str, Any]:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as err:
        raise RunnerError(f"INVALID_TOML in {label}: {err}", 3, "INVALID_TOML") from err


def canonical_digest(data: Any) -> str:
    blob = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def parse_evals(data: Mapping[str, Any], origin: str) -> tuple[list[Eval], Findings]:
    findings = Findings()
    evals: list[Eval] = []
    raw_evals = data.get("eval", [])
    if not isinstance(raw_evals, list):
        findings.errors.append(f"INVALID_SCHEMA: [[eval]] must be an array of tables ({origin})")
        return evals, findings
    for position, raw in enumerate(raw_evals, start=1):
        if not isinstance(raw, Mapping):
            findings.errors.append(f"INVALID_SCHEMA: eval #{position} is not a table ({origin})")
            continue
        questions: list[jev_client.Question] = []
        for q in raw.get("questions", []) or []:
            if not isinstance(q, Mapping):
                findings.errors.append(f"INVALID_SCHEMA: question in {raw.get('id', position)} is not a table")
                continue
            questions.append(jev_client.Question(
                id=str(q.get("id", "")),
                type=str(q.get("type", "")),  # type: ignore[arg-type]
                instructions=str(q.get("instructions", "")),
                criteria=tuple(str(c) for c in q.get("criteria", []) or []),
            ))
        state = raw.get("state", {}) or {}
        evals.append(Eval(
            id=str(raw.get("id", "")),
            verifies=tuple(str(v) for v in raw.get("verifies", []) or []),
            check_type=str(raw.get("check_type", "")),
            description=str(raw.get("description", "")),
            origin=origin,
            run=str(raw.get("run", "")),
            timeout_sec=int(raw.get("timeout_sec", DEFAULT_TIMEOUT)),
            state={str(k): str(v) for k, v in state.items()} if isinstance(state, Mapping) else {},
            questions=tuple(questions),
            owner=str(raw.get("owner", "")),
            instructions=str(raw.get("instructions", "")),
        ))
    return evals, findings


def parse_ats(define_text: str) -> set[str]:
    return set(AT_ROW.findall(define_text))


def read_frozen_digest(design_text: str) -> str | None:
    match = DIGEST_ROW.search(design_text)
    if not match:
        return None
    value = match.group(2).strip().strip("`")
    return value if value.startswith("sha256:") else None


def write_frozen_digest(design_text: str, digest: str) -> str:
    cell = f" `{digest}` "
    if DIGEST_ROW.search(design_text):
        return DIGEST_ROW.sub(lambda m: f"{m.group(1)}{cell}{m.group(3)}", design_text, count=1)
    status = STATUS_ROW.search(design_text)
    if not status:
        raise RunnerError("NO_METADATA_TABLE: DESIGN has no **Status** row to anchor **Evals Digest**", 3, "NO_METADATA_TABLE")
    row = f"| **Evals Digest** |{cell}|"
    return design_text[:status.end()] + "\n" + row + design_text[status.end():]


# ── Validation ──────────────────────────────────────────────────────────────

def bash_syntax_ok(script: str) -> tuple[bool, str]:
    proc = subprocess.run(["bash", "-n", "-c", script], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return proc.returncode == 0, proc.stderr.strip()


def validate_evals(
    contract: Sequence[Eval],
    extras: Sequence[Eval],
    ats: set[str] | None,
    required: Sequence[str] | None,
) -> Findings:
    findings = Findings()
    everything = [*contract, *extras]
    seen: set[str] = set()
    for ev in everything:
        label = f"{ev.id or '<no id>'} ({ev.origin})"
        if not EVAL_ID.match(ev.id):
            findings.errors.append(f"INVALID_ID: {label} — use letters, digits and underscore")
        if ev.id in seen:
            findings.errors.append(f"DUPLICATE_ID: {ev.id}")
        seen.add(ev.id)
        allowed = CHECK_TYPES if ev.origin == "contract" else EXTRA_CHECK_TYPES
        if ev.check_type not in allowed:
            findings.errors.append(f"INVALID_CHECK_TYPE: {label} has {ev.check_type!r}; allowed {list(allowed)}")
            continue
        if ev.origin == "contract" and not ev.verifies:
            findings.errors.append(f"MISSING_VERIFIES: {label} must verify at least one AT")
        if ats is not None:
            for at in ev.verifies:
                if at not in ats:
                    findings.errors.append(f"UNKNOWN_AT: {label} verifies {at}, which is not in the DEFINE")
        if ev.timeout_sec <= 0:
            findings.errors.append(f"INVALID_TIMEOUT: {label}")
        if ev.check_type == "deterministic":
            _validate_deterministic(ev, label, findings)
        elif ev.check_type == "graded":
            _validate_graded(ev, label, findings)
        else:
            if not ev.owner:
                findings.errors.append(f"MISSING_OWNER: {label} (human evals need an owner)")
            if not ev.instructions:
                findings.errors.append(f"MISSING_INSTRUCTIONS: {label}")
    if not contract:
        findings.errors.append("NO_EVALS: the contract declares no [[eval]] — the gate would have nothing to prove")
    if ats is not None:
        covered = {at for ev in contract for at in ev.verifies}
        for at in sorted(ats - covered):
            findings.errors.append(f"ORPHAN_AT: {at} has no contract eval")
    if required is not None:
        if not required:
            findings.errors.append("EMPTY_REQUIRED: [gate] required = [] gates nothing — list the eval ids or drop [gate] (default: every eval)")
        for eval_id in required:
            if eval_id not in seen:
                findings.errors.append(f"UNKNOWN_REQUIRED: [gate] required lists {eval_id}, which is not an eval")
        gated = set(required) | {ev.id for ev in extras}
        referenced = {at for ev in contract for at in ev.verifies}
        gated_ats = {at for ev in everything if ev.id in gated for at in ev.verifies}
        for at in sorted(referenced - gated_ats):
            findings.errors.append(f"UNGATED_AT: {at} is verified only by evals outside [gate] required")
    graded = sum(1 for ev in contract if ev.check_type == "graded")
    if contract and graded * 2 > len(contract):
        findings.warnings.append(f"TOO_MANY_GRADED: {graded}/{len(contract)} contract evals are graded (> 50%) — criteria may be too subjective")
    return findings


def _validate_deterministic(ev: Eval, label: str, findings: Findings) -> None:
    if not ev.run.strip():
        findings.errors.append(f"MISSING_RUN: {label}")
        return
    ok, detail = bash_syntax_ok(ev.run)
    if not ok:
        findings.errors.append(f"BASH_SYNTAX: {label}: {detail}")
    meaningful = [ln for ln in ev.run.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if meaningful and all(EXISTENCE_LINE.match(ln) for ln in meaningful):
        findings.warnings.append(f"EXISTENCE_ONLY: {label} only checks that files exist — it cannot prove behavior")


def _validate_graded(ev: Eval, label: str, findings: Findings) -> None:
    if not ev.state:
        findings.errors.append(f"MISSING_STATE: {label} needs at least one [eval.state] field")
    for key, command in ev.state.items():
        ok, detail = bash_syntax_ok(command)
        if not ok:
            findings.errors.append(f"BASH_SYNTAX: {label} state.{key}: {detail}")
        if SENSITIVE.search(command):
            findings.warnings.append(f"SENSITIVE_STATE: {label} state.{key} may send secrets to the Jev API: {command!r}")
    if not 2 <= len(ev.questions) <= 5:
        findings.errors.append(f"QUESTION_COUNT: {label} has {len(ev.questions)} questions; graded evals need 2-5")
    if not any(q.type == "score" for q in ev.questions):
        findings.errors.append(f"MISSING_SCORE: {label} needs at least one score question (Noul alone is unsafe)")
    ids = [q.id for q in ev.questions]
    if len(set(ids)) != len(ids):
        findings.errors.append(f"DUPLICATE_QUESTION: {label}")
    for q in ev.questions:
        if not q.id or not q.instructions:
            findings.errors.append(f"INVALID_QUESTION: {label} question needs id and instructions")
        if q.type not in ("noul", "score"):
            findings.errors.append(f"INVALID_QUESTION_TYPE: {label}.{q.id} is {q.type!r}")
        if q.type == "score" and not 2 <= len(q.criteria) <= 10:
            findings.errors.append(f"SCORE_CRITERIA: {label}.{q.id} needs 2-10 criteria")


# ── Loading a feature ───────────────────────────────────────────────────────

@dataclass(slots=True)
class Feature:
    paths: Paths
    design_text: str
    contract_text: str | None
    contract_data: dict[str, Any]
    contract: list[Eval]
    extras: list[Eval]
    extras_data: dict[str, Any]
    required: list[str] | None
    ats: set[str] | None
    parse_findings: Findings

    @property
    def is_legacy(self) -> bool:
        return self.contract_text is None

    @property
    def contract_digest(self) -> str | None:
        return None if self.is_legacy else canonical_digest(self.contract_data)

    @property
    def extras_digest(self) -> str | None:
        return canonical_digest(self.extras_data) if self.extras_data else None

    @property
    def all_evals(self) -> list[Eval]:
        return [*self.contract, *self.extras]

    def gate_ids(self) -> list[str]:
        if self.required is not None:
            return [*self.required, *(ev.id for ev in self.extras if ev.id not in self.required)]
        return [ev.id for ev in self.all_evals]


def load_feature(paths: Paths) -> Feature:
    if not paths.design.exists():
        raise RunnerError(f"DESIGN_NOT_FOUND: {paths.design}", 2, "DESIGN_NOT_FOUND")
    design_text = paths.design.read_text(encoding="utf-8")
    contract_text = find_contract(design_text)
    findings = Findings()
    contract_data: dict[str, Any] = {}
    contract: list[Eval] = []
    required: list[str] | None = None
    if contract_text is not None:
        contract_data = load_toml(contract_text, str(paths.design))
        contract, parsed = parse_evals(contract_data, "contract")
        findings.errors += parsed.errors
        gate = contract_data.get("gate", {})
        if isinstance(gate, Mapping) and "required" in gate:
            required = [str(x) for x in gate["required"]]
    extras_data: dict[str, Any] = {}
    extras: list[Eval] = []
    if paths.extras.exists():
        extras_data = load_toml(paths.extras.read_text(encoding="utf-8"), str(paths.extras))
        extras, parsed = parse_evals(extras_data, "complementary")
        findings.errors += parsed.errors
    ats = parse_ats(paths.define.read_text(encoding="utf-8")) if paths.define.exists() else None
    if contract_text is not None and ats is None:
        findings.errors.append(f"DEFINE_NOT_FOUND: {paths.define} (needed for AT traceability)")
    return Feature(paths, design_text, contract_text, contract_data, contract, extras, extras_data, required, ats, findings)


def structural_findings(feature: Feature) -> Findings:
    findings = Findings(list(feature.parse_findings.errors), list(feature.parse_findings.warnings))
    checked = validate_evals(feature.contract, feature.extras, feature.ats, feature.required)
    findings.errors += checked.errors
    findings.warnings += checked.warnings
    return findings


# ── Git state ───────────────────────────────────────────────────────────────

def git(root: Path, *args: str, binary: bool = False) -> Any:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=not binary)
    if proc.returncode != 0:
        stderr = proc.stderr if not binary else proc.stderr.decode(errors="replace")
        raise RunnerError(f"git {' '.join(args)} failed: {stderr.strip()}", 2, "GIT")
    return proc.stdout


def resolve_root(explicit: str | None) -> Path:
    base = Path(explicit).resolve() if explicit else Path.cwd()
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=base, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RunnerError(f"NOT_A_GIT_REPO: {base} is not inside a git repository", 2, "NOT_A_GIT_REPO")
    return Path(proc.stdout.strip())


def head_commit(root: Path) -> str | None:
    proc = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=root, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def worktree_digest(root: Path) -> str:
    base = head_commit(root) or EMPTY_TREE
    hasher = hashlib.sha256()
    hasher.update(git(root, "diff", base, "--binary", "--", ".", *SDD_EXCLUDES, binary=True))
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", ".", *SDD_EXCLUDES, binary=True)
    for raw in sorted(p for p in untracked.split(b"\0") if p):
        path = root / raw.decode()
        hasher.update(b"\0untracked\0" + raw + b"\0")
        if path.is_file():
            hasher.update(hashlib.sha256(path.read_bytes()).digest())
    return "sha256:" + hasher.hexdigest()


@dataclass(frozen=True, slots=True)
class RepoState:
    commit: str | None
    worktree_digest: str
    contract_digest: str | None

    def matches(self, entry: Mapping[str, Any]) -> bool:
        return (
            entry.get("commit") == self.commit
            and entry.get("worktree_digest") == self.worktree_digest
            and entry.get("contract_digest") == self.contract_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {"commit": self.commit, "worktree_digest": self.worktree_digest, "contract_digest": self.contract_digest}


def repo_state(feature: Feature) -> RepoState:
    root = feature.paths.root
    return RepoState(head_commit(root), worktree_digest(root), feature.contract_digest)


def git_user_email(root: Path) -> str | None:
    proc = subprocess.run(["git", "config", "user.email"], cwd=root, capture_output=True, text=True)
    return (proc.stdout.strip() or None) if proc.returncode == 0 else None


# ── Freeze ledger (append-only, hash-chained) ───────────────────────────────

def read_freeze_log(paths: Paths) -> list[dict[str, Any]]:
    if not paths.freeze_log.exists():
        return []
    entries: list[dict[str, Any]] = []
    for number, line in enumerate(paths.freeze_log.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as err:
            raise RunnerError(f"FREEZE_LOG_BROKEN: {paths.freeze_log.name} line {number} is not JSON", 1, "FREEZE_LOG_BROKEN") from err
        if not isinstance(row, dict):
            raise RunnerError(f"FREEZE_LOG_BROKEN: {paths.freeze_log.name} line {number} is not an object", 1, "FREEZE_LOG_BROKEN")
        entries.append(row)
    return entries


def freeze_chain_ok(entries: Sequence[Mapping[str, Any]]) -> bool:
    """Each entry carries the digest of the previous one, so deleting or
    editing a past line breaks the chain. Tamper-evident, not tamper-proof."""
    previous: str | None = None
    for entry in entries:
        if entry.get("prev") != previous:
            return False
        previous = canonical_digest(entry)
    return True


def freeze_fingerprint(entries: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    if not entries:
        return None
    return {"entries": len(entries), "last_digest": entries[-1].get("new_digest"), "last_entry": canonical_digest(entries[-1])}


def append_freeze_log(paths: Paths, entry: Mapping[str, Any]) -> None:
    paths.freeze_log.parent.mkdir(parents=True, exist_ok=True)
    with paths.freeze_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")


def load_pre_receipt(paths: Paths) -> dict[str, Any] | None:
    if not paths.pre_receipt.exists():
        return None
    try:
        data = json.loads(paths.pre_receipt.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def is_agent_identity(name: str) -> bool:
    normalized = " ".join(name.strip().lower().split())
    return not normalized or normalized in AGENT_IDENTITIES or bool(AGENT_IDENTITY.search(normalized))


def require_human(name: str, role: str) -> None:
    if is_agent_identity(name):
        raise RunnerError(
            f"NOT_A_HUMAN: {role} {name!r} looks like an agent, model, or harness name — "
            "record the name of the person who made the decision",
            2,
            "NOT_A_HUMAN",
        )


# ── Execution ───────────────────────────────────────────────────────────────

def eval_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
    env["AGENTSPEC_PYTHON"] = sys.executable
    return env


def is_bash_error(returncode: int, stderr: str) -> bool:
    """Shell-level breakage (not an assertion failure). Matches bash's own
    ``bash: line N:`` diagnostics at any exit code, because ``set -u`` exits 1."""
    if INTERPRETER_ERROR.search(stderr) or BASH_ERROR.search(stderr):
        return True
    return returncode in {126, 127}


def run_script(script: str, root: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", f"set -euo pipefail\n{script}"],
        cwd=root,
        env=eval_env(),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_deterministic(ev: Eval, root: Path) -> EvalResult:
    started = time.monotonic()
    try:
        proc = run_script(ev.run, root, ev.timeout_sec)
    except subprocess.TimeoutExpired:
        return EvalResult(ev, "error", reason="TIMEOUT", duration_sec=time.monotonic() - started)
    if proc.returncode == 0:
        status: Status = "pass"
        reason = None
    elif is_bash_error(proc.returncode, proc.stderr):
        status, reason = "error", "ENVIRONMENT" if INTERPRETER_ERROR.search(proc.stderr) else "BASH_ERROR"
    else:
        status, reason = "fail", None
    return EvalResult(
        ev,
        status,
        reason=reason,
        exit_code=proc.returncode,
        duration_sec=time.monotonic() - started,
        stdout=proc.stdout[-EVIDENCE_CHARS:],
        stderr=proc.stderr[-EVIDENCE_CHARS:],
    )


def collect_state(ev: Eval, root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, command in ev.state.items():
        try:
            proc = run_script(command, root, STATE_TIMEOUT)
        except subprocess.TimeoutExpired as err:
            raise RunnerError(f"STATE_COMMAND_TIMEOUT: {ev.id}.state.{key}", 1, "STATE_COMMAND_TIMEOUT") from err
        if proc.returncode != 0:
            raise RunnerError(
                f"STATE_COMMAND_FAILED: {ev.id}.state.{key} exited {proc.returncode}: {proc.stderr.strip()[:300]}",
                1,
                "STATE_COMMAND_FAILED",
            )
        values[key] = proc.stdout
    return values


def _argmax_level(answer: jev_client.Answer) -> int | None:
    if not answer.probabilities:
        return None
    level, _ = max(answer.probabilities.items(), key=lambda item: item[1])
    return int(level)


def _max_level(answer: jev_client.Answer) -> int | None:
    if not answer.probabilities:
        return None
    return max(int(k) for k in answer.probabilities)


def classify(answers: Mapping[str, jev_client.Answer], t: Thresholds) -> Decision:
    """Three-way decision. Noul alone never passes: every Score must also be
    confident and peak at its top level (see DESIGN, Decision 5)."""
    nouls = [a.noul for a in answers.values() if a.type == "noul"]
    scores = [a for a in answers.values() if a.type == "score"]
    confident = [s for s in scores if (s.confidence or 0.0) >= t.score_confidence]
    top = [s for s in confident if _argmax_level(s) is not None and _argmax_level(s) == _max_level(s)]
    bottom = [s for s in confident if _argmax_level(s) == 0]
    if scores and len(top) == len(scores) and all(n is not None and n >= t.noul_pass for n in nouls):
        return "pass"
    if bottom and any(n is not None and n <= t.noul_fail for n in nouls):
        return "fail"
    if bottom and not nouls:
        return "fail"
    return "escalated"


def load_calibration(paths: Paths) -> dict[str, Any] | None:
    if not paths.calibration.exists():
        return None
    try:
        return json.loads(paths.calibration.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def judge_command() -> list[str]:
    custom = os.environ.get("JUDGE_CMD")
    if custom:
        return shlex.split(custom)
    return [sys.executable, str(SCRIPTS_DIR / "judge.py")]


def render_for_judge(ev: Eval, state: Mapping[str, str]) -> str:
    parts = [f"Eval {ev.id} verifies {', '.join(ev.verifies) or '(complementary)'}: {ev.description}", "", "STATE:"]
    for key, value in state.items():
        parts += [f"--- {key} ---", value]
    parts += ["", "QUESTIONS (all must be satisfied for PASS):"]
    for q in ev.questions:
        suffix = f" Levels (low→high): {list(q.criteria)}. PASS requires the top level." if q.type == "score" else " PASS requires yes."
        parts.append(f"- [{q.type}] {q.instructions}{suffix}")
    return "\n".join(parts)


def escalate_to_judge(ev: Eval, state: Mapping[str, str], root: Path) -> tuple[Status, dict[str, Any]]:
    command = [*judge_command(), "--stdin", "--json", "--phase", "generic", "--context",
               f"AgentSpec graded eval {ev.id}: decide PASS only if every question is clearly satisfied by the STATE."]
    try:
        proc = subprocess.run(command, cwd=root, input=render_for_judge(ev, state), capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as err:
        return "pending", {"exit_code": None, "error": f"{type(err).__name__}: {err}"}
    info: dict[str, Any] = {"exit_code": proc.returncode}
    try:
        verdict = json.loads(proc.stdout)
        info["summary"] = verdict.get("summary")
        info["confidence"] = verdict.get("confidence")
    except (json.JSONDecodeError, AttributeError):
        pass
    if proc.returncode == 0:
        return "pass", info
    if proc.returncode == 1:
        return "fail", info
    info["error"] = proc.stderr.strip()[:300]
    return "pending", info


def run_graded(ev: Eval, feature: Feature, escalate: str, calibration: Mapping[str, Any] | None) -> EvalResult:
    started = time.monotonic()
    root = feature.paths.root
    try:
        state = collect_state(ev, root)
    except RunnerError as err:
        return EvalResult(ev, "error", reason=err.code, stderr=str(err), duration_sec=time.monotonic() - started)
    model = os.environ.get("JEV_MODEL", jev_client.DEFAULT_MODEL)
    calibrated = bool(calibration and calibration.get("approved") and calibration.get("model") == model)
    thresholds = Thresholds.from_mapping(calibration.get("thresholds") if calibration else None)
    jev_info: dict[str, Any] = {"model": model, "role": "authoritative" if calibrated else "advisory"}
    decision: Decision = "escalated"
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        jev_info["error"] = "CONFIG"
    elif jev_client.budget_remaining(feature.paths.ledger) <= 0:
        jev_info["error"] = "BUDGET"
    else:
        try:
            result = jev_client.decide(state, ev.questions, api_key=api_key, model=model)
            decision = classify(result.answers, thresholds)
            jev_info.update({
                "decision": decision,
                "answers": {qid: a.to_dict() for qid, a in result.answers.items()},
                "cost_usd": result.cost_usd,
                "resolved_model": result.model,
                "endpoint": result.endpoint,
                "truncated": result.truncated,
            })
            jev_client.append_ledger(feature.paths.ledger, model, f"{feature.paths.feature}:{ev.id}", decision, result.cost_usd)
        except jev_client.JevError as err:
            jev_info["error"] = err.code
            jev_info["detail"] = str(err)[:300]
            decision = "escalated"
        except (TypeError, ValueError, KeyError, AttributeError) as err:
            # A malformed answer that slipped past the client's parser: treat it
            # like any other unusable Jev response — escalate, never crash.
            jev_info["error"] = "PARSE"
            jev_info["detail"] = f"{type(err).__name__}: {err}"[:300]
            decision = "escalated"
    if calibrated and decision in ("pass", "fail"):
        return EvalResult(ev, decision, decided_by="jev", jev=jev_info, duration_sec=time.monotonic() - started)
    use_judge = escalate == "judge" or (escalate == "auto" and bool(api_key))
    if use_judge:
        status, judge_info = escalate_to_judge(ev, state, root)
        if status in ("pass", "fail"):
            return EvalResult(ev, status, decided_by="judge", jev=jev_info, judge=judge_info, duration_sec=time.monotonic() - started)
        return EvalResult(ev, "pending", reason="JUDGE_UNAVAILABLE", jev=jev_info, judge=judge_info, duration_sec=time.monotonic() - started)
    return EvalResult(ev, "pending", reason="NEEDS_HUMAN", jev=jev_info, duration_sec=time.monotonic() - started)


# ── Attestations and waivers ────────────────────────────────────────────────

def load_attestations(paths: Paths) -> dict[str, list[dict[str, Any]]]:
    if not paths.attestations.exists():
        return {"attestations": [], "waivers": []}
    data = json.loads(paths.attestations.read_text(encoding="utf-8"))
    data.setdefault("attestations", [])
    data.setdefault("waivers", [])
    return data


def save_attestations(paths: Paths, data: Mapping[str, Any]) -> None:
    paths.reports.mkdir(parents=True, exist_ok=True)
    paths.attestations.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def latest_for(entries: Sequence[Mapping[str, Any]], eval_id: str) -> Mapping[str, Any] | None:
    matching = [e for e in entries if e.get("eval_id") == eval_id]
    return matching[-1] if matching else None


def apply_human(result: EvalResult, attestations: Sequence[Mapping[str, Any]], state: RepoState) -> EvalResult:
    entry = latest_for(attestations, result.eval.id)
    if entry is None:
        return result
    if not state.matches(entry):
        result.status = "pending"
        result.reason = "STALE_ATTESTATION"
        result.human = {"owner": entry.get("owner"), "attested_at": entry.get("attested_at"), "stale": True}
        return result
    result.status = "pass" if entry.get("verdict") == "pass" else "fail"
    result.reason = None
    result.decided_by = "human"
    result.human = {k: entry.get(k) for k in ("owner", "evidence", "attested_at", "recorded_via", "recorded_by_email") if k in entry}
    return result


def apply_waiver(result: EvalResult, waivers: Sequence[Mapping[str, Any]], state: RepoState) -> EvalResult:
    if result.status == "pass":
        return result
    entry = latest_for(waivers, result.eval.id)
    if entry is None or not state.matches(entry):
        return result
    result.waiver = {k: entry.get(k) for k in ("supervisor", "reason", "waived_at", "recorded_by_email") if k in entry}
    result.waiver["previous_status"] = result.status
    if result.reason:
        result.waiver["previous_reason"] = result.reason
    result.status = "waived"
    result.reason = None
    return result


# ── Receipt and report ──────────────────────────────────────────────────────

def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_receipt(
    feature: Feature,
    state: RepoState,
    results: Sequence[EvalResult],
    structural: Findings,
    calibration: Mapping[str, Any] | None,
    legacy_waiver: Mapping[str, Any] | None = None,
    freeze_ledger: Mapping[str, Any] | None = None,
    pre_check: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    required = feature.gate_ids()
    by_id = {r.eval.id: r for r in results}
    gate_ok = bool(required) and all(by_id.get(eid) is not None and by_id[eid].status in ("pass", "waived") for eid in required)
    if legacy_waiver is not None:
        verdict = "PASS"
    else:
        verdict = "PASS" if gate_ok and not structural.errors else "FAIL"
    model = os.environ.get("JEV_MODEL", jev_client.DEFAULT_MODEL)
    receipt: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "feature": feature.paths.feature,
        **state.to_dict(),
        "extras_digest": feature.extras_digest,
        "evaluated_at": now_iso(),
        "runner_version": RUNNER_VERSION,
        "jev": {"model": model, "calibrated": bool(calibration and calibration.get("approved") and calibration.get("model") == model)},
        "results": [r.to_dict() for r in results],
        "required": required,
        "structural_errors": list(structural.errors),
        "warnings": list(structural.warnings),
        "waivers": [
            {"eval_id": r.eval.id, **(r.waiver or {})} for r in results if r.status == "waived"
        ],
        "verdict": verdict,
        "freeze_ledger": dict(freeze_ledger) if freeze_ledger else None,
        "pre_check": dict(pre_check) if pre_check else None,
    }
    if legacy_waiver is not None:
        receipt["legacy_waiver"] = {k: legacy_waiver.get(k) for k in ("supervisor", "reason", "waived_at", "recorded_by_email") if k in legacy_waiver}
    receipt["integrity"] = {"algorithm": INTEGRITY_ALGORITHM, "digest": integrity_digest(receipt)}
    return receipt


SEALED_FIELDS = (
    "schema", "feature", "commit", "worktree_digest", "contract_digest", "extras_digest", "evaluated_at",
    "runner_version", "results", "required", "structural_errors", "waivers", "verdict", "legacy_waiver",
    "freeze_ledger", "pre_check",
)


def integrity_digest(receipt: Mapping[str, Any]) -> str:
    """sha256 over the canonical JSON of every field the gate depends on,
    binding results to the commit, worktree and contract digests.

    There is no secret: anyone who can run this function can re-seal an edited
    receipt. It catches hand edits and partial rewrites, not a determined
    forger — that is what the recomputed verdict, the attestation cross-check
    and ``verify --rerun`` are for."""
    return canonical_digest({k: receipt.get(k) for k in SEALED_FIELDS})


STATUS_ICON = {"pass": "✅", "fail": "❌", "error": "💥", "escalated": "⚠️", "pending": "⏳", "waived": "🟡"}


def _cell(text: Any) -> str:
    return str(text if text is not None else "—").replace("|", "\\|").replace("\n", " ").strip() or "—"


def _evidence_summary(r: Mapping[str, Any]) -> str:
    if r.get("waiver"):
        w = r["waiver"]
        who = str(w.get("supervisor")) + (f" <{w['recorded_by_email']}>" if w.get("recorded_by_email") else "")
        return f"waiver de {who}: {w.get('reason')} (antes: {w.get('previous_status')})"
    if r.get("check_type") == "deterministic":
        ev = r.get("evidence", {})
        tail = (ev.get("stderr") or ev.get("stdout") or "").strip().splitlines()
        last = tail[-1][:160] if tail else ""
        return f"exit {r.get('exit_code')}" + (f" — {last}" if last else "")
    if r.get("check_type") == "graded":
        jev = r.get("jev", {})
        bits = [f"JEV {jev.get('role')}: {jev.get('decision', jev.get('error', '—'))}"]
        if r.get("judge"):
            bits.append(f"judge exit {r['judge'].get('exit_code')}")
        if r.get("human"):
            bits.append(f"humano: {r['human'].get('owner')}")
        return "; ".join(bits)
    human = r.get("human") or {}
    return f"{human.get('owner', 'sem atestação')}: {human.get('evidence', '')}".strip(": ")


def render_report(receipt: Mapping[str, Any], template_text: str) -> str:
    rows = ["| Eval | Verifica | Tipo | Origem | Status | Decidido por | Evidência |", "|------|----------|------|--------|--------|--------------|-----------|"]
    for r in receipt["results"]:
        rows.append("| " + " | ".join([
            f"`{r['eval_id']}`",
            _cell(", ".join(r.get("verifies", [])) or "—"),
            r["check_type"],
            r["origin"],
            f"{STATUS_ICON.get(r['status'], '')} {r['status']}" + (f" ({r['reason']})" if r.get("reason") else ""),
            _cell(r.get("decided_by")),
            _cell(_evidence_summary(r)),
        ]) + " |")
    if not receipt["results"]:
        rows.append("| — | — | — | — | — | — | Nenhum eval executado |")
    structural = receipt.get("structural_errors") or []
    structural_md = "\n".join(f"- `{e}`" for e in structural) if structural else "Nenhum."
    warnings = receipt.get("warnings") or []
    warnings_md = "\n".join(f"- `{w}`" for w in warnings) if warnings else "Nenhum."
    waivers = receipt.get("waivers") or []
    if receipt.get("legacy_waiver"):
        lw = receipt["legacy_waiver"]
        waivers = [*waivers, {"eval_id": "*legacy*", **lw}]
    if waivers:
        waiver_rows = ["| Eval | Supervisor | Motivo | Data |", "|------|------------|--------|------|"]
        waiver_rows += [f"| `{w.get('eval_id')}` | {_cell(w.get('supervisor'))} | {_cell(w.get('reason'))} | {_cell(w.get('waived_at'))} |" for w in waivers]
        waivers_md = "\n".join(waiver_rows)
    else:
        waivers_md = "Nenhum waiver registrado."
    counts: dict[str, int] = {}
    for r in receipt["results"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    summary = ", ".join(f"{STATUS_ICON.get(k, '')} {k}: {v}" for k, v in sorted(counts.items())) or "sem resultados"
    feature = receipt["feature"]
    if receipt["verdict"] == "PASS":
        next_step = f"`/ship .claude/sdd/features/DEFINE_{feature}.md`"
    else:
        blocking = [r["eval_id"] for r in receipt["results"] if r["status"] not in ("pass", "waived")]
        next_step = (
            f"Gate reprovado. Evals que bloqueiam: {', '.join(f'`{b}`' for b in blocking) or '—'}.\n\n"
            f"- Corrigir o código: `/continuar {feature}` e depois `/eval {feature}`\n"
            f"- Eval `human` pendente: `eval_runner.py attest {feature} --eval <id> --verdict pass|fail --owner <nome> --evidence <texto>`\n"
            f"- Aceitar conscientemente: `eval_runner.py waive {feature} --eval <id> --supervisor <nome> --reason <motivo>`"
        )
    values = {
        "feature": feature,
        "verdict": receipt["verdict"],
        "verdict_icon": "✅" if receipt["verdict"] == "PASS" else "❌",
        "evaluated_at": receipt["evaluated_at"],
        "commit": receipt.get("commit") or "(sem commit)",
        "worktree_digest": receipt.get("worktree_digest"),
        "contract_digest": receipt.get("contract_digest") or "(legado — sem contrato)",
        "jev_model": receipt["jev"]["model"],
        "jev_calibrated": "sim" if receipt["jev"]["calibrated"] else "não (JEV apenas consultivo)",
        "runner_version": receipt["runner_version"],
        "summary_counts": summary,
        "results_table": "\n".join(rows),
        "structural_errors": structural_md,
        "warnings": warnings_md,
        "waivers_table": waivers_md,
        "next_step": next_step,
    }
    return string.Template(template_text).safe_substitute(values)


def template_path() -> Path:
    candidates = [
        SCRIPTS_DIR.parent / ".claude" / "sdd" / "templates" / "EVAL_REPORT_TEMPLATE.md",
        SCRIPTS_DIR.parent / "sdd" / "templates" / "EVAL_REPORT_TEMPLATE.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RunnerError(f"TEMPLATE_NOT_FOUND: looked in {[str(c) for c in candidates]}", 2, "TEMPLATE_NOT_FOUND")


def write_outputs(paths: Paths, receipt: Mapping[str, Any]) -> None:
    paths.reports.mkdir(parents=True, exist_ok=True)
    paths.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths.report.write_text(render_report(receipt, template_path().read_text(encoding="utf-8")), encoding="utf-8")


# ── Commands ────────────────────────────────────────────────────────────────

def paths_for(args: argparse.Namespace) -> Paths:
    root = resolve_root(args.root)
    target = args.feature
    match = re.search(r"DESIGN_(.+)\.md$", target)
    name = match.group(1) if match else target
    return Paths(root, name)


def print_findings(findings: Findings) -> None:
    for error in findings.errors:
        print(f"  ✗ {error}")
    for warning in findings.warnings:
        print(f"  ⚠ {warning}")


def cmd_validate(args: argparse.Namespace) -> int:
    feature = load_feature(paths_for(args))
    if feature.is_legacy:
        print(f"LEGACY_NO_EVALS: {feature.paths.design.name} has no contract block")
        return 3
    findings = structural_findings(feature)
    if args.json:
        print(json.dumps({"errors": findings.errors, "warnings": findings.warnings}, indent=2))
    else:
        print(f"validate {feature.paths.feature}: {len(feature.contract)} contract + {len(feature.extras)} complementary evals")
        print_findings(findings)
        print("  ✓ contract is structurally valid" if not findings.errors else f"  {len(findings.errors)} error(s)")
    return 3 if findings.errors else 0


def cmd_freeze(args: argparse.Namespace) -> int:
    paths = paths_for(args)
    feature = load_feature(paths)
    if feature.is_legacy:
        print(f"LEGACY_NO_EVALS: {paths.design.name} has no contract block to freeze")
        return 3
    findings = structural_findings(feature)
    print_findings(findings)
    if findings.errors:
        print("  refusing to freeze an invalid contract")
        return 3
    digest = feature.contract_digest or ""
    frozen = read_frozen_digest(feature.design_text)
    log = read_freeze_log(paths)
    if log and not freeze_chain_ok(log):
        print(f"FREEZE_LOG_BROKEN: {paths.freeze_log.name} was edited — its hash chain no longer holds; restore it from git")
        return 1
    in_sync = not log or log[-1].get("new_digest") == frozen
    if frozen == digest and in_sync:
        print(f"frozen {paths.feature}: {digest} (already frozen — nothing to do)")
        return 0
    refreeze = frozen is not None or bool(log)
    reason = (args.reason or "").strip()
    if refreeze and len(reason) < MIN_REASON_CHARS:
        print(
            f"REFREEZE_NEEDS_REASON: {paths.design.name} is already frozen at {frozen or log[-1].get('new_digest')}. "
            f"Changing a frozen contract belongs to /iterate: rerun with --reason \"<why the evals changed, "
            f"≥ {MIN_REASON_CHARS} chars>\". The re-freeze is recorded in {paths.freeze_log.name}."
        )
        return 1
    paths.design.write_text(write_frozen_digest(feature.design_text, digest), encoding="utf-8")
    append_freeze_log(paths, {
        "schema": FREEZE_SCHEMA,
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "feature": paths.feature,
        "kind": "refreeze" if refreeze else "initial",
        "old_digest": frozen,
        "new_digest": digest,
        "reason": reason or None,
        "git_user_email": git_user_email(paths.root),
        "commit": head_commit(paths.root),
        "runner_version": RUNNER_VERSION,
        "prev": canonical_digest(log[-1]) if log else None,
    })
    print(f"{'re-frozen' if refreeze else 'frozen'} {paths.feature}: {digest}")
    if refreeze and paths.receipt.exists():
        print(f"  ⚠ {paths.receipt.name} is now stale — /ship will refuse until /eval runs again")
    return 0


def cmd_pre(args: argparse.Namespace) -> int:
    paths = paths_for(args)
    feature = load_feature(paths)
    if feature.is_legacy:
        print(f"pre {paths.feature}: no contract block (legacy DESIGN) — nothing to pre-check")
        return 0
    findings = structural_findings(feature)
    print_findings(findings)
    rows: list[dict[str, Any]] = []
    blocking = 0
    if not findings.errors:
        for ev in feature.contract:
            if ev.check_type != "deterministic":
                print(f"  · {ev.id}: {ev.check_type} — skipped before build")
                rows.append({"eval_id": ev.id, "check_type": ev.check_type, "status": "skipped"})
                continue
            result = run_deterministic(ev, paths.root)
            rows.append({"eval_id": ev.id, "check_type": ev.check_type, "status": result.status,
                         "reason": result.reason, "exit_code": result.exit_code})
            if result.status == "error":
                blocking += 1
                detail = (result.stderr.strip().splitlines() or [result.reason or ""])[-1]
                print(f"  ✗ {ev.id}: {result.reason} (exit {result.exit_code}) — {detail}")
            elif result.status == "pass":
                print(f"  ⚠ {ev.id}: ALREADY_PASSING — passes before the build; check that it discriminates")
            else:
                print(f"  ✓ {ev.id}: fails as expected (exit {result.exit_code})")
    outcome = "STRUCTURAL" if findings.errors else ("BLOCKED" if blocking else "OK")
    paths.reports.mkdir(parents=True, exist_ok=True)
    paths.pre_receipt.write_text(json.dumps({
        "schema": PRE_SCHEMA,
        "feature": paths.feature,
        "checked_at": now_iso(),
        "commit": head_commit(paths.root),
        "contract_digest": feature.contract_digest,
        "frozen_digest": read_frozen_digest(feature.design_text),
        "runner_version": RUNNER_VERSION,
        "outcome": outcome,
        "already_passing": [r["eval_id"] for r in rows if r["status"] == "pass"],
        "results": rows,
        "structural_errors": list(findings.errors),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if findings.errors:
        return 3
    if blocking:
        print(f"pre {paths.feature}: BLOCKED — {blocking} eval(s) cannot run; fix them in the DESIGN via /iterate")
        return 1
    print(f"pre {paths.feature}: OK — build may proceed ({paths.pre_receipt.relative_to(paths.root)})")
    return 0


def cmd_extra(args: argparse.Namespace) -> int:
    """Append complementary evals to EVALS_EXTRA_{F}.toml — the only file the
    eval phase may add to. Additive: existing extras are kept verbatim."""
    paths = paths_for(args)
    feature = load_feature(paths)
    if feature.is_legacy:
        print(f"LEGACY_NO_EVALS: {paths.design.name} has no contract — complementary evals need one")
        return 3
    text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    data = load_toml(text, args.file or "<stdin>")
    if set(data) - {"eval"}:
        print(f"  ✗ INVALID_SCHEMA: complementary evals may only declare [[eval]] tables, found {sorted(set(data) - {'eval'})}")
        return 3
    new, parsed = parse_evals(data, "complementary")
    if not new:
        print("  ✗ NO_EVALS: nothing to add")
        return 3
    findings = Findings(list(parsed.errors))
    checked = validate_evals(feature.contract, [*feature.extras, *new], feature.ats, feature.required)
    findings.errors += [e for e in checked.errors if not e.startswith(("ORPHAN_AT", "UNGATED_AT"))]
    findings.warnings += checked.warnings
    print_findings(findings)
    if findings.errors:
        print(f"  refusing to write {paths.extras.name}")
        return 3
    existing = paths.extras.read_text(encoding="utf-8") if paths.extras.exists() else ""
    separator = "" if not existing or existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    paths.extras.parent.mkdir(parents=True, exist_ok=True)
    paths.extras.write_text(existing + separator + text.rstrip("\n") + "\n", encoding="utf-8")
    print(f"extra {paths.feature}: +{len(new)} complementary eval(s) → {paths.extras.relative_to(paths.root)}")
    return 0


def freeze_warnings(paths: Paths, log: Sequence[Mapping[str, Any]]) -> list[str]:
    refreezes = [e for e in log if e.get("kind") == "refreeze"]
    if not refreezes:
        return []
    last = refreezes[-1]
    return [f"REFROZEN: contract re-frozen {len(refreezes)}x after the initial freeze; last {last.get('ts')} "
            f"by {last.get('git_user_email') or 'unknown'} — {last.get('reason')}"]


def pre_status(feature: Feature) -> tuple[dict[str, Any], list[str]]:
    pre = load_pre_receipt(feature.paths)
    if pre is None:
        return {"present": False}, [
            f"NO_PRE_RECEIPT: no `eval_runner.py pre {feature.paths.feature}` on record — nothing shows these evals failed before the build"
        ]
    info = {k: pre.get(k) for k in ("checked_at", "outcome", "contract_digest", "commit")}
    info["present"] = True
    warnings: list[str] = []
    if pre.get("contract_digest") != feature.contract_digest:
        warnings.append(f"PRE_STALE: the PRE receipt checked contract {pre.get('contract_digest')}, not the current {feature.contract_digest}")
    elif pre.get("outcome") != "OK":
        warnings.append(f"PRE_NOT_OK: the last pre-check ended {pre.get('outcome')}")
    if pre.get("already_passing"):
        warnings.append(f"PRE_ALREADY_PASSING: {', '.join(pre['already_passing'])} passed before the build")
    return info, warnings


def cmd_run(args: argparse.Namespace) -> int:
    paths = paths_for(args)
    feature = load_feature(paths)
    ledger_data = load_attestations(paths)
    state = repo_state(feature)
    calibration = load_calibration(paths)
    if feature.is_legacy:
        waiver = latest_for(ledger_data["waivers"], "*legacy*")
        if waiver is None or not state.matches(waiver):
            print(f"LEGACY_NO_EVALS: {paths.design.name} has no contract; add evals via /iterate or `waive --legacy`")
            return 1
        receipt = build_receipt(feature, state, [], Findings(), calibration, legacy_waiver=waiver)
        write_outputs(paths, receipt)
        print(f"run {paths.feature}: PASS (legacy waiver by {waiver.get('supervisor')})")
        return 0
    structural = structural_findings(feature)
    frozen = read_frozen_digest(feature.design_text)
    log = read_freeze_log(paths)
    if frozen is None:
        structural.errors.append("CONTRACT_NOT_FROZEN: run `eval_runner.py freeze` during /design or /iterate")
    elif frozen != feature.contract_digest:
        structural.errors.append(f"CONTRACT_TAMPERED: contract digest {feature.contract_digest} != frozen {frozen}")
    if log and not freeze_chain_ok(log):
        structural.errors.append(f"FREEZE_LOG_BROKEN: {paths.freeze_log.name} hash chain does not hold — restore it from git")
    elif log and log[-1].get("new_digest") != frozen:
        structural.errors.append(f"LEDGER_MISMATCH: Evals Digest {frozen} is not the last freeze in {paths.freeze_log.name} ({log[-1].get('new_digest')})")
    structural.warnings += freeze_warnings(paths, log)
    pre_info, pre_warnings = pre_status(feature)
    structural.warnings += pre_warnings
    results: list[EvalResult] = []
    if not structural.errors:
        for ev in feature.all_evals:
            if ev.check_type == "deterministic":
                result = run_deterministic(ev, paths.root)
            elif ev.check_type == "graded":
                result = run_graded(ev, feature, args.escalate, calibration)
                if result.status == "pending":
                    result = apply_human(result, ledger_data["attestations"], state)
            else:
                result = apply_human(EvalResult(ev, "pending", reason="NEEDS_HUMAN"), ledger_data["attestations"], state)
            results.append(apply_waiver(result, ledger_data["waivers"], state))
    receipt = build_receipt(feature, state, results, structural, calibration,
                            freeze_ledger=freeze_fingerprint(log), pre_check=pre_info)
    write_outputs(paths, receipt)
    if args.json:
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
    else:
        print(f"run {paths.feature}:")
        print_findings(structural)
        for r in results:
            extra = f" ({r.reason})" if r.reason else ""
            by = f" by {r.decided_by}" if r.decided_by else ""
            print(f"  {STATUS_ICON.get(r.status, '')} {r.eval.id}: {r.status}{extra}{by}")
        print(f"verdict: {receipt['verdict']} → {paths.receipt.relative_to(paths.root)}")
    if structural.errors:
        gate_codes = ("CONTRACT_TAMPERED", "LEDGER_MISMATCH", "FREEZE_LOG_BROKEN")
        return 1 if any(e.startswith(gate_codes) for e in structural.errors) else 3
    return 0 if receipt["verdict"] == "PASS" else 1


def cmd_attest(args: argparse.Namespace) -> int:
    paths = paths_for(args)
    feature = load_feature(paths)
    target = next((ev for ev in feature.all_evals if ev.id == args.eval), None)
    if target is None:
        raise RunnerError(f"UNKNOWN_EVAL: {args.eval}", 2, "UNKNOWN_EVAL")
    if target.check_type == "deterministic":
        raise RunnerError(f"NOT_ATTESTABLE: {args.eval} is deterministic — fix the code or waive it", 2, "NOT_ATTESTABLE")
    require_human(args.owner, "owner")
    state = repo_state(feature)
    data = load_attestations(paths)
    data["attestations"].append({
        "eval_id": args.eval,
        "verdict": args.verdict,
        "owner": args.owner,
        "evidence": args.evidence,
        "attested_at": now_iso(),
        "recorded_via": args.recorded_via,
        "recorded_by_email": git_user_email(paths.root),
        **state.to_dict(),
    })
    save_attestations(paths, data)
    print(f"attested {paths.feature}:{args.eval} = {args.verdict} by {args.owner} — rerun `eval_runner.py run {paths.feature}`")
    return 0


def cmd_waive(args: argparse.Namespace) -> int:
    paths = paths_for(args)
    feature = load_feature(paths)
    if args.legacy:
        if not feature.is_legacy:
            raise RunnerError("NOT_LEGACY: this DESIGN has a contract; waive individual evals instead", 2, "NOT_LEGACY")
        eval_id = "*legacy*"
        strict = True
    else:
        target = next((ev for ev in feature.all_evals if ev.id == args.eval), None)
        if target is None:
            raise RunnerError(f"UNKNOWN_EVAL: {args.eval}", 2, "UNKNOWN_EVAL")
        eval_id = args.eval
        strict = target.check_type == "deterministic"
    require_human(args.supervisor, "supervisor")
    reason = args.reason.strip()
    if strict and len(reason) < MIN_REASON_CHARS:
        kind = "a legacy DESIGN" if args.legacy else f"deterministic eval {eval_id}"
        raise RunnerError(
            f"REASON_TOO_SHORT: waiving {kind} needs a --reason of at least {MIN_REASON_CHARS} characters "
            f"(got {len(reason)}) — say why shipping without this proof is acceptable",
            2,
            "REASON_TOO_SHORT",
        )
    state = repo_state(feature)
    email = git_user_email(paths.root)
    data = load_attestations(paths)
    data["waivers"].append({
        "eval_id": eval_id,
        "supervisor": args.supervisor,
        "reason": reason,
        "waived_at": now_iso(),
        "recorded_by_email": email,
        **state.to_dict(),
    })
    save_attestations(paths, data)
    if email is None:
        print("  ⚠ git config user.email is not set — the waiver is recorded without an email")
    print(f"waived {paths.feature}:{eval_id} by {args.supervisor} — rerun `eval_runner.py run {paths.feature}`")
    return 0


VERIFY_MESSAGES = {
    "OK": "gate satisfied — ready to ship",
    "OK_LEGACY_WAIVED": "legacy DESIGN shipped under a named waiver",
    "OK_LEGACY_RECEIPT": "gate satisfied by a receipt from runner < 1.1 (unsealed, no freeze ledger) — ready to ship",
    "NO_RECEIPT": "no eval receipt — run /eval {F} before /ship",
    "RECEIPT_INVALID": "the receipt is not valid JSON of schema agentspec/eval-receipt/v1 — rerun /eval {F}",
    "INTEGRITY_MISMATCH": "the receipt was edited after eval_runner.py wrote it — rerun /eval {F}",
    "UNSEALED_RECEIPT": "the receipt has no integrity seal although the contract has a freeze ledger — rerun /eval {F}",
    "VERDICT_FAIL": "eval verdict is FAIL — run /continuar {F}, attest pending evals, or record a waiver",
    "RECEIPT_INCOMPLETE": "the receipt lacks a result for a required eval — rerun /eval {F}",
    "VERDICT_MISMATCH": "the receipt says PASS but its results do not satisfy [gate] required — rerun /eval {F}",
    "UNBACKED_DECISION": "a human pass or waiver in the receipt has no matching entry in EVAL_{F}.attestations.json — rerun /eval {F}",
    "RERUN_FAIL": "a required deterministic eval no longer passes when re-executed — run /continuar {F}",
    "STALE_COMMIT": "HEAD moved since /eval — rerun /eval {F}",
    "STALE_WORKTREE": "code changed since /eval (uncommitted edits) — rerun /eval {F}",
    "STALE_CONTRACT": "eval contract changed since /eval — rerun /eval {F}",
    "REFROZEN_AFTER_RUN": "the contract was re-frozen after /eval ran — rerun /eval {F}",
    "LEDGER_MISMATCH": "the Evals Digest is not the last entry of EVAL_{F}.freeze.log — freeze only through `eval_runner.py freeze` (/iterate)",
    "FREEZE_LOG_BROKEN": "EVAL_{F}.freeze.log was edited (hash chain broken) — restore it from git",
    "CONTRACT_TAMPERED": "## Evals block does not match its Evals Digest — change it through /iterate",
    "CONTRACT_NOT_FROZEN": "DESIGN has no Evals Digest — freeze it during /design or /iterate",
    "LEGACY_NO_EVALS": "DESIGN has no ## Evals — add evals via /iterate or `waive --legacy`",
}


def load_receipt(paths: Paths) -> tuple[dict[str, Any] | None, bool]:
    """Return (receipt, readable). A missing file is (None, True)."""
    if not paths.receipt.exists():
        return None, True
    try:
        data = json.loads(paths.receipt.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, False
    if not isinstance(data, dict) or data.get("schema") != RECEIPT_SCHEMA or not isinstance(data.get("results", []), list):
        return None, False
    return data, True


def seal_code(receipt: Mapping[str, Any], log: Sequence[Mapping[str, Any]]) -> str | None:
    """None when sealed and intact; "LEGACY" for an unsealed pre-1.1 receipt
    that is still acceptable; otherwise a refusal code."""
    seal = receipt.get("integrity")
    if seal is None:
        return "UNSEALED_RECEIPT" if log else "LEGACY"
    if not isinstance(seal, Mapping) or seal.get("algorithm") != INTEGRITY_ALGORITHM:
        return "INTEGRITY_MISMATCH"
    return None if seal.get("digest") == integrity_digest(receipt) else "INTEGRITY_MISMATCH"


def receipt_consistency(feature: Feature, receipt: Mapping[str, Any], attestations: Mapping[str, Any]) -> str | None:
    """Recompute the gate from the receipt's results — never from its stored
    ``verdict`` — against the *current* contract's required ids. Human passes
    and waivers must be backed by the attestations file for the receipt's own
    repo state. Returns a refusal code or None."""
    state = RepoState(receipt.get("commit"), str(receipt.get("worktree_digest")), receipt.get("contract_digest"))
    if feature.is_legacy:
        entry = latest_for(attestations.get("waivers", []), "*legacy*")
        return None if entry is not None and state.matches(entry) else "UNBACKED_DECISION"
    required = feature.gate_ids()
    results = receipt.get("results")
    if not required or not isinstance(results, list) or not results:
        return "RECEIPT_INCOMPLETE"
    if receipt.get("structural_errors"):
        return "VERDICT_MISMATCH"
    by_id: dict[str, Mapping[str, Any]] = {}
    for r in results:
        if not isinstance(r, Mapping) or r.get("eval_id") in by_id:
            return "RECEIPT_INCOMPLETE"
        by_id[str(r.get("eval_id"))] = r
    evals = {ev.id: ev for ev in feature.all_evals}
    for eval_id in required:
        r, ev = by_id.get(eval_id), evals.get(eval_id)
        if r is None or ev is None:
            return "RECEIPT_INCOMPLETE"
        if r.get("check_type") != ev.check_type:
            return "VERDICT_MISMATCH"
        status = r.get("status")
        if status == "waived":
            entry = latest_for(attestations.get("waivers", []), eval_id)
            if entry is None or not state.matches(entry):
                return "UNBACKED_DECISION"
        elif status == "pass":
            if ev.check_type == "deterministic" and r.get("exit_code") != 0:
                return "VERDICT_MISMATCH"
            if ev.check_type == "human" or r.get("decided_by") == "human":
                entry = latest_for(attestations.get("attestations", []), eval_id)
                if entry is None or entry.get("verdict") != "pass" or not state.matches(entry):
                    return "UNBACKED_DECISION"
        else:
            return "VERDICT_MISMATCH"
    return None


def rerun_failures(feature: Feature) -> list[str]:
    required = set(feature.gate_ids())
    failed: list[str] = []
    for ev in feature.all_evals:
        if ev.check_type == "deterministic" and ev.id in required:
            if run_deterministic(ev, feature.paths.root).status != "pass":
                failed.append(ev.id)
    return failed


def verify_code(feature: Feature, rerun: bool = False) -> tuple[str, str | None]:
    paths = feature.paths
    receipt, readable = load_receipt(paths)
    attestations = load_attestations(paths)
    if feature.is_legacy:
        if not readable:
            return "RECEIPT_INVALID", None
        if not (receipt and receipt.get("legacy_waiver") and receipt.get("verdict") == "PASS"):
            return "LEGACY_NO_EVALS", None
        seal = seal_code(receipt, [])
        if seal not in (None, "LEGACY"):
            return seal, None
        if receipt.get("commit") != head_commit(paths.root):
            return "STALE_COMMIT", None
        if receipt.get("worktree_digest") != worktree_digest(paths.root):
            return "STALE_WORKTREE", None
        if receipt_consistency(feature, receipt, attestations):
            return "UNBACKED_DECISION", None
        return "OK_LEGACY_WAIVED", None
    frozen = read_frozen_digest(feature.design_text)
    if frozen is None:
        return "CONTRACT_NOT_FROZEN", None
    if frozen != feature.contract_digest:
        return "CONTRACT_TAMPERED", None
    log = read_freeze_log(paths)
    if log and not freeze_chain_ok(log):
        return "FREEZE_LOG_BROKEN", None
    if log and log[-1].get("new_digest") != frozen:
        return "LEDGER_MISMATCH", f"Evals Digest {frozen} != last freeze {log[-1].get('new_digest')}"
    if not readable:
        return "RECEIPT_INVALID", None
    if receipt is None:
        return "NO_RECEIPT", None
    seal = seal_code(receipt, log)
    if seal not in (None, "LEGACY"):
        return seal, None
    if receipt.get("verdict") != "PASS":
        return "VERDICT_FAIL", None
    if receipt.get("commit") != head_commit(paths.root):
        return "STALE_COMMIT", None
    if receipt.get("worktree_digest") != worktree_digest(paths.root):
        return "STALE_WORKTREE", None
    if receipt.get("contract_digest") != feature.contract_digest or receipt.get("extras_digest") != feature.extras_digest:
        return "STALE_CONTRACT", None
    if seal is None and receipt.get("freeze_ledger") != freeze_fingerprint(log):
        return "REFROZEN_AFTER_RUN", f"ledger has {len(log)} entr{'y' if len(log) == 1 else 'ies'}; the receipt saw {(receipt.get('freeze_ledger') or {}).get('entries', 0)}"
    inconsistency = receipt_consistency(feature, receipt, attestations)
    if inconsistency:
        return inconsistency, None
    if rerun:
        failed = rerun_failures(feature)
        if failed:
            return "RERUN_FAIL", ", ".join(failed)
    return ("OK_LEGACY_RECEIPT" if seal == "LEGACY" else "OK"), None


def cmd_verify(args: argparse.Namespace) -> int:
    feature = load_feature(paths_for(args))
    try:
        code, detail = verify_code(feature, rerun=args.rerun)
    except RunnerError as err:
        if err.code not in VERIFY_MESSAGES:
            raise
        code, detail = err.code, str(err)
    message = VERIFY_MESSAGES[code].replace("{F}", feature.paths.feature)
    if args.json:
        print(json.dumps({"code": code, "message": message, "detail": detail}))
    else:
        print(f"verify {feature.paths.feature}: {code} — {message}" + (f" ({detail})" if detail else ""))
    return 0 if code.startswith("OK") else 1


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = load_toml(path.read_text(encoding="utf-8"), str(path))
    cases = data.get("case", [])
    if not isinstance(cases, list) or not cases:
        raise RunnerError(f"NO_CASES: {path} needs [[case]] tables", 3, "NO_CASES")
    return cases


def cmd_calibrate(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    paths = Paths(root, "_calibration")
    cases = load_cases(Path(args.cases).resolve())
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RunnerError("CONFIG: OPENROUTER_API_KEY not set", 2, "CONFIG")
    model = os.environ.get("JEV_MODEL", jev_client.DEFAULT_MODEL)
    thresholds = Thresholds()
    if jev_client.budget_remaining(paths.ledger) < len(cases):
        raise RunnerError(f"BUDGET: need {len(cases)} Jev calls; raise JEV_BUDGET", 2, "BUDGET")
    outcomes: list[dict[str, Any]] = []
    for case in cases:
        questions = tuple(jev_client.Question(
            id=str(q["id"]), type=q["type"], instructions=str(q["instructions"]),
            criteria=tuple(str(c) for c in q.get("criteria", []) or []),
        ) for q in case.get("questions", []))
        expected = str(case.get("expected", ""))
        if expected not in ("pass", "fail"):
            raise RunnerError(f"INVALID_CASE: {case.get('id')} expected must be pass|fail", 3, "INVALID_CASE")
        result = jev_client.decide({str(k): str(v) for k, v in case.get("state", {}).items()}, questions, api_key=api_key, model=model)
        decision = classify(result.answers, thresholds)
        jev_client.append_ledger(paths.ledger, model, f"calibration:{case.get('id')}", decision, result.cost_usd)
        outcomes.append({
            "id": case.get("id"),
            "expected": expected,
            "decision": decision,
            "answers": {qid: a.to_dict() for qid, a in result.answers.items()},
        })
    n = len(outcomes)
    decided = [o for o in outcomes if o["decision"] in ("pass", "fail")]
    agreed = [o for o in decided if o["decision"] == o["expected"]]
    coverage = len(decided) / n if n else 0.0
    agreement = len(agreed) / len(decided) if decided else 0.0
    approved = n >= CALIBRATION_MIN_CASES and coverage >= CALIBRATION_MIN_COVERAGE and agreement >= CALIBRATION_MIN_AGREEMENT
    report = {
        "schema": CALIBRATION_SCHEMA,
        "model": model,
        "calibrated_at": now_iso(),
        "n": n,
        "decided": len(decided),
        "agreed": len(agreed),
        "coverage": round(coverage, 3),
        "agreement": round(agreement, 3),
        "thresholds": thresholds.to_dict(),
        "criteria": {"min_cases": CALIBRATION_MIN_CASES, "min_coverage": CALIBRATION_MIN_COVERAGE, "min_agreement": CALIBRATION_MIN_AGREEMENT},
        "approved": approved,
        "cases": outcomes,
    }
    paths.calibration.parent.mkdir(parents=True, exist_ok=True)
    paths.calibration.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"calibrate: n={n} decided={len(decided)} agreed={len(agreed)} coverage={coverage:.0%} agreement={agreement:.0%} → approved={approved}")
    return 0 if approved else 1


# ── CLI ─────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eval_runner.py", description="AgentSpec post-build eval gate")
    parser.add_argument("--root", default=None, help="Repository root (default: git toplevel of the cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    def feature_cmd(name: str, help_text: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("feature", help="Feature name (POST_BUILD_EVALS) or path to DESIGN_{F}.md")
        p.add_argument("--json", action="store_true", help="Machine-readable output")
        return p

    feature_cmd("validate", "Structural checks on the eval contract")
    freeze = feature_cmd("freeze", "Write the contract digest into the DESIGN metadata and the freeze ledger")
    freeze.add_argument("--reason", default=None,
                        help=f"Required to re-freeze an already frozen contract (/iterate); at least {MIN_REASON_CHARS} characters")
    feature_cmd("pre", "Pre-build check: evals must run cleanly and fail (persists the PRE receipt)")
    extra = feature_cmd("extra", "Append complementary evals (TOML from --file or stdin) to EVALS_EXTRA_{F}.toml")
    extra.add_argument("--file", default=None, help="TOML file with [[eval]] tables (default: read stdin)")
    run = feature_cmd("run", "Execute evals and write the receipt + report")
    run.add_argument("--escalate", choices=["auto", "judge", "human"], default="auto",
                     help="How to resolve graded evals Jev cannot decide (default: judge if OPENROUTER_API_KEY, else human)")
    attest = feature_cmd("attest", "Record a human decision for a human or graded eval")
    attest.add_argument("--eval", required=True)
    attest.add_argument("--verdict", required=True, choices=["pass", "fail"])
    attest.add_argument("--owner", required=True)
    attest.add_argument("--evidence", required=True)
    attest.add_argument("--recorded-via", default="cli")
    waive = feature_cmd("waive", "Record a named waiver for an eval or a legacy DESIGN")
    target = waive.add_mutually_exclusive_group(required=True)
    target.add_argument("--eval")
    target.add_argument("--legacy", action="store_true")
    waive.add_argument("--supervisor", required=True, help="The person accepting the risk (agent/model names are refused)")
    waive.add_argument("--reason", required=True,
                       help=f"Why this is acceptable; deterministic and legacy waivers need at least {MIN_REASON_CHARS} characters")
    verify = feature_cmd("verify", "Ship gate: recompute the verdict from the receipt and match it to the current state")
    verify.add_argument("--rerun", action="store_true", help="Also re-execute every required deterministic eval")
    calibrate = sub.add_parser("calibrate", help="Measure Jev agreement on labelled cases")
    calibrate.add_argument("cases", help="TOML file with [[case]] tables (state, questions, expected)")
    return parser


COMMANDS = {
    "validate": cmd_validate,
    "freeze": cmd_freeze,
    "pre": cmd_pre,
    "extra": cmd_extra,
    "run": cmd_run,
    "attest": cmd_attest,
    "waive": cmd_waive,
    "verify": cmd_verify,
    "calibrate": cmd_calibrate,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except RunnerError as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        return err.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

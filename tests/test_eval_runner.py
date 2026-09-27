"""Tests for scripts/eval_runner.py — the deterministic post-build eval gate.

Every scenario spins up a throwaway git repository under ``tmp_path``, copies
a DEFINE/DESIGN fixture pair into ``.claude/sdd/features/`` under whatever
feature name the test picks, and drives the CLI in-process via
``eval_runner.main([...])``. Network is never touched: graded evals are
exercised by monkeypatching ``eval_runner.jev_client.decide`` with parsed
fixture responses, and escalation to ``/judge`` uses a tiny fake script
wired in through ``JUDGE_CMD``.

Test names follow the DESIGN's "Plano de Testes por AT" table exactly so the
bootstrap contract (``pytest -k atNNN``) selects the right tests.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import eval_runner
import jev_client

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "evals"
BASIC_DIR = FIXTURES / "basic"
CASES_DIR = FIXTURES / "cases"
JEV_DIR = FIXTURES / "jev"
KB_DIR = FIXTURES / "kb_evolution"
FE_DIR = FIXTURES / "frontend_ecosystem"

FAKE_JUDGE = """#!/usr/bin/env python3
import sys, json
sys.stdin.read()
print(json.dumps({{"verdict": "{verdict}", "summary": "fake judge", "confidence": 0.9}}))
sys.exit({code})
"""


# ── Repo / fixture helpers ───────────────────────────────────────────────────

def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def make_repo(tmp_path: Path) -> Path:
    """A fresh git repo, resolved to match what `git rev-parse --show-toplevel`
    (and therefore `eval_runner.resolve_root`) will report."""
    root = (tmp_path / "repo")
    root.mkdir()
    root = root.resolve()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test Suite")
    (root / ".gitkeep").write_text("", encoding="utf-8")
    commit_all(root, "init")
    return root


def commit_all(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "--allow-empty", "-m", message)


def install_feature(root: Path, name: str, define_src: Path, design_src: Path) -> None:
    features = root / ".claude" / "sdd" / "features"
    features.mkdir(parents=True, exist_ok=True)
    (features / f"DEFINE_{name}.md").write_text(define_src.read_text(encoding="utf-8"), encoding="utf-8")
    (features / f"DESIGN_{name}.md").write_text(design_src.read_text(encoding="utf-8"), encoding="utf-8")


def receipt_for(root: Path, name: str) -> dict:
    return json.loads((root / ".claude" / "sdd" / "reports" / f"EVAL_{name}.json").read_text(encoding="utf-8"))


def report_for(root: Path, name: str) -> str:
    return (root / ".claude" / "sdd" / "reports" / f"EVAL_REPORT_{name}.md").read_text(encoding="utf-8")


def setup_basic(root: Path, name: str, *, satisfy_all: bool = True) -> None:
    install_feature(root, name, BASIC_DIR / "DEFINE_BASIC.md", BASIC_DIR / "DESIGN_BASIC.md")
    if satisfy_all:
        (root / "greeting.txt").write_text("hello agentspec\n", encoding="utf-8")
        (root / "config.json").write_text(json.dumps({"ready": True}), encoding="utf-8")
        (root / "greet.sh").write_text("echo hi\n", encoding="utf-8")
    commit_all(root, "build output")


def write_fake_judge(tmp_path: Path, name: str, verdict: str, code: int) -> str:
    script = tmp_path / name
    script.write_text(FAKE_JUDGE.format(verdict=verdict, code=code), encoding="utf-8")
    return f"{sys.executable} {script}"


# ── AT-001: happy path ───────────────────────────────────────────────────────

def test_at001_happy_path(tmp_path):
    root = make_repo(tmp_path)
    setup_basic(root, "BASIC1")

    assert eval_runner.main(["--root", str(root), "freeze", "BASIC1"]) == 0
    assert eval_runner.main(["--root", str(root), "run", "BASIC1"]) == 0

    receipt = receipt_for(root, "BASIC1")
    assert receipt["verdict"] == "PASS"
    assert receipt["commit"] == eval_runner.head_commit(root)
    assert receipt["worktree_digest"] == eval_runner.worktree_digest(root)
    assert receipt["contract_digest"]
    assert len(receipt["results"]) == 3
    assert all(r["status"] == "pass" for r in receipt["results"])

    assert eval_runner.main(["--root", str(root), "verify", "BASIC1"]) == 0

    report = report_for(root, "BASIC1")
    assert "Resultados por Eval" in report
    assert "eval_1" in report and "eval_2" in report and "eval_3" in report


# ── AT-002: a failing eval ───────────────────────────────────────────────────

def test_at002_eval_fails(tmp_path):
    root = make_repo(tmp_path)
    setup_basic(root, "BASIC2", satisfy_all=False)
    # eval_2 and eval_3 pass; eval_1 fails (greeting.txt is missing).
    (root / "config.json").write_text(json.dumps({"ready": True}), encoding="utf-8")
    (root / "greet.sh").write_text("echo hi\n", encoding="utf-8")
    commit_all(root, "partial build")

    assert eval_runner.main(["--root", str(root), "freeze", "BASIC2"]) == 0
    assert eval_runner.main(["--root", str(root), "run", "BASIC2"]) == 1

    receipt = receipt_for(root, "BASIC2")
    assert receipt["verdict"] == "FAIL"
    eval1 = next(r for r in receipt["results"] if r["eval_id"] == "eval_1")
    assert eval1["status"] == "fail"
    assert "evidence" in eval1
    assert "not found" in eval1["evidence"]["stderr"]

    report = report_for(root, "BASIC2")
    assert "/continuar" in report

    assert eval_runner.main(["--root", str(root), "verify", "BASIC2"]) == 1


# ── AT-003: ship without a receipt ───────────────────────────────────────────

def test_at003_ship_without_receipt(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "BASIC3")
    assert eval_runner.main(["--root", str(root), "freeze", "BASIC3"]) == 0
    capsys.readouterr()

    assert eval_runner.main(["--root", str(root), "verify", "BASIC3", "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["code"] == "NO_RECEIPT"


# ── AT-004: stale receipt (commit / worktree) ───────────────────────────────

def test_at004_stale_commit(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "BASIC4")
    eval_runner.main(["--root", str(root), "freeze", "BASIC4"])
    assert eval_runner.main(["--root", str(root), "run", "BASIC4"]) == 0
    assert eval_runner.main(["--root", str(root), "verify", "BASIC4"]) == 0

    (root / "NOTES.md").write_text("post-eval note\n", encoding="utf-8")
    commit_all(root, "post eval change")

    capsys.readouterr()
    assert eval_runner.main(["--root", str(root), "verify", "BASIC4", "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["code"] == "STALE_COMMIT"


def test_at004_stale_worktree(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "BASIC5")
    eval_runner.main(["--root", str(root), "freeze", "BASIC5"])
    eval_runner.main(["--root", str(root), "run", "BASIC5"])
    capsys.readouterr()

    # Uncommitted edit to a tracked file — code changed since /eval.
    (root / "greeting.txt").write_text("hello agentspec\nextra line\n", encoding="utf-8")
    eval_runner.main(["--root", str(root), "verify", "BASIC5", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["code"] == "STALE_WORKTREE"

    # Revert the code edit; an edit confined to .claude/sdd/ must not count.
    (root / "greeting.txt").write_text("hello agentspec\n", encoding="utf-8")
    (root / ".claude" / "sdd" / "features" / "SCRATCH_NOTE.md").write_text("note\n", encoding="utf-8")
    assert eval_runner.main(["--root", str(root), "verify", "BASIC5"]) == 0


# ── AT-005: stale contract ───────────────────────────────────────────────────

def test_at005_stale_contract(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "BASIC6")
    eval_runner.main(["--root", str(root), "freeze", "BASIC6"])
    eval_runner.main(["--root", str(root), "run", "BASIC6"])

    design_path = root / ".claude" / "sdd" / "features" / "DESIGN_BASIC6.md"
    text = design_path.read_text(encoding="utf-8").replace(
        'description = "greeting.txt existe e contém a saudação esperada"',
        'description = "greeting.txt existe e contém a saudação esperada (revisado via /iterate)"',
    )
    assert text != design_path.read_text(encoding="utf-8")
    design_path.write_text(text, encoding="utf-8")
    # Deliberately left uncommitted: .claude/sdd/ is excluded from the
    # worktree digest (Decision 3), so re-freezing here changes the contract
    # digest without moving HEAD or the worktree digest — isolating
    # STALE_CONTRACT from STALE_COMMIT/STALE_WORKTREE.
    assert eval_runner.main(["--root", str(root), "freeze", "BASIC6"]) == 0

    capsys.readouterr()
    assert eval_runner.main(["--root", str(root), "verify", "BASIC6", "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["code"] == "STALE_CONTRACT"


# ── AT-006: PRE-check blocks on bash errors ─────────────────────────────────

def test_at006_pre_bash_error(tmp_path, capsys):
    root = make_repo(tmp_path)
    install_feature(root, "BASHERR1", CASES_DIR / "define_bash_error.md", CASES_DIR / "design_bash_error.md")
    commit_all(root, "init basherr1")

    assert eval_runner.main(["--root", str(root), "freeze", "BASHERR1"]) == 0
    capsys.readouterr()
    assert eval_runner.main(["--root", str(root), "pre", "BASHERR1"]) == 1
    out = capsys.readouterr().out
    assert "eval_missing_cmd: BASH_ERROR" in out
    # `set -u` exits 1, yet an unbound variable is still shell breakage, not a failing assertion.
    assert "eval_unbound: BASH_ERROR" in out


def test_at006_pre_syntax_error(tmp_path, capsys):
    root = make_repo(tmp_path)
    install_feature(root, "BASHERR3", CASES_DIR / "define_bash_error.md", CASES_DIR / "design_bash_error.md")
    design = root / ".claude" / "sdd" / "features" / "DESIGN_BASHERR3.md"
    design.write_text(design.read_text(encoding="utf-8").replace("nonexistent_command_xyz_12345", "if then"), encoding="utf-8")
    commit_all(root, "init basherr3")

    assert eval_runner.main(["--root", str(root), "pre", "BASHERR3"]) == 3
    out = capsys.readouterr().out
    assert "BASH_SYNTAX" in out
    assert "eval_missing_cmd" in out


def test_at006_pre_interpreter_error(tmp_path, capsys):
    root = make_repo(tmp_path)
    install_feature(root, "BASHERR2", CASES_DIR / "define_bash_error.md", CASES_DIR / "design_bash_error.md")
    commit_all(root, "init basherr2")

    assert eval_runner.main(["--root", str(root), "freeze", "BASHERR2"]) == 0
    capsys.readouterr()
    assert eval_runner.main(["--root", str(root), "pre", "BASHERR2"]) == 1
    out = capsys.readouterr().out
    assert "eval_interpreter" in out
    assert "ENVIRONMENT" in out
    # An interpreter error is a broken environment, not a plain bash mistake.
    assert "eval_interpreter: ENVIRONMENT" in out


# ── AT-007: PRE-check warns on an already-passing eval ──────────────────────

def test_at007_pre_already_passing(tmp_path, capsys):
    root = make_repo(tmp_path)
    install_feature(root, "TRIVIAL1", CASES_DIR / "define_trivial.md", CASES_DIR / "design_trivial.md")
    commit_all(root, "init trivial")

    assert eval_runner.main(["--root", str(root), "freeze", "TRIVIAL1"]) == 0
    capsys.readouterr()
    assert eval_runner.main(["--root", str(root), "pre", "TRIVIAL1"]) == 0
    out = capsys.readouterr().out
    assert "ALREADY_PASSING" in out


# ── AT-008: orphan / unknown AT ──────────────────────────────────────────────

def test_at008_orphan_at(tmp_path, capsys):
    root = make_repo(tmp_path)
    install_feature(root, "ORPHAN1", CASES_DIR / "define_orphan.md", CASES_DIR / "design_orphan.md")
    commit_all(root, "init orphan")

    assert eval_runner.main(["--root", str(root), "validate", "ORPHAN1"]) == 3
    out = capsys.readouterr().out
    assert "ORPHAN_AT: AT-002" in out
    assert "UNKNOWN_AT" in out
    assert "AT-099" in out


# ── AT-009: contract tampering / complementary evals ────────────────────────

def test_at009_contract_tampered(tmp_path):
    root = make_repo(tmp_path)
    setup_basic(root, "BASIC7")
    eval_runner.main(["--root", str(root), "freeze", "BASIC7"])

    design_path = root / ".claude" / "sdd" / "features" / "DESIGN_BASIC7.md"
    text = design_path.read_text(encoding="utf-8").replace(
        'bash greet.sh | grep -qx "hi"',
        'bash greet.sh | grep -qx "hi"\necho tampered',
    )
    design_path.write_text(text, encoding="utf-8")  # note: no re-freeze
    commit_all(root, "tamper the contract without freezing")

    code = eval_runner.main(["--root", str(root), "run", "BASIC7"])
    assert code == 1
    receipt = receipt_for(root, "BASIC7")
    assert receipt["verdict"] == "FAIL"
    assert any(e.startswith("CONTRACT_TAMPERED") for e in receipt["structural_errors"])


def test_at009_complementary_accepted(tmp_path):
    root = make_repo(tmp_path)
    setup_basic(root, "BASIC8")
    eval_runner.main(["--root", str(root), "freeze", "BASIC8"])

    extra = root / ".claude" / "sdd" / "features" / "EVALS_EXTRA_BASIC8.toml"
    extra.write_text(
        "[[eval]]\n"
        'id = "eval_extra1"\n'
        'check_type = "deterministic"\n'
        'description = "Extra check added during /eval"\n'
        "run = '''\n"
        "true\n"
        "'''\n",
        encoding="utf-8",
    )
    commit_all(root, "add complementary eval")

    assert eval_runner.main(["--root", str(root), "run", "BASIC8"]) == 0
    receipt = receipt_for(root, "BASIC8")
    extra_result = next(r for r in receipt["results"] if r["eval_id"] == "eval_extra1")
    assert extra_result["origin"] == "complementary"
    assert extra_result["status"] == "pass"
    assert "eval_extra1" in receipt["required"]
    assert receipt["verdict"] == "PASS"


# ── AT-010: human eval, pending / stale attestation ─────────────────────────

def test_at010_human_pending(tmp_path):
    root = make_repo(tmp_path)
    install_feature(root, "HUMAN1", CASES_DIR / "define_human.md", CASES_DIR / "design_human.md")
    commit_all(root, "init human1")
    eval_runner.main(["--root", str(root), "freeze", "HUMAN1"])

    assert eval_runner.main(["--root", str(root), "run", "HUMAN1"]) == 1
    receipt = receipt_for(root, "HUMAN1")
    assert receipt["verdict"] == "FAIL"
    assert receipt["results"][0]["status"] == "pending"

    assert eval_runner.main([
        "--root", str(root), "attest", "HUMAN1",
        "--eval", "eval_h1", "--verdict", "pass",
        "--owner", "Marco", "--evidence", "revisei manualmente e confirmo",
    ]) == 0
    assert eval_runner.main(["--root", str(root), "run", "HUMAN1"]) == 0
    assert receipt_for(root, "HUMAN1")["verdict"] == "PASS"

    # Code changes after the attestation invalidate it.
    (root / "CHANGED.md").write_text("code changed after attestation\n", encoding="utf-8")
    commit_all(root, "post-attestation change")
    assert eval_runner.main(["--root", str(root), "run", "HUMAN1"]) == 1
    receipt2 = receipt_for(root, "HUMAN1")
    assert receipt2["results"][0]["status"] == "pending"
    assert receipt2["results"][0]["reason"] == "STALE_ATTESTATION"


# ── AT-011: waiver unblocks the gate ─────────────────────────────────────────

def test_at011_waiver(tmp_path):
    root = make_repo(tmp_path)
    install_feature(root, "HUMAN2", CASES_DIR / "define_human.md", CASES_DIR / "design_human.md")
    commit_all(root, "init human2")
    eval_runner.main(["--root", str(root), "freeze", "HUMAN2"])

    assert eval_runner.main(["--root", str(root), "run", "HUMAN2"]) == 1
    assert eval_runner.main([
        "--root", str(root), "waive", "HUMAN2",
        "--eval", "eval_h1", "--supervisor", "Marco", "--reason", "contexto indisponível no momento",
    ]) == 0
    assert eval_runner.main(["--root", str(root), "run", "HUMAN2"]) == 0

    receipt = receipt_for(root, "HUMAN2")
    assert receipt["verdict"] == "PASS"
    assert receipt["waivers"]
    assert receipt["waivers"][0]["eval_id"] == "eval_h1"
    assert receipt["waivers"][0]["supervisor"] == "Marco"
    assert eval_runner.main(["--root", str(root), "verify", "HUMAN2"]) == 0


# ── AT-012: confident, calibrated graded eval decides via Jev ───────────────

def test_at012_graded_confident_calibrated(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    install_feature(root, "GRADED1", CASES_DIR / "define_graded.md", CASES_DIR / "design_graded.md")
    commit_all(root, "init graded1")
    eval_runner.main(["--root", str(root), "freeze", "GRADED1"])

    calibration_dir = root / ".claude" / "sdd" / "evals"
    calibration_dir.mkdir(parents=True)
    (calibration_dir / "JEV_CALIBRATION.json").write_text(json.dumps({
        "approved": True,
        "model": "typesafe/jev-1.13",
        "thresholds": {"noul_pass": 0.85, "noul_fail": 0.15, "score_confidence": 0.75},
    }), encoding="utf-8")
    commit_all(root, "approve calibration")

    pass_payload = json.loads((JEV_DIR / "pass.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(eval_runner.jev_client, "decide", lambda *a, **k: jev_client.parse_response(pass_payload))
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-dummy")

    assert eval_runner.main(["--root", str(root), "run", "GRADED1"]) == 0
    receipt = receipt_for(root, "GRADED1")
    result = receipt["results"][0]
    assert result["status"] == "pass"
    assert result["decided_by"] == "jev"
    assert result["jev"]["role"] == "authoritative"
    assert result["jev"]["answers"]["consistent"]["noul"] == pytest.approx(0.94)
    assert result["jev"]["cost_usd"] == pytest.approx(1.6296e-05)

    ledger = root / ".claude" / "storage" / "judge-ledger.jsonl"
    assert ledger.exists()
    assert len(ledger.read_text(encoding="utf-8").strip().splitlines()) == 1


# ── AT-013: low-confidence graded eval escalates ────────────────────────────

def test_at013_graded_low_confidence(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    install_feature(root, "GRADED2", CASES_DIR / "define_graded.md", CASES_DIR / "design_graded.md")
    commit_all(root, "init graded2")
    eval_runner.main(["--root", str(root), "freeze", "GRADED2"])

    pending_payload = json.loads((JEV_DIR / "pending_ambiguous.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(eval_runner.jev_client, "decide", lambda *a, **k: jev_client.parse_response(pending_payload))
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-dummy")

    monkeypatch.setenv("JUDGE_CMD", write_fake_judge(tmp_path, "fake_judge_pass.py", "PASS", 0))
    assert eval_runner.main(["--root", str(root), "run", "GRADED2"]) == 0
    receipt = receipt_for(root, "GRADED2")
    result = receipt["results"][0]
    assert result["status"] == "pass"
    assert result["decided_by"] == "judge"
    assert result["jev"]["role"] == "advisory"
    assert result["jev"]["decision"] == "escalated"

    monkeypatch.setenv("JUDGE_CMD", write_fake_judge(tmp_path, "fake_judge_fail.py", "FAIL", 1))
    assert eval_runner.main(["--root", str(root), "run", "GRADED2"]) == 1
    receipt2 = receipt_for(root, "GRADED2")
    result2 = receipt2["results"][0]
    assert result2["status"] == "fail"
    assert result2["decided_by"] == "judge"


# ── AT-014: Jev unavailable never produces a PASS ───────────────────────────

def test_at014_jev_unavailable_never_passes(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    install_feature(root, "GRADED3", CASES_DIR / "define_graded.md", CASES_DIR / "design_graded.md")
    commit_all(root, "init graded3")
    eval_runner.main(["--root", str(root), "freeze", "GRADED3"])

    def _raise(*args, **kwargs):
        raise jev_client.JevError("both endpoints down", "UNAVAILABLE")

    monkeypatch.setattr(eval_runner.jev_client, "decide", _raise)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-dummy")
    monkeypatch.setenv("JUDGE_CMD", write_fake_judge(tmp_path, "fake_judge_unavailable.py", "PASS", 4))

    assert eval_runner.main(["--root", str(root), "run", "GRADED3"]) == 1
    receipt = receipt_for(root, "GRADED3")
    result = receipt["results"][0]
    assert result["status"] != "pass"
    assert result["status"] == "pending"
    assert result["jev"]["error"] == "UNAVAILABLE"

    # Budget exhausted: Jev must not even be attempted, and still never PASS.
    monkeypatch.setenv("JEV_BUDGET", "0")
    assert eval_runner.main(["--root", str(root), "run", "GRADED3"]) == 1
    receipt2 = receipt_for(root, "GRADED3")
    result2 = receipt2["results"][0]
    assert result2["status"] != "pass"
    assert result2["jev"]["error"] == "BUDGET"


# ── AT-015: Jev without calibration is advisory only ────────────────────────

def test_at015_uncalibrated(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    install_feature(root, "GRADED4", CASES_DIR / "define_graded.md", CASES_DIR / "design_graded.md")
    commit_all(root, "init graded4")
    eval_runner.main(["--root", str(root), "freeze", "GRADED4"])

    pass_payload = json.loads((JEV_DIR / "pass.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(eval_runner.jev_client, "decide", lambda *a, **k: jev_client.parse_response(pass_payload))
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-dummy")

    # No .claude/sdd/evals/JEV_CALIBRATION.json at all: even a confident
    # "pass" from Jev cannot decide the eval by itself.
    assert eval_runner.main(["--root", str(root), "run", "GRADED4", "--escalate", "human"]) == 1
    receipt = receipt_for(root, "GRADED4")
    result = receipt["results"][0]
    assert result["status"] == "pending"
    assert result["reason"] == "NEEDS_HUMAN"
    assert result["jev"]["role"] == "advisory"
    assert result["jev"]["decision"] == "pass"


# ── AT-016: legacy DESIGN needs a global waiver ─────────────────────────────

def test_at016_legacy(tmp_path, capsys):
    root = make_repo(tmp_path)
    install_feature(root, "LEGACY1", CASES_DIR / "define_legacy.md", CASES_DIR / "design_legacy.md")
    commit_all(root, "init legacy1")

    assert eval_runner.main(["--root", str(root), "verify", "LEGACY1"]) == 1
    assert "LEGACY_NO_EVALS" in capsys.readouterr().out

    assert eval_runner.main([
        "--root", str(root), "waive", "LEGACY1", "--legacy",
        "--supervisor", "Marco", "--reason", "feature legada, anterior ao contrato de evals",
    ]) == 0
    assert eval_runner.main(["--root", str(root), "run", "LEGACY1"]) == 0
    receipt = receipt_for(root, "LEGACY1")
    assert receipt["verdict"] == "PASS"
    assert receipt["legacy_waiver"]["supervisor"] == "Marco"

    capsys.readouterr()
    assert eval_runner.main(["--root", str(root), "verify", "LEGACY1"]) == 0
    assert "OK_LEGACY_WAIVED" in capsys.readouterr().out

    # waive --legacy on a DESIGN that *has* a contract must be rejected.
    setup_basic(root, "BASIC9")
    assert eval_runner.main([
        "--root", str(root), "waive", "BASIC9", "--legacy", "--supervisor", "Marco", "--reason", "x",
    ]) == 2


# ── AT-017: too many graded evals warns but does not block ──────────────────

def test_at017_too_many_graded(tmp_path, capsys):
    root = make_repo(tmp_path)
    install_feature(root, "TMG1", CASES_DIR / "define_too_many_graded.md", CASES_DIR / "design_too_many_graded.md")
    commit_all(root, "init tmg1")

    assert eval_runner.main(["--root", str(root), "validate", "TMG1"]) == 0
    assert "TOO_MANY_GRADED" in capsys.readouterr().out


# ── Retroconversions (DEFINE success criterion: no execution error) ─────────

def test_retro_kb_evolution(tmp_path):
    root = make_repo(tmp_path)
    install_feature(root, "KB_EVOLUTION", KB_DIR / "DEFINE_KB_EVOLUTION.md", KB_DIR / "DESIGN_KB_EVOLUTION.md")

    kb = root / ".claude" / "kb"
    (kb / "medallion").mkdir(parents=True)
    (kb / "medallion" / "ingest.log").write_text(
        "No Context7 coverage for medallion; fallback to manual web search.\n", encoding="utf-8",
    )
    dbt = kb / "dbt"
    dbt.mkdir(parents=True)
    (dbt / "index.md").write_text("# dbt\n", encoding="utf-8")
    (dbt / "quick-reference.md").write_text("# quick reference\n", encoding="utf-8")
    (dbt / "concepts").mkdir()
    (dbt / "patterns").mkdir()
    (dbt / "log.md").write_text("2026-09-23: no changes detected\n", encoding="utf-8")
    (dbt / "LINT_REPORT.md").write_text(
        "# Lint dbt\n\n- stale: `materialized` posicional em stg_orders.sql:42\n", encoding="utf-8",
    )
    (dbt / "deprecated_api_fixture.md").write_text(
        (KB_DIR / "deprecated_api.md").read_text(encoding="utf-8"), encoding="utf-8",
    )
    (kb / "LINT_ALL_REPORT.md").write_text(
        "# Lint Consolidado\n\n## Ranking por severidade\n\n"
        "| Domínio | Issues | Severidade |\n"
        "|---------|--------|------------|\n"
        "| dbt | 1 | alta |\n"
        "| medallion | 0 | — |\n",
        encoding="utf-8",
    )
    commit_all(root, "simulate post-ingest KB state")

    assert eval_runner.main(["--root", str(root), "validate", "KB_EVOLUTION"]) == 0
    assert eval_runner.main(["--root", str(root), "freeze", "KB_EVOLUTION"]) == 0
    eval_runner.main(["--root", str(root), "run", "KB_EVOLUTION"])

    receipt = receipt_for(root, "KB_EVOLUTION")
    assert all(r["status"] != "error" for r in receipt["results"])
    deterministic_ids = {"eval_at002", "eval_at004", "eval_at005", "eval_at006"}
    for r in receipt["results"]:
        if r["eval_id"] in deterministic_ids:
            assert r["status"] == "pass", r


def test_retro_frontend_ecosystem(tmp_path):
    root = make_repo(tmp_path)
    install_feature(root, "FRONTEND_ECOSYSTEM", FE_DIR / "DEFINE_FRONTEND_ECOSYSTEM.md", FE_DIR / "DESIGN_FRONTEND_ECOSYSTEM.md")

    artifacts = root / "artifacts"
    artifacts.mkdir()
    (artifacts / "FILE_MANIFEST.md").write_text(
        "| # | Arquivo | Ação | Agente |\n"
        "|---|---------|------|--------|\n"
        "| 1 | app/page.tsx | Criar | @react-developer |\n"
        "| 2 | app/page.module.css | Criar | @css-specialist |\n",
        encoding="utf-8",
    )
    (artifacts / "build.log").write_text(
        "READ .claude/kb/react/patterns/component-composition.md\n"
        "CONTEXT7 fetch react/server-actions docs\n"
        "USE docs to implement onSubmit action\n"
        "GENERATE app/page.tsx\n",
        encoding="utf-8",
    )
    generated = artifacts / "generated"
    generated.mkdir()
    (generated / "Button.tsx").write_text(
        "export function Button() {\n"
        '  return <button aria-label="Enviar" alt="Enviar formulário">Enviar</button>;\n'
        "}\n",
        encoding="utf-8",
    )
    commit_all(root, "simulate frontend build artifacts")

    assert eval_runner.main(["--root", str(root), "validate", "FRONTEND_ECOSYSTEM"]) == 0
    assert eval_runner.main(["--root", str(root), "freeze", "FRONTEND_ECOSYSTEM"]) == 0
    eval_runner.main(["--root", str(root), "run", "FRONTEND_ECOSYSTEM"])

    receipt = receipt_for(root, "FRONTEND_ECOSYSTEM")
    assert all(r["status"] != "error" for r in receipt["results"])
    deterministic_ids = {"eval_at001", "eval_at003", "eval_at005"}
    for r in receipt["results"]:
        if r["eval_id"] in deterministic_ids:
            assert r["status"] == "pass", r


# ── Calibration ──────────────────────────────────────────────────────────────

def _answer_set(noul: float, score: float, probabilities: dict[str, float], confidence: float) -> dict[str, jev_client.Answer]:
    return {
        "consistent": jev_client.Answer(id="consistent", type="noul", noul=noul),
        "quality": jev_client.Answer(id="quality", type="score", score=score, probabilities=probabilities, confidence=confidence),
    }


PASS_ANSWERS = _answer_set(0.95, 3.0, {"0": 0.0, "1": 0.0, "2": 0.02, "3": 0.98}, 0.95)
FAIL_ANSWERS = _answer_set(0.05, 0.1, {"0": 0.95, "1": 0.03, "2": 0.01, "3": 0.01}, 0.95)
ESCALATED_ANSWERS = _answer_set(0.5, 1.5, {"0": 0.3, "1": 0.3, "2": 0.2, "3": 0.2}, 0.2)

# 12 cases in calibration_cases.toml, in order: case_01..06 expect "pass",
# case_07..10 expect "fail", case_11 expects "fail", case_12 expects "pass".
# This mock decides the first 10 correctly, leaves case_11 undecided
# (escalated, lowers coverage but not agreement) and gets case_12 wrong on
# purpose (lowers agreement) so the arithmetic is genuinely exercised:
# n=12, decided=11, agreed=10 -> coverage=0.917, agreement=0.909 -> approved.
CALIBRATION_PROFILES = ["pass"] * 6 + ["fail"] * 4 + ["escalated", "fail"]


def test_calibrate_approval(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-dummy")

    calls = {"n": 0}

    def fake_decide(state, questions, *, api_key, model=jev_client.DEFAULT_MODEL, **kwargs):
        profile = CALIBRATION_PROFILES[calls["n"]]
        calls["n"] += 1
        answers = {"pass": PASS_ANSWERS, "fail": FAIL_ANSWERS, "escalated": ESCALATED_ANSWERS}[profile]
        return jev_client.DecisionResult(model=model, answers=answers, cost_usd=1.6e-05)

    monkeypatch.setattr(eval_runner.jev_client, "decide", fake_decide)

    cases_path = JEV_DIR / "calibration_cases.toml"
    cases = tomllib.loads(cases_path.read_text(encoding="utf-8"))["case"]
    assert len(cases) == len(CALIBRATION_PROFILES) == 12

    assert eval_runner.main(["--root", str(root), "calibrate", str(cases_path)]) == 0
    calibration = json.loads((root / ".claude" / "sdd" / "evals" / "JEV_CALIBRATION.json").read_text(encoding="utf-8"))
    assert calibration["approved"] is True
    assert calibration["n"] == 12
    assert calibration["coverage"] == pytest.approx(11 / 12, abs=1e-3)
    assert calibration["agreement"] == pytest.approx(10 / 11, abs=1e-3)


# ── Unit tests: classify() against the real Jev fixtures ───────────────────

class TestClassify:
    @staticmethod
    def _answers(fixture_name: str) -> dict[str, jev_client.Answer]:
        payload = json.loads((JEV_DIR / fixture_name).read_text(encoding="utf-8"))
        return jev_client.parse_response(payload).answers

    def test_confident_pass_fixture_passes(self):
        assert eval_runner.classify(self._answers("pass.json"), eval_runner.Thresholds()) == "pass"

    def test_confident_fail_fixture_fails(self):
        assert eval_runner.classify(self._answers("fail_confident.json"), eval_runner.Thresholds()) == "fail"

    def test_contradiction_with_low_confidence_escalates(self):
        # Noul says "contradicts" (0.21) but the Score confidence (0.65) is
        # below the 0.75 floor — the runner refuses to decide alone.
        assert eval_runner.classify(self._answers("fail.json"), eval_runner.Thresholds()) == "escalated"

    def test_pending_ambiguous_case_escalates(self):
        # This is the real 2026-09-23 case that motivated Decision 5: Noul
        # alone (0.70) would have approved a pending AT.
        assert eval_runner.classify(self._answers("pending_ambiguous.json"), eval_runner.Thresholds()) == "escalated"

    def test_no_score_question_never_passes_on_noul_alone(self):
        answers = {"consistent": jev_client.Answer(id="consistent", type="noul", noul=0.99)}
        assert eval_runner.classify(answers, eval_runner.Thresholds()) != "pass"


# ── Unit tests: find_contract() ──────────────────────────────────────────────

class TestFindContract:
    def test_ignores_marker_inside_a_fenced_example(self):
        text = "\n".join([
            "# doc",
            "````markdown",
            "<!-- agentspec:evals:contract -->",
            "```toml",
            "[[eval]]",
            "```",
            "````",
            "",
            "<!-- agentspec:evals:contract -->",
            "```toml",
            "[[eval]]",
            'id = "real"',
            "```",
        ])
        contract = eval_runner.find_contract(text)
        assert contract is not None
        assert 'id = "real"' in contract

    def test_two_real_markers_raise_multiple_contracts(self):
        text = "\n".join([
            "<!-- agentspec:evals:contract -->",
            "```toml",
            "[[eval]]",
            "```",
            "<!-- agentspec:evals:contract -->",
            "```toml",
            "[[eval]]",
            "```",
        ])
        with pytest.raises(eval_runner.RunnerError) as excinfo:
            eval_runner.find_contract(text)
        assert excinfo.value.code == "MULTIPLE_CONTRACTS"

    def test_no_marker_returns_none(self):
        assert eval_runner.find_contract("# just a doc\nno contract here\n") is None

    def test_marker_without_toml_block_raises(self):
        with pytest.raises(eval_runner.RunnerError) as excinfo:
            eval_runner.find_contract("<!-- agentspec:evals:contract -->\nnot a toml block\n")
        assert excinfo.value.code == "CONTRACT_NOT_TOML"

    def test_unterminated_toml_block_raises(self):
        with pytest.raises(eval_runner.RunnerError) as excinfo:
            eval_runner.find_contract("<!-- agentspec:evals:contract -->\n```toml\n[[eval]]\n")
        assert excinfo.value.code == "CONTRACT_UNTERMINATED"


# ── Unit tests: canonical_digest() ───────────────────────────────────────────

class TestCanonicalDigest:
    def test_whitespace_insensitive(self):
        a = tomllib.loads('[[eval]]\nid = "e1"\ncheck_type = "deterministic"\n')
        b = tomllib.loads('[[eval]]\nid    =    "e1"\n\n\ncheck_type = "deterministic"\n')
        assert eval_runner.canonical_digest(a) == eval_runner.canonical_digest(b)

    def test_content_sensitive(self):
        a = tomllib.loads('[[eval]]\nid = "e1"\n')
        b = tomllib.loads('[[eval]]\nid = "e2"\n')
        assert eval_runner.canonical_digest(a) != eval_runner.canonical_digest(b)

    def test_stable_across_repeated_calls(self):
        data = tomllib.loads('[[eval]]\nid = "e1"\nverifies = ["AT-001", "AT-002"]\n')
        assert eval_runner.canonical_digest(data) == eval_runner.canonical_digest(data)

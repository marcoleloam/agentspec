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
    # Deliberately left uncommitted: .claude/sdd/features/ is excluded from the
    # worktree digest (Decision 3), so re-freezing here changes the contract
    # digest without moving HEAD or the worktree digest — isolating
    # STALE_CONTRACT from STALE_COMMIT/STALE_WORKTREE. A re-freeze needs a
    # recorded reason (the /iterate path).
    assert eval_runner.main([
        "--root", str(root), "freeze", "BASIC6",
        "--reason", "descrição do eval_1 revisada via /iterate após review",
    ]) == 0

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


# ═════════════════════════════════════════════════════════════════════════════
# Review fixes (POST_BUILD_EVALS review at b0f7bdd)
# ═════════════════════════════════════════════════════════════════════════════

ARCHIVE = Path(__file__).resolve().parent.parent / ".claude" / "sdd" / "archive"
REASON = "eval_1 afrouxado após review com o time de dados"


def run_cli(root: Path, *args: str) -> int:
    return eval_runner.main(["--root", str(root), *args])


def verify_json(root: Path, name: str, capsys, *extra: str) -> dict:
    capsys.readouterr()
    run_cli(root, "verify", name, "--json", *extra)
    return json.loads(capsys.readouterr().out)


def design_path(root: Path, name: str) -> Path:
    return root / ".claude" / "sdd" / "features" / f"DESIGN_{name}.md"


def edit_design(root: Path, name: str, old: str, new: str) -> None:
    path = design_path(root, name)
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def loosen_eval_1(root: Path, name: str) -> None:
    edit_design(root, name, 'grep -qx "hello agentspec" greeting.txt || { echo "content mismatch" >&2; exit 1; }',
                "true  # loosened")


def freeze_log(root: Path, name: str) -> list[dict]:
    path = root / ".claude" / "sdd" / "features" / f"EVAL_{name}.freeze.log"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def reports_dir(root: Path) -> Path:
    return root / ".claude" / "sdd" / "reports"


def write_receipt(root: Path, name: str, receipt: dict, *, seal: bool) -> None:
    receipt = dict(receipt)
    receipt.pop("integrity", None)
    if seal:
        receipt["integrity"] = {"algorithm": eval_runner.INTEGRITY_ALGORITHM, "digest": eval_runner.integrity_digest(receipt)}
    (reports_dir(root) / f"EVAL_{name}.json").write_text(json.dumps(receipt), encoding="utf-8")


# ── Finding 1: re-freeze needs a reason and lands in an append-only ledger ──

def test_refreeze_refused_without_reason(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "REFREEZE1")
    assert run_cli(root, "freeze", "REFREEZE1") == 0
    frozen = eval_runner.read_frozen_digest(design_path(root, "REFREEZE1").read_text(encoding="utf-8"))

    loosen_eval_1(root, "REFREEZE1")
    capsys.readouterr()
    assert run_cli(root, "freeze", "REFREEZE1") == 1
    assert "REFREEZE_NEEDS_REASON" in capsys.readouterr().out
    assert run_cli(root, "freeze", "REFREEZE1", "--reason", "too short") == 1
    # Refused freezes change nothing: the DESIGN keeps its digest, so run refuses.
    assert eval_runner.read_frozen_digest(design_path(root, "REFREEZE1").read_text(encoding="utf-8")) == frozen
    assert len(freeze_log(root, "REFREEZE1")) == 1
    assert run_cli(root, "run", "REFREEZE1") == 1
    assert any(e.startswith("CONTRACT_TAMPERED") for e in receipt_for(root, "REFREEZE1")["structural_errors"])

    assert run_cli(root, "freeze", "REFREEZE1", "--reason", REASON) == 0
    log = freeze_log(root, "REFREEZE1")
    assert [e["kind"] for e in log] == ["initial", "refreeze"]
    assert log[1]["old_digest"] == frozen and log[1]["reason"] == REASON
    assert log[1]["git_user_email"] == "test@example.com"
    assert log[1]["prev"] == eval_runner.canonical_digest(log[0])

    # The loosened contract can pass, but the re-freeze is on the record.
    assert run_cli(root, "run", "REFREEZE1") == 0
    receipt = receipt_for(root, "REFREEZE1")
    assert any(w.startswith("REFROZEN") and REASON in w for w in receipt["warnings"])
    assert "REFROZEN" in report_for(root, "REFREEZE1")
    assert receipt["freeze_ledger"]["entries"] == 2


def test_idempotent_freeze_writes_nothing(tmp_path):
    root = make_repo(tmp_path)
    setup_basic(root, "REFREEZE2")
    assert run_cli(root, "freeze", "REFREEZE2") == 0
    assert run_cli(root, "freeze", "REFREEZE2") == 0
    assert len(freeze_log(root, "REFREEZE2")) == 1


def test_refrozen_after_run(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "REFREEZE3")
    run_cli(root, "freeze", "REFREEZE3")
    assert run_cli(root, "run", "REFREEZE3") == 0
    original = design_path(root, "REFREEZE3").read_text(encoding="utf-8")

    # A → B → A after the run: the contract digest is back where it was, but
    # the ledger shows two freezes the receipt never saw.
    loosen_eval_1(root, "REFREEZE3")
    assert run_cli(root, "freeze", "REFREEZE3", "--reason", REASON) == 0
    assert verify_json(root, "REFREEZE3", capsys)["code"] == "STALE_CONTRACT"
    design_path(root, "REFREEZE3").write_text(original, encoding="utf-8")
    assert run_cli(root, "freeze", "REFREEZE3", "--reason", "revertido: o afrouxamento não foi aprovado") == 0
    assert verify_json(root, "REFREEZE3", capsys)["code"] == "REFROZEN_AFTER_RUN"

    assert run_cli(root, "run", "REFREEZE3") == 0
    assert verify_json(root, "REFREEZE3", capsys)["code"] == "OK"


def test_ledger_mismatch_on_hand_edited_digest(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "LEDGER1")
    run_cli(root, "freeze", "LEDGER1")
    run_cli(root, "run", "LEDGER1")

    # Bypass `freeze`: loosen the eval and write the matching digest by hand.
    loosen_eval_1(root, "LEDGER1")
    feature = eval_runner.load_feature(eval_runner.Paths(root, "LEDGER1"))
    design_path(root, "LEDGER1").write_text(
        eval_runner.write_frozen_digest(feature.design_text, feature.contract_digest), encoding="utf-8")

    out = verify_json(root, "LEDGER1", capsys)
    assert out["code"] == "LEDGER_MISMATCH"
    assert run_cli(root, "run", "LEDGER1") == 1
    assert any(e.startswith("LEDGER_MISMATCH") for e in receipt_for(root, "LEDGER1")["structural_errors"])


def test_freeze_log_chain_broken(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "LEDGER2")
    run_cli(root, "freeze", "LEDGER2")
    loosen_eval_1(root, "LEDGER2")
    run_cli(root, "freeze", "LEDGER2", "--reason", REASON)
    run_cli(root, "run", "LEDGER2")

    log_path = root / ".claude" / "sdd" / "features" / "EVAL_LEDGER2.freeze.log"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    log_path.write_text(lines[1] + "\n", encoding="utf-8")  # drop the initial freeze
    assert verify_json(root, "LEDGER2", capsys)["code"] == "FREEZE_LOG_BROKEN"
    capsys.readouterr()
    assert run_cli(root, "freeze", "LEDGER2", "--reason", REASON) == 1

    log_path.write_text("not json\n", encoding="utf-8")
    assert verify_json(root, "LEDGER2", capsys)["code"] == "FREEZE_LOG_BROKEN"


# ── Finding 2: verify recomputes the verdict; receipts are sealed ───────────

def test_forged_receipt_with_empty_results_rejected(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "FORGE1", satisfy_all=False)
    run_cli(root, "freeze", "FORGE1")
    feature = eval_runner.load_feature(eval_runner.Paths(root, "FORGE1"))
    state = eval_runner.repo_state(feature)
    forged = {
        "schema": eval_runner.RECEIPT_SCHEMA, "feature": "FORGE1", **state.to_dict(),
        "extras_digest": None, "evaluated_at": "2026-09-28T00:00:00Z", "runner_version": "1.0.0",
        "jev": {"model": "x", "calibrated": False}, "results": [], "required": [],
        "structural_errors": [], "warnings": [], "waivers": [], "verdict": "PASS",
    }
    reports_dir(root).mkdir(parents=True, exist_ok=True)

    write_receipt(root, "FORGE1", forged, seal=False)
    assert verify_json(root, "FORGE1", capsys)["code"] == "UNSEALED_RECEIPT"

    forged["freeze_ledger"] = eval_runner.freeze_fingerprint(freeze_log(root, "FORGE1"))
    write_receipt(root, "FORGE1", forged, seal=True)
    out = verify_json(root, "FORGE1", capsys)
    assert out["code"] == "RECEIPT_INCOMPLETE"
    assert run_cli(root, "verify", "FORGE1") == 1


def test_edited_verdict_breaks_the_seal(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "FORGE2", satisfy_all=False)
    run_cli(root, "freeze", "FORGE2")
    assert run_cli(root, "run", "FORGE2") == 1
    receipt = receipt_for(root, "FORGE2")

    receipt["verdict"] = "PASS"
    (reports_dir(root) / "EVAL_FORGE2.json").write_text(json.dumps(receipt), encoding="utf-8")
    assert verify_json(root, "FORGE2", capsys)["code"] == "INTEGRITY_MISMATCH"

    # Re-sealing does not help: the results still show failures.
    write_receipt(root, "FORGE2", receipt, seal=True)
    assert verify_json(root, "FORGE2", capsys)["code"] == "VERDICT_MISMATCH"

    # Flipping the statuses too is caught by the deterministic exit codes.
    for r in receipt["results"]:
        r["status"] = "pass"
    write_receipt(root, "FORGE2", receipt, seal=True)
    assert verify_json(root, "FORGE2", capsys)["code"] == "VERDICT_MISMATCH"

    # A forger who also fakes exit codes is caught only by --rerun.
    for r in receipt["results"]:
        r["exit_code"] = 0
    write_receipt(root, "FORGE2", receipt, seal=True)
    assert verify_json(root, "FORGE2", capsys)["code"] == "OK"
    out = verify_json(root, "FORGE2", capsys, "--rerun")
    assert out["code"] == "RERUN_FAIL"
    assert "eval_1" in out["detail"]


def test_forged_human_pass_is_unbacked(tmp_path, capsys):
    root = make_repo(tmp_path)
    install_feature(root, "FORGE3", CASES_DIR / "define_human.md", CASES_DIR / "design_human.md")
    commit_all(root, "init forge3")
    run_cli(root, "freeze", "FORGE3")
    assert run_cli(root, "run", "FORGE3") == 1
    receipt = receipt_for(root, "FORGE3")
    receipt["results"][0].update({"status": "pass", "decided_by": "human", "human": {"owner": "Marco"}})
    receipt["results"][0].pop("reason", None)
    receipt["verdict"] = "PASS"
    write_receipt(root, "FORGE3", receipt, seal=True)
    assert verify_json(root, "FORGE3", capsys)["code"] == "UNBACKED_DECISION"


def test_verify_rerun_sees_gitignored_inputs(tmp_path, capsys):
    """Gitignored files are outside the worktree digest (documented): a change
    to one is invisible to plain verify, and caught by verify --rerun."""
    root = make_repo(tmp_path)
    (root / ".gitignore").write_text("greeting.txt\n", encoding="utf-8")
    setup_basic(root, "RERUN1")
    run_cli(root, "freeze", "RERUN1")
    assert run_cli(root, "run", "RERUN1") == 0
    (root / "greeting.txt").write_text("changed\n", encoding="utf-8")
    assert verify_json(root, "RERUN1", capsys)["code"] == "OK"
    assert verify_json(root, "RERUN1", capsys, "--rerun")["code"] == "RERUN_FAIL"


# ── Finding 3: an empty or partial [gate] required is rejected ──────────────

def _with_gate(root: Path, name: str, required: str) -> None:
    edit_design(root, name, "```toml\n", f"```toml\n[gate]\nrequired = {required}\n\n")


def test_empty_required_rejected(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "GATE1", satisfy_all=False)
    _with_gate(root, "GATE1", "[]")
    assert run_cli(root, "validate", "GATE1") == 3
    assert "EMPTY_REQUIRED" in capsys.readouterr().out
    assert run_cli(root, "freeze", "GATE1") == 3


def test_required_must_cover_every_at(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "GATE2")
    _with_gate(root, "GATE2", '["eval_1"]')
    assert run_cli(root, "validate", "GATE2") == 3
    out = capsys.readouterr().out
    assert "UNGATED_AT: AT-002" in out and "UNGATED_AT: AT-003" in out

    edit_design(root, "GATE2", 'required = ["eval_1"]', 'required = ["eval_1", "eval_2", "eval_3"]')
    assert run_cli(root, "validate", "GATE2") == 0


# ── Finding 4: worktree digest covers templates/architecture, not workflow state ──

def test_worktree_digest_scope(tmp_path):
    root = make_repo(tmp_path)
    sdd = root / ".claude" / "sdd"
    for sub in ("templates", "architecture", "features", "reports", "archive"):
        (sdd / sub).mkdir(parents=True)
        (sdd / sub / "file.md").write_text("v1\n", encoding="utf-8")
    (root / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    commit_all(root, "sdd tree")
    base = eval_runner.worktree_digest(root)

    for sub in ("features", "reports", "archive"):
        (sdd / sub / "file.md").write_text("v2\n", encoding="utf-8")
        (sdd / sub / "new.md").write_text("new\n", encoding="utf-8")
    (sdd / "MEMORY.md").write_text("memory\n", encoding="utf-8")
    (root / ".claude" / "storage").mkdir(parents=True)
    (root / ".claude" / "storage" / "judge-ledger.jsonl").write_text("{}\n", encoding="utf-8")
    (root / "ignored.txt").write_text("gitignored\n", encoding="utf-8")
    assert eval_runner.worktree_digest(root) == base

    for sub in ("templates", "architecture"):
        (sdd / sub / "file.md").write_text("v2\n", encoding="utf-8")
        changed = eval_runner.worktree_digest(root)
        assert changed != base, sub
        (sdd / sub / "file.md").write_text("v1\n", encoding="utf-8")
    (sdd / "templates" / "NEW_TEMPLATE.md").write_text("untracked\n", encoding="utf-8")
    assert eval_runner.worktree_digest(root) != base


# ── Finding 5: waivers and attestations name a person ───────────────────────

@pytest.mark.parametrize("who", ["build-agent", "eval-agent", "Codex", "Claude", "claude code", "GPT-5", "my-agent", "  "])
def test_waiver_refuses_agent_supervisor(tmp_path, who):
    root = make_repo(tmp_path)
    setup_basic(root, "WAIVE1", satisfy_all=False)
    run_cli(root, "freeze", "WAIVE1")
    assert run_cli(root, "waive", "WAIVE1", "--eval", "eval_1", "--supervisor", who,
                   "--reason", "o arquivo é gerado só no ambiente de produção") == 2


def test_deterministic_waiver_needs_reason_and_records_email(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "WAIVE2", satisfy_all=False)
    (root / "config.json").write_text(json.dumps({"ready": True}), encoding="utf-8")
    (root / "greet.sh").write_text("echo hi\n", encoding="utf-8")
    commit_all(root, "partial")
    run_cli(root, "freeze", "WAIVE2")
    assert run_cli(root, "waive", "WAIVE2", "--eval", "eval_1", "--supervisor", "Marco", "--reason", "ok") == 2
    assert "REASON_TOO_SHORT" in capsys.readouterr().err

    assert run_cli(root, "waive", "WAIVE2", "--eval", "eval_1", "--supervisor", "Marco Monteiro",
                   "--reason", "greeting.txt é gerado pelo deploy, não pelo build") == 0
    ledger = json.loads((reports_dir(root) / "EVAL_WAIVE2.attestations.json").read_text(encoding="utf-8"))
    assert ledger["waivers"][0]["recorded_by_email"] == "test@example.com"
    assert run_cli(root, "run", "WAIVE2") == 0
    receipt = receipt_for(root, "WAIVE2")
    assert receipt["waivers"][0]["recorded_by_email"] == "test@example.com"
    assert "test@example.com" in report_for(root, "WAIVE2")
    assert verify_json(root, "WAIVE2", capsys)["code"] == "OK"


def test_attest_refuses_agent_owner(tmp_path):
    root = make_repo(tmp_path)
    install_feature(root, "ATTEST1", CASES_DIR / "define_human.md", CASES_DIR / "design_human.md")
    commit_all(root, "init attest1")
    run_cli(root, "freeze", "ATTEST1")
    assert run_cli(root, "attest", "ATTEST1", "--eval", "eval_h1", "--verdict", "pass",
                   "--owner", "eval-agent", "--evidence", "x") == 2


def test_legacy_waiver_needs_a_meaningful_reason(tmp_path):
    root = make_repo(tmp_path)
    install_feature(root, "LEGACY2", CASES_DIR / "define_legacy.md", CASES_DIR / "design_legacy.md")
    commit_all(root, "init legacy2")
    assert run_cli(root, "waive", "LEGACY2", "--legacy", "--supervisor", "Marco", "--reason", "legado") == 2


# ── Finding 6: the PRE receipt is persisted and surfaced by run ─────────────

def test_pre_receipt_persisted_and_reported(tmp_path):
    root = make_repo(tmp_path)
    setup_basic(root, "PRE1")
    run_cli(root, "freeze", "PRE1")
    assert run_cli(root, "run", "PRE1") == 0
    receipt = receipt_for(root, "PRE1")
    assert receipt["pre_check"] == {"present": False}
    assert any(w.startswith("NO_PRE_RECEIPT") for w in receipt["warnings"])
    assert "NO_PRE_RECEIPT" in report_for(root, "PRE1")

    assert run_cli(root, "pre", "PRE1") == 0
    pre = json.loads((reports_dir(root) / "EVAL_PRE1.pre.json").read_text(encoding="utf-8"))
    assert pre["schema"] == eval_runner.PRE_SCHEMA and pre["outcome"] == "OK"
    assert sorted(pre["already_passing"]) == ["eval_1", "eval_2", "eval_3"]
    assert run_cli(root, "run", "PRE1") == 0
    receipt = receipt_for(root, "PRE1")
    assert receipt["pre_check"]["present"] is True
    assert not any(w.startswith("NO_PRE_RECEIPT") for w in receipt["warnings"])
    assert any(w.startswith("PRE_ALREADY_PASSING") for w in receipt["warnings"])


def test_pre_receipt_records_blocked(tmp_path):
    root = make_repo(tmp_path)
    install_feature(root, "PRE2", CASES_DIR / "define_bash_error.md", CASES_DIR / "design_bash_error.md")
    commit_all(root, "init pre2")
    run_cli(root, "freeze", "PRE2")
    assert run_cli(root, "pre", "PRE2") == 1
    pre = json.loads((reports_dir(root) / "EVAL_PRE2.pre.json").read_text(encoding="utf-8"))
    assert pre["outcome"] == "BLOCKED"


# ── Finding 7: the eval phase adds complementary evals through the runner ───

def test_extra_appends_validated_evals(tmp_path, capsys):
    root = make_repo(tmp_path)
    setup_basic(root, "EXTRA1")
    run_cli(root, "freeze", "EXTRA1")
    good = tmp_path / "extra.toml"
    good.write_text('[[eval]]\nid = "extra_a"\nverifies = ["AT-001"]\ncheck_type = "deterministic"\nrun = "true"\n', encoding="utf-8")
    assert run_cli(root, "extra", "EXTRA1", "--file", str(good)) == 0
    good.write_text('[[eval]]\nid = "extra_b"\ncheck_type = "deterministic"\nrun = "true"\n', encoding="utf-8")
    assert run_cli(root, "extra", "EXTRA1", "--file", str(good)) == 0
    extras = tomllib.loads((root / ".claude" / "sdd" / "features" / "EVALS_EXTRA_EXTRA1.toml").read_text(encoding="utf-8"))
    assert [e["id"] for e in extras["eval"]] == ["extra_a", "extra_b"]

    for bad in (
        '[[eval]]\nid = "extra_a"\ncheck_type = "deterministic"\nrun = "true"\n',          # duplicate id
        '[[eval]]\nid = "eval_1"\ncheck_type = "deterministic"\nrun = "true"\n',           # collides with contract
        '[[eval]]\nid = "extra_h"\ncheck_type = "human"\nowner = "x"\ninstructions = "y"\n',  # human not allowed
        '[gate]\nrequired = []\n',                                                         # cannot touch the gate
    ):
        good.write_text(bad, encoding="utf-8")
        assert run_cli(root, "extra", "EXTRA1", "--file", str(good)) == 3, bad
    assert run_cli(root, "run", "EXTRA1") == 0
    assert {"extra_a", "extra_b"} <= set(receipt_for(root, "EXTRA1")["required"])


def test_eval_agent_has_no_write_tool():
    agent = (Path(__file__).resolve().parent.parent / ".claude" / "agents" / "workflow" / "eval-agent.md").read_text(encoding="utf-8")
    tools_line = next(line for line in agent.splitlines() if line.startswith("tools:"))
    assert "Write" not in tools_line.replace("TodoWrite", "")
    assert "Edit" not in tools_line


# ── Finding 8 (runner side): a malformed Jev answer never crashes /eval ─────

def test_graded_malformed_jev_answer_escalates(tmp_path, monkeypatch):
    root = make_repo(tmp_path)
    install_feature(root, "GRADED5", CASES_DIR / "define_graded.md", CASES_DIR / "design_graded.md")
    commit_all(root, "init graded5")
    run_cli(root, "freeze", "GRADED5")
    bad = {"quality": jev_client.Answer(id="quality", type="score", probabilities={"top": 0.9}, confidence=0.99)}
    monkeypatch.setattr(eval_runner.jev_client, "decide", lambda *a, **k: jev_client.DecisionResult(model="m", answers=bad))
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-dummy")
    assert run_cli(root, "run", "GRADED5", "--escalate", "human") == 1
    result = receipt_for(root, "GRADED5")["results"][0]
    assert result["status"] == "pending"
    assert result["jev"]["error"] == "PARSE"


# ── Backward compatibility: receipts written by runner 1.0.0 ────────────────

def test_legacy_receipt_still_verifies(tmp_path, capsys):
    """A receipt from runner 1.0.0 (no seal, no freeze ledger) keeps verifying,
    under an explicit code, as long as the DESIGN has no freeze ledger."""
    root = make_repo(tmp_path)
    setup_basic(root, "OLD1")
    run_cli(root, "freeze", "OLD1")
    run_cli(root, "run", "OLD1")
    receipt = receipt_for(root, "OLD1")
    for key in ("integrity", "freeze_ledger", "pre_check"):
        receipt.pop(key)
    receipt["runner_version"] = "1.0.0"
    receipt["warnings"] = []
    write_receipt(root, "OLD1", receipt, seal=False)
    log_path = root / ".claude" / "sdd" / "features" / "EVAL_OLD1.freeze.log"
    log_text = log_path.read_text(encoding="utf-8")

    log_path.unlink()
    out = verify_json(root, "OLD1", capsys)
    assert out["code"] == "OK_LEGACY_RECEIPT"
    assert run_cli(root, "verify", "OLD1") == 0

    # Once a freeze ledger exists, only sealed receipts count.
    log_path.write_text(log_text, encoding="utf-8")
    assert verify_json(root, "OLD1", capsys)["code"] == "UNSEALED_RECEIPT"


def test_legacy_waived_receipt_still_verifies(tmp_path, capsys):
    root = make_repo(tmp_path)
    install_feature(root, "LEGACY3", CASES_DIR / "define_legacy.md", CASES_DIR / "design_legacy.md")
    commit_all(root, "init legacy3")
    run_cli(root, "waive", "LEGACY3", "--legacy", "--supervisor", "Marco", "--reason", "feature legada, anterior ao contrato de evals")
    run_cli(root, "run", "LEGACY3")
    receipt = receipt_for(root, "LEGACY3")
    receipt.pop("integrity")
    write_receipt(root, "LEGACY3", receipt, seal=False)
    assert verify_json(root, "LEGACY3", capsys)["code"] == "OK_LEGACY_WAIVED"
    (reports_dir(root) / "EVAL_LEGACY3.attestations.json").unlink()
    assert verify_json(root, "LEGACY3", capsys)["code"] == "UNBACKED_DECISION"


ARCHIVED_RECEIPTS = sorted(ARCHIVE.glob("*/EVAL_*[A-Z0-9].json"))


@pytest.mark.parametrize("receipt_path", ARCHIVED_RECEIPTS, ids=lambda p: p.parent.name)
def test_archived_receipts_remain_consistent(tmp_path, receipt_path):
    """Every receipt already shipped still passes the new recomputation:
    its results satisfy the gate of its own archived DESIGN, and every human
    pass / waiver is backed by its archived attestations file."""
    name = receipt_path.parent.name
    root = make_repo(tmp_path)
    install_feature(root, name, receipt_path.parent / f"DEFINE_{name}.md", receipt_path.parent / f"DESIGN_{name}.md")
    reports_dir(root).mkdir(parents=True)
    for suffix in (".json", ".attestations.json"):
        src = receipt_path.parent / f"EVAL_{name}{suffix}"
        if src.exists():
            (reports_dir(root) / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    paths = eval_runner.Paths(root, name)
    feature = eval_runner.load_feature(paths)
    receipt, readable = eval_runner.load_receipt(paths)
    assert readable and receipt is not None
    assert eval_runner.seal_code(receipt, []) == "LEGACY"
    assert receipt.get("contract_digest") == feature.contract_digest
    assert eval_runner.receipt_consistency(feature, receipt, eval_runner.load_attestations(paths)) is None


def test_archive_has_receipts():
    assert len(ARCHIVED_RECEIPTS) >= 5

"""Tests for plugin-extras/scripts/memory-hook.py (Living Memory Claude Code hooks)."""
from __future__ import annotations

import io
import json
import shutil
from pathlib import Path

import pytest

from tests.test_memory_index import FIX, OFF_TEMPLATE, _load, write_raw_blackboard

REPO = Path(__file__).resolve().parent.parent
hook = _load("memory_hook", REPO / "plugin-extras" / "scripts" / "memory-hook.py")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A project dir whose .claude/sdd is a copy of the fixture tree."""
    shutil.copytree(FIX.parent, tmp_path / ".claude")
    return tmp_path


def fire(monkeypatch, capsys, mode: str, event: dict) -> tuple[int, str, str]:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(event)))
    code = hook.main([mode])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def sdd(project: Path) -> Path:
    return project / ".claude" / "sdd"


# --- prompt: brief injection ----------------------------------------------------

@pytest.mark.parametrize("prompt", [
    "/agentspec:workflow:design .claude/sdd/features/DEFINE_BLOCKED.md",
    "/design BLOCKED",
    "/workflow:design-m .claude/sdd/features/DEFINE_BLOCKED.md --judge",
])
def test_prompt_injects_brief_for_phase_command(project, monkeypatch, capsys, prompt):
    code, out, _ = fire(monkeypatch, capsys, "prompt", {"prompt": prompt, "cwd": str(project)})
    assert code == 0
    assert "Memória de BLOCKED — entrando em design" in out
    assert "Q-003" in out


@pytest.mark.parametrize("prompt", [
    "/continuar BLOCKED", "/agentspec:workflow:continue BLOCKED",
    "/agentspec:source-command-workflow-design BLOCKED", "/source-command-workflow-design-m blocked",
    "/design blocked", "/define .claude/sdd/features/BRAINSTORM_blocked.md",
])
def test_prompt_recognises_every_invocation_form(project, monkeypatch, capsys, prompt):
    code, out, _ = fire(monkeypatch, capsys, "prompt", {"prompt": prompt, "cwd": str(project)})
    assert code == 0
    assert "Memória de BLOCKED" in out and "Q-003" in out


@pytest.mark.parametrize("prompt", ["/build", "/continuar", "/agentspec:workflow:continue",
                                    "/agentspec:source-command-workflow-build"])
def test_prompt_without_feature_uses_active_for_build(project, monkeypatch, capsys, prompt):
    """/build and /continuar act on .claude/sdd/.active (written by /work and /build)."""
    code, out, _ = fire(monkeypatch, capsys, "prompt", {"prompt": prompt, "cwd": str(project)})
    assert code == 0
    assert "Memória de DEMO — entrando em build" in out


def test_prompt_from_a_subdirectory_finds_the_project(project, monkeypatch, capsys):
    sub = project / "src" / "pkg"
    sub.mkdir(parents=True)
    code, out, _ = fire(monkeypatch, capsys, "prompt", {"prompt": "/design BLOCKED", "cwd": str(sub)})
    assert code == 0 and "Q-003" in out


@pytest.mark.parametrize("prompt", ["/design add a login page", "/other:design BLOCKED",
                                    "/brainstorm uma ideia qualquer"])
def test_prompt_ignores_prose_and_foreign_namespaces(project, monkeypatch, capsys, prompt):
    code, out, _ = fire(monkeypatch, capsys, "prompt", {"prompt": prompt, "cwd": str(project)})
    assert code == 0 and out == ""


@pytest.mark.parametrize("prompt", ["explain the design", "/status", "/design", "/review BLOCKED"])
def test_prompt_ignores_non_phase_or_featureless_prompts(project, monkeypatch, capsys, prompt):
    code, out, _ = fire(monkeypatch, capsys, "prompt", {"prompt": prompt, "cwd": str(project)})
    assert code == 0 and out == ""


def test_prompt_stays_quiet_without_memory(project, monkeypatch, capsys):
    code, out, _ = fire(monkeypatch, capsys, "prompt",
                        {"prompt": "/brainstorm BRAND_NEW — idea", "cwd": str(project)})
    assert code == 0 and out == ""


# --- pre-write: design gate -------------------------------------------------------

def design_event(project: Path, feature: str) -> dict:
    return {"cwd": str(project), "tool_name": "Write",
            "tool_input": {"file_path": str(sdd(project) / "features" / f"DESIGN_{feature}.md")}}


def test_pre_write_blocks_new_design_on_open_question(project, monkeypatch, capsys):
    """AT-005, enforced by the hook instead of the prompt."""
    code, _, err = fire(monkeypatch, capsys, "pre-write", design_event(project, "BLOCKED"))
    assert code == 2
    assert "Q-003" in err and "DESIGN not written" in err


def test_pre_write_blocks_new_design_on_unreadable_blackboard(project, monkeypatch, capsys):
    write_raw_blackboard(sdd(project), "OFFTPL", OFF_TEMPLATE)
    code, _, err = fire(monkeypatch, capsys, "pre-write", design_event(project, "OFFTPL"))
    assert code == 2 and "ilegíve" in err


def test_pre_write_allows_clean_feature(project, monkeypatch, capsys):
    code, _, err = fire(monkeypatch, capsys, "pre-write", design_event(project, "DEMO"))
    assert code == 0 and err == ""


def test_pre_write_leaves_existing_design_alone(project, monkeypatch, capsys):
    """Editing an existing DESIGN (e.g. /iterate) is how a 🔴 gets resolved — not blocked."""
    event = design_event(project, "BLOCKED")
    Path(event["tool_input"]["file_path"]).write_text("# DESIGN\n", encoding="utf-8")
    code, _, _ = fire(monkeypatch, capsys, "pre-write", event)
    assert code == 0


def test_pre_write_gates_from_a_subdirectory_cwd(project, monkeypatch, capsys):
    """The root comes from the file being written, not from the session cwd."""
    sub = project / "src"
    sub.mkdir()
    event = {**design_event(project, "BLOCKED"), "cwd": str(sub)}
    code, _, err = fire(monkeypatch, capsys, "pre-write", event)
    assert code == 2 and "Q-003" in err


def test_pre_write_gates_with_unrelated_cwd(project, tmp_path, monkeypatch, capsys):
    event = {**design_event(project, "BLOCKED"), "cwd": str(tmp_path / "elsewhere")}
    code, _, err = fire(monkeypatch, capsys, "pre-write", event)
    assert code == 2 and "Q-003" in err


def test_pre_write_ignores_other_files(project, monkeypatch, capsys):
    event = {"cwd": str(project), "tool_input": {"file_path": str(project / "src" / "DESIGN_X.md")}}
    code, _, _ = fire(monkeypatch, capsys, "pre-write", event)
    assert code == 0


# --- post-write: index rebuild ------------------------------------------------------

def blackboard_event(project: Path, feature: str) -> dict:
    return {"cwd": str(project), "tool_name": "Edit",
            "tool_input": {"file_path": str(sdd(project) / "features" / f"BLACKBOARD_{feature}.md")}}


def test_post_write_rebuilds_index(project, monkeypatch, capsys):
    code, _, err = fire(monkeypatch, capsys, "post-write", blackboard_event(project, "DEMO"))
    assert code == 0 and err == ""
    assert "| DEMO |" in (sdd(project) / "MEMORY_INDEX.md").read_text(encoding="utf-8")


def test_post_write_feeds_unreadable_rows_back(project, monkeypatch, capsys):
    write_raw_blackboard(sdd(project), "OFFTPL", OFF_TEMPLATE)
    code, _, err = fire(monkeypatch, capsys, "post-write", blackboard_event(project, "OFFTPL"))
    assert code == 2
    assert "OFFTPL" in err and "fix them now" in err


def test_post_write_rebuilds_the_files_project_not_the_cwd(project, tmp_path, monkeypatch, capsys):
    event = {**blackboard_event(project, "DEMO"), "cwd": str(tmp_path / "elsewhere")}
    code, _, _ = fire(monkeypatch, capsys, "post-write", event)
    assert code == 0 and (sdd(project) / "MEMORY_INDEX.md").is_file()


def test_post_write_ignores_non_blackboard(project, monkeypatch, capsys):
    event = {"cwd": str(project), "tool_input": {"file_path": str(project / "README.md")}}
    code, _, _ = fire(monkeypatch, capsys, "post-write", event)
    assert code == 0
    assert not (sdd(project) / "MEMORY_INDEX.md").exists()


# --- never break the session --------------------------------------------------------

def test_project_without_sdd_is_a_no_op(tmp_path, monkeypatch, capsys):
    code, out, err = fire(monkeypatch, capsys, "prompt", {"prompt": "/design X_Y", "cwd": str(tmp_path)})
    assert (code, out, err) == (0, "", "")


def test_garbage_stdin_is_a_no_op(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert hook.main(["post-write"]) == 0


@pytest.mark.parametrize("mode", ["prompt", "pre-write", "post-write"])
def test_internal_error_is_silent_exit_0(project, monkeypatch, capsys, mode):
    """Any exception inside a handler → exit 0 and no output at all."""
    def boom(*_a, **_k):
        raise RuntimeError("boom")
    monkeypatch.setattr(hook, "load_index", boom)
    events = {"prompt": {"prompt": "/design BLOCKED", "cwd": str(project)},
              "pre-write": design_event(project, "BLOCKED"),
              "post-write": blackboard_event(project, "DEMO")}
    assert fire(monkeypatch, capsys, mode, events[mode]) == (0, "", "")


def test_hooks_json_wires_every_mode():
    config = json.loads((REPO / "plugin-extras" / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    commands = [h["command"] for groups in config["hooks"].values() for g in groups for h in g["hooks"]]
    for mode in ("prompt", "pre-write", "post-write"):
        assert any(f"memory-hook.py\" {mode}" in c for c in commands)

"""The agent selection rubric is shared by the phase commands and the LLM baseline.

What gets measured (scripts/eval_llm_baseline.py) must be what the commands apply,
and what the plugin ships must be what the repo holds.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUBRIC = REPO_ROOT / ".claude" / "sdd" / "architecture" / "AGENT_SELECTION_RUBRIC.md"
COMMANDS = ["define", "design", "define-m", "design-m"]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_rubric_mod", REPO_ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _block(text: str) -> str:
    start, end = text.index("<!-- rubric:start -->\n"), text.index("\n<!-- rubric:end -->")
    return text[start:end]


def test_rubric_block_is_what_the_baseline_measures():
    baseline = _load("eval_llm_baseline")
    rubric = baseline.load_rubric()
    assert rubric.startswith("VARIANT — pick exactly one:")
    assert "SPECIALISTS — list up to 4 agent names" in rubric
    assert rubric in baseline.build_prompt({"phase": "design", "summary": "s"}, [])


def test_rubric_limit_matches_selector():
    assert _load("jev_select").MAX_SPECIALISTS == 4


@pytest.mark.parametrize("command", COMMANDS)
def test_phase_commands_apply_the_rubric(command):
    text = (REPO_ROOT / ".claude" / "commands" / "workflow" / f"{command}.md").read_text()
    assert "AGENT_SELECTION_RUBRIC.md" in text
    assert "JEV_SECOND_OPINION" in text


def test_plugin_ships_the_same_rubric_block():
    shipped = REPO_ROOT / "plugin" / "sdd" / "architecture" / "AGENT_SELECTION_RUBRIC.md"
    if not (REPO_ROOT / "plugin").is_dir():
        pytest.skip("plugin/ not built")
    assert shipped.is_file(), "plugin/sdd/architecture/AGENT_SELECTION_RUBRIC.md missing — run `make build`"
    assert _block(shipped.read_text()) == _block(RUBRIC.read_text())

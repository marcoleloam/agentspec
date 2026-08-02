"""Regression tests for native Codex command-skill generation."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_generator():
    script = Path(__file__).resolve().parent.parent / "scripts" / "generate-codex-plugin.py"
    spec = importlib.util.spec_from_file_location("codex_generator_mod", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


def test_command_skill_name_matches_codex_migration(gen):
    command = gen.COMMANDS_DIR / "workflow" / "brainstorm.md"
    assert gen.command_skill_name(command) == "source-command-workflow-brainstorm"


def test_build_command_skill_preserves_large_command(gen):
    command = gen.COMMANDS_DIR / "workflow" / "build.md"
    text = command.read_text(encoding="utf-8")
    rendered = gen.build_command_skill(
        gen.parse_frontmatter(text), gen.strip_frontmatter(text), command
    )

    assert 'name: "source-command-workflow-build"' in rendered
    assert "Execute implementation with on-the-fly task generation" in rendered
    assert "# Build Command" in rendered
    assert len(rendered.encode("utf-8")) > 4096


def test_all_commands_generate_unique_valid_names(gen):
    names = []
    for command in sorted(gen.COMMANDS_DIR.glob("*/*.md")):
        if command.name not in gen.SKIP_FILES:
            names.append(gen.command_skill_name(command))

    assert len(names) == 39
    assert len(names) == len(set(names))
    assert all(len(name) <= 64 for name in names)
    assert {
        "source-command-workflow-brainstorm",
        "source-command-workflow-define",
        "source-command-workflow-design",
        "source-command-workflow-build",
        "source-command-workflow-ship",
        "source-command-workflow-work",
    }.issubset(names)


def test_command_without_frontmatter_gets_fallback_description(gen):
    command = gen.COMMANDS_DIR / "visual-explainer" / "share.md"
    rendered = gen.build_command_skill({}, command.read_text(encoding="utf-8"), command)
    assert 'description: "Run the AgentSpec share command"' in rendered

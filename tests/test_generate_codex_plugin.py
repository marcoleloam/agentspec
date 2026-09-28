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

    assert len(names) == 40
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


def test_workflow_agent_effort_comes_from_phase_manifest(gen):
    fm = {"name": "build-agent", "description": "Orchestrator", "model": "inherit", "tools": ["Read", "Write"]}
    toml = gen.build_agent_toml(fm, "body", "workflow")
    assert 'model_reasoning_effort = "high"' in toml


def test_non_workflow_agent_effort_still_maps_from_model(gen):
    fm = {"name": "dbt-specialist", "description": "dbt", "model": "sonnet", "tools": ["Read"]}
    toml = gen.build_agent_toml(fm, "body", "data-engineering")
    assert 'model_reasoning_effort = "medium"' in toml
    assert 'sandbox_mode = "read-only"' in toml


def _render(gen, relative: str) -> str:
    command = gen.COMMANDS_DIR / relative
    text = command.read_text(encoding="utf-8")
    return gen.build_command_skill(gen.parse_frontmatter(text), gen.strip_frontmatter(text), command)


def test_delegated_workflow_skill_explains_codex_delegation(gen):
    rendered = _render(gen, "workflow/design.md")
    note = rendered.split("## Command Template", 1)[0]
    assert "## Running in Codex" in note
    assert "spawn the `design-agent` subagent" in note
    assert 'model_reasoning_effort = "high"' in note
    assert "do not exist in Codex" in note


def test_session_workflow_skill_gives_codex_effort_from_manifest(gen):
    for relative, effort in (("workflow/brainstorm.md", "high"), ("workflow/eval.md", "medium")):
        note = _render(gen, relative).split("## Command Template", 1)[0]
        assert f"codex -c model_reasoning_effort={effort}" in note
        assert "session model" in note


def test_non_workflow_skill_gets_tool_notes_only_when_needed(gen):
    commands = [c for c in sorted(gen.COMMANDS_DIR.glob("*/*.md")) if c.parent.name != "workflow"]
    with_tools = [c for c in commands if gen._CLAUDE_TOOL_RE.search(c.read_text(encoding="utf-8"))]
    without = [c for c in commands if c not in with_tools]
    for command in with_tools[:1] + without[:1]:
        rendered = _render(gen, str(command.relative_to(gen.COMMANDS_DIR)))
        assert ("## Running in Codex" in rendered) == (command in with_tools)
        assert "model_reasoning_effort" not in rendered.split("## Command Template", 1)[0]

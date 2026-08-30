"""Regression tests for the Grok Build plugin generator."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_generator():
    script = Path(__file__).resolve().parent.parent / "scripts" / "generate-grok-plugin.py"
    spec = importlib.util.spec_from_file_location("grok_generator_mod", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


def test_remap_tools_csv_dedupes_edit_multiedit(gen):
    assert gen.remap_tools_csv("Read, Write, Edit, MultiEdit, Grep") == (
        "read_file, write, search_replace, grep"
    )


def test_remap_task_and_ask_user(gen):
    assert gen.remap_tool("Task") == "spawn_subagent"
    assert gen.remap_tool("AskUserQuestion") == "ask_user_question"
    assert gen.remap_tool("TodoWrite") == "todo_write"


def test_rewrite_tools_in_body_prefers_task_tool_phrase(gen):
    src = "Invoke via Task tool\nTask(\n  subagent_type: \"dbt-specialist\",\n)\nRead(CLAUDE.md)\n"
    out = gen.rewrite_tools_in_body(src)
    assert "spawn_subagent tool" in out
    assert "spawn_subagent(" in out
    assert "read_file(CLAUDE.md)" in out
    assert "Task(" not in out
    assert "Read(" not in out


def test_rewrite_plugin_paths_flattens_agent_and_preserves_workspace(gen):
    src = (
        "Read(.claude/agents/workflow/build-agent.md)\n"
        "Read(.claude/sdd/templates/DESIGN_TEMPLATE.md)\n"
        "Write(.claude/sdd/features/DESIGN_FOO.md)\n"
        "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/judge.py\n"
    )
    out = gen.rewrite_plugin_paths(src)
    assert "${GROK_PLUGIN_ROOT}/agents/build-agent.md" in out
    assert "${GROK_PLUGIN_ROOT}/sdd/templates/DESIGN_TEMPLATE.md" in out
    assert ".claude/sdd/features/DESIGN_FOO.md" in out
    assert "${GROK_PLUGIN_ROOT}/scripts/judge.py" in out
    assert "${CLAUDE_PLUGIN_ROOT}" not in out
    assert ".claude/agents/" not in out


def test_adapt_agent_adds_grok_fields_and_drops_model(gen):
    source = gen.AGENTS_DIR / "workflow" / "build-agent.md"
    text = source.read_text(encoding="utf-8")
    rendered = gen.adapt_agent(text, source, plugin=True)

    assert "name: build-agent" in rendered
    assert "prompt_mode: full" in rendered
    assert "agents_md: true" in rendered
    assert "permission_mode: default" in rendered
    assert "spawn_subagent" in rendered
    assert "tools:" in rendered
    assert "Task" not in rendered.split("---", 2)[1]  # frontmatter
    assert "model: opus" not in rendered
    assert "mcp_servers:" not in rendered
    assert "${GROK_PLUGIN_ROOT}" in rendered or ".claude/sdd/features" in rendered
    assert "do not edit by hand" in rendered


def test_adapt_command_flattens_and_rewrites_tools(gen):
    source = gen.COMMANDS_DIR / "workflow" / "brainstorm.md"
    text = source.read_text(encoding="utf-8")
    rendered = gen.adapt_command(text, source, plugin=True)

    assert "name: brainstorm" in rendered
    assert "read_file(" in rendered or "read_file" in rendered
    assert "Read(CLAUDE.md)" not in rendered
    assert "Source: .claude/commands/workflow/brainstorm.md" in rendered
    assert "${GROK_PLUGIN_ROOT}/sdd/templates/BRAINSTORM_TEMPLATE.md" in rendered
    assert ".claude/sdd/features/" in rendered  # workspace output stays put


def test_all_commands_have_unique_stems(gen):
    stems = [md.name for md in gen._iter_md(gen.COMMANDS_DIR)]
    assert len(stems) == 39
    assert len(stems) == len(set(stems))
    assert "brainstorm.md" in stems
    assert "continue.md" in stems
    assert "work.md" in stems


def test_all_agents_have_unique_filenames(gen):
    names = [md.name for md in gen._iter_md(gen.AGENTS_DIR)]
    assert len(names) == 73
    assert len(names) == len(set(names))
    assert "dbt-specialist.md" in names
    assert "build-agent.md" in names


def test_read_only_agent_gets_plan_permission(gen):
    # aide-slide-reviewer is documented as READ-ONLY in its description.
    source = gen.AGENTS_DIR / "data-engineering" / "spark-troubleshooter.md"
    text = source.read_text(encoding="utf-8")
    fm = gen.parse_frontmatter(text)
    rendered = gen.adapt_agent(text, source, plugin=False)
    if gen.mutates_workspace(fm.get("tools")):
        assert "permission_mode: default" in rendered
    else:
        assert "permission_mode: plan" in rendered


def test_project_mode_keeps_claude_kb_paths(gen):
    source = gen.AGENTS_DIR / "data-engineering" / "dbt-specialist.md"
    text = source.read_text(encoding="utf-8")
    rendered = gen.adapt_agent(text, source, plugin=False)
    assert "${GROK_PLUGIN_ROOT}" not in rendered
    # Body tool names still rewritten.
    assert "Task(" not in rendered

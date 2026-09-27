"""Script paths the agent's Bash tool can actually resolve.

Claude Code fills in ${CLAUDE_PLUGIN_ROOT} only in that exact form, when it loads a plugin
command, and the Bash tool never sees the variable. So ${CLAUDE_PLUGIN_ROOT:-.} resolves to
./scripts/… in a user project. Sources call "${AGENTSPEC_SCRIPTS:-scripts}/x.py"; the
SessionStart hook exports AGENTSPEC_SCRIPTS and build-plugin.sh rewrites the fallback to the
exact ${CLAUDE_PLUGIN_ROOT} form.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
UNFILLED = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT:?-")
TREES = [".claude/agents", ".claude/commands", "plugin/agents", "plugin/commands", "plugin/skills",
         "plugin-grok/agents", "plugin-grok/commands"]


def text_files(tree: str):
    root = REPO / tree
    return [p for p in root.rglob("*") if p.suffix in {".md", ".yaml", ".yml"}] if root.is_dir() else []


@pytest.mark.parametrize("tree", TREES)
def test_no_unfilled_plugin_root_form(tree):
    offenders = [str(p.relative_to(REPO)) for p in text_files(tree) if UNFILLED.search(p.read_text(encoding="utf-8"))]
    assert offenders == []


def test_plugin_fallback_is_the_exact_plugin_root():
    calls = [m for p in text_files("plugin/commands")
             for m in re.findall(r"\$\{AGENTSPEC_SCRIPTS:-([^}]*\}?)[^/]*/", p.read_text(encoding="utf-8"))]
    assert calls, "plugin commands should call scripts through AGENTSPEC_SCRIPTS"
    assert set(calls) == {"${CLAUDE_PLUGIN_ROOT}"}


def test_every_called_script_ships_in_the_plugin():
    called = {m for p in text_files("plugin") for m in re.findall(r"AGENTSPEC_SCRIPTS:-[^\"]*/([\w-]+\.py)", p.read_text(encoding="utf-8"))}
    assert called
    assert called <= {p.name for p in (REPO / "plugin" / "scripts").glob("*.py")}


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash required")
def test_session_start_exports_script_dir(tmp_path):
    env_file = tmp_path / "env"
    script = REPO / "plugin-extras" / "scripts" / "init-workspace.sh"
    subprocess.run(["bash", str(script)], cwd=tmp_path, env={"CLAUDE_ENV_FILE": str(env_file), "PATH": "/usr/bin:/bin", "HOME": str(tmp_path)},
                   check=True, capture_output=True)
    exported = env_file.read_text(encoding="utf-8")
    assert f"export AGENTSPEC_SCRIPTS={script.parent}" in exported
    assert "export AGENTSPEC_MEMORY_INDEX=" in exported


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash required")
def test_session_start_exports_nothing_in_the_source_repo(tmp_path):
    """Developing AgentSpec with the plugin installed must still run the repo's own scripts."""
    work = tmp_path / "agentspec"
    (work / "plugin-extras" / "scripts").mkdir(parents=True)
    (work / "plugin-extras" / "scripts" / "memory-index.py").write_text("", encoding="utf-8")
    (work / "build-plugin.sh").write_text("", encoding="utf-8")
    env_file = tmp_path / "env"
    subprocess.run(["bash", str(REPO / "plugin-extras" / "scripts" / "init-workspace.sh")], cwd=work,
                   env={"CLAUDE_ENV_FILE": str(env_file), "PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}, check=True, capture_output=True)
    assert not env_file.exists() or "AGENTSPEC_SCRIPTS" not in env_file.read_text(encoding="utf-8")

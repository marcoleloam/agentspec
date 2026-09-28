"""SessionStart hook (plugin-extras/scripts/init-workspace.sh) under macOS /bin/bash 3.2.

`local -A` (associative arrays) aborts bash 3.2 under `set -e`, and it ran in stack
detection whenever a dbt_project.yml existed, so AGENTSPEC_SCRIPTS, AGENTSPEC_MEMORY_INDEX
and the memory tail were never produced. These tests run the real script with /bin/bash.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "plugin-extras" / "scripts" / "init-workspace.sh"
FIX = Path(__file__).parent / "fixtures" / "memory" / "sdd"
BASH = Path("/bin/bash")

pytestmark = pytest.mark.skipif(not BASH.exists(), reason="/bin/bash required")


def session_start(project: Path, home: Path, script: Path = SCRIPT) -> tuple[subprocess.CompletedProcess, str]:
    env_file = home / "env"
    path = f"{Path(sys.executable).parent}:/usr/bin:/bin"
    result = subprocess.run([str(BASH), str(script)], cwd=project, capture_output=True, text=True,
                            env={"CLAUDE_ENV_FILE": str(env_file), "PATH": path, "HOME": str(home)})
    return result, env_file.read_text(encoding="utf-8") if env_file.exists() else ""


@pytest.fixture
def dbt_project(tmp_path: Path) -> Path:
    """A dbt project with an active feature, so every SessionStart output has something to show."""
    project = tmp_path / "proj"
    shutil.copytree(FIX.parent, project / ".claude")
    (project / "dbt_project.yml").write_text("name: demo\n", encoding="utf-8")
    (project / "profiles.yml").write_text("demo:\n  target: snowflake\n", encoding="utf-8")
    (project / "requirements.txt").write_text("pydantic\n", encoding="utf-8")
    return project


def test_dbt_project_exports_paths_and_tail_under_bash_32(dbt_project, tmp_path):
    result, exported = session_start(dbt_project, tmp_path)
    assert result.returncode == 0, result.stderr
    assert f"export AGENTSPEC_SCRIPTS={SCRIPT.parent}" in exported
    assert "export AGENTSPEC_MEMORY_INDEX=" in exported
    assert "=== Feature ativa: DEMO" in result.stdout


def test_dbt_stack_hint_is_deduplicated(dbt_project, tmp_path):
    session_start(dbt_project, tmp_path)
    hint = (dbt_project / ".claude" / "sdd" / ".detected-stack.md").read_text(encoding="utf-8")
    assert "- dbt" in hint and "Snowflake" in hint
    assert hint.count("`cloud-platforms/") == 1
    assert hint.count("`/schema") == 1


def test_pydantic_only_project_has_no_empty_array_abort(tmp_path):
    """Detected tech with no agents/commands: empty arrays must not trip `set -u` on bash 3.2."""
    project = tmp_path / "proj"
    project.mkdir()
    (project / ".git").mkdir()
    (project / "requirements.txt").write_text("pydantic\n", encoding="utf-8")
    result, exported = session_start(project, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "AGENTSPEC_MEMORY_INDEX" in exported
    hint = (project / ".claude" / "sdd" / ".detected-stack.md").read_text(encoding="utf-8")
    assert "- Pydantic" in hint


def test_a_failing_stack_detection_cannot_suppress_memory(dbt_project, tmp_path):
    """Detection runs last and isolated: even if it aborts, exports and the tail already happened."""
    broken = tmp_path / "scripts" / "init-workspace.sh"
    broken.parent.mkdir()
    shutil.copy(SCRIPT.parent / "memory-index.py", broken.parent / "memory-index.py")
    broken.write_text(SCRIPT.read_text(encoding="utf-8").replace(
        "detect_project_stack() {\n", "detect_project_stack() {\n    local -A boom=()\n    : \"$UNSET_VAR\"\n", 1),
        encoding="utf-8")
    result, exported = session_start(dbt_project, tmp_path, script=broken)
    assert result.returncode == 0, result.stderr
    assert "AGENTSPEC_MEMORY_INDEX" in exported
    assert "=== Feature ativa: DEMO" in result.stdout

"""Drift gate: runtime scripts called by phase commands must ship in the built plugins.

Phase commands call ``${CLAUDE_PLUGIN_ROOT}/scripts/jev_select.py``. If the copy in a
built plugin diverges from ``scripts/`` (or is missing), installed users silently run a
stale selector or fall back to ``script_unavailable``. Rebuild with ``make build``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "scripts" / "jev_select.py"


@pytest.mark.parametrize("plugin_dir", ["plugin", "plugin-grok"])
def test_jev_select_shipped_and_in_sync(plugin_dir):
    root = REPO_ROOT / plugin_dir
    if not root.is_dir():
        pytest.skip(f"{plugin_dir}/ not built")
    shipped = root / "scripts" / "jev_select.py"
    assert shipped.is_file(), f"{plugin_dir}/scripts/jev_select.py missing — run `make build`"
    assert shipped.read_bytes() == SOURCE.read_bytes(), f"{plugin_dir}/scripts/jev_select.py is stale — run `make build`"

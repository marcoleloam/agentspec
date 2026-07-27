"""Shared fixtures for the spec-linter test suite."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def valid_spec() -> dict[str, Any]:
    """A minimal, fully governance-compliant V2 spec as a fresh dict per test."""
    return {
        "id": "code-reviewer",
        "name": "Code Reviewer",
        "description": "Reviews diffs.",
        "model": "claude-opus-4",
        "tools": ["read_file"],
        "maturity": "V2",
        "tier": "T2",
        "output_contract": {
            "format": "structured-report",
            "required_fields": ["summary"],
            "side_effects": {
                "files_written": False,
                "git_operations": ["none"],
                "external_apis": [],
            },
        },
        "stop_conditions": ["no diff"],
        "escalation_rules": ["escalate on security change"],
        "observability": {"confidence_scoring": True, "sources_attribution": True},
        "memory_backend": "none",
        "recall_strategy": "per-session",
        "requirements": ["lint the diff"],
        "deliverables": ["lint the diff"],
    }

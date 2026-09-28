"""kb_bench — KB vs Context7 benchmark for AgentSpec knowledge domains.

Runs identical data-engineering tasks through four knowledge arms (current KB,
Context7 only, lean KB + Context7, nothing) on the Codex CLI and recommends,
per domain stratum, whether to keep, slim or retire the KB.
"""
from __future__ import annotations

__version__ = "0.1.0"

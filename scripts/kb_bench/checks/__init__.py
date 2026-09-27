"""Deterministic verifiers invoked by task evals.

Every checker is a ``python -m kb_bench.checks.<name>`` CLI that exits 0 on
success and 1 on a failed assertion, printing one line per failure. Checkers
only parse and read files — they never import or execute agent-written code.
"""
from __future__ import annotations

import sys
from collections.abc import Sequence


def finish(failures: Sequence[str]) -> int:
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


def run(main) -> None:
    sys.exit(main(sys.argv[1:]))

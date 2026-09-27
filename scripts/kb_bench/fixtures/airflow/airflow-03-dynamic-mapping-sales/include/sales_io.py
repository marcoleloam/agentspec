"""I/O helpers shared by the sales DAGs. Safe to import at DAG-parse time."""
from __future__ import annotations

import csv
from pathlib import Path

LANDING_DIR = Path(__file__).resolve().parent.parent / "data" / "landing"


def list_landing_files(landing_dir: str | Path = LANDING_DIR) -> list[str]:
    """Return the CSV files currently waiting in the landing folder (sorted)."""
    return sorted(str(p) for p in Path(landing_dir).glob("sales_*.csv"))


def load_file(path: str, table: str) -> int:
    """Load one landing CSV into ``table``; return the number of rows loaded."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    print(f"loaded {len(rows)} rows from {path} into {table}")
    return len(rows)

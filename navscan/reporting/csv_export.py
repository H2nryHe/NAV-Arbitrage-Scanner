from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List


CSV_COLUMNS = [
    "rank",
    "date",
    "symbol",
    "asset_type",
    "price_close",
    "nav",
    "premium_discount_pct",
    "pd_zscore_20d",
    "half_life_days",
    "dollar_volume",
    "score",
    "rationale",
    "risk_flags",
]


def export_candidates_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            out = {}
            for col in CSV_COLUMNS:
                val = row.get(col)
                if col == "risk_flags" and isinstance(val, list):
                    val = ";".join(val)
                out[col] = val
            writer.writerow(out)


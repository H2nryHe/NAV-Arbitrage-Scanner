from __future__ import annotations

import csv
import io
import subprocess
from typing import Any, Dict, List

from .common import utc_now_iso


def fetch_price_volume_for_date(symbols: List[str], date_str: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    source = "stooq_daily_csv"

    for symbol in symbols:
        record: Dict[str, Any] = {
            "stage": "stage1_raw",
            "dataset": "price_volume",
            "source": source,
            "fetch_timestamp_utc": utc_now_iso(),
            "requested_date": date_str,
            "symbol": symbol,
            "status": "error",
            "reason": "row_not_found",
            "raw": None,
        }
        try:
            url = f"https://stooq.com/q/d/l/?s={symbol.lower()}.us&i=d"
            proc = subprocess.run(
                ["curl", "-sS", "-L", "--max-time", "20", url],
                check=True,
                capture_output=True,
                text=True,
            )
            rows = list(csv.DictReader(io.StringIO(proc.stdout)))
            matched = next((r for r in rows if r.get("Date") == date_str), None)
            if matched:
                record["status"] = "ok"
                record["reason"] = None
                record["raw"] = matched  # Preserves original field names.
            else:
                record["status"] = "error"
                record["reason"] = "date_not_available"
        except Exception as exc:  # noqa: BLE001
            record["status"] = "error"
            record["reason"] = str(exc)
        out.append(record)
    return out


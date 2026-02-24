from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from .common import http_get_json_with_retry, utc_now_iso


def _fmt_mmddyyyy(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%m-%d-%Y")


def fetch_events_for_date(symbols: List[str], date_str: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    source = "cefconnect_api_v3_distributionhistory"
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    window_start = _fmt_mmddyyyy((date_obj - timedelta(days=45)).strftime("%Y-%m-%d"))
    window_end = _fmt_mmddyyyy((date_obj + timedelta(days=5)).strftime("%Y-%m-%d"))

    for symbol in symbols:
        record: Dict[str, Any] = {
            "stage": "stage1_raw",
            "dataset": "events",
            "source": source,
            "fetch_timestamp_utc": utc_now_iso(),
            "requested_date": date_str,
            "symbol": symbol,
            "status": "error",
            "reason": "request_failed",
            "raw": None,
            "raw_context": {"window_start": window_start, "window_end": window_end},
        }
        try:
            url = (
                f"https://www.cefconnect.com/api/v3/distributionhistory/fund/{symbol}/"
                f"{window_start}/{window_end}"
            )
            payload = http_get_json_with_retry(url)
            rows = payload.get("Data", [])
            record["status"] = "ok"
            record["reason"] = None
            record["raw"] = rows  # Preserves original field names in event rows.
        except Exception as exc:  # noqa: BLE001
            record["status"] = "error"
            record["reason"] = str(exc)
        out.append(record)

    return out


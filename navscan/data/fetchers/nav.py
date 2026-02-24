from __future__ import annotations

from typing import Any, Dict, List

from .common import http_get_json_with_retry, utc_now_iso


def fetch_nav_for_date(symbols: List[str], date_str: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    source = "cefconnect_api_v3_pricinghistory"

    for symbol in symbols:
        record: Dict[str, Any] = {
            "stage": "stage1_raw",
            "dataset": "nav",
            "source": source,
            "fetch_timestamp_utc": utc_now_iso(),
            "requested_date": date_str,
            "symbol": symbol,
            "status": "error",
            "reason": "row_not_found",
            "raw": None,
            "raw_context": None,
        }
        try:
            periods = ["5D", "1M", "YTD", "1Y", "All"]
            matched = None
            data = {}
            for period in periods:
                url = f"https://www.cefconnect.com/api/v3/pricinghistory/{symbol}/{period}"
                payload = http_get_json_with_retry(url)
                data = payload.get("Data", {}) if isinstance(payload, dict) else {}
                if not isinstance(data, dict):
                    data = {}
                rows = data.get("PriceHistory", [])
                if not isinstance(rows, list):
                    rows = []
                matched = next(
                    (
                        row
                        for row in rows
                        if isinstance(row.get("DataDate"), str) and row["DataDate"][:10] == date_str
                    ),
                    None,
                )
                if matched:
                    break

            if not matched:
                # Fallback: latest available NAV date <= requested date.
                url = f"https://www.cefconnect.com/api/v3/pricinghistory/{symbol}/1Y"
                payload = http_get_json_with_retry(url)
                data = payload.get("Data", {}) if isinstance(payload, dict) else {}
                if not isinstance(data, dict):
                    data = {}
                rows = data.get("PriceHistory", [])
                if not isinstance(rows, list):
                    rows = []
                prior_rows = [
                    row
                    for row in rows
                    if isinstance(row.get("DataDate"), str) and row["DataDate"][:10] <= date_str
                ]
                if prior_rows:
                    matched = max(prior_rows, key=lambda x: x["DataDate"])

            if matched:
                record["status"] = "ok"
                record["reason"] = (
                    None if matched.get("DataDate", "")[:10] == date_str else "used_previous_nav_date"
                )
                record["raw"] = matched  # Preserves original field names.
                record["raw_context"] = {
                    "Ticker": data.get("Ticker"),
                    "NAVTicker": data.get("NAVTicker"),
                    "Cusip": data.get("Cusip"),
                    "Period": data.get("Period"),
                    "LastUpdated": data.get("LastUpdated"),
                }
            else:
                record["status"] = "error"
                record["reason"] = "date_not_available"
        except Exception as exc:  # noqa: BLE001
            record["status"] = "error"
            record["reason"] = str(exc)
        out.append(record)
    return out

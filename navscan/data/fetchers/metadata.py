from __future__ import annotations

from typing import Any, Dict, List

from .common import http_get_json_with_retry, utc_now_iso


METADATA_URL = (
    "https://www.cefconnect.com/api/v3/DailyPricing"
    "?props=Ticker,Name,CategoryId,CategoryName,Cusip,IsManagedDistribution,"
    "DistributionRateNAV,DistributionRatePrice,ReturnOnNAV,LastUpdated/"
)


def fetch_metadata(symbols: List[str], date_str: str) -> List[Dict[str, Any]]:
    source = "cefconnect_api_v3_dailypricing"
    out: List[Dict[str, Any]] = []
    symbol_set = set(symbols)
    payload = http_get_json_with_retry(METADATA_URL)

    if not isinstance(payload, list):
        raise RuntimeError("Unexpected metadata payload (not list)")

    by_symbol = {row.get("Ticker"): row for row in payload if row.get("Ticker")}
    for symbol in symbols:
        raw = by_symbol.get(symbol)
        out.append(
            {
                "stage": "stage1_raw",
                "dataset": "metadata",
                "source": source,
                "fetch_timestamp_utc": utc_now_iso(),
                "requested_date": date_str,
                "symbol": symbol,
                "status": "ok" if raw else "error",
                "reason": None if raw else "symbol_not_in_source",
                "raw": raw,  # Preserves original field names.
            }
        )

    # Keep explicit accounting of extra source symbols not in universe (traceability).
    extra_symbols = sorted(set(by_symbol) - symbol_set)
    for symbol in extra_symbols:
        out.append(
            {
                "stage": "stage1_raw",
                "dataset": "metadata",
                "source": source,
                "fetch_timestamp_utc": utc_now_iso(),
                "requested_date": date_str,
                "symbol": symbol,
                "status": "skipped",
                "reason": "outside_universe",
                "raw": by_symbol[symbol],
            }
        )
    return out


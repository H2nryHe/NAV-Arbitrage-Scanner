from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from navscan.features.liquidity import compute_dollar_volume
from navscan.features.premium_discount import compute_premium_discount_pct
from navscan.features.statistics import rolling_zscore
from navscan.pipeline.validate import build_data_quality_flags


def _read_ndjson(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def list_raw_dates(raw_root: Path) -> List[str]:
    pattern_root = raw_root / "price_volume"
    if not pattern_root.exists():
        return []
    out = []
    for p in pattern_root.glob("date=*"):
        if p.is_dir():
            out.append(p.name.split("=", 1)[1])
    return sorted(out)


def _first_snapshot_path(raw_root: Path, dataset: str, date_str: str) -> Optional[Path]:
    base = raw_root / dataset / f"date={date_str}"
    if not base.exists():
        return None
    snapshots = sorted(base.glob("source=*/snapshot.ndjson"))
    return snapshots[0] if snapshots else None


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_mdy(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _event_flag(events_record: Dict[str, Any], date_str: str) -> bool:
    if events_record.get("status") != "ok":
        return False
    raw_events = events_record.get("raw") or []
    if not isinstance(raw_events, list):
        return False
    for event in raw_events:
        if _parse_mdy(event.get("ExDivDateDisplay")) == date_str:
            return True
    return False


def build_silver_records_for_date(
    raw_root: Path,
    date_str: str,
    symbols: Iterable[str],
    zscore_window: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    price_path = _first_snapshot_path(raw_root, "price_volume", date_str)
    nav_path = _first_snapshot_path(raw_root, "nav", date_str)
    events_path = _first_snapshot_path(raw_root, "events", date_str)
    meta_path = _first_snapshot_path(raw_root, "metadata", date_str)

    price_rows = _read_ndjson(price_path) if price_path else []
    nav_rows = _read_ndjson(nav_path) if nav_path else []
    events_rows = _read_ndjson(events_path) if events_path else []
    meta_rows = _read_ndjson(meta_path) if meta_path else []

    by_symbol: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for r in price_rows:
        by_symbol[r.get("symbol", "")]["price"] = r
    for r in nav_rows:
        by_symbol[r.get("symbol", "")]["nav"] = r
    for r in events_rows:
        by_symbol[r.get("symbol", "")]["events"] = r
    for r in meta_rows:
        if r.get("status") == "ok":
            by_symbol[r.get("symbol", "")]["meta"] = r

    silver_rows: List[Dict[str, Any]] = []
    for symbol in symbols:
        src = by_symbol.get(symbol, {})
        pr = src.get("price", {})
        nr = src.get("nav", {})
        er = src.get("events", {})
        mr = src.get("meta", {})

        raw_price = (pr.get("raw") or {}) if pr.get("status") == "ok" else {}
        raw_nav = (nr.get("raw") or {}) if nr.get("status") == "ok" else {}
        raw_meta = (mr.get("raw") or {}) if mr.get("status") == "ok" else {}
        nav_reason = nr.get("reason")
        nav_date = raw_nav.get("DataDate")

        price_close = _safe_float(raw_price.get("Close"))
        volume = _safe_float(raw_price.get("Volume"))
        nav = _safe_float(raw_nav.get("NAVData"))
        premium_discount_pct = compute_premium_discount_pct(price_close, nav)
        dollar_volume = compute_dollar_volume(price_close, volume)

        row: Dict[str, Any] = {
            "date": date_str,
            "symbol": symbol,
            "asset_type": "CEF",
            "price_close": price_close,
            "nav": nav,
            "premium_discount_pct": premium_discount_pct,
            "volume": volume,
            "dollar_volume": dollar_volume,
            "price_time": raw_price.get("Date"),
            "nav_time": nav_date,
            "nav_staleness_flag": bool(nav_date and nav_date[:10] < date_str),
            "expense_ratio": None,
            "leverage_flag": None,
            "category": raw_meta.get("CategoryName"),
            "distribution_event_flag": _event_flag(er, date_str),
            "rebalance_event_flag": None,
            "borrow_fee_proxy": None,
            "shortability_flag": None,
            "spread_proxy": None,
            "pd_zscore_20d": None,  # assigned after rolling pass
            "zscore_window_used": zscore_window,
            "data_quality_flags": [],
            "source_trace": {
                "price_source": pr.get("source"),
                "price_fetch_timestamp_utc": pr.get("fetch_timestamp_utc"),
                "nav_source": nr.get("source"),
                "nav_fetch_timestamp_utc": nr.get("fetch_timestamp_utc"),
                "events_source": er.get("source"),
                "events_fetch_timestamp_utc": er.get("fetch_timestamp_utc"),
                "metadata_source": mr.get("source"),
                "metadata_fetch_timestamp_utc": mr.get("fetch_timestamp_utc"),
                "nav_reason": nav_reason,
            },
        }
        silver_rows.append(row)

    summary = {
        "date": date_str,
        "records": len(silver_rows),
        "missing_price": sum(1 for r in silver_rows if r["price_close"] is None),
        "missing_nav": sum(1 for r in silver_rows if r["nav"] is None),
        "invalid_nav": sum(1 for r in silver_rows if isinstance(r["nav"], (int, float)) and r["nav"] <= 0),
        "missing_volume": sum(1 for r in silver_rows if r["volume"] is None),
        "nav_stale_rows": sum(1 for r in silver_rows if r["nav_staleness_flag"]),
        "distribution_event_rows": sum(1 for r in silver_rows if r["distribution_event_flag"]),
    }
    return silver_rows, summary


def apply_rolling_stats(all_rows: List[Dict[str, Any]], zscore_window: int) -> None:
    by_symbol: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in all_rows:
        by_symbol[row["symbol"]].append(row)
    for symbol_rows in by_symbol.values():
        symbol_rows.sort(key=lambda x: x["date"])
        values = [r["premium_discount_pct"] for r in symbol_rows]
        zscores = rolling_zscore(values, zscore_window)
        for row, z in zip(symbol_rows, zscores):
            row["pd_zscore_20d"] = z
    for row in all_rows:
        row["data_quality_flags"] = build_data_quality_flags(row, zscore_window)


def write_silver_outputs(
    silver_root: Path,
    rows_by_date: Dict[str, List[Dict[str, Any]]],
    summaries: Dict[str, Dict[str, Any]],
) -> None:
    silver_root.mkdir(parents=True, exist_ok=True)
    all_rows: List[Dict[str, Any]] = []
    for date_str, rows in sorted(rows_by_date.items()):
        all_rows.extend(rows)
        date_path = silver_root / f"date={date_str}" / "snapshot.ndjson"
        date_path.parent.mkdir(parents=True, exist_ok=True)
        with date_path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=True) + "\n")

    all_path = silver_root / "all_dates.ndjson"
    with all_path.open("w", encoding="utf-8") as f:
        for row in sorted(all_rows, key=lambda x: (x["date"], x["symbol"])):
            f.write(json.dumps(row, ensure_ascii=True) + "\n")

    summary_path = silver_root / "run_summary.json"
    summary_path.write_text(json.dumps({"dates": summaries, "records_total": len(all_rows)}, indent=2))

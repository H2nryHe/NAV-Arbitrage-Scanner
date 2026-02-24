#!/usr/bin/env python3
"""Stage 0 feasibility check for NAV Arbitrage Scanner.

Checks one-date field coverage for:
- price (CEFConnect DailyPricing)
- nav (CEFConnect DailyPricing)
- volume (Stooq daily CSV)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError


CEFCONNECT_URL = (
    "https://www.cefconnect.com/api/v3/DailyPricing"
    "?props=Ticker,Name,Price,NAV,LastUpdated,NAVPublished,AverageVolume,Cusip/"
)


@dataclass
class SymbolCoverage:
    symbol: str
    asset_type: str
    date: str
    price_close: Optional[float]
    nav: Optional[float]
    volume: Optional[float]
    volume_source: str
    cef_last_updated: Optional[str]
    nav_published: Optional[str]
    price_source: str
    nav_source: str
    premium_discount_pct: Optional[float]
    has_price: bool
    has_nav: bool
    has_volume: bool
    has_all_three: bool


def http_get_json(url: str) -> object:
    text = http_get_text(url)
    return json.loads(text)


def http_get_text(url: str) -> str:
    proc = subprocess.run(
        [
            "curl",
            "-sL",
            "--max-time",
            "20",
            url,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def load_universe_symbols(path: Path) -> List[str]:
    symbols: List[str] = []
    inside_symbols = False
    pattern = re.compile(r"^\s*-\s*([A-Za-z0-9.\-]+)(?:\s*#.*)?\s*$")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if re.match(r"^\s*symbols:\s*$", line):
            inside_symbols = True
            continue
        if inside_symbols:
            m = pattern.match(line)
            if m:
                symbols.append(m.group(1).upper())
            elif line.strip() and not line.startswith(" "):
                break
    if not symbols:
        raise ValueError(f"No symbols found under 'symbols:' in {path}")
    return symbols


def parse_float(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_cefconnect() -> List[dict]:
    payload = http_get_json(CEFCONNECT_URL)
    if not isinstance(payload, list):
        raise ValueError("CEFConnect response is not a list")
    return payload


def fetch_stooq_row(symbol: str, date_str: str) -> Optional[dict]:
    url = f"https://stooq.com/q/d/l/?s={symbol.lower()}.us&i=d"
    text = http_get_text(url)
    rows = list(csv.DictReader(text.splitlines()))
    for row in rows:
        if row.get("Date") == date_str:
            return row
    return None


def build_coverage(
    symbols: List[str], asset_type_by_symbol: Dict[str, str], test_date: str
) -> List[SymbolCoverage]:
    cef_rows = fetch_cefconnect()
    cef_map = {row.get("Ticker"): row for row in cef_rows if row.get("Ticker")}
    results: List[SymbolCoverage] = []

    for symbol in symbols:
        asset_type = asset_type_by_symbol.get(symbol, "CEF")
        cef_row = cef_map.get(symbol)
        price = parse_float(cef_row.get("Price")) if cef_row else None
        nav = parse_float(cef_row.get("NAV")) if cef_row else None
        stooq_row = None
        stooq_close = None
        volume = None
        try:
            stooq_row = fetch_stooq_row(symbol, test_date)
            if stooq_row:
                stooq_close = parse_float(stooq_row.get("Close"))
                volume = parse_float(stooq_row.get("Volume"))
        except (HTTPError, URLError, TimeoutError, subprocess.CalledProcessError):
            stooq_row = None

        premium_discount = None
        if price is not None and nav not in (None, 0):
            premium_discount = (price / nav - 1.0) * 100.0

        results.append(
            SymbolCoverage(
                symbol=symbol,
                asset_type=asset_type,
                date=test_date,
                price_close=price,
                nav=nav,
                volume=volume,
                volume_source="Stooq daily CSV",
                cef_last_updated=cef_row.get("LastUpdated") if cef_row else None,
                nav_published=cef_row.get("NAVPublished") if cef_row else None,
                price_source="CEFConnect DailyPricing",
                nav_source="CEFConnect DailyPricing",
                premium_discount_pct=premium_discount,
                has_price=price is not None,
                has_nav=nav is not None,
                has_volume=volume is not None,
                has_all_three=price is not None and nav is not None and volume is not None,
            )
        )

        # Optional console mismatch note between CEFConnect and Stooq close.
        if price is not None and stooq_close is not None and abs(price - stooq_close) > 0.25:
            print(
                f"warning: {symbol} CEFConnect price={price} vs Stooq close={stooq_close}",
                file=sys.stderr,
            )

    return results


def write_outputs(records: List[SymbolCoverage], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not records:
        raise ValueError("No records to write")
    date_str = records[0].date
    csv_path = output_dir / f"coverage_{date_str}.csv"
    summary_path = output_dir / f"summary_{date_str}.json"

    fieldnames = [
        "symbol",
        "asset_type",
        "date",
        "price_close",
        "nav",
        "volume",
        "premium_discount_pct",
        "has_price",
        "has_nav",
        "has_volume",
        "has_all_three",
        "cef_last_updated",
        "nav_published",
        "price_source",
        "nav_source",
        "volume_source",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({k: getattr(r, k) for k in fieldnames})

    summary = {
        "date": date_str,
        "universe_size": len(records),
        "symbols_with_price": sum(r.has_price for r in records),
        "symbols_with_nav": sum(r.has_nav for r in records),
        "symbols_with_volume": sum(r.has_volume for r in records),
        "symbols_with_all_three": sum(r.has_all_three for r in records),
        "premium_discount_computable": sum(r.premium_discount_pct is not None for r in records),
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "csv_path": str(csv_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Stage 0 data source feasibility checks.")
    parser.add_argument(
        "--universe",
        default="configs/universe_example.yaml",
        help="Path to universe YAML (expects symbols list).",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Optional date YYYY-MM-DD. If omitted, use latest CEFConnect LastUpdated date.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/feasibility",
        help="Directory for coverage CSV/summary JSON outputs.",
    )
    args = parser.parse_args()

    universe_path = Path(args.universe)
    symbols = load_universe_symbols(universe_path)

    # Determine test date from live source unless explicitly set.
    test_date = args.date
    if test_date is None:
        rows = fetch_cefconnect()
        max_dt = max(
            row.get("LastUpdated", "") for row in rows if isinstance(row.get("LastUpdated"), str)
        )
        if not max_dt:
            raise ValueError("Unable to infer date from CEFConnect LastUpdated")
        test_date = max_dt.split("T")[0]

    # Parse asset types from simple YAML lines ("- SYMBOL # TYPE")
    asset_type_by_symbol: Dict[str, str] = {}
    for raw_line in universe_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s*([A-Za-z0-9.\-]+)\s*(?:#\s*([A-Za-z0-9_ -]+))?\s*$", raw_line)
        if m:
            symbol = m.group(1).upper()
            raw_type = (m.group(2) or "CEF").strip().upper().replace("-", "_")
            asset_type_by_symbol[symbol] = "ETF" if "ETF" in raw_type else "CEF"

    records = build_coverage(symbols, asset_type_by_symbol, test_date)
    write_outputs(records, Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

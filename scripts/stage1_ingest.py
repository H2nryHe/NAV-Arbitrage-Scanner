#!/usr/bin/env python3
"""Stage 1 raw ingestion runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

# Allow running as script without package install.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from navscan.data.fetchers.common import load_universe_symbols, write_ndjson
from navscan.data.fetchers.events import fetch_events_for_date
from navscan.data.fetchers.metadata import fetch_metadata
from navscan.data.fetchers.nav import fetch_nav_for_date
from navscan.data.fetchers.price_volume import fetch_price_volume_for_date
from navscan.logging_utils import get_logger


def _summary(rows: List[Dict[str, object]]) -> Dict[str, int]:
    ok = sum(1 for r in rows if r.get("status") == "ok")
    error = sum(1 for r in rows if r.get("status") == "error")
    skipped = sum(1 for r in rows if r.get("status") == "skipped")
    return {"ok": ok, "error": error, "skipped": skipped, "total": len(rows)}


def _log_errors(logger, rows: List[Dict[str, object]], source: str) -> None:
    for r in rows:
        if r.get("status") == "error":
            logger.warning(
                "raw_fetch_failed",
                extra={
                    "stage": "stage1",
                    "source": source,
                    "symbol": r.get("symbol", "-"),
                    "reason": r.get("reason", "-"),
                },
            )


def run_for_date(date_str: str, symbols: List[str], raw_root: Path, logger) -> Dict[str, Dict[str, int]]:
    logger.info(
        "ingestion_date_start",
        extra={"stage": "stage1", "source": "-", "symbol": "-", "reason": date_str},
    )

    by_dataset: Dict[str, List[Dict[str, object]]] = {}
    by_dataset["price_volume"] = fetch_price_volume_for_date(symbols, date_str)
    by_dataset["nav"] = fetch_nav_for_date(symbols, date_str)
    by_dataset["events"] = fetch_events_for_date(symbols, date_str)
    by_dataset["metadata"] = fetch_metadata(symbols, date_str)

    for dataset, rows in by_dataset.items():
        source = rows[0]["source"] if rows else "-"
        path = raw_root / dataset / f"date={date_str}" / f"source={source}" / "snapshot.ndjson"
        write_ndjson(path, rows)
        _log_errors(logger, rows, str(source))

    summaries = {dataset: _summary(rows) for dataset, rows in by_dataset.items()}
    summary_path = raw_root / "run_summaries" / f"date={date_str}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps({"date": date_str, "datasets": summaries}, indent=2))

    logger.info(
        "ingestion_date_done",
        extra={"stage": "stage1", "source": "-", "symbol": "-", "reason": json.dumps(summaries)},
    )
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Stage 1 raw ingestion.")
    parser.add_argument("--dates", required=True, help="Comma-separated dates, e.g. 2026-02-19,2026-02-20")
    parser.add_argument("--universe", default="configs/universe_example.yaml")
    parser.add_argument("--raw-root", default="data/raw")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logger = get_logger(verbose=args.verbose)
    symbols = load_universe_symbols(Path(args.universe))
    dates = [d.strip() for d in args.dates.split(",") if d.strip()]
    if not dates:
        raise ValueError("No dates supplied")

    raw_root = Path(args.raw_root)
    all_summaries: Dict[str, Dict[str, Dict[str, int]]] = {}
    for d in dates:
        try:
            all_summaries[d] = run_for_date(d, symbols, raw_root, logger)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "ingestion_date_crashed",
                extra={"stage": "stage1", "source": "-", "symbol": "-", "reason": str(exc)},
            )
            all_summaries[d] = {"fatal": {"ok": 0, "error": 1, "skipped": 0, "total": 1}}

    logger.info(
        "stage1_complete",
        extra={"stage": "stage1", "source": "-", "symbol": "-", "reason": json.dumps(all_summaries)},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

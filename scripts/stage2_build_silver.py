#!/usr/bin/env python3
"""Stage 2 silver builder (raw -> standardized + basic features)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from navscan.data.fetchers.common import load_universe_symbols
from navscan.logging_utils import get_logger
from navscan.pipeline.standardize import (
    apply_rolling_stats,
    build_silver_records_for_date,
    list_raw_dates,
    write_silver_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 2 silver dataset from raw.")
    parser.add_argument("--raw-root", default="data/raw")
    parser.add_argument("--silver-root", default="data/silver")
    parser.add_argument("--universe", default="configs/universe_example.yaml")
    parser.add_argument("--dates", default="")
    parser.add_argument("--zscore-window", type=int, default=20)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logger = get_logger(verbose=args.verbose)
    raw_root = Path(args.raw_root)
    silver_root = Path(args.silver_root)
    symbols = load_universe_symbols(Path(args.universe))

    if args.dates.strip():
        dates = [d.strip() for d in args.dates.split(",") if d.strip()]
    else:
        dates = list_raw_dates(raw_root)

    if not dates:
        raise ValueError("No raw dates found to process")

    logger.info(
        "stage2_start",
        extra={
            "stage": "stage2",
            "source": "raw",
            "symbol": "-",
            "reason": f"dates={','.join(dates)} window={args.zscore_window}",
        },
    )

    rows_by_date: Dict[str, List[Dict[str, object]]] = {}
    summaries: Dict[str, Dict[str, object]] = {}
    all_rows: List[Dict[str, object]] = []

    for date_str in dates:
        rows, summary = build_silver_records_for_date(raw_root, date_str, symbols, args.zscore_window)
        rows_by_date[date_str] = rows
        summaries[date_str] = summary
        all_rows.extend(rows)
        logger.info(
            "stage2_date_built",
            extra={
                "stage": "stage2",
                "source": "silver",
                "symbol": "-",
                "reason": json.dumps(summary),
            },
        )

    apply_rolling_stats(all_rows, args.zscore_window)
    write_silver_outputs(silver_root, rows_by_date, summaries)

    logger.info(
        "stage2_complete",
        extra={
            "stage": "stage2",
            "source": "silver",
            "symbol": "-",
            "reason": f"records={len(all_rows)}",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


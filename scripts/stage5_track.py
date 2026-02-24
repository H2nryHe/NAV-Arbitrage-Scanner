#!/usr/bin/env python3
"""Stage 5 historical storage + reversion tracking."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from navscan.logging_utils import get_logger
from navscan.tracking.outcomes import compute_and_store_outcomes
from navscan.tracking.queries import query_reverted_by_date
from navscan.tracking.store import (
    connect,
    get_candidates_for_date,
    init_schema,
    record_run,
    upsert_candidates,
    upsert_snapshots,
)


def _read_ndjson(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _discover_dates(base: Path, pattern: str) -> List[str]:
    out = []
    for p in base.glob(pattern):
        if p.is_dir():
            out.append(p.name.split("=", 1)[1])
    return sorted(out)


def _date_list(arg_dates: str, discovered: Iterable[str]) -> List[str]:
    if arg_dates.strip():
        return sorted({x.strip() for x in arg_dates.split(",") if x.strip()})
    return sorted(set(discovered))


def cmd_update(args: argparse.Namespace) -> int:
    logger = get_logger(verbose=args.verbose)
    db_path = Path(args.db)
    signals_root = Path(args.signals_root)
    silver_root = Path(args.silver_root)
    horizons = [int(x.strip()) for x in args.horizons.split(",") if x.strip()]

    conn = connect(db_path)
    init_schema(conn)
    record_run(conn, "update", f"horizons={horizons}")

    silver_dates = _discover_dates(silver_root, "date=*")
    signal_dates = _discover_dates(signals_root, "date=*")
    dates = _date_list(args.scan_dates, sorted(set(silver_dates) | set(signal_dates)))

    for d in silver_dates:
        snap_path = silver_root / f"date={d}" / "snapshot.ndjson"
        rows = _read_ndjson(snap_path)
        upsert_snapshots(conn, rows, str(snap_path))

    for d in dates:
        cand_path = signals_root / f"date={d}" / "candidates_ranked.ndjson"
        cand_rows = _read_ndjson(cand_path)
        if cand_rows:
            upsert_candidates(conn, cand_rows, str(cand_path))

    outcome_totals = {"ok": 0, "missing_followup_data": 0, "zero_scan_pd": 0}
    for d in dates:
        cands = [dict(x) for x in get_candidates_for_date(conn, d)]
        if not cands:
            continue
        counts = compute_and_store_outcomes(conn, d, cands, horizons)
        for k, v in counts.items():
            outcome_totals[k] += v

    summary = {
        "db": str(db_path),
        "scan_dates_considered": dates,
        "horizons": horizons,
        "outcome_counts": outcome_totals,
    }
    logger.info(
        "stage5_update_complete",
        extra={"stage": "stage5", "source": "tracking", "symbol": "-", "reason": json.dumps(summary)},
    )
    print(json.dumps(summary, indent=2))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    conn = connect(Path(args.db))
    init_schema(conn)
    out = query_reverted_by_date(conn, args.scan_date, args.top_n, args.as_of_date)
    print(json.dumps(out, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Stage 5 tracking")
    sub = p.add_subparsers(dest="command", required=True)

    up = sub.add_parser("update")
    up.add_argument("--db", default="data/warehouse/navscan_stage5.sqlite")
    up.add_argument("--signals-root", default="data/gold/signals")
    up.add_argument("--silver-root", default="data/silver")
    up.add_argument("--scan-dates", default="")
    up.add_argument("--horizons", default="1,3,5")
    up.add_argument("--verbose", action="store_true")

    q = sub.add_parser("query")
    q.add_argument("--db", default="data/warehouse/navscan_stage5.sqlite")
    q.add_argument("--scan-date", required=True)
    q.add_argument("--top-n", type=int, default=10)
    q.add_argument("--as-of-date", required=True)
    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "update":
        return cmd_update(args)
    if args.command == "query":
        return cmd_query(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


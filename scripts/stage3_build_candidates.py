#!/usr/bin/env python3
"""Stage 3 candidate builder from silver data."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from navscan.logging_utils import get_logger
from navscan.signals.extreme import detect_extreme
from navscan.signals.filters import event_filter, liquidity_filter
from navscan.signals.mean_reversion import estimate_half_life_days
from navscan.signals.rank import compute_score
from navscan.signals.risk_flags import build_risk_flags


def _read_ndjson(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _write_ndjson(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")


def _latest_silver_date(silver_root: Path) -> str:
    dates = []
    for p in (silver_root).glob("date=*"):
        if p.is_dir():
            dates.append(p.name.split("=", 1)[1])
    if not dates:
        raise ValueError("No silver date snapshots found")
    return sorted(dates)[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 3 ranked candidates.")
    parser.add_argument("--silver-root", default="data/silver")
    parser.add_argument("--output-root", default="data/gold/signals")
    parser.add_argument("--config", default="configs/stage3_signals.json")
    parser.add_argument("--date", default="")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logger = get_logger(verbose=args.verbose)
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    silver_root = Path(args.silver_root)
    date_str = args.date or _latest_silver_date(silver_root)

    day_rows = _read_ndjson(silver_root / f"date={date_str}" / "snapshot.ndjson")
    all_rows = _read_ndjson(silver_root / "all_dates.ndjson")
    history_by_symbol: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in all_rows:
        if r["date"] <= date_str:
            history_by_symbol[r["symbol"]].append(r)
    for sym in history_by_symbol:
        history_by_symbol[sym].sort(key=lambda x: x["date"])

    scored_rows: List[Dict[str, Any]] = []
    candidates: List[Dict[str, Any]] = []

    for row in day_rows:
        symbol = row["symbol"]
        series = [x.get("premium_discount_pct") for x in history_by_symbol.get(symbol, [])]
        hl = estimate_half_life_days(
            series,
            min_points=int(cfg["half_life"]["min_points"]),
            max_half_life_days=float(cfg["half_life"]["max_half_life_days"]),
        )
        row["half_life_days"] = hl["half_life_days"]
        row["half_life_reason"] = hl["reason"]

        is_extreme, extreme_component, extreme_reason = detect_extreme(row, cfg["extreme"])
        liq_ok, liq_reason = liquidity_filter(row, cfg["liquidity"])
        evt_ok, evt_reason = event_filter(row, cfg["event_filter"])

        row["extreme_triggered"] = is_extreme
        row["extreme_reason"] = extreme_reason
        row["liquidity_pass"] = liq_ok
        row["liquidity_reason"] = liq_reason
        row["event_pass"] = evt_ok
        row["event_reason"] = evt_reason
        row["_liquidity_reference_dv"] = float(cfg["liquidity"]["reference_dollar_volume"])
        row["risk_flags"] = build_risk_flags(row, str(cfg["event_filter"]["event_data_status"]))

        score_parts = compute_score(row, cfg["score"], extreme_component)
        row.update(score_parts)

        rationale_bits = []
        if is_extreme:
            rationale_bits.append(f"extreme:{extreme_reason}")
        if liq_ok:
            rationale_bits.append("liquidity:pass")
        if row["half_life_days"] is not None:
            rationale_bits.append(f"half_life:{row['half_life_days']:.2f}d")
        else:
            rationale_bits.append(f"half_life:{row['half_life_reason']}")
        row["rationale"] = "; ".join(rationale_bits)

        scored_rows.append(row)
        if is_extreme and liq_ok and evt_ok:
            candidates.append(row)

    candidates.sort(key=lambda x: x["score"], reverse=True)
    for i, row in enumerate(candidates, start=1):
        row["rank"] = i

    out_dir = Path(args.output_root) / f"date={date_str}"
    _write_ndjson(out_dir / "scored_universe.ndjson", scored_rows)
    _write_ndjson(out_dir / "candidates_ranked.ndjson", candidates)

    summary = {
        "date": date_str,
        "universe_count": len(scored_rows),
        "candidate_count": len(candidates),
        "extreme_count": sum(1 for r in scored_rows if r["extreme_triggered"]),
        "liquidity_pass_count": sum(1 for r in scored_rows if r["liquidity_pass"]),
        "event_block_count": sum(1 for r in scored_rows if not r["event_pass"]),
        "half_life_available_count": sum(1 for r in scored_rows if r["half_life_days"] is not None),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    logger.info(
        "stage3_complete",
        extra={"stage": "stage3", "source": "silver", "symbol": "-", "reason": json.dumps(summary)},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


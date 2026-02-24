from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from navscan.tracking.store import fetch_snapshot_pd, upsert_outcome, utc_now


def _date_add(date_str: str, days: int) -> str:
    return (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")


def compute_and_store_outcomes(conn, scan_date: str, candidates: List[Dict[str, Any]], horizons: List[int]) -> Dict[str, int]:
    counts = {"ok": 0, "missing_followup_data": 0, "zero_scan_pd": 0}
    for c in candidates:
        symbol = c["symbol"]
        pd_scan = c["premium_discount_pct_at_scan"]
        for h in horizons:
            target_date = _date_add(scan_date, h)
            outcome = {
                "scan_date": scan_date,
                "symbol": symbol,
                "horizon_days": h,
                "target_date": target_date,
                "pd_scan": pd_scan,
                "pd_target": None,
                "abs_pd_change": None,
                "reverted_flag": None,
                "status": "missing_followup_data",
                "reason": "snapshot_not_found",
                "source_snapshot_date": target_date,
                "computed_ts": utc_now(),
            }

            if not isinstance(pd_scan, (int, float)):
                outcome["status"] = "missing_scan_pd"
                outcome["reason"] = "scan_pd_missing"
                upsert_outcome(conn, outcome)
                counts["missing_followup_data"] += 1
                continue
            if float(pd_scan) == 0.0:
                outcome["status"] = "zero_scan_pd"
                outcome["reason"] = "cannot_assess_reversion_from_zero"
                upsert_outcome(conn, outcome)
                counts["zero_scan_pd"] += 1
                continue

            pd_target = fetch_snapshot_pd(conn, target_date, symbol)
            if not isinstance(pd_target, (int, float)):
                upsert_outcome(conn, outcome)
                counts["missing_followup_data"] += 1
                continue

            abs_scan = abs(float(pd_scan))
            abs_target = abs(float(pd_target))
            reverted = 1 if abs_target < abs_scan else 0

            outcome["pd_target"] = float(pd_target)
            outcome["abs_pd_change"] = abs_scan - abs_target
            outcome["reverted_flag"] = reverted
            outcome["status"] = "ok"
            outcome["reason"] = "reverted" if reverted else "not_reverted"
            upsert_outcome(conn, outcome)
            counts["ok"] += 1

    return counts


from __future__ import annotations

from typing import Any, Dict, List


def build_risk_flags(row: Dict[str, Any], event_data_status: str) -> List[str]:
    flags: List[str] = []
    if row.get("nav_staleness_flag"):
        flags.append("nav_stale")
    if row.get("half_life_days") is None:
        flags.append("half_life_unavailable")
    if "insufficient_history_20d" in (row.get("data_quality_flags") or []):
        flags.append("insufficient_history_20d")
    if event_data_status != "full":
        flags.append("event_data_partial")
    return flags


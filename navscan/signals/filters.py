from __future__ import annotations

from typing import Any, Dict, Tuple


def liquidity_filter(row: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[bool, str]:
    dv = row.get("dollar_volume")
    threshold = float(cfg["min_dollar_volume"])
    if not isinstance(dv, (int, float)):
        return False, "missing_dollar_volume"
    if float(dv) < threshold:
        return False, f"dollar_volume_below_threshold({dv:.2f}<{threshold:.2f})"
    return True, "ok"


def event_filter(row: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[bool, str]:
    if bool(cfg.get("exclude_distribution_events", True)) and bool(row.get("distribution_event_flag")):
        return False, "distribution_event_excluded"
    return True, "ok"


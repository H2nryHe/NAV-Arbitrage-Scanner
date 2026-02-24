from __future__ import annotations

from typing import Any, Dict, List


def build_data_quality_flags(row: Dict[str, Any], zscore_window: int) -> List[str]:
    flags: List[str] = []
    if row.get("price_close") is None:
        flags.append("missing_price")
    if row.get("volume") is None:
        flags.append("missing_volume")
    nav = row.get("nav")
    if nav is None:
        flags.append("missing_nav")
    elif nav <= 0:
        flags.append("invalid_nav")
    if row.get("premium_discount_pct") is None:
        flags.append("missing_premium_discount")
    if row.get("dollar_volume") is None:
        flags.append("missing_dollar_volume")
    if row.get("pd_zscore_20d") is None:
        flags.append(f"insufficient_history_{zscore_window}d")
    if row.get("nav_staleness_flag"):
        flags.append("nav_stale")
    return flags

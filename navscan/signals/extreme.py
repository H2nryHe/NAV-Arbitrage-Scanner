from __future__ import annotations

from typing import Any, Dict, Tuple


def detect_extreme(row: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[bool, float, str]:
    z = row.get("pd_zscore_20d")
    pd = row.get("premium_discount_pct")
    z_th = float(cfg["zscore_threshold"])
    pd_th = float(cfg["abs_pd_threshold"])

    if isinstance(z, (int, float)):
        abs_z = abs(float(z))
        return abs_z >= z_th, abs_z, f"zscore={z:.4f} threshold={z_th}"

    if isinstance(pd, (int, float)):
        abs_pd = abs(float(pd))
        return abs_pd >= pd_th, abs_pd / pd_th, f"abs_pd={abs_pd:.4f}% threshold={pd_th}%"

    return False, 0.0, "missing_pd_and_zscore"


from __future__ import annotations

from typing import Optional


def compute_premium_discount_pct(price_close: Optional[float], nav: Optional[float]) -> Optional[float]:
    if price_close is None or nav is None:
        return None
    if nav <= 0:
        return None
    return (price_close / nav - 1.0) * 100.0


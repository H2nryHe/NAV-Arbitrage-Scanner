from __future__ import annotations

from typing import Optional


def compute_dollar_volume(price_close: Optional[float], volume: Optional[float]) -> Optional[float]:
    if price_close is None or volume is None:
        return None
    return price_close * volume


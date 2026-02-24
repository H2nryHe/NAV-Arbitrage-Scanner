from __future__ import annotations

import math
from typing import List, Optional


def rolling_zscore(values: List[Optional[float]], window: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for i in range(len(values)):
        v = values[i]
        if v is None:
            out.append(None)
            continue
        start = i - window + 1
        if start < 0:
            out.append(None)
            continue
        chunk = values[start : i + 1]
        if any(x is None for x in chunk):
            out.append(None)
            continue
        nums = [float(x) for x in chunk if x is not None]
        mean = sum(nums) / window
        var = sum((x - mean) ** 2 for x in nums) / window
        std = math.sqrt(var)
        if std == 0:
            out.append(None)
        else:
            out.append((v - mean) / std)
    return out


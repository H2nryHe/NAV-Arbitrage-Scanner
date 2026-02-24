from __future__ import annotations

import math
from typing import Dict, List, Optional


def estimate_half_life_days(series: List[Optional[float]], min_points: int, max_half_life_days: float) -> Dict[str, object]:
    clean = [float(x) for x in series if isinstance(x, (int, float))]
    if len(clean) < min_points:
        return {"half_life_days": None, "reason": "insufficient_history"}

    x = clean[:-1]
    y = [clean[i + 1] - clean[i] for i in range(len(clean) - 1)]
    n = len(x)
    if n < max(3, min_points - 1):
        return {"half_life_days": None, "reason": "insufficient_regression_points"}

    mean_x = sum(x) / n
    mean_y = sum(y) / n
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    if var_x == 0:
        return {"half_life_days": None, "reason": "zero_variance"}

    cov_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    beta = cov_xy / var_x
    if not math.isfinite(beta):
        return {"half_life_days": None, "reason": "invalid_beta"}
    if beta >= 0:
        return {"half_life_days": None, "reason": "non_mean_reverting_beta"}

    half_life = -math.log(2.0) / beta
    if not math.isfinite(half_life) or half_life <= 0:
        return {"half_life_days": None, "reason": "invalid_half_life"}
    if half_life > max_half_life_days:
        return {"half_life_days": None, "reason": "half_life_too_long"}

    return {"half_life_days": half_life, "reason": "ok"}


from __future__ import annotations

from typing import Any, Dict


def compute_score(row: Dict[str, Any], cfg: Dict[str, Any], extreme_component: float) -> Dict[str, float]:
    w_ext = float(cfg["weight_extreme"])
    w_liq = float(cfg["weight_liquidity"])
    w_hl = float(cfg["weight_half_life"])

    dv = row.get("dollar_volume")
    ref_dv = float(row.get("_liquidity_reference_dv", 1.0))
    liquidity_component = 0.0
    if isinstance(dv, (int, float)) and ref_dv > 0:
        liquidity_component = min(float(dv) / ref_dv, 2.0)

    hl = row.get("half_life_days")
    half_life_component = 0.0
    if isinstance(hl, (int, float)) and hl > 0:
        half_life_component = 1.0 / (1.0 + float(hl))

    penalty = 0.0
    if row.get("nav_staleness_flag"):
        penalty += float(cfg["penalty_nav_stale"])
    if row.get("half_life_days") is None:
        penalty += float(cfg["penalty_half_life_unavailable"])
    if "event_data_partial" in row.get("risk_flags", []):
        penalty += float(cfg["penalty_event_data_partial"])

    score = w_ext * extreme_component + w_liq * liquidity_component + w_hl * half_life_component - penalty
    return {
        "score": score,
        "score_extreme_component": extreme_component,
        "score_liquidity_component": liquidity_component,
        "score_half_life_component": half_life_component,
        "score_penalty": penalty,
    }


from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def _fmt(v: Any) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def build_markdown_report(
    date_str: str,
    top_rows: List[Dict[str, Any]],
    coverage: Dict[str, Any],
    signal_summary: Dict[str, Any],
) -> str:
    lines: List[str] = []
    lines.append(f"# NAVScan Daily Report ({date_str})")
    lines.append("")
    lines.append("## Scan Summary")
    lines.append(f"- Scan date: `{date_str}`")
    lines.append(f"- Universe scored: `{signal_summary.get('universe_count', 0)}`")
    lines.append(f"- Candidates: `{signal_summary.get('candidate_count', 0)}`")
    lines.append("")
    lines.append("## Coverage Summary")
    lines.append(
        f"- Raw: price ok `{coverage.get('raw_price_ok', 0)}`, nav ok `{coverage.get('raw_nav_ok', 0)}`, events ok `{coverage.get('raw_events_ok', 0)}`, metadata ok `{coverage.get('raw_metadata_ok', 0)}`"
    )
    lines.append(
        f"- Silver: records `{coverage.get('silver_records', 0)}`, missing nav `{coverage.get('silver_missing_nav', 0)}`, invalid nav `{coverage.get('silver_invalid_nav', 0)}`"
    )
    lines.append(
        f"- Signals: extreme `{signal_summary.get('extreme_count', 0)}`, liquidity pass `{signal_summary.get('liquidity_pass_count', 0)}`, half-life available `{signal_summary.get('half_life_available_count', 0)}`"
    )
    lines.append("")
    lines.append("## Top Opportunities")
    if not top_rows:
        lines.append("No candidates passed the Stage 3 filters for this date.")
    else:
        lines.append("| Rank | Symbol | PD% | Z20 | Half-life | Dollar Vol | Score | Rationale | Risk Flags |")
        lines.append("|---:|---|---:|---:|---:|---:|---:|---|---|")
        for r in top_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _fmt(r.get("rank")),
                        _fmt(r.get("symbol")),
                        _fmt(r.get("premium_discount_pct")),
                        _fmt(r.get("pd_zscore_20d")),
                        _fmt(r.get("half_life_days")),
                        _fmt(r.get("dollar_volume")),
                        _fmt(r.get("score")),
                        _fmt(r.get("rationale")),
                        _fmt(";".join(r.get("risk_flags", []))),
                    ]
                )
                + " |"
            )
    lines.append("")
    lines.append("## Risk Notes")
    lines.append("- `half_life_unavailable` means insufficient/unstable history for AR(1) fit.")
    lines.append("- `insufficient_history_20d` means 20-day z-score not statistically available.")
    lines.append("- `event_data_partial` indicates event coverage is best-effort, not exhaustive.")
    lines.append("")
    lines.append("## Data Limitations")
    lines.append("- NAV lag can exist versus close price (CEF source timing differences).")
    lines.append("- Event coverage is partial/best-effort and may miss sponsor-level updates.")
    lines.append("- Borrow fee proxy is unavailable in current free-source MVP and not in scoring.")
    lines.append("")
    return "\n".join(lines)


def write_markdown_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


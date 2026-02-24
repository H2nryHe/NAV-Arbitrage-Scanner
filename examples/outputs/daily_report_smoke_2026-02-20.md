# NAVScan Daily Report (2026-02-20)

## Scan Summary
- Scan date: `2026-02-20`
- Universe scored: `1`
- Candidates: `1`

## Coverage Summary
- Raw: price ok `20`, nav ok `20`, events ok `20`, metadata ok `20`
- Silver: records `1`, missing nav `0`, invalid nav `0`
- Signals: extreme `1`, liquidity pass `1`, half-life available `0`

## Top Opportunities
| Rank | Symbol | PD% | Z20 | Half-life | Dollar Vol | Score | Rationale | Risk Flags |
|---:|---|---:|---:|---:|---:|---:|---|---|
| 1 | UTF | -7.1206 | - | - | 14022969.3400 | 1.1252 | extreme:abs_pd=7.1206% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |

## Risk Notes
- `half_life_unavailable` means insufficient/unstable history for AR(1) fit.
- `insufficient_history_20d` means 20-day z-score not statistically available.
- `event_data_partial` indicates event coverage is best-effort, not exhaustive.

## Data Limitations
- NAV lag can exist versus close price (CEF source timing differences).
- Event coverage is partial/best-effort and may miss sponsor-level updates.
- Borrow fee proxy is unavailable in current free-source MVP and not in scoring.

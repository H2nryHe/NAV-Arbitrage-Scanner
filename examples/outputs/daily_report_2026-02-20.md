# NAVScan Daily Report (2026-02-20)

## Scan Summary
- Scan date: `2026-02-20`
- Universe scored: `20`
- Candidates: `9`

## Coverage Summary
- Raw: price ok `20`, nav ok `20`, events ok `20`, metadata ok `20`
- Silver: records `20`, missing nav `0`, invalid nav `0`
- Signals: extreme `15`, liquidity pass `13`, half-life available `0`

## Top Opportunities
| Rank | Symbol | PD% | Z20 | Half-life | Dollar Vol | Score | Rationale | Risk Flags |
|---:|---|---:|---:|---:|---:|---:|---|---|
| 1 | PDI | 11.8919 | - | - | 35372277.9900 | 1.8770 | extreme:abs_pd=11.8919% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |
| 2 | GOF | 8.5791 | - | - | 23762350.3500 | 1.4795 | extreme:abs_pd=8.5791% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |
| 3 | USA | -9.1867 | - | - | 7358113.5300 | 1.1732 | extreme:abs_pd=9.1867% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |
| 4 | ETW | -9.9237 | - | - | 4123269.2800 | 1.1645 | extreme:abs_pd=9.9237% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |
| 5 | UTF | -7.1206 | - | - | 14022969.3400 | 1.1252 | extreme:abs_pd=7.1206% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |
| 6 | QQQX | -9.6448 | - | - | 2222393.1200 | 1.0741 | extreme:abs_pd=9.6448% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |
| 7 | ETV | -7.3155 | - | - | 4480508.1200 | 0.8623 | extreme:abs_pd=7.3155% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |
| 8 | JRI | -7.5352 | - | - | 2817107.1500 | 0.8387 | extreme:abs_pd=7.5352% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |
| 9 | EXG | -5.8537 | - | - | 2644061.4000 | 0.6318 | extreme:abs_pd=5.8537% threshold=5.0%; liquidity:pass; half_life:insufficient_history | half_life_unavailable;insufficient_history_20d;event_data_partial |

## Risk Notes
- `half_life_unavailable` means insufficient/unstable history for AR(1) fit.
- `insufficient_history_20d` means 20-day z-score not statistically available.
- `event_data_partial` indicates event coverage is best-effort, not exhaustive.

## Data Limitations
- NAV lag can exist versus close price (CEF source timing differences).
- Event coverage is partial/best-effort and may miss sponsor-level updates.
- Borrow fee proxy is unavailable in current free-source MVP and not in scoring.

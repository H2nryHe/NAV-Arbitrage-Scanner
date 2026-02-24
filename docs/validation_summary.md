# Validation Summary (MVP, Stage 6)

## Purpose
Provide a basic, reproducible validation snapshot from Stage 5 historical outcomes.
This is not a production backtest.

## Data Snapshot
- Source DB: `data/warehouse/navscan_stage5.sqlite`
- Outcome table: `outcomes`
- Snapshot generated: 2026-02-24
- Horizons: T+1, T+3, T+5

## Aggregate Reversion View
| Horizon | Total Candidates | With Follow-up | Reverted Count | Reverted Rate (on follow-up) | Missing Follow-up |
|---|---:|---:|---:|---:|---:|
| T+1 | 18 | 9 | 3 | 33.33% | 9 |
| T+3 | 18 | 0 | 0 | n/a | 18 |
| T+5 | 18 | 0 | 0 | n/a | 18 |

Raw export:
- `examples/outputs/validation_summary_tplus.csv`

## Example Query (Spec-style)
Question: "How many names from date X top N reverted by date Y?"

Example result:
- Query: `scan_date=2026-02-19`, `top_n=10`, `as_of_date=2026-02-20`
- Output:
  - `candidate_count=9`
  - `reverted_count=3`
  - `with_followup_count=9`
  - `missing_followup_count=0`

Saved example:
- `examples/outputs/query_top10_2026-02-19_to_2026-02-20.txt`

## Interpretation
- Follow-up coverage is currently short-dated; T+3/T+5 are mostly unavailable due limited history.
- Reversion-rate figures are demonstration-level diagnostics only and should not be interpreted as strategy performance claims.

# NAV Arbitrage Scanner (NAVScan)

Local CLI MVP for scanning CEF NAV premium/discount dislocations and producing daily candidate lists with risk notes.

## Overview
NAVScan runs a staged pipeline:
1. Stage 1: fetch raw price/NAV/volume/events/metadata into `data/raw/`
2. Stage 2: standardize to silver schema and compute core fields
3. Stage 3: generate candidates (extreme deviation, half-life-safe logic, filters, ranking)
4. Stage 4: export daily CSV + Markdown report
5. Stage 5: store history and compute T+1/T+3/T+5 reversion outcomes

Current MVP data scope is **CEF-first** (ETF NAV sourcing is documented as limited in free sources).

## Quickstart (macOS M2)
Prerequisites:
- macOS Apple Silicon (M2)
- `python3` (3.11+ recommended)
- `curl`
- `sqlite3`

Run smoke demo (verified in Stage 6):
```bash
cd /Users/linruihe/Local\ Documents/Github/NAV\ Arbitrage\ Scanner
PATH="$PWD/scripts:$PATH" navscan run --date 2026-02-20 --config configs/default.yaml --universe configs/universe_stage6_smoke.yaml --output-dir reports_stage6_smoke
```

Run full universe (slower, network-dependent):
```bash
PATH="$PWD/scripts:$PATH" navscan run --date 2026-02-20 --config configs/default.yaml --universe configs/universe_example.yaml --output-dir reports --verbose
```

Run tests:
```bash
PYTHONPATH=. python3 -m unittest tests/test_formulas.py tests/test_half_life.py tests/test_pipeline_smoke.py
```

Optional Stage 5 tracking update/query:
```bash
python3 scripts/stage5_track.py update --db data/warehouse/navscan_stage5.sqlite --signals-root data/gold/signals --silver-root data/silver --horizons 1,3,5 --verbose
python3 scripts/stage5_track.py query --db data/warehouse/navscan_stage5.sqlite --scan-date 2026-02-19 --top-n 10 --as-of-date 2026-02-20
```

## CLI Usage
Primary command:
```bash
navscan run --date YYYY-MM-DD [--config configs/default.yaml] [--universe configs/universe_example.yaml] [--output-dir reports] [--verbose]
```

Exit codes:
- `0`: success with candidates
- `1`: partial success (pipeline completed but no candidates)
- `2`: failure (invalid input or stage failure)

## Example Outputs
From demo date `2026-02-20`:
- CSV: `reports/date=2026-02-20/top_opportunities.csv`
- Markdown: `reports/date=2026-02-20/daily_report.md`
- Frozen examples for review:
  - `examples/outputs/top_opportunities_2026-02-20.csv`
  - `examples/outputs/daily_report_2026-02-20.md`
  - `examples/outputs/validation_summary_tplus.csv`

## Data Source Limitations (MVP)
- NAV timing/staleness: CEF NAV can lag price date; lag is flagged and called out in reports.
- Event coverage: best-effort only; distribution/rebalance coverage is incomplete.
- Borrow fee: reliable free borrow-fee proxy is unavailable; field remains unavailable in scoring.
- ETF NAV: free-source reliability/consistency is weaker than CEF in this repo's tested flow.

See:
- `docs/methodology.md`
- `docs/limitations.md`
- `docs/risk_notes.md`
- `docs/data_sources.md`
- `docs/validation_summary.md`

## Non-Investment-Advice Disclaimer
This project is for research and engineering demonstration only. It is **not investment advice**, not an execution system, and does not account for full trading frictions, taxes, legal constraints, or suitability.

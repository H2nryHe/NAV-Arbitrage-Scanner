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

## Quickstart

Prereqs: Python 3.11+, curl, sqlite3

### 1) clone & enter repo
```bash
git clone https://github.com/H2nryHe/NAV-Arbitrage-Scanner.git
cd NAV-Arbitrage-Scanner
```

### 2) create venv
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

### 3) install deps (pick ONE)
#### Option A: if you have requirements.txt
```bash
python -m pip install -r requirements.txt
```
#### Option B: minimal deps (if you don’t have requirements.txt yet)
```bash
python -m pip install pandas numpy pyyaml requests python-dateutil
```

### 4) run (use repo-relative PATH, not absolute path)
```bash
export PATH="$PWD/scripts:$PATH"
navscan run --date 2026-02-20 \
  --config configs/default.yaml \
  --universe configs/universe_stage6_smoke.yaml \
  --output-dir reports_stage6_smoke
```

### 5) unit tests
```bash
PYTHONPATH=. python -m unittest \
  tests/test_formulas.py \
  tests/test_half_life.py \
  tests/test_pipeline_smoke.py
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


## Results snapshot (frozen example)

From demo date `2026-02-20` (see `examples/outputs/`):

- Top candidates: `examples/outputs/top_opportunities_2026-02-20.csv`
- Daily report: `examples/outputs/daily_report_2026-02-20.md`
- Reversion validation (T+1/T+3/T+5): `examples/outputs/validation_summary_tplus.csv`


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


Interpretation:
- This tool is **relative value**, not true “risk-free arbitrage”. It ranks **extreme discount dislocations** and flags NAV staleness / liquidity / basic risk notes.
- Stage 5 tracking records forward discount moves to quantify reversion behavior and avoid “pretty backtests”.


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

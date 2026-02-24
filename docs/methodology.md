# Methodology (MVP)

## Scope
This document describes the implemented MVP logic through Stage 5.

## Pipeline
1. Raw ingestion (`scripts/stage1_ingest.py`):
   - Fetches price/volume, NAV, events (best-effort), metadata
   - Writes source-traceable raw records into `data/raw/`
2. Standardization (`scripts/stage2_build_silver.py`):
   - Builds daily silver snapshots in `data/silver/`
   - Applies validation flags (e.g., missing/invalid NAV, insufficient history)
3. Signals (`scripts/stage3_build_candidates.py`):
   - Detects extreme dislocations
   - Applies liquidity and event-aware filters
   - Computes ranking score and rationale/risk flags
4. Reporting (`navscan run` Stage 4):
   - Produces CSV and Markdown daily outputs
5. Tracking (`scripts/stage5_track.py`):
   - Stores snapshots/candidates/outcomes idempotently
   - Computes directional reversion outcomes (T+1/T+3/T+5)

## Core Formulas
- `premium_discount_pct = (price_close / nav - 1) * 100`
- `dollar_volume = price_close * volume`

Rolling z-score:
- Implemented as configurable rolling window (default 20-day).
- If history is insufficient, value remains null and receives explicit flag (no silent fill).

## Half-Life Logic
Implemented via AR(1)-style regression on spread change (`delta = y - x`) with safe degradation:
- Returns null with reason when:
  - insufficient history
  - zero variance
  - non-mean-reverting beta
  - invalid/too-long half-life
- This avoids misleading numeric outputs when fit conditions are not valid.

## Candidate Selection and Ranking
Signals are threshold-driven from config (`configs/stage3_signals.json`):
- Extreme deviation (z-score if available; fallback to abs premium/discount threshold)
- Liquidity filter (minimum dollar volume)
- Event filter (best-effort)
- Risk flags attached per row
- Transparent score components stored in output rows

Each final candidate includes:
- `rationale`
- `risk_flags`

## Stage 5 Outcome Definition
Directional reversion for horizon H:
- Compare candidate `abs(pd_scan)` vs `abs(pd_target_at_H)`
- Mark reverted when `abs(pd_target) < abs(pd_scan)`

Explicit statuses include:
- `ok`
- `missing_followup_data`
- `missing_scan_pd`
- `zero_scan_pd`

## Reproducibility Notes
- Same-date reruns preserve output structure.
- Historical writes are idempotent by primary keys and upsert behavior.
- Data-source updates can still cause value-level drift across reruns.

# Stage 1 Raw Ingestion Contract

## Output layout

Raw outputs are written as newline-delimited JSON (`ndjson`):

- `data/raw/price_volume/date=YYYY-MM-DD/source=stooq_daily_csv/snapshot.ndjson`
- `data/raw/nav/date=YYYY-MM-DD/source=cefconnect_api_v3_pricinghistory/snapshot.ndjson`
- `data/raw/events/date=YYYY-MM-DD/source=cefconnect_api_v3_distributionhistory/snapshot.ndjson`
- `data/raw/metadata/date=YYYY-MM-DD/source=cefconnect_api_v3_dailypricing/snapshot.ndjson`
- `data/raw/run_summaries/date=YYYY-MM-DD.json`

## Common record envelope

Each `ndjson` row preserves traceability:

- `stage` (always `stage1_raw`)
- `dataset`
- `source`
- `fetch_timestamp_utc`
- `requested_date`
- `symbol`
- `status` (`ok` / `error` / `skipped`)
- `reason` (error or fallback detail)
- `raw` (original source fields, unstandardized)
- `raw_context` (dataset-specific context when relevant)

## Notes

- No Stage 2 mapping/standardization is applied in Stage 1.
- `raw` keeps upstream field names (e.g., `Date`, `Close`, `Volume`, `NAVData`, `DataDateDisplay`, `ExDivDateDisplay`).
- A record can be `ok` with `reason=used_previous_nav_date` for NAV if same-day NAV is unavailable but prior NAV is found.


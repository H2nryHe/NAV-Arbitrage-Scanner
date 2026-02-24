# Limitations

## Data Coverage Limits
- Current MVP is CEF-first; ETF NAV sourcing was not validated to the same reliability level in free endpoints.
- Event coverage is best-effort and not guaranteed complete for all symbols/dates.
- Borrow fee proxy is not reliably available from free, unified sources in this implementation.

## Timing and Staleness
- NAV and market close price can have different publication times.
- Some rows use prior-date NAV when same-date NAV is unavailable; this can distort apparent premium/discount extremity.

## Statistical Limits
- Early history windows often produce insufficient data for 20-day z-score and half-life.
- Half-life is intentionally null when fit assumptions fail.

## Execution Reality Gap
- Candidate outputs are research signals, not executable trade instructions.
- No slippage model, bid/ask spread model, borrow locate confirmation, or capacity model is included.

## Operational Limits
- Pipeline depends on external web endpoints and may degrade with source changes or throttling.
- Same-date reruns can differ at value level when upstream data revisions occur.

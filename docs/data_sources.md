# Stage 0 Data Sources (Feasibility)

## Scope and test date
- Execution date: 2026-02-23 (America/Los_Angeles run context)
- Snapshot date tested: 2026-02-20
- Universe tested: 20 symbols (`configs/universe_example.yaml`)
- Coverage artifact: `data/feasibility/coverage_2026-02-20.csv`

## Candidate source matrix

| Source | Asset coverage | Fields observed | Update frequency (observed) | Pros | Cons / limitations | Stage 0 conclusion |
|---|---|---|---|---|---|---|
| CEFConnect `api/v3/DailyPricing` | CEF universe (broad US-listed CEF set) | `Ticker`, `Price`, `NAV`, `LastUpdated`, `NAVPublished`, `AverageVolume` | Daily market close style snapshots | Free, no key, direct CEF premium/discount workflow, includes NAV publish timestamp | No confirmed same-day traded `volume` field (only `AverageVolume`), ETF coverage not broad/unified | **Primary source for CEF `price` + `NAV` + NAV staleness flags** |
| Stooq daily CSV (`q/d/l`) | Broad US tickers incl CEF/ETF | `Date`, `OHLC`, `Volume` | Daily bars | Free, no key, easy symbol-level daily volume | No NAV field; close may not exactly match other sources | **Primary source for `volume` (and fallback `price`)** |
| CEFConnect `api/v3/distributionhistory/fund/...` | CEF | Distribution history (`ExDivDateDisplay`, `PayDateDisplay`, totals/components) | Historical/event-driven | Free and directly tied to CEF funds | No ETF rebalance events; coverage semantics depend on sponsor reporting | **Usable for CEF distribution event flags (best-effort)** |
| Yahoo quote API (`query1.finance.yahoo.com`) | ETF/CEF broad in principle | Would provide quote fields if available | Near-real-time in principle | Broad symbol universe | In Stage 0 checks returned HTTP 429 (`Edge: Too Many Requests`) repeatedly, unstable for unattended local pipeline | **Not reliable as primary free source in this environment** |
| Sponsor ETF pages/files (iShares/State Street/etc.) | ETF only, provider-specific | NAV/iNAV varies by provider | Varies | Official sponsor data | Fragmented formats, non-unified, often fund-family-specific; high maintenance for MVP | **Not selected for Stage 1-4 MVP** |

## Measured Stage 0 coverage (real check)

Source combination used:
- `price_close`, `nav`: CEFConnect DailyPricing
- `volume`: Stooq daily CSV

Result on `2026-02-20`:
- Universe size: 20
- Symbols with `price_close`: 20
- Symbols with `nav`: 20
- Symbols with `volume`: 20
- Symbols with all three: 20
- `premium_discount_pct` computable: 20

Observed NAV timing/staleness on this universe:
- 13/20 symbols had `NAVPublished` earlier than `LastUpdated` (1-day stale NAV risk on snapshot day).

## Borrow fee proxy feasibility

Conclusion: **Unavailable from robust free unified sources for this MVP scope**.

Notes:
- Reliable borrow fee / short availability typically comes from broker prime data or paid datasets.
- Public free sources are inconsistent, stale, or missing for the required cross-symbol daily workflow.

Strategy impact:
- `borrow_fee_proxy` must be nullable in schema and explicitly flagged in outputs.
- Premium/discount signals cannot be interpreted as directly shortable alpha without external borrow data.

## Event data feasibility

- CEF distributions: feasible via CEFConnect distribution history endpoint.
- ETF rebalance events: no unified free API validated in Stage 0; considered unavailable for MVP automation.

Strategy impact:
- Stage 1-4 should implement CEF distribution event flags only (best-effort).
- ETF rebalance filtering should remain disabled or manual until a stable source is added.

## ETF vs CEF NAV timing/staleness notes

- CEF NAV is typically end-of-day and often published with a lag; `NAVPublished` should be stored and compared to price date (`nav_staleness_flag`).
- ETF “NAV-like” concepts differ (official NAV, iNAV/IOPV, sponsor estimates) and are provider-specific, making cross-ETF normalization fragile for MVP.
- With current free-source reliability, a mixed CEF+ETF pipeline risks false comparability.

Recommendation:
- **CEF-only MVP for Stages 1-4**.
- Re-introduce ETFs only after selecting a stable, unified ETF NAV methodology and validating history consistency.


# Stage Checklist (Execution Record)

## Stage 0 — 数据源可行性验证（Feasibility First）
- Status: PASS
- Execution Date: 2026-02-23
- Owner: Implementation Agent
- Spec Reference: `PROJECT_SPEC.md` §9 Stage 0

### Goal
确认 `price / nav / volume` 获取可行性，并明确 `borrow fee / events` 限制与降级方案。

### Inputs
- Universe file: `configs/universe_example.yaml`
- Candidate sources:
  - CEFConnect DailyPricing / distributionhistory
  - Stooq daily CSV
  - Yahoo quote API (viability probe)
- Date(s) tested: `2026-02-20`

### Commands Run
```bash
sed -n '1,260p' PROJECT_SPEC.md
sed -n '1,260p' TASK_BOARD.md
sed -n '1,260p' STAGE_CHECKLIST.md

curl -i --max-time 10 'https://query1.finance.yahoo.com/v7/finance/quote?symbols=SPY,QQQ'
curl -sL --max-time 20 'https://www.cefconnect.com/api/v3/pricinghistory/UTF/5D'
curl -sL --max-time 20 'https://www.cefconnect.com/api/v3/DailyPricing?props=Ticker,Price,NAV,LastUpdated,NAVPublished,Volume,AverageVolume,Cusip/'
curl -sL --max-time 20 'https://www.cefconnect.com/api/v3/distributionhistory/fund/UTF/02-22-2025/02-22-2026'
curl -sL --max-time 10 'https://stooq.com/q/d/l/?s=spy.us&i=d'

python3 scripts/source_feasibility.py --universe configs/universe_example.yaml --output-dir data/feasibility
```

### Artifacts Produced
- `docs/data_sources.md`
- `configs/universe_example.yaml`
- `scripts/source_feasibility.py`
- `data/feasibility/coverage_2026-02-20.csv`
- `data/feasibility/summary_2026-02-20.json`

### Coverage / Quality Summary
- Universe size: 20
- Symbols with price: 20
- Symbols with NAV: 20
- Symbols with volume: 20
- Symbols with all three: 20
- `premium_discount_pct` computable count: 20
- ETF coverage notes:
  - Yahoo quote endpoint returned HTTP 429 during checks.
  - CEFConnect is CEF-focused and not a unified ETF NAV source.
- CEF coverage notes:
  - CEFConnect + Stooq combination achieved 20/20 for required Stage 0 fields.
  - 13/20 had `NAVPublished < LastUpdated` (NAV staleness risk).
- Borrow fee proxy availability: unavailable from reliable free unified data.
- Event data availability:
  - CEF distributions available via CEFConnect distribution history endpoint.
  - ETF rebalance events not validated as unified free source.

### Gate Check
- [x] 至少 20 个标的可获取 `price_close`, `nav`, `volume`
- [x] `premium_discount_pct` 可计算
- [x] `borrow_fee_proxy` 不可得时限制已明确
- [x] ETF/CEF NAV 时间口径差异风险已记录

### Manual Spot Checks (3–5 rows)
- UTF / 2026-02-20 / price 26.87 / nav 28.93 / volume 521882
- PDI / 2026-02-20 / price 18.63 / nav 16.65 / volume 1898673
- GOF / 2026-02-20 / price 12.15 / nav 11.17 / volume 1955749
- EOS / 2026-02-20 / price 21.99 / nav 23.39 / volume 76633
- ETY / 2026-02-20 / price 14.92 / nav 15.33 / volume 137861

### Deviations from Plan
- Universe uses CEF-only MVP set (no ETF in initial 20) due free ETF NAV source instability/non-unified format.

### Decisions Made
- Decision: Use CEF-only MVP for Stages 1-4.
- Reason: CEF sources provided validated coverage; ETF NAV sourcing is fragmented/unreliable in free endpoints tested.
- Impact: Stage 1+ fetch/standardize pipelines should target CEF first; ETF support postponed.

- Decision: Treat borrow fee proxy as unavailable in MVP.
- Reason: No reliable free unified borrow fee feed validated.
- Impact: add nullable field + risk disclosure in reports/signals.

### Known Issues / Risks
- CEF NAV may be stale vs price date (observed on majority of sample symbols).
- Cross-source price/volume mixing (CEFConnect + Stooq) can introduce minor reconciliation drift.
- Yahoo free endpoint rate limits make it unsuitable for deterministic pipeline runs.

### Next Stage Entry Criteria
- [x] 确定 Stage 1 使用的数据源列表
- [x] 确定 raw schema 最小字段
- [x] universe 冻结（至少 MVP 版本）

### Attachments / Evidence
- logs path: terminal command logs from this run
- coverage csv path: `data/feasibility/coverage_2026-02-20.csv`
- summary path: `data/feasibility/summary_2026-02-20.json`

## Stage 1 — 数据抓取管道（Raw / Bronze）
- Status: PASS
- Execution Date: 2026-02-23
- Owner: Implementation Agent
- Spec Reference: `PROJECT_SPEC.md` §9 Stage 1

### Goal
建立每日可重复运行的数据抓取流程，原始数据落盘到 `data/raw/`，并保留 source 与抓取时间。

### Inputs
- Universe file: `configs/universe_example.yaml`
- Source config:
  - price/volume: Stooq daily CSV
  - nav: CEFConnect `api/v3/pricinghistory/{symbol}/{period}`
  - events: CEFConnect `api/v3/distributionhistory/fund/{symbol}/{start}/{end}`
  - metadata: CEFConnect `api/v3/DailyPricing`
- Scan date(s): `2026-02-19`, `2026-02-20`

### Commands Run
```bash
python3 scripts/stage1_ingest.py --dates 2026-02-19,2026-02-20 --universe configs/universe_example.yaml --raw-root data/raw --verbose
python3 scripts/stage1_ingest.py --dates 2026-02-20 --universe configs/universe_example.yaml --raw-root data/raw --verbose

# single-symbol failure resilience smoke test
cat > configs/universe_stage1_failure_test.yaml <<'EOF'
version: 1
symbols:
  - UTF
  - BADSYM
EOF
python3 scripts/stage1_ingest.py --dates 2026-02-20 --universe configs/universe_stage1_failure_test.yaml --raw-root data/raw_smoke --verbose
```

### Artifacts Produced
- `scripts/stage1_ingest.py`
- `navscan/logging_utils.py`
- `navscan/data/fetchers/common.py`
- `navscan/data/fetchers/price_volume.py`
- `navscan/data/fetchers/nav.py`
- `navscan/data/fetchers/events.py`
- `navscan/data/fetchers/metadata.py`
- `docs/raw_ingestion_contract.md`
- `data/raw/price_volume/date=2026-02-19/source=stooq_daily_csv/snapshot.ndjson`
- `data/raw/price_volume/date=2026-02-20/source=stooq_daily_csv/snapshot.ndjson`
- `data/raw/nav/date=2026-02-19/source=cefconnect_api_v3_pricinghistory/snapshot.ndjson`
- `data/raw/nav/date=2026-02-20/source=cefconnect_api_v3_pricinghistory/snapshot.ndjson`
- `data/raw/events/date=2026-02-19/source=cefconnect_api_v3_distributionhistory/snapshot.ndjson`
- `data/raw/events/date=2026-02-20/source=cefconnect_api_v3_distributionhistory/snapshot.ndjson`
- `data/raw/metadata/date=2026-02-19/source=cefconnect_api_v3_dailypricing/snapshot.ndjson`
- `data/raw/metadata/date=2026-02-20/source=cefconnect_api_v3_dailypricing/snapshot.ndjson`
- `data/raw/run_summaries/date=2026-02-19.json`
- `data/raw/run_summaries/date=2026-02-20.json`

### Coverage / Quality Summary
- Price records (main universe): 20/20 both dates
- NAV records (main universe): 20/20 both dates
  - 2026-02-20 contains 13 records with fallback flag `reason=used_previous_nav_date`
- Event records (best-effort): 20/20 request success both dates (some symbols have empty `raw` list)
- Metadata records (universe symbols): 20/20; outside-universe rows are marked `skipped`
- Failed symbols count: 0 on main universe run
- Retry/timeout: enabled via shared HTTP helper (`curl --max-time`, 3-attempt retry with backoff)
- Warning count / Error count:
  - main universe: no `error` rows in run summary
  - resilience smoke test: `BADSYM` generated per-source warnings while run completed

### Gate Check
- [x] 同一日期重复抓取流程可完成
- [x] 单 symbol 失败不会阻断整体
- [x] raw 层保留 `source` 与 `fetch_timestamp`
- [x] raw 输出结构满足 Stage 2 标准化输入要求

### Manual Spot Checks (3–5 rows)
- Raw prices row sample: `UTF` on 2026-02-20 has raw `Date/Open/High/Low/Close/Volume`
- Raw nav row sample: `PDI` on 2026-02-20 has `DataDate=2026-02-19` and `reason=used_previous_nav_date`
- Raw events row sample: `PDI` on 2026-02-20 has distribution row with `ExDivDateDisplay=2/12/2026`
- Raw metadata row sample: `UTF` includes `CategoryId`, `CategoryName`, `Cusip`, `DistributionRateNAV`

### Deviations from Plan
- `events` and `metadata` implemented as best-effort source coverage (as allowed by spec).
- CEF-only universe carried forward from Stage 0 decision.

### Decisions Made
- Decision: NAV fetch uses exact-date first, then latest prior NAV fallback.
- Reason: improve raw coverage while preserving staleness traceability.
- Impact: Stage 2 must treat fallback NAV as stale/quality-flagged when computing features.

### Known Issues / Risks
- CEFConnect NAV can lag price date; fallback rows require explicit downstream quality handling.
- Metadata endpoint returns many non-universe rows; ingestion marks them `skipped` for traceability.
- Event endpoint availability is source-dependent and may return empty arrays for some symbols/windows.

### Next Stage Entry Criteria
- [x] raw schema frozen (MVP envelope + dataset-specific raw payload)
- [x] Stage 2 mapping inputs documented (`docs/raw_ingestion_contract.md`)
- [x] At least 1–2 days raw samples available in `data/raw/`

### Attachments / Evidence
- logs path: terminal output from `scripts/stage1_ingest.py` runs
- sample raw files: `data/raw/*/date=2026-02-19/*/snapshot.ndjson`, `data/raw/*/date=2026-02-20/*/snapshot.ndjson`
- run summary output: `data/raw/run_summaries/date=2026-02-19.json`, `data/raw/run_summaries/date=2026-02-20.json`

## Stage 2 — 标准化与特征工程（Silver）
- Status: PASS
- Execution Date: 2026-02-23
- Owner: Implementation Agent
- Spec Reference: `PROJECT_SPEC.md` §9 Stage 2

### Goal
标准化 Stage 1 raw 数据并计算基础特征：`premium_discount_pct`, `dollar_volume`, rolling z-score。

### Inputs
- Raw dates: `2026-02-19`, `2026-02-20`
- Raw paths:
  - `data/raw/price_volume/date=YYYY-MM-DD/...`
  - `data/raw/nav/date=YYYY-MM-DD/...`
  - `data/raw/events/date=YYYY-MM-DD/...`
  - `data/raw/metadata/date=YYYY-MM-DD/...`
- Universe: `configs/universe_example.yaml`
- z-score window: 20

### Commands Run
```bash
python3 scripts/stage2_build_silver.py --raw-root data/raw --silver-root data/silver --universe configs/universe_example.yaml --zscore-window 20 --verbose
PYTHONPATH=. python3 -m unittest tests/test_formulas.py
```

### Artifacts Produced
- `scripts/stage2_build_silver.py`
- `navscan/pipeline/standardize.py`
- `navscan/pipeline/validate.py`
- `navscan/features/premium_discount.py`
- `navscan/features/liquidity.py`
- `navscan/features/statistics.py`
- `tests/test_formulas.py`
- `data/silver/date=2026-02-19/snapshot.ndjson`
- `data/silver/date=2026-02-20/snapshot.ndjson`
- `data/silver/all_dates.ndjson`
- `data/silver/run_summary.json`

### Coverage / Quality Summary
- Silver records: 40 total (20 symbols × 2 dates)
- Missing `price_close`: 0
- Missing `nav`: 0
- Invalid NAV (`<=0`): 0
- Missing `volume`: 0
- `premium_discount_pct` computed: 40/40
- `dollar_volume` computed: 40/40
- `pd_zscore_20d` non-null: 0/40 (expected: insufficient history for 20-day window)
- `insufficient_history_20d` flags: 40/40

### Gate Check
- [x] 抽查 5 个样本公式正确
- [x] 输出包含必备字段
- [x] 缺失值处理可追溯（日志/flag）
- [x] 核心单元测试通过

### Manual Spot Checks (3–5 rows)
- UTF / 2026-02-19: `price_close=26.61`, `nav=28.71`, `premium_discount_pct=-7.314524555903867`, `volume=334899`, `dollar_volume=8911662.39`
- PDI / 2026-02-20: `price_close=18.63`, `nav=16.65`, `premium_discount_pct=11.891891891891904`, `volume=1898673`, `dollar_volume=35372277.989999995`
- GOF / 2026-02-20: `price_close=12.15`, `nav=11.19`, `premium_discount_pct=8.579088471849872`, `volume=1955749`, `dollar_volume=23762350.35`
- EOS / 2026-02-20: `price_close=21.99`, `nav=23.58`, `premium_discount_pct=-6.743002544529264`, `volume=76633`, `dollar_volume=1685159.67`
- ETW / 2026-02-19: `pd_zscore_20d=null`, `data_quality_flags=['insufficient_history_20d']`

### Deviations from Plan
- 20-day z-score is configured and computed, but history length (2 days) is insufficient, so z-score remains null with explicit flags.

### Decisions Made
- Decision: No silent filling for missing/insufficient history values.
- Reason: preserve data-quality transparency for downstream logic.
- Impact: Stage 3 must read `data_quality_flags` when consuming `pd_zscore_20d`.

### Known Issues / Risks
- Current raw history is too short for meaningful 20-day z-score.
- `distribution_event_flag` is exact-date based and currently all false on sampled dates.
- `rebalance_event_flag` remains unavailable in CEF-only MVP data scope.

### Next Stage Entry Criteria
- [x] Silver schema frozen for MVP-required fields
- [x] Core formulas tested (`premium_discount_pct`, `dollar_volume`)
- [x] Quality flags available for missing/invalid/insufficient-history handling

### Attachments / Evidence
- silver outputs: `data/silver/date=2026-02-19/snapshot.ndjson`, `data/silver/date=2026-02-20/snapshot.ndjson`
- summary output: `data/silver/run_summary.json`
- tests output: `PYTHONPATH=. python3 -m unittest tests/test_formulas.py` (pass)

## Stage 3 — 信号引擎（Extreme + Half-life + Filters）
- Status: PASS
- Execution Date: 2026-02-23
- Owner: Implementation Agent
- Spec Reference: `PROJECT_SPEC.md` §9 Stage 3

### Goal
基于 Silver 数据生成可解释、可排序的候选列表，并附带风险标签。

### Inputs
- Silver data:
  - `data/silver/date=2026-02-20/snapshot.ndjson`
  - `data/silver/all_dates.ndjson`
- Signal config: `configs/stage3_signals.json`
- Candidate date: `2026-02-20`

### Commands Run
```bash
python3 scripts/stage3_build_candidates.py --silver-root data/silver --output-root data/gold/signals --config configs/stage3_signals.json --date 2026-02-20 --verbose
PYTHONPATH=. python3 -m unittest tests/test_half_life.py
```

### Artifacts Produced
- `configs/stage3_signals.json`
- `scripts/stage3_build_candidates.py`
- `navscan/signals/extreme.py`
- `navscan/signals/mean_reversion.py`
- `navscan/signals/filters.py`
- `navscan/signals/risk_flags.py`
- `navscan/signals/rank.py`
- `tests/test_half_life.py`
- `data/gold/signals/date=2026-02-20/scored_universe.ndjson`
- `data/gold/signals/date=2026-02-20/candidates_ranked.ndjson`
- `data/gold/signals/date=2026-02-20/summary.json`

### Coverage / Quality Summary
- Universe scored: 20
- Extreme triggered: 15
- Liquidity pass: 13
- Event blocked: 0
- Final candidates: 9
- Half-life available: 0
  - all symbols flagged with `half_life_reason=insufficient_history` (safe degradation)

### Gate Check
- [x] 候选清单非空（合理 universe 下）
- [x] 每条候选有 `rationale`
- [x] 每条候选有 `risk_flags`
- [x] half-life 异常不输出误导值
- [x] 阈值配置化

### Manual Spot Checks (3–5 rows)
- Rank 1 `PDI`: score `1.8770`, rationale `extreme:abs_pd=11.8919% threshold=5.0%; liquidity:pass; half_life:insufficient_history`, risk flags `['half_life_unavailable','insufficient_history_20d','event_data_partial']`
- Rank 2 `GOF`: score `1.4795`, rationale includes extreme + liquidity + half-life reason, risk flags present
- Rank 3 `USA`: score `1.1732`, rationale includes extreme + liquidity + half-life reason, risk flags present
- Rank 4 `ETW`: score `1.1645`, rationale includes extreme + liquidity + half-life reason, risk flags present
- Rank 5 `UTF`: score `1.1252`, rationale includes extreme + liquidity + half-life reason, risk flags present

### Deviations from Plan
- z-score threshold logic is implemented but current history is insufficient, so extreme detection falls back to abs PD threshold on this sample date.

### Decisions Made
- Decision: Use fallback extreme logic (`abs_pd_threshold`) when z-score is unavailable.
- Reason: maintain usable candidate generation under short history while preserving traceability.
- Impact: Stage 4 output should annotate when fallback mode drives candidate selection.

### Known Issues / Risks
- Half-life unavailable for all current symbols due insufficient history; candidates carry `half_life_unavailable` risk.
- Event coverage is best-effort; marked with `event_data_partial` risk flag for transparency.
- Ranking quality will improve after longer silver history enables z-score and half-life coverage.

### Next Stage Entry Criteria
- [x] Stage 4 can consume ranked candidates from `data/gold/signals/...`
- [x] Candidate rows include `rationale` and `risk_flags`
- [x] Scoring components are explicit (`score_extreme_component`, `score_liquidity_component`, `score_half_life_component`, `score_penalty`)

### Attachments / Evidence
- ranked candidates: `data/gold/signals/date=2026-02-20/candidates_ranked.ndjson`
- scored universe: `data/gold/signals/date=2026-02-20/scored_universe.ndjson`
- run summary: `data/gold/signals/date=2026-02-20/summary.json`
- half-life tests: `PYTHONPATH=. python3 -m unittest tests/test_half_life.py` (pass)

## Stage 4 — CLI 串联 + 报表输出（MVP）
- Status: PASS
- Execution Date: 2026-02-23
- Owner: Implementation Agent
- Spec Reference: `PROJECT_SPEC.md` §9 Stage 4

### Goal
通过 `navscan run --date YYYY-MM-DD` 串联 Stage 1–4，并生成 CSV + Markdown 日报输出。

### Inputs
- Date: `2026-02-20`
- Config: `configs/default.yaml`
- Universe: `configs/universe_example.yaml`
- Stage 3 signal config: `configs/stage3_signals.json`

### Commands Run
```bash
# main MVP command
PATH="$PWD/scripts:$PATH" navscan run --date 2026-02-20 --config configs/default.yaml --universe configs/universe_example.yaml --output-dir reports --verbose

# repeat-run structure check
PATH="$PWD/scripts:$PATH" navscan run --date 2026-02-20 --config configs/default.yaml --universe configs/universe_example.yaml --output-dir reports

# invalid input error + exit code check
PATH="$PWD/scripts:$PATH" navscan run --date 2026-2-20 --config configs/default.yaml --universe configs/universe_example.yaml --output-dir reports

# no-candidate behavior check (strict thresholds)
PATH="$PWD/scripts:$PATH" navscan run --date 2026-02-20 --config configs/default_no_candidates.yaml --universe configs/universe_example.yaml --output-dir reports_no_candidates
```

### Artifacts Produced
- `navscan/cli.py`
- `scripts/navscan`
- `configs/default.yaml`
- `navscan/reporting/csv_export.py`
- `navscan/reporting/markdown_report.py`
- `reports/date=2026-02-20/top_opportunities.csv`
- `reports/date=2026-02-20/daily_report.md`
- `reports_no_candidates/date=2026-02-20/top_opportunities.csv`
- `reports_no_candidates/date=2026-02-20/daily_report.md`

### Coverage / Quality Summary
- Main run (`2026-02-20`):
  - candidates exported: 9
  - CSV generated: yes
  - Markdown generated: yes
- No-candidate run:
  - candidates exported: 0
  - report still generated with explanation line
  - CLI returned partial-success exit code (`1`)

### Gate Check
- [x] `navscan run --date YYYY-MM-DD` 可执行成功
- [x] CSV + Markdown 文件生成
- [x] 同日重复运行结构一致
- [x] CLI 错误提示清晰
- [x] 退出码符合规范

### Manual Spot Checks (3–5 rows)
- `reports/date=2026-02-20/top_opportunities.csv` contains ranked candidate rows with score/rationale/risk flags.
- `reports/date=2026-02-20/daily_report.md` includes scan date, coverage summary, top opportunities table, risk notes, and data limitation notes.
- Invalid date input `2026-2-20` returns clear error: `error: --date must be YYYY-MM-DD` and exit code `2`.
- No-candidate report (`reports_no_candidates/.../daily_report.md`) includes: `No candidates passed the Stage 3 filters for this date.`

### Deviations from Plan
- CLI implementation uses argparse and subprocess orchestration to reuse Stage 1–3 scripts, rather than rewriting pipeline internals in one module.

### Decisions Made
- Decision: use `0/1/2` exit-code policy directly in CLI:
  - `0` normal success with candidates
  - `1` partial success (no candidates but artifacts generated)
  - `2` hard failure/invalid input
- Reason: align with spec while keeping behavior explicit and testable.
- Impact: downstream automation can branch on exit codes consistently.

### Known Issues / Risks
- `run` currently depends on subprocess calls to stage scripts; interface drift across scripts would require synchronized updates.
- Execution time is bounded by upstream network calls in Stage 1.
- Event and borrow data limitations remain and are surfaced in report text.

### Next Stage Entry Criteria
- [x] CLI run command stable for MVP flow
- [x] CSV + Markdown artifacts generated from one command
- [x] Error and partial-success behaviors validated

### Attachments / Evidence
- main CSV: `reports/date=2026-02-20/top_opportunities.csv`
- main Markdown: `reports/date=2026-02-20/daily_report.md`
- no-candidate CSV: `reports_no_candidates/date=2026-02-20/top_opportunities.csv`
- no-candidate Markdown: `reports_no_candidates/date=2026-02-20/daily_report.md`

## Stage 5 — 历史跟踪与回归监控
- Status: PASS
- Execution Date: 2026-02-23
- Owner: Implementation Agent
- Spec Reference: `PROJECT_SPEC.md` §9 Stage 5

### Goal
实现候选历史持久化与方向性回归跟踪，支持基本查询：某日 Top N 到某日有多少回归。

### Inputs
- Signals candidates:
  - `data/gold/signals/date=2026-02-19/candidates_ranked.ndjson`
  - `data/gold/signals/date=2026-02-20/candidates_ranked.ndjson`
- Silver snapshots:
  - `data/silver/date=2026-02-19/snapshot.ndjson`
  - `data/silver/date=2026-02-20/snapshot.ndjson`
- DB path: `data/warehouse/navscan_stage5.sqlite`
- Horizons: `1,3,5`

### Commands Run
```bash
# ensure a second scan date exists for follow-up demonstration
PATH="$PWD/scripts:$PATH" navscan run --date 2026-02-19 --config configs/default.yaml --universe configs/universe_example.yaml --output-dir reports --verbose

# stage 5 update + query
python3 scripts/stage5_track.py update --db data/warehouse/navscan_stage5.sqlite --signals-root data/gold/signals --silver-root data/silver --horizons 1,3,5 --verbose
python3 scripts/stage5_track.py query --db data/warehouse/navscan_stage5.sqlite --scan-date 2026-02-19 --top-n 5 --as-of-date 2026-02-20
python3 scripts/stage5_track.py query --db data/warehouse/navscan_stage5.sqlite --scan-date 2026-02-20 --top-n 5 --as-of-date 2026-02-24

# idempotence check (rerun update and compare row counts)
python3 scripts/stage5_track.py update --db data/warehouse/navscan_stage5.sqlite --signals-root data/gold/signals --silver-root data/silver --horizons 1,3,5 --verbose
```

### Artifacts Produced
- `scripts/stage5_track.py`
- `navscan/tracking/store.py`
- `navscan/tracking/outcomes.py`
- `navscan/tracking/queries.py`
- `data/warehouse/navscan_stage5.sqlite`

### Coverage / Quality Summary
- Snapshots stored: 40 (`20 symbols x 2 dates`)
- Candidates stored: 18 (`9 per scan date`)
- Outcomes stored: 54 (`18 candidates x 3 horizons`, idempotent upsert)
- Outcome statuses:
  - `ok`: 9
  - `missing_followup_data`: 45
  - `zero_scan_pd`: 0

### Gate Check
- [x] 能回答某天 Top N 到某天有多少回归
- [x] rerun/backfill 不产生重复记录
- [x] 有主键或去重逻辑
- [x] 缺口数据有明确标记

### Manual Spot Checks (3–5 rows)
- Query (`scan_date=2026-02-19`, `top_n=5`, `as_of=2026-02-20`):
  - `candidate_count=5`, `reverted_count=2`, `with_followup_count=5`, `missing_followup_count=0`
- Query (`scan_date=2026-02-20`, `top_n=5`, `as_of=2026-02-24`):
  - `candidate_count=5`, `reverted_count=0`, `with_followup_count=0`, `missing_followup_count=5`
- Idempotence row counts before and after rerun:
  - `snapshots=40`, `candidates=18`, `outcomes=54` (unchanged)

### Deviations from Plan
- 存储采用 SQLite（DuckDB 等价实现）以满足本地零依赖与幂等 upsert 需求。

### Decisions Made
- Decision: directional reversion defined as `abs(pd_target) < abs(pd_scan)` on follow-up dates.
- Reason: MVP 需简单、可解释、可查询。
- Impact: 后续可扩展为更复杂的路径/速度指标，但当前输出保持透明。

### Known Issues / Risks
- 当前仅有两天银层数据，T+3/T+5 大多为 `missing_followup_data`。
- 数据修订会通过 upsert 覆盖历史行；如需审计版本演进，后续应增加版本表。
- 回归定义为方向性绝对收敛，不包含交易成本/滑点/可交易性约束。

### Next Stage Entry Criteria
- [x] 历史存储可幂等更新
- [x] outcome 计算可运行并可查询
- [x] 缺口数据有显式状态标记

### Attachments / Evidence
- DB file: `data/warehouse/navscan_stage5.sqlite`
- tracking update summary: terminal output from `scripts/stage5_track.py update`
- query outputs:
  - `scripts/stage5_track.py query --scan-date 2026-02-19 --top-n 5 --as-of-date 2026-02-20`
  - `scripts/stage5_track.py query --scan-date 2026-02-20 --top-n 5 --as-of-date 2026-02-24`

## Stage 6 — 验证 / 文档 / 发布质量
- Status: PASS
- Execution Date: 2026-02-24
- Owner: Implementation Agent
- Spec Reference: `PROJECT_SPEC.md` §9 Stage 6

### Goal
提高仓库复现性与展示质量：补齐 README / 方法文档 / 限制与风险说明 / 示例产物 / 基础验证统计，并验证关键测试与 demo 命令可运行。

### Precondition Check
- Stage 5 status in this file: PASS
- Stage 5 gate items: all checked
- Result: Stage 6 allowed to execute

### Inputs
- Spec/task docs:
  - `PROJECT_SPEC.md`
  - `TASK_BOARD.md`
  - `docs/stage_checklist.md`
- Existing outputs:
  - `reports/date=2026-02-20/*`
  - `data/warehouse/navscan_stage5.sqlite`

### Commands Run
```bash
# required-doc pre-read
cat PROJECT_SPEC.md
cat TASK_BOARD.md
cat docs/stage_checklist.md

# validation summary extract + query evidence
sqlite3 -header -csv data/warehouse/navscan_stage5.sqlite \
  "select horizon_days, count(*) as total_candidates, sum(case when status='ok' then 1 else 0 end) as with_followup, sum(case when reverted_flag=1 then 1 else 0 end) as reverted_count, round(100.0 * sum(case when reverted_flag=1 then 1 else 0 end) / nullif(sum(case when status='ok' then 1 else 0 end),0), 2) as reverted_rate_pct, sum(case when status='missing_followup_data' then 1 else 0 end) as missing_followup from outcomes group by horizon_days order by horizon_days;" > examples/outputs/validation_summary_tplus.csv
python3 scripts/stage5_track.py query --db data/warehouse/navscan_stage5.sqlite --scan-date 2026-02-19 --top-n 10 --as-of-date 2026-02-20 > examples/outputs/query_top10_2026-02-19_to_2026-02-20.txt

# tests
PYTHONPATH=. python3 -m unittest tests/test_formulas.py tests/test_half_life.py tests/test_pipeline_smoke.py

# demo run
PATH="$PWD/scripts:$PATH" navscan run --date 2026-02-20 --config configs/default.yaml --universe configs/universe_stage6_smoke.yaml --output-dir reports_stage6_smoke
```

### Artifacts Produced
- `README.md`
- `docs/methodology.md`
- `docs/limitations.md`
- `docs/risk_notes.md`
- `docs/validation_summary.md`
- `configs/universe_stage6_smoke.yaml`
- `tests/test_pipeline_smoke.py`
- `examples/outputs/top_opportunities_2026-02-20.csv`
- `examples/outputs/daily_report_2026-02-20.md`
- `examples/outputs/top_opportunities_smoke_2026-02-20.csv`
- `examples/outputs/daily_report_smoke_2026-02-20.md`
- `examples/outputs/validation_summary_tplus.csv`
- `examples/outputs/query_top10_2026-02-19_to_2026-02-20.txt`

### Basic Validation Summary (T+ horizon)
From `examples/outputs/validation_summary_tplus.csv`:
- T+1: total 18, with_followup 9, reverted 3, reverted_rate 33.33%, missing_followup 9
- T+3: total 18, with_followup 0, reverted 0, missing_followup 18
- T+5: total 18, with_followup 0, reverted 0, missing_followup 18

### Gate Check
- [x] README 可指导新用户在 Mac M2 跑 demo
- [x] 核心公式/half-life 有测试
- [x] 限制说明清楚且不夸大
- [x] 文档、代码结构、输出示例一致

### Manual Spot Checks (3–5 items)
- `README.md` quickstart command matches actual entrypoint `scripts/navscan` and tested smoke universe.
- `docs/limitations.md` explicitly covers NAV lag, event incompleteness, borrow-fee unavailability.
- `docs/risk_notes.md` explicitly covers execution/slippage/liquidity and structure risks.
- `examples/outputs/daily_report_smoke_2026-02-20.md` and CSV exist and are generated by demo command.
- Unit/integration tests pass: 9 tests total.

### Deviations from Plan
- No Stage 6 strategy logic redesign; only documentation/validation/testing/reproducibility improvements.

### Decisions Made
- Decision: Add a repo-tracked smoke universe (`configs/universe_stage6_smoke.yaml`) for reproducible quickstart.
- Reason: full universe runtime depends more heavily on network latency; smoke run provides deterministic demo path.
- Impact: demo instructions remain runnable while full-universe command is still documented.

### Known Issues / Risks
- Validation sample remains short; T+3/T+5 mostly missing follow-up coverage.
- Full-universe daily run remains dependent on external endpoint stability/throttling.
- MVP still CEF-first; ETF NAV support remains a documented limitation.

### Next Stage Entry Criteria
- [x] Stage 6 gates complete and documented
- [x] Repo has runnable docs, tests, and examples for interview/demo use

### Attachments / Evidence
- smoke run outputs:
  - `reports_stage6_smoke/date=2026-02-20/top_opportunities.csv`
  - `reports_stage6_smoke/date=2026-02-20/daily_report.md`
- validation exports:
  - `examples/outputs/validation_summary_tplus.csv`
  - `examples/outputs/query_top10_2026-02-19_to_2026-02-20.txt`

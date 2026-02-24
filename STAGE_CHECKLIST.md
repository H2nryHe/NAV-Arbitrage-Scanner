# STAGE_CHECKLIST.md

# NAV Arbitrage Scanner — Stage Checklist（阶段验收记录模板）

> 用途：记录每个 Stage 的**实际执行情况、命令、产出、Gate 验收、偏差与决策**。  
> 这不是任务计划表；任务拆解请看 `TASK_BOARD.md`。

## 使用说明
- 每完成一个 Stage，就填写对应章节（保留历史记录，不覆盖）。
- 如果 Stage 未通过，保留失败记录并写明 blocker / next action。
- 命令、输出文件、样本截图路径要尽量可复现。
- 关键阈值或降级策略必须写入 **Decisions Made**。

---

## 全局信息（可选）

- Project: NAV Arbitrage Scanner（CEF/ETF NAV premium-discount）
- Repo branch:
- Agent / Operator:
- Environment:
  - OS: macOS (M2)
  - Python:
  - Run date timezone: America/Los_Angeles
- Config file:
- Universe file:

---

## Stage 模板（复制用于新增 Stage）
```md
## Stage X — [名称]
- Status: PASS / FAIL / PARTIAL
- Execution Date:
- Owner:
- Spec Reference: PROJECT_SPEC.md §[section]

### Goal
[本阶段目标]

### Inputs
- [输入文件/配置/日期范围]
- [数据源]

### Commands Run
```bash
# 命令 1
# 命令 2
```

### Artifacts Produced
- path/to/file1
- path/to/file2

### Coverage / Quality Summary
- Universe size:
- Records fetched:
- NAV coverage:
- Missing field summary:
- Warning count / Error count:

### Gate Check
- [ ] Gate item 1
- [ ] Gate item 2
- [ ] Gate item 3

### Manual Spot Checks (3–5 rows)
- Sample 1:
- Sample 2:
- Sample 3:

### Deviations from Plan
- [与 TASK_BOARD 或 PROJECT_SPEC 不一致的地方]

### Decisions Made
- Decision:
- Reason:
- Impact:

### Known Issues / Risks
- [问题 1]
- [问题 2]

### Next Stage Entry Criteria
- [进入下一阶段前必须满足条件]

### Attachments / Evidence
- report path:
- screenshot path:
- logs path:
```

---

## Stage 0 — 数据源可行性验证（Feasibility First）

- Status:
- Execution Date:
- Owner:
- Spec Reference: PROJECT_SPEC.md §9 Stage 0

### Goal
确认 `price / nav / volume` 获取可行性，并明确 `borrow fee / events` 限制与降级方案。

### Inputs
- Universe file:
- Candidate sources:
- Date(s) tested:

### Commands Run
```bash
# Example
# python scripts/source_feasibility.py --date 2026-02-22 --universe configs/universe_example.yaml
```

### Artifacts Produced
- `docs/data_sources.md`
- `configs/universe_example.yaml`
- 可行性脚本/Notebook:
- 覆盖率结果文件:

### Coverage / Quality Summary
- Universe size:
- Symbols with price:
- Symbols with NAV:
- Symbols with volume:
- Symbols with all three:
- `premium_discount_pct` computable count:
- ETF coverage notes:
- CEF coverage notes:
- Borrow fee proxy availability:
- Event data availability:

### Gate Check
- [ ] 至少 20 个标的可获取 `price_close`, `nav`, `volume`
- [ ] `premium_discount_pct` 可计算
- [ ] `borrow_fee_proxy` 不可得时限制已明确
- [ ] ETF/CEF NAV 时间口径差异风险已记录

### Manual Spot Checks (3–5 rows)
- Symbol / date / price / nav / volume:
- Symbol / date / price / nav / volume:
- Symbol / date / price / nav / volume:

### Deviations from Plan
- 

### Decisions Made
- Decision:
- Reason:
- Impact:

### Known Issues / Risks
- 
- 

### Next Stage Entry Criteria
- [ ] 确定 Stage 1 使用的数据源列表
- [ ] 确定 raw schema 最小字段
- [ ] universe 冻结（至少 MVP 版本）

### Attachments / Evidence
- logs path:
- notebook path:
- coverage csv path:

---

## Stage 1 — 数据抓取管道（Raw / Bronze）

- Status:
- Execution Date:
- Owner:
- Spec Reference: PROJECT_SPEC.md §9 Stage 1

### Goal
建立每日可重复运行的数据抓取流程，原始数据落盘到 `data/raw/`，并保留 source 与抓取时间。

### Inputs
- Universe file:
- Source config:
- Scan date(s):

### Commands Run
```bash
# Example
# navscan run --date 2026-02-22 --verbose   # (if CLI already exists)
# python scripts/fetch_snapshot.py --date 2026-02-22
```

### Artifacts Produced
- `data/raw/prices/date=YYYY-MM-DD/...`
- `data/raw/nav/date=YYYY-MM-DD/...`
- `data/raw/events/date=YYYY-MM-DD/...` (optional)
- `data/raw/metadata/...` (optional)
- logs:

### Coverage / Quality Summary
- Price records:
- NAV records:
- Event records:
- Metadata records:
- Failed symbols count:
- Retry count:
- Warning count / Error count:

### Gate Check
- [ ] 同一日期重复抓取流程可完成
- [ ] 单 symbol 失败不会阻断整体
- [ ] raw 层保留 `source` 与 `fetch_timestamp`
- [ ] raw 输出结构满足 Stage 2 标准化输入要求

### Manual Spot Checks (3–5 rows)
- Raw prices row sample:
- Raw nav row sample:
- Raw events row sample (if any):

### Deviations from Plan
- 

### Decisions Made
- Decision:
- Reason:
- Impact:

### Known Issues / Risks
- 
- 

### Next Stage Entry Criteria
- [ ] raw schema 冻结（MVP）
- [ ] Stage 2 字段映射表完成
- [ ] 至少 1–2 天 raw 样例可用

### Attachments / Evidence
- logs path:
- sample raw files:
- run summary output:

---

## Stage 2 — 标准化与特征工程（Silver）

- Status:
- Execution Date:
- Owner:
- Spec Reference: PROJECT_SPEC.md §9 Stage 2

### Goal
标准化 raw 数据并计算基础特征：`premium_discount_pct`, `dollar_volume`, rolling z-score。

### Inputs
- `data/raw/` dates:
- Metadata availability:
- History window length:

### Commands Run
```bash
# Example
# python scripts/build_silver.py --date 2026-02-22
# pytest tests/test_formulas.py -q
```

### Artifacts Produced
- `data/silver/date=YYYY-MM-DD/...`
- `tests/test_formulas.py` results
- validation logs / quality report:

### Coverage / Quality Summary
- Silver records:
- Valid `premium_discount_pct` count:
- Missing NAV count:
- Invalid NAV (`<=0`) count:
- Missing volume count:
- `dollar_volume` valid count:
- z-score available count:
- insufficient_history count:

### Gate Check
- [ ] 抽查 5 个样本 `premium_discount_pct` 公式正确
- [ ] 输出表包含 Stage 2 必备字段
- [ ] 缺失值策略通过日志或 flags 可追溯
- [ ] 核心公式单元测试通过

### Manual Spot Checks (3–5 rows)
- Sample 1: verify `premium_discount_pct`
- Sample 2: verify `dollar_volume`
- Sample 3: verify z-score window behavior
- Sample 4:
- Sample 5:

### Deviations from Plan
- 

### Decisions Made
- Decision:
- Reason:
- Impact:

### Known Issues / Risks
- 
- 

### Next Stage Entry Criteria
- [ ] Stage 3 可直接读取 silver schema
- [ ] zscore 窗口与阈值配置化
- [ ] data quality flags 字段冻结（MVP）

### Attachments / Evidence
- silver sample path:
- test output path:
- validation report path:

---

## Stage 3 — 信号引擎（Extreme + Half-life + Filters）

- Status:
- Execution Date:
- Owner:
- Spec Reference: PROJECT_SPEC.md §9 Stage 3

### Goal
生成可解释候选名单，包含偏离信号、half-life、过滤、风险标签与排序。

### Inputs
- Silver dataset dates:
- Config thresholds:
- Event mode (`strict|best_effort|off`):

### Commands Run
```bash
# Example
# python scripts/build_signals.py --date 2026-02-22
# pytest tests/test_half_life.py -q
```

### Artifacts Produced
- candidate intermediate table:
- ranked opportunities table:
- half-life diagnostics / logs:
- risk flags output:

### Coverage / Quality Summary
- Candidate count before filters:
- Candidate count after liquidity filter:
- Candidate count after event filter:
- Final ranked count:
- half-life computed count:
- half-life missing count:
- half-life unreliable count:
- Risk flag frequencies:

### Gate Check
- [ ] 候选清单非空（合理 universe 条件下）
- [ ] 每条候选有 `rationale`
- [ ] 每条候选有 `risk_flags`
- [ ] half-life 异常情况降级处理正确
- [ ] 阈值来自配置而非硬编码

### Manual Spot Checks (3–5 rows)
- Candidate 1:
  - Why selected:
  - Risk flags:
  - half-life sanity check:
- Candidate 2:
- Candidate 3:

### Deviations from Plan
- 

### Decisions Made
- Decision:
- Reason:
- Impact:

### Known Issues / Risks
- 
- 

### Next Stage Entry Criteria
- [ ] 输出字段满足 Stage 4 报表模板
- [ ] 评分字段与排序规则冻结（MVP）
- [ ] 无候选时的降级行为明确

### Attachments / Evidence
- candidates csv path:
- diagnostics path:
- test output path:

---

## Stage 4 — CLI 串联与日报输出（MVP）

- Status:
- Execution Date:
- Owner:
- Spec Reference: PROJECT_SPEC.md §9 Stage 4

### Goal
通过 `navscan run --date YYYY-MM-DD` 串联全流程，生成 CSV + Markdown 日报。

### Inputs
- CLI config:
- Date(s):
- Universe file:

### Commands Run
```bash
# Example
# navscan run --date 2026-02-22 --config configs/default.yaml --verbose
```

### Artifacts Produced
- `reports/top_opportunities_YYYY-MM-DD.csv`
- `reports/top_opportunities_YYYY-MM-DD.md`
- CLI stdout/stderr logs
- run summary (exit code)

### Coverage / Quality Summary
- Runtime duration:
- Universe size:
- Records fetched / standardized:
- Final top count:
- Warning count / Error count:
- Exit code:

### Gate Check
- [ ] `navscan run --date YYYY-MM-DD` 成功执行
- [ ] CSV + Markdown 文件生成
- [ ] 同日重复运行结构一致
- [ ] 日期格式错误/空 universe 有明确报错
- [ ] 退出码符合规范（0/1/2）

### Manual Spot Checks (3–5 rows)
- Report row 1 fields complete:
- Report row 2 rationale/risk flags sensible:
- Markdown risk section present:
- Data limitation note present:

### Deviations from Plan
- 

### Decisions Made
- Decision:
- Reason:
- Impact:

### Known Issues / Risks
- 
- 

### Next Stage Entry Criteria
- [ ] 历史存储格式确定（Stage 5）
- [ ] 报表 schema 冻结（MVP）
- [ ] 输出路径与命名规范冻结

### Attachments / Evidence
- report paths:
- logs path:
- stdout capture:

---

## Stage 5 — 历史跟踪与回归监控

- Status:
- Execution Date:
- Owner:
- Spec Reference: PROJECT_SPEC.md §9 Stage 5

### Goal
记录每日候选并跟踪后续回归（T+1/T+3/T+5），支持基础监控问题查询。

### Inputs
- Historical reports/snapshots:
- Warehouse path:
- Follow-up horizon(s):

### Commands Run
```bash
# Example
# navscan backfill --start 2026-01-01 --end 2026-02-22
# python scripts/update_outcomes.py --as-of 2026-02-22
```

### Artifacts Produced
- `data/warehouse/navscan.duckdb` (or equivalent)
- tracking tables / outcome tables
- status update report section (optional)

### Coverage / Quality Summary
- Historical dates loaded:
- Candidate records stored:
- Deduplicated rows:
- Outcome rows computed:
- Missing follow-up data count:
- Query sanity check result:

### Gate Check
- [ ] 能回答“某天 Top N 到某天有多少回归”
- [ ] rerun/backfill 不产生重复记录
- [ ] 主键或去重逻辑有效
- [ ] 缺口数据有明确标记（`missing_followup_data` 等）

### Manual Spot Checks (3–5 rows)
- Tracking row sample 1:
- Tracking row sample 2:
- Outcome direction sanity check:
- Duplicate prevention sanity check:

### Deviations from Plan
- 

### Decisions Made
- Decision:
- Reason:
- Impact:

### Known Issues / Risks
- 
- 

### Next Stage Entry Criteria
- [ ] 基础验证统计所需字段齐全
- [ ] 历史库结构与 README 描述一致
- [ ] 数据修订策略已说明

### Attachments / Evidence
- warehouse schema dump:
- query output snippet:
- logs path:

---

## Stage 6 — 验证 / 文档 / 发布质量

- Status:
- Execution Date:
- Owner:
- Spec Reference: PROJECT_SPEC.md §9 Stage 6

### Goal
补全文档、测试、示例输出与基础验证，使 repo 可复现、可展示、可面试讲述。

### Inputs
- All prior stage outputs
- README draft
- Example reports

### Commands Run
```bash
# Example
# pytest -q
# navscan run --date 2026-02-22
# python scripts/validation_summary.py
```

### Artifacts Produced
- `README.md`
- `docs/methodology.md`
- `docs/limitations.md`
- `docs/risk_notes.md`
- `examples/outputs/...`
- validation summary tables/plots (optional)

### Coverage / Quality Summary
- Tests passed / failed:
- Demo run success:
- Example outputs present:
- Validation summary generated:
- Docs completion status:

### Gate Check
- [ ] README 可指导新用户在 Mac M2 跑 demo
- [ ] 核心公式 / half-life 有测试
- [ ] 限制说明清楚且不夸大
- [ ] 文档、代码结构、示例输出一致
- [ ] 非投资建议免责声明已出现

### Manual Spot Checks (3–5 rows)
- README quickstart verified:
- Example report opens correctly:
- Limitation note mentions NAV lag / borrow / events:
- Test command reproducible:

### Deviations from Plan
- 

### Decisions Made
- Decision:
- Reason:
- Impact:

### Known Issues / Risks
- 
- 

### Final Release Readiness
- [ ] MVP DoD 满足（PROJECT_SPEC.md §16）
- [ ] 标签/版本号确定（可选）
- [ ] 后续 roadmap 已更新

### Attachments / Evidence
- README path:
- examples paths:
- test output:
- validation summary path:

---

## 变更日志（Checklist 文件本身）
- [ ] 初始化模板创建
- [ ] Stage 0 首次填写
- [ ] Stage 1 首次填写
- [ ] Stage 2 首次填写
- [ ] Stage 3 首次填写
- [ ] Stage 4 首次填写
- [ ] Stage 5 首次填写
- [ ] Stage 6 首次填写

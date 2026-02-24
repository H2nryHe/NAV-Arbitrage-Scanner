# PROJECT_SPEC.md

# NAV Arbitrage Scanner（CEF / ETF NAV Premium-Discount）项目规格（Agent 执行版）

## 1. 项目定位

构建一个**像 desk 日常工具**的本地 CLI 项目：  
每天抓取 CEF / ETF 的价格与 NAV，计算 premium/discount 偏离，筛选极端机会，结合均值回归速度（half-life）、流动性与事件过滤，输出 **Top opportunities 清单 + 风险提示**。

### 核心使用方式（目标）
```bash
navscan run --date YYYY-MM-DD
```

### 目标用户
- Quant researcher / trader / PM / desk analyst
- 需要“每日监控 + 每日名单 + 历史跟踪”的研究型工具用户

---

## 2. 项目目标（MVP）

### 必须实现（MVP）
1. **每日抓取数据**
   - `price`
   - `NAV`
   - `premium_discount`
   - `volume`
   - `borrow-fee proxy`（若无法获取必须明确限制）
2. **信号生成**
   - 极端偏离（绝对值 / z-score）
   - 回归速度（half-life）
   - 流动性过滤
   - 事件过滤（distribution / rebalance，允许部分覆盖但必须标注）
3. **输出报告**
   - Top opportunities 清单
   - 风险提示（流动性、杠杆、费用、跳价风险等）
4. **CLI**
   - `navscan run --date YYYY-MM-DD`
5. **可重复运行**
   - 同一日期重复运行可得到稳定结果（允许上游数据源微小差异）

### 非目标（MVP 不做）
- 自动下单 / 执行交易
- 完整实时撮合/盘口微观结构系统
- 严格生产级回测引擎
- 依赖付费 prime/券源系统作为唯一数据源

---

## 3. 运行环境与约束

### 3.1 本地环境（必须兼容）
- OS: macOS（Apple Silicon, M2）
- Python: 3.11+（建议）
- 本地运行，不依赖云服务

### 3.2 数据约束（必须透明）
- 免费数据源可能存在：
  - NAV 更新滞后
  - 覆盖不全
  - 事件数据不完整
  - 无法获取真实 borrow fee
- 对于不可得字段，必须：
  1. 在代码中显式置空或打标记
  2. 在文档中说明限制
  3. 在报告中提示风险影响

---

## 4. Agent 执行原则（必须遵守）

1. **阶段化推进**：按 Stage 顺序执行；每阶段必须通过验收（Gate）后进入下一阶段。
2. **先可用再增强**：优先做 MVP；不要在 Stage 0/1 过度设计。
3. **数据可追溯**：原始数据必须落盘（raw/bronze）；不能只保留最终结果。
4. **失败可诊断**：日志必须说明失败源（source / symbol / field）。
5. **限制透明**：不要假装事件/borrow 数据完整。
6. **输出可解释**：候选标的必须有“入选原因 + 风险标签”。
7. **幂等性优先**：同日期重复跑不会导致历史数据重复污染。
8. **CLI 优先**：notebook 可用于调试，但不是主入口。

---

## 5. 高层架构（MVP）

```text
Data Sources
   ├─ Price/Volume
   ├─ NAV
   ├─ Events (optional/partial)
   └─ Metadata (expense/leverage/category)
        ↓
[Fetchers]  -> raw (bronze)
        ↓
[Standardize + Validate] -> silver
        ↓
[Features] (pd, zscore, adv, half-life inputs)
        ↓
[Signals + Filters + Ranking]
        ↓
[Reports + Tracking]
        ↓
CLI: navscan run --date YYYY-MM-DD
```

---

## 6. 数据模型（MVP 字段规范）

### 6.1 必备字段（每日快照）
- `date` (YYYY-MM-DD)
- `symbol`
- `asset_type` (`CEF` / `ETF`)
- `price_close`
- `nav`
- `premium_discount_pct` = `(price_close / nav - 1) * 100`
- `volume`
- `dollar_volume`

### 6.2 建议字段（强烈建议）
- `price_time`
- `nav_time`
- `nav_staleness_flag`
- `expense_ratio`
- `leverage_flag`
- `category`
- `distribution_event_flag`
- `rebalance_event_flag`

### 6.3 可选字段（拿不到必须说明）
- `borrow_fee_proxy`
- `shortability_flag`
- `spread_proxy`

### 6.4 输出字段（Top opportunities）
- `date`
- `symbol`
- `asset_type`
- `price_close`
- `nav`
- `premium_discount_pct`
- `pd_zscore_20d`（或 60d）
- `half_life_days`
- `dollar_volume`
- `event_flags`
- `risk_flags`
- `score`
- `rationale`（一行解释）
- `data_quality_flags`

---

## 7. 目录结构（建议，Agent 可直接创建）

```text
repo_root/
├─ PROJECT_SPEC.md
├─ README.md
├─ pyproject.toml
├─ .gitignore
├─ configs/
│  ├─ default.yaml
│  └─ universe_example.yaml
├─ navscan/
│  ├─ __init__.py
│  ├─ cli.py
│  ├─ config.py
│  ├─ logging_utils.py
│  ├─ data/
│  │  ├─ io.py
│  │  ├─ schemas.py
│  │  ├─ fetchers/
│  │  │  ├─ price.py
│  │  │  ├─ nav.py
│  │  │  ├─ events.py
│  │  │  └─ metadata.py
│  ├─ pipeline/
│  │  ├─ standardize.py
│  │  ├─ validate.py
│  │  └─ run_pipeline.py
│  ├─ features/
│  │  ├─ premium_discount.py
│  │  ├─ liquidity.py
│  │  ├─ mean_reversion.py
│  │  └─ build_features.py
│  ├─ signals/
│  │  ├─ extreme.py
│  │  ├─ filters.py
│  │  ├─ rank.py
│  │  └─ risk_flags.py
│  ├─ reporting/
│  │  ├─ tables.py
│  │  ├─ markdown_report.py
│  │  └─ csv_export.py
│  └─ tracking/
│     ├─ store.py
│     ├─ outcomes.py
│     └─ performance.py
├─ data/                # runtime data (gitignored)
│  ├─ raw/
│  ├─ silver/
│  ├─ gold/
│  └─ warehouse/
├─ reports/             # generated reports
├─ examples/
│  └─ outputs/
├─ tests/
│  ├─ test_formulas.py
│  ├─ test_half_life.py
│  ├─ test_pipeline.py
│  └─ fixtures/
└─ docs/
   ├─ data_sources.md
   ├─ methodology.md
   ├─ limitations.md
   └─ stage_checklist.md
```

---

## 8. CLI 规范（MVP）

### 8.1 必需命令
#### `navscan run --date YYYY-MM-DD`
执行完整流程（fetch → standardize → features → signals → report → tracking）

### 参数（MVP）
- `--date YYYY-MM-DD`：扫描日期（必填）
- `--config PATH`：配置文件（默认 `configs/default.yaml`)
- `--universe PATH`：标的列表文件（可覆盖配置）
- `--output-dir PATH`：输出目录
- `--verbose`：详细日志

### 8.2 建议命令（v1）
- `navscan backfill --start YYYY-MM-DD --end YYYY-MM-DD`
- `navscan report --date YYYY-MM-DD`
- `navscan validate --date YYYY-MM-DD`
- `navscan universe check`

### 8.3 CLI 退出码
- `0`: 成功
- `1`: 部分成功（有 warning，但产出结果）
- `2`: 失败（关键数据缺失 / pipeline 中断）

---

## 9. 分阶段执行计划（Agent 任务分解 + Gate）

> 每个 Stage 必须记录到 `docs/stage_checklist.md`：执行日期、命令、输入、输出、结果、已知问题、是否通过。

### Stage 0 — 数据源可行性验证（Feasibility First）

**目标**  
确认核心字段可获得，尤其 `NAV` 与 `price` 的匹配可行性。若 borrow fee / 事件不可得，明确替代方案与限制。

**输出（Deliverables）**
- `docs/data_sources.md`
- `configs/universe_example.yaml`
- 可行性脚本或 notebook
- 覆盖率汇总（至少 1 日快照）

**Gate**
- [ ] 至少 20 个标的可获取 `price_close`, `nav`, `volume`
- [ ] 可以计算 `premium_discount_pct`
- [ ] 对 `borrow_fee_proxy` 不可得时有明确说明
- [ ] 明确 ETF/CEF NAV 时间口径差异风险

**失败处理**
- NAV 覆盖率过低时更换或增加数据源
- ETF NAV 困难时，MVP 可先只做 CEF（必须写入文档）

---

### Stage 1 — 数据抓取管道（Raw / Bronze）

**目标**  
建立每日可重复运行的数据抓取，并把原始数据落盘到 `data/raw/`。

**输出（Deliverables）**
- `navscan/data/fetchers/` 模块
- `data/raw/` 样例数据（至少 1–2 天）
- 日志输出（含 source/symbol/failure reason）

**Gate**
- [ ] 同一日期重复抓取流程可完成
- [ ] 单标的失败不会阻断整体
- [ ] `raw` 层可追溯 source 与抓取时间
- [ ] 输出结构满足后续标准化需要

---

### Stage 2 — 标准化与特征工程（Silver）

**目标**  
把 raw 数据转成统一 schema，并计算基础指标（pd、zscore、流动性）。

**必须实现**
- `premium_discount_pct`
- `dollar_volume`
- 至少一种 rolling zscore（如 20d）

**Gate**
- [ ] 抽查 5 个样本公式正确
- [ ] 输出表包含必备字段
- [ ] 缺失值处理策略显式记录
- [ ] 核心公式单元测试通过

---

### Stage 3 — 信号引擎（极端偏离 + Half-life + 过滤）

**目标**  
生成可用候选名单，而非仅计算指标。

**必须实现**
- 极端偏离（阈值可配置）
- half-life（异常值需降级处理）
- 流动性过滤
- 事件过滤（best effort）
- 风险标签
- 排序/评分

**Gate**
- [ ] 候选清单非空（合理 universe 条件下）
- [ ] 每条候选有 `rationale`
- [ ] 每条候选有 `risk_flags`
- [ ] half-life 异常情形处理正确
- [ ] 阈值配置化

---

### Stage 4 — 报表输出与 CLI 串联（MVP 可运行）

**目标**  
一条命令跑通整条链路并生成日报输出。

**输出**
- `top_opportunities_YYYY-MM-DD.csv`
- `top_opportunities_YYYY-MM-DD.md`

**Gate**
- [ ] `navscan run --date YYYY-MM-DD` 可执行成功
- [ ] CSV + Markdown 文件生成
- [ ] 同日重复运行结构一致
- [ ] CLI 错误输入有明确报错
- [ ] 退出码行为符合规范

---

### Stage 5 — 历史跟踪与回归监控

**目标**  
支持对历史候选进行回归跟踪（T+1/T+3/T+5）。

**Gate**
- [ ] 能回答“某天 Top 10 到某天有多少回归”
- [ ] rerun/backfill 不产生重复记录
- [ ] 历史库有主键/去重逻辑

---

### Stage 6 — 验证、文档与发布质量

**目标**  
让 repo 具备面试展示和复现实用价值。

**Gate**
- [ ] README 可指导新用户在 Mac M2 跑 demo
- [ ] 核心公式/half-life 有测试
- [ ] 限制说明清楚且不夸大
- [ ] 文档、代码结构、输出示例一致

---

## 10. 测试与验证规范（Agent 必须执行）

### 10.1 单元测试（至少）
- `premium_discount_pct`
- `dollar_volume`
- z-score（窗口足够/不足）
- half-life 异常情况处理

### 10.2 集成测试（建议）
- 用 mock/raw 样例跑通端到端小样本流程

### 10.3 手工抽查（必须）
每阶段至少抽查 3–5 条记录，确认：
- 字段意义正确
- 单位正确
- 时间口径合理

---

## 11. 配置规范（MVP 示例字段）

`configs/default.yaml` 应至少支持：

```yaml
run:
  timezone: "America/Los_Angeles"
  output_dir: "reports"
  raw_dir: "data/raw"
  silver_dir: "data/silver"
  warehouse_path: "data/warehouse/navscan.duckdb"

universe:
  path: "configs/universe_example.yaml"

signals:
  zscore_window: 20
  zscore_threshold: 2.0
  min_dollar_volume: 1000000
  min_price: 5.0

filters:
  enable_liquidity: true
  enable_events: true
  enable_risk_flags: true

events:
  mode: "best_effort"   # strict | best_effort | off

ranking:
  top_n: 20

report:
  export_csv: true
  export_markdown: true
  include_data_limitations: true
```

---

## 12. 日志与错误处理规范（必须）

### 日志等级
- `INFO`: 正常流程摘要
- `WARNING`: 单标的缺失/降级处理
- `ERROR`: 当前阶段无法继续
- `DEBUG`: 可选详细诊断

### 错误处理原则
- 局部失败不阻断整体（单 symbol 失败）
- 关键依赖失败必须停止（如 NAV 全部不可得）
- 每个 warning/error 包含：
  - `stage`
  - `source`
  - `symbol`（如适用）
  - `reason`

---

## 13. 风险与限制（必须在报告和文档中体现）

1. **NAV 时滞风险**
2. **事件覆盖不完整**
3. **borrow 数据缺失**
4. **执行风险（滑点、跳价、低流动性）**
5. **基金结构风险（如杠杆 CEF）**
6. **费用与税务因素**

> 所有输出必须附带“非投资建议”免责声明。

---

## 14. Agent 交付格式要求（每个 Stage）

每个 Stage 结束时提交：
1. **Stage Summary**
2. **Artifacts**
3. **Run Commands**
4. **Gate Check**
5. **Known Issues**
6. **Next Stage Plan**

---

## 15. 开发优先级（强制顺序）

1. Stage 0（可行性）
2. Stage 1（抓取 raw）
3. Stage 2（标准化 + 基础特征）
4. Stage 3（信号 + 过滤 + 风险标签）
5. Stage 4（CLI 串联 + 报表）
6. Stage 5（历史跟踪）
7. Stage 6（验证 + 文档 + 发布）

> 不允许在 Stage 0 未通过时提前实现复杂评分/回测。

---

## 16. 最终验收（项目级 DoD）

当且仅当满足以下条件，项目视为 MVP 完成：
- [ ] `navscan run --date YYYY-MM-DD` 可在 Mac M2 本地运行
- [ ] 输出 Top opportunities CSV + Markdown
- [ ] 候选包含入选原因与风险标签
- [ ] 数据限制（borrow/events/NAV lag）透明说明
- [ ] 至少支持一组可运行的 universe 示例
- [ ] 核心公式/half-life 有测试
- [ ] README 可指导他人运行 demo
- [ ] 历史跟踪（至少基础版本）可回答“是否回归”

---

## 17. 后续扩展路线（非 MVP）

- 更可靠 NAV / iNAV 数据源适配器
- 更完整事件日历（distribution/rebal/corp actions）
- 更强 liquidity proxies（spread/depth）
- 实时版扫描（盘中）
- Dashboard（Streamlit/Plotly）
- 回测与组合层（需额外风险/执行假设）

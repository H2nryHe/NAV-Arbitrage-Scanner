# TASK_BOARD.md

# NAV Arbitrage Scanner — Agent Task Board（Stage / Task / Gate）

> 用途：这是执行看板（任务分解 + 依赖 + 状态），不是验收记录。  
> 阶段完成后的实际命令、产出、Gate 勾选请写入 `docs/stage_checklist.md`。

## 状态说明
- `TODO`：未开始
- `IN_PROGRESS`：进行中
- `BLOCKED`：被依赖/数据源问题阻塞
- `REVIEW`：已完成等待验收
- `DONE`：已通过阶段 Gate

## 优先级说明
- `P0`：必须完成（阻塞后续）
- `P1`：强烈建议（MVP质量关键）
- `P2`：增强项（可后置）

---

## 全局里程碑（Milestones）
- [x] M0: Stage 0 数据源可行性通过
- [x] M1: Stage 1 raw 抓取管道可重复运行
- [x] M2: Stage 2 标准化与基础特征完成
- [x] M3: Stage 3 信号与过滤逻辑完成
- [x] M4: Stage 4 CLI + 报表 MVP 可跑通
- [x] M5: Stage 5 历史跟踪可回答回归问题
- [x] M6: Stage 6 文档/测试/发布质量完成

---

## Stage 0 — 数据源可行性验证（Feasibility）

### Goal
验证 `price / nav / volume` 获取可行性，并明确 `borrow fee / events` 限制。

### Tasks
- [x] `S0-T1`（P0, DONE）列出候选数据源（price/nav/events/metadata）
  - 输出：source matrix（覆盖率、更新频率、限制）
- [x] `S0-T2`（P0, DONE）定义初始 universe（10–30 symbols, CEF+ETF）
  - 输出：`configs/universe_example.yaml`
- [x] `S0-T3`（P0, DONE）写可行性脚本拉取单日快照
  - 输出：coverage snapshot（至少 1 个日期）
- [x] `S0-T4`（P1, DONE）统计字段覆盖率（按 source / by symbol）
  - 输出：`docs/data_sources.md`
- [x] `S0-T5`（P1, DONE）确认数据限制与降级方案
  - 输出：ETF/CEF NAV 时滞说明、borrow 不可得说明

### Gate（进入 Stage 1 前必须满足）
- [x] 至少 20 个标的有 `price_close`, `nav`, `volume`
- [x] `premium_discount_pct` 可计算
- [x] `borrow_fee_proxy` 限制已明确
- [x] ETF/CEF 时间口径风险已记录

### Blockers
- 数据源反爬 / API 失败
- ETF NAV 覆盖率过低

### Decision Log（填写）
- 日期：2026-02-23
- 决策：Stage 1-4 采用 CEF-only MVP；ETF 延后。
- 原因：免费 ETF NAV 数据源在统一性和可用性上不稳定（Yahoo 429、供应商口径分裂）。
- 影响阶段：Stage 1-4 数据抓取与信号口径先围绕 CEF。

---

## Stage 1 — 数据抓取管道（Raw / Bronze）

### Goal
建立每日抓取 + raw 落盘 + 日志，保证单标的失败不阻断整体。

### Tasks
- [x] `S1-T1`（P0, DONE）定义 raw schema 与落盘路径约定
  - `data/raw/{dataset}/date=YYYY-MM-DD/...`
- [x] `S1-T2`（P0, DONE）实现 `fetch_price_volume(date, symbols)`
- [x] `S1-T3`（P0, DONE）实现 `fetch_nav(date, symbols)`
- [x] `S1-T4`（P1, DONE）实现 `fetch_events(date, symbols)`（允许 best-effort）
- [x] `S1-T5`（P1, DONE）实现 `fetch_metadata(symbols)`
- [x] `S1-T6`（P0, DONE）实现 retry/timeout + warning logging
- [x] `S1-T7`（P0, DONE）生成 raw 样例数据（1–2 days）
- [x] `S1-T8`（P1, DONE）编写 pipeline 输入输出结构说明（供 Stage 2 使用）

### Gate
- [x] 同一日期重复抓取流程可完成
- [x] 单 symbol 失败不会阻断整体
- [x] raw 层保留 source + fetch timestamp
- [x] raw 数据可被标准化模块读取

### Blockers
- NAV 抓取结构频繁变化
- 批量请求限速太严

### Decision Log（填写）
- 日期：2026-02-23
- 决策：NAV 拉取优先 exact-date；缺失时允许回退到最近可用 NAV（并以 `reason=used_previous_nav_date` 标记）。
- 原因：CEFConnect 对部分基金无同日 NAV 更新，若不回退会导致 Stage 1 raw 覆盖率显著下降。
- 影响阶段：Stage 2 需要基于 `reason`/`DataDate` 做 NAV 时效性质量标记与过滤。

---

## Stage 2 — 标准化与特征工程（Silver）

### Goal
统一 schema 并输出基础特征：premium/discount、dollar volume、z-score。

### Tasks
- [x] `S2-T1`（P0, DONE）定义标准化表 schema（silver）
- [x] `S2-T2`（P0, DONE）实现字段映射与类型转换
- [x] `S2-T3`（P0, DONE）实现 `premium_discount_pct`
- [x] `S2-T4`（P0, DONE）实现 `dollar_volume`
- [x] `S2-T5`（P1, DONE）实现 rolling stats（mean/std/zscore）
- [x] `S2-T6`（P1, DONE）实现缺失值策略与 data_quality flags
- [x] `S2-T7`（P0, DONE）编写核心公式单元测试
- [x] `S2-T8`（P1, DONE）生成 `data/silver/` 样例输出

### Gate
- [x] 抽查 5 个样本公式正确
- [x] 输出包含必备字段
- [x] 缺失值处理可追溯（日志/flag）
- [x] 核心单元测试通过

### Blockers
- 历史窗口不足（zscore 为空）
- NAV 为 0 或负数导致异常

### Decision Log（填写）
- 日期：2026-02-23
- 决策：z-score 使用可配置窗口（默认 20d），历史不足不补值，直接置空并打 `insufficient_history_20d`。
- 原因：避免隐式填充掩盖数据不足问题，保持质量可追溯。
- 影响阶段：Stage 3 读取 `pd_zscore_20d` 时需结合质量标记筛选可用样本。

---

## Stage 3 — 信号引擎（Extreme + Half-life + Filters）

### Goal
生成“可解释 + 可排序”的候选名单，含风险标签。

### Tasks
- [x] `S3-T1`（P0, DONE）实现极端偏离规则（abs PD 或 zscore）
- [x] `S3-T2`（P0, DONE）实现 half-life 估计（含异常降级）
- [x] `S3-T3`（P0, DONE）实现流动性过滤（min dollar volume）
- [x] `S3-T4`（P1, DONE）实现事件过滤（best-effort）
- [x] `S3-T5`（P0, DONE）实现风险标签（low_liquidity, leverage, nav_stale 等）
- [x] `S3-T6`（P1, DONE）实现透明评分/排序
- [x] `S3-T7`（P0, DONE）输出候选中间表（含 rationale/risk_flags）
- [x] `S3-T8`（P1, DONE）half-life 单元测试（边界 case）

### Gate
- [x] 候选清单非空（合理 universe 下）
- [x] 每条候选有 `rationale`
- [x] 每条候选有 `risk_flags`
- [x] half-life 异常不输出误导值
- [x] 阈值配置化

### Blockers
- 历史数据长度不足
- 事件数据覆盖差影响过滤稳定性

### Decision Log（填写）
- 日期：2026-02-23
- 决策：极端信号优先使用 z-score，z-score 缺失时回退到绝对 premium/discount 阈值，确保低历史期可产出可解释候选。
- 原因：当前样本窗口较短（20d z-score 不可用），若不回退将无法形成候选清单。
- 影响阶段：Stage 4 报表需明确候选来源于 abs PD fallback 逻辑。

---

## Stage 4 — CLI 串联 + 报表输出（MVP）

### Goal
通过 `navscan run --date YYYY-MM-DD` 串联全流程并生成日报。

### Tasks
- [x] `S4-T1`（P0, DONE）搭建 CLI 主命令（Typer/argparse）
- [x] `S4-T2`（P0, DONE）串联 fetch → standardize → features → signals → report
- [x] `S4-T3`（P0, DONE）生成 CSV 报表
- [x] `S4-T4`（P0, DONE）生成 Markdown 报表（含风险/限制说明）
- [x] `S4-T5`（P1, DONE）CLI summary（覆盖率、候选数、warnings）
- [x] `S4-T6`（P1, DONE）退出码规范（0/1/2）
- [x] `S4-T7`（P1, DONE）错误输入处理（日期格式、空 universe）

### Gate
- [x] `navscan run --date YYYY-MM-DD` 可执行成功
- [x] CSV + Markdown 文件生成
- [x] 同日重复运行结构一致
- [x] CLI 错误提示清晰
- [x] 退出码符合规范

### Blockers
- 前几阶段接口不稳定
- 报表字段命名频繁变动

### Decision Log（填写）
- 日期：2026-02-23
- 决策：`run` 命令采用子流程编排（Stage1→Stage2→Stage3→Stage4 报表导出）并以 exit code 表达完整/部分/失败状态。
- 原因：最小实现即可满足 MVP 单命令可运行目标，且复用前序阶段脚本降低耦合。
- 影响阶段：Stage 5 可在此编排框架上追加 tracking 步骤而不重构前段流程。

---

## Stage 5 — 历史跟踪与回归监控

### Goal
跟踪候选后续回归情况（T+1 / T+3 / T+5），支持基础监控问题查询。

### Tasks
- [x] `S5-T1`（P0, DONE）选择并初始化历史存储（DuckDB/Parquet）
- [x] `S5-T2`（P0, DONE）写入每日候选与快照（幂等）
- [x] `S5-T3`（P0, DONE）实现回归 outcome 计算（方向性回归）
- [x] `S5-T4`（P1, DONE）实现 MAE / 未回归天数等追踪字段
- [x] `S5-T5`（P1, DONE）增加“昨日候选状态更新”报表段落
- [x] `S5-T6`（P1, DONE）回填/backfill 逻辑（不重复写入）

### Gate
- [x] 能回答某天 Top N 到某天有多少回归
- [x] rerun/backfill 不产生重复记录
- [x] 有主键或去重逻辑
- [x] 缺口数据有明确标记

### Blockers
- 历史数据不足导致 outcome 空
- 数据源修订导致历史复算差异

### Decision Log（填写）
- 日期：2026-02-23
- 决策：Stage 5 使用 SQLite 作为 DuckDB 等价 MVP 存储，并以主键 upsert 实现幂等写入。
- 原因：SQLite 为本地零依赖，满足历史快照/候选/outcome 的结构化查询与去重需求。
- 影响阶段：Stage 6 可按需要切换到 DuckDB，但需要迁移脚本与查询兼容层。

---

## Stage 6 — 验证 / 文档 / 发布质量

### Goal
让 repo 可复现、可展示、可面试讲述。

### Tasks
- [x] `S6-T1`（P0, DONE）完成 README（Quickstart + CLI + 限制）
- [x] `S6-T2`（P0, DONE）完成 `docs/limitations.md` 与 `docs/methodology.md`
- [x] `S6-T3`（P1, DONE）增加 examples 输出样例
- [x] `S6-T4`（P1, DONE）补充集成测试（小样本 E2E）
- [x] `S6-T5`（P1, DONE）做基础验证统计（T+1/T+3/T+5 回归率）
- [ ] `S6-T6`（P2, TODO）CI / lint / pre-commit（可选）
- [x] `S6-T7`（P1, DONE）整理风险与免责声明（非投资建议）

### Gate
- [x] 新用户可按 README 在 Mac M2 跑 demo
- [x] 核心公式/half-life 有测试
- [x] 限制与风险写清楚
- [x] 文档与代码结构一致
- [x] 示例输出可展示

### Blockers
- 无（Stage 6 执行期未出现阻塞性问题）

### Decision Log（填写）
- 日期：2026-02-24
- 决策：保留现有核心策略逻辑，仅补齐可复现文档、示例与基础验证统计，不在 Stage 6 做策略重构。
- 原因：遵循 Stage 6 目标（发布质量与展示质量），避免偏离“只修 blocker，不重设计核心逻辑”。
- 影响阶段：Stage 6 交付可用于演示与复现；后续优化应在 Stage 6 之后独立规划。

---

## 跨阶段持续任务（Recurring Work）

- [ ] `X-T1`（P0, TODO）维护 `docs/stage_checklist.md`（每个 stage 完成后记录）
- [ ] `X-T2`（P1, TODO）保持配置参数集中化（避免硬编码阈值）
- [ ] `X-T3`（P1, TODO）统一日志格式（含 stage/source/symbol/reason）
- [ ] `X-T4`（P1, TODO）更新 known limitations（随着实现推进同步修订）
- [ ] `X-T5`（P2, TODO）记录性能耗时（Mac M2 本地运行时间）

---

## 当前冲刺（建议先做）
- [ ] Sprint-1: 完成 Stage 0 全部 P0 + P1
- [ ] Sprint-2: 完成 Stage 1 全部 P0 + raw 样例
- [ ] Sprint-3: 完成 Stage 2 P0 + Stage 3 P0（形成最小信号清单）
- [ ] Sprint-4: 完成 Stage 4（CLI + CSV/MD 输出 MVP）

---

## 备注（使用方式）
- `TASK_BOARD.md` 用来安排“做什么、先后顺序、卡点是什么”
- `docs/stage_checklist.md` 用来记录“实际跑了什么、产出了什么、Gate 是否通过”

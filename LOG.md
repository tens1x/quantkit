# Development Log

所有重要决策、变更、想法的时间线记录。可以回溯任何一个节点。

---

## 2026-04-05

### 项目起源
- **背景**: 调研了 8 个量化交易相关内容（小红书帖子、Bilibili 视频、GitHub 项目），发现量化工具中的因子分析、回测、风险管理对个人投资者有学习价值
- **核心想法**: 不做自动交易，做一个**反思和学习工具**，帮助建立投资流程和纪律
- **决策**: 建终端工具而非 Web，menu-driven 交互，支持 A 股 + 美股

### Design & Planning
- **Who**: Claude Code
- **What**:
  - 完成设计文档 `docs/superpowers/specs/2026-04-05-quantkit-design.md`
  - 完成实施计划 `docs/superpowers/plans/2026-04-05-quantkit-implementation.md`（11 tasks）
  - 确定团队分工: Claude Code (PM) + Codex CLI (Dev) + Gemini CLI (QA/Docs)
- **Commits**: `fe10b96` design spec, `a936be5` implementation plan

### 第一次实现（已废弃）
- **Who**: Claude Code subagents
- **What**: 用 Claude Code 自己的 subagent 完成了全部实现
- **问题**: 违反了约定分工——代码应该由 Codex CLI 写
- **决策**: 用户要求推翻重来，严格按分工执行
- **操作**: `git reset --hard a936be5` 回退到 plan commit

### 第二次实现（正式版）
- **Who**: Codex CLI（由 Claude Code 调度）
- **What**: 严格按分工重新实现全部 10 个 task，35 tests passing
- **Commits**:
  - `8163d49` Task 1 — Project Scaffold
  - `ca94b25` Task 2 — Settings & Config
  - `d46d29e` Task 3 — SQLite Cache Layer
  - `dd63fbc` Task 4 — Data Provider
  - `a8593f7` Task 5 — Portfolio Management
  - `508d768` Task 6 — Factor Check Engine
  - `c392225` Task 7 — Backtest Engine
  - `ce8f113` Task 8 — Risk Lens Engine
  - `68773e4` Task 9 — CLI Menu System
  - `442f3ef` Task 10 — Integration Test

### Documentation (Task 11)
- **Who**: Gemini CLI（尝试）→ Claude Code（实际执行）
- **What**: Gemini 因 Plan Mode 权限限制无法写文件，生成了内容但由 Claude Code 落盘
- **教训**: Gemini CLI 的 `-p` 模式下 write_file 工具不可用
- **Commit**: `2deaa89`

## 2026-04-06

### UX 改进（5 个问题修复）
- **Who**: Codex CLI（由 Claude Code 调度）
- **触发**: 用户实际使用后反馈
- **问题和修复**:
  1. 报错后被踢回主菜单 → 所有子菜单改为 while True 循环
  2. CSV 导入无引导 → 增加格式提示 + IBKR 自动识别
  3. Factor Check 查完一只就退 → 循环菜单
  4. Backtest 缺 Low PE + 提示不清 → 加选项 + 中文提示
  5. IBKR CSV 格式不兼容 → 新增 `import_ibkr_csv()` + `detect_and_import()`
- **Tests**: 35 → 37
- **Commit**: `36a69bc`

### 文档体系重构
- **Who**: Claude Code
- **想法**: 现有文档是散的，没有一个入口回答"我今天该做什么"
- **决策**:
  - PLAN.md 重新定位为**行动入口**，包含月度复盘 checklist 和研究 pipeline
  - PROJECT.md 纯技术文档，包含模块接口和标准流程
  - GUIDE.md 保持为使用教程
  - LOG.md（本文件）记录所有决策和变更，可回溯
  - research/ 目录存放论文、策略、笔记
- **设计原则**:
  - 每件事有明确触发条件，不靠"记得做"
  - 模板统一，不用每次想格式
  - checklist 可以打勾
  - 打开 PLAN.md 就知道下一步

### 关键决策记录

| 决策 | 原因 | 日期 |
|------|------|------|
| 终端工具而非 Web | 简单、专注、不分心 | 04-05 |
| 不做自动交易 | 目的是学习和反思，不是赚快钱 | 04-05 |
| 三 AI 分工（Claude/Codex/Gemini） | 各有所长，严格分工保证质量 | 04-05 |
| 推翻重来按分工执行 | 流程纪律比速度重要 | 04-05 |
| IBKR 只导入买单 | 简单起步；后续可改为买卖净额化 | 04-06 |
| research/ 目录独立于代码 | 认知积累不随代码重写丢失 | 04-06 |
| PLAN.md 作为行动入口 | 解决"打开项目不知道做什么"的问题 | 04-06 |
| CLAUDE.md 作为 agent 规范 | 所有 AI agent 读同一份规范，保证一致性 | 04-06 |
| Ruff 作为 linter | 轻量、快速、够用，不引入重型工具链 | 04-06 |
| CLI 从菜单驱动改为命令驱动 | 更灵活、更像开发者工具、扩展性好 | 04-06 |
| Persona 功能作为隐藏彩蛋 | 降低新用户认知负担，进阶用户自行发现 | 04-06 |
| PyYAML 解析 persona 文件 | 轻量、规则可读、不依赖 LLM | 04-06 |

---

## 2026-04-06（续）

### CLI 重写：菜单驱动 → Stock-centric 命令驱动

- **Who**: Claude Code（设计 + review）+ Codex CLI（实现）
- **触发**: 用户提出"Investor Persona"功能时，顺带重新设计了整个交互模型
- **变更**:
  - 旧模式: 数字菜单导航（主菜单 → 子菜单 → 操作）
  - 新模式: 输入股票代码 → `/命令` 交互（如 `/factor`, `/backtest ma`, `/guru buffett`）
  - 新增 `StockContext`：预加载 1y OHLCV + fundamentals，带区间管理和延迟因子缓存
  - 新增 `commands/` 模块：命令注册表 + 路由 + handler 分离
  - `cli.py` 从 475 行缩减到 ~60 行（主循环）
- **设计文档**: `docs/superpowers/specs/2026-04-06-cli-rewrite-persona-design.md`
- **实施计划**: `docs/superpowers/plans/2026-04-06-cli-rewrite-persona.md`（10 tasks）

### Investor Persona 功能

- **Who**: Claude Code（设计）+ Codex CLI（实现）
- **What**:
  - 投资人决策规则蒸馏为 YAML 文件（规则引擎，非 LLM）
  - 加权评分 → 买入/观望/回避 + 理由列表
  - `/guru buffett` 单人评估、`/guru all` 全部、`/guru` 交互选择
  - 隐藏功能：需在 `/settings` 中开启 persona_mode
- **文件**:
  - `persona/engine.py` — 规则引擎（加载、校验、评估）
  - `persona/personas/buffett.yaml` — 巴菲特 persona
  - `commands/persona_cmd.py` — /guru handler
- **Commits**:
  - `44c0bad` feat: add persona_mode config + pyyaml dependency
  - `c3e44f0` feat: add StockContext with preloaded data and interval tracking
  - `9e14b10` feat: add persona engine with YAML loading and rule evaluation
  - `8f0a0b1` feat: rewrite CLI to stock-centric command-driven interface
  - `30b1307` test: update integration tests for command-driven CLI
- **Tests**: 37 → 71（+34 tests covering StockContext, persona, commands, routing, integration）

### Codex CLI 工具迁移

- **Who**: 用户
- **What**: 从 `~/.claude/skills/codex-dev-g/`（ask_dev_g.sh）迁移到 `codex-plugin-cc` 插件
- **原因**: 旧 dev-g 脚本持续返回截断响应（1-2 行），--session 参数报错，无法正常工作
- **新工具**: `codex-companion.mjs task --write "prompt"` 模式，稳定可用

### CLI UX Upgrade: prompt_toolkit + 视觉统一

- **Who**: Codex CLI（由 Claude Code 调度）
- **What**:
  - 主循环输入层从 Rich Prompt 换为 prompt_toolkit PromptSession
  - 输入 `/` 自动弹命令补全菜单，参数补全（策略/投资人）
  - fish-style 灰色建议历史股票代码（SymbolAutoSuggest）
  - 启动清屏 + 品牌 banner（ROUNDED green Panel）
  - 所有表格统一 ROUNDED 圆角 + Rule 标题头
  - 补全菜单深色主题样式
- **设计文档**: `docs/superpowers/specs/2026-04-06-cli-ux-upgrade-design.md`
- **新增依赖**: prompt-toolkit>=3.0
- **Tests**: 71 → 90（+19 tests covering completer, auto-suggest, prompt styling）
- **Commits**: `047e8ac` prompt_toolkit core, `49883d8` visual unification

---

## 2026-04-06（研究）

### 论文研究: The Intramonth Momentum Cycle

- **Who**: Claude Code（研究 + 分析）
- **What**: 研究 Nathan, Suominen, Tasa (2026) 论文，分析与用户现有 PineScript 策略的关系
- **关键发现**: 动量收益集中在月末前 6 个交易日（PreTOM 窗口 T-9 到 T-4），由机构 "dash for cash" 驱动。效应在 19 个发达市场可复制，但 A 股不在样本中。
- **论文笔记**: `research/papers/2026-04-06-intramonth-momentum-cycle.md`

### PineScript 策略分析

- **Who**: Claude Code + Codex（协作分析）
- **What**: 分析用户提供的 4 个 TradingView PineScript 策略（HKEX:1810 小米、TVC:GOLD 黄金、比亚迪、阳光电源）
- **发现**: 四个策略共享同一套 G1 框架（Regime Guard + Turtle Breakout + MFE 2-Stage Trail + Vol Targeting + DD Scaling），是改进版海龟交易系统

### PreTOM 日历仓位缩放（小米版）

- **Who**: Claude Code（设计 + 实现）+ Codex（方案评审）
- **What**: 基于论文发现，在小米策略的 `scale` 链条中加入日历系数。PreTOM 窗口 ×1.15，非窗口 ×0.90。港股 T+2 结算，窗口前移至 T-10 到 T-5。
- **文件**: `docs/HKEX_preTOM.pine`（本地，不上传 git）
- **策略文档**: `research/strategies/pretom-calendar-sizing.md`
- **决策**: 不做入场过滤（会大幅减少信号），用仓位缩放（保留所有信号但倾斜资金分配）

### G1 Dual Engine 融合策略

- **Who**: Claude Code（设计 + 实现）+ Codex（架构设计协作）
- **触发**: 用户要求融合 G1 框架与 StockTradebyZ B1 策略
- **What**:
  - 双引擎入场: Engine A（Donchian 突破）+ Engine B（KDJ 超卖回踩）
  - 知行线 Regime 替代 EMA200（ZXDKX 有效滞后 ~27 bar vs EMA200 ~100 bar）
  - 最大量非阴线过滤（排除主力出货）
  - 保留完整 G1 出场/风控系统
- **文件**: `docs/G1_DualEngine_AShare.pine`（本地，不上传 git）
- **策略文档**: `research/strategies/g1-dual-engine.md`

### StockTradebyZ 项目分析

- **Who**: Claude Code + Codex（协作 review）
- **What**: Review GitHub 项目 SebastienZh/StockTradebyZ（A 股半自动选股系统）
- **发现**: 量化筛选（KDJ + 知行线 + 周线多排 + 量能确认）→ K 线图生成 → Gemini AI 打分。是选股系统，不是交易系统——与 G1 互补。
- **借鉴**: KDJ 回踩入场、知行线 Regime、最大量非阴线过滤 → 融入 G1 Dual Engine

### 回测引擎讨论

- **Who**: Claude Code + Codex（方案评审）
- **决策**: 不替换 QuantKit 现有回测引擎
- **原因**:
  - 复杂策略回测在 TradingView (PineScript) 完成，QuantKit 不需要竞争
  - QuantKit 的回测是教学功能（MA/DCA vs Buy & Hold），现有引擎够用
  - QuantKit 的差异化价值在因子分析、风险评估、反思流程
  - 主流框架（vectorbt/backtrader/bt）要么太重、要么过时、要么能力不足

### 关键决策记录

| 决策 | 原因 | 日期 |
|------|------|------|
| PineScript 策略文件不上传 git | 个人策略资产，不公开 | 04-06 |
| 不替换 QuantKit 回测引擎 | TradingView 做复杂回测，QuantKit 做教学回测，各司其职 | 04-06 |
| PreTOM 用仓位缩放而非入场过滤 | 突破频率已低（31-73 bar），入场过滤会严重减少信号 | 04-06 |
| 知行线替代 EMA200 | ZXDKX 响应快 3-4 倍，更适合 A 股牛熊转换速度 | 04-06 |
| A 股策略暂不加 PreTOM | 论文样本不含 A 股，需先验证效应存在 | 04-06 |

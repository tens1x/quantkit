# Development Log

## 2026-04-05

### Design & Planning
- **Who**: Claude Code
- **What**: 调研量化交易帖子 → 设计 QuantKit spec → 撰写实施计划（11 tasks）
- **Commits**: `fe10b96` design spec, `a936be5` implementation plan

### Implementation (Tasks 1-10)
- **Who**: Codex CLI (由 Claude Code 调度)
- **What**: 全部代码实现，TDD，35 tests passing
- **Commits**:
    - `8163d49` Task 1 — Project Scaffold
    - `ca94b25` Task 2 — Settings & Config
    - `d46d29e` Task 3 — SQLite Cache Layer
    - `dd63fbc` Task 4 — Data Provider (yfinance + Tushare)
    - `a8593f7` Task 5 — Portfolio Management
    - `508d768` Task 6 — Factor Check Engine
    - `c392225` Task 7 — Backtest Engine
    - `ce8f113` Task 8 — Risk Lens Engine
    - `68773e4` Task 9 — CLI Menu System
    - `442f3ef` Task 10 — Integration Test

### Documentation (Task 11)
- **Who**: Gemini CLI (内容生成) → Claude Code (落盘 + 修正 commit hash)
- **What**: 创建 PLAN.md, PROJECT.md, LOG.md
- **Commit**: `2deaa89`
- **Note**: Gemini 因 Plan Mode 权限限制无法写文件，生成了完整内容由 Claude Code 写入

## 2026-04-06

### UX Improvements
- **Who**: Codex CLI (由 Claude Code 调度)
- **What**: 5 个用户体验修复
    1. 报错后留在当前子菜单，不回主菜单
    2. CSV 导入增加 IBKR 格式自动识别 + 格式提示
    3. Factor Check 可连续查多只股票
    4. Strategy Backtest 加回 Low PE 选项 + 中文提示
    5. IBKR 交易记录解析（仅导入买单）
- **Tests**: 35 → 37 (+2 IBKR import tests)
- **Commit**: `36a69bc`

### Documentation Update
- **Who**: Claude Code
- **What**: 重写 PLAN.md, PROJECT.md, LOG.md，反映最新功能和接口变更

# QuantKit

终端版个人投资工具包。学习和反思工具，不是自动交易系统。

## 文档导航

| 文件 | 用途 | 什么时候看 |
|------|------|-----------|
| **PLAN.md** | 行动入口，月度复盘 checklist，研究 pipeline | **每次打开项目先看这个** |
| **CLAUDE.md** | AI agent 协作规范 + 代码/测试/Git/文档标准 | **所有 agent 必读** |
| **GUIDE.md** | 软件使用教程，功能详解 | 第一次用、忘了操作时看 |
| **PROJECT.md** | 技术架构，模块接口，开发指南 | 要改代码时看 |
| **LOG.md** | 开发日志，决策记录 | 想回溯历史时看 |
| **research/README.md** | 论文/策略/复盘模板 | 要写笔记时看 |

---

## 快速开始

```bash
uv pip install -e ".[dev]"     # 安装
uv run python -m quantkit       # 运行
uv run pytest tests/ -v         # 测试
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              CLI (cli.py) — Stock-centric REPL           │
│  输入股票代码 → /命令交互 (Rich TUI + plotext)            │
├─────────────────────────────────────────────────────────┤
│                  Commands (commands/)                     │
│  /factor │ /backtest │ /risk │ /guru │ /portfolio │ ...  │
├──────────┬──────────┬─────────┬──────────┬──────────────┤
│ Factor   │ Backtest │ Risk    │ Persona  │ Portfolio    │
│ Engine   │ Engine   │ Engine  │ Engine   │ Management   │
│ (6 维)   │ (MA/DCA) │ (4 维)  │ (YAML)   │ (CSV/IBKR)  │
├──────────┴──────────┴─────────┴──────────┴──────────────┤
│           StockContext (stock_context.py)                 │
│         预加载 OHLCV + fundamentals + 区间管理             │
├─────────────────────────────────────────────────────────┤
│              Data Provider (auto-routing)                 │
│         yfinance (US) ←→ Tushare (CN)                    │
│              SQLite Cache Layer                           │
└─────────────────────────────────────────────────────────┘
```

## Module Interfaces

### StockContext (`stock_context.py`)
- `StockContext.load(symbol)` → StockContext — 预加载 1y OHLCV + fundamentals（fundamentals 失败降级为 None）
- `.get_ohlcv(start, end)` → DataFrame — 区间内返回切片，超出范围自动重新获取
- `.get_factors()` → dict — 延迟计算 + 缓存因子结果
- `.has_fundamentals` → bool
- `.symbol` → str, `.ohlcv` → DataFrame, `.fundamentals` → dict | None

### Command Router (`commands/__init__.py`)
- `parse_command(raw)` → (cmd_name, args) — 解析 `/command args` 输入
- `route(raw, ctx)` → "exit" | None — 验证上下文/权限后分发到 handler
- `COMMANDS` → dict[str, CommandInfo] — 命令注册表（name, description, requires_context, requires_persona）

### Command Handlers
- `commands/analysis.py` — `/factor`, `/backtest`, `/risk` 处理器
- `commands/persona_cmd.py` — `/guru [name|all]` 处理器
- `commands/management.py` — `/portfolio`, `/settings`, `/help` 处理器

### Data Provider (`data/provider.py`)
- `get_ohlcv(symbol, start, end)` → DataFrame[date, open, high, low, close, volume]
- `get_fundamentals(symbol)` → dict{pe, pb, roe, market_cap, revenue_growth}
- `is_cn_symbol(symbol)` → bool — 自动路由 A 股/美股

### Portfolio (`portfolio.py`)
- `detect_and_import(path)` → (count, format_name) — 自动检测 QuantKit CSV / IBKR 格式
- `import_csv(path)` → int — QuantKit 格式
- `import_ibkr_csv(path)` → int — IBKR 格式（仅买单）
- `list_positions()` → list[dict]
- `clear_positions()` → None

### Factor Engine (`factor/engine.py`)
- `compute_factors(ohlcv, fundamentals)` → dict{name: {value, rating, label}}
- `rate_factor(name, value, percentile)` → (color, label)
- 6 因子: PE, PB, ROE, Revenue Growth, Volatility(60d), Momentum(20d)

### Backtest Engine (`backtest/engine.py` + `strategies.py`)
- `run_backtest(ohlcv, signals, capital, slippage_bps, commission_bps)` → dict{equity_curve, trades, final_equity}
- `compute_metrics(equity, trades)` → dict{total_return, annualized_return, sharpe, max_drawdown, win_rate, trade_count}
- `ma_cross_signals(ohlcv, short_window, long_window)` → Series
- `low_pe_signals(pe_series, buy_percentile, sell_percentile)` → Series（未接入，待实现）
- `dca_signals(ohlcv, day_of_month)` → Series

### Risk Engine (`risk/engine.py`)
- `compute_concentration(market_values)` → dict — 持仓集中度（>30% 警告）
- `compute_correlation_matrix(returns_df)` → DataFrame — 相关性矩阵
- `compute_volatility_contribution(returns_df, weights)` → dict — 边际波动贡献
- `compute_max_drawdown(equity)` → dict{max_drawdown, peak_date_idx, trough_date_idx}

### Persona Engine (`persona/engine.py`)
- `load_personas()` → list[Persona] — 扫描 YAML 文件，校验格式，跳过无效文件
- `evaluate(persona, factors)` → Verdict{action, score, reasons} — 加权规则评分
- 数据类: `Rule`, `Persona`, `Verdict`
- 有效因子: pe, pb, roe, revenue_growth, volatility, momentum
- 有效运算符: <, >, <=, >=

## Directory Structure

```
quantkit/
├── src/quantkit/
│   ├── __main__.py          # python -m quantkit
│   ├── cli.py               # Stock-centric REPL（主循环）
│   ├── prompt.py            # prompt_toolkit 集成（补全/建议/样式）
│   ├── stock_context.py     # 预加载数据 + 区间管理
│   ├── config.py            # ~/.quantkit/config.json 管理
│   ├── portfolio.py         # 持仓管理（CSV/IBKR 导入）
│   ├── commands/
│   │   ├── __init__.py      # 命令注册表 + 路由
│   │   ├── analysis.py      # /factor, /backtest, /risk
│   │   ├── persona_cmd.py   # /guru
│   │   └── management.py    # /portfolio, /settings, /help
│   ├── data/
│   │   ├── provider.py      # 统一数据接口 + 路由 + 缓存
│   │   ├── yfinance_src.py  # 美股适配器
│   │   ├── tushare_src.py   # A 股适配器
│   │   └── cache.py         # SQLite 缓存（OHLCV + fundamentals）
│   ├── factor/
│   │   └── engine.py        # 因子计算 + 红绿灯评级
│   ├── backtest/
│   │   ├── engine.py        # 逐日回测引擎
│   │   └── strategies.py    # 内置策略（MA/PE/DCA）
│   ├── risk/
│   │   └── engine.py        # 风险分析四维度
│   └── persona/
│       ├── engine.py        # 规则引擎（加载 YAML + 评估）
│       └── personas/        # 投资人 YAML 文件
│           └── buffett.yaml
├── tests/                   # 90 tests
├── research/
│   ├── papers/              # 论文笔记
│   ├── strategies/          # 策略想法
│   └── notes/               # 复盘笔记 + 零散记录
├── docs/superpowers/
│   ├── specs/               # 设计文档
│   └── plans/               # 实施计划
├── PLAN.md                  # 行动入口
├── PROJECT.md               # 技术文档（本文件）
├── GUIDE.md                 # 使用指南
├── LOG.md                   # 开发日志
├── pyproject.toml
└── .gitignore
```

## Configuration

`~/.quantkit/config.json`:

| Setting | Default | Description |
|---------|---------|-------------|
| tushare_token | "" | Tushare API token（A 股必需） |
| default_capital | 100,000 | 回测初始资金 |
| slippage_bps | 10 | 滑点 (basis points) |
| commission_bps | 5 | 佣金 (basis points) |
| persona_mode | false | 投资人视角功能开关（/settings 中开启后可用 /guru） |

## Data Sources

| 市场 | 数据源 | 认证 |
|------|--------|------|
| 美股 | yfinance | 免费，无需配置 |
| A 股 | Tushare | 需要 token（https://tushare.pro） |

## Development Workflow

所有代码修改严格遵循：

```
Claude Code 设计 → Codex CLI 实现 → Claude Code review + test → commit + push
```

详见 PLAN.md 主线 B 的完整 pipeline。

## 添加新策略的标准流程

1. 在 `research/strategies/` 写策略文档
2. 在 `backtest/strategies.py` 添加 `xxx_signals()` 函数
3. 在 `tests/test_backtest.py` 添加对应测试
4. 在 `commands/analysis.py` 的 `cmd_backtest()` 添加策略选项
5. 全部测试通过 → commit + push

## 添加新因子的标准流程

1. 在 `research/papers/` 记录理论依据
2. 在 `factor/engine.py` 的 `rate_factor()` 添加评级逻辑
3. 在 `factor/engine.py` 的 `compute_factors()` 添加计算
4. 在 `tests/test_factor.py` 添加测试
5. `commands/analysis.py` 的 `cmd_factor()` 添加显示名
6. 全部测试通过 → commit + push

## 添加新投资人 Persona 的标准流程

1. 在 `research/papers/` 记录投资理念和依据
2. 在 `persona/personas/` 创建 `name_en.yaml`（参考 `buffett.yaml` 格式）
3. YAML 必须包含: name, name_en, philosophy, rules[], buy_threshold, watch_threshold
4. 在 `tests/test_persona.py` 添加测试
5. 全部测试通过 → commit + push

# QuantKit

终端版个人投资工具包。支持 A 股和美股，提供因子检查、策略回测、风险分析三大功能。

## 快速开始

```bash
# 安装
uv pip install -e ".[dev]"

# 运行
uv run python -m quantkit

# 测试
uv run pytest tests/ -v
```

## Architecture

```
数据层 (Data Layer)          分析层 (Analysis Layer)       UI 层
┌──────────────────┐    ┌───────────────────────┐    ┌──────────┐
│ yfinance (US)    │    │ Factor Check (6维)     │    │ Rich TUI │
│ Tushare (CN)     │───▶│ Backtest (MA/DCA/PE)  │───▶│ plotext  │
│ SQLite Cache     │    │ Risk Lens (4维)        │    │ menus    │
└──────────────────┘    └───────────────────────┘    └──────────┘
```

## Module Interfaces

### Data Provider (`data/provider.py`)
- `get_ohlcv(symbol, start, end)` → DataFrame[date, open, high, low, close, volume]
- `get_fundamentals(symbol)` → dict{pe, pb, roe, market_cap, revenue_growth}
- `is_cn_symbol(symbol)` → bool — 自动路由 A 股/美股

### Portfolio (`portfolio.py`)
- `import_csv(path)` → int — 导入 QuantKit 格式 CSV
- `import_ibkr_csv(path)` → int — 导入 IBKR 交易记录（仅买单）
- `detect_and_import(path)` → (count, format_name) — 自动检测格式并导入
- `list_positions()` → list[dict]
- `clear_positions()` → None

### Factor Engine (`factor/engine.py`)
- `compute_factors(ohlcv, fundamentals)` → dict — 6 个因子 + 红绿灯评级
- `rate_factor(name, value, percentile)` → (color, label)

6 个因子: PE(TTM), PB, ROE, Revenue Growth, Volatility(60d), Momentum(20d)

### Backtest Engine (`backtest/engine.py`, `strategies.py`)
- `run_backtest(ohlcv, signals, capital, slippage_bps, commission_bps)` → dict{equity_curve, trades}
- `compute_metrics(equity, trades)` → dict{total_return, annualized, sharpe, max_drawdown, win_rate}
- Strategies: `ma_cross_signals()`, `low_pe_signals()`, `dca_signals()`

### Risk Engine (`risk/engine.py`)
- `compute_concentration(market_values)` — 持仓集中度（>30% 警告）
- `compute_correlation_matrix(returns)` — 相关性矩阵
- `compute_volatility_contribution(returns, weights)` — 波动贡献
- `compute_max_drawdown(equity)` — 历史最大回撤

## Directory Structure

```
quantkit/
├── src/quantkit/
│   ├── __main__.py          # python -m quantkit
│   ├── cli.py               # Rich 菜单系统
│   ├── config.py            # ~/.quantkit/config.json
│   ├── portfolio.py         # CSV 导入 (QuantKit + IBKR 格式)
│   ├── data/
│   │   ├── provider.py      # 统一数据接口 + 自动路由
│   │   ├── yfinance_src.py  # 美股数据
│   │   ├── tushare_src.py   # A 股数据
│   │   └── cache.py         # SQLite 缓存
│   ├── factor/
│   │   └── engine.py        # 因子计算 + 评级
│   ├── backtest/
│   │   ├── engine.py        # 逐日回测引擎
│   │   └── strategies.py    # MA 交叉 / 低 PE / 定投
│   └── risk/
│       └── engine.py        # 集中度 / 相关性 / 波动 / 回撤
├── tests/                   # 37 tests
├── pyproject.toml
└── .gitignore
```

## Configuration

`~/.quantkit/config.json`:

| Setting | Default | Description |
|---------|---------|-------------|
| tushare_token | "" | Tushare API token (A 股必需) |
| default_capital | 100,000 | 回测初始资金 |
| slippage_bps | 10 | 滑点 (basis points) |
| commission_bps | 5 | 佣金 (basis points) |

## Data Sources

- **美股**: yfinance — 免费，无需配置
- **A 股**: Tushare — 需要 token，在 https://tushare.pro 注册获取

## CSV Import 格式

**QuantKit 格式:**
```csv
symbol,buy_date,buy_price,quantity,market
AAPL,2024-03-15,172.50,100,US
600519.SH,2024-06-01,1680.00,200,CN
```

**IBKR 格式:** 直接导入 Interactive Brokers 的 Transaction History 导出文件，自动识别。仅导入买入交易。

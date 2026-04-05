# QuantKit Design Spec

**Date**: 2026-04-05
**Status**: Approved

## Overview

QuantKit is a terminal-based personal investment toolkit for an individual investor trading A-shares and US stocks. It is a learning and reflection tool, not an automated trading system.

Three core modules:
1. **Factor Check** — multi-dimensional health check on stocks
2. **Strategy Backtest** — validate simple buy/sell rules against history
3. **Risk Lens** — understand portfolio risk exposure

## Constraints & Decisions

- **New independent project** — does not share code with existing `whylosemoney`
- **Terminal UI only** — Rich library for menus/tables/panels, plotext for charts
- **Menu-driven interaction** — number keys to navigate, no commands to memorize
- **Data sources**: Tushare (A-shares) + yfinance (US stocks), cached in SQLite
- **Portfolio input**: CSV import from broker exports
- **No auto-trading** — analysis and reflection only

## Team Roles

| Role | Agent | Responsibilities |
|------|-------|------------------|
| Architect + PM | Claude Code | Plan, code review, test execution, quality control |
| Developer | Codex CLI | Code implementation |
| QA + Docs | Gemini CLI | Unit tests, PROJECT.md, LOG.md maintenance, second review perspective |

## Project Structure

```
quantkit/
├── src/quantkit/
│   ├── __main__.py         # Entry point: python -m quantkit
│   ├── cli.py              # Rich menu system
│   ├── data/
│   │   ├── __init__.py
│   │   ├── provider.py     # Unified get_ohlcv / get_fundamentals interface
│   │   ├── tushare_src.py  # Tushare adapter (A-shares)
│   │   ├── yfinance_src.py # yfinance adapter (US stocks)
│   │   └── cache.py        # SQLite cache layer
│   ├── portfolio.py        # CSV import, position storage, listing
│   ├── factor/
│   │   ├── __init__.py
│   │   └── engine.py       # Factor computation + report generation
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py       # Bar-by-bar backtest engine
│   │   └── strategies.py   # Built-in strategies (MA cross, low-PE, DCA)
│   └── risk/
│       ├── __init__.py
│       └── engine.py       # Risk analysis (concentration, correlation, drawdown)
├── tests/
│   ├── test_data.py
│   ├── test_portfolio.py
│   ├── test_factor.py
│   ├── test_backtest.py
│   └── test_risk.py
├── PLAN.md                 # Implementation plan & progress (Claude Code)
├── PROJECT.md              # Project docs & architecture (Gemini)
├── LOG.md                  # Development log (Gemini)
├── pyproject.toml
└── .gitignore
```

## Data Layer

### Unified Interface (`data/provider.py`)

```python
def get_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    Auto-routes by symbol format:
    - 600xxx.SH / 000xxx.SZ → Tushare
    - AAPL / TSLA → yfinance
    Returns: DataFrame[date, open, high, low, close, volume]
    """

def get_fundamentals(symbol: str) -> dict:
    """
    Returns: {pe, pb, roe, market_cap, revenue_growth, ...}
    """
```

### Caching (`data/cache.py`)

- SQLite database at `~/.quantkit/data.db`
- Table `ohlcv`: symbol, date, open, high, low, close, volume
- Table `fundamentals`: symbol, fetch_date, pe, pb, roe, market_cap, revenue_growth
- Cache validity: OHLCV data refreshed if last fetch > 1 day; fundamentals refreshed if > 7 days

### Adapters

- `tushare_src.py`: Requires `TUSHARE_TOKEN` env var. Falls back to error message if not set.
- `yfinance_src.py`: No auth required. Uses `yfinance.download()`.

## Portfolio Management

### CSV Import Format

```csv
symbol,buy_date,buy_price,quantity,market
AAPL,2024-03-15,172.50,100,US
600519.SH,2024-06-01,1680.00,200,CN
```

- `market` column: `US` or `CN`, used for display/grouping
- Stored in SQLite table `positions`
- Multiple imports append (no dedup — user manages their CSV)
- Menu option to list all current positions as a Rich table

## Module 1: Factor Check

### Factors (6 dimensions)

| Factor | Source | Green | Yellow | Red |
|--------|--------|-------|--------|-----|
| PE (TTM) | fundamentals | < 50th percentile of own 5-year history | 50-80th | > 80th |
| PB | fundamentals | < 50th percentile of own 5-year history | 50-80th | > 80th |
| ROE | fundamentals | > 15% | 10-15% | < 10% |
| Revenue Growth | fundamentals | > 10% | 0-10% | < 0% |
| Volatility (60d) | OHLCV | < 25% annualized | 25-40% | > 40% |
| Momentum (20d) | OHLCV | -10% to +20% | +20% to +40% | > +40% (chasing) or < -10% (falling) |

### Interaction

```
Factor Check → [1] Single stock  [2] All positions
→ Input symbol (or auto-load positions)
→ Rich table output with colored traffic lights per factor
→ Press Enter to return
```

### Output Example

```
╭─────────── AAPL Factor Check ───────────╮
│ Factor           Value    Status         │
│ PE (TTM)         28.5     🟡 67th pct   │
│ PB               45.2     🔴 92nd pct   │
│ ROE              26.3%    🟢 Healthy    │
│ Revenue Growth   8.2%     🟡 Moderate   │
│ Volatility (60d) 22.1%    🟢 Low        │
│ Momentum (20d)   +5.3%    🟢 Normal     │
╰──────────────────────────────────────────╯
```

## Module 2: Strategy Backtest

### Built-in Strategies (no coding required)

**1. MA Cross (均线交叉)**
- Parameters: short_window (default 5), long_window (default 20)
- Buy: short MA crosses above long MA
- Sell: short MA crosses below long MA

**2. Low PE (低估值买入)**
- Parameters: buy_percentile (default 20), sell_percentile (default 50)
- Buy: PE drops below buy_percentile of its rolling 3-year history
- Sell: PE returns above sell_percentile

**3. DCA (定投)**
- Parameters: amount (default 10000), day_of_month (default 1)
- Buy: fixed amount on specified day each month
- Sell: never (hold until end)

### Backtest Engine

- Bar-by-bar daily simulation
- Slippage: configurable, default 10 bps
- Commission: configurable, default 5 bps
- Initial capital: configurable, default 100,000
- No short selling, no margin

### Interaction

```
Strategy Backtest → Select strategy [1/2/3]
→ Input symbol → Input date range (default: last 3 years)
→ Confirm parameters (or use defaults)
→ Output: plotext net value chart + Rich performance table
→ Disclaimer: "Backtest ≠ live trading. Past performance ≠ future results."
```

### Performance Metrics

| Metric | Description |
|--------|-------------|
| Total Return | Cumulative % return |
| Annualized Return | CAGR |
| Sharpe Ratio | Risk-adjusted return (rf=0) |
| Max Drawdown | Worst peak-to-trough |
| Win Rate | % of profitable trades |
| Trade Count | Total number of trades |
| vs Benchmark | Return vs buy-and-hold same stock |

## Module 3: Risk Lens

### Analysis Dimensions

**1. Concentration**
- Calculate each position's weight by current market value
- Threshold: > 30% single position → red warning
- Display: Rich horizontal bar chart

**2. Correlation Matrix**
- Pairwise correlation of daily returns (last 1 year)
- Display: Rich table with colored cells (dark red = high correlation > 0.7)
- Summary: "X out of Y pairs are highly correlated — limited diversification"

**3. Volatility Contribution**
- Each stock's marginal contribution to portfolio volatility
- Display: Rich table sorted by contribution (highest first)

**4. Drawdown Simulation**
- Using historical daily returns, calculate portfolio's historical max drawdown
- One-line summary: "Based on history, your portfolio could drop up to X% from peak"
- Show the worst drawdown period (start date → trough date → recovery date)

### Interaction

```
Risk Lens → Auto-loads all positions
→ Fetches latest prices → Calculates current weights
→ Displays all 4 analyses sequentially
→ Press Enter to return
```

## Terminal UI

### Launch

```bash
python -m quantkit
```

### Main Menu

```
╭──────────── QuantKit ────────────╮
│                                  │
│   [1] Factor Check               │
│   [2] Strategy Backtest          │
│   [3] Risk Lens                  │
│   [4] Portfolio Management       │
│   [5] Settings                   │
│   [0] Exit                       │
│                                  │
╰──────────────────────────────────╯
```

### UI Principles

- All navigation via number keys
- Stock codes and dates entered via `rich.prompt.Prompt`
- Results displayed in Rich panels/tables
- Charts rendered via plotext (inline in terminal)
- Errors shown as red Rich panels, never raw tracebacks
- After each function completes, "Press Enter to return" prompt

### Settings

Stored in `~/.quantkit/config.json`:
- `tushare_token`: Tushare API token
- `default_capital`: Default initial capital for backtest (100000)
- `slippage_bps`: Default slippage in bps (10)
- `commission_bps`: Default commission in bps (5)

## Documentation

| File | Purpose | Owner |
|------|---------|-------|
| `PLAN.md` | Implementation plan, milestones, progress tracking | Claude Code |
| `PROJECT.md` | Architecture overview, module interfaces, setup guide | Gemini |
| `LOG.md` | Timestamped development log: what changed, who did it, why | Gemini |

## Dependencies

```toml
[project]
dependencies = [
    "rich>=13.0",
    "plotext>=5.2",
    "pandas>=2.0",
    "numpy>=1.24",
    "yfinance>=0.2.31",
    "tushare>=1.4",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]
```

## Out of Scope

- No web UI
- No auto-trading or order execution
- No real-time streaming data
- No custom factor definition (v1)
- No custom strategy coding (v1)
- No multi-portfolio support (v1)

# QuantKit Project Documentation

QuantKit is a terminal-based personal investment toolkit for A-shares and US stocks, designed for individual investors to analyze stock health, validate strategies, and understand portfolio risks.

## Architecture

The project follows a layered architecture:
- **Data Layer (`data/`)**: Unified provider with Tushare (A-shares) and yfinance (US) adapters, supported by a SQLite cache layer to minimize API calls.
- **Analysis Layer**:
    - **Factor Check (`factor/`)**: 6-dimension health check (PE, PB, ROE, Revenue Growth, Volatility, Momentum).
    - **Strategy Backtest (`backtest/`)**: Bar-by-bar daily simulation for MA Cross, Low PE, and DCA strategies.
    - **Risk Lens (`risk/`)**: Analysis of concentration, correlation, volatility contribution, and historical drawdown.
- **UI Layer (`cli.py`)**: Rich-based menu system and Plotext-based terminal charts.

## Module Interfaces

- **Data Provider**: `get_ohlcv(symbol, start, end)` and `get_fundamentals(symbol)`.
- **Portfolio**: `import_csv(path)`, `list_positions()`, and `clear_positions()`.
- **Factor Engine**: `compute_factors(ohlcv, fundamentals)` and `rate_factor(name, value)`.
- **Backtest Engine**: `run_backtest(ohlcv, signals, capital, slippage, commission)` and `compute_metrics(equity, trades)`.
- **Risk Engine**: `compute_concentration()`, `compute_correlation_matrix()`, `compute_volatility_contribution()`, and `compute_max_drawdown()`.

## Directory Structure

```
quantkit/
├── src/quantkit/
│   ├── __main__.py         # Entry point: python -m quantkit
│   ├── cli.py              # Rich menu system
│   ├── config.py           # Settings management (~/.quantkit/config.json)
│   ├── portfolio.py        # CSV import, position storage
│   ├── data/
│   │   ├── provider.py     # Unified get_ohlcv / get_fundamentals
│   │   ├── tushare_src.py  # Tushare adapter (A-shares)
│   │   ├── yfinance_src.py # yfinance adapter (US stocks)
│   │   └── cache.py        # SQLite cache layer
│   ├── factor/
│   │   └── engine.py       # Factor computation + rating
│   ├── backtest/
│   │   ├── engine.py       # Bar-by-bar backtest engine
│   │   └── strategies.py   # MA cross, low PE, DCA
│   └── risk/
│       └── engine.py       # Concentration, correlation, vol, drawdown
├── tests/
│   ├── test_config.py
│   ├── test_cache.py
│   ├── test_data.py
│   ├── test_portfolio.py
│   ├── test_factor.py
│   ├── test_backtest.py
│   ├── test_risk.py
│   └── test_integration.py
├── PLAN.md
├── PROJECT.md
├── LOG.md
├── pyproject.toml
└── .gitignore
```

## Installation & Usage

```bash
# Installation
uv pip install -e ".[dev]"

# Running the App
uv run python -m quantkit

# Running Tests
uv run pytest tests/ -v
```

## Configuration

Settings are stored at `~/.quantkit/config.json`:
- `tushare_token`: API token for A-share data.
- `default_capital`: Default initial capital for backtests (default: 100,000).
- `slippage_bps`: Default slippage in basis points (default: 10).
- `commission_bps`: Default commission in basis points (default: 5).

## Data Sources

- **US Stocks**: yfinance (free, no authentication required)
- **A-Shares (CN)**: Tushare (requires token, get one at https://tushare.pro)

## Team

- **Claude Code**: Architect & PM — plan, code review, test execution
- **Codex CLI**: Developer — code implementation (Tasks 1-10)
- **Gemini CLI**: QA & Documentation — documentation (Task 11)

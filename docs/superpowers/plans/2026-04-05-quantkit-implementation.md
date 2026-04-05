# QuantKit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a terminal-based personal investment toolkit with factor check, strategy backtest, and risk lens modules.

**Architecture:** Python package with Rich TUI, three independent analysis modules sharing a unified data layer (Tushare + yfinance) with SQLite caching. Menu-driven interaction, plotext for terminal charts.

**Tech Stack:** Python 3.11+, rich, plotext, pandas, numpy, yfinance, tushare, sqlite3, pytest

**Spec:** `docs/superpowers/specs/2026-04-05-quantkit-design.md`

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/quantkit/__init__.py`
- Create: `src/quantkit/__main__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "quantkit"
version = "0.1.0"
description = "Terminal-based personal investment toolkit"
requires-python = ">=3.11"
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

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
*.db
.DS_Store
```

- [ ] **Step 3: Create src/quantkit/__init__.py**

```python
"""QuantKit - Personal investment toolkit."""
```

- [ ] **Step 4: Create src/quantkit/__main__.py**

```python
"""Entry point: python -m quantkit"""

from quantkit.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Create empty directories and __init__ files**

Create these files (all empty or with module docstring):
- `src/quantkit/data/__init__.py`
- `src/quantkit/factor/__init__.py`
- `src/quantkit/backtest/__init__.py`
- `src/quantkit/risk/__init__.py`
- `tests/__init__.py`

- [ ] **Step 6: Create minimal cli.py stub**

Create `src/quantkit/cli.py`:

```python
"""Rich menu system for QuantKit."""

from rich.console import Console

console = Console()


def main() -> None:
    console.print("[bold green]QuantKit[/bold green] - Coming soon")
```

- [ ] **Step 7: Install in dev mode and verify**

Run: `cd /Users/wuzikang/Project/quantkit && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

Then: `python -m quantkit`

Expected: Prints "QuantKit - Coming soon"

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: project scaffold with pyproject.toml and package structure"
```

---

## Task 2: Settings & Config

**Files:**
- Create: `src/quantkit/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_config.py`:

```python
"""Tests for config module."""

import json
import os
from pathlib import Path

from quantkit.config import load_config, save_config, get_data_dir


def test_get_data_dir_creates_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    data_dir = get_data_dir()
    assert data_dir.exists()
    assert data_dir.name == ".quantkit"


def test_load_config_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    cfg = load_config()
    assert cfg["default_capital"] == 100_000
    assert cfg["slippage_bps"] == 10
    assert cfg["commission_bps"] == 5
    assert cfg["tushare_token"] == ""


def test_save_and_load_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    cfg = load_config()
    cfg["tushare_token"] = "abc123"
    save_config(cfg)
    cfg2 = load_config()
    assert cfg2["tushare_token"] == "abc123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'quantkit.config'`

- [ ] **Step 3: Write implementation**

Create `src/quantkit/config.py`:

```python
"""Configuration management. Stored at ~/.quantkit/config.json."""

import json
from pathlib import Path
import os

DEFAULTS = {
    "tushare_token": "",
    "default_capital": 100_000,
    "slippage_bps": 10,
    "commission_bps": 5,
}


def get_data_dir() -> Path:
    """Return the quantkit data directory, creating it if needed."""
    path = Path(os.environ.get("QUANTKIT_HOME", Path.home() / ".quantkit"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _config_path() -> Path:
    return get_data_dir() / "config.json"


def load_config() -> dict:
    """Load config from disk, falling back to defaults."""
    path = _config_path()
    cfg = dict(DEFAULTS)
    if path.exists():
        with open(path) as f:
            cfg.update(json.load(f))
    return cfg


def save_config(cfg: dict) -> None:
    """Save config to disk."""
    path = _config_path()
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/quantkit/config.py tests/test_config.py
git commit -m "feat: add config module with load/save and defaults"
```

---

## Task 3: SQLite Cache Layer

**Files:**
- Create: `src/quantkit/data/cache.py`
- Create: `tests/test_cache.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cache.py`:

```python
"""Tests for SQLite cache layer."""

import pandas as pd
from datetime import date, timedelta

from quantkit.data.cache import OHLCVCache


def test_cache_save_and_load(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "test.db")
    df = pd.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 2)],
        "open": [100.0, 101.0],
        "high": [102.0, 103.0],
        "low": [99.0, 100.0],
        "close": [101.0, 102.0],
        "volume": [1000, 1100],
    })
    cache.save_ohlcv("AAPL", df)
    result = cache.load_ohlcv("AAPL", "2024-01-01", "2024-01-02")
    assert len(result) == 2
    assert result.iloc[0]["close"] == 101.0


def test_cache_returns_none_when_missing(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "test.db")
    result = cache.load_ohlcv("MISSING", "2024-01-01", "2024-01-02")
    assert result is None


def test_cache_save_and_load_fundamentals(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "test.db")
    data = {"pe": 28.5, "pb": 6.2, "roe": 0.26, "market_cap": 3e12, "revenue_growth": 0.08}
    cache.save_fundamentals("AAPL", data)
    result = cache.load_fundamentals("AAPL")
    assert result is not None
    assert result["pe"] == 28.5


def test_fundamentals_cache_expires(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "test.db")
    data = {"pe": 28.5, "pb": 6.2, "roe": 0.26, "market_cap": 3e12, "revenue_growth": 0.08}
    cache.save_fundamentals("AAPL", data)
    # Force expire by setting fetch_date to 8 days ago
    cache._conn.execute(
        "UPDATE fundamentals SET fetch_date = ? WHERE symbol = ?",
        ((date.today() - timedelta(days=8)).isoformat(), "AAPL"),
    )
    cache._conn.commit()
    result = cache.load_fundamentals("AAPL")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cache.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write implementation**

Create `src/quantkit/data/cache.py`:

```python
"""SQLite cache for market data."""

import sqlite3
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from quantkit.config import get_data_dir


class OHLCVCache:
    """Cache OHLCV and fundamentals data in SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = get_data_dir() / "data.db"
        self._conn = sqlite3.connect(str(db_path))
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL,
                volume REAL,
                PRIMARY KEY (symbol, date)
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS fundamentals (
                symbol TEXT PRIMARY KEY,
                fetch_date TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def save_ohlcv(self, symbol: str, df: pd.DataFrame) -> None:
        """Save OHLCV dataframe to cache."""
        for _, row in df.iterrows():
            self._conn.execute(
                "INSERT OR REPLACE INTO ohlcv VALUES (?, ?, ?, ?, ?, ?, ?)",
                (symbol, str(row["date"]), row["open"], row["high"],
                 row["low"], row["close"], row["volume"]),
            )
        self._conn.commit()

    def load_ohlcv(self, symbol: str, start: str, end: str) -> Optional[pd.DataFrame]:
        """Load OHLCV data from cache. Returns None if no data found."""
        cursor = self._conn.execute(
            "SELECT date, open, high, low, close, volume FROM ohlcv "
            "WHERE symbol = ? AND date >= ? AND date <= ? ORDER BY date",
            (symbol, start, end),
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def save_fundamentals(self, symbol: str, data: dict) -> None:
        """Save fundamentals data to cache."""
        self._conn.execute(
            "INSERT OR REPLACE INTO fundamentals VALUES (?, ?, ?)",
            (symbol, date.today().isoformat(), json.dumps(data)),
        )
        self._conn.commit()

    def load_fundamentals(self, symbol: str, max_age_days: int = 7) -> Optional[dict]:
        """Load fundamentals from cache. Returns None if expired or missing."""
        cursor = self._conn.execute(
            "SELECT fetch_date, data FROM fundamentals WHERE symbol = ?",
            (symbol,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        fetch_date = date.fromisoformat(row[0])
        if date.today() - fetch_date > timedelta(days=max_age_days):
            return None
        return json.loads(row[1])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cache.py -v`

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/quantkit/data/cache.py tests/test_cache.py
git commit -m "feat: add SQLite cache layer for OHLCV and fundamentals data"
```

---

## Task 4: Data Provider (yfinance + Tushare adapters)

**Files:**
- Create: `src/quantkit/data/yfinance_src.py`
- Create: `src/quantkit/data/tushare_src.py`
- Create: `src/quantkit/data/provider.py`
- Create: `tests/test_data.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_data.py`:

```python
"""Tests for data provider."""

import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import date

from quantkit.data.provider import get_ohlcv, get_fundamentals, is_cn_symbol


def test_is_cn_symbol():
    assert is_cn_symbol("600519.SH") is True
    assert is_cn_symbol("000001.SZ") is True
    assert is_cn_symbol("AAPL") is False
    assert is_cn_symbol("TSLA") is False


def test_get_ohlcv_routes_us_to_yfinance(tmp_path):
    mock_df = pd.DataFrame({
        "date": [date(2024, 1, 2)],
        "open": [100.0], "high": [102.0], "low": [99.0],
        "close": [101.0], "volume": [1000],
    })
    with patch("quantkit.data.provider._fetch_yfinance_ohlcv", return_value=mock_df):
        with patch("quantkit.data.provider._get_cache") as mock_cache:
            mock_cache.return_value.load_ohlcv.return_value = None
            result = get_ohlcv("AAPL", "2024-01-01", "2024-01-05")
            assert len(result) == 1
            assert result.iloc[0]["close"] == 101.0


def test_get_ohlcv_uses_cache_when_available(tmp_path):
    cached_df = pd.DataFrame({
        "date": [date(2024, 1, 2)],
        "open": [100.0], "high": [102.0], "low": [99.0],
        "close": [101.0], "volume": [1000],
    })
    with patch("quantkit.data.provider._get_cache") as mock_cache:
        mock_cache.return_value.load_ohlcv.return_value = cached_df
        result = get_ohlcv("AAPL", "2024-01-01", "2024-01-05")
        assert len(result) == 1


def test_get_fundamentals_routes_us(tmp_path):
    mock_data = {"pe": 28.5, "pb": 6.2, "roe": 0.26, "market_cap": 3e12, "revenue_growth": 0.08}
    with patch("quantkit.data.provider._fetch_yfinance_fundamentals", return_value=mock_data):
        with patch("quantkit.data.provider._get_cache") as mock_cache:
            mock_cache.return_value.load_fundamentals.return_value = None
            result = get_fundamentals("AAPL")
            assert result["pe"] == 28.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write yfinance adapter**

Create `src/quantkit/data/yfinance_src.py`:

```python
"""yfinance adapter for US stock data."""

import pandas as pd
import yfinance as yf


def fetch_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch OHLCV data from yfinance."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end)
    if df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    df = df.reset_index()
    df = df.rename(columns={
        "Date": "date", "Open": "open", "High": "high",
        "Low": "low", "Close": "close", "Volume": "volume",
    })
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df[["date", "open", "high", "low", "close", "volume"]]


def fetch_fundamentals(symbol: str) -> dict:
    """Fetch fundamental data from yfinance."""
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        "pe": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "roe": info.get("returnOnEquity"),
        "market_cap": info.get("marketCap"),
        "revenue_growth": info.get("revenueGrowth"),
    }
```

- [ ] **Step 4: Write tushare adapter**

Create `src/quantkit/data/tushare_src.py`:

```python
"""Tushare adapter for A-share data."""

import os
from typing import Optional

import pandas as pd


def _get_api():
    """Get tushare API instance."""
    import tushare as ts
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise RuntimeError(
            "TUSHARE_TOKEN not set. Get a token at https://tushare.pro "
            "and set it via QuantKit Settings or: export TUSHARE_TOKEN=your_token"
        )
    return ts.pro_api(token)


def fetch_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch OHLCV data from Tushare."""
    api = _get_api()
    # Tushare wants dates as YYYYMMDD
    start_fmt = start.replace("-", "")
    end_fmt = end.replace("-", "")
    df = api.daily(ts_code=symbol, start_date=start_fmt, end_date=end_fmt)
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    df = df.rename(columns={
        "trade_date": "date", "vol": "volume",
    })
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.sort_values("date")
    return df[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def fetch_fundamentals(symbol: str) -> dict:
    """Fetch fundamental data from Tushare."""
    api = _get_api()
    # Get latest daily basic
    df = api.daily_basic(ts_code=symbol, fields="pe_ttm,pb,total_mv")
    if df is None or df.empty:
        return {"pe": None, "pb": None, "roe": None, "market_cap": None, "revenue_growth": None}
    row = df.iloc[0]
    # Get ROE and revenue growth from financial indicators
    fin = api.fina_indicator(ts_code=symbol, fields="roe,revenue_yoy")
    roe = None
    rev_growth = None
    if fin is not None and not fin.empty:
        roe = fin.iloc[0].get("roe")
        if roe is not None:
            roe = roe / 100.0  # Convert percentage to decimal
        rev_growth = fin.iloc[0].get("revenue_yoy")
        if rev_growth is not None:
            rev_growth = rev_growth / 100.0
    return {
        "pe": row.get("pe_ttm"),
        "pb": row.get("pb"),
        "roe": roe,
        "market_cap": row.get("total_mv"),
        "revenue_growth": rev_growth,
    }
```

- [ ] **Step 5: Write unified provider**

Create `src/quantkit/data/provider.py`:

```python
"""Unified data provider with auto-routing and caching."""

import re
from typing import Optional

import pandas as pd

from quantkit.data.cache import OHLCVCache
from quantkit.data import yfinance_src, tushare_src

_cache_instance: Optional[OHLCVCache] = None


def _get_cache() -> OHLCVCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = OHLCVCache()
    return _cache_instance


def is_cn_symbol(symbol: str) -> bool:
    """Check if symbol is a Chinese A-share (e.g. 600519.SH, 000001.SZ)."""
    return bool(re.match(r"^\d{6}\.(SH|SZ|BJ)$", symbol, re.IGNORECASE))


def _fetch_yfinance_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    return yfinance_src.fetch_ohlcv(symbol, start, end)


def _fetch_tushare_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    return tushare_src.fetch_ohlcv(symbol, start, end)


def _fetch_yfinance_fundamentals(symbol: str) -> dict:
    return yfinance_src.fetch_fundamentals(symbol)


def _fetch_tushare_fundamentals(symbol: str) -> dict:
    return tushare_src.fetch_fundamentals(symbol)


def get_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Get OHLCV data, using cache when available."""
    cache = _get_cache()
    cached = cache.load_ohlcv(symbol, start, end)
    if cached is not None:
        return cached

    if is_cn_symbol(symbol):
        df = _fetch_tushare_ohlcv(symbol, start, end)
    else:
        df = _fetch_yfinance_ohlcv(symbol, start, end)

    if not df.empty:
        cache.save_ohlcv(symbol, df)
    return df


def get_fundamentals(symbol: str) -> dict:
    """Get fundamentals data, using cache when available."""
    cache = _get_cache()
    cached = cache.load_fundamentals(symbol)
    if cached is not None:
        return cached

    if is_cn_symbol(symbol):
        data = _fetch_tushare_fundamentals(symbol)
    else:
        data = _fetch_yfinance_fundamentals(symbol)

    cache.save_fundamentals(symbol, data)
    return data
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_data.py -v`

Expected: 4 passed

- [ ] **Step 7: Commit**

```bash
git add src/quantkit/data/ tests/test_data.py
git commit -m "feat: add data provider with yfinance/tushare adapters and caching"
```

---

## Task 5: Portfolio Management

**Files:**
- Create: `src/quantkit/portfolio.py`
- Create: `tests/test_portfolio.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_portfolio.py`:

```python
"""Tests for portfolio management."""

import csv
from pathlib import Path

from quantkit.portfolio import import_csv, list_positions, clear_positions


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_import_csv_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    csv_path = tmp_path / "portfolio.csv"
    _write_csv(csv_path, [
        {"symbol": "AAPL", "buy_date": "2024-03-15", "buy_price": "172.50",
         "quantity": "100", "market": "US"},
        {"symbol": "600519.SH", "buy_date": "2024-06-01", "buy_price": "1680.00",
         "quantity": "200", "market": "CN"},
    ])
    count = import_csv(csv_path)
    assert count == 2
    positions = list_positions()
    assert len(positions) == 2
    assert positions[0]["symbol"] == "AAPL"


def test_import_csv_appends(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    csv_path = tmp_path / "p.csv"
    _write_csv(csv_path, [
        {"symbol": "AAPL", "buy_date": "2024-03-15", "buy_price": "172.50",
         "quantity": "100", "market": "US"},
    ])
    import_csv(csv_path)
    import_csv(csv_path)
    positions = list_positions()
    assert len(positions) == 2  # Appended, not deduped


def test_clear_positions(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    csv_path = tmp_path / "p.csv"
    _write_csv(csv_path, [
        {"symbol": "AAPL", "buy_date": "2024-03-15", "buy_price": "172.50",
         "quantity": "100", "market": "US"},
    ])
    import_csv(csv_path)
    clear_positions()
    assert len(list_positions()) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_portfolio.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write implementation**

Create `src/quantkit/portfolio.py`:

```python
"""Portfolio management: CSV import, position storage, listing."""

import csv
import sqlite3
from pathlib import Path
from typing import Optional

from quantkit.config import get_data_dir

_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        db_path = get_data_dir() / "data.db"
        _conn = sqlite3.connect(str(db_path))
        _conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                buy_date TEXT NOT NULL,
                buy_price REAL NOT NULL,
                quantity REAL NOT NULL,
                market TEXT NOT NULL
            )
        """)
        _conn.commit()
    return _conn


def import_csv(path: Path) -> int:
    """Import positions from CSV file. Returns number of rows imported."""
    conn = _get_conn()
    count = 0
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                "INSERT INTO positions (symbol, buy_date, buy_price, quantity, market) "
                "VALUES (?, ?, ?, ?, ?)",
                (row["symbol"], row["buy_date"], float(row["buy_price"]),
                 float(row["quantity"]), row["market"]),
            )
            count += 1
    conn.commit()
    return count


def list_positions() -> list[dict]:
    """Return all positions as a list of dicts."""
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT symbol, buy_date, buy_price, quantity, market FROM positions ORDER BY buy_date"
    )
    return [
        {"symbol": r[0], "buy_date": r[1], "buy_price": r[2],
         "quantity": r[3], "market": r[4]}
        for r in cursor.fetchall()
    ]


def clear_positions() -> None:
    """Delete all positions."""
    conn = _get_conn()
    conn.execute("DELETE FROM positions")
    conn.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_portfolio.py -v`

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/quantkit/portfolio.py tests/test_portfolio.py
git commit -m "feat: add portfolio management with CSV import and SQLite storage"
```

---

## Task 6: Factor Check Engine

**Files:**
- Create: `src/quantkit/factor/engine.py`
- Create: `tests/test_factor.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_factor.py`:

```python
"""Tests for factor check engine."""

import pandas as pd
from datetime import date, timedelta
from unittest.mock import patch

from quantkit.factor.engine import compute_factors, rate_factor


def test_rate_factor_pe_green():
    assert rate_factor("pe", 15.0, percentile=30) == ("green", "30th pct")


def test_rate_factor_pe_yellow():
    assert rate_factor("pe", 25.0, percentile=65) == ("yellow", "65th pct")


def test_rate_factor_pe_red():
    assert rate_factor("pe", 40.0, percentile=85) == ("red", "85th pct")


def test_rate_factor_roe_green():
    assert rate_factor("roe", 0.20) == ("green", "Healthy")


def test_rate_factor_roe_yellow():
    assert rate_factor("roe", 0.12) == ("yellow", "Moderate")


def test_rate_factor_roe_red():
    assert rate_factor("roe", 0.05) == ("red", "Low")


def test_rate_factor_volatility_green():
    assert rate_factor("volatility", 0.20) == ("green", "Low")


def test_rate_factor_volatility_red():
    assert rate_factor("volatility", 0.45) == ("red", "High")


def test_rate_factor_momentum_green():
    assert rate_factor("momentum", 0.05) == ("green", "Normal")


def test_rate_factor_momentum_red_chasing():
    assert rate_factor("momentum", 0.45) == ("red", "Chasing")


def test_rate_factor_momentum_red_falling():
    assert rate_factor("momentum", -0.15) == ("red", "Falling")


def test_compute_factors_returns_all_six():
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(120)]
    ohlcv = pd.DataFrame({
        "date": dates,
        "open": [100 + i * 0.1 for i in range(120)],
        "high": [101 + i * 0.1 for i in range(120)],
        "low": [99 + i * 0.1 for i in range(120)],
        "close": [100.5 + i * 0.1 for i in range(120)],
        "volume": [1000] * 120,
    })
    fundamentals = {
        "pe": 28.5, "pb": 6.2, "roe": 0.26,
        "market_cap": 3e12, "revenue_growth": 0.08,
    }
    result = compute_factors(ohlcv, fundamentals)
    assert len(result) == 6
    assert all(k in result for k in ["pe", "pb", "roe", "revenue_growth", "volatility", "momentum"])
    for factor_data in result.values():
        assert "value" in factor_data
        assert "rating" in factor_data
        assert "label" in factor_data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_factor.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write implementation**

Create `src/quantkit/factor/engine.py`:

```python
"""Factor check engine: compute and rate 6 factors."""

import numpy as np
import pandas as pd
from typing import Optional


def rate_factor(
    name: str, value: Optional[float], percentile: Optional[float] = None
) -> tuple[str, str]:
    """Rate a factor value. Returns (color, label)."""
    if value is None:
        return ("yellow", "N/A")

    if name in ("pe", "pb"):
        if percentile is None:
            return ("yellow", "N/A")
        if percentile < 50:
            return ("green", f"{percentile:.0f}th pct")
        elif percentile < 80:
            return ("yellow", f"{percentile:.0f}th pct")
        else:
            return ("red", f"{percentile:.0f}th pct")

    if name == "roe":
        if value > 0.15:
            return ("green", "Healthy")
        elif value > 0.10:
            return ("yellow", "Moderate")
        else:
            return ("red", "Low")

    if name == "revenue_growth":
        if value > 0.10:
            return ("green", "Strong")
        elif value > 0:
            return ("yellow", "Moderate")
        else:
            return ("red", "Negative")

    if name == "volatility":
        if value < 0.25:
            return ("green", "Low")
        elif value < 0.40:
            return ("yellow", "Medium")
        else:
            return ("red", "High")

    if name == "momentum":
        if value > 0.40:
            return ("red", "Chasing")
        elif value < -0.10:
            return ("red", "Falling")
        elif value > 0.20:
            return ("yellow", "Elevated")
        else:
            return ("green", "Normal")

    return ("yellow", "Unknown")


def _annualized_volatility(closes: pd.Series, window: int = 60) -> Optional[float]:
    """Calculate annualized volatility from last N days of close prices."""
    if len(closes) < window:
        return None
    recent = closes.tail(window)
    returns = recent.pct_change().dropna()
    return float(returns.std() * np.sqrt(252))


def _momentum(closes: pd.Series, window: int = 20) -> Optional[float]:
    """Calculate momentum as % change over last N days."""
    if len(closes) < window:
        return None
    return float((closes.iloc[-1] / closes.iloc[-window] - 1))


def compute_factors(ohlcv: pd.DataFrame, fundamentals: dict) -> dict:
    """Compute all 6 factors. Returns dict of {name: {value, rating, label}}."""
    results = {}

    # PE
    pe_val = fundamentals.get("pe")
    pe_rating, pe_label = rate_factor("pe", pe_val, percentile=50)  # Default 50th if no history
    results["pe"] = {"value": pe_val, "rating": pe_rating, "label": pe_label}

    # PB
    pb_val = fundamentals.get("pb")
    pb_rating, pb_label = rate_factor("pb", pb_val, percentile=50)
    results["pb"] = {"value": pb_val, "rating": pb_rating, "label": pb_label}

    # ROE
    roe_val = fundamentals.get("roe")
    roe_rating, roe_label = rate_factor("roe", roe_val)
    results["roe"] = {"value": roe_val, "rating": roe_rating, "label": roe_label}

    # Revenue Growth
    rg_val = fundamentals.get("revenue_growth")
    rg_rating, rg_label = rate_factor("revenue_growth", rg_val)
    results["revenue_growth"] = {"value": rg_val, "rating": rg_rating, "label": rg_label}

    # Volatility
    vol_val = _annualized_volatility(ohlcv["close"])
    vol_rating, vol_label = rate_factor("volatility", vol_val)
    results["volatility"] = {"value": vol_val, "rating": vol_rating, "label": vol_label}

    # Momentum
    mom_val = _momentum(ohlcv["close"])
    mom_rating, mom_label = rate_factor("momentum", mom_val)
    results["momentum"] = {"value": mom_val, "rating": mom_rating, "label": mom_label}

    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_factor.py -v`

Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add src/quantkit/factor/engine.py tests/test_factor.py
git commit -m "feat: add factor check engine with 6 factors and traffic light rating"
```

---

## Task 7: Backtest Engine

**Files:**
- Create: `src/quantkit/backtest/engine.py`
- Create: `src/quantkit/backtest/strategies.py`
- Create: `tests/test_backtest.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_backtest.py`:

```python
"""Tests for backtest engine."""

import pandas as pd
from datetime import date, timedelta

from quantkit.backtest.engine import run_backtest, compute_metrics
from quantkit.backtest.strategies import ma_cross_signals, dca_signals


def _make_ohlcv(n: int = 100, base: float = 100.0, trend: float = 0.1) -> pd.DataFrame:
    """Generate synthetic OHLCV data with a gentle uptrend."""
    dates = [date(2023, 1, 2) + timedelta(days=i) for i in range(n)]
    closes = [base + i * trend for i in range(n)]
    return pd.DataFrame({
        "date": dates,
        "open": [c - 0.5 for c in closes],
        "high": [c + 1.0 for c in closes],
        "low": [c - 1.0 for c in closes],
        "close": closes,
        "volume": [1000] * n,
    })


def test_ma_cross_generates_signals():
    ohlcv = _make_ohlcv(50)
    signals = ma_cross_signals(ohlcv, short_window=5, long_window=10)
    assert len(signals) == len(ohlcv)
    assert set(signals.unique()).issubset({0, 1})  # 1=hold/buy, 0=sell/no position


def test_dca_generates_signals():
    ohlcv = _make_ohlcv(90)
    signals = dca_signals(ohlcv, day_of_month=1)
    assert len(signals) == len(ohlcv)
    # DCA should have some buy signals
    assert signals.sum() > 0


def test_run_backtest_returns_result():
    ohlcv = _make_ohlcv(100)
    signals = ma_cross_signals(ohlcv, short_window=5, long_window=20)
    result = run_backtest(ohlcv, signals, capital=100_000, slippage_bps=10, commission_bps=5)
    assert "equity_curve" in result
    assert "trades" in result
    assert len(result["equity_curve"]) == len(ohlcv)
    assert result["equity_curve"].iloc[0] == 100_000


def test_compute_metrics():
    equity = pd.Series([100_000, 101_000, 99_000, 102_000, 105_000])
    trades = [{"pnl": 1000}, {"pnl": -2000}, {"pnl": 3000}, {"pnl": 3000}]
    metrics = compute_metrics(equity, trades, days=252)
    assert "total_return" in metrics
    assert "max_drawdown" in metrics
    assert "sharpe" in metrics
    assert "win_rate" in metrics
    assert metrics["trade_count"] == 4
    assert metrics["win_rate"] == 0.75
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_backtest.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write strategies**

Create `src/quantkit/backtest/strategies.py`:

```python
"""Built-in backtest strategies. Each returns a signal Series (1=long, 0=flat)."""

import pandas as pd
import numpy as np


def ma_cross_signals(
    ohlcv: pd.DataFrame, short_window: int = 5, long_window: int = 20
) -> pd.Series:
    """MA crossover: 1 when short MA > long MA, else 0."""
    close = ohlcv["close"]
    short_ma = close.rolling(window=short_window).mean()
    long_ma = close.rolling(window=long_window).mean()
    signals = (short_ma > long_ma).astype(int)
    # No signal until both MAs are available
    signals.iloc[:long_window] = 0
    return signals


def low_pe_signals(
    pe_series: pd.Series, buy_percentile: int = 20, sell_percentile: int = 50,
    window: int = 756  # ~3 years of trading days
) -> pd.Series:
    """Low PE strategy: buy when PE < buy_percentile of rolling history."""
    signals = pd.Series(0, index=pe_series.index)
    position = 0
    for i in range(window, len(pe_series)):
        history = pe_series.iloc[max(0, i - window):i]
        buy_thresh = np.nanpercentile(history, buy_percentile)
        sell_thresh = np.nanpercentile(history, sell_percentile)
        current_pe = pe_series.iloc[i]
        if pd.isna(current_pe):
            signals.iloc[i] = position
            continue
        if position == 0 and current_pe < buy_thresh:
            position = 1
        elif position == 1 and current_pe > sell_thresh:
            position = 0
        signals.iloc[i] = position
    return signals


def dca_signals(ohlcv: pd.DataFrame, day_of_month: int = 1) -> pd.Series:
    """DCA: signal=1 on the specified day of month (or next trading day), else 0."""
    signals = pd.Series(0, index=ohlcv.index)
    dates = ohlcv["date"]
    prev_month = None
    for i, d in enumerate(dates):
        month = (d.year, d.month)
        if month != prev_month and d.day >= day_of_month:
            signals.iloc[i] = 1
            prev_month = month
        elif month != prev_month:
            pass  # Wait for the right day
        else:
            prev_month = month
    return signals
```

- [ ] **Step 4: Write backtest engine**

Create `src/quantkit/backtest/engine.py`:

```python
"""Bar-by-bar backtest engine."""

import numpy as np
import pandas as pd


def run_backtest(
    ohlcv: pd.DataFrame,
    signals: pd.Series,
    capital: float = 100_000,
    slippage_bps: float = 10,
    commission_bps: float = 5,
) -> dict:
    """Run a bar-by-bar backtest. Returns equity curve and trade list."""
    closes = ohlcv["close"].values
    sigs = signals.values
    n = len(closes)

    cash = capital
    shares = 0.0
    equity = np.zeros(n)
    trades = []
    entry_price = 0.0
    slip_rate = slippage_bps / 10_000
    comm_rate = commission_bps / 10_000

    for i in range(n):
        price = closes[i]

        if sigs[i] == 1 and shares == 0:
            # Buy
            exec_price = price * (1 + slip_rate)
            commission = exec_price * comm_rate
            max_shares = cash / (exec_price + commission)
            shares = int(max_shares)
            if shares > 0:
                cost = shares * exec_price + shares * commission
                cash -= cost
                entry_price = exec_price

        elif sigs[i] == 0 and shares > 0:
            # Sell
            exec_price = price * (1 - slip_rate)
            commission = shares * exec_price * comm_rate
            proceeds = shares * exec_price - commission
            pnl = proceeds - shares * entry_price
            trades.append({"pnl": pnl, "entry": entry_price, "exit": exec_price})
            cash += proceeds
            shares = 0

        equity[i] = cash + shares * price

    return {
        "equity_curve": pd.Series(equity, index=ohlcv.index),
        "trades": trades,
        "final_equity": equity[-1] if n > 0 else capital,
    }


def compute_metrics(equity: pd.Series, trades: list[dict], days: int = 252) -> dict:
    """Compute performance metrics from equity curve and trades."""
    total_return = (equity.iloc[-1] / equity.iloc[0] - 1) if len(equity) > 0 else 0
    n_days = len(equity)
    years = n_days / days if n_days > 0 else 1
    annualized = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    # Sharpe
    returns = equity.pct_change().dropna()
    sharpe = (returns.mean() / returns.std() * np.sqrt(days)) if len(returns) > 1 and returns.std() > 0 else 0

    # Max drawdown
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    max_drawdown = float(drawdown.min()) if len(drawdown) > 0 else 0

    # Win rate
    trade_count = len(trades)
    wins = sum(1 for t in trades if t["pnl"] > 0)
    win_rate = wins / trade_count if trade_count > 0 else 0

    return {
        "total_return": total_return,
        "annualized_return": annualized,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "trade_count": trade_count,
    }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_backtest.py -v`

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/quantkit/backtest/ tests/test_backtest.py
git commit -m "feat: add backtest engine with MA cross, low PE, and DCA strategies"
```

---

## Task 8: Risk Lens Engine

**Files:**
- Create: `src/quantkit/risk/engine.py`
- Create: `tests/test_risk.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_risk.py`:

```python
"""Tests for risk lens engine."""

import pandas as pd
import numpy as np
from datetime import date, timedelta

from quantkit.risk.engine import (
    compute_concentration,
    compute_correlation_matrix,
    compute_volatility_contribution,
    compute_max_drawdown,
)


def _make_returns(n: int = 252, k: int = 3, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic daily returns for k stocks."""
    rng = np.random.RandomState(seed)
    dates = [date(2023, 1, 2) + timedelta(days=i) for i in range(n)]
    data = {}
    for i in range(k):
        data[f"STOCK{i}"] = rng.normal(0.0005, 0.02, n)
    return pd.DataFrame(data, index=dates)


def test_concentration():
    weights = {"AAPL": 50_000, "GOOG": 30_000, "MSFT": 20_000}
    result = compute_concentration(weights)
    assert len(result) == 3
    assert abs(result["AAPL"]["weight"] - 0.5) < 0.01
    assert result["AAPL"]["warning"] is True  # > 30%


def test_correlation_matrix():
    returns = _make_returns(252, 3)
    corr = compute_correlation_matrix(returns)
    assert corr.shape == (3, 3)
    # Diagonal should be 1.0
    for i in range(3):
        assert abs(corr.iloc[i, i] - 1.0) < 0.01


def test_volatility_contribution():
    returns = _make_returns(252, 3)
    weights = {"STOCK0": 0.4, "STOCK1": 0.35, "STOCK2": 0.25}
    contrib = compute_volatility_contribution(returns, weights)
    assert len(contrib) == 3
    # Contributions should sum to approximately 1.0
    total = sum(c["contribution"] for c in contrib.values())
    assert abs(total - 1.0) < 0.1


def test_max_drawdown():
    # Create a simple portfolio equity curve
    equity = pd.Series([100, 110, 105, 95, 100, 108, 90, 95, 110])
    dd = compute_max_drawdown(equity)
    assert dd["max_drawdown"] < 0  # Negative number
    assert "peak_date_idx" in dd
    assert "trough_date_idx" in dd
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_risk.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write implementation**

Create `src/quantkit/risk/engine.py`:

```python
"""Risk lens engine: concentration, correlation, volatility contribution, drawdown."""

import numpy as np
import pandas as pd


def compute_concentration(market_values: dict[str, float]) -> dict:
    """Compute position weights and flag concentration risk (>30%)."""
    total = sum(market_values.values())
    if total == 0:
        return {}
    result = {}
    for symbol, mv in sorted(market_values.items(), key=lambda x: -x[1]):
        weight = mv / total
        result[symbol] = {
            "market_value": mv,
            "weight": weight,
            "warning": weight > 0.30,
        }
    return result


def compute_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Compute pairwise correlation matrix of daily returns."""
    return returns.corr()


def compute_volatility_contribution(
    returns: pd.DataFrame, weights: dict[str, float]
) -> dict:
    """Compute each stock's marginal contribution to portfolio volatility."""
    symbols = list(weights.keys())
    w = np.array([weights[s] for s in symbols])
    cov = returns[symbols].cov().values
    port_vol = np.sqrt(w @ cov @ w)

    if port_vol == 0:
        return {s: {"contribution": 0.0} for s in symbols}

    # Marginal contribution = (cov @ w) * w / port_var
    marginal = (cov @ w) * w / (port_vol ** 2)
    result = {}
    for i, s in enumerate(symbols):
        result[s] = {"contribution": float(marginal[i])}
    return result


def compute_max_drawdown(equity: pd.Series) -> dict:
    """Compute maximum drawdown from equity series."""
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    trough_idx = drawdown.idxmin()
    peak_idx = equity.loc[:trough_idx].idxmax()

    # Find recovery (if any)
    peak_value = equity.loc[peak_idx]
    recovery_idx = None
    after_trough = equity.loc[trough_idx:]
    recovered = after_trough[after_trough >= peak_value]
    if len(recovered) > 0:
        recovery_idx = recovered.index[0]

    return {
        "max_drawdown": float(drawdown.min()),
        "peak_date_idx": peak_idx,
        "trough_date_idx": trough_idx,
        "recovery_date_idx": recovery_idx,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_risk.py -v`

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/quantkit/risk/ tests/test_risk.py
git commit -m "feat: add risk lens engine with concentration, correlation, vol contribution, drawdown"
```

---

## Task 9: CLI Menu System

**Files:**
- Modify: `src/quantkit/cli.py`

- [ ] **Step 1: Write the full CLI implementation**

Replace `src/quantkit/cli.py` with:

```python
"""Rich menu system for QuantKit."""

from pathlib import Path

import plotext as plt
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.text import Text

from quantkit.config import load_config, save_config
from quantkit.data.provider import get_ohlcv, get_fundamentals
from quantkit.portfolio import import_csv, list_positions, clear_positions
from quantkit.factor.engine import compute_factors
from quantkit.backtest.engine import run_backtest, compute_metrics
from quantkit.backtest.strategies import ma_cross_signals, dca_signals
from quantkit.risk.engine import (
    compute_concentration,
    compute_correlation_matrix,
    compute_volatility_contribution,
    compute_max_drawdown,
)

console = Console()

RATING_ICONS = {"green": "[green]●[/green]", "yellow": "[yellow]●[/yellow]", "red": "[red]●[/red]"}


def _pause() -> None:
    Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")


def _error(msg: str) -> None:
    console.print(Panel(msg, title="Error", border_style="red"))


# ── Main Menu ──


def main() -> None:
    """Main menu loop."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold][1][/bold] Factor Check       Multi-dimensional health check\n"
            "[bold][2][/bold] Strategy Backtest   Validate buy/sell rules\n"
            "[bold][3][/bold] Risk Lens           Understand portfolio risk\n"
            "[bold][4][/bold] Portfolio           Import / view positions\n"
            "[bold][5][/bold] Settings            Configure tokens & defaults\n"
            "[bold][0][/bold] Exit",
            title="[bold green]QuantKit[/bold green]",
            subtitle="Personal Investment Toolkit",
            padding=(1, 2),
        ))
        choice = Prompt.ask("Choose", choices=["0", "1", "2", "3", "4", "5"], default="0")
        if choice == "0":
            console.print("[dim]Goodbye.[/dim]")
            break
        elif choice == "1":
            _menu_factor_check()
        elif choice == "2":
            _menu_backtest()
        elif choice == "3":
            _menu_risk_lens()
        elif choice == "4":
            _menu_portfolio()
        elif choice == "5":
            _menu_settings()


# ── Factor Check ──


def _menu_factor_check() -> None:
    console.clear()
    console.print(Panel("Factor Check", style="bold cyan"))
    mode = Prompt.ask("[1] Single stock  [2] All positions", choices=["1", "2"], default="1")

    if mode == "1":
        symbol = Prompt.ask("Stock symbol (e.g. AAPL or 600519.SH)").strip().upper()
        _run_factor_check([symbol])
    else:
        positions = list_positions()
        if not positions:
            _error("No positions found. Import a CSV first via Portfolio menu.")
            _pause()
            return
        symbols = list(set(p["symbol"] for p in positions))
        _run_factor_check(symbols)
    _pause()


def _run_factor_check(symbols: list[str]) -> None:
    from datetime import date, timedelta
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=365)).isoformat()

    for symbol in symbols:
        try:
            console.print(f"\n[bold]Fetching data for {symbol}...[/bold]")
            ohlcv = get_ohlcv(symbol, start, end)
            fundamentals = get_fundamentals(symbol)
            if ohlcv.empty:
                _error(f"No OHLCV data for {symbol}")
                continue
            factors = compute_factors(ohlcv, fundamentals)
            _display_factor_table(symbol, factors)
        except Exception as e:
            _error(f"{symbol}: {e}")


def _display_factor_table(symbol: str, factors: dict) -> None:
    table = Table(title=f"{symbol} Factor Check", show_lines=True)
    table.add_column("Factor", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Status")

    display_names = {
        "pe": "PE (TTM)", "pb": "PB", "roe": "ROE",
        "revenue_growth": "Revenue Growth", "volatility": "Volatility (60d)",
        "momentum": "Momentum (20d)",
    }
    for key, name in display_names.items():
        f = factors[key]
        val = f["value"]
        if val is None:
            val_str = "N/A"
        elif key in ("roe", "revenue_growth", "volatility", "momentum"):
            val_str = f"{val:.1%}"
        else:
            val_str = f"{val:.1f}"
        icon = RATING_ICONS.get(f["rating"], "")
        table.add_row(name, val_str, f"{icon} {f['label']}")

    console.print(table)


# ── Backtest ──


def _menu_backtest() -> None:
    console.clear()
    console.print(Panel("Strategy Backtest", style="bold cyan"))
    console.print("[bold][1][/bold] MA Cross (short/long moving average crossover)")
    console.print("[bold][2][/bold] DCA (dollar-cost averaging / monthly fixed buy)")
    strategy = Prompt.ask("Choose strategy", choices=["1", "2"], default="1")
    symbol = Prompt.ask("Stock symbol").strip().upper()

    from datetime import date, timedelta
    default_start = (date.today() - timedelta(days=3 * 365)).isoformat()
    default_end = date.today().isoformat()
    start = Prompt.ask("Start date", default=default_start)
    end = Prompt.ask("End date", default=default_end)

    cfg = load_config()
    capital = cfg["default_capital"]
    slippage = cfg["slippage_bps"]
    commission = cfg["commission_bps"]

    try:
        console.print(f"\n[bold]Fetching data for {symbol}...[/bold]")
        ohlcv = get_ohlcv(symbol, start, end)
        if ohlcv.empty:
            _error(f"No data for {symbol}")
            _pause()
            return

        if strategy == "1":
            signals = ma_cross_signals(ohlcv, short_window=5, long_window=20)
            strategy_name = "MA Cross (5/20)"
        else:
            signals = dca_signals(ohlcv, day_of_month=1)
            strategy_name = "DCA (Monthly)"

        result = run_backtest(ohlcv, signals, capital=capital,
                              slippage_bps=slippage, commission_bps=commission)
        metrics = compute_metrics(result["equity_curve"], result["trades"])

        _display_backtest_result(symbol, strategy_name, ohlcv, result, metrics, capital)
    except Exception as e:
        _error(str(e))
    _pause()


def _display_backtest_result(
    symbol: str, strategy_name: str, ohlcv, result: dict, metrics: dict, capital: float
) -> None:
    # Equity curve chart
    equity = result["equity_curve"].values
    plt.clear_figure()
    plt.plot(list(range(len(equity))), list(equity), label="Strategy")
    # Buy & hold benchmark
    closes = ohlcv["close"].values
    benchmark = [capital * (c / closes[0]) for c in closes]
    plt.plot(list(range(len(benchmark))), benchmark, label="Buy & Hold")
    plt.title(f"{symbol} - {strategy_name}")
    plt.xlabel("Trading Days")
    plt.ylabel("Equity")
    plt.theme("dark")
    plt.plot_size(80, 20)
    plt.show()

    # Metrics table
    table = Table(title="Performance Metrics", show_lines=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Total Return", f"{metrics['total_return']:.1%}")
    table.add_row("Annualized Return", f"{metrics['annualized_return']:.1%}")
    table.add_row("Sharpe Ratio", f"{metrics['sharpe']:.2f}")
    table.add_row("Max Drawdown", f"{metrics['max_drawdown']:.1%}")
    table.add_row("Win Rate", f"{metrics['win_rate']:.0%}")
    table.add_row("Trade Count", str(metrics["trade_count"]))
    bh_return = (closes[-1] / closes[0] - 1) if len(closes) > 0 else 0
    table.add_row("vs Buy & Hold", f"{metrics['total_return'] - bh_return:+.1%}")
    console.print(table)

    console.print(
        "\n[dim italic]Backtest ≠ live trading. Past performance ≠ future results.[/dim italic]"
    )


# ── Risk Lens ──


def _menu_risk_lens() -> None:
    console.clear()
    console.print(Panel("Risk Lens", style="bold cyan"))
    positions = list_positions()
    if not positions:
        _error("No positions found. Import a CSV first via Portfolio menu.")
        _pause()
        return

    from datetime import date, timedelta
    import pandas as pd
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=365)).isoformat()

    # Aggregate positions by symbol
    holdings = {}
    for p in positions:
        s = p["symbol"]
        if s not in holdings:
            holdings[s] = {"quantity": 0, "total_cost": 0}
        holdings[s]["quantity"] += p["quantity"]
        holdings[s]["total_cost"] += p["quantity"] * p["buy_price"]

    # Fetch current prices and returns
    console.print("[bold]Fetching market data...[/bold]")
    returns_dict = {}
    market_values = {}
    for symbol in holdings:
        try:
            ohlcv = get_ohlcv(symbol, start, end)
            if ohlcv.empty:
                continue
            current_price = ohlcv["close"].iloc[-1]
            market_values[symbol] = current_price * holdings[symbol]["quantity"]
            returns_dict[symbol] = ohlcv.set_index("date")["close"].pct_change().dropna()
        except Exception as e:
            console.print(f"[yellow]Skipping {symbol}: {e}[/yellow]")

    if not market_values:
        _error("Could not fetch data for any positions.")
        _pause()
        return

    # 1. Concentration
    console.print("\n[bold underline]1. Concentration[/bold underline]")
    conc = compute_concentration(market_values)
    table = Table(show_lines=True)
    table.add_column("Symbol", style="bold")
    table.add_column("Market Value", justify="right")
    table.add_column("Weight", justify="right")
    table.add_column("Status")
    for s, data in conc.items():
        status = "[red]CONCENTRATED[/red]" if data["warning"] else "[green]OK[/green]"
        table.add_row(s, f"{data['market_value']:,.0f}", f"{data['weight']:.1%}", status)
    console.print(table)

    # 2. Correlation
    if len(returns_dict) >= 2:
        console.print("\n[bold underline]2. Correlation Matrix[/bold underline]")
        returns_df = pd.DataFrame(returns_dict)
        corr = compute_correlation_matrix(returns_df)
        corr_table = Table(show_lines=True)
        corr_table.add_column("")
        for col in corr.columns:
            corr_table.add_column(str(col), justify="center")
        for idx in corr.index:
            row_vals = []
            for col in corr.columns:
                v = corr.loc[idx, col]
                if idx == col:
                    row_vals.append("[dim]1.00[/dim]")
                elif v > 0.7:
                    row_vals.append(f"[red]{v:.2f}[/red]")
                elif v > 0.4:
                    row_vals.append(f"[yellow]{v:.2f}[/yellow]")
                else:
                    row_vals.append(f"[green]{v:.2f}[/green]")
            corr_table.add_row(str(idx), *row_vals)
        console.print(corr_table)
        high_pairs = sum(1 for i in range(len(corr)) for j in range(i+1, len(corr))
                         if corr.iloc[i, j] > 0.7)
        total_pairs = len(corr) * (len(corr) - 1) // 2
        if high_pairs > 0:
            console.print(
                f"[yellow]{high_pairs} of {total_pairs} pairs highly correlated (>0.7) "
                f"— limited diversification[/yellow]"
            )

    # 3. Volatility contribution
    if len(returns_dict) >= 2:
        console.print("\n[bold underline]3. Volatility Contribution[/bold underline]")
        total_mv = sum(market_values.values())
        weights = {s: mv / total_mv for s, mv in market_values.items()}
        returns_df = pd.DataFrame(returns_dict)
        vol_contrib = compute_volatility_contribution(returns_df, weights)
        vol_table = Table(show_lines=True)
        vol_table.add_column("Symbol", style="bold")
        vol_table.add_column("Contribution", justify="right")
        for s, data in sorted(vol_contrib.items(), key=lambda x: -x[1]["contribution"]):
            vol_table.add_row(s, f"{data['contribution']:.1%}")
        console.print(vol_table)

    # 4. Max drawdown
    console.print("\n[bold underline]4. Historical Drawdown[/bold underline]")
    # Build portfolio equity curve
    returns_df = pd.DataFrame(returns_dict)
    total_mv = sum(market_values.values())
    weights_arr = pd.Series({s: market_values[s] / total_mv for s in returns_df.columns})
    port_returns = (returns_df * weights_arr).sum(axis=1)
    port_equity = (1 + port_returns).cumprod() * total_mv
    dd = compute_max_drawdown(port_equity)
    console.print(
        f"Based on the past year, your portfolio could drop up to "
        f"[bold red]{abs(dd['max_drawdown']):.1%}[/bold red] from peak."
    )

    _pause()


# ── Portfolio ──


def _menu_portfolio() -> None:
    console.clear()
    console.print(Panel("Portfolio Management", style="bold cyan"))
    console.print("[bold][1][/bold] Import CSV")
    console.print("[bold][2][/bold] View positions")
    console.print("[bold][3][/bold] Clear all positions")
    console.print("[bold][0][/bold] Back")
    choice = Prompt.ask("Choose", choices=["0", "1", "2", "3"], default="0")

    if choice == "1":
        path = Prompt.ask("CSV file path").strip()
        try:
            count = import_csv(Path(path))
            console.print(f"[green]Imported {count} positions.[/green]")
        except Exception as e:
            _error(str(e))
    elif choice == "2":
        positions = list_positions()
        if not positions:
            console.print("[dim]No positions yet.[/dim]")
        else:
            table = Table(title="Positions", show_lines=True)
            table.add_column("Symbol", style="bold")
            table.add_column("Buy Date")
            table.add_column("Buy Price", justify="right")
            table.add_column("Quantity", justify="right")
            table.add_column("Market")
            for p in positions:
                table.add_row(p["symbol"], p["buy_date"], f"{p['buy_price']:.2f}",
                              f"{p['quantity']:.0f}", p["market"])
            console.print(table)
    elif choice == "3":
        confirm = Prompt.ask("Delete all positions?", choices=["y", "n"], default="n")
        if confirm == "y":
            clear_positions()
            console.print("[green]All positions cleared.[/green]")
    _pause()


# ── Settings ──


def _menu_settings() -> None:
    console.clear()
    console.print(Panel("Settings", style="bold cyan"))
    cfg = load_config()
    table = Table(show_lines=True)
    table.add_column("Setting", style="bold")
    table.add_column("Current Value")
    table.add_row("Tushare Token", cfg["tushare_token"] or "[dim]not set[/dim]")
    table.add_row("Default Capital", f"{cfg['default_capital']:,}")
    table.add_row("Slippage (bps)", str(cfg["slippage_bps"]))
    table.add_row("Commission (bps)", str(cfg["commission_bps"]))
    console.print(table)

    console.print("\n[bold][1][/bold] Set Tushare Token")
    console.print("[bold][2][/bold] Set Default Capital")
    console.print("[bold][3][/bold] Set Slippage")
    console.print("[bold][4][/bold] Set Commission")
    console.print("[bold][0][/bold] Back")
    choice = Prompt.ask("Choose", choices=["0", "1", "2", "3", "4"], default="0")

    if choice == "1":
        cfg["tushare_token"] = Prompt.ask("Tushare Token")
        save_config(cfg)
        console.print("[green]Saved.[/green]")
    elif choice == "2":
        cfg["default_capital"] = IntPrompt.ask("Default Capital", default=cfg["default_capital"])
        save_config(cfg)
        console.print("[green]Saved.[/green]")
    elif choice == "3":
        cfg["slippage_bps"] = IntPrompt.ask("Slippage (bps)", default=cfg["slippage_bps"])
        save_config(cfg)
        console.print("[green]Saved.[/green]")
    elif choice == "4":
        cfg["commission_bps"] = IntPrompt.ask("Commission (bps)", default=cfg["commission_bps"])
        save_config(cfg)
        console.print("[green]Saved.[/green]")
    _pause()
```

- [ ] **Step 2: Manually test the CLI**

Run: `cd /Users/wuzikang/Project/quantkit && python -m quantkit`

Verify:
- Main menu displays with Rich panel
- Each menu option navigates correctly
- [0] exits cleanly
- Settings can be viewed and modified

- [ ] **Step 3: Commit**

```bash
git add src/quantkit/cli.py
git commit -m "feat: add Rich CLI menu system with all 5 menu options"
```

---

## Task 10: Integration Test & Final Polish

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""Integration test: verify all modules wire together."""

import csv
from pathlib import Path
from datetime import date, timedelta
from unittest.mock import patch

import pandas as pd

from quantkit.portfolio import import_csv, list_positions
from quantkit.factor.engine import compute_factors
from quantkit.backtest.engine import run_backtest, compute_metrics
from quantkit.backtest.strategies import ma_cross_signals
from quantkit.risk.engine import compute_concentration, compute_max_drawdown


def _make_ohlcv(n: int = 100) -> pd.DataFrame:
    dates = [date(2023, 1, 2) + timedelta(days=i) for i in range(n)]
    closes = [100 + i * 0.1 for i in range(n)]
    return pd.DataFrame({
        "date": dates,
        "open": [c - 0.5 for c in closes],
        "high": [c + 1.0 for c in closes],
        "low": [c - 1.0 for c in closes],
        "close": closes,
        "volume": [1000] * n,
    })


def test_full_workflow(tmp_path, monkeypatch):
    """Test the full workflow: import → factor check → backtest → risk."""
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))

    # 1. Import portfolio
    csv_path = tmp_path / "portfolio.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "buy_date", "buy_price", "quantity", "market"])
        writer.writeheader()
        writer.writerow({"symbol": "AAPL", "buy_date": "2024-01-15", "buy_price": "180",
                         "quantity": "50", "market": "US"})
        writer.writerow({"symbol": "GOOG", "buy_date": "2024-02-01", "buy_price": "140",
                         "quantity": "30", "market": "US"})
    assert import_csv(csv_path) == 2
    assert len(list_positions()) == 2

    # 2. Factor check
    ohlcv = _make_ohlcv(120)
    fundamentals = {"pe": 25, "pb": 5, "roe": 0.20, "market_cap": 3e12, "revenue_growth": 0.12}
    factors = compute_factors(ohlcv, fundamentals)
    assert len(factors) == 6
    assert factors["roe"]["rating"] == "green"

    # 3. Backtest
    signals = ma_cross_signals(ohlcv, short_window=5, long_window=20)
    result = run_backtest(ohlcv, signals, capital=100_000)
    metrics = compute_metrics(result["equity_curve"], result["trades"])
    assert metrics["total_return"] is not None
    assert "max_drawdown" in metrics

    # 4. Risk
    market_values = {"AAPL": 50 * 190, "GOOG": 30 * 150}
    conc = compute_concentration(market_values)
    assert len(conc) == 2
    dd = compute_max_drawdown(result["equity_curve"])
    assert dd["max_drawdown"] <= 0
```

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`

Expected: All tests pass (config: 3, cache: 4, data: 4, portfolio: 3, factor: 12, backtest: 4, risk: 4, integration: 1 = 35 total)

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration test covering full workflow"
```

---

## Task 11: Documentation (Gemini's Job)

**Files:**
- Create: `PROJECT.md`
- Create: `LOG.md`
- Create: `PLAN.md`

- [ ] **Step 1: Create PROJECT.md**

```markdown
# QuantKit

Terminal-based personal investment toolkit for A-shares and US stocks.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m quantkit
```

## Modules

- **Factor Check**: 6-dimension health check (PE, PB, ROE, Revenue Growth, Volatility, Momentum)
- **Strategy Backtest**: MA Cross, DCA strategies with performance metrics
- **Risk Lens**: Concentration, correlation, volatility contribution, drawdown analysis

## Data Sources

- US stocks: yfinance (no auth required)
- A-shares: Tushare (requires TUSHARE_TOKEN)
- Cache: SQLite at ~/.quantkit/data.db

## Configuration

Settings stored at ~/.quantkit/config.json. Configurable via Settings menu.
```

- [ ] **Step 2: Create LOG.md**

```markdown
# Development Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-05 | Claude Code | Initial design spec and implementation plan |
```

- [ ] **Step 3: Create PLAN.md**

Copy the task list from this plan with checkbox status.

- [ ] **Step 4: Commit**

```bash
git add PROJECT.md LOG.md PLAN.md
git commit -m "docs: add PROJECT.md, LOG.md, and PLAN.md"
```

"""Tests for SQLite cache layer."""

from datetime import date, timedelta

import pandas as pd

from quantkit.data.cache import OHLCVCache


def test_cache_save_and_load(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "test.db")
    df = pd.DataFrame(
        {
            "date": [date(2024, 1, 1), date(2024, 1, 2)],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [1000, 1100],
        }
    )
    cache.save_ohlcv("AAPL", df)
    result = cache.load_ohlcv("AAPL", "2024-01-01", "2024-01-02")
    assert len(result) == 2
    assert result.iloc[0]["close"] == 101.0


def test_cache_load_ohlcv_filters_requested_range(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "test.db")
    df = pd.DataFrame(
        {
            "date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)],
            "open": [100.0, 101.0, 102.0],
            "high": [102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0],
            "close": [101.0, 102.0, 103.0],
            "volume": [1000, 1100, 1200],
        }
    )
    cache.save_ohlcv("AAPL", df, start="2024-01-01", end="2024-01-03")

    result = cache.load_ohlcv("AAPL", "2024-01-02", "2024-01-03")

    assert result is not None
    assert result["date"].tolist() == [date(2024, 1, 2), date(2024, 1, 3)]


def test_cache_returns_none_when_missing(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "test.db")
    result = cache.load_ohlcv("MISSING", "2024-01-01", "2024-01-02")
    assert result is None


def test_cache_save_and_load_fundamentals(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "test.db")
    data = {
        "pe": 28.5,
        "pb": 6.2,
        "roe": 0.26,
        "market_cap": 3e12,
        "revenue_growth": 0.08,
    }
    cache.save_fundamentals("AAPL", data)
    result = cache.load_fundamentals("AAPL")
    assert result is not None
    assert result["pe"] == 28.5


def test_fundamentals_cache_expires(tmp_path):
    cache = OHLCVCache(db_path=tmp_path / "test.db")
    data = {
        "pe": 28.5,
        "pb": 6.2,
        "roe": 0.26,
        "market_cap": 3e12,
        "revenue_growth": 0.08,
    }
    cache.save_fundamentals("AAPL", data)
    cache._conn.execute(
        "UPDATE fundamentals SET fetch_date = ? WHERE symbol = ?",
        ((date.today() - timedelta(days=8)).isoformat(), "AAPL"),
    )
    cache._conn.commit()
    result = cache.load_fundamentals("AAPL")
    assert result is None

"""Tests for StockContext."""

import pandas as pd
import pytest

from quantkit.stock_context import StockContext


def _make_ohlcv(n_days: int = 60, start_date: str = "2025-01-01") -> pd.DataFrame:
    """Helper: create fake OHLCV DataFrame."""
    dates = pd.bdate_range(start_date, periods=n_days).date
    return pd.DataFrame({
        "date": list(dates),
        "open": [100.0] * n_days,
        "high": [105.0] * n_days,
        "low": [95.0] * n_days,
        "close": [102.0] * n_days,
        "volume": [1_000_000] * n_days,
    })


def test_load_success(monkeypatch):
    ohlcv = _make_ohlcv(252)
    fundamentals = {"pe": 20.0, "pb": 3.0, "roe": 0.18}

    monkeypatch.setattr(
        "quantkit.stock_context.get_ohlcv",
        lambda sym, s, e: ohlcv,
    )
    monkeypatch.setattr(
        "quantkit.stock_context.get_fundamentals",
        lambda sym: fundamentals,
    )

    ctx = StockContext.load("AAPL")
    assert ctx.symbol == "AAPL"
    assert len(ctx.ohlcv) == 252
    assert ctx.fundamentals == fundamentals
    assert ctx.has_fundamentals is True


def test_load_ohlcv_empty_raises(monkeypatch):
    monkeypatch.setattr(
        "quantkit.stock_context.get_ohlcv",
        lambda sym, s, e: pd.DataFrame(),
    )
    with pytest.raises(ValueError, match="No OHLCV data"):
        StockContext.load("FAKE")


def test_load_fundamentals_failure_degrades(monkeypatch):
    ohlcv = _make_ohlcv(60)
    monkeypatch.setattr(
        "quantkit.stock_context.get_ohlcv",
        lambda sym, s, e: ohlcv,
    )
    monkeypatch.setattr(
        "quantkit.stock_context.get_fundamentals",
        lambda sym: (_ for _ in ()).throw(Exception("API error")),
    )

    ctx = StockContext.load("AAPL")
    assert ctx.has_fundamentals is False
    assert ctx.fundamentals is None


def test_get_factors_lazy_cache(monkeypatch):
    ohlcv = _make_ohlcv(252)
    fundamentals = {"pe": 15.0, "pb": 2.0, "roe": 0.20, "revenue_growth": 0.1}

    monkeypatch.setattr(
        "quantkit.stock_context.get_ohlcv",
        lambda sym, s, e: ohlcv,
    )
    monkeypatch.setattr(
        "quantkit.stock_context.get_fundamentals",
        lambda sym: fundamentals,
    )

    ctx = StockContext.load("AAPL")
    factors1 = ctx.get_factors()
    factors2 = ctx.get_factors()
    assert factors1 is factors2


def test_get_ohlcv_within_range(monkeypatch):
    ohlcv = _make_ohlcv(252, start_date="2025-01-01")
    monkeypatch.setattr(
        "quantkit.stock_context.get_ohlcv",
        lambda sym, s, e: ohlcv,
    )
    monkeypatch.setattr(
        "quantkit.stock_context.get_fundamentals",
        lambda sym: {},
    )

    ctx = StockContext.load("AAPL")
    subset = ctx.get_ohlcv("2025-03-01", "2025-06-01")
    assert len(subset) <= len(ohlcv)


def test_get_ohlcv_extends_range(monkeypatch):
    short_ohlcv = _make_ohlcv(60, start_date="2025-10-01")
    long_ohlcv = _make_ohlcv(756, start_date="2023-01-01")
    call_count = {"n": 0}

    def mock_get_ohlcv(sym, s, e):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return short_ohlcv
        return long_ohlcv

    monkeypatch.setattr("quantkit.stock_context.get_ohlcv", mock_get_ohlcv)
    monkeypatch.setattr(
        "quantkit.stock_context.get_fundamentals",
        lambda sym: {},
    )

    ctx = StockContext.load("AAPL")
    assert call_count["n"] == 1

    extended = ctx.get_ohlcv("2023-01-01", "2025-12-31")
    assert call_count["n"] == 2
    assert len(extended) == 756

"""Tests for backtest engine."""

from datetime import date, timedelta

import pandas as pd

from quantkit.backtest.engine import compute_metrics, run_backtest
from quantkit.backtest.strategies import dca_signals, ma_cross_signals


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


def test_dca_hold_mode_does_not_sell_monthly():
    ohlcv = _make_ohlcv(90)
    signals = dca_signals(ohlcv, day_of_month=1)

    result = run_backtest(
        ohlcv,
        signals,
        capital=100_000,
        slippage_bps=10,
        commission_bps=5,
        hold_mode=True,
    )

    assert len(result["trades"]) == 0
    assert result["final_equity"] > result["equity_curve"].iloc[0]

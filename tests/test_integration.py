"""Integration test covering the end-to-end QuantKit workflow."""

import csv
from datetime import date, timedelta
from unittest.mock import patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import quantkit.data.provider as provider_module
from quantkit.backtest.engine import compute_metrics, run_backtest
from quantkit.backtest.strategies import ma_cross_signals
from quantkit.data.provider import get_fundamentals, get_ohlcv
from quantkit.factor.engine import compute_factors
from quantkit.portfolio import _reset_conn, import_csv, list_positions
from quantkit.risk.engine import (
    compute_concentration,
    compute_correlation_matrix,
    compute_max_drawdown,
    compute_volatility_contribution,
)


@pytest.fixture(autouse=True)
def _reset_integration_state():
    _reset_conn()
    provider_module._cache_instance = None
    yield
    _reset_conn()
    cache = provider_module._cache_instance
    if cache is not None:
        cache._conn.close()
    provider_module._cache_instance = None


def _make_ohlcv(closes: list[float], start: date = date(2023, 1, 2)) -> pd.DataFrame:
    dates = [start + timedelta(days=i) for i in range(len(closes))]
    return pd.DataFrame(
        {
            "date": dates,
            "open": [close - 0.5 for close in closes],
            "high": [close + 1.0 for close in closes],
            "low": [close - 1.0 for close in closes],
            "close": closes,
            "volume": [1_000] * len(closes),
        }
    )


def _write_portfolio_csv(path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=["symbol", "buy_date", "buy_price", "quantity", "market"],
        )
        writer.writeheader()
        writer.writerows(rows)


def test_full_workflow(tmp_path, monkeypatch):
    """Import a portfolio, pull mocked data, then run factor/backtest/risk flows."""
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))

    csv_path = tmp_path / "portfolio.csv"
    _write_portfolio_csv(
        csv_path,
        [
            {
                "symbol": "AAPL",
                "buy_date": "2024-01-15",
                "buy_price": "180",
                "quantity": "50",
                "market": "US",
            },
            {
                "symbol": "GOOG",
                "buy_date": "2024-02-01",
                "buy_price": "140",
                "quantity": "30",
                "market": "US",
            },
        ],
    )

    assert import_csv(csv_path) == 2
    positions = list_positions()
    assert [position["symbol"] for position in positions] == ["AAPL", "GOOG"]

    aapl_closes = [100 + i * 0.5 for i in range(40)]
    aapl_closes += [120 - i * 0.6 for i in range(40)]
    aapl_closes += [96 + i * 0.9 for i in range(40)]
    goog_closes = [80 + i * 0.3 for i in range(40)]
    goog_closes += [92 - i * 0.4 for i in range(40)]
    goog_closes += [76 + i * 0.5 for i in range(40)]

    ohlcv_by_symbol = {
        "AAPL": _make_ohlcv(aapl_closes),
        "GOOG": _make_ohlcv(goog_closes),
    }
    fundamentals_by_symbol = {
        "AAPL": {
            "pe": 25.0,
            "pb": 5.0,
            "roe": 0.20,
            "market_cap": 3e12,
            "revenue_growth": 0.12,
        }
    }

    with patch(
        "quantkit.data.provider._fetch_yfinance_ohlcv",
        side_effect=lambda symbol, start, end: ohlcv_by_symbol[symbol].copy(),
    ) as mock_fetch_ohlcv, patch(
        "quantkit.data.provider._fetch_yfinance_fundamentals",
        side_effect=lambda symbol: fundamentals_by_symbol[symbol].copy(),
    ) as mock_fetch_fundamentals:
        aapl_ohlcv = get_ohlcv("AAPL", "2023-01-02", "2023-05-01")
        goog_ohlcv = get_ohlcv("GOOG", "2023-01-02", "2023-05-01")
        cached_aapl_ohlcv = get_ohlcv("AAPL", "2023-01-02", "2023-05-01")
        aapl_fundamentals = get_fundamentals("AAPL")
        cached_aapl_fundamentals = get_fundamentals("AAPL")

    assert mock_fetch_ohlcv.call_count == 2
    assert mock_fetch_fundamentals.call_count == 1
    assert_frame_equal(cached_aapl_ohlcv, aapl_ohlcv, check_dtype=False)
    assert cached_aapl_fundamentals == aapl_fundamentals

    factors = compute_factors(aapl_ohlcv, aapl_fundamentals)
    assert len(factors) == 6
    assert factors["roe"]["rating"] == "green"
    assert factors["revenue_growth"]["rating"] == "green"

    signals = ma_cross_signals(aapl_ohlcv, short_window=5, long_window=20)
    backtest_result = run_backtest(aapl_ohlcv, signals, capital=100_000)
    metrics = compute_metrics(backtest_result["equity_curve"], backtest_result["trades"])
    assert metrics["trade_count"] >= 1
    assert metrics["max_drawdown"] <= 0
    assert len(backtest_result["equity_curve"]) == len(aapl_ohlcv)

    latest_close_by_symbol = {
        "AAPL": float(aapl_ohlcv["close"].iloc[-1]),
        "GOOG": float(goog_ohlcv["close"].iloc[-1]),
    }
    market_values = {
        position["symbol"]: position["quantity"] * latest_close_by_symbol[position["symbol"]]
        for position in positions
    }
    concentration = compute_concentration(market_values)
    returns = pd.DataFrame(
        {
            "AAPL": aapl_ohlcv["close"].pct_change(),
            "GOOG": goog_ohlcv["close"].pct_change(),
        }
    ).dropna()
    weights = {
        symbol: factor_data["weight"] for symbol, factor_data in concentration.items()
    }
    correlation = compute_correlation_matrix(returns)
    volatility_contribution = compute_volatility_contribution(returns, weights)
    drawdown = compute_max_drawdown(backtest_result["equity_curve"])

    assert len(concentration) == 2
    assert concentration["AAPL"]["warning"] is True
    assert correlation.shape == (2, 2)
    assert set(volatility_contribution) == {"AAPL", "GOOG"}
    assert abs(sum(item["contribution"] for item in volatility_contribution.values()) - 1.0) < 0.1
    assert drawdown["max_drawdown"] <= 0

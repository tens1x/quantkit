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

"""Tests for risk lens engine."""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from quantkit.risk.engine import (
    compute_concentration,
    compute_correlation_matrix,
    compute_max_drawdown,
    compute_volatility_contribution,
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

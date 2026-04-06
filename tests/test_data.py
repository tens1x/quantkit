"""Tests for data provider."""

from datetime import date
from unittest.mock import patch

import pandas as pd

from quantkit.data.provider import get_fundamentals, get_ohlcv, is_cn_symbol


def test_is_cn_symbol():
    assert is_cn_symbol("600519.SH") is True
    assert is_cn_symbol("000001.SZ") is True
    assert is_cn_symbol("AAPL") is False
    assert is_cn_symbol("TSLA") is False


def test_get_ohlcv_routes_us_to_yfinance(tmp_path):
    mock_df = pd.DataFrame(
        {
            "date": [date(2024, 1, 2)],
            "open": [100.0],
            "high": [102.0],
            "low": [99.0],
            "close": [101.0],
            "volume": [1000],
        }
    )
    with patch("quantkit.data.provider._fetch_yfinance_ohlcv", return_value=mock_df):
        with patch("quantkit.data.provider._get_cache") as mock_cache:
            mock_cache.return_value.load_ohlcv.return_value = None
            mock_cache.return_value.has_ohlcv_coverage.return_value = False
            result = get_ohlcv("AAPL", "2024-01-01", "2024-01-05")
            assert len(result) == 1
            assert result.iloc[0]["close"] == 101.0


def test_get_ohlcv_uses_cache_when_available(tmp_path):
    cached_df = pd.DataFrame(
        {
            "date": [date(2024, 1, 2)],
            "open": [100.0],
            "high": [102.0],
            "low": [99.0],
            "close": [101.0],
            "volume": [1000],
        }
    )
    with patch("quantkit.data.provider._get_cache") as mock_cache:
        mock_cache.return_value.load_ohlcv.return_value = cached_df
        mock_cache.return_value.has_ohlcv_coverage.return_value = True
        result = get_ohlcv("AAPL", "2024-01-01", "2024-01-05")
        assert len(result) == 1


def test_get_ohlcv_refetches_when_cached_range_is_incomplete(tmp_path):
    cached_df = pd.DataFrame(
        {
            "date": [date(2024, 1, 3), date(2024, 1, 4)],
            "open": [102.0, 103.0],
            "high": [103.0, 104.0],
            "low": [101.0, 102.0],
            "close": [102.5, 103.5],
            "volume": [1000, 1000],
        }
    )
    full_df = pd.DataFrame(
        {
            "date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
            "open": [100.0, 101.0, 102.0, 103.0],
            "high": [101.0, 102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0, 102.0],
            "close": [100.5, 101.5, 102.5, 103.5],
            "volume": [1000, 1000, 1000, 1000],
        }
    )
    with patch("quantkit.data.provider._fetch_yfinance_ohlcv", return_value=full_df) as mock_fetch:
        with patch("quantkit.data.provider._get_cache") as mock_cache:
            mock_cache.return_value.load_ohlcv.return_value = cached_df
            mock_cache.return_value.has_ohlcv_coverage.return_value = False

            result = get_ohlcv("AAPL", "2024-01-01", "2024-01-04")

            assert result.equals(full_df)
            mock_fetch.assert_called_once_with("AAPL", "2024-01-01", "2024-01-04")
            mock_cache.return_value.save_ohlcv.assert_called_once_with(
                "AAPL",
                full_df,
                start="2024-01-01",
                end="2024-01-04",
            )


def test_get_fundamentals_routes_us(tmp_path):
    mock_data = {"pe": 28.5, "pb": 6.2, "roe": 0.26, "market_cap": 3e12, "revenue_growth": 0.08}
    with patch("quantkit.data.provider._fetch_yfinance_fundamentals", return_value=mock_data):
        with patch("quantkit.data.provider._get_cache") as mock_cache:
            mock_cache.return_value.load_fundamentals.return_value = None
            result = get_fundamentals("AAPL")
            assert result["pe"] == 28.5

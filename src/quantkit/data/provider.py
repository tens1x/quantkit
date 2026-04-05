"""Unified data provider with auto-routing and caching."""

import re
from typing import Optional

import pandas as pd

from quantkit.data import tushare_src, yfinance_src
from quantkit.data.cache import OHLCVCache

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

"""Stock context: preloaded data for the current stock."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from quantkit.data.provider import get_fundamentals, get_ohlcv
from quantkit.factor.engine import compute_factors


class StockContext:
    """Holds preloaded data for the active stock symbol."""

    def __init__(
        self,
        symbol: str,
        ohlcv: pd.DataFrame,
        fundamentals: dict | None,
        loaded_start: str,
        loaded_end: str,
    ) -> None:
        self.symbol = symbol
        self.ohlcv = ohlcv
        self.fundamentals = fundamentals
        self._loaded_start = loaded_start
        self._loaded_end = loaded_end
        self._factors_cache: dict | None = None

    @classmethod
    def load(cls, symbol: str) -> "StockContext":
        """Load 1y OHLCV + fundamentals. Raises ValueError if OHLCV empty."""
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=365)).isoformat()

        ohlcv = get_ohlcv(symbol, start, end)
        if ohlcv.empty:
            raise ValueError(f"No OHLCV data for {symbol}")

        fundamentals: dict | None
        try:
            fundamentals = get_fundamentals(symbol)
        except Exception:
            fundamentals = None

        return cls(
            symbol=symbol,
            ohlcv=ohlcv,
            fundamentals=fundamentals,
            loaded_start=start,
            loaded_end=end,
        )

    @property
    def has_fundamentals(self) -> bool:
        """Whether fundamentals data is available."""
        return self.fundamentals is not None

    def get_factors(self) -> dict:
        """Lazily compute and cache factor results."""
        if self._factors_cache is None:
            fund = self.fundamentals if self.fundamentals is not None else {}
            self._factors_cache = compute_factors(self.ohlcv, fund)
        return self._factors_cache

    def get_ohlcv(self, start: str, end: str) -> pd.DataFrame:
        """Get OHLCV for a date range. Re-fetches if range exceeds preloaded data."""
        if start >= self._loaded_start and end <= self._loaded_end:
            df = self.ohlcv
            mask = (df["date"].astype(str) >= start) & (df["date"].astype(str) <= end)
            return df[mask].reset_index(drop=True)

        ohlcv = get_ohlcv(self.symbol, start, end)
        if not ohlcv.empty:
            self.ohlcv = ohlcv
            self._loaded_start = start
            self._loaded_end = end
            self._factors_cache = None
        return ohlcv

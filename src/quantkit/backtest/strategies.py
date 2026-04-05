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

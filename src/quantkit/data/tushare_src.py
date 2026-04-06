"""Tushare adapter for A-share data."""

import pandas as pd

from quantkit.config import get_tushare_token


def _get_api():
    """Get tushare API instance."""
    import tushare as ts

    token = get_tushare_token()
    if not token:
        raise RuntimeError(
            "TUSHARE_TOKEN not set. Get a token at https://tushare.pro "
            "and set it via QuantKit Settings or: export TUSHARE_TOKEN=your_token"
        )
    return ts.pro_api(token)


def fetch_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch OHLCV data from Tushare."""
    api = _get_api()
    start_fmt = start.replace("-", "")
    end_fmt = end.replace("-", "")
    df = api.daily(ts_code=symbol, start_date=start_fmt, end_date=end_fmt)
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    df = df.rename(columns={"trade_date": "date", "vol": "volume"})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.sort_values("date")
    return df[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def fetch_fundamentals(symbol: str) -> dict:
    """Fetch fundamental data from Tushare."""
    api = _get_api()
    df = api.daily_basic(ts_code=symbol, fields="pe_ttm,pb,total_mv")
    if df is None or df.empty:
        return {"pe": None, "pb": None, "roe": None, "market_cap": None, "revenue_growth": None}
    row = df.iloc[0]
    fin = api.fina_indicator(ts_code=symbol, fields="roe,revenue_yoy")
    roe = None
    rev_growth = None
    if fin is not None and not fin.empty:
        roe = fin.iloc[0].get("roe")
        if roe is not None:
            roe = roe / 100.0
        rev_growth = fin.iloc[0].get("revenue_yoy")
        if rev_growth is not None:
            rev_growth = rev_growth / 100.0
    return {
        "pe": row.get("pe_ttm"),
        "pb": row.get("pb"),
        "roe": roe,
        "market_cap": row.get("total_mv"),
        "revenue_growth": rev_growth,
    }

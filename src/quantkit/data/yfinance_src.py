"""yfinance adapter for US stock data."""

import pandas as pd
import yfinance as yf


def fetch_ohlcv(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch OHLCV data from yfinance."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end)
    if df.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    df = df.reset_index()
    df = df.rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df[["date", "open", "high", "low", "close", "volume"]]


def fetch_fundamentals(symbol: str) -> dict:
    """Fetch fundamental data from yfinance."""
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        "pe": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "roe": info.get("returnOnEquity"),
        "market_cap": info.get("marketCap"),
        "revenue_growth": info.get("revenueGrowth"),
    }

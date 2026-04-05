"""SQLite cache for market data."""

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from quantkit.config import get_data_dir


class OHLCVCache:
    """Cache OHLCV and fundamentals data in SQLite."""

    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            db_path = get_data_dir() / "data.db"
        self._conn = sqlite3.connect(str(db_path))
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ohlcv (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL,
                volume REAL,
                PRIMARY KEY (symbol, date)
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fundamentals (
                symbol TEXT PRIMARY KEY,
                fetch_date TEXT NOT NULL,
                data TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def save_ohlcv(self, symbol: str, df: pd.DataFrame) -> None:
        """Save OHLCV dataframe to cache."""
        for _, row in df.iterrows():
            self._conn.execute(
                "INSERT OR REPLACE INTO ohlcv VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    symbol,
                    str(row["date"]),
                    row["open"],
                    row["high"],
                    row["low"],
                    row["close"],
                    row["volume"],
                ),
            )
        self._conn.commit()

    def load_ohlcv(self, symbol: str, start: str, end: str) -> pd.DataFrame | None:
        """Load OHLCV data from cache. Returns None if no data found."""
        cursor = self._conn.execute(
            "SELECT date, open, high, low, close, volume FROM ohlcv "
            "WHERE symbol = ? AND date >= ? AND date <= ? ORDER BY date",
            (symbol, start, end),
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        df = pd.DataFrame(
            rows,
            columns=["date", "open", "high", "low", "close", "volume"],
        )
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    def save_fundamentals(self, symbol: str, data: dict) -> None:
        """Save fundamentals data to cache."""
        self._conn.execute(
            "INSERT OR REPLACE INTO fundamentals VALUES (?, ?, ?)",
            (symbol, date.today().isoformat(), json.dumps(data)),
        )
        self._conn.commit()

    def load_fundamentals(self, symbol: str, max_age_days: int = 7) -> dict | None:
        """Load fundamentals from cache. Returns None if expired or missing."""
        cursor = self._conn.execute(
            "SELECT fetch_date, data FROM fundamentals WHERE symbol = ?",
            (symbol,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        fetch_date = date.fromisoformat(row[0])
        if date.today() - fetch_date > timedelta(days=max_age_days):
            return None
        return json.loads(row[1])

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
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ohlcv_ranges (
                symbol TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                PRIMARY KEY (symbol, start_date, end_date)
            )
            """
        )
        self._conn.commit()

    def save_ohlcv(
        self, symbol: str, df: pd.DataFrame, start: str | None = None, end: str | None = None
    ) -> None:
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
        if not df.empty:
            range_start = start or str(df["date"].min())
            range_end = end or str(df["date"].max())
            self._conn.execute(
                "INSERT OR REPLACE INTO ohlcv_ranges VALUES (?, ?, ?)",
                (symbol, range_start, range_end),
            )
        self._conn.commit()

    def has_ohlcv_coverage(self, symbol: str, start: str, end: str) -> bool:
        """Return whether the cache is known to cover the full requested range."""
        cursor = self._conn.execute(
            "SELECT 1 FROM ohlcv_ranges "
            "WHERE symbol = ? AND start_date <= ? AND end_date >= ? LIMIT 1",
            (symbol, start, end),
        )
        return cursor.fetchone() is not None

    def load_ohlcv(self, symbol: str, start: str, end: str) -> pd.DataFrame | None:
        """Load OHLCV data from cache. Returns None if no data found."""
        if not self.has_ohlcv_coverage(symbol, start, end):
            return None
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

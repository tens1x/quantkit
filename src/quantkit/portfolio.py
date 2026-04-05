"""Portfolio management: CSV import, position storage, listing."""

import csv
import sqlite3
from pathlib import Path
from typing import Optional

from quantkit.config import get_data_dir

_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        db_path = get_data_dir() / "data.db"
        _conn = sqlite3.connect(str(db_path))
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                buy_date TEXT NOT NULL,
                buy_price REAL NOT NULL,
                quantity REAL NOT NULL,
                market TEXT NOT NULL
            )
            """
        )
        _conn.commit()
    return _conn


def _reset_conn() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
    _conn = None


def import_csv(path: Path) -> int:
    """Import positions from CSV file. Returns number of rows imported."""
    conn = _get_conn()
    count = 0
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                "INSERT INTO positions (symbol, buy_date, buy_price, quantity, market) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    row["symbol"],
                    row["buy_date"],
                    float(row["buy_price"]),
                    float(row["quantity"]),
                    row["market"],
                ),
            )
            count += 1
    conn.commit()
    return count


def import_ibkr_csv(path: Path) -> int:
    """Import buy transactions from an IBKR export CSV file."""
    conn = _get_conn()
    count = 0
    with open(path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) <= 9:
                continue
            if row[0].strip() != "Transaction History" or row[1].strip() != "Data":
                continue
            if row[5].strip() != "买":
                continue

            market = "US" if row[9].strip() == "USD" else "CN"
            conn.execute(
                "INSERT INTO positions (symbol, buy_date, buy_price, quantity, market) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    row[6].strip(),
                    row[2].strip(),
                    float(row[8].strip()),
                    float(row[7].strip()),
                    market,
                ),
            )
            count += 1
    conn.commit()
    return count


def detect_and_import(path: Path) -> tuple[int, str]:
    """Detect CSV format and import positions."""
    with open(path, newline="") as f:
        first_line = f.readline().lstrip("\ufeff")

    if first_line.startswith("Statement,") or "Transaction History" in first_line:
        return import_ibkr_csv(path), "IBKR"
    return import_csv(path), "QuantKit CSV"


def list_positions() -> list[dict]:
    """Return all positions as a list of dicts."""
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT symbol, buy_date, buy_price, quantity, market FROM positions ORDER BY buy_date"
    )
    return [
        {
            "symbol": row[0],
            "buy_date": row[1],
            "buy_price": row[2],
            "quantity": row[3],
            "market": row[4],
        }
        for row in cursor.fetchall()
    ]


def clear_positions() -> None:
    """Delete all positions."""
    conn = _get_conn()
    conn.execute("DELETE FROM positions")
    conn.commit()

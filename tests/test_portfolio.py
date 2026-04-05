"""Tests for portfolio management."""

import csv
from pathlib import Path

import pytest

from quantkit.portfolio import clear_positions, import_csv, list_positions


@pytest.fixture(autouse=True)
def _reset_portfolio_conn():
    from quantkit.portfolio import _reset_conn

    _reset_conn()
    yield
    _reset_conn()


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_import_csv_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    csv_path = tmp_path / "portfolio.csv"
    _write_csv(
        csv_path,
        [
            {
                "symbol": "AAPL",
                "buy_date": "2024-03-15",
                "buy_price": "172.50",
                "quantity": "100",
                "market": "US",
            },
            {
                "symbol": "600519.SH",
                "buy_date": "2024-06-01",
                "buy_price": "1680.00",
                "quantity": "200",
                "market": "CN",
            },
        ],
    )
    count = import_csv(csv_path)
    assert count == 2
    positions = list_positions()
    assert len(positions) == 2
    assert positions[0]["symbol"] == "AAPL"


def test_import_csv_appends(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    csv_path = tmp_path / "p.csv"
    _write_csv(
        csv_path,
        [
            {
                "symbol": "AAPL",
                "buy_date": "2024-03-15",
                "buy_price": "172.50",
                "quantity": "100",
                "market": "US",
            },
        ],
    )
    import_csv(csv_path)
    import_csv(csv_path)
    positions = list_positions()
    assert len(positions) == 2  # Appended, not deduped


def test_clear_positions(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    csv_path = tmp_path / "p.csv"
    _write_csv(
        csv_path,
        [
            {
                "symbol": "AAPL",
                "buy_date": "2024-03-15",
                "buy_price": "172.50",
                "quantity": "100",
                "market": "US",
            },
        ],
    )
    import_csv(csv_path)
    clear_positions()
    assert len(list_positions()) == 0

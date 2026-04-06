"""Tests for portfolio management."""

import csv
from pathlib import Path

import pytest

from quantkit.portfolio import clear_positions, detect_and_import, import_csv, list_positions


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


def test_detect_and_import_quantkit_csv(tmp_path, monkeypatch):
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
        ],
    )

    count, format_name = detect_and_import(csv_path)

    assert count == 1
    assert format_name == "QuantKit CSV"
    positions = list_positions()
    assert positions[0]["symbol"] == "AAPL"


def test_detect_and_import_ibkr_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    csv_path = tmp_path / "ibkr.csv"
    rows = [
        ["Statement", "BrokerName"],
        [
            "Transaction History",
            "Header",
            "Date",
            "Unused1",
            "Unused2",
            "交易类型",
            "代码",
            "数量",
            "价格",
            "Price Currency",
        ],
        [
            "Transaction History",
            "Data",
            "2025-12-17",
            "",
            "",
            "买",
            "BRK B",
            "10",
            "455.25",
            "USD",
        ],
        [
            "Transaction History",
            "Data",
            "2025-12-18",
            "",
            "",
            "卖",
            "AAPL",
            "5",
            "200.00",
            "USD",
        ],
        [
            "Transaction History",
            "Data",
            "2025-12-19",
            "",
            "",
            "买",
            "600519.SH",
            "2",
            "1680.00",
            "CNY",
        ],
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    count, format_name = detect_and_import(csv_path)

    assert count == 2
    assert format_name == "IBKR"
    positions = list_positions()
    assert positions[0]["symbol"] == "BRK B"
    assert positions[0]["market"] == "US"
    assert positions[1]["symbol"] == "600519.SH"
    assert positions[1]["market"] == "CN"


def test_detect_and_import_ibkr_csv_with_english_buy(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    csv_path = tmp_path / "ibkr_en.csv"
    rows = [
        ["Statement", "BrokerName"],
        [
            "Transaction History",
            "Header",
            "Date",
            "Unused1",
            "Unused2",
            "Action",
            "Symbol",
            "Quantity",
            "Price",
            "Price Currency",
        ],
        [
            "Transaction History",
            "Data",
            "2025-12-17",
            "",
            "",
            "Buy",
            "AAPL",
            "10",
            "200.00",
            "USD",
        ],
        [
            "Transaction History",
            "Data",
            "2025-12-18",
            "",
            "",
            "SELL",
            "TSLA",
            "5",
            "300.00",
            "USD",
        ],
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    count, format_name = detect_and_import(csv_path)

    assert count == 1
    assert format_name == "IBKR"
    positions = list_positions()
    assert positions == [
        {
            "symbol": "AAPL",
            "buy_date": "2025-12-17",
            "buy_price": 200.0,
            "quantity": 10.0,
            "market": "US",
        }
    ]

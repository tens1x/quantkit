"""Integration test for the new command-driven CLI flow."""

import pandas as pd

from quantkit.commands import parse_command, route
from quantkit.stock_context import StockContext


def _make_ohlcv(n: int = 252) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-01", periods=n).date
    return pd.DataFrame(
        {
            "date": list(dates),
            "open": [100.0] * n,
            "high": [105.0] * n,
            "low": [95.0] * n,
            "close": [102.0] * n,
            "volume": [1_000_000] * n,
        }
    )


def test_full_workflow(monkeypatch):
    """Test: load stock -> factor check -> route commands."""
    ohlcv = _make_ohlcv()
    fundamentals = {"pe": 15.0, "pb": 2.0, "roe": 0.20, "revenue_growth": 0.1}

    monkeypatch.setattr("quantkit.stock_context.get_ohlcv", lambda s, st, e: ohlcv)
    monkeypatch.setattr("quantkit.stock_context.get_fundamentals", lambda s: fundamentals)

    ctx = StockContext.load("AAPL")
    assert ctx.symbol == "AAPL"
    assert ctx.has_fundamentals

    factors = ctx.get_factors()
    assert "pe" in factors
    assert "roe" in factors

    cmd, args = parse_command("/factor")
    assert cmd == "factor"
    assert args == []

    cmd, args = parse_command("/guru buffett")
    assert cmd == "guru"
    assert args == ["buffett"]

    result = route("/exit", ctx)
    assert result == "exit"


def test_persona_evaluation_with_stock_context(monkeypatch):
    """Test: persona engine works with StockContext factors."""
    ohlcv = _make_ohlcv()
    fundamentals = {"pe": 15.0, "pb": 2.0, "roe": 0.20, "revenue_growth": 0.1}

    monkeypatch.setattr("quantkit.stock_context.get_ohlcv", lambda s, st, e: ohlcv)
    monkeypatch.setattr("quantkit.stock_context.get_fundamentals", lambda s: fundamentals)

    ctx = StockContext.load("AAPL")
    factors = ctx.get_factors()

    from quantkit.persona.engine import Persona, Rule, evaluate

    persona = Persona(
        name="Test",
        name_en="test",
        philosophy="test",
        rules=[
            Rule(factor="pe", op="<", threshold=20, weight=3, hit="good", miss="bad"),
            Rule(factor="roe", op=">", threshold=0.15, weight=3, hit="good", miss="bad"),
        ],
        buy_threshold=0.7,
        watch_threshold=0.4,
    )
    verdict = evaluate(persona, factors)
    assert verdict.action in ("买入", "观望", "回避", "数据不足")
    assert 0.0 <= verdict.score <= 1.0

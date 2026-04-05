"""Bar-by-bar backtest engine."""

import numpy as np
import pandas as pd


def run_backtest(
    ohlcv: pd.DataFrame,
    signals: pd.Series,
    capital: float = 100_000,
    slippage_bps: float = 10,
    commission_bps: float = 5,
) -> dict:
    """Run a bar-by-bar backtest. Returns equity curve and trade list."""
    closes = ohlcv["close"].values
    sigs = signals.values
    n = len(closes)

    cash = capital
    shares = 0.0
    equity = np.zeros(n)
    trades = []
    entry_price = 0.0
    slip_rate = slippage_bps / 10_000
    comm_rate = commission_bps / 10_000

    for i in range(n):
        price = closes[i]

        if sigs[i] == 1 and shares == 0:
            # Buy
            exec_price = price * (1 + slip_rate)
            commission = exec_price * comm_rate
            max_shares = cash / (exec_price + commission)
            shares = int(max_shares)
            if shares > 0:
                cost = shares * exec_price + shares * commission
                cash -= cost
                entry_price = exec_price

        elif sigs[i] == 0 and shares > 0:
            # Sell
            exec_price = price * (1 - slip_rate)
            commission = shares * exec_price * comm_rate
            proceeds = shares * exec_price - commission
            pnl = proceeds - shares * entry_price
            trades.append({"pnl": pnl, "entry": entry_price, "exit": exec_price})
            cash += proceeds
            shares = 0

        equity[i] = cash + shares * price

    return {
        "equity_curve": pd.Series(equity, index=ohlcv.index),
        "trades": trades,
        "final_equity": equity[-1] if n > 0 else capital,
    }


def compute_metrics(equity: pd.Series, trades: list[dict], days: int = 252) -> dict:
    """Compute performance metrics from equity curve and trades."""
    total_return = (equity.iloc[-1] / equity.iloc[0] - 1) if len(equity) > 0 else 0
    n_days = len(equity)
    years = n_days / days if n_days > 0 else 1
    annualized = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    # Sharpe
    returns = equity.pct_change().dropna()
    if len(returns) > 1 and returns.std() > 0:
        sharpe = returns.mean() / returns.std() * np.sqrt(days)
    else:
        sharpe = 0

    # Max drawdown
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    max_drawdown = float(drawdown.min()) if len(drawdown) > 0 else 0

    # Win rate
    trade_count = len(trades)
    wins = sum(1 for t in trades if t["pnl"] > 0)
    win_rate = wins / trade_count if trade_count > 0 else 0

    return {
        "total_return": total_return,
        "annualized_return": annualized,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "trade_count": trade_count,
    }

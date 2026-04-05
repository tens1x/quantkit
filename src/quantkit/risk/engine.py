"""Risk lens engine: concentration, correlation, volatility contribution, drawdown."""

import numpy as np
import pandas as pd


def compute_concentration(market_values: dict[str, float]) -> dict:
    """Compute position weights and flag concentration risk (>30%)."""
    total = sum(market_values.values())
    if total == 0:
        return {}
    result = {}
    for symbol, mv in sorted(market_values.items(), key=lambda x: -x[1]):
        weight = mv / total
        result[symbol] = {
            "market_value": mv,
            "weight": weight,
            "warning": weight > 0.30,
        }
    return result


def compute_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Compute pairwise correlation matrix of daily returns."""
    return returns.corr()


def compute_volatility_contribution(
    returns: pd.DataFrame, weights: dict[str, float]
) -> dict:
    """Compute each stock's marginal contribution to portfolio volatility."""
    symbols = list(weights.keys())
    w = np.array([weights[s] for s in symbols])
    cov = returns[symbols].cov().values
    port_vol = np.sqrt(w @ cov @ w)

    if port_vol == 0:
        return {s: {"contribution": 0.0} for s in symbols}

    # Marginal contribution = (cov @ w) * w / port_var
    marginal = (cov @ w) * w / (port_vol ** 2)
    result = {}
    for i, s in enumerate(symbols):
        result[s] = {"contribution": float(marginal[i])}
    return result


def compute_max_drawdown(equity: pd.Series) -> dict:
    """Compute maximum drawdown from equity series."""
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    trough_idx = drawdown.idxmin()
    peak_idx = equity.loc[:trough_idx].idxmax()

    # Find recovery (if any)
    peak_value = equity.loc[peak_idx]
    recovery_idx = None
    after_trough = equity.loc[trough_idx:]
    recovered = after_trough[after_trough >= peak_value]
    if len(recovered) > 0:
        recovery_idx = recovered.index[0]

    return {
        "max_drawdown": float(drawdown.min()),
        "peak_date_idx": peak_idx,
        "trough_date_idx": trough_idx,
        "recovery_date_idx": recovery_idx,
    }

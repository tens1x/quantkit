"""Factor check engine: compute and rate 6 factors."""

import numpy as np
import pandas as pd
from typing import Optional


def rate_factor(
    name: str, value: Optional[float], percentile: Optional[float] = None
) -> tuple[str, str]:
    """Rate a factor value. Returns (color, label)."""
    if value is None:
        return ("yellow", "N/A")

    if name in ("pe", "pb"):
        if percentile is None:
            return ("yellow", "N/A")
        if percentile < 50:
            return ("green", f"{percentile:.0f}th pct")
        elif percentile < 80:
            return ("yellow", f"{percentile:.0f}th pct")
        else:
            return ("red", f"{percentile:.0f}th pct")

    if name == "roe":
        if value > 0.15:
            return ("green", "Healthy")
        elif value > 0.10:
            return ("yellow", "Moderate")
        else:
            return ("red", "Low")

    if name == "revenue_growth":
        if value > 0.10:
            return ("green", "Strong")
        elif value > 0:
            return ("yellow", "Moderate")
        else:
            return ("red", "Negative")

    if name == "volatility":
        if value < 0.25:
            return ("green", "Low")
        elif value < 0.40:
            return ("yellow", "Medium")
        else:
            return ("red", "High")

    if name == "momentum":
        if value > 0.40:
            return ("red", "Chasing")
        elif value < -0.10:
            return ("red", "Falling")
        elif value > 0.20:
            return ("yellow", "Elevated")
        else:
            return ("green", "Normal")

    return ("yellow", "Unknown")


def _annualized_volatility(closes: pd.Series, window: int = 60) -> Optional[float]:
    """Calculate annualized volatility from last N days of close prices."""
    if len(closes) < window:
        return None
    recent = closes.tail(window)
    returns = recent.pct_change().dropna()
    return float(returns.std() * np.sqrt(252))


def _momentum(closes: pd.Series, window: int = 20) -> Optional[float]:
    """Calculate momentum as % change over last N days."""
    if len(closes) < window:
        return None
    return float((closes.iloc[-1] / closes.iloc[-window] - 1))


def compute_factors(ohlcv: pd.DataFrame, fundamentals: dict) -> dict:
    """Compute all 6 factors. Returns dict of {name: {value, rating, label}}."""
    results = {}

    # PE
    pe_val = fundamentals.get("pe")
    pe_rating, pe_label = rate_factor("pe", pe_val, percentile=50)  # Default 50th if no history
    results["pe"] = {"value": pe_val, "rating": pe_rating, "label": pe_label}

    # PB
    pb_val = fundamentals.get("pb")
    pb_rating, pb_label = rate_factor("pb", pb_val, percentile=50)
    results["pb"] = {"value": pb_val, "rating": pb_rating, "label": pb_label}

    # ROE
    roe_val = fundamentals.get("roe")
    roe_rating, roe_label = rate_factor("roe", roe_val)
    results["roe"] = {"value": roe_val, "rating": roe_rating, "label": roe_label}

    # Revenue Growth
    rg_val = fundamentals.get("revenue_growth")
    rg_rating, rg_label = rate_factor("revenue_growth", rg_val)
    results["revenue_growth"] = {"value": rg_val, "rating": rg_rating, "label": rg_label}

    # Volatility
    vol_val = _annualized_volatility(ohlcv["close"])
    vol_rating, vol_label = rate_factor("volatility", vol_val)
    results["volatility"] = {"value": vol_val, "rating": vol_rating, "label": vol_label}

    # Momentum
    mom_val = _momentum(ohlcv["close"])
    mom_rating, mom_label = rate_factor("momentum", mom_val)
    results["momentum"] = {"value": mom_val, "rating": mom_rating, "label": mom_label}

    return results

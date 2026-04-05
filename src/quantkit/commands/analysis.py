"""Analysis command handlers: /factor, /backtest, /risk."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

import plotext as plt
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from quantkit.backtest.engine import compute_metrics, run_backtest
from quantkit.backtest.strategies import dca_signals, ma_cross_signals
from quantkit.config import load_config
from quantkit.portfolio import list_positions

if TYPE_CHECKING:
    from quantkit.stock_context import StockContext

console = Console()

RATING_ICONS = {
    "green": "[green]●[/green]",
    "yellow": "[yellow]●[/yellow]",
    "red": "[red]●[/red]",
}

FACTOR_DISPLAY = {
    "pe": "PE (TTM)",
    "pb": "PB",
    "roe": "ROE",
    "revenue_growth": "Revenue Growth",
    "volatility": "Volatility (60d)",
    "momentum": "Momentum (20d)",
}


def cmd_factor(ctx: StockContext) -> None:
    """Display 6-factor analysis table."""
    if not ctx.has_fundamentals:
        console.print("[yellow]基本面数据不可用，部分因子可能显示 N/A[/yellow]")

    factors = ctx.get_factors()
    table = Table(title=f"{ctx.symbol} Factor Check", show_lines=True)
    table.add_column("Factor", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Status")

    for key, name in FACTOR_DISPLAY.items():
        factor = factors[key]
        value = factor["value"]
        if value is None:
            value_str = "N/A"
        elif key in ("roe", "revenue_growth", "volatility", "momentum"):
            value_str = f"{value:.1%}"
        else:
            value_str = f"{value:.1f}"
        icon = RATING_ICONS.get(factor["rating"], "")
        table.add_row(name, value_str, f"{icon} {factor['label']}")

    console.print(table)


def cmd_backtest(ctx: StockContext, args: list[str]) -> None:
    """Run a backtest strategy. Prompts for strategy if not specified."""
    strategies = {"ma": "MA Cross (5/20)", "dca": "DCA (Monthly)"}

    if args and args[0].lower() in strategies:
        strategy_key = args[0].lower()
    else:
        if args and args[0].lower() not in strategies:
            console.print(f"[red]未知策略: {args[0]}，可选: ma, dca[/red]")
            return
        console.print("[bold][1][/bold] MA Cross (short/long moving average crossover)")
        console.print("[bold][2][/bold] DCA (dollar-cost averaging / monthly fixed buy)")
        choice = Prompt.ask("请选择策略", choices=["1", "2"], default="1")
        strategy_key = "ma" if choice == "1" else "dca"

    strategy_name = strategies[strategy_key]

    default_start = (date.today() - timedelta(days=3 * 365)).isoformat()
    default_end = date.today().isoformat()
    start = Prompt.ask("Start date", default=default_start)
    end = Prompt.ask("End date", default=default_end)

    cfg = load_config()
    capital = cfg["default_capital"]
    slippage = cfg["slippage_bps"]
    commission = cfg["commission_bps"]

    console.print(f"\n[bold]Fetching data for {ctx.symbol}...[/bold]")
    ohlcv = ctx.get_ohlcv(start, end)
    if ohlcv.empty:
        console.print(Panel(f"No data for {ctx.symbol}", title="Error", border_style="red"))
        return

    if strategy_key == "ma":
        signals = ma_cross_signals(ohlcv, short_window=5, long_window=20)
    else:
        signals = dca_signals(ohlcv, day_of_month=1)

    result = run_backtest(
        ohlcv,
        signals,
        capital=capital,
        slippage_bps=slippage,
        commission_bps=commission,
    )
    metrics = compute_metrics(result["equity_curve"], result["trades"])

    equity = result["equity_curve"].values
    plt.clear_figure()
    plt.plot(list(range(len(equity))), list(equity), label="Strategy")
    closes = ohlcv["close"].values
    benchmark = [capital * (c / closes[0]) for c in closes]
    plt.plot(list(range(len(benchmark))), benchmark, label="Buy & Hold")
    plt.title(f"{ctx.symbol} - {strategy_name}")
    plt.xlabel("Trading Days")
    plt.ylabel("Equity")
    plt.theme("dark")
    plt.plot_size(80, 20)
    plt.show()

    table = Table(title="Performance Metrics", show_lines=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Total Return", f"{metrics['total_return']:.1%}")
    table.add_row("Annualized Return", f"{metrics['annualized_return']:.1%}")
    table.add_row("Sharpe Ratio", f"{metrics['sharpe']:.2f}")
    table.add_row("Max Drawdown", f"{metrics['max_drawdown']:.1%}")
    table.add_row("Win Rate", f"{metrics['win_rate']:.0%}")
    table.add_row("Trade Count", str(metrics["trade_count"]))
    buy_hold_return = (closes[-1] / closes[0] - 1) if len(closes) > 0 else 0
    table.add_row("vs Buy & Hold", f"{metrics['total_return'] - buy_hold_return:+.1%}")
    console.print(table)

    console.print(
        "\n[dim italic]Backtest ≠ live trading. Past performance ≠ future results.[/dim italic]"
    )


def cmd_risk() -> None:
    """Portfolio risk analysis. Does not require stock context."""
    import pandas as pd

    from quantkit.data.provider import get_ohlcv
    from quantkit.risk.engine import (
        compute_concentration,
        compute_correlation_matrix,
        compute_max_drawdown,
        compute_volatility_contribution,
    )

    positions = list_positions()
    if not positions:
        console.print(
            Panel(
                "No positions found. Use /portfolio to import a CSV first.",
                title="Error",
                border_style="red",
            )
        )
        return

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=365)).isoformat()

    holdings: dict[str, dict[str, float]] = {}
    for pos in positions:
        sym = pos["symbol"]
        if sym not in holdings:
            holdings[sym] = {"quantity": 0, "total_cost": 0}
        holdings[sym]["quantity"] += pos["quantity"]
        holdings[sym]["total_cost"] += pos["quantity"] * pos["buy_price"]

    console.print("[bold]Fetching market data...[/bold]")
    returns_dict: dict[str, pd.Series] = {}
    market_values: dict[str, float] = {}
    for sym in holdings:
        try:
            ohlcv = get_ohlcv(sym, start, end)
            if ohlcv.empty:
                continue
            current_price = ohlcv["close"].iloc[-1]
            market_values[sym] = current_price * holdings[sym]["quantity"]
            returns_dict[sym] = ohlcv.set_index("date")["close"].pct_change().dropna()
        except Exception as exc:
            console.print(f"[yellow]Skipping {sym}: {exc}[/yellow]")

    if not market_values:
        console.print(
            Panel("Could not fetch data for any positions.", title="Error", border_style="red")
        )
        return

    console.print("\n[bold underline]1. Concentration[/bold underline]")
    concentration = compute_concentration(market_values)
    table = Table(show_lines=True)
    table.add_column("Symbol", style="bold")
    table.add_column("Market Value", justify="right")
    table.add_column("Weight", justify="right")
    table.add_column("Status")
    for sym, data in concentration.items():
        status = "[red]CONCENTRATED[/red]" if data["warning"] else "[green]OK[/green]"
        table.add_row(sym, f"{data['market_value']:,.0f}", f"{data['weight']:.1%}", status)
    console.print(table)

    if len(returns_dict) >= 2:
        console.print("\n[bold underline]2. Correlation Matrix[/bold underline]")
        returns_df = pd.DataFrame(returns_dict)
        correlation = compute_correlation_matrix(returns_df)
        corr_table = Table(show_lines=True)
        corr_table.add_column("")
        for col in correlation.columns:
            corr_table.add_column(str(col), justify="center")
        for idx in correlation.index:
            row_vals = []
            for col in correlation.columns:
                val = correlation.loc[idx, col]
                if idx == col:
                    row_vals.append("[dim]1.00[/dim]")
                elif val > 0.7:
                    row_vals.append(f"[red]{val:.2f}[/red]")
                elif val > 0.4:
                    row_vals.append(f"[yellow]{val:.2f}[/yellow]")
                else:
                    row_vals.append(f"[green]{val:.2f}[/green]")
            corr_table.add_row(str(idx), *row_vals)
        console.print(corr_table)

    if len(returns_dict) >= 2:
        console.print("\n[bold underline]3. Volatility Contribution[/bold underline]")
        total_mv = sum(market_values.values())
        weights = {s: mv / total_mv for s, mv in market_values.items()}
        returns_df = pd.DataFrame(returns_dict)
        vol_contrib = compute_volatility_contribution(returns_df, weights)
        vol_table = Table(show_lines=True)
        vol_table.add_column("Symbol", style="bold")
        vol_table.add_column("Contribution", justify="right")
        for sym, data in sorted(vol_contrib.items(), key=lambda x: -x[1]["contribution"]):
            vol_table.add_row(sym, f"{data['contribution']:.1%}")
        console.print(vol_table)

    console.print("\n[bold underline]4. Historical Drawdown[/bold underline]")
    returns_df = pd.DataFrame(returns_dict)
    total_mv = sum(market_values.values())
    weights_s = pd.Series({s: market_values[s] / total_mv for s in returns_df.columns})
    port_returns = (returns_df * weights_s).sum(axis=1)
    port_equity = (1 + port_returns).cumprod() * total_mv
    dd = compute_max_drawdown(port_equity)
    console.print(
        f"Based on the past year, your portfolio could drop up to "
        f"[bold red]{abs(dd['max_drawdown']):.1%}[/bold red] from peak."
    )

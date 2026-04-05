"""Rich menu system for QuantKit."""

from pathlib import Path

import plotext as plt
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from quantkit.backtest.engine import compute_metrics, run_backtest
from quantkit.backtest.strategies import dca_signals, ma_cross_signals
from quantkit.config import load_config, save_config
from quantkit.data.provider import get_fundamentals, get_ohlcv
from quantkit.factor.engine import compute_factors
from quantkit.portfolio import clear_positions, import_csv, list_positions
from quantkit.risk.engine import (
    compute_concentration,
    compute_correlation_matrix,
    compute_max_drawdown,
    compute_volatility_contribution,
)

console = Console()

RATING_ICONS = {
    "green": "[green]●[/green]",
    "yellow": "[yellow]●[/yellow]",
    "red": "[red]●[/red]",
}


def _pause() -> None:
    Prompt.ask("\n[dim]Press Enter to return[/dim]", default="")


def _error(msg: str) -> None:
    console.print(Panel(msg, title="Error", border_style="red"))


def main() -> None:
    """Main menu loop."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold][1][/bold] Factor Check       Multi-dimensional health check\n"
                "[bold][2][/bold] Strategy Backtest   Validate buy/sell rules\n"
                "[bold][3][/bold] Risk Lens           Understand portfolio risk\n"
                "[bold][4][/bold] Portfolio Management Import / view positions\n"
                "[bold][5][/bold] Settings            Configure tokens & defaults\n"
                "[bold][0][/bold] Exit",
                title="[bold green]QuantKit[/bold green]",
                subtitle="Personal Investment Toolkit",
                padding=(1, 2),
            )
        )
        choice = Prompt.ask("Choose", choices=["0", "1", "2", "3", "4", "5"], default="0")
        if choice == "0":
            console.print("[dim]Goodbye.[/dim]")
            break
        if choice == "1":
            _menu_factor_check()
        elif choice == "2":
            _menu_backtest()
        elif choice == "3":
            _menu_risk_lens()
        elif choice == "4":
            _menu_portfolio()
        elif choice == "5":
            _menu_settings()


def _menu_factor_check() -> None:
    console.clear()
    console.print(Panel("Factor Check", style="bold cyan"))
    mode = Prompt.ask("[1] Single stock  [2] All positions", choices=["1", "2"], default="1")

    if mode == "1":
        symbol = Prompt.ask("Stock symbol (e.g. AAPL or 600519.SH)").strip().upper()
        _run_factor_check([symbol])
    else:
        positions = list_positions()
        if not positions:
            _error("No positions found. Import a CSV first via Portfolio menu.")
            _pause()
            return
        symbols = list({position["symbol"] for position in positions})
        _run_factor_check(symbols)
    _pause()


def _run_factor_check(symbols: list[str]) -> None:
    from datetime import date, timedelta

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=365)).isoformat()

    for symbol in symbols:
        try:
            console.print(f"\n[bold]Fetching data for {symbol}...[/bold]")
            ohlcv = get_ohlcv(symbol, start, end)
            fundamentals = get_fundamentals(symbol)
            if ohlcv.empty:
                _error(f"No OHLCV data for {symbol}")
                continue
            factors = compute_factors(ohlcv, fundamentals)
            _display_factor_table(symbol, factors)
        except Exception as exc:
            _error(f"{symbol}: {exc}")


def _display_factor_table(symbol: str, factors: dict) -> None:
    table = Table(title=f"{symbol} Factor Check", show_lines=True)
    table.add_column("Factor", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Status")

    display_names = {
        "pe": "PE (TTM)",
        "pb": "PB",
        "roe": "ROE",
        "revenue_growth": "Revenue Growth",
        "volatility": "Volatility (60d)",
        "momentum": "Momentum (20d)",
    }
    for key, name in display_names.items():
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


def _menu_backtest() -> None:
    console.clear()
    console.print(Panel("Strategy Backtest", style="bold cyan"))
    console.print("[bold][1][/bold] MA Cross (short/long moving average crossover)")
    console.print("[bold][2][/bold] DCA (dollar-cost averaging / monthly fixed buy)")
    strategy = Prompt.ask("Choose strategy", choices=["1", "2"], default="1")
    symbol = Prompt.ask("Stock symbol").strip().upper()

    from datetime import date, timedelta

    default_start = (date.today() - timedelta(days=3 * 365)).isoformat()
    default_end = date.today().isoformat()
    start = Prompt.ask("Start date", default=default_start)
    end = Prompt.ask("End date", default=default_end)

    cfg = load_config()
    capital = cfg["default_capital"]
    slippage = cfg["slippage_bps"]
    commission = cfg["commission_bps"]

    try:
        console.print(f"\n[bold]Fetching data for {symbol}...[/bold]")
        ohlcv = get_ohlcv(symbol, start, end)
        if ohlcv.empty:
            _error(f"No data for {symbol}")
            _pause()
            return

        if strategy == "1":
            signals = ma_cross_signals(ohlcv, short_window=5, long_window=20)
            strategy_name = "MA Cross (5/20)"
        else:
            signals = dca_signals(ohlcv, day_of_month=1)
            strategy_name = "DCA (Monthly)"

        result = run_backtest(
            ohlcv,
            signals,
            capital=capital,
            slippage_bps=slippage,
            commission_bps=commission,
        )
        metrics = compute_metrics(result["equity_curve"], result["trades"])

        _display_backtest_result(symbol, strategy_name, ohlcv, result, metrics, capital)
    except Exception as exc:
        _error(str(exc))
    _pause()


def _display_backtest_result(
    symbol: str, strategy_name: str, ohlcv, result: dict, metrics: dict, capital: float
) -> None:
    equity = result["equity_curve"].values
    plt.clear_figure()
    plt.plot(list(range(len(equity))), list(equity), label="Strategy")

    closes = ohlcv["close"].values
    benchmark = [capital * (close / closes[0]) for close in closes]
    plt.plot(list(range(len(benchmark))), benchmark, label="Buy & Hold")
    plt.title(f"{symbol} - {strategy_name}")
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


def _menu_risk_lens() -> None:
    console.clear()
    console.print(Panel("Risk Lens", style="bold cyan"))
    positions = list_positions()
    if not positions:
        _error("No positions found. Import a CSV first via Portfolio menu.")
        _pause()
        return

    from datetime import date, timedelta

    import pandas as pd

    end = date.today().isoformat()
    start = (date.today() - timedelta(days=365)).isoformat()

    holdings: dict[str, dict[str, float]] = {}
    for position in positions:
        symbol = position["symbol"]
        if symbol not in holdings:
            holdings[symbol] = {"quantity": 0, "total_cost": 0}
        holdings[symbol]["quantity"] += position["quantity"]
        holdings[symbol]["total_cost"] += position["quantity"] * position["buy_price"]

    console.print("[bold]Fetching market data...[/bold]")
    returns_dict = {}
    market_values = {}
    for symbol in holdings:
        try:
            ohlcv = get_ohlcv(symbol, start, end)
            if ohlcv.empty:
                continue
            current_price = ohlcv["close"].iloc[-1]
            market_values[symbol] = current_price * holdings[symbol]["quantity"]
            returns_dict[symbol] = ohlcv.set_index("date")["close"].pct_change().dropna()
        except Exception as exc:
            console.print(f"[yellow]Skipping {symbol}: {exc}[/yellow]")

    if not market_values:
        _error("Could not fetch data for any positions.")
        _pause()
        return

    console.print("\n[bold underline]1. Concentration[/bold underline]")
    concentration = compute_concentration(market_values)
    table = Table(show_lines=True)
    table.add_column("Symbol", style="bold")
    table.add_column("Market Value", justify="right")
    table.add_column("Weight", justify="right")
    table.add_column("Status")
    for symbol, data in concentration.items():
        status = "[red]CONCENTRATED[/red]" if data["warning"] else "[green]OK[/green]"
        table.add_row(
            symbol,
            f"{data['market_value']:,.0f}",
            f"{data['weight']:.1%}",
            status,
        )
    console.print(table)

    if len(returns_dict) >= 2:
        console.print("\n[bold underline]2. Correlation Matrix[/bold underline]")
        returns_df = pd.DataFrame(returns_dict)
        correlation = compute_correlation_matrix(returns_df)
        corr_table = Table(show_lines=True)
        corr_table.add_column("")
        for column in correlation.columns:
            corr_table.add_column(str(column), justify="center")
        for index in correlation.index:
            row_values = []
            for column in correlation.columns:
                value = correlation.loc[index, column]
                if index == column:
                    row_values.append("[dim]1.00[/dim]")
                elif value > 0.7:
                    row_values.append(f"[red]{value:.2f}[/red]")
                elif value > 0.4:
                    row_values.append(f"[yellow]{value:.2f}[/yellow]")
                else:
                    row_values.append(f"[green]{value:.2f}[/green]")
            corr_table.add_row(str(index), *row_values)
        console.print(corr_table)
        high_pairs = sum(
            1
            for i in range(len(correlation))
            for j in range(i + 1, len(correlation))
            if correlation.iloc[i, j] > 0.7
        )
        total_pairs = len(correlation) * (len(correlation) - 1) // 2
        if high_pairs > 0:
            console.print(
                f"[yellow]{high_pairs} of {total_pairs} pairs highly correlated (>0.7) "
                f"— limited diversification[/yellow]"
            )

    if len(returns_dict) >= 2:
        console.print("\n[bold underline]3. Volatility Contribution[/bold underline]")
        total_market_value = sum(market_values.values())
        weights = {symbol: market_value / total_market_value for symbol, market_value in market_values.items()}
        returns_df = pd.DataFrame(returns_dict)
        vol_contribution = compute_volatility_contribution(returns_df, weights)
        vol_table = Table(show_lines=True)
        vol_table.add_column("Symbol", style="bold")
        vol_table.add_column("Contribution", justify="right")
        for symbol, data in sorted(
            vol_contribution.items(),
            key=lambda item: -item[1]["contribution"],
        ):
            vol_table.add_row(symbol, f"{data['contribution']:.1%}")
        console.print(vol_table)

    console.print("\n[bold underline]4. Historical Drawdown[/bold underline]")
    returns_df = pd.DataFrame(returns_dict)
    total_market_value = sum(market_values.values())
    weights = pd.Series({symbol: market_values[symbol] / total_market_value for symbol in returns_df.columns})
    portfolio_returns = (returns_df * weights).sum(axis=1)
    portfolio_equity = (1 + portfolio_returns).cumprod() * total_market_value
    drawdown = compute_max_drawdown(portfolio_equity)
    console.print(
        f"Based on the past year, your portfolio could drop up to "
        f"[bold red]{abs(drawdown['max_drawdown']):.1%}[/bold red] from peak."
    )

    _pause()


def _menu_portfolio() -> None:
    console.clear()
    console.print(Panel("Portfolio Management", style="bold cyan"))
    console.print("[bold][1][/bold] Import CSV")
    console.print("[bold][2][/bold] View positions")
    console.print("[bold][3][/bold] Clear all positions")
    console.print("[bold][0][/bold] Back")
    choice = Prompt.ask("Choose", choices=["0", "1", "2", "3"], default="0")

    if choice == "1":
        path = Prompt.ask("CSV file path").strip()
        try:
            count = import_csv(Path(path))
            console.print(f"[green]Imported {count} positions.[/green]")
        except Exception as exc:
            _error(str(exc))
    elif choice == "2":
        positions = list_positions()
        if not positions:
            console.print("[dim]No positions yet.[/dim]")
        else:
            table = Table(title="Positions", show_lines=True)
            table.add_column("Symbol", style="bold")
            table.add_column("Buy Date")
            table.add_column("Buy Price", justify="right")
            table.add_column("Quantity", justify="right")
            table.add_column("Market")
            for position in positions:
                table.add_row(
                    position["symbol"],
                    position["buy_date"],
                    f"{position['buy_price']:.2f}",
                    f"{position['quantity']:.0f}",
                    position["market"],
                )
            console.print(table)
    elif choice == "3":
        confirm = Prompt.ask("Delete all positions?", choices=["y", "n"], default="n")
        if confirm == "y":
            clear_positions()
            console.print("[green]All positions cleared.[/green]")
    _pause()


def _menu_settings() -> None:
    console.clear()
    console.print(Panel("Settings", style="bold cyan"))
    cfg = load_config()
    table = Table(show_lines=True)
    table.add_column("Setting", style="bold")
    table.add_column("Current Value")
    table.add_row("Tushare Token", cfg["tushare_token"] or "[dim]not set[/dim]")
    table.add_row("Default Capital", f"{cfg['default_capital']:,}")
    table.add_row("Slippage (bps)", str(cfg["slippage_bps"]))
    table.add_row("Commission (bps)", str(cfg["commission_bps"]))
    console.print(table)

    console.print("\n[bold][1][/bold] Set Tushare Token")
    console.print("[bold][2][/bold] Set Default Capital")
    console.print("[bold][3][/bold] Set Slippage")
    console.print("[bold][4][/bold] Set Commission")
    console.print("[bold][0][/bold] Back")
    choice = Prompt.ask("Choose", choices=["0", "1", "2", "3", "4"], default="0")

    if choice == "1":
        cfg["tushare_token"] = Prompt.ask("Tushare Token")
        save_config(cfg)
        console.print("[green]Saved.[/green]")
    elif choice == "2":
        cfg["default_capital"] = IntPrompt.ask("Default Capital", default=cfg["default_capital"])
        save_config(cfg)
        console.print("[green]Saved.[/green]")
    elif choice == "3":
        cfg["slippage_bps"] = IntPrompt.ask("Slippage (bps)", default=cfg["slippage_bps"])
        save_config(cfg)
        console.print("[green]Saved.[/green]")
    elif choice == "4":
        cfg["commission_bps"] = IntPrompt.ask("Commission (bps)", default=cfg["commission_bps"])
        save_config(cfg)
        console.print("[green]Saved.[/green]")
    _pause()

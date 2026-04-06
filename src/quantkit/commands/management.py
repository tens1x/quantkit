"""Management command handlers: /portfolio, /settings, /help."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.rule import Rule
from rich.table import Table

from quantkit.commands import COMMANDS
from quantkit.config import load_config, save_config
from quantkit.portfolio import clear_positions, detect_and_import, list_positions

if TYPE_CHECKING:
    from quantkit.stock_context import StockContext

console = Console()


def _ask_int_with_min(label: str, default: int, min_value: int) -> int:
    """Prompt until the user enters an integer greater than or equal to min_value."""
    while True:
        value = IntPrompt.ask(label, default=default)
        if value >= min_value:
            return value
        console.print(f"[red]{label} 必须 >= {min_value}，请重试。[/red]")


def _mask_token(token: str) -> str:
    """Mask a token for display in settings."""
    if len(token) <= 8:
        return token
    return f"{token[:4]}****{token[-4:]}"


def cmd_portfolio() -> None:
    """Portfolio management submenu."""
    while True:
        console.print(Rule("Portfolio", style="cyan"))
        console.print("[bold][1][/bold] Import CSV")
        console.print("[bold][2][/bold] View positions")
        console.print("[bold][3][/bold] Clear all positions")
        console.print("[bold][0][/bold] Back")
        choice = Prompt.ask("Choose", choices=["0", "1", "2", "3"], default="0")

        if choice == "0":
            return
        if choice == "1":
            console.print("支持格式: QuantKit CSV 或 IBKR 交易记录导出")
            console.print("QuantKit CSV 格式: symbol,buy_date,buy_price,quantity,market")
            path = Prompt.ask("CSV file path").strip()
            try:
                count, format_name = detect_and_import(Path(path))
                console.print(f"[green]Detected format: {format_name}[/green]")
                console.print(f"[green]Imported {count} positions.[/green]")
            except Exception as exc:
                console.print(Panel(str(exc), title="Error", border_style="red"))
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            continue
        if choice == "2":
            positions = list_positions()
            if not positions:
                console.print("[dim]No positions yet.[/dim]")
            else:
                table = Table(
                    title="Positions",
                    show_lines=True,
                    box=box.ROUNDED,
                    title_style="bold cyan",
                )
                table.add_column("Symbol", style="bold")
                table.add_column("Buy Date")
                table.add_column("Buy Price", justify="right")
                table.add_column("Quantity", justify="right")
                table.add_column("Market")
                for pos in positions:
                    table.add_row(
                        pos["symbol"],
                        pos["buy_date"],
                        f"{pos['buy_price']:.2f}",
                        f"{pos['quantity']:.0f}",
                        pos["market"],
                    )
                console.print(table)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            continue

        confirm = Prompt.ask("Delete all positions?", choices=["y", "n"], default="n")
        if confirm == "y":
            clear_positions()
            console.print("[green]All positions cleared.[/green]")
        Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def cmd_settings() -> None:
    """Settings submenu."""
    while True:
        cfg = load_config()
        table = Table(show_lines=True, box=box.ROUNDED)
        table.add_column("Setting", style="bold")
        table.add_column("Current Value")
        token = cfg.get("tushare_token", "")
        table.add_row("Tushare Token", _mask_token(token) if token else "[dim]not set[/dim]")
        table.add_row("Default Capital", f"{cfg['default_capital']:,}")
        table.add_row("Slippage (bps)", str(cfg["slippage_bps"]))
        table.add_row("Commission (bps)", str(cfg["commission_bps"]))
        persona_status = "[green]ON[/green]" if cfg.get("persona_mode") else "[red]OFF[/red]"
        table.add_row("Persona Mode", persona_status)

        console.print(Rule("Settings", style="cyan"))
        console.print(table)

        console.print("\n[bold][1][/bold] Set Tushare Token")
        console.print("[bold][2][/bold] Set Default Capital")
        console.print("[bold][3][/bold] Set Slippage")
        console.print("[bold][4][/bold] Set Commission")
        console.print("[bold][5][/bold] Toggle Persona Mode")
        console.print("[bold][0][/bold] Back")
        choice = Prompt.ask("Choose", choices=["0", "1", "2", "3", "4", "5"], default="0")

        if choice == "0":
            return
        if choice == "1":
            cfg["tushare_token"] = Prompt.ask("Tushare Token")
            save_config(cfg)
            console.print("[green]Saved.[/green]")
        elif choice == "2":
            cfg["default_capital"] = _ask_int_with_min(
                "Default Capital",
                default=cfg["default_capital"],
                min_value=1000,
            )
            save_config(cfg)
            console.print("[green]Saved.[/green]")
        elif choice == "3":
            cfg["slippage_bps"] = _ask_int_with_min(
                "Slippage (bps)",
                default=cfg["slippage_bps"],
                min_value=0,
            )
            save_config(cfg)
            console.print("[green]Saved.[/green]")
        elif choice == "4":
            cfg["commission_bps"] = _ask_int_with_min(
                "Commission (bps)",
                default=cfg["commission_bps"],
                min_value=0,
            )
            save_config(cfg)
            console.print("[green]Saved.[/green]")
        elif choice == "5":
            cfg["persona_mode"] = not cfg.get("persona_mode", False)
            save_config(cfg)
            state = "ON" if cfg["persona_mode"] else "OFF"
            console.print(f"[green]Persona Mode: {state}[/green]")
        Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")


def cmd_help(ctx: StockContext | None) -> None:
    """Display available commands."""
    cfg = load_config()
    persona_enabled = cfg.get("persona_mode", False)

    console.print(Rule("Help", style="cyan"))
    table = Table(show_lines=True, box=box.ROUNDED)
    table.add_column("Command", style="bold")
    table.add_column("Description")

    for name, info in COMMANDS.items():
        if name == "exit":
            continue
        if info.requires_persona and not persona_enabled:
            continue
        note = " (需要先输入股票代码)" if info.requires_context else ""
        table.add_row(f"/{name}", f"{info.description}{note}")

    table.add_row("/exit", "退出程序")
    table.add_row("[dim]<股票代码>[/dim]", "[dim]输入股票代码进入/切换上下文[/dim]")
    console.print(table)

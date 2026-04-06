"""Stock-centric command-driven CLI for QuantKit."""

from __future__ import annotations

import os
import sys

from rich import box
from rich.console import Console
from rich.panel import Panel

from quantkit.commands import route
from quantkit.config import load_config
from quantkit.prompt import SymbolAutoSuggest, create_session, get_prompt_message
from quantkit.stock_context import StockContext

console = Console()
VERSION = "0.1.0"


def _show_banner() -> None:
    """Display startup banner."""
    console.print(
        Panel(
            f"[bold green]QuantKit[/bold green] v{VERSION}\n"
            "Personal Investment Toolkit\n\n"
            "输入股票代码开始 · /help 查看命令",
            box=box.ROUNDED,
            border_style="green",
            padding=(1, 2),
        )
    )


def main() -> None:
    """Main loop: stock-centric command interface with auto-completion."""
    if sys.stdout.isatty():
        os.system("clear")

    _show_banner()

    symbol_suggest = SymbolAutoSuggest()
    session = create_session(symbol_suggest)
    ctx: StockContext | None = None

    while True:
        try:
            cfg = load_config()
            persona_mode = cfg.get("persona_mode", False)
            prompt_msg = get_prompt_message(ctx, persona_mode)
            user_input = session.prompt(prompt_msg).strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                result = route(user_input, ctx)
                if result == "exit":
                    console.print("[dim]Goodbye.[/dim]")
                    break
            else:
                symbol = user_input.upper()
                console.print(f"[bold]Fetching data for {symbol}...[/bold]")
                try:
                    new_ctx = StockContext.load(symbol)
                    ctx = new_ctx
                    symbol_suggest.add(symbol)
                    info_parts = [f"1y OHLCV ({len(ctx.ohlcv)} bars)"]
                    if ctx.has_fundamentals:
                        info_parts.append("fundamentals")
                    else:
                        info_parts.append("[yellow]fundamentals unavailable[/yellow]")
                    console.print(f"[green]Done[/green] ({', '.join(info_parts)})")
                except ValueError as exc:
                    console.print(Panel(str(exc), title="Error", border_style="red"))
                except Exception as exc:
                    console.print(Panel(str(exc), title="Error", border_style="red"))

        except KeyboardInterrupt:
            console.print()
            continue
        except EOFError:
            console.print("\n[dim]Goodbye.[/dim]")
            break

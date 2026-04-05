"""Stock-centric command-driven CLI for QuantKit."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from quantkit.commands import route
from quantkit.stock_context import StockContext

console = Console()


def main() -> None:
    """Main loop: stock-centric command interface."""
    console.print(
        Panel(
            "[bold green]QuantKit[/bold green] - Personal Investment Toolkit\n\n"
            "输入股票代码开始，或输入 /help 查看命令",
            padding=(1, 2),
        )
    )

    ctx: StockContext | None = None

    while True:
        try:
            prompt_str = f"{ctx.symbol} > " if ctx else "> "
            user_input = Prompt.ask(prompt_str).strip()

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

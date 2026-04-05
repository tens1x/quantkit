"""Persona command handler: /guru."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from quantkit.persona.engine import evaluate, load_personas

if TYPE_CHECKING:
    from quantkit.stock_context import StockContext

console = Console()

ACTION_STYLE = {
    "买入": "[bold green]买入[/bold green]",
    "观望": "[bold yellow]观望[/bold yellow]",
    "回避": "[bold red]回避[/bold red]",
    "数据不足": "[bold dim]数据不足[/bold dim]",
}


def _display_verdict(symbol: str, persona_name: str, philosophy: str, verdict) -> None:
    """Render a single persona verdict as a Rich panel."""
    action_str = ACTION_STYLE.get(verdict.action, verdict.action)
    reasons_str = "\n".join(verdict.reasons) if verdict.reasons else "(无评估数据)"

    content = (
        f'[dim italic]"{philosophy}"[/dim italic]\n\n'
        f"判断: {action_str} ({verdict.score:.0%})\n\n"
        f"{reasons_str}"
    )

    console.print(
        Panel(
            content,
            title=f"{persona_name}视角: {symbol}",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def cmd_guru(ctx: StockContext, args: list[str]) -> None:
    """Evaluate current stock through investor persona lens."""
    personas = load_personas()
    if not personas:
        console.print(
            "[yellow]没有可用的 persona 文件。请在 persona/personas/ 目录添加 YAML 文件。[/yellow]"
        )
        return

    if not ctx.has_fundamentals:
        console.print("[yellow]基本面数据不可用，评估结果可能不完整[/yellow]")

    factors = ctx.get_factors()

    if args and args[0].lower() == "all":
        selected = personas
    elif args:
        name = args[0].lower()
        match = [p for p in personas if p.name_en.lower() == name]
        if not match:
            available = ", ".join(p.name_en for p in personas)
            console.print(f"[red]未知投资人: {args[0]}，可选: {available}, all[/red]")
            return
        selected = match
    else:
        console.print("[bold]可用投资人:[/bold]")
        for i, p in enumerate(personas, 1):
            console.print(f"  [bold][{i}][/bold] {p.name} ({p.name_en})")
        console.print("  [bold][0][/bold] 全部")

        choices = [str(i) for i in range(len(personas) + 1)]
        choice = Prompt.ask("请选择", choices=choices, default="0")
        if choice == "0":
            selected = personas
        else:
            selected = [personas[int(choice) - 1]]

    if len(selected) > 5:
        summary = Table(title=f"{ctx.symbol} — 投资人总览", show_lines=True)
        summary.add_column("投资人", style="bold")
        summary.add_column("判断")
        summary.add_column("得分", justify="right")
        for p in selected:
            v = evaluate(p, factors)
            action_str = ACTION_STYLE.get(v.action, v.action)
            summary.add_row(f"{p.name} ({p.name_en})", action_str, f"{v.score:.0%}")
        console.print(summary)
        console.print("[dim]输入 /guru <name> 查看详情[/dim]")
        return

    for p in selected:
        verdict = evaluate(p, factors)
        _display_verdict(ctx.symbol, p.name, p.philosophy, verdict)

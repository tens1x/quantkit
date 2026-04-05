"""Command router: parse, validate, dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rich.console import Console

from quantkit.config import load_config

if TYPE_CHECKING:
    from collections.abc import Callable

    from quantkit.stock_context import StockContext

console = Console()


@dataclass
class CommandInfo:
    """Metadata for a registered command."""

    name: str
    description: str
    requires_context: bool
    requires_persona: bool = False


# Command registry — handlers are attached in submodules
COMMANDS: dict[str, CommandInfo] = {
    "factor": CommandInfo("factor", "因子分析", requires_context=True),
    "backtest": CommandInfo("backtest", "策略回测", requires_context=True),
    "risk": CommandInfo("risk", "持仓风险分析", requires_context=False),
    "guru": CommandInfo(
        "guru", "投资人视角评估", requires_context=True, requires_persona=True
    ),
    "portfolio": CommandInfo("portfolio", "持仓管理", requires_context=False),
    "settings": CommandInfo("settings", "设置", requires_context=False),
    "help": CommandInfo("help", "显示可用命令", requires_context=False),
    "exit": CommandInfo("exit", "退出", requires_context=False),
}


def parse_command(raw: str) -> tuple[str, list[str]]:
    """Parse user input into (command_name, args).

    Command name is lowercased. Args are preserved as-is.
    """
    stripped = raw.lstrip("/").strip()
    parts = stripped.split()
    if not parts:
        return "", []
    return parts[0].lower(), parts[1:]


def route(raw: str, ctx: StockContext | None) -> str | None:
    """Parse, validate, and dispatch a command.

    Returns "exit" if the user wants to quit, None otherwise.
    """
    cmd, args = parse_command(raw)

    if cmd == "exit":
        return "exit"

    if cmd not in COMMANDS:
        console.print(f"[red]未知命令: /{cmd}，输入 /help 查看可用命令[/red]")
        return None

    info = COMMANDS[cmd]

    if info.requires_context and ctx is None:
        console.print("[yellow]请先输入股票代码（如 AAPL 或 600519.SH）[/yellow]")
        return None

    if info.requires_persona:
        cfg = load_config()
        if not cfg.get("persona_mode", False):
            console.print("[yellow]Persona 功能未开启，请在 /settings 中启用[/yellow]")
            return None

    _dispatch(cmd, ctx, args)
    return None


def _dispatch(cmd: str, ctx: StockContext | None, args: list[str]) -> None:
    """Call the appropriate handler. Handlers are imported lazily."""
    from quantkit.commands.analysis import cmd_backtest, cmd_factor, cmd_risk
    from quantkit.commands.management import cmd_help, cmd_portfolio, cmd_settings
    from quantkit.commands.persona_cmd import cmd_guru

    handlers: dict[str, Callable[[], None]] = {
        "factor": lambda: cmd_factor(ctx),
        "backtest": lambda: cmd_backtest(ctx, args),
        "risk": cmd_risk,
        "guru": lambda: cmd_guru(ctx, args),
        "portfolio": cmd_portfolio,
        "settings": cmd_settings,
        "help": lambda: cmd_help(ctx),
    }

    handler = handlers.get(cmd)
    if handler:
        handler()

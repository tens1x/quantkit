"""prompt_toolkit integration: completer, auto-suggest, session, styles."""

from __future__ import annotations

from collections.abc import Iterator

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style as PtStyle

from quantkit.commands import COMMANDS
from quantkit.config import load_config
from quantkit.persona.engine import load_personas

STRATEGIES = {"ma": "MA Cross (5/20)", "dca": "DCA (Monthly)"}
PROMPT_STYLE = PtStyle.from_dict(
    {
        "completion-menu.completion": "bg:#333333 #ffffff",
        "completion-menu.completion.current": "bg:#00aa00 #ffffff bold",
        "completion-menu.meta.completion": "bg:#333333 #aaaaaa",
        "completion-menu.meta.completion.current": "bg:#00aa00 #aaaaaa",
        "auto-suggest": "#666666",
        "symbol": "bold ansibrightcyan",
        "chevron": "ansigreen",
        "persona-icon": "",
    }
)


class SymbolAutoSuggest(AutoSuggest):
    """Fish-style auto-suggest from successfully loaded stock symbols."""

    def __init__(self) -> None:
        self.symbols: list[str] = []

    def add(self, symbol: str) -> None:
        """Add a symbol to the suggestion list. Most recent first, no duplicates."""
        upper = symbol.upper()
        if upper in self.symbols:
            self.symbols.remove(upper)
        self.symbols.insert(0, upper)

    def get_suggestion(self, _buffer: object, document: Document) -> Suggestion | None:
        """Return suggestion if text prefix-matches a known symbol."""
        text = document.text.strip()
        if not text or text.startswith("/"):
            return None
        upper_text = text.upper()
        for sym in self.symbols:
            if sym.startswith(upper_text) and len(sym) > len(upper_text):
                return Suggestion(sym[len(upper_text) :])
        return None


class QuantKitCompleter(Completer):
    """Three-layer completer: commands, parameters, nothing for plain text."""

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        del complete_event

        text = document.text_before_cursor.lstrip()

        if not text.startswith("/"):
            return

        parts = text.split(None, 1)
        cmd_part = parts[0]

        if len(parts) == 1 and not text.endswith(" "):
            prefix = cmd_part[1:]
            cfg = load_config()
            persona_on = cfg.get("persona_mode", False)

            for name, info in COMMANDS.items():
                if info.requires_persona and not persona_on:
                    continue
                if name.startswith(prefix):
                    yield Completion(
                        name[len(prefix) :],
                        display=f"/{name}",
                        display_meta=info.description,
                    )
            return

        cmd_name = cmd_part[1:].lower()
        arg_text = parts[1].strip() if len(parts) > 1 else ""

        if cmd_name == "backtest":
            for key, desc in STRATEGIES.items():
                if key.startswith(arg_text.lower()):
                    yield Completion(
                        key[len(arg_text) :],
                        display=key,
                        display_meta=desc,
                    )
        elif cmd_name == "guru":
            cfg = load_config()
            if cfg.get("persona_mode", False):
                candidates = {"all": "全部投资人"}
                for persona in load_personas():
                    candidates[persona.name_en] = persona.name
                for key, desc in candidates.items():
                    if key.startswith(arg_text.lower()):
                        yield Completion(
                            key[len(arg_text) :],
                            display=key,
                            display_meta=desc,
                        )


def get_prompt_message(ctx: object | None, persona_mode: bool) -> FormattedText:
    """Build the prompt as FormattedText. ctx must have .symbol attribute if not None."""
    parts: list[tuple[str, str]] = []
    if ctx is not None:
        parts.append(("class:symbol", ctx.symbol))  # type: ignore[union-attr]
        parts.append(("", " "))
        if persona_mode:
            parts.append(("class:persona-icon", "🎭 "))
    parts.append(("class:chevron", "❯ "))
    return FormattedText(parts)


def create_session(symbol_suggest: SymbolAutoSuggest) -> PromptSession:
    """Create a configured PromptSession with completer, auto-suggest, and styles."""
    return PromptSession(
        completer=QuantKitCompleter(),
        auto_suggest=symbol_suggest,
        style=PROMPT_STYLE,
        complete_while_typing=True,
    )

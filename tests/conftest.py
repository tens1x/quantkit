"""Test configuration and prompt_toolkit fallback stubs for offline runs."""

from __future__ import annotations

import sys
import types


def _install_prompt_toolkit_stub() -> None:
    prompt_toolkit = types.ModuleType("prompt_toolkit")
    auto_suggest = types.ModuleType("prompt_toolkit.auto_suggest")
    completion = types.ModuleType("prompt_toolkit.completion")
    document = types.ModuleType("prompt_toolkit.document")
    formatted_text = types.ModuleType("prompt_toolkit.formatted_text")
    styles = types.ModuleType("prompt_toolkit.styles")

    class PromptSession:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

        def prompt(self, _message: object) -> str:
            raise EOFError

    class AutoSuggest:
        def get_suggestion(self, _buffer: object, _document: object) -> object | None:
            return None

    class Suggestion:
        def __init__(self, text: str) -> None:
            self.text = text

    class Document:
        def __init__(self, text: str = "", cursor_position: int | None = None) -> None:
            self.text = text
            self.cursor_position = len(text) if cursor_position is None else cursor_position

        @property
        def text_before_cursor(self) -> str:
            return self.text[: self.cursor_position]

    class CompleteEvent:
        pass

    class Completion:
        def __init__(
            self,
            text: str,
            display: str | None = None,
            display_meta: str | None = None,
        ) -> None:
            self.text = text
            self.display = display
            self.display_meta = display_meta

    class Completer:
        def get_completions(self, _document: object, _event: object) -> list[Completion]:
            return []

    class FormattedText(list[tuple[str, str]]):
        pass

    class Style(dict[str, str]):
        @classmethod
        def from_dict(cls, style_map: dict[str, str]) -> Style:
            return cls(style_map)

    prompt_toolkit.PromptSession = PromptSession
    auto_suggest.AutoSuggest = AutoSuggest
    auto_suggest.Suggestion = Suggestion
    completion.CompleteEvent = CompleteEvent
    completion.Completion = Completion
    completion.Completer = Completer
    document.Document = Document
    formatted_text.FormattedText = FormattedText
    styles.Style = Style

    sys.modules["prompt_toolkit"] = prompt_toolkit
    sys.modules["prompt_toolkit.auto_suggest"] = auto_suggest
    sys.modules["prompt_toolkit.completion"] = completion
    sys.modules["prompt_toolkit.document"] = document
    sys.modules["prompt_toolkit.formatted_text"] = formatted_text
    sys.modules["prompt_toolkit.styles"] = styles


try:
    import prompt_toolkit  # noqa: F401
except ImportError:
    _install_prompt_toolkit_stub()

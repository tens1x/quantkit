"""Tests for prompt_toolkit integration layer."""

from unittest.mock import patch

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from quantkit.prompt import (
    QuantKitCompleter,
    SymbolAutoSuggest,
    create_session,
    get_prompt_message,
)


def _get_completions(completer, text, cursor_pos=None):
    """Helper: get completion list from a completer for given text."""
    if cursor_pos is None:
        cursor_pos = len(text)
    doc = Document(text, cursor_pos)
    event = CompleteEvent()
    return list(completer.get_completions(doc, event))


class TestSymbolAutoSuggest:
    def test_no_suggestion_when_empty(self):
        suggest = SymbolAutoSuggest()
        doc = Document("AA")
        result = suggest.get_suggestion(None, doc)
        assert result is None

    def test_suggests_matching_symbol(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        doc = Document("AA")
        result = suggest.get_suggestion(None, doc)
        assert result is not None
        assert result.text == "PL"

    def test_no_suggestion_when_no_prefix_match(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        doc = Document("GO")
        result = suggest.get_suggestion(None, doc)
        assert result is None

    def test_dedup_most_recent_first(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        suggest.add("AMZN")
        suggest.add("AAPL")
        assert suggest.symbols == ["AAPL", "AMZN"]

    def test_no_suggestion_for_slash_input(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        doc = Document("/f")
        result = suggest.get_suggestion(None, doc)
        assert result is None

    def test_case_insensitive_match(self):
        suggest = SymbolAutoSuggest()
        suggest.add("AAPL")
        doc = Document("aa")
        result = suggest.get_suggestion(None, doc)
        assert result is not None
        assert result.text == "PL"


class TestQuantKitCompleter:
    def test_slash_shows_commands(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "/")
        texts = [completion.text for completion in completions]
        assert "factor" in texts
        assert "backtest" in texts
        assert "exit" in texts

    def test_slash_partial_filters(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "/fa")
        texts = [completion.text for completion in completions]
        assert "ctor" in texts
        assert len(texts) == 1

    def test_guru_hidden_when_persona_off(self):
        with patch("quantkit.prompt.load_config", return_value={"persona_mode": False}):
            completer = QuantKitCompleter()
            completions = _get_completions(completer, "/")
            texts = [completion.text for completion in completions]
            assert "guru" not in texts

    def test_guru_shown_when_persona_on(self):
        with patch("quantkit.prompt.load_config", return_value={"persona_mode": True}):
            completer = QuantKitCompleter()
            completions = _get_completions(completer, "/")
            texts = [completion.text for completion in completions]
            assert "guru" in texts

    def test_backtest_param_completion(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "/backtest ")
        texts = [completion.text for completion in completions]
        assert "ma" in texts
        assert "dca" in texts

    def test_guru_param_completion(self):
        from quantkit.persona.engine import Persona, Rule

        persona = Persona(
            name="Test",
            name_en="testguru",
            philosophy="test",
            rules=[Rule(factor="pe", op="<", threshold=20, weight=1, hit="g", miss="b")],
            buy_threshold=0.7,
            watch_threshold=0.4,
        )
        with patch("quantkit.prompt.load_config", return_value={"persona_mode": True}):
            with patch("quantkit.prompt.load_personas", return_value=[persona]):
                completer = QuantKitCompleter()
                completions = _get_completions(completer, "/guru ")
                texts = [completion.text for completion in completions]
                assert "testguru" in texts
                assert "all" in texts

    def test_no_completion_for_plain_text(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "AAPL")
        assert completions == []

    def test_no_completion_for_empty(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "")
        assert completions == []

    def test_completions_have_display_meta(self):
        completer = QuantKitCompleter()
        completions = _get_completions(completer, "/fac")
        assert len(completions) == 1
        assert completions[0].display_meta is not None


class TestGetPromptMessage:
    def test_no_context(self):
        result = get_prompt_message(ctx=None, persona_mode=False)
        text = "".join(text_part for _, text_part in result)
        assert "❯" in text
        assert "AAPL" not in text

    def test_with_context(self):
        from unittest.mock import MagicMock

        ctx = MagicMock()
        ctx.symbol = "AAPL"
        result = get_prompt_message(ctx=ctx, persona_mode=False)
        text = "".join(text_part for _, text_part in result)
        assert "AAPL" in text
        assert "❯" in text
        assert "🎭" not in text

    def test_with_persona_mode(self):
        from unittest.mock import MagicMock

        ctx = MagicMock()
        ctx.symbol = "AAPL"
        result = get_prompt_message(ctx=ctx, persona_mode=True)
        text = "".join(text_part for _, text_part in result)
        assert "AAPL" in text
        assert "🎭" in text
        assert "❯" in text


class TestCreateSession:
    def test_returns_prompt_session(self):
        from prompt_toolkit import PromptSession

        suggest = SymbolAutoSuggest()
        session = create_session(suggest)
        assert isinstance(session, PromptSession)

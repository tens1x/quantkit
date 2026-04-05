"""Tests for CLI main loop routing logic."""

from unittest.mock import MagicMock

from quantkit.commands import route


class TestRouting:
    def test_exit_returns_exit(self):
        result = route("/exit", ctx=None)
        assert result == "exit"

    def test_unknown_command(self, capsys):
        result = route("/foobar", ctx=None)
        assert result is None

    def test_factor_without_context(self, capsys):
        result = route("/factor", ctx=None)
        assert result is None

    def test_help_without_context(self):
        result = route("/help", ctx=None)
        assert result is None

    def test_guru_without_persona_mode(self, monkeypatch):
        """Guru should warn when persona_mode is off, even with valid context."""
        monkeypatch.setattr(
            "quantkit.commands.load_config",
            lambda: {"persona_mode": False},
        )
        ctx = MagicMock()
        ctx.symbol = "AAPL"
        result = route("/guru buffett", ctx)
        assert result is None

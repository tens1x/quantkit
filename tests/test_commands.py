"""Tests for command router."""

from quantkit.commands import COMMANDS, parse_command


class TestParseCommand:
    def test_simple_command(self):
        cmd, args = parse_command("/factor")
        assert cmd == "factor"
        assert args == []

    def test_command_with_args(self):
        cmd, args = parse_command("/backtest ma")
        assert cmd == "backtest"
        assert args == ["ma"]

    def test_command_case_insensitive(self):
        cmd, args = parse_command("/Factor")
        assert cmd == "factor"
        assert args == []

    def test_guru_with_name(self):
        cmd, args = parse_command("/guru buffett")
        assert cmd == "guru"
        assert args == ["buffett"]

    def test_guru_all(self):
        cmd, args = parse_command("/guru all")
        assert cmd == "guru"
        assert args == ["all"]

    def test_command_with_extra_spaces(self):
        cmd, args = parse_command("/backtest   ma  ")
        assert cmd == "backtest"
        assert args == ["ma"]

    def test_empty_after_slash(self):
        cmd, args = parse_command("/")
        assert cmd == ""
        assert args == []


class TestCommandRegistry:
    def test_known_commands_registered(self):
        expected = {
            "factor",
            "backtest",
            "risk",
            "guru",
            "portfolio",
            "settings",
            "help",
            "exit",
        }
        assert expected.issubset(set(COMMANDS.keys()))

    def test_commands_have_requires_context(self):
        assert COMMANDS["factor"].requires_context is True
        assert COMMANDS["portfolio"].requires_context is False
        assert COMMANDS["help"].requires_context is False
        assert COMMANDS["guru"].requires_context is True

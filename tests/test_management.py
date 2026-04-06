"""Tests for management commands."""

from quantkit.commands.management import _ask_int_with_min, _mask_token


def test_ask_int_with_min_retries_until_value_is_valid(monkeypatch):
    answers = iter([-1, 5000])
    printed: list[str] = []

    monkeypatch.setattr(
        "quantkit.commands.management.IntPrompt.ask",
        lambda *args, **kwargs: next(answers),
    )
    monkeypatch.setattr("quantkit.commands.management.console.print", printed.append)

    value = _ask_int_with_min("Default Capital", default=100_000, min_value=1000)

    assert value == 5000
    assert printed == ["[red]Default Capital 必须 >= 1000，请重试。[/red]"]


def test_ask_int_with_min_allows_zero_for_bps(monkeypatch):
    answers = iter([-5, 0])
    printed: list[str] = []

    monkeypatch.setattr(
        "quantkit.commands.management.IntPrompt.ask",
        lambda *args, **kwargs: next(answers),
    )
    monkeypatch.setattr("quantkit.commands.management.console.print", printed.append)

    value = _ask_int_with_min("Slippage (bps)", default=10, min_value=0)

    assert value == 0
    assert printed == ["[red]Slippage (bps) 必须 >= 0，请重试。[/red]"]


def test_mask_token_hides_middle_characters():
    assert _mask_token("12345678") == "12345678"
    assert _mask_token("1234567890abcdef") == "1234****cdef"

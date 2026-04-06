"""Tests for Tushare token resolution."""

import sys
from types import SimpleNamespace

from quantkit.config import load_config, save_config
from quantkit.data.tushare_src import _get_api


def test_get_api_prefers_config_token(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    monkeypatch.setenv("TUSHARE_TOKEN", "env-token")

    cfg = load_config()
    cfg["tushare_token"] = "config-token"
    save_config(cfg)

    seen: dict[str, str] = {}
    monkeypatch.setitem(
        sys.modules,
        "tushare",
        SimpleNamespace(pro_api=lambda token: seen.setdefault("token", token)),
    )

    api = _get_api()

    assert api == "config-token"
    assert seen["token"] == "config-token"


def test_get_api_falls_back_to_env_token(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    monkeypatch.setenv("TUSHARE_TOKEN", "env-token")

    seen: dict[str, str] = {}
    monkeypatch.setitem(
        sys.modules,
        "tushare",
        SimpleNamespace(pro_api=lambda token: seen.setdefault("token", token)),
    )

    api = _get_api()

    assert api == "env-token"
    assert seen["token"] == "env-token"

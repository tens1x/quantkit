"""Tests for config module."""


from quantkit.config import get_data_dir, load_config, save_config


def test_get_data_dir_creates_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    data_dir = get_data_dir()
    assert data_dir.exists()
    assert data_dir.name == ".quantkit"


def test_load_config_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    cfg = load_config()
    assert cfg["default_capital"] == 100_000
    assert cfg["slippage_bps"] == 10
    assert cfg["commission_bps"] == 5
    assert cfg["tushare_token"] == ""


def test_save_and_load_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("QUANTKIT_HOME", str(tmp_path / ".quantkit"))
    cfg = load_config()
    cfg["tushare_token"] = "abc123"
    save_config(cfg)
    cfg2 = load_config()
    assert cfg2["tushare_token"] == "abc123"

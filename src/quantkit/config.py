"""Configuration management. Stored at ~/.quantkit/config.json."""

import json
import os
from pathlib import Path

DEFAULTS = {
    "tushare_token": "",
    "default_capital": 100_000,
    "slippage_bps": 10,
    "commission_bps": 5,
    "persona_mode": False,
}


def get_data_dir() -> Path:
    """Return the quantkit data directory, creating it if needed."""
    path = Path(os.environ.get("QUANTKIT_HOME", Path.home() / ".quantkit"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _config_path() -> Path:
    return get_data_dir() / "config.json"


def load_config() -> dict:
    """Load config from disk, falling back to defaults."""
    path = _config_path()
    cfg = dict(DEFAULTS)
    if path.exists():
        with open(path) as f:
            cfg.update(json.load(f))
    return cfg


def save_config(cfg: dict) -> None:
    path = _config_path()
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)

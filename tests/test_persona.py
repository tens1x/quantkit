"""Tests for persona engine."""

from pathlib import Path

import pytest
import yaml

from quantkit.persona.engine import Persona, Rule, evaluate, load_personas


def _write_yaml(tmp_path: Path, filename: str, content: dict) -> Path:
    p = tmp_path / filename
    p.write_text(yaml.dump(content, allow_unicode=True), encoding="utf-8")
    return p


def _sample_persona() -> Persona:
    return Persona(
        name="测试大师",
        name_en="test_master",
        philosophy="测试用",
        rules=[
            Rule(factor="pe", op="<", threshold=20, weight=3, hit="PE低", miss="PE高"),
            Rule(factor="roe", op=">", threshold=0.15, weight=3, hit="ROE强", miss="ROE弱"),
            Rule(factor="volatility", op="<", threshold=0.30, weight=1, hit="稳", miss="不稳"),
        ],
        buy_threshold=0.7,
        watch_threshold=0.4,
    )


def _make_factors(**overrides) -> dict:
    """Build a factors dict matching compute_factors() output format."""
    defaults = {
        "pe": {"value": 15.0, "rating": "green", "label": "ok"},
        "pb": {"value": 2.0, "rating": "green", "label": "ok"},
        "roe": {"value": 0.20, "rating": "green", "label": "ok"},
        "revenue_growth": {"value": 0.10, "rating": "green", "label": "ok"},
        "volatility": {"value": 0.25, "rating": "green", "label": "ok"},
        "momentum": {"value": 0.05, "rating": "green", "label": "ok"},
    }
    for key, value in overrides.items():
        if value is None:
            defaults[key]["value"] = None
        else:
            defaults[key]["value"] = value
    return defaults


class TestEvaluate:
    def test_all_hit_buy(self):
        persona = _sample_persona()
        factors = _make_factors(pe=10.0, roe=0.25, volatility=0.20)
        verdict = evaluate(persona, factors)
        assert verdict.action == "买入"
        assert verdict.score == pytest.approx(1.0)
        assert len(verdict.reasons) == 3
        assert all("✅" in reason for reason in verdict.reasons)

    def test_all_miss_avoid(self):
        persona = _sample_persona()
        factors = _make_factors(pe=30.0, roe=0.08, volatility=0.50)
        verdict = evaluate(persona, factors)
        assert verdict.action == "回避"
        assert verdict.score == pytest.approx(0.0)
        assert all("❌" in reason for reason in verdict.reasons)

    def test_partial_hit_watch(self):
        persona = _sample_persona()
        # PE hits (weight 3), ROE misses (weight 3), volatility hits (weight 1)
        # earned=4, total=7, score=0.571
        factors = _make_factors(pe=10.0, roe=0.08, volatility=0.20)
        verdict = evaluate(persona, factors)
        assert verdict.action == "观望"
        assert 0.4 <= verdict.score < 0.7

    def test_none_values_skipped(self):
        persona = _sample_persona()
        # PE=None (skip, weight 3), ROE hits (weight 3), volatility hits (weight 1)
        # earned=4, total=4, score=1.0
        factors = _make_factors(pe=None, roe=0.25, volatility=0.20)
        verdict = evaluate(persona, factors)
        assert verdict.action == "买入"
        assert verdict.score == pytest.approx(1.0)

    def test_all_none_insufficient_data(self):
        persona = _sample_persona()
        factors = _make_factors(pe=None, roe=None, volatility=None)
        verdict = evaluate(persona, factors)
        assert verdict.action == "数据不足"
        assert verdict.score == 0.0

    def test_threshold_boundary_buy(self):
        """Score exactly at buy_threshold -> 买入."""
        persona = Persona(
            name="边界",
            name_en="boundary",
            philosophy="test",
            rules=[
                Rule(factor="pe", op="<", threshold=20, weight=7, hit="ok", miss="no"),
                Rule(factor="roe", op=">", threshold=0.1, weight=3, hit="ok", miss="no"),
            ],
            buy_threshold=0.7,
            watch_threshold=0.4,
        )
        # PE hits (7), ROE misses (3) -> score=0.7 exactly
        factors = _make_factors(pe=15.0, roe=0.05)
        verdict = evaluate(persona, factors)
        assert verdict.action == "买入"

    def test_operators_le_ge(self):
        persona = Persona(
            name="OP",
            name_en="op_test",
            philosophy="test",
            rules=[
                Rule(factor="pe", op="<=", threshold=20, weight=1, hit="ok", miss="no"),
                Rule(factor="roe", op=">=", threshold=0.15, weight=1, hit="ok", miss="no"),
            ],
            buy_threshold=0.7,
            watch_threshold=0.4,
        )
        factors = _make_factors(pe=20.0, roe=0.15)
        verdict = evaluate(persona, factors)
        assert verdict.score == pytest.approx(1.0)


class TestLoadPersonas:
    def test_load_valid_yaml(self, tmp_path, monkeypatch):
        data = {
            "name": "巴菲特",
            "name_en": "buffett",
            "philosophy": "价值投资",
            "rules": [
                {
                    "factor": "pe",
                    "op": "<",
                    "threshold": 20,
                    "weight": 3,
                    "hit": "PE低",
                    "miss": "PE高",
                },
            ],
            "buy_threshold": 0.7,
            "watch_threshold": 0.4,
        }
        _write_yaml(tmp_path, "buffett.yaml", data)
        monkeypatch.setattr("quantkit.persona.engine._personas_dir", lambda: tmp_path)
        personas = load_personas()
        assert len(personas) == 1
        assert personas[0].name_en == "buffett"
        assert len(personas[0].rules) == 1

    def test_skip_invalid_yaml(self, tmp_path, monkeypatch):
        data = {
            "name_en": "bad",
            "philosophy": "x",
            "rules": [],
            "buy_threshold": 0.7,
            "watch_threshold": 0.4,
        }
        _write_yaml(tmp_path, "bad.yaml", data)
        monkeypatch.setattr("quantkit.persona.engine._personas_dir", lambda: tmp_path)
        personas = load_personas()
        assert len(personas) == 0

    def test_skip_invalid_op(self, tmp_path, monkeypatch):
        data = {
            "name": "Bad",
            "name_en": "bad",
            "philosophy": "x",
            "rules": [
                {
                    "factor": "pe",
                    "op": "!=",
                    "threshold": 20,
                    "weight": 1,
                    "hit": "x",
                    "miss": "y",
                }
            ],
            "buy_threshold": 0.7,
            "watch_threshold": 0.4,
        }
        _write_yaml(tmp_path, "bad.yaml", data)
        monkeypatch.setattr("quantkit.persona.engine._personas_dir", lambda: tmp_path)
        personas = load_personas()
        assert len(personas) == 0

    def test_skip_negative_weight(self, tmp_path, monkeypatch):
        data = {
            "name": "Bad",
            "name_en": "bad",
            "philosophy": "x",
            "rules": [
                {
                    "factor": "pe",
                    "op": "<",
                    "threshold": 20,
                    "weight": -1,
                    "hit": "x",
                    "miss": "y",
                }
            ],
            "buy_threshold": 0.7,
            "watch_threshold": 0.4,
        }
        _write_yaml(tmp_path, "bad.yaml", data)
        monkeypatch.setattr("quantkit.persona.engine._personas_dir", lambda: tmp_path)
        personas = load_personas()
        assert len(personas) == 0

    def test_empty_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr("quantkit.persona.engine._personas_dir", lambda: tmp_path)
        personas = load_personas()
        assert len(personas) == 0

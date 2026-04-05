"""Persona engine: load YAML personas and evaluate stocks against investor rules."""

from __future__ import annotations

import operator
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


VALID_FACTORS = {"pe", "pb", "roe", "revenue_growth", "volatility", "momentum"}
VALID_OPS = {"<", ">", "<=", ">="}
OP_MAP = {
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
}


@dataclass
class Rule:
    """A single evaluation rule."""

    factor: str
    op: str
    threshold: float
    weight: int
    hit: str
    miss: str


@dataclass
class Persona:
    """An investor persona with evaluation rules."""

    name: str
    name_en: str
    philosophy: str
    rules: list[Rule]
    buy_threshold: float
    watch_threshold: float


@dataclass
class Verdict:
    """Result of evaluating a stock against a persona."""

    action: str
    score: float
    reasons: list[str] = field(default_factory=list)


def _personas_dir() -> Path:
    """Return the path to the personas YAML directory."""
    return Path(__file__).parent / "personas"


def _warn_skip(path: Path, message: str) -> None:
    warnings.warn(f"Skipping persona {path.name}: {message}", stacklevel=2)


def _validate_persona_data(data: dict[str, Any]) -> str | None:
    """Validate raw YAML data. Returns error message or None if valid."""
    for key in ("name", "name_en", "philosophy"):
        if key not in data or data[key] in (None, ""):
            return f"missing required field: {key}"

    rules = data.get("rules")
    if not isinstance(rules, list) or len(rules) == 0:
        return "rules must be a non-empty list"

    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            return f"rule {index}: must be a dict"
        for key in ("factor", "op", "threshold", "weight", "hit", "miss"):
            if key not in rule:
                return f"rule {index}: missing field {key}"
            if key in ("factor", "op", "hit", "miss") and rule[key] in (None, ""):
                return f"rule {index}: {key} must be non-empty"
        if rule["factor"] not in VALID_FACTORS:
            return f"rule {index}: unknown factor '{rule['factor']}'"
        if rule["op"] not in VALID_OPS:
            return f"rule {index}: invalid op '{rule['op']}'"
        if not isinstance(rule["weight"], int) or rule["weight"] <= 0:
            return f"rule {index}: weight must be a positive integer"

    buy_threshold = data.get("buy_threshold")
    watch_threshold = data.get("watch_threshold")
    if not isinstance(buy_threshold, (int, float)) or not isinstance(
        watch_threshold, (int, float)
    ):
        return "buy_threshold and watch_threshold must be numbers"
    if not (0 <= watch_threshold <= buy_threshold <= 1):
        return (
            f"thresholds invalid: watch={watch_threshold}, buy={buy_threshold} "
            "(need 0 <= watch <= buy <= 1)"
        )

    return None


def load_personas() -> list[Persona]:
    """Load all valid YAML persona files from the personas directory."""
    directory = _personas_dir()
    if not directory.exists():
        return []

    personas: list[Persona] = []
    seen_names: set[str] = set()

    for path in sorted(directory.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            _warn_skip(path, f"failed to parse YAML ({exc})")
            continue

        if not isinstance(data, dict):
            _warn_skip(path, "top-level YAML must be a mapping")
            continue

        error = _validate_persona_data(data)
        if error:
            _warn_skip(path, error)
            continue

        name_en = str(data["name_en"])
        if name_en in seen_names:
            _warn_skip(path, f"duplicate name_en '{name_en}'")
            continue
        seen_names.add(name_en)

        rules = [
            Rule(
                factor=str(rule["factor"]),
                op=str(rule["op"]),
                threshold=float(rule["threshold"]),
                weight=int(rule["weight"]),
                hit=str(rule["hit"]),
                miss=str(rule["miss"]),
            )
            for rule in data["rules"]
        ]

        personas.append(
            Persona(
                name=str(data["name"]),
                name_en=name_en,
                philosophy=str(data["philosophy"]),
                rules=rules,
                buy_threshold=float(data["buy_threshold"]),
                watch_threshold=float(data["watch_threshold"]),
            )
        )

    return personas


def evaluate(persona: Persona, factors: dict[str, Any]) -> Verdict:
    """Evaluate factors against a persona's rules.

    factors is expected to match compute_factors() output:
    {key: {"value": ..., "rating": ..., "label": ...}}.
    """
    total_weight = 0
    earned_weight = 0
    reasons: list[str] = []

    for rule in persona.rules:
        factor_data = factors.get(rule.factor)
        if not isinstance(factor_data, dict):
            continue

        value = factor_data.get("value")
        if value is None:
            continue

        total_weight += rule.weight

        if OP_MAP[rule.op](value, rule.threshold):
            earned_weight += rule.weight
            reasons.append(f"✅ {rule.hit}")
        else:
            reasons.append(f"❌ {rule.miss}")

    if total_weight == 0:
        return Verdict(action="数据不足", score=0.0, reasons=reasons)

    score = earned_weight / total_weight
    if score >= persona.buy_threshold:
        action = "买入"
    elif score >= persona.watch_threshold:
        action = "观望"
    else:
        action = "回避"

    return Verdict(action=action, score=score, reasons=reasons)

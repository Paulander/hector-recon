"""Adaptive curriculum bookkeeping for staged KRK training."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class StagePassCriteria:
    """Thresholds used to decide whether a curriculum stage is mastered."""

    min_mate_rate: Optional[float] = None
    max_no_move_rate: Optional[float] = None
    min_improved_rate: Optional[float] = None
    min_optimal_rate: Optional[float] = None
    max_worsened_rate: Optional[float] = None
    min_avg_reward: Optional[float] = None
    min_mate_playout_rate: Optional[float] = None
    max_draw_rate: Optional[float] = None
    max_max_plies_rate: Optional[float] = None


@dataclass(frozen=True)
class AdaptiveStageSpec:
    """Decision spec for one adaptive curriculum stage."""

    stage_index: int
    label: str
    source_stage_names: tuple[str, ...] = ()
    target_label: Optional[str] = None
    criteria: StagePassCriteria = field(default_factory=StagePassCriteria)


@dataclass
class StageEvalResult:
    """Normalized result for one stage evaluation."""

    stage_label: str
    cycle: int
    metrics: Dict[str, Any]
    passed: bool
    failure_reasons: List[str]
    score: float


def _rate(metrics: Dict[str, Any], numerator: str, denominator: str = "total") -> float:
    total = float(metrics.get(denominator, 0) or 0)
    if total <= 0:
        return 0.0
    return float(metrics.get(numerator, 0) or 0) / total


def _playout_rate(metrics: Dict[str, Any], key: str) -> float:
    playouts = metrics.get("playouts", {}) or {}
    total = sum(int(v) for v in playouts.values())
    if total <= 0:
        return 0.0
    return float(playouts.get(key, 0) or 0) / total


def stage_score(metrics: Dict[str, Any]) -> float:
    """Return a monotonic scalar for checkpoint selection."""
    score = 0.0
    score += _rate(metrics, "mate_found") * 3.0
    score += _rate(metrics, "improved") * 2.0
    score += _rate(metrics, "optimal") * 1.5
    score += _playout_rate(metrics, "mate") * 2.0
    score -= _rate(metrics, "worsened") * 2.0
    score -= _rate(metrics, "no_move") * 2.0
    score -= _playout_rate(metrics, "draw") * 2.0
    score -= _playout_rate(metrics, "max_plies") * 1.0
    score += float(metrics.get("avg_reward", 0.0) or 0.0)
    return float(score)


def evaluate_pass_criteria(metrics: Dict[str, Any], criteria: StagePassCriteria) -> tuple[bool, List[str]]:
    """Evaluate metrics against criteria and return pass/failure reasons."""
    reasons: List[str] = []

    checks = [
        ("mate_rate", criteria.min_mate_rate, _rate(metrics, "mate_found"), ">="),
        ("no_move_rate", criteria.max_no_move_rate, _rate(metrics, "no_move"), "<="),
        ("improved_rate", criteria.min_improved_rate, _rate(metrics, "improved"), ">="),
        ("optimal_rate", criteria.min_optimal_rate, _rate(metrics, "optimal"), ">="),
        ("worsened_rate", criteria.max_worsened_rate, _rate(metrics, "worsened"), "<="),
        ("avg_reward", criteria.min_avg_reward, float(metrics.get("avg_reward", 0.0) or 0.0), ">="),
        ("mate_playout_rate", criteria.min_mate_playout_rate, _playout_rate(metrics, "mate"), ">="),
        ("draw_rate", criteria.max_draw_rate, _playout_rate(metrics, "draw"), "<="),
        ("max_plies_rate", criteria.max_max_plies_rate, _playout_rate(metrics, "max_plies"), "<="),
    ]
    for name, threshold, value, op in checks:
        if threshold is None:
            continue
        if op == ">=" and value < threshold:
            reasons.append(f"{name}={value:.3f} < {threshold:.3f}")
        elif op == "<=" and value > threshold:
            reasons.append(f"{name}={value:.3f} > {threshold:.3f}")

    one_ply_ok = (
        criteria.min_improved_rate is not None
        and _rate(metrics, "improved") >= criteria.min_improved_rate
        and (criteria.max_worsened_rate is None or _rate(metrics, "worsened") <= criteria.max_worsened_rate)
        and (criteria.min_avg_reward is None or float(metrics.get("avg_reward", 0.0) or 0.0) >= criteria.min_avg_reward)
    )
    playout_failed = any(
        reason.startswith(("mate_playout_rate", "draw_rate", "max_plies_rate"))
        for reason in reasons
    )
    if one_ply_ok and playout_failed:
        reasons.append("handoff_or_conversion")

    return not reasons, reasons


def make_eval_result(
    stage_label: str,
    cycle: int,
    metrics: Dict[str, Any],
    criteria: StagePassCriteria,
) -> StageEvalResult:
    passed, reasons = evaluate_pass_criteria(metrics, criteria)
    return StageEvalResult(
        stage_label=stage_label,
        cycle=int(cycle),
        metrics=metrics,
        passed=passed,
        failure_reasons=reasons,
        score=stage_score(metrics),
    )


def record_curriculum_event(history_path: Path, event: Dict[str, Any]) -> None:
    """Append an event to a JSON history file."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    if history_path.exists():
        payload = json.loads(history_path.read_text(encoding="utf-8"))
    else:
        payload = {"events": []}
    serializable = {}
    for key, value in event.items():
        if isinstance(value, StageEvalResult):
            serializable[key] = asdict(value)
        else:
            serializable[key] = value
    payload.setdefault("events", []).append(serializable)
    history_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


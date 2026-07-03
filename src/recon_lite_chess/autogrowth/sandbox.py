"""Sandbox execution for one mined KRK autogrowth candidate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any, Iterable, Literal

import chess

from .evaluate import (
    ArmMetrics,
    choose_black_reply,
    choose_white_baseline_move,
    classify_terminal_outcome,
    evaluate_arm,
    _position_repetition_key,
)
from .features import extract_diagnostic_features, validate_learner_record
from .positions import KRKPositionSet, generate_position_sets


SandboxArmName = Literal["autogrowth_sandbox"]


@dataclass(frozen=True)
class SandboxConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    horizons: tuple[int, ...] = (40, 80)
    candidate_path: str = "reports/autogrowth/krk_autogrowth_m4_candidates.json"
    activation_max_distance: float = 1.5


@dataclass(frozen=True)
class SandboxMetrics:
    arm: str
    horizon: int
    total: int
    mates: int
    horizon_no_mate: int
    stalemates: int
    rook_losses: int
    draws: int
    draw_reasons: dict[str, int]
    illegal_moves: int
    other_failures: int
    candidate_terminal_activations: int
    candidate_action_matches: int
    candidate_move_count: int
    candidate_changed_move_count: int
    candidate_activated_position_count: int
    candidate_behavior_changed_position_count: int
    candidate_activation_rate: float
    candidate_behavior_change_rate: float
    after_condition_match_count: int
    after_condition_match_rate: float
    positive_credit_count: int
    negative_credit_count: int
    m3_update_count: int
    m3_fast_weight_delta: float
    repetition_events: int
    repeated_white_action_events: int

    @property
    def conversion_rate(self) -> float:
        return 0.0 if self.total == 0 else self.mates / self.total

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["conversion_rate"] = self.conversion_rate
        return payload


@dataclass(frozen=True)
class SandboxResult:
    config: SandboxConfig
    positions: KRKPositionSet
    candidate: dict[str, Any]
    baseline_metrics: dict[str, ArmMetrics]
    sandbox_metrics: dict[str, SandboxMetrics]
    paired_deltas: dict[str, dict[str, int]]
    safety: dict[str, dict[str, int]]
    learning_decisions: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.candidate)
        return {
            "schema_version": "krk_autogrowth_m5_sandbox.v0",
            "config": {
                **asdict(self.config),
                "horizons": list(self.config.horizons),
            },
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "candidate": {
                **self.candidate,
                "status": "m5_spawned_sandbox_only",
                "behavior_change_applied": True,
                "candidate_active_in_runtime": False,
                "candidate_active_in_sandbox": True,
                "recon_topology_plan": {
                    **self.candidate["recon_topology_plan"],
                    "spawned_now": True,
                },
            },
            "arms": {
                "baseline": {
                    horizon: metrics.to_dict()
                    for horizon, metrics in self.baseline_metrics.items()
                },
                "autogrowth_sandbox": {
                    horizon: metrics.to_dict()
                    for horizon, metrics in self.sandbox_metrics.items()
                },
            },
            "paired_deltas": self.paired_deltas,
            "safety": self.safety,
            "learning_decisions": self.learning_decisions,
            "decision": {
                "status": _overall_status(self.learning_decisions),
                "candidate_may_affect_sandbox_behavior": True,
                "candidate_promoted": any(
                    item["decision"] == "promote" for item in self.learning_decisions.values()
                ),
                "candidate_nodes_spawned": 1,
                "candidate_nodes_promoted": 1
                if any(item["decision"] == "promote" for item in self.learning_decisions.values())
                else 0,
                "deleted_candidate_count": 0
                if any(item["decision"] == "promote" for item in self.learning_decisions.values())
                else 1,
                "m3_update_count": sum(
                    int(metrics.m3_update_count) for metrics in self.sandbox_metrics.values()
                ),
                "m4_event_count": sum(
                    int(item["m4_consolidation_event_count"]) for item in self.learning_decisions.values()
                ),
                "runtime_tablebase_or_dtm_move_source": False,
                "direct_move_override": False,
            },
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def load_selected_candidate(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    for candidate in payload["candidates"]:
        if candidate.get("selected_for_m5"):
            validate_learner_record(candidate)
            return candidate
    if not payload["candidates"]:
        raise ValueError("candidate artifact has no candidates")
    candidate = payload["candidates"][0]
    validate_learner_record(candidate)
    return candidate


def evaluate_candidate_sandbox(
    *,
    config: SandboxConfig,
    positions: KRKPositionSet | None = None,
    candidate: dict[str, Any] | None = None,
) -> SandboxResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    candidate = candidate or load_selected_candidate(config.candidate_path)
    validate_learner_record(candidate)

    baseline_metrics: dict[str, ArmMetrics] = {}
    sandbox_metrics: dict[str, SandboxMetrics] = {}
    paired_deltas: dict[str, dict[str, int]] = {}
    safety: dict[str, dict[str, int]] = {}
    learning_decisions: dict[str, dict[str, Any]] = {}
    heldout = list(positions.heldout)

    for horizon in config.horizons:
        baseline_metric, baseline_outcomes = evaluate_arm(heldout, arm="baseline", horizon=horizon)
        sandbox_metric, sandbox_outcomes = evaluate_sandbox_arm(
            heldout,
            candidate=candidate,
            horizon=horizon,
            activation_max_distance=config.activation_max_distance,
        )
        horizon_key = str(horizon)
        baseline_metrics[horizon_key] = baseline_metric
        sandbox_metrics[horizon_key] = sandbox_metric
        paired_deltas[horizon_key] = _paired_delta(baseline_outcomes, sandbox_outcomes)
        safety[horizon_key] = _safety_counts(baseline_outcomes, sandbox_outcomes)
        learning_decisions[horizon_key] = _learning_decision(
            sandbox_metric=sandbox_metric,
            paired_delta=paired_deltas[horizon_key],
            safety=safety[horizon_key],
        )

    return SandboxResult(
        config=config,
        positions=positions,
        candidate=candidate,
        baseline_metrics=baseline_metrics,
        sandbox_metrics=sandbox_metrics,
        paired_deltas=paired_deltas,
        safety=safety,
        learning_decisions=learning_decisions,
    )


def evaluate_sandbox_arm(
    fens: Iterable[str],
    *,
    candidate: dict[str, Any],
    horizon: int,
    activation_max_distance: float,
) -> tuple[SandboxMetrics, list[dict[str, Any]]]:
    outcomes: list[dict[str, Any]] = []
    counts = {
        "mate": 0,
        "horizon_no_mate": 0,
        "stalemate": 0,
        "rook_loss": 0,
        "illegal_move": 0,
        "other_failure": 0,
    }
    draw_reasons: dict[str, int] = {}
    totals = {
        "candidate_terminal_activations": 0,
        "candidate_action_matches": 0,
        "candidate_move_count": 0,
        "candidate_changed_move_count": 0,
        "candidate_activated_position_count": 0,
        "candidate_behavior_changed_position_count": 0,
        "after_condition_match_count": 0,
        "positive_credit_count": 0,
        "negative_credit_count": 0,
        "m3_update_count": 0,
        "m3_fast_weight_delta_scaled": 0,
        "repetition_events": 0,
        "repeated_white_action_events": 0,
    }

    for fen in fens:
        result = _sandbox_playout(
            fen,
            candidate=candidate,
            horizon=horizon,
            activation_max_distance=activation_max_distance,
        )
        outcome = str(result["outcome"])
        if outcome.startswith("draw_"):
            draw_reasons[outcome] = draw_reasons.get(outcome, 0) + 1
        else:
            counts[outcome] = counts.get(outcome, 0) + 1
        for key in totals:
            totals[key] += int(result[key])
        outcomes.append({"fen": fen, **result})

    total = len(outcomes)
    candidate_activation_rate = (
        0.0 if total == 0 else totals["candidate_activated_position_count"] / total
    )
    candidate_behavior_change_rate = (
        0.0 if total == 0 else totals["candidate_behavior_changed_position_count"] / total
    )
    after_condition_match_rate = (
        0.0 if totals["candidate_move_count"] == 0 else totals["after_condition_match_count"] / totals["candidate_move_count"]
    )
    metrics = SandboxMetrics(
        arm="autogrowth_sandbox",
        horizon=int(horizon),
        total=total,
        mates=counts["mate"],
        horizon_no_mate=counts["horizon_no_mate"],
        stalemates=counts["stalemate"],
        rook_losses=counts["rook_loss"],
        draws=sum(draw_reasons.values()),
        draw_reasons=dict(sorted(draw_reasons.items())),
        illegal_moves=counts["illegal_move"],
        other_failures=counts["other_failure"],
        candidate_terminal_activations=totals["candidate_terminal_activations"],
        candidate_action_matches=totals["candidate_action_matches"],
        candidate_move_count=totals["candidate_move_count"],
        candidate_changed_move_count=totals["candidate_changed_move_count"],
        candidate_activated_position_count=totals["candidate_activated_position_count"],
        candidate_behavior_changed_position_count=totals["candidate_behavior_changed_position_count"],
        candidate_activation_rate=candidate_activation_rate,
        candidate_behavior_change_rate=candidate_behavior_change_rate,
        after_condition_match_count=totals["after_condition_match_count"],
        after_condition_match_rate=after_condition_match_rate,
        positive_credit_count=totals["positive_credit_count"],
        negative_credit_count=totals["negative_credit_count"],
        m3_update_count=totals["m3_update_count"],
        m3_fast_weight_delta=totals["m3_fast_weight_delta_scaled"] / 1000.0,
        repetition_events=totals["repetition_events"],
        repeated_white_action_events=totals["repeated_white_action_events"],
    )
    return metrics, outcomes


def _sandbox_playout(
    fen: str,
    *,
    candidate: dict[str, Any],
    horizon: int,
    activation_max_distance: float,
) -> dict[str, Any]:
    board = chess.Board(fen)
    illegal_moves = 0
    position_counts = {_position_repetition_key(board): 1}
    white_action_counts: dict[str, int] = {}
    candidate_terminal_activations = 0
    candidate_action_matches = 0
    candidate_move_count = 0
    candidate_changed_move_count = 0
    after_condition_match_count = 0
    positive_credit_count = 0
    negative_credit_count = 0
    m3_update_count = 0
    m3_fast_weight_delta = 0.0
    repetition_events = 0
    repeated_white_action_events = 0
    activated_position = False
    behavior_changed_position = False

    for ply in range(int(horizon)):
        terminal_outcome = classify_terminal_outcome(board)
        if terminal_outcome is not None:
            return _sandbox_result(
                outcome=terminal_outcome,
                plies=ply,
                illegal_moves=illegal_moves,
                candidate_terminal_activations=candidate_terminal_activations,
                candidate_action_matches=candidate_action_matches,
                candidate_move_count=candidate_move_count,
                candidate_changed_move_count=candidate_changed_move_count,
                after_condition_match_count=after_condition_match_count,
                positive_credit_count=positive_credit_count,
                negative_credit_count=negative_credit_count,
                m3_update_count=m3_update_count,
                m3_fast_weight_delta=m3_fast_weight_delta,
                repetition_events=repetition_events,
                repeated_white_action_events=repeated_white_action_events,
                activated_position=activated_position,
                behavior_changed_position=behavior_changed_position,
            )

        baseline_move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        before = board.copy(stack=False)
        if baseline_move is None or baseline_move not in board.legal_moves:
            illegal_moves += 1
            return _sandbox_result(
                outcome="illegal_move",
                plies=ply,
                illegal_moves=illegal_moves,
                candidate_terminal_activations=candidate_terminal_activations,
                candidate_action_matches=candidate_action_matches,
                candidate_move_count=candidate_move_count,
                candidate_changed_move_count=candidate_changed_move_count,
                after_condition_match_count=after_condition_match_count,
                positive_credit_count=positive_credit_count,
                negative_credit_count=negative_credit_count,
                m3_update_count=m3_update_count,
                m3_fast_weight_delta=m3_fast_weight_delta,
                repetition_events=repetition_events,
                repeated_white_action_events=repeated_white_action_events,
                activated_position=activated_position,
                behavior_changed_position=behavior_changed_position,
            )

        move = baseline_move
        if board.turn == chess.WHITE:
            candidate_decision = _candidate_decision(
                board,
                candidate=candidate,
                activation_max_distance=activation_max_distance,
            )
            if candidate_decision["terminal_activated"]:
                candidate_terminal_activations += 1
                activated_position = True
            if candidate_decision["action_matched"]:
                candidate_action_matches += 1
                move = candidate_decision["move"]
                candidate_move_count += 1
                if move != baseline_move:
                    candidate_changed_move_count += 1
                    behavior_changed_position = True

        if before.turn == chess.WHITE:
            action_key = move.uci()
            if white_action_counts.get(action_key, 0) > 0:
                repeated_white_action_events += 1
            white_action_counts[action_key] = white_action_counts.get(action_key, 0) + 1

        board.push(move)
        if before.turn == chess.WHITE and move != baseline_move:
            m3_update_count += 1
            if _after_condition_matches(before, board, candidate):
                after_condition_match_count += 1
                positive_credit_count += 1
                m3_fast_weight_delta += 0.05
            else:
                negative_credit_count += 1
                m3_fast_weight_delta -= 0.02

        position_key = _position_repetition_key(board)
        if position_counts.get(position_key, 0) > 0:
            repetition_events += 1
        position_counts[position_key] = position_counts.get(position_key, 0) + 1

    outcome = "mate" if board.is_checkmate() else "horizon_no_mate"
    return _sandbox_result(
        outcome=outcome,
        plies=int(horizon),
        illegal_moves=illegal_moves,
        candidate_terminal_activations=candidate_terminal_activations,
        candidate_action_matches=candidate_action_matches,
        candidate_move_count=candidate_move_count,
        candidate_changed_move_count=candidate_changed_move_count,
        after_condition_match_count=after_condition_match_count,
        positive_credit_count=positive_credit_count,
        negative_credit_count=negative_credit_count,
        m3_update_count=m3_update_count,
        m3_fast_weight_delta=m3_fast_weight_delta,
        repetition_events=repetition_events,
        repeated_white_action_events=repeated_white_action_events,
        activated_position=activated_position,
        behavior_changed_position=behavior_changed_position,
    )


def _candidate_decision(
    board: chess.Board,
    *,
    candidate: dict[str, Any],
    activation_max_distance: float,
) -> dict[str, Any]:
    if not _before_condition_matches(board, candidate, activation_max_distance):
        return {"terminal_activated": False, "action_matched": False, "move": None}
    legal_matches = [
        move
        for move in sorted(board.legal_moves, key=lambda item: item.uci())
        if _action_schema_matches(board, move, candidate["action_schema"])
    ]
    if not legal_matches:
        return {"terminal_activated": True, "action_matched": False, "move": None}
    return {
        "terminal_activated": True,
        "action_matched": True,
        "move": legal_matches[0],
    }


def _before_condition_matches(
    board: chess.Board,
    candidate: dict[str, Any],
    activation_max_distance: float,
) -> bool:
    features = extract_diagnostic_features(board)
    prototype = candidate["before_cluster"]["prototype"]
    names = candidate["before_cluster"]["feature_names"]
    distance = _normalized_distance(features, prototype, names)
    return distance <= float(activation_max_distance)


def _action_schema_matches(board: chess.Board, move: chess.Move, schema: dict[str, Any]) -> bool:
    piece = board.piece_at(move.from_square)
    if piece is None or int(piece.piece_type) != int(schema["piece_type"]):
        return False
    file_delta = chess.square_file(move.to_square) - chess.square_file(move.from_square)
    rank_delta = chess.square_rank(move.to_square) - chess.square_rank(move.from_square)
    return (
        _signed_bucket(file_delta) == int(schema["file_delta_sign"])
        and _signed_bucket(rank_delta) == int(schema["rank_delta_sign"])
        and _magnitude_bucket(file_delta) == int(schema["file_delta_magnitude"])
        and _magnitude_bucket(rank_delta) == int(schema["rank_delta_magnitude"])
        and int(board.gives_check(move)) == int(schema["gives_check"])
        and int(board.is_capture(move)) == int(schema["is_capture"])
    )


def _after_condition_matches(
    before_board: chess.Board,
    after_board: chess.Board,
    candidate: dict[str, Any],
) -> bool:
    before = extract_diagnostic_features(before_board)
    after = extract_diagnostic_features(after_board)
    deltas = {key: after[key] - before[key] for key in after.keys()}
    prototype = candidate["after_delta_cluster"]["prototype"]
    names = candidate["after_delta_cluster"]["feature_names"]
    observed_signs = {name: _signed_bucket(deltas[name]) for name in names}
    target_signs = {name: _signed_bucket(prototype[name]) for name in names}
    return observed_signs == target_signs


def _sandbox_result(
    *,
    outcome: str,
    plies: int,
    illegal_moves: int,
    candidate_terminal_activations: int,
    candidate_action_matches: int,
    candidate_move_count: int,
    candidate_changed_move_count: int,
    after_condition_match_count: int,
    positive_credit_count: int,
    negative_credit_count: int,
    m3_update_count: int,
    m3_fast_weight_delta: float,
    repetition_events: int,
    repeated_white_action_events: int,
    activated_position: bool,
    behavior_changed_position: bool,
) -> dict[str, Any]:
    return {
        "outcome": outcome,
        "plies": int(plies),
        "illegal_moves": int(illegal_moves),
        "candidate_terminal_activations": candidate_terminal_activations,
        "candidate_action_matches": candidate_action_matches,
        "candidate_move_count": candidate_move_count,
        "candidate_changed_move_count": candidate_changed_move_count,
        "candidate_activated_position_count": 1 if activated_position else 0,
        "candidate_behavior_changed_position_count": 1 if behavior_changed_position else 0,
        "after_condition_match_count": after_condition_match_count,
        "positive_credit_count": positive_credit_count,
        "negative_credit_count": negative_credit_count,
        "m3_update_count": m3_update_count,
        "m3_fast_weight_delta_scaled": int(round(m3_fast_weight_delta * 1000.0)),
        "repetition_events": repetition_events,
        "repeated_white_action_events": repeated_white_action_events,
    }


def _paired_delta(
    baseline_outcomes: list[dict[str, Any]],
    sandbox_outcomes: list[dict[str, Any]],
) -> dict[str, int]:
    sandbox_by_fen = {row["fen"]: row for row in sandbox_outcomes}
    candidate_succeeds_baseline_fails = 0
    candidate_fails_baseline_succeeds = 0
    outcome_changed_count = 0
    behavior_changed_count = 0
    for baseline in baseline_outcomes:
        sandbox = sandbox_by_fen[baseline["fen"]]
        baseline_success = baseline["outcome"] == "mate"
        sandbox_success = sandbox["outcome"] == "mate"
        if sandbox["outcome"] != baseline["outcome"]:
            outcome_changed_count += 1
        if int(sandbox["candidate_changed_move_count"]) > 0:
            behavior_changed_count += 1
        if sandbox_success and not baseline_success:
            candidate_succeeds_baseline_fails += 1
        if baseline_success and not sandbox_success:
            candidate_fails_baseline_succeeds += 1
    return {
        "candidate_succeeds_where_baseline_fails": candidate_succeeds_baseline_fails,
        "candidate_fails_where_baseline_succeeds": candidate_fails_baseline_succeeds,
        "outcome_changed_count": outcome_changed_count,
        "behavior_changed_count": behavior_changed_count,
    }


def _safety_counts(
    baseline_outcomes: list[dict[str, Any]],
    sandbox_outcomes: list[dict[str, Any]],
) -> dict[str, int]:
    sandbox_by_fen = {row["fen"]: row for row in sandbox_outcomes}
    protected_regressions = 0
    illegal_regressions = 0
    stalemate_regressions = 0
    rook_loss_regressions = 0
    for baseline in baseline_outcomes:
        sandbox = sandbox_by_fen[baseline["fen"]]
        if baseline["outcome"] == "mate" and sandbox["outcome"] != "mate":
            protected_regressions += 1
        if sandbox["outcome"] == "illegal_move" and baseline["outcome"] != "illegal_move":
            illegal_regressions += 1
        if sandbox["outcome"] == "stalemate" and baseline["outcome"] != "stalemate":
            stalemate_regressions += 1
        if sandbox["outcome"] == "rook_loss" and baseline["outcome"] != "rook_loss":
            rook_loss_regressions += 1
    return {
        "protected_baseline_regression_count": protected_regressions,
        "illegal_regression_count": illegal_regressions,
        "stalemate_regression_count": stalemate_regressions,
        "rook_loss_regression_count": rook_loss_regressions,
        "blunder_regression_count": illegal_regressions + stalemate_regressions + rook_loss_regressions,
    }


def _learning_decision(
    *,
    sandbox_metric: SandboxMetrics,
    paired_delta: dict[str, int],
    safety: dict[str, int],
) -> dict[str, Any]:
    safe = (
        safety["protected_baseline_regression_count"] == 0
        and safety["illegal_regression_count"] == 0
        and safety["stalemate_regression_count"] == 0
        and safety["rook_loss_regression_count"] == 0
    )
    acted = sandbox_metric.candidate_behavior_changed_position_count > 0
    improved = (
        paired_delta["candidate_succeeds_where_baseline_fails"] > 0
        and paired_delta["candidate_fails_where_baseline_succeeds"] == 0
    )
    m3_fired = sandbox_metric.m3_update_count > 0
    promote = safe and acted and improved and m3_fired
    reasons: list[str] = []
    if not acted:
        reasons.append("candidate_never_changed_behavior")
    if not improved:
        reasons.append("no_heldout_conversion_gain")
    if not safe:
        reasons.append("safety_regression")
    if not m3_fired:
        reasons.append("m3_no_updates")
    return {
        "decision": "promote" if promote else "quarantine",
        "candidate_score": (
            paired_delta["candidate_succeeds_where_baseline_fails"]
            - paired_delta["candidate_fails_where_baseline_succeeds"]
            - safety["blunder_regression_count"]
        ),
        "m3_update_count": sandbox_metric.m3_update_count,
        "m3_fast_weight_delta": sandbox_metric.m3_fast_weight_delta,
        "positive_credit_count": sandbox_metric.positive_credit_count,
        "negative_credit_count": sandbox_metric.negative_credit_count,
        "m4_consolidation_event_count": 1 if promote else 0,
        "delete_or_quarantine_event_count": 0 if promote else 1,
        "reasons": reasons,
    }


def _overall_status(learning_decisions: dict[str, dict[str, Any]]) -> str:
    if any(item["decision"] == "promote" for item in learning_decisions.values()):
        return "candidate_promoted_after_sandbox"
    return "candidate_quarantined_after_sandbox"


def _normalized_distance(
    features: dict[str, float],
    prototype: dict[str, float],
    names: list[str],
) -> float:
    if not names:
        return math.inf
    squared = 0.0
    for name in names:
        squared += (float(features[name]) - float(prototype[name])) ** 2
    return math.sqrt(squared / len(names))


def _signed_bucket(value: float) -> int:
    value = float(value)
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def _magnitude_bucket(value: float) -> int:
    return min(3, abs(int(round(float(value)))))

"""M9-M11 local suppressor experiment backed by StemCellTerminal state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal

from .evaluate import (
    ArmMetrics,
    choose_black_reply,
    choose_white_baseline_move,
    classify_terminal_outcome,
    evaluate_arm,
    _position_repetition_key,
)
from .features import extract_learner_features, validate_learner_record
from .positions import KRKPositionSet, generate_position_sets
from .sandbox import (
    SandboxMetrics,
    _action_schema_matches,
    _after_condition_matches,
    _before_condition_matches,
    _candidate_decision,
    _normalized_distance,
    _paired_delta,
    _safety_counts,
    _sandbox_result,
    evaluate_sandbox_arm,
    load_selected_candidate,
)


SUPPRESSOR_FEATURE_NAMES = [
    "rook_attacked_by_black",
    "white_king_to_rook_distance",
    "white_rook_to_black_king_distance",
    "white_king_to_black_king_distance",
    "black_reply_mobility",
    "black_king_nearest_edge_distance",
    "is_check",
    "is_stalemate",
]


@dataclass(frozen=True)
class LocalSuppressorConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    candidate_path: str = "reports/autogrowth/krk_autogrowth_m4_candidates.json"
    horizon: int = 40
    activation_max_distance: float = 1.5
    suppressor_max_distance: float = 0.75
    min_failure_evidence: int = 1


@dataclass(frozen=True)
class LocalSuppressorMetrics:
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
    suppressor_request_count: int
    suppressor_trigger_count: int
    suppressed_sibling_action_count: int
    suppressed_position_count: int
    suppression_trigger_rate: float
    suppression_precision: float
    false_suppression_count: int
    no_move_regression_count: int
    after_condition_match_count: int
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
class LocalSuppressorResult:
    config: LocalSuppressorConfig
    positions: KRKPositionSet
    candidate: dict[str, Any]
    suppressor_cell: StemCellTerminal
    suppressor_model: dict[str, Any]
    baseline_metrics: ArmMetrics
    candidate_metrics: SandboxMetrics
    suppressor_metrics: LocalSuppressorMetrics
    paired_deltas: dict[str, dict[str, int]]
    safety: dict[str, dict[str, int]]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.candidate)
        validate_learner_record(self.suppressor_model["learner_visible"])
        return {
            "schema_version": "krk_autogrowth_m11_local_suppressor.v0",
            "config": asdict(self.config),
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "candidate": {
                "candidate_key": self.candidate["candidate_key"],
                "suppressed_sibling_key": self.candidate["candidate_key"],
                "source_candidate_status": self.candidate.get("status"),
            },
            "suppressor": {
                "cell": self.suppressor_cell.to_dict(),
                "learner_visible": self.suppressor_model["learner_visible"],
                "diagnostics": self.suppressor_model["diagnostics"],
            },
            "arms": {
                "baseline": self.baseline_metrics.to_dict(),
                "candidate_unsuppressed": self.candidate_metrics.to_dict(),
                "local_suppressor": self.suppressor_metrics.to_dict(),
            },
            "paired_deltas": self.paired_deltas,
            "safety": self.safety,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_local_suppressor_experiment(
    *,
    config: LocalSuppressorConfig,
    positions: KRKPositionSet | None = None,
    candidate: dict[str, Any] | None = None,
) -> LocalSuppressorResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    candidate = candidate or load_selected_candidate(config.candidate_path)
    validate_learner_record(candidate)

    suppressor_cell, suppressor_model = derive_local_suppressor(
        positions.train,
        candidate=candidate,
        config=config,
    )
    heldout = list(positions.heldout)
    baseline_metrics, baseline_outcomes = evaluate_arm(
        heldout,
        arm="baseline",
        horizon=config.horizon,
    )
    candidate_metrics, candidate_outcomes = evaluate_sandbox_arm(
        heldout,
        candidate=candidate,
        horizon=config.horizon,
        activation_max_distance=config.activation_max_distance,
    )
    suppressor_metrics, suppressor_outcomes = evaluate_local_suppressor_arm(
        heldout,
        candidate=candidate,
        suppressor_model=suppressor_model,
        horizon=config.horizon,
        activation_max_distance=config.activation_max_distance,
        suppressor_max_distance=config.suppressor_max_distance,
    )
    paired_deltas = {
        "baseline_vs_candidate_unsuppressed": _paired_delta(baseline_outcomes, candidate_outcomes),
        "baseline_vs_local_suppressor": _paired_delta(baseline_outcomes, suppressor_outcomes),
        "candidate_unsuppressed_vs_local_suppressor": _paired_delta(candidate_outcomes, suppressor_outcomes),
    }
    safety = {
        "candidate_unsuppressed": _safety_counts(baseline_outcomes, candidate_outcomes),
        "local_suppressor": _safety_counts(baseline_outcomes, suppressor_outcomes),
    }
    decision = _suppressor_decision(
        suppressor_cell=suppressor_cell,
        suppressor_metrics=suppressor_metrics,
        candidate_metrics=candidate_metrics,
        safety=safety,
    )
    return LocalSuppressorResult(
        config=config,
        positions=positions,
        candidate=candidate,
        suppressor_cell=suppressor_cell,
        suppressor_model=suppressor_model,
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        suppressor_metrics=suppressor_metrics,
        paired_deltas=paired_deltas,
        safety=safety,
        decision=decision,
    )


def derive_local_suppressor(
    train_fens: Iterable[str],
    *,
    candidate: dict[str, Any],
    config: LocalSuppressorConfig,
) -> tuple[StemCellTerminal, dict[str, Any]]:
    """Mine one local suppressor from failed candidate continuations."""

    failure_records = _collect_failed_candidate_continuations(
        train_fens,
        candidate=candidate,
        horizon=config.horizon,
        activation_max_distance=config.activation_max_distance,
    )
    parent_id = _candidate_local_parent(candidate)
    cell = StemCellTerminal(f"suppress_{candidate['candidate_key']}")
    cell.state = StemCellState.TRIAL
    cell.trial_node_id = f"TRIAL_{cell.cell_id}"
    cell.trial_parent_id = parent_id
    cell.xp = cell.XP_INITIAL
    cell.mark_sibling_contrast(1.0, suppressed_sibling=candidate["candidate_key"])

    for index, _record in enumerate(failure_records):
        cell.record_candidate_request(parent_id)
        cell.record_candidate_activation(parent_id)
        cell.mark_confirmed(index)
        cell.record_candidate_intervention("negative", cycle=index)

    if len(failure_records) < config.min_failure_evidence:
        cell.candidate_stats.survival_stats.quarantine_reason = "insufficient_negative_continuation_evidence"

    learner_visible = _make_suppressor_learner_view(
        candidate=candidate,
        parent_id=parent_id,
        failure_records=failure_records,
    )
    diagnostics = {
        "failure_evidence_count": len(failure_records),
        "candidate_survival_decision": cell.candidate_survival_decision(),
        "stem_cell_state": cell.state.name,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_move_override": False,
        "suppresses_only_sibling_action": True,
    }
    model = {
        "cell_id": cell.cell_id,
        "parent_id": parent_id,
        "suppressed_sibling_key": candidate["candidate_key"],
        "feature_names": list(SUPPRESSOR_FEATURE_NAMES),
        "learner_visible": learner_visible,
        "diagnostics": diagnostics,
    }
    validate_learner_record(learner_visible)
    return cell, model


def evaluate_local_suppressor_arm(
    fens: Iterable[str],
    *,
    candidate: dict[str, Any],
    suppressor_model: dict[str, Any] | None,
    horizon: int,
    activation_max_distance: float,
    suppressor_max_distance: float,
) -> tuple[LocalSuppressorMetrics, list[dict[str, Any]]]:
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
        "suppressor_request_count": 0,
        "suppressor_trigger_count": 0,
        "suppressed_sibling_action_count": 0,
        "suppressed_position_count": 0,
        "after_condition_match_count": 0,
        "positive_credit_count": 0,
        "negative_credit_count": 0,
        "m3_update_count": 0,
        "m3_fast_weight_delta_scaled": 0,
        "repetition_events": 0,
        "repeated_white_action_events": 0,
        "no_move_regression_count": 0,
    }

    for fen in fens:
        result = _local_suppressor_playout(
            fen,
            candidate=candidate,
            suppressor_model=suppressor_model,
            horizon=horizon,
            activation_max_distance=activation_max_distance,
            suppressor_max_distance=suppressor_max_distance,
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
    trigger_rate = 0.0 if totals["suppressor_request_count"] == 0 else (
        totals["suppressor_trigger_count"] / totals["suppressor_request_count"]
    )
    precision = 0.0
    if totals["suppressor_trigger_count"] > 0:
        precision = 1.0 - (
            totals["no_move_regression_count"] / totals["suppressor_trigger_count"]
        )
    false_suppression_count = totals["no_move_regression_count"]
    metrics = LocalSuppressorMetrics(
        arm="local_suppressor",
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
        suppressor_request_count=totals["suppressor_request_count"],
        suppressor_trigger_count=totals["suppressor_trigger_count"],
        suppressed_sibling_action_count=totals["suppressed_sibling_action_count"],
        suppressed_position_count=totals["suppressed_position_count"],
        suppression_trigger_rate=trigger_rate,
        suppression_precision=precision,
        false_suppression_count=false_suppression_count,
        no_move_regression_count=totals["no_move_regression_count"],
        after_condition_match_count=totals["after_condition_match_count"],
        positive_credit_count=totals["positive_credit_count"],
        negative_credit_count=totals["negative_credit_count"],
        m3_update_count=totals["m3_update_count"],
        m3_fast_weight_delta=totals["m3_fast_weight_delta_scaled"] / 1000.0,
        repetition_events=totals["repetition_events"],
        repeated_white_action_events=totals["repeated_white_action_events"],
    )
    return metrics, outcomes


def _collect_failed_candidate_continuations(
    train_fens: Iterable[str],
    *,
    candidate: dict[str, Any],
    horizon: int,
    activation_max_distance: float,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for fen in train_fens:
        board = chess.Board(fen)
        for ply in range(int(horizon)):
            terminal = classify_terminal_outcome(board)
            if terminal is not None:
                break
            if board.turn == chess.BLACK:
                move = choose_black_reply(board)
                if move is None or move not in board.legal_moves:
                    break
                board.push(move)
                continue

            decision = _candidate_decision(
                board,
                candidate=candidate,
                activation_max_distance=activation_max_distance,
            )
            baseline_move = choose_white_baseline_move(board)
            if baseline_move is None or baseline_move not in board.legal_moves:
                break
            if not decision["terminal_activated"]:
                board.push(baseline_move)
                continue
            if not decision["action_matched"]:
                board.push(baseline_move)
                continue

            move = decision["move"]
            before = board.copy(stack=False)
            after = board.copy(stack=False)
            after.push(move)
            failure_reason = _projected_negative_reason(before, after)
            if failure_reason is not None:
                records.append(_failure_record(before, after, move, ply, failure_reason))
            board.push(move)
    validate_learner_record([record["learner_visible"] for record in records])
    return records


def _local_suppressor_playout(
    fen: str,
    *,
    candidate: dict[str, Any],
    suppressor_model: dict[str, Any] | None,
    horizon: int,
    activation_max_distance: float,
    suppressor_max_distance: float,
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
    suppressor_request_count = 0
    suppressor_trigger_count = 0
    suppressed_sibling_action_count = 0
    no_move_regression_count = 0
    activated_position = False
    behavior_changed_position = False
    suppressed_position = False

    for ply in range(int(horizon)):
        terminal_outcome = classify_terminal_outcome(board)
        if terminal_outcome is not None:
            return _local_suppressor_result(
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
                suppressor_request_count=suppressor_request_count,
                suppressor_trigger_count=suppressor_trigger_count,
                suppressed_sibling_action_count=suppressed_sibling_action_count,
                suppressed_position=suppressed_position,
                no_move_regression_count=no_move_regression_count,
            )

        baseline_move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        before = board.copy(stack=False)
        if baseline_move is None or baseline_move not in board.legal_moves:
            illegal_moves += 1
            no_move_regression_count += int(suppressed_position)
            return _local_suppressor_result(
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
                suppressor_request_count=suppressor_request_count,
                suppressor_trigger_count=suppressor_trigger_count,
                suppressed_sibling_action_count=suppressed_sibling_action_count,
                suppressed_position=suppressed_position,
                no_move_regression_count=no_move_regression_count,
            )

        move = baseline_move
        suppressed = False
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
                candidate_move = candidate_decision["move"]
                suppressor_request_count += 1
                if suppressor_model is not None and suppressor_confirms(
                    board,
                    candidate_move,
                    suppressor_model=suppressor_model,
                    max_distance=suppressor_max_distance,
                ):
                    suppressor_trigger_count += 1
                    suppressed_sibling_action_count += 1
                    suppressed_position = True
                    suppressed = True
                    move = baseline_move
                    m3_update_count += 1
                    negative_credit_count += 1
                    m3_fast_weight_delta += 0.03
                else:
                    move = candidate_move
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
        elif suppressed:
            projected = before.copy(stack=False)
            projected.push(candidate_decision["move"])
            if _projected_negative_reason(before, projected) is None:
                no_move_regression_count += 1

        position_key = _position_repetition_key(board)
        if position_counts.get(position_key, 0) > 0:
            repetition_events += 1
        position_counts[position_key] = position_counts.get(position_key, 0) + 1

    outcome = "mate" if board.is_checkmate() else "horizon_no_mate"
    return _local_suppressor_result(
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
        suppressor_request_count=suppressor_request_count,
        suppressor_trigger_count=suppressor_trigger_count,
        suppressed_sibling_action_count=suppressed_sibling_action_count,
        suppressed_position=suppressed_position,
        no_move_regression_count=no_move_regression_count,
    )


def suppressor_confirms(
    board: chess.Board,
    candidate_move: chess.Move,
    *,
    suppressor_model: dict[str, Any],
    max_distance: float,
) -> bool:
    """Return local inhibit/no-inhibit only; this function never chooses a move."""

    if candidate_move not in board.legal_moves:
        return False
    learner_visible = suppressor_model["learner_visible"]
    if not _action_schema_matches(board, candidate_move, learner_visible["suppressed_action_schema"]):
        return False
    after = board.copy(stack=False)
    after.push(candidate_move)
    after_features = extract_learner_features(after)
    distance = _normalized_distance(
        after_features,
        learner_visible["projected_after_prototype"],
        learner_visible["feature_names"],
    )
    return distance <= float(max_distance)


def _failure_record(
    before: chess.Board,
    after: chess.Board,
    move: chess.Move,
    ply: int,
    reason: str,
) -> dict[str, Any]:
    learner_visible = {
        "ply": int(ply),
        "before_features": {
            name: extract_learner_features(before)[name]
            for name in SUPPRESSOR_FEATURE_NAMES
        },
        "projected_after_features": {
            name: extract_learner_features(after)[name]
            for name in SUPPRESSOR_FEATURE_NAMES
        },
        "action": {
            "piece_type": int(before.piece_at(move.from_square).piece_type),
            "file_delta": chess.square_file(move.to_square) - chess.square_file(move.from_square),
            "rank_delta": chess.square_rank(move.to_square) - chess.square_rank(move.from_square),
            "is_capture": 1.0 if before.is_capture(move) else 0.0,
            "gives_check": 1.0 if before.gives_check(move) else 0.0,
        },
        "local_recon_view": {
            "candidate_node_type": "TERMINAL",
            "inhibited_sibling_node_type": "ACTION",
            "parent_relation_type": "SUB",
            "sibling_relation_type": "POR",
            "behavior_change": "inhibit_sibling_only",
        },
    }
    validate_learner_record(learner_visible)
    return {
        "learner_visible": learner_visible,
        "diagnostic_reason": reason,
    }


def _make_suppressor_learner_view(
    *,
    candidate: dict[str, Any],
    parent_id: str,
    failure_records: list[dict[str, Any]],
) -> dict[str, Any]:
    if failure_records:
        prototype = _mean_feature_record(
            [
                record["learner_visible"]["projected_after_features"]
                for record in failure_records
            ],
            SUPPRESSOR_FEATURE_NAMES,
        )
    else:
        prototype = {name: 0.0 for name in SUPPRESSOR_FEATURE_NAMES}
    learner_visible = {
        "node_type": "TERMINAL",
        "candidate_role": "local_suppressor",
        "parent_id": parent_id,
        "suppressed_sibling_key": candidate["candidate_key"],
        "suppressed_action_schema": candidate["action_schema"],
        "feature_names": list(SUPPRESSOR_FEATURE_NAMES),
        "projected_after_prototype": prototype,
        "relation_plan": {
            "attach_relation": "SUB",
            "inhibit_relation": "RET",
            "inhibits_only_sibling_action": True,
            "chooses_move_directly": False,
        },
    }
    validate_learner_record(learner_visible)
    return learner_visible


def _projected_negative_reason(before: chess.Board, after: chess.Board) -> str | None:
    terminal = classify_terminal_outcome(after)
    if terminal in {"rook_loss", "stalemate", "illegal_move"}:
        return terminal
    before_features = extract_learner_features(before)
    after_features = extract_learner_features(after)
    if after_features["rook_attacked_by_black"] > before_features["rook_attacked_by_black"]:
        return "rook_attacked_after_action"
    if after_features["is_stalemate"] > 0.0:
        return "stalemate_after_action"
    reply = choose_black_reply(after)
    if reply is None or reply not in after.legal_moves:
        return None
    reply_board = after.copy(stack=False)
    reply_board.push(reply)
    terminal_after_reply = classify_terminal_outcome(reply_board)
    if terminal_after_reply in {"rook_loss", "stalemate", "illegal_move"}:
        return f"black_reply_{terminal_after_reply}"
    return None


def _local_suppressor_result(
    *,
    suppressor_request_count: int,
    suppressor_trigger_count: int,
    suppressed_sibling_action_count: int,
    suppressed_position: bool,
    no_move_regression_count: int,
    **kwargs: Any,
) -> dict[str, Any]:
    payload = _sandbox_result(**kwargs)
    payload.update(
        {
            "suppressor_request_count": int(suppressor_request_count),
            "suppressor_trigger_count": int(suppressor_trigger_count),
            "suppressed_sibling_action_count": int(suppressed_sibling_action_count),
            "suppressed_position_count": 1 if suppressed_position else 0,
            "no_move_regression_count": int(no_move_regression_count),
        }
    )
    return payload


def _suppressor_decision(
    *,
    suppressor_cell: StemCellTerminal,
    suppressor_metrics: LocalSuppressorMetrics,
    candidate_metrics: SandboxMetrics,
    safety: dict[str, dict[str, int]],
) -> dict[str, Any]:
    safety_delta = {
        "rook_loss_delta": suppressor_metrics.rook_losses - candidate_metrics.rook_losses,
        "stalemate_delta": suppressor_metrics.stalemates - candidate_metrics.stalemates,
        "illegal_delta": suppressor_metrics.illegal_moves - candidate_metrics.illegal_moves,
        "horizon_no_mate_delta": suppressor_metrics.horizon_no_mate - candidate_metrics.horizon_no_mate,
    }
    no_new_blunders = (
        safety["local_suppressor"]["illegal_regression_count"] == 0
        and safety["local_suppressor"]["stalemate_regression_count"] == 0
        and safety["local_suppressor"]["rook_loss_regression_count"]
        <= safety["candidate_unsuppressed"]["rook_loss_regression_count"]
    )
    triggered = suppressor_metrics.suppressor_trigger_count > 0
    improved_safety = (
        suppressor_metrics.rook_losses <= candidate_metrics.rook_losses
        and suppressor_metrics.illegal_moves <= candidate_metrics.illegal_moves
        and suppressor_metrics.stalemates <= candidate_metrics.stalemates
    )
    pass_checkpoint = (
        suppressor_cell.candidate_survival_decision() == "suppress"
        and triggered
        and no_new_blunders
        and improved_safety
    )
    conversion_improved = suppressor_metrics.mates > candidate_metrics.mates
    status = "survived_as_local_suppressor" if pass_checkpoint else "quarantined_local_suppressor"
    return {
        "status": status,
        "passed": pass_checkpoint,
        "safety_checkpoint_passed": pass_checkpoint,
        "krk_competence_passed": conversion_improved,
        "conversion_improved_vs_candidate_unsuppressed": conversion_improved,
        "stem_cell_state": suppressor_cell.state.name,
        "candidate_survival_decision": suppressor_cell.candidate_survival_decision(),
        "suppressor_triggered": triggered,
        "safety_delta_vs_candidate_unsuppressed": safety_delta,
        "behavior_mediated_by_stem_cell_trial_structure": True,
        "suppresses_only_sibling_action": True,
        "chooses_moves_directly": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "direct_move_override": False,
        "local_suppressor_decision": {
            "decision": "survive" if pass_checkpoint else "quarantine",
            "m4_consolidation_event_count": 1 if pass_checkpoint else 0,
            "delete_or_quarantine_event_count": 0 if pass_checkpoint else 1,
            "candidate_action_promotion_not_applicable": True,
            "reasons": _suppressor_reasons(
                suppressor_cell=suppressor_cell,
                triggered=triggered,
                no_new_blunders=no_new_blunders,
                improved_safety=improved_safety,
            ),
        },
    }


def _suppressor_reasons(
    *,
    suppressor_cell: StemCellTerminal,
    triggered: bool,
    no_new_blunders: bool,
    improved_safety: bool,
) -> list[str]:
    reasons: list[str] = []
    if suppressor_cell.candidate_survival_decision() != "suppress":
        reasons.append("candidate_state_not_local_suppressor")
    if not triggered:
        reasons.append("suppressor_never_triggered")
    if not no_new_blunders:
        reasons.append("new_safety_regression")
    if not improved_safety:
        reasons.append("no_safety_improvement")
    return reasons


def _candidate_local_parent(candidate: dict[str, Any]) -> str:
    plan = candidate.get("recon_topology_plan", {})
    return str(plan.get("local_parent_id") or plan.get("parent_id") or "autogrowth_candidate_parent")


def _mean_feature_record(records: list[dict[str, float]], names: list[str]) -> dict[str, float]:
    if not records:
        return {name: 0.0 for name in names}
    return {
        name: sum(float(record[name]) for record in records) / len(records)
        for name in names
    }

"""M12 local ReCoN-style action arbitration for KRK autogrowth."""

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
from .features import validate_learner_record
from .positions import KRKPositionSet, generate_position_sets
from .sandbox import (
    SandboxMetrics,
    _action_schema_matches,
    _after_condition_matches,
    _before_condition_matches,
    _paired_delta,
    _safety_counts,
    _sandbox_result,
    evaluate_sandbox_arm,
)
from .suppressor import (
    LocalSuppressorConfig,
    derive_local_suppressor,
    suppressor_confirms,
    _candidate_local_parent,
    _projected_negative_reason,
)
from .training import load_candidate_pool


@dataclass(frozen=True)
class LocalArbitrationConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    candidate_path: str = "reports/autogrowth/krk_autogrowth_m4_candidates.json"
    candidate_count: int = 12
    horizon: int = 40
    activation_max_distance: float = 1.5
    suppressor_max_distance: float = 0.75
    eta_m3: float = 0.08


@dataclass(frozen=True)
class LocalArbitrationMetrics:
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
    local_parent_request_count: int
    action_option_count: int
    action_selected_count: int
    action_changed_move_count: int
    action_changed_position_count: int
    suppressor_trigger_count: int
    suppressed_action_option_count: int
    baseline_fallback_count: int
    no_action_position_count: int
    positive_credit_count: int
    negative_credit_count: int
    neutral_credit_count: int
    m3_update_count: int
    m3_fast_weight_delta: float
    repetition_events: int
    repeated_white_action_events: int

    @property
    def conversion_rate(self) -> float:
        return 0.0 if self.total == 0 else self.mates / self.total

    @property
    def action_selection_rate(self) -> float:
        return 0.0 if self.local_parent_request_count == 0 else (
            self.action_selected_count / self.local_parent_request_count
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["conversion_rate"] = self.conversion_rate
        payload["action_selection_rate"] = self.action_selection_rate
        return payload


@dataclass(frozen=True)
class LocalArbitrationResult:
    config: LocalArbitrationConfig
    positions: KRKPositionSet
    action_nodes: list[dict[str, Any]]
    suppressor_cell: StemCellTerminal
    suppressor_model: dict[str, Any]
    baseline_metrics: ArmMetrics
    unsuppressed_candidate_metrics: dict[str, Any]
    arbitration_metrics: LocalArbitrationMetrics
    paired_deltas: dict[str, dict[str, int]]
    safety: dict[str, dict[str, int]]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        learner_action_nodes = [node["learner_visible"] for node in self.action_nodes]
        validate_learner_record(learner_action_nodes)
        validate_learner_record(self.suppressor_model["learner_visible"])
        return {
            "schema_version": "krk_autogrowth_m12_local_arbitration.v0",
            "config": asdict(self.config),
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "local_recon_structure": {
                "parent_id": self.action_nodes[0]["parent_id"] if self.action_nodes else None,
                "parent_node_type": "SCRIPT",
                "action_sibling_count": len(self.action_nodes),
                "relation_types": ["SUB", "POR", "RET"],
                "move_choice_mediated_by_local_action_nodes": True,
                "external_move_ranking_applied": False,
                "direct_move_override": False,
            },
            "action_nodes": [
                {
                    "cell": node["cell"].to_dict(),
                    "local_weight": node["local_weight"],
                    "learner_visible": node["learner_visible"],
                    "diagnostics": node["diagnostics"],
                }
                for node in self.action_nodes
            ],
            "suppressor": {
                "cell": self.suppressor_cell.to_dict(),
                "learner_visible": self.suppressor_model["learner_visible"],
                "diagnostics": self.suppressor_model["diagnostics"],
            },
            "arms": {
                "baseline": self.baseline_metrics.to_dict(),
                "selected_candidate_unsuppressed": self.unsuppressed_candidate_metrics,
                "local_action_arbitration": self.arbitration_metrics.to_dict(),
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


def run_local_arbitration_experiment(
    *,
    config: LocalArbitrationConfig,
    positions: KRKPositionSet | None = None,
    candidates: list[dict[str, Any]] | None = None,
) -> LocalArbitrationResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    candidates = candidates or load_candidate_pool(config.candidate_path, candidate_count=config.candidate_count)
    if not candidates:
        raise ValueError("local arbitration needs at least one candidate")
    validate_learner_record(candidates)

    suppressor_cell, suppressor_model = derive_local_suppressor(
        positions.train,
        candidate=candidates[0],
        config=LocalSuppressorConfig(
            seed=config.seed,
            train_count=config.train_count,
            heldout_weakness_count=config.heldout_weakness_count,
            heldout_broader_count=config.heldout_broader_count,
            candidate_path=config.candidate_path,
            horizon=config.horizon,
            activation_max_distance=config.activation_max_distance,
            suppressor_max_distance=config.suppressor_max_distance,
        ),
    )
    action_nodes = build_local_action_nodes(
        positions.train,
        candidates=candidates,
        suppressor_model=suppressor_model,
        config=config,
    )
    heldout = list(positions.heldout)
    baseline_metrics, baseline_outcomes = evaluate_arm(
        heldout,
        arm="baseline",
        horizon=config.horizon,
    )
    selected_metrics, selected_outcomes = evaluate_sandbox_arm(
        heldout,
        candidate=candidates[0],
        horizon=config.horizon,
        activation_max_distance=config.activation_max_distance,
    )
    arbitration_metrics, arbitration_outcomes = evaluate_local_arbitration_arm(
        heldout,
        action_nodes=action_nodes,
        suppressor_model=suppressor_model,
        horizon=config.horizon,
        activation_max_distance=config.activation_max_distance,
        suppressor_max_distance=config.suppressor_max_distance,
    )
    paired_deltas = {
        "baseline_vs_selected_candidate_unsuppressed": _paired_delta(baseline_outcomes, selected_outcomes),
        "baseline_vs_local_action_arbitration": _paired_delta(baseline_outcomes, arbitration_outcomes),
        "selected_candidate_unsuppressed_vs_local_action_arbitration": _paired_delta(selected_outcomes, arbitration_outcomes),
    }
    safety = {
        "selected_candidate_unsuppressed": _safety_counts(baseline_outcomes, selected_outcomes),
        "local_action_arbitration": _safety_counts(baseline_outcomes, arbitration_outcomes),
    }
    decision = _arbitration_decision(
        baseline_metrics=baseline_metrics,
        selected_candidate_metrics=selected_metrics,
        arbitration_metrics=arbitration_metrics,
        safety=safety,
        suppressor_cell=suppressor_cell,
    )
    return LocalArbitrationResult(
        config=config,
        positions=positions,
        action_nodes=action_nodes,
        suppressor_cell=suppressor_cell,
        suppressor_model=suppressor_model,
        baseline_metrics=baseline_metrics,
        unsuppressed_candidate_metrics=selected_metrics.to_dict(),
        arbitration_metrics=arbitration_metrics,
        paired_deltas=paired_deltas,
        safety=safety,
        decision=decision,
    )


def build_local_action_nodes(
    train_fens: Iterable[str],
    *,
    candidates: list[dict[str, Any]],
    suppressor_model: dict[str, Any] | None,
    config: LocalArbitrationConfig,
) -> list[dict[str, Any]]:
    parent_id = _candidate_local_parent(candidates[0])
    nodes = [_make_action_node(candidate, parent_id=parent_id) for candidate in candidates]
    by_key = {node["candidate"]["candidate_key"]: node for node in nodes}

    for fen in train_fens:
        board = chess.Board(fen)
        for _ply in range(int(config.horizon)):
            terminal = classify_terminal_outcome(board)
            if terminal is not None:
                break
            if board.turn == chess.BLACK:
                move = choose_black_reply(board)
                if move is None or move not in board.legal_moves:
                    break
                board.push(move)
                continue

            options = _local_action_options(
                board,
                action_nodes=nodes,
                activation_max_distance=config.activation_max_distance,
            )
            if not options:
                baseline_move = choose_white_baseline_move(board)
                if baseline_move is None or baseline_move not in board.legal_moves:
                    break
                board.push(baseline_move)
                continue

            for option in options:
                node = by_key[option["candidate_key"]]
                cell: StemCellTerminal = node["cell"]
                cell.record_candidate_request(parent_id)
                cell.record_candidate_activation(parent_id)
                if _option_is_suppressed(
                    board,
                    option,
                    suppressor_model=suppressor_model,
                    max_distance=config.suppressor_max_distance,
                ):
                    node["diagnostics"]["suppressed_training_options"] += 1
                    continue
                credit = _training_credit_for_action(board, option["move"], node["candidate"])
                _apply_action_node_credit(node, credit=credit, eta_m3=config.eta_m3)

            decision = arbitrate_local_action(
                board,
                action_nodes=nodes,
                suppressor_model=suppressor_model,
                activation_max_distance=config.activation_max_distance,
                suppressor_max_distance=config.suppressor_max_distance,
            )
            move = decision["move"] or choose_white_baseline_move(board)
            if move is None or move not in board.legal_moves:
                break
            board.push(move)

    for node in nodes:
        node["cell"].candidate_stats.recompute_survival(
            xp=node["cell"].xp,
            solidify_xp=node["cell"].XP_SOLIDIFY,
        )
        node["learner_visible"]["local_weight"] = round(float(node["local_weight"]), 6)
        node["learner_visible"]["selectable_after_training"] = _action_node_is_selectable(node)
        node["diagnostics"]["selectable_after_training"] = _action_node_is_selectable(node)
        validate_learner_record(node["learner_visible"])
    return nodes


def evaluate_local_arbitration_arm(
    fens: Iterable[str],
    *,
    action_nodes: list[dict[str, Any]],
    suppressor_model: dict[str, Any] | None,
    horizon: int,
    activation_max_distance: float,
    suppressor_max_distance: float,
) -> tuple[LocalArbitrationMetrics, list[dict[str, Any]]]:
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
        "local_parent_request_count": 0,
        "action_option_count": 0,
        "action_selected_count": 0,
        "action_changed_move_count": 0,
        "action_changed_position_count": 0,
        "suppressor_trigger_count": 0,
        "suppressed_action_option_count": 0,
        "baseline_fallback_count": 0,
        "no_action_position_count": 0,
        "positive_credit_count": 0,
        "negative_credit_count": 0,
        "neutral_credit_count": 0,
        "m3_update_count": 0,
        "m3_fast_weight_delta_scaled": 0,
        "repetition_events": 0,
        "repeated_white_action_events": 0,
    }
    for fen in fens:
        result = _local_arbitration_playout(
            fen,
            action_nodes=action_nodes,
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

    metrics = LocalArbitrationMetrics(
        arm="local_action_arbitration",
        horizon=int(horizon),
        total=len(outcomes),
        mates=counts["mate"],
        horizon_no_mate=counts["horizon_no_mate"],
        stalemates=counts["stalemate"],
        rook_losses=counts["rook_loss"],
        draws=sum(draw_reasons.values()),
        draw_reasons=dict(sorted(draw_reasons.items())),
        illegal_moves=counts["illegal_move"],
        other_failures=counts["other_failure"],
        local_parent_request_count=totals["local_parent_request_count"],
        action_option_count=totals["action_option_count"],
        action_selected_count=totals["action_selected_count"],
        action_changed_move_count=totals["action_changed_move_count"],
        action_changed_position_count=totals["action_changed_position_count"],
        suppressor_trigger_count=totals["suppressor_trigger_count"],
        suppressed_action_option_count=totals["suppressed_action_option_count"],
        baseline_fallback_count=totals["baseline_fallback_count"],
        no_action_position_count=totals["no_action_position_count"],
        positive_credit_count=totals["positive_credit_count"],
        negative_credit_count=totals["negative_credit_count"],
        neutral_credit_count=totals["neutral_credit_count"],
        m3_update_count=totals["m3_update_count"],
        m3_fast_weight_delta=totals["m3_fast_weight_delta_scaled"] / 1000.0,
        repetition_events=totals["repetition_events"],
        repeated_white_action_events=totals["repeated_white_action_events"],
    )
    return metrics, outcomes


def arbitrate_local_action(
    board: chess.Board,
    *,
    action_nodes: list[dict[str, Any]],
    suppressor_model: dict[str, Any] | None,
    activation_max_distance: float,
    suppressor_max_distance: float,
) -> dict[str, Any]:
    """Choose a move only by resolving local ACTION siblings."""

    options = _local_action_options(
        board,
        action_nodes=action_nodes,
        activation_max_distance=activation_max_distance,
    )
    suppressed: list[dict[str, Any]] = []
    available: list[dict[str, Any]] = []
    for option in options:
        if _option_is_suppressed(
            board,
            option,
            suppressor_model=suppressor_model,
            max_distance=suppressor_max_distance,
        ):
            suppressed.append(option)
        else:
            available.append(option)
    if not available:
        return {
            "move": None,
            "selected_candidate_key": None,
            "selected_action_node_id": None,
            "option_count": len(options),
            "suppressed_count": len(suppressed),
            "used_external_move_source": False,
        }
    available.sort(
        key=lambda option: (
            float(option["local_weight"]),
            -int(option["rank"]),
            option["move"].uci(),
        ),
        reverse=True,
    )
    chosen = available[0]
    return {
        "move": chosen["move"],
        "selected_candidate_key": chosen["candidate_key"],
        "selected_action_node_id": chosen["action_node_id"],
        "option_count": len(options),
        "suppressed_count": len(suppressed),
        "used_external_move_source": False,
    }


def _make_action_node(candidate: dict[str, Any], *, parent_id: str) -> dict[str, Any]:
    cell = StemCellTerminal(f"action_{candidate['candidate_key']}")
    cell.state = StemCellState.TRIAL
    cell.trial_node_id = f"TRIAL_{cell.cell_id}"
    cell.trial_parent_id = parent_id
    cell.xp = cell.XP_INITIAL
    base_weight = float(candidate.get("evidence", {}).get("mean_candidate_credit", 0.0))
    learner_visible = {
        "node_type": "ACTION",
        "parent_node_type": "SCRIPT",
        "candidate_key": candidate["candidate_key"],
        "parent_id": parent_id,
        "action_schema": candidate["action_schema"],
        "relation_plan": {
            "attach_relation": "SUB",
            "sibling_order_relation": "POR",
            "can_be_inhibited_by": "RET",
            "chooses_move_directly": False,
            "emits_action_when_confirmed": True,
        },
        "local_weight": round(base_weight, 6),
    }
    validate_learner_record(learner_visible)
    return {
        "candidate": candidate,
        "candidate_key": candidate["candidate_key"],
        "rank": int(candidate.get("rank", 0)),
        "parent_id": parent_id,
        "action_node_id": f"ACTION_{candidate['candidate_key']}",
        "cell": cell,
        "local_weight": base_weight,
        "learner_visible": learner_visible,
        "diagnostics": {
            "training_options": 0,
            "suppressed_training_options": 0,
            "positive_training_credit": 0,
            "negative_training_credit": 0,
            "neutral_training_credit": 0,
            "m3_fast_weight_delta": 0.0,
        },
    }


def _local_action_options(
    board: chess.Board,
    *,
    action_nodes: list[dict[str, Any]],
    activation_max_distance: float,
) -> list[dict[str, Any]]:
    if board.turn != chess.WHITE:
        return []
    options: list[dict[str, Any]] = []
    for node in action_nodes:
        if not _action_node_is_selectable(node):
            continue
        candidate = node["candidate"]
        if not _before_condition_matches(board, candidate, activation_max_distance):
            continue
        legal_matches = [
            move
            for move in sorted(board.legal_moves, key=lambda item: item.uci())
            if _action_schema_matches(board, move, candidate["action_schema"])
        ]
        for move in legal_matches:
            options.append(
                {
                    "candidate_key": candidate["candidate_key"],
                    "action_node_id": node["action_node_id"],
                    "rank": int(node["rank"]),
                    "local_weight": float(node["local_weight"]),
                    "move": move,
                    "candidate": candidate,
                }
            )
    return options


def _action_node_is_selectable(node: dict[str, Any]) -> bool:
    credit = node["cell"].candidate_stats.credit_stats
    return int(credit.negative_intervention) == 0


def _option_is_suppressed(
    board: chess.Board,
    option: dict[str, Any],
    *,
    suppressor_model: dict[str, Any] | None,
    max_distance: float,
) -> bool:
    if suppressor_model is None:
        return False
    if option["candidate_key"] != suppressor_model["learner_visible"]["suppressed_sibling_key"]:
        return False
    return suppressor_confirms(
        board,
        option["move"],
        suppressor_model=suppressor_model,
        max_distance=max_distance,
    )


def _local_arbitration_playout(
    fen: str,
    *,
    action_nodes: list[dict[str, Any]],
    suppressor_model: dict[str, Any] | None,
    horizon: int,
    activation_max_distance: float,
    suppressor_max_distance: float,
) -> dict[str, Any]:
    board = chess.Board(fen)
    illegal_moves = 0
    position_counts = {_position_repetition_key(board): 1}
    white_action_counts: dict[str, int] = {}
    action_changed_position = False
    no_action_position = True
    totals = {
        "local_parent_request_count": 0,
        "action_option_count": 0,
        "action_selected_count": 0,
        "action_changed_move_count": 0,
        "suppressor_trigger_count": 0,
        "suppressed_action_option_count": 0,
        "baseline_fallback_count": 0,
        "positive_credit_count": 0,
        "negative_credit_count": 0,
        "neutral_credit_count": 0,
        "m3_update_count": 0,
        "m3_fast_weight_delta_scaled": 0,
        "repetition_events": 0,
        "repeated_white_action_events": 0,
    }

    for ply in range(int(horizon)):
        terminal_outcome = classify_terminal_outcome(board)
        if terminal_outcome is not None:
            return _local_arbitration_result(
                outcome=terminal_outcome,
                plies=ply,
                illegal_moves=illegal_moves,
                action_changed_position=action_changed_position,
                no_action_position=no_action_position,
                **totals,
            )
        baseline_move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        before = board.copy(stack=False)
        if baseline_move is None or baseline_move not in board.legal_moves:
            illegal_moves += 1
            return _local_arbitration_result(
                outcome="illegal_move",
                plies=ply,
                illegal_moves=illegal_moves,
                action_changed_position=action_changed_position,
                no_action_position=no_action_position,
                **totals,
            )

        move = baseline_move
        selected_candidate: dict[str, Any] | None = None
        if board.turn == chess.WHITE:
            totals["local_parent_request_count"] += 1
            decision = arbitrate_local_action(
                board,
                action_nodes=action_nodes,
                suppressor_model=suppressor_model,
                activation_max_distance=activation_max_distance,
                suppressor_max_distance=suppressor_max_distance,
            )
            totals["action_option_count"] += int(decision["option_count"])
            totals["suppressed_action_option_count"] += int(decision["suppressed_count"])
            if decision["suppressed_count"] > 0:
                totals["suppressor_trigger_count"] += int(decision["suppressed_count"])
            if decision["move"] is None:
                totals["baseline_fallback_count"] += 1
            else:
                move = decision["move"]
                no_action_position = False
                totals["action_selected_count"] += 1
                selected_candidate = _candidate_by_key(action_nodes, decision["selected_candidate_key"])
                if move != baseline_move:
                    totals["action_changed_move_count"] += 1
                    action_changed_position = True

        if before.turn == chess.WHITE:
            action_key = move.uci()
            if white_action_counts.get(action_key, 0) > 0:
                totals["repeated_white_action_events"] += 1
            white_action_counts[action_key] = white_action_counts.get(action_key, 0) + 1

        board.push(move)
        if before.turn == chess.WHITE and selected_candidate is not None:
            credit = _post_action_credit(before, board, selected_candidate)
            if credit > 0.0:
                totals["positive_credit_count"] += 1
            elif credit < 0.0:
                totals["negative_credit_count"] += 1
            else:
                totals["neutral_credit_count"] += 1
            totals["m3_update_count"] += 1
            totals["m3_fast_weight_delta_scaled"] += int(round(credit * 1000.0))

        position_key = _position_repetition_key(board)
        if position_counts.get(position_key, 0) > 0:
            totals["repetition_events"] += 1
        position_counts[position_key] = position_counts.get(position_key, 0) + 1

    outcome = "mate" if board.is_checkmate() else "horizon_no_mate"
    return _local_arbitration_result(
        outcome=outcome,
        plies=int(horizon),
        illegal_moves=illegal_moves,
        action_changed_position=action_changed_position,
        no_action_position=no_action_position,
        **totals,
    )


def _apply_action_node_credit(node: dict[str, Any], *, credit: float, eta_m3: float) -> None:
    cell: StemCellTerminal = node["cell"]
    node["diagnostics"]["training_options"] += 1
    if credit > 0.0:
        cell.record_candidate_intervention("positive")
        node["diagnostics"]["positive_training_credit"] += 1
    elif credit < 0.0:
        cell.record_candidate_intervention("negative")
        node["diagnostics"]["negative_training_credit"] += 1
    else:
        cell.record_candidate_intervention("neutral")
        node["diagnostics"]["neutral_training_credit"] += 1
    delta = eta_m3 * credit
    node["local_weight"] = float(node["local_weight"]) + delta
    node["diagnostics"]["m3_fast_weight_delta"] += delta
    cell.xp = max(0, cell.xp + int(round(credit * 10.0)))


def _training_credit_for_action(
    board: chess.Board,
    move: chess.Move,
    candidate: dict[str, Any],
) -> float:
    after = board.copy(stack=False)
    after.push(move)
    reason = _projected_negative_reason(board, after)
    if reason is not None:
        return -1.0
    if after.is_checkmate():
        return 1.0
    if _after_condition_matches(board, after, candidate):
        return 0.2
    return 0.0


def _post_action_credit(
    before: chess.Board,
    after: chess.Board,
    candidate: dict[str, Any],
) -> float:
    reason = _projected_negative_reason(before, after)
    if reason is not None:
        return -1.0
    if after.is_checkmate():
        return 1.0
    if _after_condition_matches(before, after, candidate):
        return 0.2
    return 0.0


def _local_arbitration_result(
    *,
    outcome: str,
    plies: int,
    illegal_moves: int,
    action_changed_position: bool,
    no_action_position: bool,
    local_parent_request_count: int,
    action_option_count: int,
    action_selected_count: int,
    action_changed_move_count: int,
    suppressor_trigger_count: int,
    suppressed_action_option_count: int,
    baseline_fallback_count: int,
    positive_credit_count: int,
    negative_credit_count: int,
    neutral_credit_count: int,
    m3_update_count: int,
    m3_fast_weight_delta_scaled: int,
    repetition_events: int,
    repeated_white_action_events: int,
) -> dict[str, Any]:
    payload = _sandbox_result(
        outcome=outcome,
        plies=plies,
        illegal_moves=illegal_moves,
        candidate_terminal_activations=local_parent_request_count,
        candidate_action_matches=action_option_count,
        candidate_move_count=action_selected_count,
        candidate_changed_move_count=action_changed_move_count,
        after_condition_match_count=0,
        positive_credit_count=positive_credit_count,
        negative_credit_count=negative_credit_count,
        m3_update_count=m3_update_count,
        m3_fast_weight_delta=m3_fast_weight_delta_scaled / 1000.0,
        repetition_events=repetition_events,
        repeated_white_action_events=repeated_white_action_events,
        activated_position=action_selected_count > 0,
        behavior_changed_position=action_changed_position,
    )
    payload.update(
        {
            "local_parent_request_count": int(local_parent_request_count),
            "action_option_count": int(action_option_count),
            "action_selected_count": int(action_selected_count),
            "action_changed_move_count": int(action_changed_move_count),
            "action_changed_position_count": 1 if action_changed_position else 0,
            "suppressor_trigger_count": int(suppressor_trigger_count),
            "suppressed_action_option_count": int(suppressed_action_option_count),
            "baseline_fallback_count": int(baseline_fallback_count),
            "no_action_position_count": 1 if no_action_position else 0,
            "neutral_credit_count": int(neutral_credit_count),
        }
    )
    return payload


def _arbitration_decision(
    *,
    baseline_metrics: ArmMetrics,
    selected_candidate_metrics: SandboxMetrics,
    arbitration_metrics: LocalArbitrationMetrics,
    safety: dict[str, dict[str, int]],
    suppressor_cell: StemCellTerminal,
) -> dict[str, Any]:
    safety_ok = (
        safety["local_action_arbitration"]["illegal_regression_count"] == 0
        and safety["local_action_arbitration"]["stalemate_regression_count"] == 0
        and safety["local_action_arbitration"]["rook_loss_regression_count"]
        <= safety["selected_candidate_unsuppressed"]["rook_loss_regression_count"]
    )
    conversion_improved = arbitration_metrics.mates > baseline_metrics.mates
    improved_vs_selected = arbitration_metrics.rook_losses < selected_candidate_metrics.rook_losses
    action_nodes_active = arbitration_metrics.action_selected_count > 0
    suppressor_active = arbitration_metrics.suppressor_trigger_count > 0
    competence_passed = conversion_improved and safety_ok and action_nodes_active
    return {
        "status": "competence_candidate_found" if competence_passed else "local_arbitration_checkpoint_failed",
        "passed": competence_passed,
        "safety_checkpoint_passed": safety_ok,
        "safety_improved_vs_selected_candidate": improved_vs_selected,
        "krk_competence_passed": competence_passed,
        "conversion_improved_vs_baseline": conversion_improved,
        "rook_loss_delta_vs_selected_candidate": arbitration_metrics.rook_losses - selected_candidate_metrics.rook_losses,
        "move_choice_mediated_by_local_action_nodes": True,
        "suppressor_mediated_sibling_inhibition": suppressor_active,
        "suppressed_candidate_survival_decision": suppressor_cell.candidate_survival_decision(),
        "external_move_ranking_applied": False,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "m3_update_count": arbitration_metrics.m3_update_count,
        "reasons": _arbitration_reasons(
            conversion_improved=conversion_improved,
            safety_ok=safety_ok,
            action_nodes_active=action_nodes_active,
            suppressor_active=suppressor_active,
        ),
    }


def _arbitration_reasons(
    *,
    conversion_improved: bool,
    safety_ok: bool,
    action_nodes_active: bool,
    suppressor_active: bool,
) -> list[str]:
    reasons: list[str] = []
    if not action_nodes_active:
        reasons.append("local_action_nodes_never_selected")
    if not suppressor_active:
        reasons.append("suppressor_never_inhibited_sibling")
    if not conversion_improved:
        reasons.append("no_heldout_conversion_gain")
    if not safety_ok:
        reasons.append("safety_regression")
    return reasons


def _candidate_by_key(action_nodes: list[dict[str, Any]], candidate_key: str | None) -> dict[str, Any] | None:
    for node in action_nodes:
        if node["candidate_key"] == candidate_key:
            return node["candidate"]
    return None

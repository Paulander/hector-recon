"""M15 local multi-step SCRIPT candidates for KRK autogrowth."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal

from .candidate_generation import CONTEXT_SPECIALIZED_FEATURES, RISK_DELTA_FEATURES, _risk_aware_credit
from .evaluate import (
    ArmMetrics,
    choose_black_reply,
    choose_white_baseline_move,
    classify_terminal_outcome,
    evaluate_arm,
    _position_repetition_key,
)
from .features import extract_learner_features, validate_learner_record
from .mining import _magnitude_bucket, _signed_bucket
from .positions import KRKPositionSet, generate_position_sets
from .sandbox import _action_schema_matches, _before_condition_matches, _paired_delta, _safety_counts, _sandbox_result
from .suppressor import _projected_negative_reason


@dataclass(frozen=True)
class LocalScriptConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    min_support: int = 1
    max_candidates: int = 12
    horizon: int = 40
    min_sequence_credit: float = 0.10
    activation_max_distance: float = 0.0
    eta_m3: float = 0.08


@dataclass(frozen=True)
class LocalScriptMetrics:
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
    script_request_count: int
    script_start_count: int
    script_step_count: int
    script_complete_count: int
    script_abort_count: int
    script_changed_position_count: int
    baseline_fallback_count: int
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

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["conversion_rate"] = self.conversion_rate
        return payload


@dataclass(frozen=True)
class LocalScriptResult:
    config: LocalScriptConfig
    positions: KRKPositionSet
    candidates: list[dict[str, Any]]
    script_nodes: list[dict[str, Any]]
    generation_summary: dict[str, Any]
    baseline_metrics: ArmMetrics
    script_metrics: LocalScriptMetrics
    paired_deltas: dict[str, int]
    safety: dict[str, int]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.candidates)
        return {
            "schema_version": "krk_autogrowth_m15_local_script_candidates.v0",
            "config": asdict(self.config),
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "generation_summary": self.generation_summary,
            "local_recon_structure": {
                "parent_node_type": "SCRIPT",
                "candidate_node_type": "SCRIPT",
                "action_child_count_per_script": 2,
                "relation_types": ["SUB", "POR", "RET"],
                "move_choice_mediated_by_local_script_nodes": True,
                "direct_move_override": False,
            },
            "candidates": self.candidates,
            "script_nodes": [
                {
                    "cell": node["cell"].to_dict(),
                    "local_weight": node["local_weight"],
                    "learner_visible": node["learner_visible"],
                    "diagnostics": node["diagnostics"],
                }
                for node in self.script_nodes
            ],
            "arms": {
                "baseline": self.baseline_metrics.to_dict(),
                "local_script": self.script_metrics.to_dict(),
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


def run_local_script_experiment(
    *,
    config: LocalScriptConfig,
    positions: KRKPositionSet | None = None,
) -> LocalScriptResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    candidates, generation_summary = generate_local_script_candidates(positions.train, config=config)
    script_nodes = build_local_script_nodes(positions.train, candidates=candidates, config=config)
    heldout = list(positions.heldout)
    baseline_metrics, baseline_outcomes = evaluate_arm(heldout, arm="baseline", horizon=config.horizon)
    script_metrics, script_outcomes = evaluate_local_script_arm(
        heldout,
        script_nodes=script_nodes,
        horizon=config.horizon,
        activation_max_distance=config.activation_max_distance,
    )
    paired = _paired_delta(baseline_outcomes, script_outcomes)
    safety = _safety_counts(baseline_outcomes, script_outcomes)
    decision = _script_decision(
        baseline_metrics=baseline_metrics,
        script_metrics=script_metrics,
        safety=safety,
    )
    return LocalScriptResult(
        config=config,
        positions=positions,
        candidates=candidates,
        script_nodes=script_nodes,
        generation_summary=generation_summary,
        baseline_metrics=baseline_metrics,
        script_metrics=script_metrics,
        paired_deltas=paired,
        safety=safety,
        decision=decision,
    )


def generate_local_script_candidates(
    train_fens: Iterable[str],
    *,
    config: LocalScriptConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    starts_considered = 0
    rejected_negative = 0
    rejected_low_credit = 0

    for position_index, fen in enumerate(train_fens):
        board = chess.Board(fen)
        if board.turn != chess.WHITE:
            continue
        before_features = extract_learner_features(board)
        for first_move in sorted(board.legal_moves, key=lambda item: item.uci()):
            piece = board.piece_at(first_move.from_square)
            if piece is None or piece.color != chess.WHITE:
                continue
            starts_considered += 1
            after_first = board.copy(stack=False)
            after_first.push(first_move)
            if _projected_negative_reason(board, after_first) is not None:
                rejected_negative += 1
                continue
            black_move = choose_black_reply(after_first)
            if black_move is None or black_move not in after_first.legal_moves:
                continue
            before_second = after_first.copy(stack=False)
            before_second.push(black_move)
            if before_second.turn != chess.WHITE:
                continue
            first_credit = _risk_aware_credit(board, after_first)
            for second_move in sorted(before_second.legal_moves, key=lambda item: item.uci()):
                second_piece = before_second.piece_at(second_move.from_square)
                if second_piece is None or second_piece.color != chess.WHITE:
                    continue
                after_second = before_second.copy(stack=False)
                after_second.push(second_move)
                if _projected_negative_reason(before_second, after_second) is not None:
                    rejected_negative += 1
                    continue
                second_credit = _risk_aware_credit(before_second, after_second)
                sequence_credit = first_credit + second_credit
                if sequence_credit < config.min_sequence_credit:
                    rejected_low_credit += 1
                    continue
                after_features = extract_learner_features(after_second)
                deltas = {key: after_features[key] - before_features[key] for key in before_features}
                first_schema = _action_schema(board, first_move)
                second_schema = _action_schema(before_second, second_move)
                key = _script_bucket_key(before_features, first_schema, second_schema)
                buckets.setdefault(key, []).append(
                    {
                        "position_index": position_index,
                        "before_features": before_features,
                        "after_features": after_features,
                        "progress_deltas": deltas,
                        "first_action_schema": first_schema,
                        "second_action_schema": second_schema,
                        "credit": sequence_credit,
                    }
                )

    raw_candidates = [
        _candidate_from_script_bucket(bucket_key=key, rows=rows)
        for key, rows in buckets.items()
        if len(rows) >= config.min_support
    ]
    raw_candidates.sort(
        key=lambda candidate: (
            candidate["evidence"]["mean_candidate_credit"],
            candidate["evidence"]["support_count"],
            candidate["candidate_key"],
        ),
        reverse=True,
    )
    candidates = raw_candidates[: config.max_candidates]
    for rank, candidate in enumerate(candidates, start=1):
        candidate["rank"] = rank
        candidate["selected_for_m5"] = rank == 1
        validate_learner_record(candidate)
    return candidates, {
        "first_step_actions_considered": starts_considered,
        "rejected_negative_projection_count": rejected_negative,
        "rejected_low_credit_count": rejected_low_credit,
        "bucket_count": len(buckets),
        "candidate_count": len(candidates),
        "behavior_change_applied": False,
        "candidate_active_in_runtime": False,
        "direct_move_override": False,
    }


def build_local_script_nodes(
    train_fens: Iterable[str],
    *,
    candidates: list[dict[str, Any]],
    config: LocalScriptConfig,
) -> list[dict[str, Any]]:
    nodes = [_make_script_node(candidate) for candidate in candidates]
    for fen in train_fens:
        board = chess.Board(fen)
        for node in nodes:
            credit = _script_training_credit(board, node["candidate"], config=config)
            if credit is None:
                continue
            node["cell"].record_candidate_request("m15_script_parent")
            node["cell"].record_candidate_activation("m15_script_parent")
            if credit > 0.0:
                node["cell"].record_candidate_intervention("positive")
                node["diagnostics"]["positive_training_credit"] += 1
            elif credit < 0.0:
                node["cell"].record_candidate_intervention("negative")
                node["diagnostics"]["negative_training_credit"] += 1
            else:
                node["cell"].record_candidate_intervention("neutral")
                node["diagnostics"]["neutral_training_credit"] += 1
            node["diagnostics"]["training_sequences"] += 1
            node["local_weight"] += config.eta_m3 * credit
            node["diagnostics"]["m3_fast_weight_delta"] += config.eta_m3 * credit
    for node in nodes:
        node["cell"].candidate_stats.recompute_survival(xp=node["cell"].xp, solidify_xp=node["cell"].XP_SOLIDIFY)
        node["learner_visible"]["local_weight"] = round(float(node["local_weight"]), 6)
        node["learner_visible"]["selectable_after_training"] = _script_node_is_selectable(node)
        node["diagnostics"]["selectable_after_training"] = _script_node_is_selectable(node)
        validate_learner_record(node["learner_visible"])
    return nodes


def evaluate_local_script_arm(
    fens: Iterable[str],
    *,
    script_nodes: list[dict[str, Any]],
    horizon: int,
    activation_max_distance: float,
) -> tuple[LocalScriptMetrics, list[dict[str, Any]]]:
    outcomes: list[dict[str, Any]] = []
    counts = {"mate": 0, "horizon_no_mate": 0, "stalemate": 0, "rook_loss": 0, "illegal_move": 0, "other_failure": 0}
    draw_reasons: dict[str, int] = {}
    totals = {
        "script_request_count": 0,
        "script_start_count": 0,
        "script_step_count": 0,
        "script_complete_count": 0,
        "script_abort_count": 0,
        "script_changed_position_count": 0,
        "baseline_fallback_count": 0,
        "positive_credit_count": 0,
        "negative_credit_count": 0,
        "neutral_credit_count": 0,
        "m3_update_count": 0,
        "m3_fast_weight_delta_scaled": 0,
        "repetition_events": 0,
        "repeated_white_action_events": 0,
    }
    for fen in fens:
        result = _script_playout(
            fen,
            script_nodes=script_nodes,
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
    return LocalScriptMetrics(
        arm="local_script",
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
        script_request_count=totals["script_request_count"],
        script_start_count=totals["script_start_count"],
        script_step_count=totals["script_step_count"],
        script_complete_count=totals["script_complete_count"],
        script_abort_count=totals["script_abort_count"],
        script_changed_position_count=totals["script_changed_position_count"],
        baseline_fallback_count=totals["baseline_fallback_count"],
        positive_credit_count=totals["positive_credit_count"],
        negative_credit_count=totals["negative_credit_count"],
        neutral_credit_count=totals["neutral_credit_count"],
        m3_update_count=totals["m3_update_count"],
        m3_fast_weight_delta=totals["m3_fast_weight_delta_scaled"] / 1000.0,
        repetition_events=totals["repetition_events"],
        repeated_white_action_events=totals["repeated_white_action_events"],
    ), outcomes


def choose_local_script_action(
    board: chess.Board,
    *,
    script_nodes: list[dict[str, Any]],
    active_script: dict[str, Any] | None,
    activation_max_distance: float,
) -> dict[str, Any]:
    """Resolve local SCRIPT state to one ACTION move or no local action."""

    if active_script is not None:
        node = _script_node_by_key(script_nodes, active_script["candidate_key"])
        if node is not None and _script_node_is_selectable(node):
            move = _first_matching_move(board, node["candidate"]["script_plan"]["actions"][1])
            if move is not None:
                return {"move": move, "node": node, "phase": 1, "started": False, "completed": True}
        return {"move": None, "node": None, "phase": None, "started": False, "completed": False, "aborted": True}

    options: list[tuple[float, int, str, dict[str, Any], chess.Move]] = []
    for node in script_nodes:
        if not _script_node_is_selectable(node):
            continue
        candidate = node["candidate"]
        if not _before_condition_matches(board, candidate, activation_max_distance):
            continue
        move = _first_matching_move(board, candidate["script_plan"]["actions"][0])
        if move is None:
            continue
        options.append((float(node["local_weight"]), -int(node["rank"]), move.uci(), node, move))
    if not options:
        return {"move": None, "node": None, "phase": None, "started": False, "completed": False}
    options.sort(reverse=True)
    _weight, _rank, _uci, node, move = options[0]
    return {"move": move, "node": node, "phase": 0, "started": True, "completed": False}


def _script_playout(
    fen: str,
    *,
    script_nodes: list[dict[str, Any]],
    horizon: int,
    activation_max_distance: float,
) -> dict[str, Any]:
    board = chess.Board(fen)
    active_script: dict[str, Any] | None = None
    position_counts = {_position_repetition_key(board): 1}
    white_action_counts: dict[str, int] = {}
    changed_position = False
    totals = {
        "script_request_count": 0,
        "script_start_count": 0,
        "script_step_count": 0,
        "script_complete_count": 0,
        "script_abort_count": 0,
        "baseline_fallback_count": 0,
        "positive_credit_count": 0,
        "negative_credit_count": 0,
        "neutral_credit_count": 0,
        "m3_update_count": 0,
        "m3_fast_weight_delta_scaled": 0,
        "repetition_events": 0,
        "repeated_white_action_events": 0,
    }
    illegal_moves = 0
    for ply in range(int(horizon)):
        terminal = classify_terminal_outcome(board)
        if terminal is not None:
            return _script_result(outcome=terminal, plies=ply, illegal_moves=illegal_moves, changed_position=changed_position, **totals)
        baseline_move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        before = board.copy(stack=False)
        if baseline_move is None or baseline_move not in board.legal_moves:
            illegal_moves += 1
            return _script_result(outcome="illegal_move", plies=ply, illegal_moves=illegal_moves, changed_position=changed_position, **totals)
        move = baseline_move
        selected_node = None
        if board.turn == chess.WHITE:
            totals["script_request_count"] += 1
            decision = choose_local_script_action(
                board,
                script_nodes=script_nodes,
                active_script=active_script,
                activation_max_distance=activation_max_distance,
            )
            if decision.get("aborted"):
                totals["script_abort_count"] += 1
                active_script = None
            elif decision["move"] is None:
                totals["baseline_fallback_count"] += 1
                active_script = None
            else:
                move = decision["move"]
                selected_node = decision["node"]
                totals["script_step_count"] += 1
                if decision["started"]:
                    totals["script_start_count"] += 1
                    active_script = {"candidate_key": selected_node["candidate_key"]}
                if decision["completed"]:
                    totals["script_complete_count"] += 1
                    active_script = None
                if move != baseline_move:
                    changed_position = True
        if before.turn == chess.WHITE:
            action_key = move.uci()
            if white_action_counts.get(action_key, 0) > 0:
                totals["repeated_white_action_events"] += 1
            white_action_counts[action_key] = white_action_counts.get(action_key, 0) + 1
        board.push(move)
        if before.turn == chess.WHITE and selected_node is not None:
            credit = _post_script_step_credit(before, board)
            if credit > 0.0:
                totals["positive_credit_count"] += 1
            elif credit < 0.0:
                totals["negative_credit_count"] += 1
            else:
                totals["neutral_credit_count"] += 1
            totals["m3_update_count"] += 1
            totals["m3_fast_weight_delta_scaled"] += int(round(credit * 1000.0))
        key = _position_repetition_key(board)
        if position_counts.get(key, 0) > 0:
            totals["repetition_events"] += 1
        position_counts[key] = position_counts.get(key, 0) + 1
    return _script_result(
        outcome="mate" if board.is_checkmate() else "horizon_no_mate",
        plies=int(horizon),
        illegal_moves=illegal_moves,
        changed_position=changed_position,
        **totals,
    )


def _candidate_from_script_bucket(*, bucket_key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    before = _mean_features(row["before_features"] for row in rows)
    after = _mean_features(row["after_features"] for row in rows)
    deltas = _mean_features(row["progress_deltas"] for row in rows)
    scores = [float(row["credit"]) for row in rows]
    digest = hashlib.sha256(bucket_key.encode("utf-8")).hexdigest()[:12]
    return {
        "candidate_key": f"m15_script_{digest}",
        "rank": 0,
        "selected_for_m5": False,
        "status": "m15_local_script_not_spawned",
        "source_split": "train",
        "behavior_change_applied": False,
        "candidate_active_in_runtime": False,
        "recon_topology_plan": {
            "node_types": ["SCRIPT", "TERMINAL", "ACTION", "ACTION", "TERMINAL"],
            "relation_types": ["SUB", "POR", "SUR", "RET"],
            "spawn_count": 1,
            "spawned_now": False,
            "m3_update_count": 0,
            "m4_event_count": 0,
            "local_parent_id": "m15_script_parent",
        },
        "before_cluster": {
            "feature_names": list(CONTEXT_SPECIALIZED_FEATURES),
            "prototype": {name: before[name] for name in CONTEXT_SPECIALIZED_FEATURES},
        },
        "script_plan": {
            "node_type": "SCRIPT",
            "actions": [rows[0]["first_action_schema"], rows[0]["second_action_schema"]],
            "relation_plan": {
                "parent_relation": "SUB",
                "step_relation": "POR",
                "confirmation_relation": "SUR",
                "can_be_inhibited_by": "RET",
                "chooses_move_directly": False,
            },
        },
        "after_delta_cluster": {
            "feature_names": list(RISK_DELTA_FEATURES),
            "prototype": {name: deltas[name] for name in RISK_DELTA_FEATURES},
        },
        "after_cluster": {"feature_names": sorted(after), "prototype": after},
        "evidence": {
            "support_count": len(rows),
            "position_count": len({int(row["position_index"]) for row in rows}),
            "mean_generic_progress_credit": mean(scores),
            "mean_terminal_reward": 0.0,
            "mean_candidate_credit": mean(scores),
            "positive_credit_count": sum(1 for score in scores if score > 0.0),
            "negative_credit_count": sum(1 for score in scores if score < 0.0),
            "example_trace_keys": [f"m15_script_{row['position_index']}" for row in rows[:8]],
        },
    }


def _make_script_node(candidate: dict[str, Any]) -> dict[str, Any]:
    cell = StemCellTerminal(f"script_{candidate['candidate_key']}")
    cell.state = StemCellState.TRIAL
    cell.trial_node_id = f"TRIAL_{cell.cell_id}"
    cell.trial_parent_id = "m15_script_parent"
    cell.xp = cell.XP_INITIAL
    base_weight = float(candidate.get("evidence", {}).get("mean_candidate_credit", 0.0))
    learner_visible = {
        "node_type": "SCRIPT",
        "candidate_key": candidate["candidate_key"],
        "parent_id": "m15_script_parent",
        "action_child_count": 2,
        "script_plan": candidate["script_plan"],
        "local_weight": round(base_weight, 6),
    }
    validate_learner_record(learner_visible)
    return {
        "candidate": candidate,
        "candidate_key": candidate["candidate_key"],
        "rank": int(candidate.get("rank", 0)),
        "cell": cell,
        "local_weight": base_weight,
        "learner_visible": learner_visible,
        "diagnostics": {
            "training_sequences": 0,
            "positive_training_credit": 0,
            "negative_training_credit": 0,
            "neutral_training_credit": 0,
            "m3_fast_weight_delta": 0.0,
        },
    }


def _script_training_credit(board: chess.Board, candidate: dict[str, Any], *, config: LocalScriptConfig) -> float | None:
    if not _before_condition_matches(board, candidate, config.activation_max_distance):
        return None
    first = _first_matching_move(board, candidate["script_plan"]["actions"][0])
    if first is None:
        return None
    after_first = board.copy(stack=False)
    after_first.push(first)
    if _projected_negative_reason(board, after_first) is not None:
        return -1.0
    black_move = choose_black_reply(after_first)
    if black_move is None or black_move not in after_first.legal_moves:
        return 0.0
    before_second = after_first.copy(stack=False)
    before_second.push(black_move)
    second = _first_matching_move(before_second, candidate["script_plan"]["actions"][1])
    if second is None:
        return 0.0
    after_second = before_second.copy(stack=False)
    after_second.push(second)
    if _projected_negative_reason(before_second, after_second) is not None:
        return -1.0
    return _risk_aware_credit(board, after_first) + _risk_aware_credit(before_second, after_second)


def _post_script_step_credit(before: chess.Board, after: chess.Board) -> float:
    if _projected_negative_reason(before, after) is not None:
        return -1.0
    if after.is_checkmate():
        return 1.0
    return _risk_aware_credit(before, after)


def _script_node_is_selectable(node: dict[str, Any]) -> bool:
    credit = node["cell"].candidate_stats.credit_stats
    return int(credit.negative_intervention) == 0


def _first_matching_move(board: chess.Board, action_schema: dict[str, Any]) -> chess.Move | None:
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        if _action_schema_matches(board, move, action_schema):
            return move
    return None


def _script_node_by_key(script_nodes: list[dict[str, Any]], candidate_key: str) -> dict[str, Any] | None:
    for node in script_nodes:
        if node["candidate_key"] == candidate_key:
            return node
    return None


def _action_schema(board: chess.Board, move: chess.Move) -> dict[str, int]:
    piece = board.piece_at(move.from_square)
    file_delta = chess.square_file(move.to_square) - chess.square_file(move.from_square)
    rank_delta = chess.square_rank(move.to_square) - chess.square_rank(move.from_square)
    return {
        "piece_type": 0 if piece is None else int(piece.piece_type),
        "file_delta_sign": _signed_bucket(file_delta),
        "rank_delta_sign": _signed_bucket(rank_delta),
        "file_delta_magnitude": _magnitude_bucket(file_delta),
        "rank_delta_magnitude": _magnitude_bucket(rank_delta),
        "gives_check": int(board.gives_check(move)),
        "is_capture": int(board.is_capture(move)),
    }


def _script_bucket_key(
    before_features: dict[str, float],
    first_schema: dict[str, Any],
    second_schema: dict[str, Any],
) -> str:
    before_bucket = {name: int(round(before_features[name])) for name in CONTEXT_SPECIALIZED_FEATURES}
    return json.dumps(
        {"before": before_bucket, "first": first_schema, "second": second_schema},
        sort_keys=True,
        separators=(",", ":"),
    )


def _mean_features(rows: Iterable[dict[str, float]]) -> dict[str, float]:
    materialized = list(rows)
    if not materialized:
        return {}
    return {
        key: sum(float(row[key]) for row in materialized) / len(materialized)
        for key in materialized[0]
    }


def _script_result(
    *,
    outcome: str,
    plies: int,
    illegal_moves: int,
    changed_position: bool,
    script_request_count: int,
    script_start_count: int,
    script_step_count: int,
    script_complete_count: int,
    script_abort_count: int,
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
        candidate_terminal_activations=script_request_count,
        candidate_action_matches=script_step_count,
        candidate_move_count=script_step_count,
        candidate_changed_move_count=script_step_count if changed_position else 0,
        after_condition_match_count=0,
        positive_credit_count=positive_credit_count,
        negative_credit_count=negative_credit_count,
        m3_update_count=m3_update_count,
        m3_fast_weight_delta=m3_fast_weight_delta_scaled / 1000.0,
        repetition_events=repetition_events,
        repeated_white_action_events=repeated_white_action_events,
        activated_position=script_step_count > 0,
        behavior_changed_position=changed_position,
    )
    payload.update(
        {
            "script_request_count": script_request_count,
            "script_start_count": script_start_count,
            "script_step_count": script_step_count,
            "script_complete_count": script_complete_count,
            "script_abort_count": script_abort_count,
            "script_changed_position_count": 1 if changed_position else 0,
            "baseline_fallback_count": baseline_fallback_count,
            "neutral_credit_count": neutral_credit_count,
        }
    )
    return payload


def _script_decision(
    *,
    baseline_metrics: ArmMetrics,
    script_metrics: LocalScriptMetrics,
    safety: dict[str, int],
) -> dict[str, Any]:
    safety_ok = (
        safety["illegal_regression_count"] == 0
        and safety["stalemate_regression_count"] == 0
        and safety["rook_loss_regression_count"] == 0
    )
    conversion_improved = script_metrics.mates > baseline_metrics.mates
    competence = conversion_improved and safety_ok and script_metrics.script_step_count > 0
    reasons: list[str] = []
    if script_metrics.script_step_count == 0:
        reasons.append("local_script_never_selected")
    if not conversion_improved:
        reasons.append("no_heldout_conversion_gain")
    if not safety_ok:
        reasons.append("safety_regression")
    return {
        "status": "local_script_competence_candidate_found" if competence else "local_script_checkpoint_failed",
        "passed": competence,
        "safety_checkpoint_passed": safety_ok,
        "krk_competence_passed": competence,
        "conversion_improved_vs_baseline": conversion_improved,
        "move_choice_mediated_by_local_script_nodes": True,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "m3_update_count": script_metrics.m3_update_count,
        "reasons": reasons,
    }

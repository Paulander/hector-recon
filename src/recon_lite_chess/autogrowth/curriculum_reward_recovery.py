"""TG24 KRK curriculum reward recovery for graded evaluation.

This module recovers useful curriculum reward/stage diagnostics without making
curriculum labels learner-visible or adding another retry candidate mechanism.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
from statistics import pstdev
from typing import Any, Iterable

import chess

from recon_lite_chess.training.krk_curriculum import (
    KRK_STAGES,
    box_min_side,
    compute_confinement_box,
    did_box_grow,
    krk_reward,
)

from .continuation_retry import (
    choose_continuation_retry_action,
    evaluate_continuation_retry_arm,
    _empty_retry_totals,
)
from .evaluate import (
    choose_black_reply,
    choose_white_baseline_move,
    classify_terminal_outcome,
    _position_repetition_key,
)
from .features import extract_learner_features, validate_learner_record
from .fragment_chain_curriculum import (
    FragmentChainCurriculumConfig,
    _chain_adjacency,
    _empty_chain_totals,
    _generate_fragment_candidates,
    _local_script_config,
)
from .lag_terminals import _after_terminal_matches, _apply_lag_quarantine, _empty_lag_totals
from .positions import KRKPositionSet, generate_position_sets
from .script_candidates import (
    build_local_script_nodes,
    _action_schema,
    _candidate_from_script_bucket,
    _post_script_step_credit,
    _script_bucket_key,
)
from .script_fragments import generalize_script_candidates_to_fragments
from .topological_growth import build_triplet_chain_view


@dataclass(frozen=True)
class CurriculumRewardRecoveryConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    min_support: int = 1
    max_candidates: int = 12
    horizons: tuple[int, ...] = (40, 80)
    min_sequence_credit: float = 0.10
    activation_max_distance: float = 0.5
    after_max_distance: float = 1.5
    chain_max_distance: float = 1.5
    max_chain_edges: int = 64
    chain_request_bonus: float = 0.75
    eta_m3: float = 0.08
    lag_negative_threshold: int = 1
    curriculum_probe_per_stage: int = 1
    max_rollout_samples: int = 8


@dataclass(frozen=True)
class RetryRuntime:
    candidates: list[dict[str, Any]]
    chain_view: dict[str, Any]
    script_nodes: list[dict[str, Any]]
    chain_adjacency: dict[str, list[str]]
    training_summary: dict[str, Any]


@dataclass(frozen=True)
class CurriculumRewardRecoveryResult:
    config: CurriculumRewardRecoveryConfig
    positions: KRKPositionSet
    retry_runtime: RetryRuntime
    yoked_random_runtime: RetryRuntime
    heldout_metrics: dict[str, Any]
    curriculum_probe_metrics: dict[str, Any]
    audit: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        primary = str(self.config.horizons[0])
        primary_metrics = self.heldout_metrics[primary]
        baseline_metrics = primary_metrics["baseline"]
        candidate_on_metrics = primary_metrics["continuation_retry_on"]
        yoked_random_metrics = primary_metrics["yoked_random_control"]
        paired_delta_metrics = primary_metrics["paired_deltas"]
        safety_metrics = primary_metrics["safety_metrics"]
        trace_mined_vs_yoked = _trace_mined_vs_yoked_random(primary_metrics)
        return {
            "schema_version": "krk_autogrowth_tg24_curriculum_reward_recovery.v0",
            "checkpoint": "TG24_curriculum_reward_recovery",
            "config": {
                **asdict(self.config),
                "horizons": list(self.config.horizons),
            },
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "audit": self.audit,
            "old_curriculum_usage_audit": self.audit,
            "graded_metrics_available": True,
            "dtm_available": False,
            "runtime_tablebase_or_dtm_move_source": False,
            "curriculum_labels_learner_visible": False,
            "paired_rollouts_enabled": True,
            "m3_training_confirmation_split_enforced": True,
            "m4_consolidation_event_count": 0,
            "local_recon_structure": {
                "candidate_on_arm": "tg20_local_continuation_retry",
                "candidate_off_arm": "baseline",
                "graded_evaluator_changes_behavior": False,
                "candidate_on_behavior_mediated_by_local_script_nodes": True,
                "direct_move_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "selector_behavior_enabled": False,
                "curriculum_labels_learner_visible": False,
                "curriculum_labels_diagnostics_only": True,
            },
            "credit_policy": {
                "old_curriculum_reward_component_recorded": True,
                "non_terminal_graded_progress_recorded": True,
                "m3_training_chunk_graded_credit_available": True,
                "m3_graded_credit_applied_in_tg24": False,
                "m4_consolidation_event_count": 0,
                "m4_consolidation_requires_fresh_confirmation_with_m3_frozen": True,
                "selection_training_split": "train",
                "confirmation_split": "heldout",
                "confirmation_m3_update_nodes": False,
            },
            "learner_visibility": {
                "curriculum_labels_in_learner_records": False,
                "stage_labels_in_learner_records": False,
                "curriculum_labels_in_diagnostics": True,
                "validated_generic_credit_record": _validated_generic_credit_record(),
            },
            "retry_runtime": {
                "candidate_count": len(self.retry_runtime.candidates),
                "chain_edge_count": int(self.retry_runtime.chain_view.get("chain_edge_count", 0)),
                "training_summary": self.retry_runtime.training_summary,
            },
            "yoked_random_runtime": {
                "candidate_count": len(self.yoked_random_runtime.candidates),
                "chain_edge_count": int(self.yoked_random_runtime.chain_view.get("chain_edge_count", 0)),
                "training_summary": self.yoked_random_runtime.training_summary,
            },
            "trace_mined_vs_yoked_random": trace_mined_vs_yoked,
            "baseline_metrics": baseline_metrics,
            "candidate_off_metrics": baseline_metrics,
            "candidate_on_metrics": candidate_on_metrics,
            "yoked_random_control_metrics": yoked_random_metrics,
            "paired_delta_metrics": paired_delta_metrics,
            "safety_metrics": safety_metrics,
            "heldout_metrics": self.heldout_metrics,
            "curriculum_probe_metrics": self.curriculum_probe_metrics,
            "decision": self.decision,
            "next_recommended_checkpoint": self.decision["next_recommended_checkpoint"],
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_curriculum_reward_recovery(
    *,
    config: CurriculumRewardRecoveryConfig,
    positions: KRKPositionSet | None = None,
) -> CurriculumRewardRecoveryResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    retry_runtime = _build_retry_runtime(config=config, positions=positions)
    yoked_random_runtime = _build_yoked_random_runtime(config=config, positions=positions)
    heldout_metrics = _evaluate_paired_graded(
        positions.heldout,
        config=config,
        retry_runtime=retry_runtime,
        yoked_random_runtime=yoked_random_runtime,
        split="heldout",
        include_stage_slices=True,
    )
    curriculum_probe_metrics = _evaluate_paired_graded(
        _curriculum_probe_fens(config.curriculum_probe_per_stage),
        config=config,
        retry_runtime=retry_runtime,
        yoked_random_runtime=yoked_random_runtime,
        split="curriculum_probe",
        include_stage_slices=True,
    )
    audit = _audit_curriculum_use()
    decision = _decision(config=config, heldout_metrics=heldout_metrics)
    return CurriculumRewardRecoveryResult(
        config=config,
        positions=positions,
        retry_runtime=retry_runtime,
        yoked_random_runtime=yoked_random_runtime,
        heldout_metrics=heldout_metrics,
        curriculum_probe_metrics=curriculum_probe_metrics,
        audit=audit,
        decision=decision,
    )


def _build_retry_runtime(*, config: CurriculumRewardRecoveryConfig, positions: KRKPositionSet) -> RetryRuntime:
    chain_config = _fragment_config(config)
    candidates = _generate_fragment_candidates(positions, config=chain_config)
    chain_view = build_triplet_chain_view(
        candidates,
        max_distance=config.chain_max_distance,
        max_edges=config.max_chain_edges,
    )
    script_nodes = build_local_script_nodes(
        positions.train,
        candidates=candidates,
        config=_local_script_config(chain_config, horizon=max(config.horizons)),
    )
    adjacency = _chain_adjacency(chain_view)
    training_metrics, _training_outcomes = evaluate_continuation_retry_arm(
        positions.train,
        script_nodes=script_nodes,
        chain_adjacency=adjacency,
        horizon=max(config.horizons),
        activation_max_distance=config.activation_max_distance,
        after_max_distance=config.after_max_distance,
        chain_request_bonus=config.chain_request_bonus,
        eta_m3=config.eta_m3,
        lag_negative_threshold=config.lag_negative_threshold,
        update_nodes=True,
        arm="tg24_training_retry_runtime",
    )
    _apply_lag_quarantine(script_nodes, threshold=config.lag_negative_threshold)
    return RetryRuntime(
        candidates=candidates,
        chain_view=chain_view,
        script_nodes=script_nodes,
        chain_adjacency=adjacency,
        training_summary={
            "arm": "tg24_training_retry_runtime",
            "m3_update_count": training_metrics.chain.m3_update_count,
            "m3_fast_weight_delta": training_metrics.chain.m3_fast_weight_delta,
            "positive_credit_count": training_metrics.chain.positive_credit_count,
            "negative_credit_count": training_metrics.chain.negative_credit_count,
            "neutral_credit_count": training_metrics.chain.neutral_credit_count,
            "lag_quarantined_candidate_count": training_metrics.lag_quarantined_candidate_count,
            "m4_consolidation_event_count": 0,
            "graded_tg24_credit_applied": False,
        },
    )


def _build_yoked_random_runtime(*, config: CurriculumRewardRecoveryConfig, positions: KRKPositionSet) -> RetryRuntime:
    candidates = _generate_yoked_random_candidates(
        positions.train,
        candidate_count=config.max_candidates,
        seed=config.seed + 24,
    )
    chain_view = build_triplet_chain_view(
        candidates,
        max_distance=config.chain_max_distance,
        max_edges=config.max_chain_edges,
    )
    script_nodes = build_local_script_nodes(
        positions.train,
        candidates=candidates,
        config=_local_script_config(_fragment_config(config), horizon=max(config.horizons)),
    )
    adjacency = _chain_adjacency(chain_view)
    _apply_lag_quarantine(script_nodes, threshold=config.lag_negative_threshold)
    return RetryRuntime(
        candidates=candidates,
        chain_view=chain_view,
        script_nodes=script_nodes,
        chain_adjacency=adjacency,
        training_summary={
            "arm": "tg24_yoked_random_control",
            "generation": "matched SCRIPT shape from random train legal two-action schemas",
            "same_candidate_count_as_trace_mined_limit": config.max_candidates,
            "m3_update_count": 0,
            "m3_fast_weight_delta": 0.0,
            "positive_credit_count": 0,
            "negative_credit_count": 0,
            "neutral_credit_count": 0,
            "lag_quarantined_candidate_count": 0,
            "m4_consolidation_event_count": 0,
            "graded_tg24_credit_applied": False,
        },
    )


def _generate_yoked_random_candidates(
    train_fens: Iterable[str],
    *,
    candidate_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    fens = list(train_fens)
    rows: list[dict[str, Any]] = []
    attempts = 0
    max_attempts = max(200, candidate_count * 80)
    while len(rows) < candidate_count and attempts < max_attempts and fens:
        attempts += 1
        fen = rng.choice(fens)
        board = chess.Board(fen)
        if board.turn != chess.WHITE:
            continue
        first_moves = [move for move in board.legal_moves if board.piece_at(move.from_square) is not None]
        first_moves = [move for move in first_moves if board.piece_at(move.from_square).color == chess.WHITE]
        if not first_moves:
            continue
        before_features = extract_learner_features(board)
        first_move = rng.choice(first_moves)
        after_first = board.copy(stack=False)
        after_first.push(first_move)
        black_move = choose_black_reply(after_first)
        if black_move is None or black_move not in after_first.legal_moves:
            continue
        before_second = after_first.copy(stack=False)
        before_second.push(black_move)
        if before_second.turn != chess.WHITE:
            continue
        second_moves = [
            move
            for move in before_second.legal_moves
            if before_second.piece_at(move.from_square) is not None
            and before_second.piece_at(move.from_square).color == chess.WHITE
        ]
        if not second_moves:
            continue
        second_move = rng.choice(second_moves)
        after_second = before_second.copy(stack=False)
        after_second.push(second_move)
        after_features = extract_learner_features(after_second)
        deltas = {key: after_features[key] - before_features[key] for key in before_features}
        first_schema = _action_schema(board, first_move)
        second_schema = _action_schema(before_second, second_move)
        bucket_key = f"tg24_yoked_{len(rows)}_" + _script_bucket_key(before_features, first_schema, second_schema)
        rows.append(
            {
                "position_index": len(rows),
                "before_features": before_features,
                "after_features": after_features,
                "progress_deltas": deltas,
                "first_action_schema": first_schema,
                "second_action_schema": second_schema,
                "credit": 0.0,
                "bucket_key": bucket_key,
            }
        )
    exact_candidates = [
        _candidate_from_script_bucket(bucket_key=row["bucket_key"], rows=[row])
        for row in rows
    ]
    fragments = generalize_script_candidates_to_fragments(exact_candidates)
    for index, candidate in enumerate(fragments, start=1):
        candidate["candidate_key"] = f"tg24_yoked_random_{index:03d}"
        candidate["status"] = "tg24_yoked_random_control_not_spawned"
        candidate["rank"] = 10_000 + index
        candidate["selected_for_m5"] = False
        candidate["yoked_random_control"] = {
            "same_shape_as_trace_mined_script_fragment": True,
            "random_context_action_schema": True,
            "chooses_move_directly": False,
        }
        validate_learner_record(candidate)
    return fragments


def _evaluate_paired_graded(
    fens: Iterable[str],
    *,
    config: CurriculumRewardRecoveryConfig,
    retry_runtime: RetryRuntime,
    yoked_random_runtime: RetryRuntime,
    split: str,
    include_stage_slices: bool,
) -> dict[str, Any]:
    fens_tuple = tuple(fens)
    by_horizon: dict[str, Any] = {}
    for horizon in config.horizons:
        baseline = [
            _graded_playout(fen, arm="baseline", horizon=horizon, config=config, retry_runtime=None)
            for fen in fens_tuple
        ]
        retry = [
            _graded_playout(
                fen,
                arm="continuation_retry_on",
                horizon=horizon,
                config=config,
                retry_runtime=retry_runtime,
            )
            for fen in fens_tuple
        ]
        yoked_random = [
            _graded_playout(
                fen,
                arm="yoked_random_control",
                horizon=horizon,
                config=config,
                retry_runtime=yoked_random_runtime,
            )
            for fen in fens_tuple
        ]
        by_horizon[str(horizon)] = {
            "split": split,
            "baseline": _summarize_rollouts(baseline, arm="baseline", horizon=horizon, config=config),
            "continuation_retry_on": _summarize_rollouts(
                retry,
                arm="continuation_retry_on",
                horizon=horizon,
                config=config,
            ),
            "yoked_random_control": _summarize_rollouts(
                yoked_random,
                arm="yoked_random_control",
                horizon=horizon,
                config=config,
            ),
            "paired_deltas": {
                "baseline_vs_candidate_on": _graded_paired_delta(baseline, retry),
                "baseline_vs_yoked_random": _graded_paired_delta(baseline, yoked_random),
            },
            "safety_metrics": {
                "candidate_on": _safety_from_paired(baseline, retry),
                "yoked_random_control": _safety_from_paired(baseline, yoked_random),
            },
            "stage_slices": _stage_slices(baseline, retry, yoked_random) if include_stage_slices else {},
            "samples": {
                "baseline": baseline[: config.max_rollout_samples],
                "continuation_retry_on": retry[: config.max_rollout_samples],
                "yoked_random_control": yoked_random[: config.max_rollout_samples],
            },
        }
    return by_horizon


def _graded_playout(
    fen: str,
    *,
    arm: str,
    horizon: int,
    config: CurriculumRewardRecoveryConfig,
    retry_runtime: RetryRuntime | None,
    precision_gate: Any | None = None,
) -> dict[str, Any]:
    board = chess.Board(fen)
    initial_board = board.copy(stack=False)
    initial_features = extract_learner_features(initial_board)
    initial_box = box_min_side(initial_board)
    stage_info = _match_curriculum_stage(initial_board)
    active_script: dict[str, Any] | None = None
    requested_successors: list[str] = []
    position_counts = {_position_repetition_key(board): 1}
    white_action_counts: dict[str, int] = {}
    totals = _empty_chain_totals()
    lag_totals = _empty_lag_totals()
    retry_totals = _empty_retry_totals()
    precision_gate_totals = {
        "gate_request_count": 0,
        "gate_suppression_count": 0,
        "gate_confinement_suppression_count": 0,
        "gate_negative_progress_suppression_count": 0,
        "gate_rook_safety_suppression_count": 0,
    }
    box_trajectory = [initial_box]
    confinement_box_trajectory = [list(compute_confinement_box(initial_board))]
    tracked_feature_names = (
        "black_king_nearest_edge_distance",
        "black_reply_mobility",
        "white_king_to_black_king_distance",
        "white_rook_to_black_king_distance",
        "white_king_to_rook_distance",
        "is_check",
    )
    feature_trajectories = {
        name: [float(initial_features[name])]
        for name in tracked_feature_names
    }
    repetition_trajectory = [1]
    confinement_worsened_count = 0
    rook_attacked_count = 0
    rook_missing_count = 0
    check_count = int(initial_features["is_check"] > 0.0)
    illegal_moves = 0
    white_action_count = 0
    repeated_white_action_events = 0
    repetition_events = 0
    fivefold_repetition_count = 0
    changed_from_baseline = False
    final_outcome = "horizon_no_mate"
    final_ply = int(horizon)

    for ply in range(int(horizon)):
        terminal = classify_terminal_outcome(board)
        if terminal is not None:
            final_outcome = terminal
            final_ply = ply
            break
        baseline_move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        before = board.copy(stack=False)
        if baseline_move is None or baseline_move not in board.legal_moves:
            illegal_moves += 1
            final_outcome = "illegal_move"
            final_ply = ply
            break
        move = baseline_move
        selected_node: dict[str, Any] | None = None
        completed_node: dict[str, Any] | None = None
        if arm in {"continuation_retry_on", "yoked_random_control"} and board.turn == chess.WHITE and retry_runtime is not None:
            totals["chain_request_count"] += 1
            if requested_successors:
                totals["chained_successor_request_count"] += 1
            decision = choose_continuation_retry_action(
                board,
                script_nodes=retry_runtime.script_nodes,
                active_script=active_script,
                requested_successors=requested_successors,
                activation_max_distance=config.activation_max_distance,
                chain_request_bonus=config.chain_request_bonus,
                lag_negative_threshold=config.lag_negative_threshold,
                update_nodes=False,
                position_counts=position_counts,
            )
            for key in lag_totals:
                lag_totals[key] += int(decision["lag_counts"].get(key, 0))
            for key in retry_totals:
                retry_totals[key] += int(decision["retry_counts"].get(key, 0))
            if decision.get("aborted"):
                totals["chain_abort_count"] += 1
                active_script = None
                requested_successors = []
            elif decision["move"] is None:
                totals["baseline_fallback_count"] += 1
                totals["no_chain_activation_count"] += 1
                active_script = None
                requested_successors = []
            else:
                gate_result = None
                if precision_gate is not None:
                    precision_gate_totals["gate_request_count"] += 1
                    gate_result = precision_gate.evaluate(board, decision["move"], decision["node"])
                if gate_result is not None and gate_result["suppress"]:
                    precision_gate_totals["gate_suppression_count"] += 1
                    precision_gate_totals["gate_confinement_suppression_count"] += int(
                        gate_result["reason"] == "confinement_would_worsen"
                    )
                    precision_gate_totals["gate_negative_progress_suppression_count"] += int(
                        gate_result["reason"] == "negative_immediate_progress"
                    )
                    precision_gate_totals["gate_rook_safety_suppression_count"] += int(
                        gate_result["reason"] == "rook_safety_regression"
                    )
                    totals["baseline_fallback_count"] += 1
                    active_script = None
                    requested_successors = []
                else:
                    move = decision["move"]
                    selected_node = decision["node"]
                    totals["chain_step_count"] += 1
                    if decision["started"]:
                        totals["chain_start_count"] += 1
                        active_script = {"candidate_key": selected_node["candidate_key"]}
                        requested_successors = []
                    if decision["completed"]:
                        completed_node = selected_node
                        active_script = None
                    if move != baseline_move:
                        changed_from_baseline = True

        if before.turn == chess.WHITE:
            white_action_count += 1
            action_key = move.uci()
            if white_action_counts.get(action_key, 0) > 0:
                repeated_white_action_events += 1
                totals["repeated_white_action_events"] += 1
            white_action_counts[action_key] = white_action_counts.get(action_key, 0) + 1

        board.push(move)
        after_features = extract_learner_features(board)
        if after_features["rook_attacked_by_black"] > 0.0:
            rook_attacked_count += 1
        if after_features["rook_present"] <= 0.0:
            rook_missing_count += 1
        if did_box_grow(before, board):
            confinement_worsened_count += 1
        box_trajectory.append(box_min_side(board))
        confinement_box_trajectory.append(list(compute_confinement_box(board)))
        for name in tracked_feature_names:
            feature_trajectories[name].append(float(after_features[name]))
        check_count += int(after_features["is_check"] > 0.0)

        if before.turn == chess.WHITE and selected_node is not None:
            credit = _post_script_step_credit(before, board)
            if completed_node is not None:
                if _after_terminal_matches(board, completed_node["candidate"], config.after_max_distance):
                    totals["chain_completion_count"] += 1
                    totals["chain_after_confirm_count"] += 1
                    requested_successors = list(retry_runtime.chain_adjacency.get(completed_node["candidate_key"], []))
                    if requested_successors:
                        credit += 0.25
                else:
                    totals["chain_abort_count"] += 1
                    totals["chain_after_fail_count"] += 1
                    totals["chain_abort_loop_count"] += 1
                    requested_successors = []
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
            repetition_events += 1
            totals["repetition_events"] += 1
        position_counts[key] = position_counts.get(key, 0) + 1
        repetition_trajectory.append(position_counts[key])
        if position_counts[key] >= 5:
            fivefold_repetition_count += 1
            totals["fivefold_repetition_count"] += 1
    else:
        final_outcome = "mate" if board.is_checkmate() else "horizon_no_mate"

    final_features = extract_learner_features(board)
    non_terminal_progress = score_non_terminal_progress(
        initial_features=initial_features,
        final_features=final_features,
        initial_box=initial_box,
        final_box=box_trajectory[-1],
        confinement_worsened_count=confinement_worsened_count,
        repetition_events=repetition_events,
        repeated_white_action_events=repeated_white_action_events,
        rook_attacked_count=rook_attacked_count,
        rook_missing_count=rook_missing_count,
    )
    optimal_moves = stage_info["optimal_moves"]
    curriculum_optimal_excess = (
        max(0, white_action_count - int(optimal_moves)) if optimal_moves is not None else None
    )
    fallback_optimal = int(optimal_moves) if optimal_moves is not None else KRK_STAGES[-1].get_optimal_moves(initial_board)
    old_reward_component = krk_reward(
        won=final_outcome == "mate",
        move_count=white_action_count,
        optimal_moves=fallback_optimal,
        box_grew=confinement_worsened_count > 0,
        stalemate=final_outcome == "stalemate",
    )
    graded_credit = old_reward_component + non_terminal_progress
    return {
        "fen": fen,
        "arm": arm,
        "outcome": final_outcome,
        "plies": final_ply,
        "white_action_count": white_action_count,
        "changed_from_baseline": changed_from_baseline,
        "curriculum_diagnostic": stage_info,
        "curriculum_optimal_excess_moves": curriculum_optimal_excess,
        "old_curriculum_reward_component": old_reward_component,
        "old_reward_optimal_moves_used": fallback_optimal,
        "old_reward_exact_curriculum_match": optimal_moves is not None,
        "non_terminal_progress_delta": non_terminal_progress,
        "graded_credit_total": graded_credit,
        "stalemate": final_outcome == "stalemate",
        "rook_loss": final_outcome == "rook_loss",
        "rook_attacked_events": rook_attacked_count,
        "rook_missing_events": rook_missing_count,
        "confinement": {
            "box_min_side_start": initial_box,
            "box_min_side_end": box_trajectory[-1],
            "box_min_side_delta": box_trajectory[-1] - initial_box,
            "box_grew_or_confinement_worsened_count": confinement_worsened_count,
            "box_dimensions_start": confinement_box_trajectory[0],
            "box_dimensions_end": confinement_box_trajectory[-1],
            "trajectory": box_trajectory,
            "box_dimensions_trajectory": confinement_box_trajectory,
        },
        "generic_progress_trajectories": {
            "enemy_king_nearest_edge_distance": feature_trajectories["black_king_nearest_edge_distance"],
            "black_reply_mobility": feature_trajectories["black_reply_mobility"],
            "white_king_to_black_king_distance": feature_trajectories["white_king_to_black_king_distance"],
            "white_rook_to_black_king_distance": feature_trajectories["white_rook_to_black_king_distance"],
            "white_king_to_rook_distance": feature_trajectories["white_king_to_rook_distance"],
            "is_check": feature_trajectories["is_check"],
            "repetition_visit_count": repetition_trajectory,
        },
        "check_count": check_count,
        "check_rate": 0.0 if final_ply == 0 else round(check_count / max(1, final_ply), 6),
        "dtm_evaluation_only": None,
        "repetition_events": repetition_events,
        "fivefold_repetition_count": fivefold_repetition_count,
        "repeated_white_action_events": repeated_white_action_events,
        "white_unique_action_total": len(white_action_counts),
        "illegal_moves": illegal_moves,
        "chain": {key: totals[key] for key in sorted(totals)},
        "lag": {key: lag_totals[key] for key in sorted(lag_totals)},
        "retry": {key: retry_totals[key] for key in sorted(retry_totals)},
        "precision_gate": precision_gate_totals,
    }


def score_non_terminal_progress(
    *,
    initial_features: dict[str, float],
    final_features: dict[str, float],
    initial_box: int,
    final_box: int,
    confinement_worsened_count: int,
    repetition_events: int,
    repeated_white_action_events: int,
    rook_attacked_count: int,
    rook_missing_count: int,
) -> float:
    """Generic non-terminal progress score for diagnostics/credit instrumentation."""

    edge_progress = initial_features["black_king_nearest_edge_distance"] - final_features["black_king_nearest_edge_distance"]
    mobility_progress = initial_features["black_reply_mobility"] - final_features["black_reply_mobility"]
    king_coordination = initial_features["white_king_to_black_king_distance"] - final_features["white_king_to_black_king_distance"]
    rook_coordination = initial_features["white_rook_to_black_king_distance"] - final_features["white_rook_to_black_king_distance"]
    confinement_progress = float(initial_box - final_box)
    safety_penalty = (
        0.05 * confinement_worsened_count
        + 0.01 * repetition_events
        + 0.02 * repeated_white_action_events
        + 0.04 * rook_attacked_count
        + 0.50 * rook_missing_count
    )
    return round(
        0.08 * edge_progress
        + 0.01 * mobility_progress
        + 0.02 * king_coordination
        + 0.01 * rook_coordination
        + 0.04 * confinement_progress
        - safety_penalty,
        6,
    )


def _summarize_rollouts(
    rows: list[dict[str, Any]],
    *,
    arm: str,
    horizon: int,
    config: CurriculumRewardRecoveryConfig,
) -> dict[str, Any]:
    total = len(rows)
    mates = sum(1 for row in rows if row["outcome"] == "mate")
    exact_matches = [row for row in rows if row["old_reward_exact_curriculum_match"]]
    excess_values = [
        int(row["curriculum_optimal_excess_moves"])
        for row in exact_matches
        if row["curriculum_optimal_excess_moves"] is not None
    ]
    return {
        "arm": arm,
        "horizon": int(horizon),
        "total": total,
        "mates": mates,
        "conversion_rate": 0.0 if total == 0 else mates / total,
        "horizon_no_mate": sum(1 for row in rows if row["outcome"] == "horizon_no_mate"),
        "stalemates": sum(1 for row in rows if row["outcome"] == "stalemate"),
        "rook_losses": sum(1 for row in rows if row["outcome"] == "rook_loss"),
        "draws": sum(1 for row in rows if str(row["outcome"]).startswith("draw_")),
        "illegal_moves": sum(int(row["illegal_moves"]) for row in rows),
        "avg_plies": _avg(row["plies"] for row in rows),
        "avg_white_action_count": _avg(row["white_action_count"] for row in rows),
        "curriculum_exact_match_count": len(exact_matches),
        "avg_excess_moves_vs_curriculum_optimal_when_applicable": _avg(excess_values),
        "old_curriculum_reward_component_sum": round(sum(float(row["old_curriculum_reward_component"]) for row in rows), 6),
        "old_curriculum_reward_component_avg": _avg(row["old_curriculum_reward_component"] for row in rows),
        "non_terminal_progress_delta_sum": round(sum(float(row["non_terminal_progress_delta"]) for row in rows), 6),
        "non_terminal_progress_delta_avg": _avg(row["non_terminal_progress_delta"] for row in rows),
        "graded_credit_total_sum": round(sum(float(row["graded_credit_total"]) for row in rows), 6),
        "graded_credit_total_avg": _avg(row["graded_credit_total"] for row in rows),
        "box_grew_or_confinement_worsened_count": sum(
            int(row["confinement"]["box_grew_or_confinement_worsened_count"]) for row in rows
        ),
        "avg_box_min_side_delta": _avg(row["confinement"]["box_min_side_delta"] for row in rows),
        "repetition_events": sum(int(row["repetition_events"]) for row in rows),
        "fivefold_repetition_count": sum(int(row["fivefold_repetition_count"]) for row in rows),
        "repeated_white_action_events": sum(int(row["repeated_white_action_events"]) for row in rows),
        "rook_attacked_events": sum(int(row["rook_attacked_events"]) for row in rows),
        "rook_missing_events": sum(int(row["rook_missing_events"]) for row in rows),
        "check_count": sum(int(row["check_count"]) for row in rows),
        "avg_enemy_edge_distance_delta": _avg(
            _trajectory_delta(row, "enemy_king_nearest_edge_distance") for row in rows
        ),
        "avg_black_reply_mobility_delta": _avg(
            _trajectory_delta(row, "black_reply_mobility") for row in rows
        ),
        "avg_white_king_to_black_king_distance_delta": _avg(
            _trajectory_delta(row, "white_king_to_black_king_distance") for row in rows
        ),
        "avg_white_rook_to_black_king_distance_delta": _avg(
            _trajectory_delta(row, "white_rook_to_black_king_distance") for row in rows
        ),
        "avg_white_king_to_rook_distance_delta": _avg(
            _trajectory_delta(row, "white_king_to_rook_distance") for row in rows
        ),
        "changed_from_baseline_count": sum(1 for row in rows if row["changed_from_baseline"]),
        "precision_gate_request_count": sum(int(row.get("precision_gate", {}).get("gate_request_count", 0)) for row in rows),
        "precision_gate_suppression_count": sum(
            int(row.get("precision_gate", {}).get("gate_suppression_count", 0)) for row in rows
        ),
        "precision_gate_confinement_suppression_count": sum(
            int(row.get("precision_gate", {}).get("gate_confinement_suppression_count", 0)) for row in rows
        ),
        "precision_gate_negative_progress_suppression_count": sum(
            int(row.get("precision_gate", {}).get("gate_negative_progress_suppression_count", 0)) for row in rows
        ),
        "precision_gate_rook_safety_suppression_count": sum(
            int(row.get("precision_gate", {}).get("gate_rook_safety_suppression_count", 0)) for row in rows
        ),
        "m3_update_count": sum(int(row["chain"]["m3_update_count"]) for row in rows),
        "m3_fast_weight_delta_preview": round(
            sum(int(row["chain"]["m3_fast_weight_delta_scaled"]) for row in rows) / 1000.0,
            6,
        ),
        "m3_graded_credit_applied": False,
        "m4_consolidation_event_count": 0,
        "sample_cap": int(config.max_rollout_samples),
    }


def _graded_paired_delta(baseline: list[dict[str, Any]], candidate: list[dict[str, Any]]) -> dict[str, Any]:
    base_by_fen = {row["fen"]: row for row in baseline}
    candidate_by_fen = {row["fen"]: row for row in candidate}
    outcome_changed = 0
    candidate_succeeds_baseline_fails = 0
    candidate_fails_baseline_succeeds = 0
    graded_delta_sum = 0.0
    progress_delta_sum = 0.0
    old_reward_delta_sum = 0.0
    rook_loss_regressions = 0
    stalemate_regressions = 0
    confinement_regressions = 0
    repetition_delta = 0
    box_min_side_delta = 0
    illegal_delta = 0
    stalemate_delta = 0
    rook_loss_delta = 0
    mate_delta = 0
    changed_move_count = 0
    graded_deltas: list[float] = []
    progress_deltas: list[float] = []
    for fen, base in base_by_fen.items():
        cand = candidate_by_fen[fen]
        base_success = base["outcome"] == "mate"
        cand_success = cand["outcome"] == "mate"
        outcome_changed += int(base["outcome"] != cand["outcome"])
        candidate_succeeds_baseline_fails += int(cand_success and not base_success)
        candidate_fails_baseline_succeeds += int(base_success and not cand_success)
        graded_delta = float(cand["graded_credit_total"] - base["graded_credit_total"])
        progress_delta = float(cand["non_terminal_progress_delta"] - base["non_terminal_progress_delta"])
        graded_deltas.append(graded_delta)
        progress_deltas.append(progress_delta)
        graded_delta_sum += graded_delta
        progress_delta_sum += progress_delta
        old_reward_delta_sum += float(cand["old_curriculum_reward_component"] - base["old_curriculum_reward_component"])
        rook_loss_regressions += int(cand["outcome"] == "rook_loss" and base["outcome"] != "rook_loss")
        stalemate_regressions += int(cand["outcome"] == "stalemate" and base["outcome"] != "stalemate")
        confinement_regressions += int(
            cand["confinement"]["box_grew_or_confinement_worsened_count"]
            > base["confinement"]["box_grew_or_confinement_worsened_count"]
        )
        repetition_delta += int(cand["repetition_events"] - base["repetition_events"])
        box_min_side_delta += int(cand["confinement"]["box_min_side_delta"] - base["confinement"]["box_min_side_delta"])
        illegal_delta += int(cand["illegal_moves"] - base["illegal_moves"])
        stalemate_delta += int(cand["outcome"] == "stalemate") - int(base["outcome"] == "stalemate")
        rook_loss_delta += int(cand["outcome"] == "rook_loss") - int(base["outcome"] == "rook_loss")
        mate_delta += int(cand_success) - int(base_success)
        changed_move_count += int(cand["changed_from_baseline"])
    paired_count = len(graded_deltas)
    positive = sum(1 for value in graded_deltas if value > 0.0)
    negative = sum(1 for value in graded_deltas if value < 0.0)
    neutral = paired_count - positive - negative
    return {
        "paired_rollout_count": paired_count,
        "candidate_succeeds_where_baseline_fails": candidate_succeeds_baseline_fails,
        "candidate_fails_where_baseline_succeeds": candidate_fails_baseline_succeeds,
        "outcome_changed_count": outcome_changed,
        "changed_move_count": changed_move_count,
        "candidate_on_progress_mean": _avg(row["non_terminal_progress_delta"] for row in candidate),
        "candidate_off_progress_mean": _avg(row["non_terminal_progress_delta"] for row in baseline),
        "paired_progress_delta_mean": _avg(progress_deltas),
        "paired_progress_delta_std": round(pstdev(progress_deltas), 6) if len(progress_deltas) > 1 else 0.0,
        "paired_graded_delta_mean": _avg(graded_deltas),
        "paired_graded_delta_std": round(pstdev(graded_deltas), 6) if len(graded_deltas) > 1 else 0.0,
        "paired_mate_delta": mate_delta,
        "paired_old_reward_delta": round(old_reward_delta_sum, 6),
        "paired_box_min_side_delta": box_min_side_delta,
        "paired_box_escape_delta": confinement_regressions,
        "paired_repetition_delta": repetition_delta,
        "paired_rook_loss_delta": rook_loss_delta,
        "paired_illegal_delta": illegal_delta,
        "paired_stalemate_delta": stalemate_delta,
        "causal_effect_positive_count": positive,
        "causal_effect_negative_count": negative,
        "causal_effect_neutral_count": neutral,
        "graded_credit_delta_sum": round(graded_delta_sum, 6),
        "non_terminal_progress_delta_sum": round(progress_delta_sum, 6),
        "old_curriculum_reward_delta_sum": round(old_reward_delta_sum, 6),
        "rook_loss_regression_count": rook_loss_regressions,
        "stalemate_regression_count": stalemate_regressions,
        "confinement_regression_count": confinement_regressions,
        "repetition_event_delta": repetition_delta,
    }


def _safety_from_paired(baseline: list[dict[str, Any]], candidate: list[dict[str, Any]]) -> dict[str, int]:
    paired = _graded_paired_delta(baseline, candidate)
    return {
        "rook_loss_regression_count": int(paired["rook_loss_regression_count"]),
        "stalemate_regression_count": int(paired["stalemate_regression_count"]),
        "illegal_regression_count": max(0, int(paired["paired_illegal_delta"])),
        "confinement_regression_count": int(paired["confinement_regression_count"]),
        "protected_regression_count": (
            int(paired["rook_loss_regression_count"])
            + int(paired["stalemate_regression_count"])
            + max(0, int(paired["paired_illegal_delta"]))
        ),
    }


def _stage_slices(
    baseline: list[dict[str, Any]],
    candidate: list[dict[str, Any]],
    yoked_random: list[dict[str, Any]],
) -> dict[str, Any]:
    by_label: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for arm, rows in (
        ("baseline", baseline),
        ("continuation_retry_on", candidate),
        ("yoked_random_control", yoked_random),
    ):
        for row in rows:
            diagnostic = row["curriculum_diagnostic"]
            label = str(diagnostic.get("stage_name") or "unmatched_autogrowth_position")
            by_label.setdefault(
                label,
                {"baseline": [], "continuation_retry_on": [], "yoked_random_control": []},
            )[arm].append(row)
    slices: dict[str, Any] = {}
    for label, arms in sorted(by_label.items()):
        slices[label] = {
            "baseline_total": len(arms["baseline"]),
            "candidate_total": len(arms["continuation_retry_on"]),
            "yoked_random_total": len(arms["yoked_random_control"]),
            "baseline_mates": sum(1 for row in arms["baseline"] if row["outcome"] == "mate"),
            "candidate_mates": sum(1 for row in arms["continuation_retry_on"] if row["outcome"] == "mate"),
            "yoked_random_mates": sum(1 for row in arms["yoked_random_control"] if row["outcome"] == "mate"),
            "graded_credit_delta_sum": round(
                sum(row["graded_credit_total"] for row in arms["continuation_retry_on"])
                - sum(row["graded_credit_total"] for row in arms["baseline"]),
                6,
            ),
            "yoked_random_graded_credit_delta_sum": round(
                sum(row["graded_credit_total"] for row in arms["yoked_random_control"])
                - sum(row["graded_credit_total"] for row in arms["baseline"]),
                6,
            ),
            "diagnostic_only_not_learner_visible": True,
        }
    return slices


def _match_curriculum_stage(board: chess.Board) -> dict[str, Any]:
    placement = board.fen().split(" ")[0]
    for index, stage in enumerate(KRK_STAGES):
        for position_index, position in enumerate(stage.positions):
            if position.fen.split(" ")[0] == placement:
                return {
                    "matched": True,
                    "stage_index": index,
                    "stage_id": stage.stage_id,
                    "stage_name": stage.name,
                    "position_index": position_index,
                    "optimal_moves": position.optimal_moves,
                    "failure_condition": position.failure_condition,
                    "distance_to_mate": stage.distance_to_mate,
                    "diagnostic_only_not_learner_visible": True,
                }
    return {
        "matched": False,
        "stage_index": None,
        "stage_id": None,
        "stage_name": "unmatched_autogrowth_position",
        "position_index": None,
        "optimal_moves": None,
        "failure_condition": None,
        "distance_to_mate": None,
        "diagnostic_only_not_learner_visible": True,
    }


def _curriculum_probe_fens(per_stage: int) -> tuple[str, ...]:
    fens: list[str] = []
    for stage in KRK_STAGES:
        for position in stage.positions[: max(0, int(per_stage))]:
            fens.append(position.fen)
    return tuple(fens)


def _fragment_config(config: CurriculumRewardRecoveryConfig) -> FragmentChainCurriculumConfig:
    return FragmentChainCurriculumConfig(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
        min_support=config.min_support,
        max_candidates=config.max_candidates,
        horizons=config.horizons,
        min_sequence_credit=config.min_sequence_credit,
        activation_max_distance=config.activation_max_distance,
        after_max_distance=config.after_max_distance,
        chain_max_distance=config.chain_max_distance,
        max_chain_edges=config.max_chain_edges,
        chain_request_bonus=config.chain_request_bonus,
        eta_m3=config.eta_m3,
    )


def _audit_curriculum_use() -> dict[str, Any]:
    return {
        "curriculum_source": {
            "file": "src/recon_lite_chess/training/krk_curriculum.py",
            "recovered_mechanisms": [
                "KRK_STAGES staged positions",
                "KRKStagePosition.optimal_moves",
                "krk_reward hard move penalty",
                "box_min_side and did_box_grow confinement diagnostics",
                "stalemate penalty",
                "stage target win rates and progression scaffolding",
                "Full_KRK ramp positions",
            ],
        },
        "current_autogrowth_tg18_tg23_use": {
            "uses_krk_curriculum_reward_or_stage_generation": False,
            "statement": (
                "TG18-TG23 autogrowth runners use locked random KRK position generation, "
                "generic learner features, baseline/retry rollout metrics, LAG/retry/sibling "
                "counts, and mate/stalemate/rook-loss/repetition outcomes. They do not call "
                "krk_reward(), generate_krk_curriculum_position(), KRK_STAGES, box_min_side(), "
                "or did_box_grow() in their runtime evaluation loops."
            ),
            "audited_paths": [
                "src/recon_lite_chess/autogrowth/fragment_chain_curriculum.py",
                "src/recon_lite_chess/autogrowth/lag_terminals.py",
                "src/recon_lite_chess/autogrowth/continuation_retry.py",
                "src/recon_lite_chess/autogrowth/retry_edges.py",
                "src/recon_lite_chess/autogrowth/retry_diagnostics.py",
                "src/recon_lite_chess/autogrowth/retry_candidate_expansion.py",
            ],
        },
        "existing_non_autogrowth_uses": [
            {
                "path": "scripts/test_15_games.py",
                "use": "imports KRK_STAGES for old stage smoke games",
            },
            {
                "path": "tests/test_krk_triplet_pipeline.py",
                "use": "tests older staged triplet pipeline command/config plumbing",
            },
            {
                "path": "tests/test_krk_landmarks.py",
                "use": "tests older landmark/curriculum stage selection utilities",
            },
            {
                "path": "src/recon_lite_chess/krk_strategy.py",
                "use": "uses predicate box_min_side helpers for predefined KRK strategy scoring",
            },
        ],
        "tg24_integration_boundary": {
            "stage_labels_are_diagnostics_only": True,
            "curriculum_labels_are_learner_visible": False,
            "runtime_tablebase_or_dtm_move_source": False,
            "handcoded_phase_control_reintroduced": False,
        },
    }


def _decision(*, config: CurriculumRewardRecoveryConfig, heldout_metrics: dict[str, Any]) -> dict[str, Any]:
    primary = str(config.horizons[0])
    primary_metrics = heldout_metrics[primary]
    paired = primary_metrics["paired_deltas"]["baseline_vs_candidate_on"]
    yoked_paired = primary_metrics["paired_deltas"]["baseline_vs_yoked_random"]
    baseline = primary_metrics["baseline"]
    candidate = primary_metrics["continuation_retry_on"]
    safety = primary_metrics["safety_metrics"]["candidate_on"]
    trace_beats_yoked = paired["graded_credit_delta_sum"] > yoked_paired["graded_credit_delta_sum"]
    instrument_ready = (
        "non_terminal_progress_delta_avg" in baseline
        and "old_curriculum_reward_component_avg" in baseline
        and paired["rook_loss_regression_count"] >= 0
        and paired["paired_rollout_count"] == baseline["total"]
    )
    continue_mechanism = (
        instrument_ready
        and paired["graded_credit_delta_sum"] > 0.0
        and trace_beats_yoked
        and safety["protected_regression_count"] == 0
    )
    return {
        "status": "tg24_instrument_ready" if instrument_ready else "tg24_instrument_incomplete",
        "continue_mechanism": continue_mechanism,
        "falsifies_current_candidate_mechanism": (
            instrument_ready
            and (
                paired["graded_credit_delta_sum"] <= 0.0
                or yoked_paired["graded_credit_delta_sum"] >= paired["graded_credit_delta_sum"]
            )
        ),
        "primary_horizon": int(config.horizons[0]),
        "baseline_primary_mates": baseline["mates"],
        "candidate_primary_mates": candidate["mates"],
        "candidate_conversion_delta": candidate["mates"] - baseline["mates"],
        "graded_credit_delta_sum": paired["graded_credit_delta_sum"],
        "non_terminal_progress_delta_sum": paired["non_terminal_progress_delta_sum"],
        "old_curriculum_reward_delta_sum": paired["old_curriculum_reward_delta_sum"],
        "yoked_random_graded_credit_delta_sum": yoked_paired["graded_credit_delta_sum"],
        "trace_mined_beats_yoked_random": trace_beats_yoked,
        "candidate_rook_loss_regressions": paired["rook_loss_regression_count"],
        "candidate_stalemate_regressions": paired["stalemate_regression_count"],
        "candidate_confinement_regressions": paired["confinement_regression_count"],
        "curriculum_reward_recovered_for_diagnostics": True,
        "non_win_reward_no_longer_flat_in_tg24_metrics": True,
        "adds_retry_candidates": False,
        "behavior_change_from_graded_evaluator": False,
        "m3_graded_credit_applied_in_tg24": False,
        "m3_training_confirmation_split_enforced": True,
        "paired_rollouts_enabled": True,
        "yoked_random_control_enabled": True,
        "m4_consolidation_event_count": 0,
        "next_recommended_checkpoint": (
            "Use TG24 graded credit to train/freeze one local precision gate, then confirm with M3 frozen "
            "before any M4 promotion."
        ),
    }


def _validated_generic_credit_record() -> dict[str, Any]:
    record = {
        "before_features": {"black_king_nearest_edge_distance": 2.0},
        "after_features": {"black_king_nearest_edge_distance": 1.0},
        "credit": {"non_terminal_progress_delta": 0.08},
    }
    validate_learner_record(record)
    return record


def _avg(values: Iterable[int | float | None]) -> float | None:
    concrete = [float(value) for value in values if value is not None]
    if not concrete:
        return None
    return round(sum(concrete) / len(concrete), 6)


def _trajectory_delta(row: dict[str, Any], key: str) -> float | None:
    trajectory = row["generic_progress_trajectories"].get(key, [])
    if not trajectory:
        return None
    return float(trajectory[-1] - trajectory[0])


def _trace_mined_vs_yoked_random(primary_metrics: dict[str, Any]) -> dict[str, Any]:
    trace = primary_metrics["paired_deltas"]["baseline_vs_candidate_on"]
    yoked = primary_metrics["paired_deltas"]["baseline_vs_yoked_random"]
    trace_safety = primary_metrics["safety_metrics"]["candidate_on"]
    yoked_safety = primary_metrics["safety_metrics"]["yoked_random_control"]
    return {
        "status": "implemented",
        "same_candidate_budget": True,
        "same_candidate_shape_class": "SCRIPT fragment with two ACTION schemas and local TERMINAL conditions",
        "trace_mined_paired_rollouts": trace["paired_rollout_count"],
        "yoked_random_paired_rollouts": yoked["paired_rollout_count"],
        "trace_mined_graded_credit_delta_sum": trace["graded_credit_delta_sum"],
        "yoked_random_graded_credit_delta_sum": yoked["graded_credit_delta_sum"],
        "trace_mined_progress_delta_sum": trace["non_terminal_progress_delta_sum"],
        "yoked_random_progress_delta_sum": yoked["non_terminal_progress_delta_sum"],
        "trace_mined_mate_delta": trace["paired_mate_delta"],
        "yoked_random_mate_delta": yoked["paired_mate_delta"],
        "trace_mined_protected_regressions": trace_safety["protected_regression_count"],
        "yoked_random_protected_regressions": yoked_safety["protected_regression_count"],
        "trace_mined_beats_yoked_random_on_graded_credit": (
            trace["graded_credit_delta_sum"] > yoked["graded_credit_delta_sum"]
        ),
    }

"""TG20 local continuation retry after LAG-suppressed script completion."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from .evaluate import (
    ArmMetrics,
    choose_black_reply,
    choose_white_baseline_move,
    classify_terminal_outcome,
    evaluate_arm,
    _position_repetition_key,
)
from .fragment_chain_curriculum import (
    FragmentChainCurriculumConfig,
    FragmentChainMetrics,
    _chain_adjacency,
    _chain_result,
    _empty_chain_totals,
    _generate_fragment_candidates,
    _inert_candidate_outcomes,
    _local_script_config,
    _record_chain_credit,
    _script_node_by_key,
)
from .lag_terminals import (
    LAG_FEATURES,
    LagFragmentChainMetrics,
    evaluate_lag_fragment_chain_arm,
    evaluate_lag_terminal,
    _after_terminal_matches,
    _apply_lag_quarantine,
    _chain_config,
    _empty_lag_totals,
    _lag_node_selectable,
    _merge_lag_counts,
    _record_lag_negative,
)
from .positions import KRKPositionSet, generate_position_sets
from .sandbox import _before_condition_matches, _paired_delta, _safety_counts
from .script_candidates import (
    build_local_script_nodes,
    _first_matching_move,
    _post_script_step_credit,
)
from .topological_growth import build_triplet_chain_view


@dataclass(frozen=True)
class ContinuationRetryConfig:
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


@dataclass(frozen=True)
class ContinuationRetryMetrics:
    chain: FragmentChainMetrics
    lag_request_count: int
    lag_trigger_count: int
    lag_suppression_count: int
    lag_rook_threat_delta_count: int
    lag_rook_missing_delta_count: int
    lag_repetition_delta_count: int
    lag_quarantined_candidate_count: int
    retry_request_count: int
    retry_success_count: int
    retry_no_local_sibling_count: int
    retry_suppressed_active_completion_count: int
    retry_sibling_lag_suppression_count: int

    def to_dict(self) -> dict[str, Any]:
        payload = self.chain.to_dict()
        payload.update(
            {
                "lag_request_count": self.lag_request_count,
                "lag_trigger_count": self.lag_trigger_count,
                "lag_suppression_count": self.lag_suppression_count,
                "lag_rook_threat_delta_count": self.lag_rook_threat_delta_count,
                "lag_rook_missing_delta_count": self.lag_rook_missing_delta_count,
                "lag_repetition_delta_count": self.lag_repetition_delta_count,
                "lag_quarantined_candidate_count": self.lag_quarantined_candidate_count,
                "retry_request_count": self.retry_request_count,
                "retry_success_count": self.retry_success_count,
                "retry_no_local_sibling_count": self.retry_no_local_sibling_count,
                "retry_suppressed_active_completion_count": self.retry_suppressed_active_completion_count,
                "retry_sibling_lag_suppression_count": self.retry_sibling_lag_suppression_count,
            }
        )
        return payload


@dataclass(frozen=True)
class ContinuationRetryResult:
    config: ContinuationRetryConfig
    positions: KRKPositionSet
    candidates: list[dict[str, Any]]
    chain_view: dict[str, Any]
    trained_nodes: list[dict[str, Any]]
    training_metrics: ContinuationRetryMetrics
    baseline_metrics: dict[str, ArmMetrics]
    sham_metrics: dict[str, ArmMetrics]
    no_lag_metrics: dict[str, FragmentChainMetrics]
    lag_metrics: dict[str, LagFragmentChainMetrics]
    retry_metrics: dict[str, ContinuationRetryMetrics]
    paired_deltas: dict[str, dict[str, int]]
    safety: dict[str, dict[str, int]]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg20_continuation_retry.v0",
            "config": {
                **asdict(self.config),
                "horizons": list(self.config.horizons),
                "lag_features": list(LAG_FEATURES),
            },
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "local_recon_structure": {
                "parent_node_type": "SCRIPT",
                "lag_node_type": "TERMINAL",
                "retry_scope": "same local SCRIPT parent after active completion inhibition",
                "relation_types": ["SUB", "POR", "SUR", "RET"],
                "move_choice_mediated_by_local_script_nodes": True,
                "retry_chooses_only_among_local_sibling_scripts": True,
                "direct_move_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "selector_behavior_enabled": False,
            },
            "candidates": self.candidates,
            "triplet_chain_view": self.chain_view,
            "trained_nodes": [
                {
                    "cell": node["cell"].to_dict(),
                    "local_weight": node["local_weight"],
                    "learner_visible": node["learner_visible"],
                    "diagnostics": node["diagnostics"],
                }
                for node in self.trained_nodes
            ],
            "arms": {
                "training_continuation_retry": self.training_metrics.to_dict(),
                "baseline": {str(horizon): metrics.to_dict() for horizon, metrics in self.baseline_metrics.items()},
                "sham_fragment_chain": {str(horizon): metrics.to_dict() for horizon, metrics in self.sham_metrics.items()},
                "real_fragment_chain_no_lag": {str(horizon): metrics.to_dict() for horizon, metrics in self.no_lag_metrics.items()},
                "real_fragment_chain_lag_only": {str(horizon): metrics.to_dict() for horizon, metrics in self.lag_metrics.items()},
                "real_fragment_chain_lag_retry": {str(horizon): metrics.to_dict() for horizon, metrics in self.retry_metrics.items()},
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


def run_continuation_retry_experiment(
    *,
    config: ContinuationRetryConfig,
    positions: KRKPositionSet | None = None,
) -> ContinuationRetryResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    chain_config = _chain_config(_lag_compatible_config(config))
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
        arm="training_continuation_retry",
    )
    no_lag_script_nodes = copy.deepcopy(script_nodes)
    lag_only_script_nodes = copy.deepcopy(script_nodes)
    _apply_lag_quarantine(script_nodes, threshold=config.lag_negative_threshold)
    _apply_lag_quarantine(lag_only_script_nodes, threshold=config.lag_negative_threshold)

    from .fragment_chain_curriculum import evaluate_fragment_chain_arm

    heldout = list(positions.heldout)
    baseline_metrics: dict[str, ArmMetrics] = {}
    sham_metrics: dict[str, ArmMetrics] = {}
    no_lag_metrics: dict[str, FragmentChainMetrics] = {}
    lag_metrics: dict[str, LagFragmentChainMetrics] = {}
    retry_metrics: dict[str, ContinuationRetryMetrics] = {}
    paired_deltas: dict[str, dict[str, int]] = {}
    safety: dict[str, dict[str, int]] = {}

    for horizon in config.horizons:
        baseline_metric, baseline_outcomes = evaluate_arm(heldout, arm="baseline", horizon=horizon)
        sham_metric, sham_outcomes = evaluate_arm(heldout, arm="sham_growth", horizon=horizon)
        no_lag_metric, no_lag_outcomes = evaluate_fragment_chain_arm(
            heldout,
            script_nodes=no_lag_script_nodes,
            chain_adjacency=adjacency,
            horizon=horizon,
            activation_max_distance=config.activation_max_distance,
            after_max_distance=config.after_max_distance,
            chain_request_bonus=config.chain_request_bonus,
            eta_m3=config.eta_m3,
            update_nodes=False,
            arm="real_fragment_chain_no_lag",
        )
        lag_metric, lag_outcomes = evaluate_lag_fragment_chain_arm(
            heldout,
            script_nodes=lag_only_script_nodes,
            chain_adjacency=adjacency,
            horizon=horizon,
            activation_max_distance=config.activation_max_distance,
            after_max_distance=config.after_max_distance,
            chain_request_bonus=config.chain_request_bonus,
            eta_m3=config.eta_m3,
            lag_negative_threshold=config.lag_negative_threshold,
            update_nodes=False,
            arm="real_fragment_chain_lag_only",
        )
        retry_metric, retry_outcomes = evaluate_continuation_retry_arm(
            heldout,
            script_nodes=script_nodes,
            chain_adjacency=adjacency,
            horizon=horizon,
            activation_max_distance=config.activation_max_distance,
            after_max_distance=config.after_max_distance,
            chain_request_bonus=config.chain_request_bonus,
            eta_m3=config.eta_m3,
            lag_negative_threshold=config.lag_negative_threshold,
            update_nodes=False,
            arm="real_fragment_chain_lag_retry",
        )
        key = str(horizon)
        baseline_metrics[key] = baseline_metric
        sham_metrics[key] = sham_metric
        no_lag_metrics[key] = no_lag_metric
        lag_metrics[key] = lag_metric
        retry_metrics[key] = retry_metric
        paired_deltas[f"baseline_vs_retry_h{key}"] = _paired_delta(baseline_outcomes, retry_outcomes)
        paired_deltas[f"lag_only_vs_retry_h{key}"] = _paired_delta(lag_outcomes, retry_outcomes)
        paired_deltas[f"baseline_vs_no_lag_h{key}"] = _paired_delta(baseline_outcomes, no_lag_outcomes)
        paired_deltas[f"sham_vs_retry_h{key}"] = _paired_delta(_inert_candidate_outcomes(sham_outcomes), retry_outcomes)
        safety[f"retry_h{key}"] = _safety_counts(baseline_outcomes, retry_outcomes)
        safety[f"lag_only_h{key}"] = _safety_counts(baseline_outcomes, lag_outcomes)
        safety[f"no_lag_h{key}"] = _safety_counts(baseline_outcomes, no_lag_outcomes)
        safety[f"sham_h{key}"] = _safety_counts(baseline_outcomes, _inert_candidate_outcomes(sham_outcomes))

    decision = _continuation_retry_decision(
        config=config,
        training_metrics=training_metrics,
        baseline_metrics=baseline_metrics,
        lag_metrics=lag_metrics,
        retry_metrics=retry_metrics,
        safety=safety,
    )
    return ContinuationRetryResult(
        config=config,
        positions=positions,
        candidates=candidates,
        chain_view=chain_view,
        trained_nodes=script_nodes,
        training_metrics=training_metrics,
        baseline_metrics=baseline_metrics,
        sham_metrics=sham_metrics,
        no_lag_metrics=no_lag_metrics,
        lag_metrics=lag_metrics,
        retry_metrics=retry_metrics,
        paired_deltas=paired_deltas,
        safety=safety,
        decision=decision,
    )


def evaluate_continuation_retry_arm(
    fens: Iterable[str],
    *,
    script_nodes: list[dict[str, Any]],
    chain_adjacency: dict[str, list[str]],
    horizon: int,
    activation_max_distance: float,
    after_max_distance: float,
    chain_request_bonus: float,
    eta_m3: float,
    lag_negative_threshold: int,
    update_nodes: bool,
    arm: str,
) -> tuple[ContinuationRetryMetrics, list[dict[str, Any]]]:
    outcomes: list[dict[str, Any]] = []
    counts = {"mate": 0, "horizon_no_mate": 0, "stalemate": 0, "rook_loss": 0, "illegal_move": 0, "other_failure": 0}
    draw_reasons: dict[str, int] = {}
    totals = _empty_chain_totals()
    lag_totals = _empty_lag_totals()
    retry_totals = _empty_retry_totals()
    for fen in fens:
        result = _retry_chain_playout(
            fen,
            script_nodes=script_nodes,
            chain_adjacency=chain_adjacency,
            horizon=horizon,
            activation_max_distance=activation_max_distance,
            after_max_distance=after_max_distance,
            chain_request_bonus=chain_request_bonus,
            eta_m3=eta_m3,
            lag_negative_threshold=lag_negative_threshold,
            update_nodes=update_nodes,
        )
        outcome = str(result["outcome"])
        if outcome.startswith("draw_"):
            draw_reasons[outcome] = draw_reasons.get(outcome, 0) + 1
        else:
            counts[outcome] = counts.get(outcome, 0) + 1
        for key in totals:
            totals[key] += int(result[key])
        for key in lag_totals:
            lag_totals[key] += int(result[key])
        for key in retry_totals:
            retry_totals[key] += int(result[key])
        outcomes.append({"fen": fen, **result})
    chain = FragmentChainMetrics(
        arm=arm,
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
        max_plies=counts["horizon_no_mate"],
        chain_request_count=totals["chain_request_count"],
        chain_start_count=totals["chain_start_count"],
        chain_step_count=totals["chain_step_count"],
        chain_completion_count=totals["chain_completion_count"],
        chain_abort_count=totals["chain_abort_count"],
        chain_after_confirm_count=totals["chain_after_confirm_count"],
        chain_after_fail_count=totals["chain_after_fail_count"],
        chained_successor_request_count=totals["chained_successor_request_count"],
        chained_successor_start_count=totals["chained_successor_start_count"],
        baseline_fallback_count=totals["baseline_fallback_count"],
        no_chain_activation_count=totals["no_chain_activation_count"],
        repeated_local_chain_loop_count=totals["repeated_local_chain_loop_count"],
        repeated_white_action_events=totals["repeated_white_action_events"],
        repetition_events=totals["repetition_events"],
        fivefold_repetition_count=totals["fivefold_repetition_count"],
        chain_abort_loop_count=totals["chain_abort_loop_count"],
        baseline_fallback_loop_count=totals["baseline_fallback_loop_count"],
        positive_credit_count=totals["positive_credit_count"],
        negative_credit_count=totals["negative_credit_count"],
        neutral_credit_count=totals["neutral_credit_count"],
        m3_update_count=totals["m3_update_count"],
        m3_fast_weight_delta=totals["m3_fast_weight_delta_scaled"] / 1000.0,
        m4_consolidation_event_count=0,
    )
    lag_totals["lag_quarantined_candidate_count"] = sum(
        1 for node in script_nodes if int(node["diagnostics"].get("lag_negative_training_count", 0)) >= int(lag_negative_threshold)
    )
    return ContinuationRetryMetrics(chain=chain, **lag_totals, **retry_totals), outcomes


def choose_continuation_retry_action(
    board: chess.Board,
    *,
    script_nodes: list[dict[str, Any]],
    active_script: dict[str, Any] | None,
    requested_successors: list[str],
    activation_max_distance: float,
    chain_request_bonus: float,
    lag_negative_threshold: int,
    update_nodes: bool,
    position_counts: dict[str, int],
) -> dict[str, Any]:
    lag_counts = _empty_lag_totals()
    retry_counts = _empty_retry_totals()
    if active_script is not None:
        active_key = active_script["candidate_key"]
        node = _script_node_by_key(script_nodes, active_key)
        if node is not None and _lag_node_selectable(node, lag_negative_threshold):
            move = _first_matching_move(board, node["candidate"]["script_plan"]["actions"][1])
            if move is not None:
                lag_counts["lag_request_count"] += 1
                lag = evaluate_lag_terminal(board, move, position_counts=position_counts)
                _merge_lag_counts(lag_counts, lag)
                if not lag["inhibits"]:
                    return _decision(move=move, node=node, started=False, completed=True, lag_counts=lag_counts, retry_counts=retry_counts)
                retry_counts["retry_suppressed_active_completion_count"] += 1
                if update_nodes:
                    _record_lag_negative(node, sibling_action=move.uci())
        retry_counts["retry_request_count"] += 1
        retry = _choose_lag_start_action(
            board,
            script_nodes=script_nodes,
            requested_successors=[],
            activation_max_distance=activation_max_distance,
            chain_request_bonus=chain_request_bonus,
            lag_negative_threshold=lag_negative_threshold,
            update_nodes=update_nodes,
            position_counts=position_counts,
            exclude_candidate_key=active_key,
        )
        _merge_lag_counts(lag_counts, retry["lag_counts"])
        retry_counts["retry_sibling_lag_suppression_count"] += int(retry["lag_counts"]["lag_suppression_count"])
        if retry["move"] is None:
            retry_counts["retry_no_local_sibling_count"] += 1
            return _decision(move=None, node=None, started=False, completed=False, aborted=True, lag_counts=lag_counts, retry_counts=retry_counts)
        retry_counts["retry_success_count"] += 1
        return _decision(move=retry["move"], node=retry["node"], started=True, completed=False, lag_counts=lag_counts, retry_counts=retry_counts)

    retry = _choose_lag_start_action(
        board,
        script_nodes=script_nodes,
        requested_successors=requested_successors,
        activation_max_distance=activation_max_distance,
        chain_request_bonus=chain_request_bonus,
        lag_negative_threshold=lag_negative_threshold,
        update_nodes=update_nodes,
        position_counts=position_counts,
        exclude_candidate_key=None,
    )
    return _decision(
        move=retry["move"],
        node=retry["node"],
        started=retry["move"] is not None,
        completed=False,
        lag_counts=retry["lag_counts"],
        retry_counts=retry_counts,
    )


def _retry_chain_playout(
    fen: str,
    *,
    script_nodes: list[dict[str, Any]],
    chain_adjacency: dict[str, list[str]],
    horizon: int,
    activation_max_distance: float,
    after_max_distance: float,
    chain_request_bonus: float,
    eta_m3: float,
    lag_negative_threshold: int,
    update_nodes: bool,
) -> dict[str, Any]:
    board = chess.Board(fen)
    active_script: dict[str, Any] | None = None
    requested_successors: list[str] = []
    position_counts = {_position_repetition_key(board): 1}
    white_action_counts: dict[str, int] = {}
    totals = _empty_chain_totals()
    lag_totals = _empty_lag_totals()
    retry_totals = _empty_retry_totals()
    illegal_moves = 0
    changed_position = False
    for ply in range(int(horizon)):
        terminal = classify_terminal_outcome(board)
        if terminal is not None:
            return _retry_chain_result(
                outcome=terminal,
                plies=ply,
                illegal_moves=illegal_moves,
                changed_position=changed_position,
                **totals,
                **lag_totals,
                **retry_totals,
            )
        baseline_move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        before = board.copy(stack=False)
        if baseline_move is None or baseline_move not in board.legal_moves:
            illegal_moves += 1
            return _retry_chain_result(
                outcome="illegal_move",
                plies=ply,
                illegal_moves=illegal_moves,
                changed_position=changed_position,
                **totals,
                **lag_totals,
                **retry_totals,
            )
        move = baseline_move
        selected_node: dict[str, Any] | None = None
        completed_node: dict[str, Any] | None = None
        if board.turn == chess.WHITE:
            totals["chain_request_count"] += 1
            if requested_successors:
                totals["chained_successor_request_count"] += 1
            decision = choose_continuation_retry_action(
                board,
                script_nodes=script_nodes,
                active_script=active_script,
                requested_successors=requested_successors,
                activation_max_distance=activation_max_distance,
                chain_request_bonus=chain_request_bonus,
                lag_negative_threshold=lag_negative_threshold,
                update_nodes=update_nodes,
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
                    changed_position = True
        if before.turn == chess.WHITE:
            action_key = move.uci()
            if white_action_counts.get(action_key, 0) > 0:
                totals["repeated_white_action_events"] += 1
            white_action_counts[action_key] = white_action_counts.get(action_key, 0) + 1
        board.push(move)
        if before.turn == chess.WHITE and selected_node is not None:
            credit = _post_script_step_credit(before, board)
            if completed_node is not None:
                if _after_terminal_matches(board, completed_node["candidate"], after_max_distance):
                    totals["chain_completion_count"] += 1
                    totals["chain_after_confirm_count"] += 1
                    requested_successors = list(chain_adjacency.get(completed_node["candidate_key"], []))
                    if requested_successors:
                        credit += 0.25
                else:
                    totals["chain_abort_count"] += 1
                    totals["chain_after_fail_count"] += 1
                    totals["chain_abort_loop_count"] += 1
                    requested_successors = []
            _record_chain_credit(selected_node, credit=credit, eta_m3=eta_m3, update_node=update_nodes)
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
        if position_counts[key] >= 5:
            totals["fivefold_repetition_count"] += 1
    return _retry_chain_result(
        outcome="mate" if board.is_checkmate() else "horizon_no_mate",
        plies=int(horizon),
        illegal_moves=illegal_moves,
        changed_position=changed_position,
        **totals,
        **lag_totals,
        **retry_totals,
    )


def _choose_lag_start_action(
    board: chess.Board,
    *,
    script_nodes: list[dict[str, Any]],
    requested_successors: list[str],
    activation_max_distance: float,
    chain_request_bonus: float,
    lag_negative_threshold: int,
    update_nodes: bool,
    position_counts: dict[str, int],
    exclude_candidate_key: str | None,
) -> dict[str, Any]:
    lag_counts = _empty_lag_totals()
    requested = set(requested_successors)
    options: list[tuple[float, int, str, dict[str, Any], chess.Move]] = []
    for node in script_nodes:
        if exclude_candidate_key is not None and node["candidate_key"] == exclude_candidate_key:
            continue
        if not _lag_node_selectable(node, lag_negative_threshold):
            continue
        candidate = node["candidate"]
        if not _before_condition_matches(board, candidate, activation_max_distance):
            continue
        move = _first_matching_move(board, candidate["script_plan"]["actions"][0])
        if move is None:
            continue
        lag_counts["lag_request_count"] += 1
        lag = evaluate_lag_terminal(board, move, position_counts=position_counts)
        _merge_lag_counts(lag_counts, lag)
        if lag["inhibits"]:
            if update_nodes:
                _record_lag_negative(node, sibling_action=move.uci())
            continue
        score = float(node["local_weight"])
        if node["candidate_key"] in requested:
            score += float(chain_request_bonus)
        options.append((score, -int(node["rank"]), move.uci(), node, move))
    if not options:
        return {"move": None, "node": None, "lag_counts": lag_counts}
    options.sort(reverse=True)
    _score, _rank, _uci, node, move = options[0]
    return {"move": move, "node": node, "lag_counts": lag_counts}


def _decision(
    *,
    move: chess.Move | None,
    node: dict[str, Any] | None,
    started: bool,
    completed: bool,
    lag_counts: dict[str, int],
    retry_counts: dict[str, int],
    aborted: bool = False,
) -> dict[str, Any]:
    return {
        "move": move,
        "node": node,
        "started": started,
        "completed": completed,
        "aborted": aborted,
        "lag_counts": lag_counts,
        "retry_counts": retry_counts,
    }


def _empty_retry_totals() -> dict[str, int]:
    return {
        "retry_request_count": 0,
        "retry_success_count": 0,
        "retry_no_local_sibling_count": 0,
        "retry_suppressed_active_completion_count": 0,
        "retry_sibling_lag_suppression_count": 0,
    }


def _retry_chain_result(
    *,
    retry_request_count: int,
    retry_success_count: int,
    retry_no_local_sibling_count: int,
    retry_suppressed_active_completion_count: int,
    retry_sibling_lag_suppression_count: int,
    lag_request_count: int,
    lag_trigger_count: int,
    lag_suppression_count: int,
    lag_rook_threat_delta_count: int,
    lag_rook_missing_delta_count: int,
    lag_repetition_delta_count: int,
    lag_quarantined_candidate_count: int,
    **kwargs: Any,
) -> dict[str, Any]:
    payload = _chain_result(**kwargs)
    payload.update(
        {
            "lag_request_count": lag_request_count,
            "lag_trigger_count": lag_trigger_count,
            "lag_suppression_count": lag_suppression_count,
            "lag_rook_threat_delta_count": lag_rook_threat_delta_count,
            "lag_rook_missing_delta_count": lag_rook_missing_delta_count,
            "lag_repetition_delta_count": lag_repetition_delta_count,
            "lag_quarantined_candidate_count": lag_quarantined_candidate_count,
            "retry_request_count": retry_request_count,
            "retry_success_count": retry_success_count,
            "retry_no_local_sibling_count": retry_no_local_sibling_count,
            "retry_suppressed_active_completion_count": retry_suppressed_active_completion_count,
            "retry_sibling_lag_suppression_count": retry_sibling_lag_suppression_count,
        }
    )
    return payload


def _lag_compatible_config(config: ContinuationRetryConfig) -> Any:
    return type(
        "LagCompatibleConfig",
        (),
        {
            "seed": config.seed,
            "train_count": config.train_count,
            "heldout_weakness_count": config.heldout_weakness_count,
            "heldout_broader_count": config.heldout_broader_count,
            "min_support": config.min_support,
            "max_candidates": config.max_candidates,
            "horizons": config.horizons,
            "min_sequence_credit": config.min_sequence_credit,
            "activation_max_distance": config.activation_max_distance,
            "after_max_distance": config.after_max_distance,
            "chain_max_distance": config.chain_max_distance,
            "max_chain_edges": config.max_chain_edges,
            "chain_request_bonus": config.chain_request_bonus,
            "eta_m3": config.eta_m3,
        },
    )()


def _continuation_retry_decision(
    *,
    config: ContinuationRetryConfig,
    training_metrics: ContinuationRetryMetrics,
    baseline_metrics: dict[str, ArmMetrics],
    lag_metrics: dict[str, LagFragmentChainMetrics],
    retry_metrics: dict[str, ContinuationRetryMetrics],
    safety: dict[str, dict[str, int]],
) -> dict[str, Any]:
    primary_key = str(config.horizons[0])
    baseline = baseline_metrics[primary_key]
    lag = lag_metrics[primary_key]
    retry = retry_metrics[primary_key]
    primary_safety = safety[f"retry_h{primary_key}"]
    safety_ok = (
        primary_safety["illegal_regression_count"] == 0
        and primary_safety["stalemate_regression_count"] == 0
        and primary_safety["rook_loss_regression_count"] == 0
    )
    conversion_gain = retry.chain.mates > baseline.mates
    completion_gain_vs_lag = retry.chain.chain_completion_count > lag.chain.chain_completion_count
    retry_used = retry.retry_success_count > 0
    repetition_delta_vs_baseline = baseline.repetition_events - retry.chain.repetition_events
    full_pass = (
        safety_ok
        and retry.chain.conversion_rate >= baseline.conversion_rate + 0.10
        and retry.chain.m3_update_count > 0
        and retry_used
    )
    partial_continue = (
        safety_ok
        and not full_pass
        and retry_used
        and (
            conversion_gain
            or completion_gain_vs_lag
            or repetition_delta_vs_baseline > 0
        )
    )
    reasons: list[str] = []
    if not safety_ok:
        reasons.append("retry_safety_regression")
    if retry.chain.mates == 0:
        reasons.append("zero_heldout_conversion")
    if not retry_used:
        reasons.append("retry_never_used")
    if not completion_gain_vs_lag:
        reasons.append("no_completion_gain_vs_lag_only")
    if repetition_delta_vs_baseline <= 0:
        reasons.append("no_repetition_reduction_vs_baseline")
    status = "tg20_retry_full_pass" if full_pass else "tg20_retry_partial_continue" if partial_continue else "tg20_retry_failed_cleanly"
    return {
        "status": status,
        "full_pass": full_pass,
        "partial_continue": partial_continue,
        "failed": not full_pass and not partial_continue,
        "safety_checkpoint_passed": safety_ok,
        "conversion_improved_vs_baseline": conversion_gain,
        "primary_horizon": int(config.horizons[0]),
        "baseline_primary_mates": baseline.mates,
        "lag_only_primary_mates": lag.chain.mates,
        "retry_primary_mates": retry.chain.mates,
        "baseline_primary_repetition_events": baseline.repetition_events,
        "retry_primary_repetition_events": retry.chain.repetition_events,
        "repetition_event_delta_vs_baseline": repetition_delta_vs_baseline,
        "lag_only_chain_completions": lag.chain.chain_completion_count,
        "retry_chain_completions": retry.chain.chain_completion_count,
        "completion_delta_vs_lag_only": retry.chain.chain_completion_count - lag.chain.chain_completion_count,
        "lag_only_rook_losses": lag.chain.rook_losses,
        "retry_rook_losses": retry.chain.rook_losses,
        "retry_request_count": retry.retry_request_count,
        "retry_success_count": retry.retry_success_count,
        "retry_suppressed_active_completion_count": retry.retry_suppressed_active_completion_count,
        "lag_suppression_count": retry.lag_suppression_count,
        "training_retry_success_count": training_metrics.retry_success_count,
        "training_m3_update_count": training_metrics.chain.m3_update_count,
        "heldout_m3_update_count": retry.chain.m3_update_count,
        "m4_consolidation_event_count": 0,
        "candidate_promoted": False,
        "candidate_quarantined_or_pruned": not full_pass,
        "move_choice_mediated_by_local_script_nodes": True,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "selector_behavior_enabled": False,
        "next_recommended_checkpoint": "TG21 mine safer continuations from retry traces" if partial_continue else "inspect local retry failures before broad training",
        "reasons": reasons,
    }

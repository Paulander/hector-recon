"""TG19 LAG terminal guard for fragment-chain KRK autogrowth."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from .evaluate import ArmMetrics, choose_black_reply, choose_white_baseline_move, classify_terminal_outcome, evaluate_arm, _position_repetition_key
from .features import extract_learner_features, validate_learner_record
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
from .positions import KRKPositionSet, generate_position_sets
from .sandbox import _before_condition_matches, _paired_delta, _safety_counts
from .script_candidates import build_local_script_nodes, _first_matching_move, _post_script_step_credit, _script_node_is_selectable
from .topological_growth import build_triplet_chain_view


LAG_FEATURES = (
    "rook_attacked_by_black",
    "rook_present",
    "repetition_seen",
)


@dataclass(frozen=True)
class LagTerminalConfig:
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
class LagFragmentChainMetrics:
    chain: FragmentChainMetrics
    lag_request_count: int
    lag_trigger_count: int
    lag_suppression_count: int
    lag_rook_threat_delta_count: int
    lag_rook_missing_delta_count: int
    lag_repetition_delta_count: int
    lag_quarantined_candidate_count: int

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
            }
        )
        return payload


@dataclass(frozen=True)
class LagTerminalResult:
    config: LagTerminalConfig
    positions: KRKPositionSet
    candidates: list[dict[str, Any]]
    chain_view: dict[str, Any]
    trained_nodes: list[dict[str, Any]]
    training_metrics: LagFragmentChainMetrics
    baseline_metrics: dict[str, ArmMetrics]
    sham_metrics: dict[str, ArmMetrics]
    no_lag_metrics: dict[str, FragmentChainMetrics]
    lag_metrics: dict[str, LagFragmentChainMetrics]
    paired_deltas: dict[str, dict[str, int]]
    safety: dict[str, dict[str, int]]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.candidates)
        return {
            "schema_version": "krk_autogrowth_tg19_lag_terminals.v0",
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
                "lag_relation": "RET",
                "lag_feature_keys": list(LAG_FEATURES),
                "move_choice_mediated_by_local_script_nodes": True,
                "lag_terminal_can_inhibit_candidate_action": True,
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
                "training_lag_fragment_chain": self.training_metrics.to_dict(),
                "baseline": {str(horizon): metrics.to_dict() for horizon, metrics in self.baseline_metrics.items()},
                "sham_fragment_chain": {str(horizon): metrics.to_dict() for horizon, metrics in self.sham_metrics.items()},
                "real_fragment_chain_no_lag": {str(horizon): metrics.to_dict() for horizon, metrics in self.no_lag_metrics.items()},
                "real_fragment_chain_lag": {str(horizon): metrics.to_dict() for horizon, metrics in self.lag_metrics.items()},
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


def run_lag_terminal_experiment(
    *,
    config: LagTerminalConfig,
    positions: KRKPositionSet | None = None,
) -> LagTerminalResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    chain_config = _chain_config(config)
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
    training_metrics, _training_outcomes = evaluate_lag_fragment_chain_arm(
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
        arm="training_lag_fragment_chain",
    )
    no_lag_script_nodes = copy.deepcopy(script_nodes)
    _apply_lag_quarantine(script_nodes, threshold=config.lag_negative_threshold)
    heldout = list(positions.heldout)
    baseline_metrics: dict[str, ArmMetrics] = {}
    sham_metrics: dict[str, ArmMetrics] = {}
    no_lag_metrics: dict[str, FragmentChainMetrics] = {}
    lag_metrics: dict[str, LagFragmentChainMetrics] = {}
    paired_deltas: dict[str, dict[str, int]] = {}
    safety: dict[str, dict[str, int]] = {}
    from .fragment_chain_curriculum import evaluate_fragment_chain_arm

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
            script_nodes=script_nodes,
            chain_adjacency=adjacency,
            horizon=horizon,
            activation_max_distance=config.activation_max_distance,
            after_max_distance=config.after_max_distance,
            chain_request_bonus=config.chain_request_bonus,
            eta_m3=config.eta_m3,
            lag_negative_threshold=config.lag_negative_threshold,
            update_nodes=False,
            arm="real_fragment_chain_lag",
        )
        key = str(horizon)
        baseline_metrics[key] = baseline_metric
        sham_metrics[key] = sham_metric
        no_lag_metrics[key] = no_lag_metric
        lag_metrics[key] = lag_metric
        paired_deltas[f"baseline_vs_lag_h{key}"] = _paired_delta(baseline_outcomes, lag_outcomes)
        paired_deltas[f"baseline_vs_no_lag_h{key}"] = _paired_delta(baseline_outcomes, no_lag_outcomes)
        paired_deltas[f"sham_vs_lag_h{key}"] = _paired_delta(_inert_candidate_outcomes(sham_outcomes), lag_outcomes)
        safety[f"lag_h{key}"] = _safety_counts(baseline_outcomes, lag_outcomes)
        safety[f"no_lag_h{key}"] = _safety_counts(baseline_outcomes, no_lag_outcomes)
        safety[f"sham_h{key}"] = _safety_counts(baseline_outcomes, _inert_candidate_outcomes(sham_outcomes))
    decision = _lag_decision(
        config=config,
        training_metrics=training_metrics,
        baseline_metrics=baseline_metrics,
        sham_metrics=sham_metrics,
        no_lag_metrics=no_lag_metrics,
        lag_metrics=lag_metrics,
        safety=safety,
    )
    return LagTerminalResult(
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
        paired_deltas=paired_deltas,
        safety=safety,
        decision=decision,
    )


def evaluate_lag_fragment_chain_arm(
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
) -> tuple[LagFragmentChainMetrics, list[dict[str, Any]]]:
    outcomes: list[dict[str, Any]] = []
    counts = {"mate": 0, "horizon_no_mate": 0, "stalemate": 0, "rook_loss": 0, "illegal_move": 0, "other_failure": 0}
    draw_reasons: dict[str, int] = {}
    totals = _empty_chain_totals()
    lag_totals = _empty_lag_totals()
    for fen in fens:
        result = _lag_chain_playout(
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
    return LagFragmentChainMetrics(chain=chain, **lag_totals), outcomes


def _lag_chain_playout(
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
    illegal_moves = 0
    changed_position = False
    for ply in range(int(horizon)):
        terminal = classify_terminal_outcome(board)
        if terminal is not None:
            return _lag_chain_result(outcome=terminal, plies=ply, illegal_moves=illegal_moves, changed_position=changed_position, **totals, **lag_totals)
        baseline_move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        before = board.copy(stack=False)
        if baseline_move is None or baseline_move not in board.legal_moves:
            illegal_moves += 1
            return _lag_chain_result(outcome="illegal_move", plies=ply, illegal_moves=illegal_moves, changed_position=changed_position, **totals, **lag_totals)
        move = baseline_move
        selected_node: dict[str, Any] | None = None
        completed_node: dict[str, Any] | None = None
        if board.turn == chess.WHITE:
            totals["chain_request_count"] += 1
            if requested_successors:
                totals["chained_successor_request_count"] += 1
            decision = choose_lag_fragment_chain_action(
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
    return _lag_chain_result(
        outcome="mate" if board.is_checkmate() else "horizon_no_mate",
        plies=int(horizon),
        illegal_moves=illegal_moves,
        changed_position=changed_position,
        **totals,
        **lag_totals,
    )


def choose_lag_fragment_chain_action(
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
    if active_script is not None:
        node = _script_node_by_key(script_nodes, active_script["candidate_key"])
        if node is not None and _lag_node_selectable(node, lag_negative_threshold):
            move = _first_matching_move(board, node["candidate"]["script_plan"]["actions"][1])
            if move is not None:
                lag_counts["lag_request_count"] += 1
                lag = evaluate_lag_terminal(board, move, position_counts=position_counts)
                _merge_lag_counts(lag_counts, lag)
                if not lag["inhibits"]:
                    return {"move": move, "node": node, "started": False, "completed": True, "lag_counts": lag_counts}
                if update_nodes:
                    _record_lag_negative(node, sibling_action=move.uci())
        return {"move": None, "node": None, "started": False, "completed": False, "aborted": True, "lag_counts": lag_counts}

    requested = set(requested_successors)
    options: list[tuple[float, int, str, dict[str, Any], chess.Move]] = []
    for node in script_nodes:
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
        return {"move": None, "node": None, "started": False, "completed": False, "lag_counts": lag_counts}
    options.sort(reverse=True)
    _score, _rank, _uci, node, move = options[0]
    return {"move": move, "node": node, "started": True, "completed": False, "lag_counts": lag_counts}


def evaluate_lag_terminal(
    board: chess.Board,
    move: chess.Move,
    *,
    position_counts: dict[str, int],
) -> dict[str, Any]:
    before = extract_learner_features(board)
    after_board = board.copy(stack=False)
    after_board.push(move)
    after = extract_learner_features(after_board)
    after_key = _position_repetition_key(after_board)
    rook_threat_delta = int(after["rook_attacked_by_black"] > before["rook_attacked_by_black"])
    rook_missing_delta = int(after["rook_present"] < before["rook_present"])
    repetition_delta = int(position_counts.get(after_key, 0) > 0)
    inhibits = bool(rook_threat_delta or rook_missing_delta or repetition_delta)
    return {
        "inhibits": inhibits,
        "lag_trigger_count": 1 if inhibits else 0,
        "lag_suppression_count": 1 if inhibits else 0,
        "lag_rook_threat_delta_count": rook_threat_delta,
        "lag_rook_missing_delta_count": rook_missing_delta,
        "lag_repetition_delta_count": repetition_delta,
        "lag_features": {
            "rook_attacked_by_black_delta": after["rook_attacked_by_black"] - before["rook_attacked_by_black"],
            "rook_present_delta": after["rook_present"] - before["rook_present"],
            "repetition_seen": float(repetition_delta),
        },
    }


def _apply_lag_quarantine(script_nodes: list[dict[str, Any]], *, threshold: int) -> None:
    for node in script_nodes:
        if int(node["diagnostics"].get("lag_negative_training_count", 0)) >= int(threshold):
            node["cell"].record_candidate_intervention("negative")
            node["cell"].candidate_stats.survival_stats.quarantine_reason = "lag_terminal_negative_transition"
            node["cell"].candidate_stats.recompute_survival(xp=node["cell"].xp, solidify_xp=node["cell"].XP_SOLIDIFY)
            node["learner_visible"]["lag_quarantined"] = True
        else:
            node["learner_visible"]["lag_quarantined"] = False


def _lag_node_selectable(node: dict[str, Any], lag_negative_threshold: int) -> bool:
    if _script_node_is_selectable(node):
        return True
    lag_negatives = int(node["diagnostics"].get("lag_negative_training_count", 0))
    credit = node["cell"].candidate_stats.credit_stats
    survival = node["cell"].candidate_stats.survival_stats
    return (
        lag_negatives >= int(lag_negative_threshold)
        and survival.quarantine_reason == "lag_terminal_negative_transition"
        and int(credit.negative_intervention) <= lag_negatives
    )


def _record_lag_negative(node: dict[str, Any], *, sibling_action: str) -> None:
    node["diagnostics"]["lag_negative_training_count"] = int(node["diagnostics"].get("lag_negative_training_count", 0)) + 1
    node["cell"].record_candidate_request("tg19_lag_terminal_parent")
    node["cell"].record_candidate_activation("tg19_lag_terminal_parent")
    node["cell"].candidate_stats.mark_sibling_contrast(1.0, suppressed_sibling=sibling_action)
    node["learner_visible"]["lag_suppressed_sibling_action"] = sibling_action


def _merge_lag_counts(totals: dict[str, int], lag: dict[str, Any]) -> None:
    for key in (
        "lag_trigger_count",
        "lag_suppression_count",
        "lag_rook_threat_delta_count",
        "lag_rook_missing_delta_count",
        "lag_repetition_delta_count",
    ):
        totals[key] += int(lag.get(key, 0))


def _empty_lag_totals() -> dict[str, int]:
    return {
        "lag_request_count": 0,
        "lag_trigger_count": 0,
        "lag_suppression_count": 0,
        "lag_rook_threat_delta_count": 0,
        "lag_rook_missing_delta_count": 0,
        "lag_repetition_delta_count": 0,
        "lag_quarantined_candidate_count": 0,
    }


def _lag_chain_result(
    *,
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
        }
    )
    return payload


def _after_terminal_matches(board: chess.Board, candidate: dict[str, Any], max_distance: float) -> bool:
    features = extract_learner_features(board)
    cluster = candidate["after_cluster"]
    names = [name for name in cluster["feature_names"] if name in features]
    if not names:
        return False
    squared = 0.0
    for name in names:
        squared += (float(features[name]) - float(cluster["prototype"][name])) ** 2
    distance = (squared / len(names)) ** 0.5
    return distance <= float(max_distance)


def _chain_config(config: LagTerminalConfig) -> FragmentChainCurriculumConfig:
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


def _inert_candidate_outcomes(outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in outcomes:
        payload = dict(row)
        payload.setdefault("candidate_changed_move_count", 0)
        payload.setdefault("candidate_move_count", 0)
        payload.setdefault("candidate_behavior_changed_position_count", 0)
        normalized.append(payload)
    return normalized


def _lag_decision(
    *,
    config: LagTerminalConfig,
    training_metrics: LagFragmentChainMetrics,
    baseline_metrics: dict[str, ArmMetrics],
    sham_metrics: dict[str, ArmMetrics],
    no_lag_metrics: dict[str, FragmentChainMetrics],
    lag_metrics: dict[str, LagFragmentChainMetrics],
    safety: dict[str, dict[str, int]],
) -> dict[str, Any]:
    primary_key = str(config.horizons[0])
    baseline = baseline_metrics[primary_key]
    sham = sham_metrics[primary_key]
    no_lag = no_lag_metrics[primary_key]
    lag = lag_metrics[primary_key]
    primary_safety = safety[f"lag_h{primary_key}"]
    safety_ok = (
        primary_safety["illegal_regression_count"] == 0
        and primary_safety["stalemate_regression_count"] == 0
        and primary_safety["rook_loss_regression_count"] == 0
    )
    rook_loss_delta_vs_no_lag = no_lag.rook_losses - lag.chain.rook_losses
    repetition_delta_vs_baseline = baseline.repetition_events - lag.chain.repetition_events
    conversion_gain = lag.chain.mates > baseline.mates
    sham_matches_lag = sham.mates == lag.chain.mates and sham.repetition_events == lag.chain.repetition_events
    full_pass = safety_ok and lag.chain.conversion_rate >= baseline.conversion_rate + 0.10 and lag.chain.m3_update_count > 0 and not sham_matches_lag
    partial_continue = (
        safety_ok
        and not full_pass
        and lag.lag_trigger_count > 0
        and (
            conversion_gain
            or rook_loss_delta_vs_no_lag > 0
            or repetition_delta_vs_baseline > 0
            or lag.chain.chain_completion_count > no_lag.chain_completion_count
        )
    )
    reasons: list[str] = []
    if not safety_ok:
        reasons.append("lag_safety_regression")
    if lag.chain.mates == 0:
        reasons.append("zero_heldout_conversion")
    if rook_loss_delta_vs_no_lag <= 0:
        reasons.append("no_rook_loss_improvement_vs_no_lag")
    if repetition_delta_vs_baseline <= 0:
        reasons.append("no_repetition_reduction_vs_baseline")
    if lag.lag_trigger_count <= 0:
        reasons.append("lag_terminal_never_triggered")
    status = "tg19_lag_full_pass" if full_pass else "tg19_lag_partial_continue" if partial_continue else "tg19_lag_failed_cleanly"
    return {
        "status": status,
        "full_pass": full_pass,
        "partial_continue": partial_continue,
        "failed": not full_pass and not partial_continue,
        "safety_checkpoint_passed": safety_ok,
        "conversion_improved_vs_baseline": conversion_gain,
        "primary_horizon": int(config.horizons[0]),
        "baseline_primary_mates": baseline.mates,
        "sham_primary_mates": sham.mates,
        "no_lag_primary_mates": no_lag.mates,
        "lag_primary_mates": lag.chain.mates,
        "baseline_primary_repetition_events": baseline.repetition_events,
        "lag_primary_repetition_events": lag.chain.repetition_events,
        "repetition_event_delta_vs_baseline": repetition_delta_vs_baseline,
        "no_lag_rook_losses": no_lag.rook_losses,
        "lag_rook_losses": lag.chain.rook_losses,
        "rook_loss_delta_vs_no_lag": rook_loss_delta_vs_no_lag,
        "lag_trigger_count": lag.lag_trigger_count,
        "lag_suppression_count": lag.lag_suppression_count,
        "training_lag_trigger_count": training_metrics.lag_trigger_count,
        "training_m3_update_count": training_metrics.chain.m3_update_count,
        "heldout_m3_update_count": lag.chain.m3_update_count,
        "m4_consolidation_event_count": 0,
        "candidate_promoted": False,
        "candidate_quarantined_or_pruned": not full_pass,
        "move_choice_mediated_by_local_script_nodes": True,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "selector_behavior_enabled": False,
        "next_recommended_checkpoint": "TG20-local sensor composition or refine LAG threshold" if partial_continue else "inspect LAG precision before another curriculum run",
        "reasons": reasons,
    }

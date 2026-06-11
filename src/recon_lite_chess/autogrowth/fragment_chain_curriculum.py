"""TG18 bounded fragment-chain curriculum for KRK autogrowth."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from recon_lite_hector.nodes.stem_cell import StemCellTerminal

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
from .sandbox import _before_condition_matches, _paired_delta, _safety_counts, _sandbox_result
from .script_candidates import (
    LocalScriptConfig,
    build_local_script_nodes,
    generate_local_script_candidates,
    _first_matching_move,
    _post_script_step_credit,
    _script_node_is_selectable,
)
from .script_fragments import ScriptFragmentConfig, generalize_script_candidates_to_fragments
from .topological_growth import build_triplet_chain_view


@dataclass(frozen=True)
class FragmentChainCurriculumConfig:
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


@dataclass(frozen=True)
class FragmentChainMetrics:
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
    max_plies: int
    chain_request_count: int
    chain_start_count: int
    chain_step_count: int
    chain_completion_count: int
    chain_abort_count: int
    chain_after_confirm_count: int
    chain_after_fail_count: int
    chained_successor_request_count: int
    chained_successor_start_count: int
    baseline_fallback_count: int
    no_chain_activation_count: int
    repeated_local_chain_loop_count: int
    repeated_white_action_events: int
    repetition_events: int
    fivefold_repetition_count: int
    chain_abort_loop_count: int
    baseline_fallback_loop_count: int
    positive_credit_count: int
    negative_credit_count: int
    neutral_credit_count: int
    m3_update_count: int
    m3_fast_weight_delta: float
    m4_consolidation_event_count: int

    @property
    def conversion_rate(self) -> float:
        return 0.0 if self.total == 0 else self.mates / self.total

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["conversion_rate"] = self.conversion_rate
        return payload


@dataclass(frozen=True)
class FragmentChainCurriculumResult:
    config: FragmentChainCurriculumConfig
    positions: KRKPositionSet
    candidates: list[dict[str, Any]]
    chain_view: dict[str, Any]
    trained_nodes: list[dict[str, Any]]
    training_metrics: FragmentChainMetrics
    baseline_metrics: dict[str, ArmMetrics]
    sham_metrics: dict[str, ArmMetrics]
    chain_metrics: dict[str, FragmentChainMetrics]
    paired_deltas: dict[str, dict[str, int]]
    safety: dict[str, dict[str, int]]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.candidates)
        return {
            "schema_version": "krk_autogrowth_tg18_fragment_chain_curriculum.v0",
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
            "local_recon_structure": {
                "parent_node_type": "SCRIPT",
                "fragment_node_type": "TERMINAL",
                "action_child_count_per_script": 2,
                "chain_relation": "after TERMINAL can locally request/confirm another before TERMINAL",
                "relation_types": ["SUB", "POR", "SUR", "RET"],
                "move_choice_mediated_by_local_script_nodes": True,
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
                "training_real_fragment_chain": self.training_metrics.to_dict(),
                "baseline": {str(horizon): metrics.to_dict() for horizon, metrics in self.baseline_metrics.items()},
                "sham_fragment_chain": {str(horizon): metrics.to_dict() for horizon, metrics in self.sham_metrics.items()},
                "real_fragment_chain": {str(horizon): metrics.to_dict() for horizon, metrics in self.chain_metrics.items()},
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


def run_fragment_chain_curriculum(
    *,
    config: FragmentChainCurriculumConfig,
    positions: KRKPositionSet | None = None,
) -> FragmentChainCurriculumResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    candidates = _generate_fragment_candidates(positions, config=config)
    chain_view = build_triplet_chain_view(
        candidates,
        max_distance=config.chain_max_distance,
        max_edges=config.max_chain_edges,
    )
    script_nodes = build_local_script_nodes(
        positions.train,
        candidates=candidates,
        config=_local_script_config(config, horizon=max(config.horizons)),
    )
    adjacency = _chain_adjacency(chain_view)
    training_metrics, _training_outcomes = evaluate_fragment_chain_arm(
        positions.train,
        script_nodes=script_nodes,
        chain_adjacency=adjacency,
        horizon=max(config.horizons),
        activation_max_distance=config.activation_max_distance,
        after_max_distance=config.after_max_distance,
        chain_request_bonus=config.chain_request_bonus,
        eta_m3=config.eta_m3,
        update_nodes=True,
        arm="training_real_fragment_chain",
    )
    heldout = list(positions.heldout)
    baseline_metrics: dict[str, ArmMetrics] = {}
    sham_metrics: dict[str, ArmMetrics] = {}
    chain_metrics: dict[str, FragmentChainMetrics] = {}
    paired_deltas: dict[str, dict[str, int]] = {}
    safety: dict[str, dict[str, int]] = {}
    for horizon in config.horizons:
        baseline_metric, baseline_outcomes = evaluate_arm(heldout, arm="baseline", horizon=horizon)
        sham_metric, sham_outcomes = evaluate_arm(heldout, arm="sham_growth", horizon=horizon)
        chain_metric, chain_outcomes = evaluate_fragment_chain_arm(
            heldout,
            script_nodes=script_nodes,
            chain_adjacency=adjacency,
            horizon=horizon,
            activation_max_distance=config.activation_max_distance,
            after_max_distance=config.after_max_distance,
            chain_request_bonus=config.chain_request_bonus,
            eta_m3=config.eta_m3,
            update_nodes=False,
            arm="real_fragment_chain",
        )
        key = str(horizon)
        baseline_metrics[key] = baseline_metric
        sham_metrics[key] = sham_metric
        chain_metrics[key] = chain_metric
        paired_deltas[f"baseline_vs_real_h{key}"] = _paired_delta(baseline_outcomes, chain_outcomes)
        paired_deltas[f"baseline_vs_sham_h{key}"] = _paired_delta(
            baseline_outcomes,
            _inert_candidate_outcomes(sham_outcomes),
        )
        paired_deltas[f"sham_vs_real_h{key}"] = _paired_delta(sham_outcomes, chain_outcomes)
        safety[f"real_h{key}"] = _safety_counts(baseline_outcomes, chain_outcomes)
        safety[f"sham_h{key}"] = _safety_counts(baseline_outcomes, _inert_candidate_outcomes(sham_outcomes))
    decision = _curriculum_decision(
        config=config,
        training_metrics=training_metrics,
        baseline_metrics=baseline_metrics,
        sham_metrics=sham_metrics,
        chain_metrics=chain_metrics,
        paired_deltas=paired_deltas,
        safety=safety,
        chain_view=chain_view,
    )
    return FragmentChainCurriculumResult(
        config=config,
        positions=positions,
        candidates=candidates,
        chain_view=chain_view,
        trained_nodes=script_nodes,
        training_metrics=training_metrics,
        baseline_metrics=baseline_metrics,
        sham_metrics=sham_metrics,
        chain_metrics=chain_metrics,
        paired_deltas=paired_deltas,
        safety=safety,
        decision=decision,
    )


def evaluate_fragment_chain_arm(
    fens: Iterable[str],
    *,
    script_nodes: list[dict[str, Any]],
    chain_adjacency: dict[str, list[str]],
    horizon: int,
    activation_max_distance: float,
    after_max_distance: float,
    chain_request_bonus: float,
    eta_m3: float,
    update_nodes: bool,
    arm: str = "real_fragment_chain",
) -> tuple[FragmentChainMetrics, list[dict[str, Any]]]:
    outcomes: list[dict[str, Any]] = []
    counts = {"mate": 0, "horizon_no_mate": 0, "stalemate": 0, "rook_loss": 0, "illegal_move": 0, "other_failure": 0}
    draw_reasons: dict[str, int] = {}
    totals = _empty_chain_totals()
    for fen in fens:
        result = _chain_playout(
            fen,
            script_nodes=script_nodes,
            chain_adjacency=chain_adjacency,
            horizon=horizon,
            activation_max_distance=activation_max_distance,
            after_max_distance=after_max_distance,
            chain_request_bonus=chain_request_bonus,
            eta_m3=eta_m3,
            update_nodes=update_nodes,
        )
        outcome = str(result["outcome"])
        if outcome.startswith("draw_"):
            draw_reasons[outcome] = draw_reasons.get(outcome, 0) + 1
        else:
            counts[outcome] = counts.get(outcome, 0) + 1
        for key in totals:
            totals[key] += int(result[key])
        outcomes.append({"fen": fen, **result})
    return FragmentChainMetrics(
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
    ), outcomes


def _chain_playout(
    fen: str,
    *,
    script_nodes: list[dict[str, Any]],
    chain_adjacency: dict[str, list[str]],
    horizon: int,
    activation_max_distance: float,
    after_max_distance: float,
    chain_request_bonus: float,
    eta_m3: float,
    update_nodes: bool,
) -> dict[str, Any]:
    board = chess.Board(fen)
    active_script: dict[str, Any] | None = None
    requested_successors: list[str] = []
    position_counts = {_position_repetition_key(board): 1}
    white_action_counts: dict[str, int] = {}
    chain_pair_counts: dict[str, int] = {}
    totals = _empty_chain_totals()
    illegal_moves = 0
    changed_position = False
    last_completed_key: str | None = None
    for ply in range(int(horizon)):
        terminal = classify_terminal_outcome(board)
        if terminal is not None:
            return _chain_result(outcome=terminal, plies=ply, illegal_moves=illegal_moves, changed_position=changed_position, **totals)
        baseline_move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        before = board.copy(stack=False)
        if baseline_move is None or baseline_move not in board.legal_moves:
            illegal_moves += 1
            return _chain_result(outcome="illegal_move", plies=ply, illegal_moves=illegal_moves, changed_position=changed_position, **totals)
        move = baseline_move
        selected_node: dict[str, Any] | None = None
        completed_node: dict[str, Any] | None = None
        if board.turn == chess.WHITE:
            totals["chain_request_count"] += 1
            if requested_successors:
                totals["chained_successor_request_count"] += 1
            decision = choose_fragment_chain_action(
                board,
                script_nodes=script_nodes,
                active_script=active_script,
                requested_successors=requested_successors,
                activation_max_distance=activation_max_distance,
                chain_request_bonus=chain_request_bonus,
            )
            if decision.get("aborted"):
                totals["chain_abort_count"] += 1
                active_script = None
                requested_successors = []
            elif decision["move"] is None:
                totals["baseline_fallback_count"] += 1
                totals["no_chain_activation_count"] += 1
                if requested_successors:
                    totals["baseline_fallback_loop_count"] += 1
                active_script = None
                requested_successors = []
            else:
                move = decision["move"]
                selected_node = decision["node"]
                totals["chain_step_count"] += 1
                if decision["started"]:
                    totals["chain_start_count"] += 1
                    if requested_successors and selected_node["candidate_key"] in requested_successors:
                        totals["chained_successor_start_count"] += 1
                        if last_completed_key is not None:
                            pair_key = f"{last_completed_key}->{selected_node['candidate_key']}"
                            if chain_pair_counts.get(pair_key, 0) > 0:
                                totals["repeated_local_chain_loop_count"] += 1
                            chain_pair_counts[pair_key] = chain_pair_counts.get(pair_key, 0) + 1
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
                    successors = chain_adjacency.get(completed_node["candidate_key"], [])
                    requested_successors = list(successors)
                    last_completed_key = completed_node["candidate_key"]
                    if successors:
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
    return _chain_result(
        outcome="mate" if board.is_checkmate() else "horizon_no_mate",
        plies=int(horizon),
        illegal_moves=illegal_moves,
        changed_position=changed_position,
        **totals,
    )


def choose_fragment_chain_action(
    board: chess.Board,
    *,
    script_nodes: list[dict[str, Any]],
    active_script: dict[str, Any] | None,
    requested_successors: list[str],
    activation_max_distance: float,
    chain_request_bonus: float,
) -> dict[str, Any]:
    if active_script is not None:
        node = _script_node_by_key(script_nodes, active_script["candidate_key"])
        if node is not None and _script_node_is_selectable(node):
            move = _first_matching_move(board, node["candidate"]["script_plan"]["actions"][1])
            if move is not None:
                return {"move": move, "node": node, "started": False, "completed": True}
        return {"move": None, "node": None, "started": False, "completed": False, "aborted": True}

    requested = set(requested_successors)
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
        score = float(node["local_weight"])
        if node["candidate_key"] in requested:
            score += float(chain_request_bonus)
        options.append((score, -int(node["rank"]), move.uci(), node, move))
    if not options:
        return {"move": None, "node": None, "started": False, "completed": False}
    options.sort(reverse=True)
    _score, _rank, _uci, node, move = options[0]
    return {"move": move, "node": node, "started": True, "completed": False}


def _generate_fragment_candidates(
    positions: KRKPositionSet,
    *,
    config: FragmentChainCurriculumConfig,
) -> list[dict[str, Any]]:
    exact_candidates, _summary = generate_local_script_candidates(
        positions.train,
        config=_local_script_config(config, horizon=max(config.horizons)),
    )
    return generalize_script_candidates_to_fragments(
        exact_candidates,
        fragment_feature_names=ScriptFragmentConfig().fragment_feature_names,
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


def _local_script_config(config: FragmentChainCurriculumConfig, *, horizon: int) -> LocalScriptConfig:
    return LocalScriptConfig(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
        min_support=config.min_support,
        max_candidates=config.max_candidates,
        horizon=int(horizon),
        min_sequence_credit=config.min_sequence_credit,
        activation_max_distance=config.activation_max_distance,
        eta_m3=config.eta_m3,
    )


def _chain_adjacency(chain_view: dict[str, Any]) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {}
    for edge in chain_view["chain_edges"]:
        source = str(edge["source_after_candidate_key"])
        target = str(edge["target_before_candidate_key"])
        adjacency.setdefault(source, []).append(target)
    for targets in adjacency.values():
        targets.sort()
    return adjacency


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


def _record_chain_credit(node: dict[str, Any], *, credit: float, eta_m3: float, update_node: bool) -> None:
    if not update_node:
        return
    cell: StemCellTerminal = node["cell"]
    cell.record_candidate_request("tg18_fragment_chain_parent")
    cell.record_candidate_activation("tg18_fragment_chain_parent")
    if credit > 0.0:
        cell.record_candidate_intervention("positive")
        node["diagnostics"]["positive_training_credit"] += 1
    elif credit < 0.0:
        cell.record_candidate_intervention("negative")
        node["diagnostics"]["negative_training_credit"] += 1
    else:
        cell.record_candidate_intervention("neutral")
        node["diagnostics"]["neutral_training_credit"] += 1
    node["diagnostics"]["training_sequences"] += 1
    node["local_weight"] += float(eta_m3) * float(credit)
    node["diagnostics"]["m3_fast_weight_delta"] += float(eta_m3) * float(credit)
    node["cell"].candidate_stats.recompute_survival(xp=node["cell"].xp, solidify_xp=node["cell"].XP_SOLIDIFY)
    node["learner_visible"]["local_weight"] = round(float(node["local_weight"]), 6)
    node["learner_visible"]["selectable_after_training"] = _script_node_is_selectable(node)
    node["diagnostics"]["selectable_after_training"] = _script_node_is_selectable(node)


def _script_node_by_key(script_nodes: list[dict[str, Any]], candidate_key: str) -> dict[str, Any] | None:
    for node in script_nodes:
        if node["candidate_key"] == candidate_key:
            return node
    return None


def _empty_chain_totals() -> dict[str, int]:
    return {
        "chain_request_count": 0,
        "chain_start_count": 0,
        "chain_step_count": 0,
        "chain_completion_count": 0,
        "chain_abort_count": 0,
        "chain_after_confirm_count": 0,
        "chain_after_fail_count": 0,
        "chained_successor_request_count": 0,
        "chained_successor_start_count": 0,
        "baseline_fallback_count": 0,
        "no_chain_activation_count": 0,
        "repeated_local_chain_loop_count": 0,
        "repeated_white_action_events": 0,
        "repetition_events": 0,
        "fivefold_repetition_count": 0,
        "chain_abort_loop_count": 0,
        "baseline_fallback_loop_count": 0,
        "positive_credit_count": 0,
        "negative_credit_count": 0,
        "neutral_credit_count": 0,
        "m3_update_count": 0,
        "m3_fast_weight_delta_scaled": 0,
    }


def _chain_result(
    *,
    outcome: str,
    plies: int,
    illegal_moves: int,
    changed_position: bool,
    chain_request_count: int,
    chain_start_count: int,
    chain_step_count: int,
    chain_completion_count: int,
    chain_abort_count: int,
    chain_after_confirm_count: int,
    chain_after_fail_count: int,
    chained_successor_request_count: int,
    chained_successor_start_count: int,
    baseline_fallback_count: int,
    no_chain_activation_count: int,
    repeated_local_chain_loop_count: int,
    repeated_white_action_events: int,
    repetition_events: int,
    fivefold_repetition_count: int,
    chain_abort_loop_count: int,
    baseline_fallback_loop_count: int,
    positive_credit_count: int,
    negative_credit_count: int,
    neutral_credit_count: int,
    m3_update_count: int,
    m3_fast_weight_delta_scaled: int,
) -> dict[str, Any]:
    payload = _sandbox_result(
        outcome=outcome,
        plies=plies,
        illegal_moves=illegal_moves,
        candidate_terminal_activations=chain_request_count,
        candidate_action_matches=chain_step_count,
        candidate_move_count=chain_step_count,
        candidate_changed_move_count=chain_step_count if changed_position else 0,
        after_condition_match_count=chain_after_confirm_count,
        positive_credit_count=positive_credit_count,
        negative_credit_count=negative_credit_count,
        m3_update_count=m3_update_count,
        m3_fast_weight_delta=m3_fast_weight_delta_scaled / 1000.0,
        repetition_events=repetition_events,
        repeated_white_action_events=repeated_white_action_events,
        activated_position=chain_step_count > 0,
        behavior_changed_position=changed_position,
    )
    payload.update(
        {
            "chain_request_count": chain_request_count,
            "chain_start_count": chain_start_count,
            "chain_step_count": chain_step_count,
            "chain_completion_count": chain_completion_count,
            "chain_abort_count": chain_abort_count,
            "chain_after_confirm_count": chain_after_confirm_count,
            "chain_after_fail_count": chain_after_fail_count,
            "chained_successor_request_count": chained_successor_request_count,
            "chained_successor_start_count": chained_successor_start_count,
            "baseline_fallback_count": baseline_fallback_count,
            "no_chain_activation_count": no_chain_activation_count,
            "repeated_local_chain_loop_count": repeated_local_chain_loop_count,
            "fivefold_repetition_count": fivefold_repetition_count,
            "chain_abort_loop_count": chain_abort_loop_count,
            "baseline_fallback_loop_count": baseline_fallback_loop_count,
            "neutral_credit_count": neutral_credit_count,
        }
    )
    return payload


def _curriculum_decision(
    *,
    config: FragmentChainCurriculumConfig,
    training_metrics: FragmentChainMetrics,
    baseline_metrics: dict[str, ArmMetrics],
    sham_metrics: dict[str, ArmMetrics],
    chain_metrics: dict[str, FragmentChainMetrics],
    paired_deltas: dict[str, dict[str, int]],
    safety: dict[str, dict[str, int]],
    chain_view: dict[str, Any],
) -> dict[str, Any]:
    primary = chain_metrics[str(config.horizons[0])]
    baseline_primary = baseline_metrics[str(config.horizons[0])]
    sham_primary = sham_metrics[str(config.horizons[0])]
    primary_safety = safety[f"real_h{config.horizons[0]}"]
    safety_ok = (
        primary_safety["illegal_regression_count"] == 0
        and primary_safety["stalemate_regression_count"] == 0
        and primary_safety["rook_loss_regression_count"] == 0
    )
    conversion_gain = primary.mates > baseline_primary.mates
    sham_matches_real = sham_primary.mates == primary.mates and sham_primary.repetition_events == primary.repetition_events
    repetition_delta = baseline_primary.repetition_events - primary.repetition_events
    completion_gain = primary.chain_completion_count > 0
    full_pass = (
        safety_ok
        and primary.conversion_rate >= baseline_primary.conversion_rate + 0.10
        and primary.m3_update_count > 0
        and not sham_matches_real
    )
    partial_continue = (
        safety_ok
        and not full_pass
        and (
            conversion_gain
            or repetition_delta > 0
            or completion_gain
        )
        and primary.m3_update_count > 0
    )
    reasons: list[str] = []
    if not safety_ok:
        reasons.append("safety_regression")
    if primary.mates == 0:
        reasons.append("zero_heldout_conversion")
    if repetition_delta <= 0:
        reasons.append("no_repetition_reduction")
    if primary.chain_completion_count <= 0:
        reasons.append("no_safe_chain_completion_gain")
    if primary.m3_update_count <= 0:
        reasons.append("no_causal_m3_updates")
    if sham_matches_real:
        reasons.append("sham_matches_real_on_primary_mate_and_repetition")
    status = "tg18_full_pass" if full_pass else "tg18_partial_continue" if partial_continue else "tg18_failed_cleanly"
    return {
        "status": status,
        "full_pass": full_pass,
        "partial_continue": partial_continue,
        "failed": not full_pass and not partial_continue,
        "safety_checkpoint_passed": safety_ok,
        "conversion_improved_vs_baseline": conversion_gain,
        "primary_horizon": int(config.horizons[0]),
        "baseline_primary_mates": baseline_primary.mates,
        "sham_primary_mates": sham_primary.mates,
        "real_primary_mates": primary.mates,
        "baseline_primary_repetition_events": baseline_primary.repetition_events,
        "real_primary_repetition_events": primary.repetition_events,
        "repetition_event_delta_vs_baseline": repetition_delta,
        "chain_edge_count": int(chain_view["chain_edge_count"]),
        "training_m3_update_count": training_metrics.m3_update_count,
        "heldout_m3_update_count": primary.m3_update_count,
        "m4_consolidation_event_count": 0,
        "candidate_promoted": False,
        "candidate_quarantined_or_pruned": not full_pass,
        "move_choice_mediated_by_local_script_nodes": True,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "selector_behavior_enabled": False,
        "next_recommended_checkpoint": "TG19-LAG" if not full_pass else "repeat TG18 with locked validation split",
        "reasons": reasons,
    }

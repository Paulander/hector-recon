"""TG22 retry-event diagnostics for TG20/TG21 local continuation behavior."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable

import chess

from .continuation_retry import (
    choose_continuation_retry_action,
    evaluate_continuation_retry_arm,
)
from .evaluate import choose_black_reply, choose_white_baseline_move, classify_terminal_outcome, _position_repetition_key
from .features import extract_diagnostic_features
from .fragment_chain_curriculum import _chain_adjacency, _generate_fragment_candidates, _local_script_config
from .lag_terminals import LAG_FEATURES, evaluate_lag_terminal, _after_terminal_matches, _apply_lag_quarantine, _lag_node_selectable
from .positions import KRKPositionSet, generate_position_sets
from .retry_edges import RetryEdgeConfig, _chain_config, _retry_edge_weights
from .sandbox import _before_condition_matches
from .script_candidates import build_local_script_nodes, _first_matching_move, _post_script_step_credit
from .topological_growth import build_triplet_chain_view


@dataclass(frozen=True)
class RetryDiagnosticsConfig:
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
    retry_edge_min_support: int = 1
    retry_edge_bonus: float = 1.25
    max_event_records: int = 200


@dataclass(frozen=True)
class RetryDiagnosticsResult:
    config: RetryDiagnosticsConfig
    positions: KRKPositionSet
    candidates: list[dict[str, Any]]
    chain_view: dict[str, Any]
    retry_edge_learning_counts: dict[str, int]
    retry_edge_weights: dict[str, float]
    training_metrics: dict[str, Any]
    trace_summary: dict[str, Any]
    event_records: list[dict[str, Any]]
    comparison_records: list[dict[str, Any]]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg22_retry_diagnostics.v0",
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
                "diagnostic_only": True,
                "parent_node_type": "SCRIPT",
                "edge_type": "local_retry_request_edge",
                "relation_types": ["SUB", "POR", "SUR", "RET"],
                "move_choice_mediated_by_local_script_nodes": True,
                "direct_move_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "selector_behavior_enabled": False,
            },
            "retry_edges": {
                "learned_edge_count": len(self.retry_edge_weights),
                "learning_counts": self.retry_edge_learning_counts,
                "weights": self.retry_edge_weights,
            },
            "candidates": self.candidates,
            "triplet_chain_view": self.chain_view,
            "training_metrics": self.training_metrics,
            "trace_summary": self.trace_summary,
            "event_records": self.event_records,
            "comparison_records": self.comparison_records,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_retry_diagnostics(
    *,
    config: RetryDiagnosticsConfig,
    positions: KRKPositionSet | None = None,
) -> RetryDiagnosticsResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    edge_config = _edge_config(config)
    chain_config = _chain_config(edge_config)
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
    retry_edge_learning: dict[str, int] = {}
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
        arm="training_retry_edge_mining",
        retry_edge_learning=retry_edge_learning,
    )
    retry_edge_weights = _retry_edge_weights(retry_edge_learning, min_support=config.retry_edge_min_support)
    trace_nodes = copy.deepcopy(script_nodes)
    _apply_lag_quarantine(trace_nodes, threshold=config.lag_negative_threshold)

    records: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    train_trace = _collect_retry_traces(
        positions.train,
        split="train",
        arm="tg20_retry",
        script_nodes=trace_nodes,
        chain_adjacency=adjacency,
        horizon=max(config.horizons),
        config=config,
        retry_edge_weights=None,
    )
    records.extend(train_trace[: config.max_event_records])
    for horizon in config.horizons:
        no_edge = _collect_retry_traces(
            positions.heldout,
            split="heldout",
            arm=f"tg20_retry_h{horizon}",
            script_nodes=trace_nodes,
            chain_adjacency=adjacency,
            horizon=horizon,
            config=config,
            retry_edge_weights=None,
        )
        with_edge = _collect_retry_traces(
            positions.heldout,
            split="heldout",
            arm=f"tg21_retry_edges_h{horizon}",
            script_nodes=trace_nodes,
            chain_adjacency=adjacency,
            horizon=horizon,
            config=config,
            retry_edge_weights=retry_edge_weights,
        )
        records.extend(no_edge[: max(0, config.max_event_records - len(records))])
        records.extend(with_edge[: max(0, config.max_event_records - len(records))])
        comparisons.extend(_compare_retry_traces(no_edge, with_edge, horizon=horizon))

    summary = _trace_summary(records=records, comparisons=comparisons)
    decision = _diagnostic_decision(
        retry_edge_weights=retry_edge_weights,
        summary=summary,
        training_metrics=training_metrics.to_dict(),
    )
    return RetryDiagnosticsResult(
        config=config,
        positions=positions,
        candidates=candidates,
        chain_view=chain_view,
        retry_edge_learning_counts=dict(sorted(retry_edge_learning.items())),
        retry_edge_weights=retry_edge_weights,
        training_metrics=training_metrics.to_dict(),
        trace_summary=summary,
        event_records=records,
        comparison_records=comparisons[: config.max_event_records],
        decision=decision,
    )


def _collect_retry_traces(
    fens: Iterable[str],
    *,
    split: str,
    arm: str,
    script_nodes: list[dict[str, Any]],
    chain_adjacency: dict[str, list[str]],
    horizon: int,
    config: RetryDiagnosticsConfig,
    retry_edge_weights: dict[str, float] | None,
) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    for position_index, fen in enumerate(fens):
        traces.extend(
            _trace_one_playout(
                fen,
                split=split,
                arm=arm,
                position_index=position_index,
                script_nodes=script_nodes,
                chain_adjacency=chain_adjacency,
                horizon=horizon,
                config=config,
                retry_edge_weights=retry_edge_weights,
            )
        )
    return traces


def _trace_one_playout(
    fen: str,
    *,
    split: str,
    arm: str,
    position_index: int,
    script_nodes: list[dict[str, Any]],
    chain_adjacency: dict[str, list[str]],
    horizon: int,
    config: RetryDiagnosticsConfig,
    retry_edge_weights: dict[str, float] | None,
) -> list[dict[str, Any]]:
    board = chess.Board(fen)
    active_script: dict[str, Any] | None = None
    requested_successors: list[str] = []
    position_counts = {_position_repetition_key(board): 1}
    events: list[dict[str, Any]] = []
    pending_event_indexes: list[int] = []
    for ply in range(int(horizon)):
        terminal = classify_terminal_outcome(board)
        if terminal is not None:
            _finalize_events(events, pending_event_indexes, outcome=terminal, plies=ply)
            return events
        baseline_move = choose_white_baseline_move(board) if board.turn == chess.WHITE else choose_black_reply(board)
        if baseline_move is None or baseline_move not in board.legal_moves:
            _finalize_events(events, pending_event_indexes, outcome="illegal_move", plies=ply)
            return events
        before = board.copy(stack=False)
        move = baseline_move
        selected_node: dict[str, Any] | None = None
        completed_node: dict[str, Any] | None = None
        if board.turn == chess.WHITE:
            active_key = None if active_script is None else str(active_script["candidate_key"])
            options = _retry_options(
                board,
                script_nodes=script_nodes,
                active_key=active_key,
                config=config,
                position_counts=position_counts,
                retry_edge_weights=retry_edge_weights,
            )
            decision = choose_continuation_retry_action(
                board,
                script_nodes=script_nodes,
                active_script=active_script,
                requested_successors=requested_successors,
                activation_max_distance=config.activation_max_distance,
                chain_request_bonus=config.chain_request_bonus,
                lag_negative_threshold=config.lag_negative_threshold,
                update_nodes=False,
                position_counts=position_counts,
                retry_edge_weights=retry_edge_weights,
                retry_edge_bonus=config.retry_edge_bonus,
            )
            if decision["retry_counts"]["retry_request_count"] > 0:
                chosen_key = None if decision["node"] is None else str(decision["node"]["candidate_key"])
                event = {
                    "split": split,
                    "arm": arm,
                    "position_index": int(position_index),
                    "ply": int(ply),
                    "fen_before": before.fen(),
                    "active_candidate_key": active_key,
                    "suppressed_completion_action": _active_completion_action(before, script_nodes, active_key),
                    "retry_candidate_key": chosen_key,
                    "retry_move": None if decision["move"] is None else decision["move"].uci(),
                    "retry_success": int(decision["retry_counts"]["retry_success_count"]),
                    "retry_no_local_sibling": int(decision["retry_counts"]["retry_no_local_sibling_count"]),
                    "retry_edge_bonus_hit": int(decision["retry_counts"]["retry_edge_bonus_hit_count"]),
                    "retry_options": options,
                    "classification": _event_classification(decision=decision, options=options),
                    "before_features": _compact_features(before),
                }
                events.append(event)
                pending_event_indexes.append(len(events) - 1)
            if decision.get("aborted") or decision["move"] is None:
                active_script = None
                requested_successors = []
            else:
                move = decision["move"]
                selected_node = decision["node"]
                if decision["started"]:
                    active_script = {"candidate_key": selected_node["candidate_key"]}
                    requested_successors = []
                if decision["completed"]:
                    completed_node = selected_node
                    active_script = None
        board.push(move)
        if before.turn == chess.WHITE and selected_node is not None:
            if completed_node is not None and _after_terminal_matches(board, completed_node["candidate"], config.after_max_distance):
                requested_successors = list(chain_adjacency.get(completed_node["candidate_key"], []))
                for event_index in pending_event_indexes:
                    events[event_index]["event_led_to_completion"] = True
            elif completed_node is not None:
                requested_successors = []
            _post_script_step_credit(before, board)
        key = _position_repetition_key(board)
        position_counts[key] = position_counts.get(key, 0) + 1
    _finalize_events(events, pending_event_indexes, outcome="mate" if board.is_checkmate() else "horizon_no_mate", plies=int(horizon))
    return events


def _retry_options(
    board: chess.Board,
    *,
    script_nodes: list[dict[str, Any]],
    active_key: str | None,
    config: RetryDiagnosticsConfig,
    position_counts: dict[str, int],
    retry_edge_weights: dict[str, float] | None,
) -> list[dict[str, Any]]:
    if active_key is None:
        return []
    options: list[dict[str, Any]] = []
    for node in script_nodes:
        if node["candidate_key"] == active_key:
            continue
        if not _lag_node_selectable(node, config.lag_negative_threshold):
            continue
        if not _before_condition_matches(board, node["candidate"], config.activation_max_distance):
            continue
        move = _first_matching_move(board, node["candidate"]["script_plan"]["actions"][0])
        if move is None:
            continue
        lag = evaluate_lag_terminal(board, move, position_counts=position_counts)
        edge_key = f"{active_key}->{node['candidate_key']}"
        edge_weight = 0.0 if retry_edge_weights is None else float(retry_edge_weights.get(edge_key, 0.0))
        options.append(
            {
                "candidate_key": node["candidate_key"],
                "move": move.uci(),
                "local_weight": round(float(node["local_weight"]), 6),
                "rank": int(node["rank"]),
                "lag_inhibits": bool(lag["inhibits"]),
                "edge_key": edge_key,
                "edge_weight": edge_weight,
                "edge_bonus": round(edge_weight * float(config.retry_edge_bonus), 6),
            }
        )
    options.sort(key=lambda item: (item["lag_inhibits"], -item["edge_bonus"], -item["local_weight"], item["rank"], item["move"]))
    return options


def _compare_retry_traces(no_edge: list[dict[str, Any]], with_edge: list[dict[str, Any]], *, horizon: int) -> list[dict[str, Any]]:
    keyed_no_edge = {
        _event_key(record): record
        for record in no_edge
    }
    comparisons: list[dict[str, Any]] = []
    for edge_record in with_edge:
        base = keyed_no_edge.get(_event_key(edge_record))
        if base is None:
            continue
        comparisons.append(
            {
                "horizon": int(horizon),
                "position_index": edge_record["position_index"],
                "ply": edge_record["ply"],
                "active_candidate_key": edge_record["active_candidate_key"],
                "retry_candidate_without_edge": base["retry_candidate_key"],
                "retry_candidate_with_edge": edge_record["retry_candidate_key"],
                "edge_bonus_hit": int(edge_record["retry_edge_bonus_hit"]),
                "choice_changed": base["retry_candidate_key"] != edge_record["retry_candidate_key"],
                "same_outcome": base.get("final_outcome") == edge_record.get("final_outcome"),
                "final_outcome_without_edge": base.get("final_outcome"),
                "final_outcome_with_edge": edge_record.get("final_outcome"),
            }
        )
    return comparisons


def _event_key(record: dict[str, Any]) -> tuple[int, int, str | None]:
    return (int(record["position_index"]), int(record["ply"]), record.get("active_candidate_key"))


def _active_completion_action(board: chess.Board, script_nodes: list[dict[str, Any]], active_key: str | None) -> str | None:
    if active_key is None:
        return None
    node = next((item for item in script_nodes if item["candidate_key"] == active_key), None)
    if node is None:
        return None
    move = _first_matching_move(board, node["candidate"]["script_plan"]["actions"][1])
    return None if move is None else move.uci()


def _event_classification(*, decision: dict[str, Any], options: list[dict[str, Any]]) -> str:
    if decision["retry_counts"]["retry_no_local_sibling_count"] > 0:
        return "no_local_sibling_available" if not options else "all_local_siblings_inhibited"
    if decision["retry_counts"]["retry_edge_bonus_hit_count"] > 0:
        return "edge_bonus_used"
    if decision["retry_counts"]["retry_success_count"] > 0:
        return "retry_sibling_selected_without_edge"
    return "retry_requested_without_selection"


def _finalize_events(events: list[dict[str, Any]], indexes: list[int], *, outcome: str, plies: int) -> None:
    for index in indexes:
        events[index]["final_outcome"] = str(outcome)
        events[index]["final_plies"] = int(plies)
        events[index].setdefault("event_led_to_completion", False)
        events[index]["event_led_to_mate"] = outcome == "mate"


def _compact_features(board: chess.Board) -> dict[str, float]:
    features = extract_diagnostic_features(board)
    return {
        "black_king_nearest_edge_distance": features["black_king_nearest_edge_distance"],
        "black_reply_mobility": features["black_reply_mobility"],
        "rook_attacked_by_black": features["rook_attacked_by_black"],
        "rook_present": features["rook_present"],
        "is_check": features["is_check"],
        "white_king_to_black_king_distance": features["white_king_to_black_king_distance"],
        "white_rook_to_black_king_distance": features["white_rook_to_black_king_distance"],
    }


def _trace_summary(*, records: list[dict[str, Any]], comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, int] = {}
    by_arm: dict[str, int] = {}
    for record in records:
        by_class[record["classification"]] = by_class.get(record["classification"], 0) + 1
        by_arm[record["arm"]] = by_arm.get(record["arm"], 0) + 1
    return {
        "event_count": len(records),
        "event_count_by_arm": dict(sorted(by_arm.items())),
        "event_count_by_classification": dict(sorted(by_class.items())),
        "comparison_count": len(comparisons),
        "edge_bonus_hit_comparison_count": sum(1 for item in comparisons if item["edge_bonus_hit"]),
        "edge_changed_choice_count": sum(1 for item in comparisons if item["choice_changed"]),
        "edge_same_outcome_count": sum(1 for item in comparisons if item["same_outcome"]),
        "no_local_sibling_count": by_class.get("no_local_sibling_available", 0),
        "all_siblings_inhibited_count": by_class.get("all_local_siblings_inhibited", 0),
        "retry_success_event_count": sum(1 for item in records if item["retry_success"]),
        "retry_event_led_to_completion_count": sum(1 for item in records if item.get("event_led_to_completion")),
        "retry_event_led_to_mate_count": sum(1 for item in records if item.get("event_led_to_mate")),
    }


def _diagnostic_decision(
    *,
    retry_edge_weights: dict[str, float],
    summary: dict[str, Any],
    training_metrics: dict[str, Any],
) -> dict[str, Any]:
    edge_changed_choice = int(summary["edge_changed_choice_count"])
    no_local = int(summary["no_local_sibling_count"])
    completion_events = int(summary["retry_event_led_to_completion_count"])
    if not retry_edge_weights:
        next_checkpoint = "increase retry evidence or change candidate construction before retry-edge learning"
        finding = "no_train_retry_edges"
    elif edge_changed_choice == 0:
        next_checkpoint = "do not tune retry-edge bonus; diagnose candidate equivalence or mine richer retry contexts"
        finding = "retry_edges_redundant"
    elif no_local > completion_events:
        next_checkpoint = "improve local continuation candidate construction before adding edge logic"
        finding = "local_retry_candidate_gap"
    else:
        next_checkpoint = "test one richer local terminal over retry contexts"
        finding = "retry_context_needs_richer_terminal"
    return {
        "status": "tg22_retry_diagnostics_complete",
        "diagnostic_only": True,
        "finding": finding,
        "training_retry_success_count": training_metrics.get("retry_success_count", 0),
        "learned_retry_edge_count": len(retry_edge_weights),
        "edge_changed_choice_count": edge_changed_choice,
        "no_local_sibling_count": no_local,
        "retry_event_led_to_completion_count": completion_events,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "selector_behavior_enabled": False,
        "next_recommended_checkpoint": next_checkpoint,
    }


def _edge_config(config: RetryDiagnosticsConfig) -> RetryEdgeConfig:
    return RetryEdgeConfig(
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
        lag_negative_threshold=config.lag_negative_threshold,
        retry_edge_min_support=config.retry_edge_min_support,
        retry_edge_bonus=config.retry_edge_bonus,
    )

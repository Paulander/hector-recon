"""TG23 train-only retry-context SCRIPT sibling expansion."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import chess

from .candidate_generation import RISK_BEFORE_FEATURES, _risk_aware_credit
from .continuation_retry import ContinuationRetryMetrics, evaluate_continuation_retry_arm
from .evaluate import ArmMetrics, choose_black_reply, evaluate_arm
from .features import extract_learner_features, validate_learner_record
from .fragment_chain_curriculum import (
    FragmentChainCurriculumConfig,
    FragmentChainMetrics,
    _chain_adjacency,
    _generate_fragment_candidates,
    _local_script_config,
)
from .lag_terminals import (
    LagFragmentChainMetrics,
    evaluate_lag_fragment_chain_arm,
    _apply_lag_quarantine,
)
from .positions import KRKPositionSet, generate_position_sets
from .retry_diagnostics import RetryDiagnosticsConfig, _collect_retry_traces
from .sandbox import _paired_delta, _safety_counts
from .script_candidates import (
    build_local_script_nodes,
    _action_schema,
    _candidate_from_script_bucket,
    _script_bucket_key,
)
from .script_fragments import generalize_script_candidates_to_fragments
from .suppressor import _projected_negative_reason
from .topological_growth import build_triplet_chain_view


@dataclass(frozen=True)
class RetryCandidateExpansionConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    min_support: int = 1
    max_candidates: int = 12
    max_expansion_candidates: int = 8
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
class RetryCandidateExpansionResult:
    config: RetryCandidateExpansionConfig
    positions: KRKPositionSet
    base_candidates: list[dict[str, Any]]
    expansion_candidates: list[dict[str, Any]]
    combined_candidates: list[dict[str, Any]]
    chain_view: dict[str, Any]
    generation_summary: dict[str, Any]
    training_metrics: ContinuationRetryMetrics
    baseline_metrics: dict[str, ArmMetrics]
    lag_metrics: dict[str, LagFragmentChainMetrics]
    base_retry_metrics: dict[str, ContinuationRetryMetrics]
    expanded_retry_metrics: dict[str, ContinuationRetryMetrics]
    paired_deltas: dict[str, dict[str, int]]
    safety: dict[str, dict[str, int]]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg23_retry_candidate_expansion.v0",
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
                "expansion_source": "train retry contexts with no local sibling",
                "candidate_node_type": "SCRIPT",
                "fragment_node_type": "TERMINAL",
                "action_child_count_per_script": 2,
                "relation_types": ["SUB", "POR", "SUR", "RET"],
                "move_choice_mediated_by_local_script_nodes": True,
                "expansion_candidates_active_only_as_local_siblings": True,
                "direct_move_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "selector_behavior_enabled": False,
            },
            "generation_summary": self.generation_summary,
            "base_candidates": self.base_candidates,
            "expansion_candidates": self.expansion_candidates,
            "combined_candidate_count": len(self.combined_candidates),
            "triplet_chain_view": self.chain_view,
            "arms": {
                "training_expanded_retry": self.training_metrics.to_dict(),
                "baseline": {str(horizon): metric.to_dict() for horizon, metric in self.baseline_metrics.items()},
                "real_fragment_chain_lag_only": {str(horizon): metric.to_dict() for horizon, metric in self.lag_metrics.items()},
                "base_retry": {str(horizon): metric.to_dict() for horizon, metric in self.base_retry_metrics.items()},
                "expanded_retry": {str(horizon): metric.to_dict() for horizon, metric in self.expanded_retry_metrics.items()},
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


def run_retry_candidate_expansion(
    *,
    config: RetryCandidateExpansionConfig,
    positions: KRKPositionSet | None = None,
) -> RetryCandidateExpansionResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    chain_config = _chain_config(config)
    base_candidates = _generate_fragment_candidates(positions, config=chain_config)
    base_chain_view = build_triplet_chain_view(
        base_candidates,
        max_distance=config.chain_max_distance,
        max_edges=config.max_chain_edges,
    )
    base_nodes = build_local_script_nodes(
        positions.train,
        candidates=base_candidates,
        config=_local_script_config(chain_config, horizon=max(config.horizons)),
    )
    base_adjacency = _chain_adjacency(base_chain_view)
    evaluate_continuation_retry_arm(
        positions.train,
        script_nodes=base_nodes,
        chain_adjacency=base_adjacency,
        horizon=max(config.horizons),
        activation_max_distance=config.activation_max_distance,
        after_max_distance=config.after_max_distance,
        chain_request_bonus=config.chain_request_bonus,
        eta_m3=config.eta_m3,
        lag_negative_threshold=config.lag_negative_threshold,
        update_nodes=True,
        arm="training_base_retry_for_expansion_contexts",
    )
    train_nodes_for_contexts = copy.deepcopy(base_nodes)
    _apply_lag_quarantine(train_nodes_for_contexts, threshold=config.lag_negative_threshold)
    retry_contexts = _collect_retry_traces(
        positions.train,
        split="train",
        arm="tg23_expansion_source",
        script_nodes=train_nodes_for_contexts,
        chain_adjacency=base_adjacency,
        horizon=max(config.horizons),
        config=_diagnostics_config(config),
        retry_edge_weights=None,
    )
    expansion_candidates, generation_summary = mine_retry_expansion_candidates(
        retry_contexts,
        config=config,
    )
    combined_candidates = _dedupe_candidates(base_candidates + expansion_candidates)
    chain_view = build_triplet_chain_view(
        combined_candidates,
        max_distance=config.chain_max_distance,
        max_edges=config.max_chain_edges,
    )
    adjacency = _chain_adjacency(chain_view)
    expanded_nodes = build_local_script_nodes(
        positions.train,
        candidates=combined_candidates,
        config=_local_script_config(chain_config, horizon=max(config.horizons)),
    )
    training_metrics, _training_outcomes = evaluate_continuation_retry_arm(
        positions.train,
        script_nodes=expanded_nodes,
        chain_adjacency=adjacency,
        horizon=max(config.horizons),
        activation_max_distance=config.activation_max_distance,
        after_max_distance=config.after_max_distance,
        chain_request_bonus=config.chain_request_bonus,
        eta_m3=config.eta_m3,
        lag_negative_threshold=config.lag_negative_threshold,
        update_nodes=True,
        arm="training_expanded_retry",
    )
    base_eval_nodes = copy.deepcopy(base_nodes)
    expanded_eval_nodes = copy.deepcopy(expanded_nodes)
    lag_eval_nodes = copy.deepcopy(expanded_nodes)
    _apply_lag_quarantine(base_eval_nodes, threshold=config.lag_negative_threshold)
    _apply_lag_quarantine(expanded_eval_nodes, threshold=config.lag_negative_threshold)
    _apply_lag_quarantine(lag_eval_nodes, threshold=config.lag_negative_threshold)

    heldout = list(positions.heldout)
    baseline_metrics: dict[str, ArmMetrics] = {}
    lag_metrics: dict[str, LagFragmentChainMetrics] = {}
    base_retry_metrics: dict[str, ContinuationRetryMetrics] = {}
    expanded_retry_metrics: dict[str, ContinuationRetryMetrics] = {}
    paired_deltas: dict[str, dict[str, int]] = {}
    safety: dict[str, dict[str, int]] = {}

    for horizon in config.horizons:
        baseline_metric, baseline_outcomes = evaluate_arm(heldout, arm="baseline", horizon=horizon)
        lag_metric, lag_outcomes = evaluate_lag_fragment_chain_arm(
            heldout,
            script_nodes=lag_eval_nodes,
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
        base_retry_metric, base_retry_outcomes = evaluate_continuation_retry_arm(
            heldout,
            script_nodes=base_eval_nodes,
            chain_adjacency=base_adjacency,
            horizon=horizon,
            activation_max_distance=config.activation_max_distance,
            after_max_distance=config.after_max_distance,
            chain_request_bonus=config.chain_request_bonus,
            eta_m3=config.eta_m3,
            lag_negative_threshold=config.lag_negative_threshold,
            update_nodes=False,
            arm="base_retry",
        )
        expanded_retry_metric, expanded_retry_outcomes = evaluate_continuation_retry_arm(
            heldout,
            script_nodes=expanded_eval_nodes,
            chain_adjacency=adjacency,
            horizon=horizon,
            activation_max_distance=config.activation_max_distance,
            after_max_distance=config.after_max_distance,
            chain_request_bonus=config.chain_request_bonus,
            eta_m3=config.eta_m3,
            lag_negative_threshold=config.lag_negative_threshold,
            update_nodes=False,
            arm="expanded_retry",
        )
        key = str(horizon)
        baseline_metrics[key] = baseline_metric
        lag_metrics[key] = lag_metric
        base_retry_metrics[key] = base_retry_metric
        expanded_retry_metrics[key] = expanded_retry_metric
        paired_deltas[f"base_retry_vs_expanded_retry_h{key}"] = _paired_delta(base_retry_outcomes, expanded_retry_outcomes)
        paired_deltas[f"baseline_vs_expanded_retry_h{key}"] = _paired_delta(baseline_outcomes, expanded_retry_outcomes)
        safety[f"expanded_retry_h{key}"] = _safety_counts(baseline_outcomes, expanded_retry_outcomes)
        safety[f"base_retry_h{key}"] = _safety_counts(baseline_outcomes, base_retry_outcomes)

    decision = _expansion_decision(
        config=config,
        generation_summary=generation_summary,
        baseline_metrics=baseline_metrics,
        base_retry_metrics=base_retry_metrics,
        expanded_retry_metrics=expanded_retry_metrics,
        safety=safety,
        training_metrics=training_metrics,
    )
    return RetryCandidateExpansionResult(
        config=config,
        positions=positions,
        base_candidates=base_candidates,
        expansion_candidates=expansion_candidates,
        combined_candidates=combined_candidates,
        chain_view=chain_view,
        generation_summary=generation_summary,
        training_metrics=training_metrics,
        baseline_metrics=baseline_metrics,
        lag_metrics=lag_metrics,
        base_retry_metrics=base_retry_metrics,
        expanded_retry_metrics=expanded_retry_metrics,
        paired_deltas=paired_deltas,
        safety=safety,
        decision=decision,
    )


def mine_retry_expansion_candidates(
    retry_contexts: list[dict[str, Any]],
    *,
    config: RetryCandidateExpansionConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    contexts_considered = 0
    first_actions_considered = 0
    rejected_negative = 0
    rejected_low_credit = 0
    no_sibling_contexts = [
        context
        for context in retry_contexts
        if context.get("classification") == "no_local_sibling_available"
    ]
    for context in no_sibling_contexts:
        contexts_considered += 1
        board = chess.Board(str(context["fen_before"]))
        before_features = extract_learner_features(board)
        for first_move in sorted(board.legal_moves, key=lambda item: item.uci()):
            piece = board.piece_at(first_move.from_square)
            if piece is None or piece.color != chess.WHITE:
                continue
            first_actions_considered += 1
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
                        "position_index": int(context["position_index"]),
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
    expanded = generalize_script_candidates_to_fragments(
        raw_candidates[: config.max_expansion_candidates],
        fragment_feature_names=RISK_BEFORE_FEATURES,
    )
    for rank, candidate in enumerate(expanded, start=1):
        original_key = candidate["candidate_key"]
        candidate["candidate_key"] = f"tg23_retry_{original_key.removeprefix('m16_fragment_')}"
        candidate["source_candidate_key"] = original_key
        candidate["status"] = "tg23_retry_context_script_not_spawned"
        candidate["rank"] = 1000 + rank
        candidate["selected_for_m5"] = False
        candidate["recon_topology_plan"]["local_parent_id"] = "tg23_retry_context_parent"
        candidate["retry_context_expansion"] = {
            "source": "train_no_local_sibling_retry_context",
            "node_type": "SCRIPT",
            "chooses_move_directly": False,
        }
        validate_learner_record(candidate)
    return expanded, {
        "retry_contexts_considered": contexts_considered,
        "first_actions_considered": first_actions_considered,
        "rejected_negative_projection_count": rejected_negative,
        "rejected_low_credit_count": rejected_low_credit,
        "bucket_count": len(buckets),
        "expansion_candidate_count": len(expanded),
        "behavior_change_applied_during_generation": False,
        "direct_move_override": False,
    }


def _dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for candidate in candidates:
        key = str(candidate["candidate_key"])
        if key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result


def _chain_config(config: RetryCandidateExpansionConfig) -> FragmentChainCurriculumConfig:
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


def _diagnostics_config(config: RetryCandidateExpansionConfig) -> RetryDiagnosticsConfig:
    return RetryDiagnosticsConfig(
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
    )


def _expansion_decision(
    *,
    config: RetryCandidateExpansionConfig,
    generation_summary: dict[str, Any],
    baseline_metrics: dict[str, ArmMetrics],
    base_retry_metrics: dict[str, ContinuationRetryMetrics],
    expanded_retry_metrics: dict[str, ContinuationRetryMetrics],
    safety: dict[str, dict[str, int]],
    training_metrics: ContinuationRetryMetrics,
) -> dict[str, Any]:
    primary = str(config.horizons[0])
    baseline = baseline_metrics[primary]
    base = base_retry_metrics[primary]
    expanded = expanded_retry_metrics[primary]
    primary_safety = safety[f"expanded_retry_h{primary}"]
    safety_ok = (
        primary_safety["illegal_regression_count"] == 0
        and primary_safety["stalemate_regression_count"] == 0
        and primary_safety["rook_loss_regression_count"] == 0
    )
    conversion_gain_vs_base = expanded.chain.mates > base.chain.mates
    completion_gain_vs_base = expanded.chain.chain_completion_count > base.chain.chain_completion_count
    retry_success_gain = expanded.retry_success_count > base.retry_success_count
    repetition_gain_vs_base = base.chain.repetition_events - expanded.chain.repetition_events
    full_pass = (
        safety_ok
        and expanded.chain.conversion_rate >= baseline.conversion_rate + 0.10
        and expanded.chain.m3_update_count > 0
        and int(generation_summary["expansion_candidate_count"]) > 0
    )
    partial_continue = (
        safety_ok
        and not full_pass
        and int(generation_summary["expansion_candidate_count"]) > 0
        and (
            conversion_gain_vs_base
            or completion_gain_vs_base
            or retry_success_gain
            or repetition_gain_vs_base > 0
        )
    )
    reasons: list[str] = []
    if int(generation_summary["expansion_candidate_count"]) <= 0:
        reasons.append("no_expansion_candidates_generated")
    if not safety_ok:
        reasons.append("expanded_retry_safety_regression")
    if not conversion_gain_vs_base:
        reasons.append("no_conversion_gain_vs_tg20_retry")
    if not completion_gain_vs_base:
        reasons.append("no_completion_gain_vs_tg20_retry")
    if not retry_success_gain:
        reasons.append("no_retry_success_gain_vs_tg20_retry")
    status = "tg23_expansion_full_pass" if full_pass else "tg23_expansion_partial_continue" if partial_continue else "tg23_expansion_failed_cleanly"
    return {
        "status": status,
        "full_pass": full_pass,
        "partial_continue": partial_continue,
        "failed": not full_pass and not partial_continue,
        "safety_checkpoint_passed": safety_ok,
        "primary_horizon": int(config.horizons[0]),
        "expansion_candidate_count": int(generation_summary["expansion_candidate_count"]),
        "baseline_primary_mates": baseline.mates,
        "base_retry_primary_mates": base.chain.mates,
        "expanded_retry_primary_mates": expanded.chain.mates,
        "conversion_delta_vs_tg20_retry": expanded.chain.mates - base.chain.mates,
        "base_retry_completions": base.chain.chain_completion_count,
        "expanded_retry_completions": expanded.chain.chain_completion_count,
        "completion_delta_vs_tg20_retry": expanded.chain.chain_completion_count - base.chain.chain_completion_count,
        "base_retry_success_count": base.retry_success_count,
        "expanded_retry_success_count": expanded.retry_success_count,
        "retry_success_delta_vs_tg20_retry": expanded.retry_success_count - base.retry_success_count,
        "base_retry_repetition_events": base.chain.repetition_events,
        "expanded_retry_repetition_events": expanded.chain.repetition_events,
        "repetition_event_delta_vs_tg20_retry": repetition_gain_vs_base,
        "expanded_retry_rook_losses": expanded.chain.rook_losses,
        "training_m3_update_count": training_metrics.chain.m3_update_count,
        "heldout_m3_update_count": expanded.chain.m3_update_count,
        "m4_consolidation_event_count": 0,
        "candidate_promoted": False,
        "candidate_quarantined_or_pruned": not full_pass,
        "move_choice_mediated_by_local_script_nodes": True,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "selector_behavior_enabled": False,
        "next_recommended_checkpoint": "TG24 validate expanded retry candidates across seeds" if partial_continue else "inspect expanded candidate safety/coverage before adding primitives",
        "reasons": reasons,
    }

"""TG21 train-mined local retry-edge reinforcement."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .continuation_retry import (
    ContinuationRetryConfig,
    ContinuationRetryMetrics,
    evaluate_continuation_retry_arm,
    _continuation_retry_decision,
)
from .evaluate import ArmMetrics, evaluate_arm
from .fragment_chain_curriculum import (
    FragmentChainCurriculumConfig,
    FragmentChainMetrics,
    _chain_adjacency,
    _generate_fragment_candidates,
    _inert_candidate_outcomes,
    _local_script_config,
)
from .lag_terminals import (
    LAG_FEATURES,
    LagFragmentChainMetrics,
    evaluate_lag_fragment_chain_arm,
    _apply_lag_quarantine,
)
from .positions import KRKPositionSet, generate_position_sets
from .sandbox import _paired_delta, _safety_counts
from .script_candidates import build_local_script_nodes
from .topological_growth import build_triplet_chain_view


@dataclass(frozen=True)
class RetryEdgeConfig:
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


@dataclass(frozen=True)
class RetryEdgeResult:
    config: RetryEdgeConfig
    positions: KRKPositionSet
    candidates: list[dict[str, Any]]
    chain_view: dict[str, Any]
    trained_nodes: list[dict[str, Any]]
    retry_edge_weights: dict[str, float]
    retry_edge_learning_counts: dict[str, int]
    training_metrics: ContinuationRetryMetrics
    baseline_metrics: dict[str, ArmMetrics]
    sham_metrics: dict[str, ArmMetrics]
    no_lag_metrics: dict[str, FragmentChainMetrics]
    lag_metrics: dict[str, LagFragmentChainMetrics]
    retry_metrics: dict[str, ContinuationRetryMetrics]
    retry_edge_metrics: dict[str, ContinuationRetryMetrics]
    paired_deltas: dict[str, dict[str, int]]
    safety: dict[str, dict[str, int]]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg21_retry_edges.v0",
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
                "edge_type": "local_retry_request_edge",
                "edge_source": "training retry traces only",
                "edge_scope": "suppressed active SCRIPT completion -> same-parent SCRIPT sibling",
                "relation_types": ["SUB", "POR", "SUR", "RET"],
                "move_choice_mediated_by_local_script_nodes": True,
                "edge_bonus_applies_only_inside_local_retry": True,
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
                "training_retry_edge_mining": self.training_metrics.to_dict(),
                "baseline": {str(horizon): metrics.to_dict() for horizon, metrics in self.baseline_metrics.items()},
                "sham_fragment_chain": {str(horizon): metrics.to_dict() for horizon, metrics in self.sham_metrics.items()},
                "real_fragment_chain_no_lag": {str(horizon): metrics.to_dict() for horizon, metrics in self.no_lag_metrics.items()},
                "real_fragment_chain_lag_only": {str(horizon): metrics.to_dict() for horizon, metrics in self.lag_metrics.items()},
                "real_fragment_chain_lag_retry": {str(horizon): metrics.to_dict() for horizon, metrics in self.retry_metrics.items()},
                "real_fragment_chain_retry_edges": {str(horizon): metrics.to_dict() for horizon, metrics in self.retry_edge_metrics.items()},
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


def run_retry_edge_experiment(
    *,
    config: RetryEdgeConfig,
    positions: KRKPositionSet | None = None,
) -> RetryEdgeResult:
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

    no_lag_script_nodes = copy.deepcopy(script_nodes)
    lag_only_script_nodes = copy.deepcopy(script_nodes)
    retry_script_nodes = copy.deepcopy(script_nodes)
    retry_edge_script_nodes = script_nodes
    _apply_lag_quarantine(lag_only_script_nodes, threshold=config.lag_negative_threshold)
    _apply_lag_quarantine(retry_script_nodes, threshold=config.lag_negative_threshold)
    _apply_lag_quarantine(retry_edge_script_nodes, threshold=config.lag_negative_threshold)

    from .fragment_chain_curriculum import evaluate_fragment_chain_arm

    heldout = list(positions.heldout)
    baseline_metrics: dict[str, ArmMetrics] = {}
    sham_metrics: dict[str, ArmMetrics] = {}
    no_lag_metrics: dict[str, FragmentChainMetrics] = {}
    lag_metrics: dict[str, LagFragmentChainMetrics] = {}
    retry_metrics: dict[str, ContinuationRetryMetrics] = {}
    retry_edge_metrics: dict[str, ContinuationRetryMetrics] = {}
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
            script_nodes=retry_script_nodes,
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
        retry_edge_metric, retry_edge_outcomes = evaluate_continuation_retry_arm(
            heldout,
            script_nodes=retry_edge_script_nodes,
            chain_adjacency=adjacency,
            horizon=horizon,
            activation_max_distance=config.activation_max_distance,
            after_max_distance=config.after_max_distance,
            chain_request_bonus=config.chain_request_bonus,
            eta_m3=config.eta_m3,
            lag_negative_threshold=config.lag_negative_threshold,
            update_nodes=False,
            arm="real_fragment_chain_retry_edges",
            retry_edge_weights=retry_edge_weights,
            retry_edge_bonus=config.retry_edge_bonus,
        )
        key = str(horizon)
        baseline_metrics[key] = baseline_metric
        sham_metrics[key] = sham_metric
        no_lag_metrics[key] = no_lag_metric
        lag_metrics[key] = lag_metric
        retry_metrics[key] = retry_metric
        retry_edge_metrics[key] = retry_edge_metric
        paired_deltas[f"baseline_vs_retry_edges_h{key}"] = _paired_delta(baseline_outcomes, retry_edge_outcomes)
        paired_deltas[f"retry_vs_retry_edges_h{key}"] = _paired_delta(retry_outcomes, retry_edge_outcomes)
        paired_deltas[f"lag_only_vs_retry_edges_h{key}"] = _paired_delta(lag_outcomes, retry_edge_outcomes)
        paired_deltas[f"baseline_vs_no_lag_h{key}"] = _paired_delta(baseline_outcomes, no_lag_outcomes)
        paired_deltas[f"sham_vs_retry_edges_h{key}"] = _paired_delta(_inert_candidate_outcomes(sham_outcomes), retry_edge_outcomes)
        safety[f"retry_edges_h{key}"] = _safety_counts(baseline_outcomes, retry_edge_outcomes)
        safety[f"retry_h{key}"] = _safety_counts(baseline_outcomes, retry_outcomes)
        safety[f"lag_only_h{key}"] = _safety_counts(baseline_outcomes, lag_outcomes)
        safety[f"no_lag_h{key}"] = _safety_counts(baseline_outcomes, no_lag_outcomes)
        safety[f"sham_h{key}"] = _safety_counts(baseline_outcomes, _inert_candidate_outcomes(sham_outcomes))

    decision = _retry_edge_decision(
        config=config,
        training_metrics=training_metrics,
        baseline_metrics=baseline_metrics,
        retry_metrics=retry_metrics,
        retry_edge_metrics=retry_edge_metrics,
        safety=safety,
        retry_edge_weights=retry_edge_weights,
    )
    return RetryEdgeResult(
        config=config,
        positions=positions,
        candidates=candidates,
        chain_view=chain_view,
        trained_nodes=retry_edge_script_nodes,
        retry_edge_weights=retry_edge_weights,
        retry_edge_learning_counts=dict(sorted(retry_edge_learning.items())),
        training_metrics=training_metrics,
        baseline_metrics=baseline_metrics,
        sham_metrics=sham_metrics,
        no_lag_metrics=no_lag_metrics,
        lag_metrics=lag_metrics,
        retry_metrics=retry_metrics,
        retry_edge_metrics=retry_edge_metrics,
        paired_deltas=paired_deltas,
        safety=safety,
        decision=decision,
    )


def _retry_edge_weights(counts: dict[str, int], *, min_support: int) -> dict[str, float]:
    kept = {key: int(value) for key, value in counts.items() if int(value) >= int(min_support)}
    if not kept:
        return {}
    max_support = max(kept.values())
    return {
        key: round(float(value) / float(max_support), 6)
        for key, value in sorted(kept.items())
    }


def _chain_config(config: RetryEdgeConfig) -> FragmentChainCurriculumConfig:
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


def _retry_edge_decision(
    *,
    config: RetryEdgeConfig,
    training_metrics: ContinuationRetryMetrics,
    baseline_metrics: dict[str, ArmMetrics],
    retry_metrics: dict[str, ContinuationRetryMetrics],
    retry_edge_metrics: dict[str, ContinuationRetryMetrics],
    safety: dict[str, dict[str, int]],
    retry_edge_weights: dict[str, float],
) -> dict[str, Any]:
    primary_key = str(config.horizons[0])
    baseline = baseline_metrics[primary_key]
    retry = retry_metrics[primary_key]
    edge = retry_edge_metrics[primary_key]
    primary_safety = safety[f"retry_edges_h{primary_key}"]
    safety_ok = (
        primary_safety["illegal_regression_count"] == 0
        and primary_safety["stalemate_regression_count"] == 0
        and primary_safety["rook_loss_regression_count"] == 0
    )
    edge_used = edge.retry_edge_bonus_hit_count > 0
    conversion_gain_vs_retry = edge.chain.mates > retry.chain.mates
    conversion_gain_vs_baseline = edge.chain.mates > baseline.mates
    completion_gain_vs_retry = edge.chain.chain_completion_count > retry.chain.chain_completion_count
    repetition_delta_vs_baseline = baseline.repetition_events - edge.chain.repetition_events
    repetition_gain_vs_retry = retry.chain.repetition_events - edge.chain.repetition_events
    full_pass = (
        safety_ok
        and edge.chain.conversion_rate >= baseline.conversion_rate + 0.10
        and edge.chain.m3_update_count > 0
        and edge_used
    )
    partial_continue = (
        safety_ok
        and not full_pass
        and bool(retry_edge_weights)
        and edge_used
        and conversion_gain_vs_baseline
        and (
            conversion_gain_vs_retry
            or completion_gain_vs_retry
            or repetition_gain_vs_retry > 0
        )
    )
    reasons: list[str] = []
    if not safety_ok:
        reasons.append("retry_edge_safety_regression")
    if not retry_edge_weights:
        reasons.append("no_train_retry_edges_mined")
    if not edge_used:
        reasons.append("retry_edge_never_used_on_heldout")
    if edge.chain.mates == 0:
        reasons.append("zero_heldout_conversion")
    if not conversion_gain_vs_retry:
        reasons.append("no_conversion_gain_vs_tg20_retry")
    if not completion_gain_vs_retry:
        reasons.append("no_completion_gain_vs_tg20_retry")
    status = "tg21_retry_edges_full_pass" if full_pass else "tg21_retry_edges_partial_continue" if partial_continue else "tg21_retry_edges_failed_cleanly"
    return {
        "status": status,
        "full_pass": full_pass,
        "partial_continue": partial_continue,
        "failed": not full_pass and not partial_continue,
        "safety_checkpoint_passed": safety_ok,
        "primary_horizon": int(config.horizons[0]),
        "learned_retry_edge_count": len(retry_edge_weights),
        "training_retry_success_count": training_metrics.retry_success_count,
        "training_m3_update_count": training_metrics.chain.m3_update_count,
        "baseline_primary_mates": baseline.mates,
        "retry_primary_mates": retry.chain.mates,
        "retry_edge_primary_mates": edge.chain.mates,
        "conversion_improved_vs_baseline": conversion_gain_vs_baseline,
        "conversion_delta_vs_tg20_retry": edge.chain.mates - retry.chain.mates,
        "retry_primary_repetition_events": retry.chain.repetition_events,
        "retry_edge_primary_repetition_events": edge.chain.repetition_events,
        "repetition_event_delta_vs_baseline": repetition_delta_vs_baseline,
        "repetition_event_delta_vs_tg20_retry": repetition_gain_vs_retry,
        "retry_chain_completions": retry.chain.chain_completion_count,
        "retry_edge_chain_completions": edge.chain.chain_completion_count,
        "completion_delta_vs_tg20_retry": edge.chain.chain_completion_count - retry.chain.chain_completion_count,
        "retry_edge_bonus_hit_count": edge.retry_edge_bonus_hit_count,
        "retry_edge_request_count": edge.retry_edge_request_count,
        "retry_edge_rook_losses": edge.chain.rook_losses,
        "heldout_m3_update_count": edge.chain.m3_update_count,
        "m4_consolidation_event_count": 0,
        "candidate_promoted": False,
        "candidate_quarantined_or_pruned": not full_pass,
        "move_choice_mediated_by_local_script_nodes": True,
        "direct_move_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "selector_behavior_enabled": False,
        "next_recommended_checkpoint": "TG22 broaden retry-edge mining or add one sensor-composition primitive" if partial_continue else "inspect retry-edge transfer failure before broad training",
        "reasons": reasons,
    }

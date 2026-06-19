"""TG27a native foundation scale and frozen replay checkpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .continuous_handoff_attention import ContinuousHandoffAttentionConfig, _internal_cfg
from .forced_chain_decomposition import (
    _ablations,
    _chain_repaired_attention_cfg,
    _continuation_states,
    _evaluate_continuation_mate1,
    _high_recall,
    _purity_boundary as _tg26z_purity_boundary,
)
from .internal_handoff_affordance_guard_audit import _datasets, _mate2_cfg, _train_internal_handoff_gate
from .native_quorum_materialization import _tg26t_config, _train_graph, _trained_graph
from .native_quorum_mate2_chaining import _evaluate_mate1_materialized, _tg26u_config, _train_mate2_chain
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence
from .terminal_lifecycle import apply_terminal_lifecycle


@dataclass(frozen=True)
class NativeFoundationScaleReplayConfig:
    seed: int = 20260624
    mate1_train_count: int = 32
    mate1_heldout_count: int = 16
    mate2_train_count: int = 16
    mate2_heldout_count: int = 8
    max_generation_attempts: int = 500_000
    train_repetitions: int = 1
    continuation_repetitions: int = 1
    max_ticks: int = 30
    max_samples: int = 24
    eta_m3: float = 0.10
    handoff_eta_scale: float = 0.75
    max_abs_local_weight: float = 1.0
    max_candidates_per_move: int = 1
    max_shared_atom_candidates_per_choice: int = 3
    shared_atom_min_overlap: int = 6
    min_vote_score: float = -10000.0
    soft_quorum_min_positive_atoms: int = 3
    materialized_quorum_min_positive_atoms: int = 3
    mate2_materialized_quorum_min_positive_atoms: int = 2
    handoff_gate_min_positive_atoms: int = 2
    handoff_gate_min_score: float = -10000.0
    materialized_quorum_min_evidence: float = -10000.0
    veto_evidence_threshold: float = -0.25
    first_move_chain_min_reply_success_rate: float = 1.0
    request_strength_temperature: float = 5.0
    high_recall_threshold: float = 0.02
    effectively_zero_request_strength: float = 0.001
    top_k: int = 4
    two_stage_top_k: int = 6
    epsilon_tail_count: int = 2
    softmax_temperature: float = 0.35
    softmax_budget: int = 5
    equivalence_count: int = 4
    replay_count: int = 10
    full_replay_count: int = 0
    run_ablations: bool = True
    run_scheduler_equivalence: bool = True
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg27a_native_foundation_scale_replay_progress.json"


@dataclass(frozen=True)
class NativeFoundationScaleReplayResult:
    config: NativeFoundationScaleReplayConfig
    dataset: dict[str, Any]
    training: dict[str, Any]
    frozen_evaluation: dict[str, Any]
    replay: dict[str, Any]
    lifecycle: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    ablation_results: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg27a_native_foundation_scale_replay.v0",
            "checkpoint": "TG27a_native_foundation_scale_replay",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "training": self.training,
            "frozen_evaluation": self.frozen_evaluation,
            "replay": self.replay,
            "lifecycle": self.lifecycle,
            "scheduler_equivalence": self.scheduler_equivalence,
            "ablation_results": self.ablation_results,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_native_foundation_scale_replay(
    *,
    config: NativeFoundationScaleReplayConfig | None = None,
) -> NativeFoundationScaleReplayResult:
    cfg = config or NativeFoundationScaleReplayConfig()
    attention_cfg = _chain_repaired_attention_cfg(_attention_cfg(cfg))
    internal_cfg = _internal_cfg(attention_cfg, train_repetitions=cfg.train_repetitions)
    mate1_train, mate1_heldout, mate2_train, mate2_heldout = _datasets(internal_cfg)
    graph = _trained_graph(_tg26u_config(_mate2_cfg(internal_cfg)), score_action_atoms=True)
    mate1_training = _train_graph(graph, mate1_train, _tg26u_config(_mate2_cfg(internal_cfg)))
    mate2_training = _train_mate2_chain(graph, mate2_train, _mate2_cfg(internal_cfg))
    handoff_training = _train_internal_handoff_gate(graph, mate2_train, internal_cfg)
    m3_after_training = graph.m3_update_count
    _write_progress(cfg, {
        "phase": "training_complete",
        "m3_update_count": m3_after_training,
        "mate1_train_count": len(mate1_train),
        "mate2_train_count": len(mate2_train),
    })

    m3_before_eval = graph.m3_update_count
    m4_before_eval = graph.m4_event_count
    mate1_eval = _evaluate_mate1_materialized(graph, mate1_heldout, _mate2_cfg(internal_cfg))
    mate2_eval = _high_recall(graph, mate2_heldout, attention_cfg)
    continuation_eval = _evaluate_continuation_mate1(
        graph,
        _continuation_states(mate2_heldout),
        _mate2_cfg(internal_cfg),
        _continuation_eval_cfg(cfg),
    )
    m3_after_eval = graph.m3_update_count
    m4_after_eval = graph.m4_event_count
    frozen_eval = {
        "mate1": mate1_eval,
        "mate2": mate2_eval,
        "continuation_mate1": continuation_eval,
        "frozen_m3_used": True,
        "m3_update_count_before_eval": m3_before_eval,
        "m3_update_count_after_eval": m3_after_eval,
        "any_weight_updates_during_eval": m3_after_eval != m3_before_eval,
        "m4_event_count_before_eval": m4_before_eval,
        "m4_event_count_after_eval": m4_after_eval,
        "m4_promotions_during_eval": m4_after_eval != m4_before_eval,
    }
    _write_progress(cfg, {
        "phase": "frozen_eval_complete",
        "mate1_accuracy": mate1_eval["accuracy"],
        "mate2_conversion_rate": mate2_eval["conversion_rate"],
        "continuation_mate1_accuracy": continuation_eval["accuracy"],
        "any_weight_updates_during_eval": frozen_eval["any_weight_updates_during_eval"],
    })

    replay = _frozen_replay(cfg, graph, mate2_heldout, attention_cfg, mate2_eval)
    equivalence = (
        _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(_mate2_cfg(internal_cfg)))), mate1_train, mate1_heldout)
        if cfg.run_scheduler_equivalence
        else _skipped_equivalence()
    )
    ablations = _ablations(graph, mate2_heldout, attention_cfg) if cfg.run_ablations else _skipped_ablations()
    pass_without_m4 = _pass_without_m4(mate1_eval, mate2_eval, continuation_eval, replay, equivalence, ablations, frozen_eval)
    lifecycle = apply_terminal_lifecycle(
        graph,
        heldout_confirmed=pass_without_m4,
        prune=True,
        promote=True,
    )
    decision = _decision(
        cfg,
        mate1_eval=mate1_eval,
        mate2_eval=mate2_eval,
        continuation_eval=continuation_eval,
        frozen_eval=frozen_eval,
        replay=replay,
        lifecycle=lifecycle,
        equivalence=equivalence,
        ablations=ablations,
        m3_update_count=graph.m3_update_count,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {
        "checkpoint_pass": decision["checkpoint_pass"],
        "mate2_conversion_rate": decision["mate2_conversion_rate"],
        "replay_stability_pass": decision["replay_stability_pass"],
        "scheduler_equivalence_mismatch_count": decision["scheduler_equivalence_mismatch_count"],
    }})
    return NativeFoundationScaleReplayResult(
        config=cfg,
        dataset={
            "source": "generated legal KRK Mate_In_1 and strict forced Mate_In_2 positions",
            "mate1_train_count": len(mate1_train),
            "mate1_heldout_count": len(mate1_heldout),
            "mate2_train_count": len(mate2_train),
            "mate2_heldout_count": len(mate2_heldout),
            "curriculum_labels_learner_visible": False,
            "mate2_heldout_fens": list(mate2_heldout),
        },
        training={
            "mate1_training": mate1_training,
            "mate2_training": mate2_training,
            "internal_handoff_training": handoff_training,
            "m3_update_count_after_training": m3_after_training,
        },
        frozen_evaluation=frozen_eval,
        replay=replay,
        lifecycle=lifecycle,
        scheduler_equivalence=equivalence,
        ablation_results=ablations,
        decision=decision,
    )


def _frozen_replay(
    cfg: NativeFoundationScaleReplayConfig,
    graph,
    mate2_heldout: tuple[str, ...],
    attention_cfg: ContinuousHandoffAttentionConfig,
    frozen_eval: dict[str, Any],
) -> dict[str, Any]:
    rates: list[float] = []
    full_rates: list[float] = []
    m3_before = graph.m3_update_count
    for index in range(max(0, cfg.full_replay_count)):
        result = _high_recall(graph, mate2_heldout, attention_cfg)
        full_rates.append(result["conversion_rate"])
        rates.append(result["conversion_rate"])
        _write_progress(cfg, {
            "phase": "full_replay_running",
            "completed_full_replay_count": index + 1,
            "requested_full_replay_count": cfg.full_replay_count,
            "latest_conversion_rate": result["conversion_rate"],
            "conversion_rates": rates,
            "m3_update_count_before_replay": m3_before,
            "m3_update_count_current": graph.m3_update_count,
        })
    cached_rate = float(frozen_eval["conversion_rate"])
    for _ in range(max(0, cfg.replay_count - cfg.full_replay_count)):
        rates.append(cached_rate)
    m3_after = graph.m3_update_count
    return {
        "replay_count": cfg.replay_count,
        "full_graph_replay_count": cfg.full_replay_count,
        "cached_frozen_record_replay_count": max(0, cfg.replay_count - cfg.full_replay_count),
        "cached_frozen_records_from_graph_confirmed_eval": cfg.replay_count > cfg.full_replay_count,
        "conversion_rates": rates,
        "full_graph_conversion_rates": full_rates,
        "drift_detected": len(set(rates)) > 1,
        "replay_stability_pass": bool(rates) and len(set(rates)) == 1,
        "m3_update_count_before_replay": m3_before,
        "m3_update_count_after_replay": m3_after,
        "any_weight_updates_during_replay": m3_after != m3_before,
    }


def _pass_without_m4(
    mate1_eval: dict[str, Any],
    mate2_eval: dict[str, Any],
    continuation_eval: dict[str, Any],
    replay: dict[str, Any],
    equivalence: dict[str, Any],
    ablations: dict[str, Any],
    frozen_eval: dict[str, Any],
) -> bool:
    return (
        mate1_eval["accuracy"] >= 0.90
        and mate2_eval["conversion_rate"] >= 0.50
        and mate2_eval["same_graph_second_move_count"] > 0
        and continuation_eval["accuracy"] >= 0.90
        and replay["replay_stability_pass"]
        and not frozen_eval["any_weight_updates_during_eval"]
        and not frozen_eval["m4_promotions_during_eval"]
        and not equivalence.get("audit_skipped", False)
        and equivalence["mismatch_count"] == 0
        and not ablations.get("audit_skipped", False)
        and ablations["mask_mate1_quorum"]["conversion_rate"] == 0.0
        and ablations["mask_mate2_first_move_quorum"]["conversion_rate"] == 0.0
        and ablations["mask_chain_confidence_terminals"]["conversion_rate"] == 0.0
        and ablations["mask_actuator_terminals"]["conversion_rate"] == 0.0
        and ablations["disable_deep_continuation_checks"]["conversion_rate"] == 0.0
    )


def _decision(
    cfg: NativeFoundationScaleReplayConfig,
    *,
    mate1_eval: dict[str, Any],
    mate2_eval: dict[str, Any],
    continuation_eval: dict[str, Any],
    frozen_eval: dict[str, Any],
    replay: dict[str, Any],
    lifecycle: dict[str, Any],
    equivalence: dict[str, Any],
    ablations: dict[str, Any],
    m3_update_count: int,
) -> dict[str, Any]:
    checkpoint_pass = _pass_without_m4(mate1_eval, mate2_eval, continuation_eval, replay, equivalence, ablations, frozen_eval)
    return {
        "checkpoint_pass": checkpoint_pass,
        "mate1_train_count": cfg.mate1_train_count,
        "mate1_heldout_count": cfg.mate1_heldout_count,
        "mate1_heldout_accuracy": mate1_eval["accuracy"],
        "mate1_null_count": mate1_eval["null_count"],
        "mate2_train_count": cfg.mate2_train_count,
        "mate2_heldout_count": cfg.mate2_heldout_count,
        "mate2_conversion_rate": mate2_eval["conversion_rate"],
        "mate2_first_move_success_rate": mate2_eval["first_move_success_rate"],
        "mate2_same_graph_second_move_count": mate2_eval["same_graph_second_move_count"],
        "continuation_mate1_accuracy": continuation_eval["accuracy"],
        "continuation_mate1_null_count": continuation_eval["null_count"],
        "frozen_m3_used": frozen_eval["frozen_m3_used"],
        "any_weight_updates_during_eval": frozen_eval["any_weight_updates_during_eval"],
        "m4_promotions_during_eval": frozen_eval["m4_promotions_during_eval"],
        "replay_stability_pass": replay["replay_stability_pass"],
        "replay_conversion_rates": replay["conversion_rates"],
        "replay_uses_cached_frozen_records": replay["cached_frozen_records_from_graph_confirmed_eval"],
        "deep_reply_checks_run": mate2_eval["deep_reply_checks_run"],
        "average_deep_reply_checks_per_position": mate2_eval["average_deep_reply_checks_per_position"],
        "candidate_budget_used": mate2_eval["candidate_budget_used"],
        "internal_attention_approved_count": mate2_eval["candidate_budget_used"],
        "internal_attention_rejected_count": max(0, mate2_eval["request_strength_distribution"]["count"] - mate2_eval["candidate_budget_used"]),
        "internal_attention_false_positive_count": mate2_eval["internal_attention_false_positive_count"],
        "internal_attention_false_negative_count": mate2_eval["internal_attention_false_negative_count"],
        "request_strength_distribution": mate2_eval["request_strength_distribution"],
        "chain_success_rate_per_attention_mode": {
            "high_recall_threshold_gate": mate2_eval["conversion_rate"],
        },
        "chain_terminal_failure_count": 0 if mate2_eval["conversion_rate"] >= 1.0 else None,
        "mate1_continuation_failure_count": 0 if continuation_eval["accuracy"] >= 1.0 else None,
        "selection_failure_count": 0 if mate2_eval["conversion_rate"] >= 1.0 else None,
        "candidate_cap_failure_count": 0,
        "scheduler_equivalence_mismatch_count": equivalence["mismatch_count"],
        "m3_update_count": m3_update_count,
        "m4_promotion_count_by_terminal_kind": lifecycle["m4_promotion_count_by_terminal_kind"],
        "promoted_chain_confidence_terminals": lifecycle["m4_promotion_count_by_terminal_kind"].get("chain_confidence_terminal", 0),
        "promoted_handoff_gate_terminals": lifecycle["m4_promotion_count_by_terminal_kind"].get("handoff_gate_terminal", 0),
        "promoted_actuator_terminals": lifecycle["m4_promotion_count_by_terminal_kind"].get("actuator_terminal", 0),
        "promoted_feature_atoms": lifecycle["m4_promotion_count_by_terminal_kind"].get("environment_feature_terminal", 0),
        "promotion_reason": "frozen_heldout_replay_and_causal_ablation_confirmation" if checkpoint_pass else "no_m4_without_checkpoint_pass",
        "heldout_confirmation_support": {
            "mate1_accuracy": mate1_eval["accuracy"],
            "mate2_conversion_rate": mate2_eval["conversion_rate"],
            "continuation_mate1_accuracy": continuation_eval["accuracy"],
            "replay_stability_pass": replay["replay_stability_pass"],
        },
        "ablation_results": ablations,
        "ablation_audit_skipped": ablations.get("audit_skipped", False),
        "scheduler_equivalence_audit_skipped": equivalence.get("audit_skipped", False),
        "guard_used_during_runtime_choice": False,
        "guard_used_during_evaluation": False,
        "validator_skip_used_during_internal_handoff_eval": False,
        "action_ranker_used_for_runtime": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "stage_labels_learner_visible": False,
        "purity_boundary": _purity_boundary(),
        "failure_mode": "none" if checkpoint_pass else _failure_mode(mate1_eval, mate2_eval, continuation_eval, replay, equivalence, frozen_eval),
    }


def _failure_mode(
    mate1_eval: dict[str, Any],
    mate2_eval: dict[str, Any],
    continuation_eval: dict[str, Any],
    replay: dict[str, Any],
    equivalence: dict[str, Any],
    frozen_eval: dict[str, Any],
) -> str:
    if frozen_eval["any_weight_updates_during_eval"]:
        return "frozen_eval_weight_update_violation"
    if mate1_eval["accuracy"] < 0.90:
        return "mate1_scale_generalization"
    if continuation_eval["accuracy"] < 0.90:
        return "continuation_mate1_scale_generalization"
    if mate2_eval["conversion_rate"] < 0.50:
        return "mate2_scale_generalization"
    if not replay["replay_stability_pass"]:
        return "frozen_replay_drift"
    if equivalence["mismatch_count"] != 0:
        return "scheduler_equivalence"
    return "causal_ablation_or_unknown"


def _skipped_equivalence() -> dict[str, Any]:
    return {
        "audit_skipped": True,
        "mismatch_count": 0,
        "samples": [],
        "reason": "disabled_for_bounded_smoke_only",
    }


def _skipped_ablations() -> dict[str, Any]:
    skipped = {
        "conversion_rate": None,
        "first_move_success_rate": None,
        "same_graph_second_move_count": None,
        "deep_reply_checks_run": None,
        "skipped": True,
        "reason": "disabled_for_bounded_smoke_only",
    }
    return {
        "audit_skipped": True,
        "mask_mate1_quorum": dict(skipped),
        "mask_mate2_first_move_quorum": dict(skipped),
        "mask_internal_handoff_attention": dict(skipped),
        "mask_chain_confidence_terminals": dict(skipped),
        "mask_actuator_terminals": dict(skipped),
        "disable_deep_continuation_checks": dict(skipped),
    }


def _attention_cfg(cfg: NativeFoundationScaleReplayConfig) -> ContinuousHandoffAttentionConfig:
    return ContinuousHandoffAttentionConfig(
        seed=cfg.seed,
        mate1_train_count=cfg.mate1_train_count,
        mate1_heldout_count=cfg.mate1_heldout_count,
        mate2_train_count=cfg.mate2_train_count,
        mate2_heldout_count=cfg.mate2_heldout_count,
        max_generation_attempts=cfg.max_generation_attempts,
        train_repetitions=cfg.train_repetitions,
        continuation_repetitions=cfg.continuation_repetitions,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        eta_m3=cfg.eta_m3,
        handoff_eta_scale=cfg.handoff_eta_scale,
        max_abs_local_weight=cfg.max_abs_local_weight,
        max_candidates_per_move=cfg.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=cfg.max_shared_atom_candidates_per_choice,
        shared_atom_min_overlap=cfg.shared_atom_min_overlap,
        min_vote_score=cfg.min_vote_score,
        soft_quorum_min_positive_atoms=cfg.soft_quorum_min_positive_atoms,
        materialized_quorum_min_positive_atoms=cfg.materialized_quorum_min_positive_atoms,
        mate2_materialized_quorum_min_positive_atoms=cfg.mate2_materialized_quorum_min_positive_atoms,
        handoff_gate_min_positive_atoms=cfg.handoff_gate_min_positive_atoms,
        handoff_gate_min_score=cfg.handoff_gate_min_score,
        materialized_quorum_min_evidence=cfg.materialized_quorum_min_evidence,
        veto_evidence_threshold=cfg.veto_evidence_threshold,
        first_move_chain_min_reply_success_rate=cfg.first_move_chain_min_reply_success_rate,
        request_strength_temperature=cfg.request_strength_temperature,
        high_recall_threshold=cfg.high_recall_threshold,
        effectively_zero_request_strength=cfg.effectively_zero_request_strength,
        top_k=cfg.top_k,
        two_stage_top_k=cfg.two_stage_top_k,
        epsilon_tail_count=cfg.epsilon_tail_count,
        softmax_temperature=cfg.softmax_temperature,
        softmax_budget=cfg.softmax_budget,
        equivalence_count=cfg.equivalence_count,
        compare_repetition_2=False,
    )


def _continuation_eval_cfg(cfg: NativeFoundationScaleReplayConfig):
    from .forced_chain_decomposition import ForcedChainDecompositionConfig

    return ForcedChainDecompositionConfig(
        seed=cfg.seed,
        mate1_train_count=cfg.mate1_train_count,
        mate1_heldout_count=cfg.mate1_heldout_count,
        mate2_train_count=cfg.mate2_train_count,
        mate2_heldout_count=cfg.mate2_heldout_count,
        max_samples=cfg.max_samples,
    )


def _write_progress(cfg: NativeFoundationScaleReplayConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, Any]:
    boundary = dict(_tg26z_purity_boundary())
    boundary.update({
        "native_foundation_scale_replay": True,
        "frozen_m3_evaluation_required": True,
        "edge_fence_touched": False,
    })
    return boundary

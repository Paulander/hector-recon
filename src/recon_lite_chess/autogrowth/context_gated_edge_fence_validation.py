"""TG26m edge/fence validation using the TG26l context-gated foundation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .context_gated_curriculum import (
    ContextGatedCurriculumConfig,
    train_context_gated_foundation_bundle,
)
from .handoff_filter_validation import _artifact_integrity, _edge_config
from .persisted_pool_validation import _handoff_compatible_config
from .terminal_edge_fence_validation import (
    _decision,
    _reference_summary,
    _run_terminal_fence_stage,
    _run_terminal_stage,
)


@dataclass(frozen=True)
class ContextGatedEdgeFenceValidationConfig:
    seed: int = 20260616
    foundation_seed: int = 20260612
    foundation_mate1_train_count: int = 0
    foundation_mate1_heldout_count: int = 0
    foundation_mate1_mirror_count: int = 0
    foundation_mate2_train_count: int = 0
    foundation_mate2_heldout_count: int = 0
    include_symmetries: bool = True
    foundation_train_repetitions: int = 5
    gate_min_overlap: float = 0.72
    gate_granularity: str = "position"
    foundation_eta_m3: float = 0.10
    foundation_rich_feature_credit_scale: float = 0.25
    foundation_mate1_threshold: float = 0.98
    foundation_mate2_threshold: float = 0.95
    train_pool_size: int = 32
    fence_rehearsal_pool_size: int = 16
    eval_window_size: int = 16
    train_chunk_size: int = 64
    max_chunks_per_stage: int = 2
    edge_success_threshold: float = 0.80
    fence_success_threshold: float = 0.70
    mate1_regression_threshold: float = 0.98
    mate2_regression_threshold: float = 0.95
    eta_m3: float = 0.06
    terminal_rich_feature_credit_scale: float = 0.25
    max_generation_attempts: int = 220_000
    max_samples: int = 12
    top_k_deep_score: int = 3
    strict_safety_gate: bool = True
    tg26c_main_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg26c_edge_fence_curriculum_handoff.json"
    tg26i_reference_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg26i_terminal_edge_fence_validation.json"


@dataclass(frozen=True)
class ContextGatedEdgeFenceValidationResult:
    config: ContextGatedEdgeFenceValidationConfig
    artifact_integrity: dict[str, Any]
    reference: dict[str, Any]
    foundation_payload: dict[str, Any]
    pools: dict[str, Any]
    stages: list[dict[str, Any]]
    regression: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26m_context_gated_edge_fence_validation.v0",
            "checkpoint": "TG26m_context_gated_edge_fence_validation",
            "config": asdict(self.config),
            "artifact_integrity": self.artifact_integrity,
            "tg26i_terminal_reference": self.reference,
            "training_runway": {
                "uses_tg26l_context_gated_foundation": True,
                "uses_curated_repaired_mate2_bank": True,
                "uses_terminal_native_stage_rankers": True,
                "persisted_pools": True,
                "curriculum_filter_is_schedule_only": True,
                "curriculum_labels_learner_visible": False,
                "stage_labels_learner_visible": False,
                "direct_provider_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "broad_random_krk_enabled": False,
                "ecological_spawning_enabled": False,
                "script_or_lag_expansion_enabled": False,
            },
            "local_recon_structure": {
                "foundation_mate1_node_type": "TERMINAL",
                "foundation_mate2_node_type": "context-gated local TERMINAL subgraph",
                "stage_node_type": "TERMINAL",
                "behavior_choice_mediated_by_terminal_activations": True,
                "mate2_handoff_mediated_by_context_gate_and_terminal_weights": True,
                "terminal_weights_receive_m3_credit": True,
                "remaining_scaffold": [
                    "synchronous Python legal-move enumeration as environment interface",
                    "batch evaluation loop rather than full ReCoN tick engine",
                    "pool filters are trainer-side schedule, not learner-visible causes",
                ],
            },
            "foundation": self.foundation_payload,
            "regression": self.regression,
            "pools": self.pools,
            "stages": self.stages,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_context_gated_edge_fence_validation(
    *,
    config: ContextGatedEdgeFenceValidationConfig,
) -> ContextGatedEdgeFenceValidationResult:
    artifact_integrity = _artifact_integrity(Path(config.tg26c_main_artifact_path))
    if not artifact_integrity["parseable_full_json"]:
        raise RuntimeError(f"TG26c main artifact is not parseable: {config.tg26c_main_artifact_path}")

    reference = _reference_summary(Path(config.tg26i_reference_artifact_path))
    foundation = train_context_gated_foundation_bundle(
        config=ContextGatedCurriculumConfig(
            include_symmetries=config.include_symmetries,
            train_repetitions=config.foundation_train_repetitions,
            gate_min_overlap=config.gate_min_overlap,
            gate_granularity=config.gate_granularity,
            eta_m3=config.foundation_eta_m3,
            rich_feature_credit_scale=config.foundation_rich_feature_credit_scale,
            mate1_threshold=config.foundation_mate1_threshold,
            mate2_threshold=config.foundation_mate2_threshold,
            max_samples=config.max_samples,
        )
    )
    edge_config = _edge_config(_handoff_compatible_config(config))
    edge_stage, edge_pools = _run_terminal_stage(
        label="edge_trap",
        diagnostic_name="Edge_Trap_Context_Gated_Handoff",
        generator="edge",
        ideal_white_moves=3,
        threshold=config.edge_success_threshold,
        seed=config.seed,
        config=config,
        edge_config=edge_config,
        mate_ranker=foundation.mate1_learner,
        mate2_ranker=foundation.mate2_first_learner,
    )
    fence_stage, fence_pools = _run_terminal_fence_stage(
        config=config,
        edge_config=edge_config,
        mate_ranker=foundation.mate1_learner,
        mate2_ranker=foundation.mate2_first_learner,
    )
    payload = foundation.payload
    foundation_payload = _foundation_payload(payload)
    regression = _regression(foundation_payload, config=config)
    stages = [edge_stage, fence_stage]
    decision = _decision(stages=stages, regression=regression, reference=reference)
    decision = {
        **decision,
        "status": "tg26m_context_gated_validation_complete",
        "m4_blocked_reason": (
            "edge/fence M4 remains blocked until context-gated handoff improves "
            "filtered, unfiltered, and boundary slices at larger scale"
        ),
        "next_recommended_checkpoint": (
            "Scale TG26m across another seed/window before edge/fence M4"
            if decision["foundation_regression_passed"]
            and decision["safety_passed"]
            and decision["fence_boundary_nonzero"]
            else "Audit TG26m edge/fence failures before broad KRK or SCRIPT/LAG expansion"
        ),
    }
    return ContextGatedEdgeFenceValidationResult(
        config=config,
        artifact_integrity=artifact_integrity,
        reference=reference,
        foundation_payload=foundation_payload,
        pools={**edge_pools, **fence_pools},
        stages=stages,
        regression=regression,
        decision=decision,
    )


def _foundation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    training = payload["training"]
    evaluation = payload["evaluation"]
    gate_summary = evaluation["gate_activation_summary"]
    return {
        "source_checkpoint": "TG26l_context_gated_curriculum",
        "mate1_position_count": payload["dataset"]["mate1_position_count"],
        "mate2_position_count": payload["dataset"]["mate2_position_count"],
        "mate2_gate_context_count": payload["dataset"]["mate2_gate_context_count"],
        "mate1_self_accuracy": training["mate1_self_evaluation"]["accuracy"],
        "mate2_conversion_rate": evaluation["conversion_rate"],
        "mate2_first_move_success_rate": evaluation["first_move_success_rate"],
        "mate2_no_confirmed_gate_count": gate_summary["no_confirmed_gate_count"],
        "mate1_m3_update_count": training["mate1_m3_update_count"],
        "mate1_terminal_count": training["mate1_terminal_count"],
        "mate2_first_terminal_count_by_context": training["mate2_first_terminal_count_by_bucket"],
        "mate2_first_m3_update_count_by_context": training["mate2_first_m3_update_count_by_bucket"],
        "mate2_m4_consolidation_event_count": payload["decision"]["m4_mate2_consolidation_event_count"],
        "stage_labels_learner_visible": payload["purity_boundary"]["stage_labels_learner_visible"],
        "direct_provider_override": payload["purity_boundary"]["direct_provider_override"],
        "runtime_tablebase_or_dtm_move_source": payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"],
    }


def _regression(
    foundation_payload: dict[str, Any],
    *,
    config: ContextGatedEdgeFenceValidationConfig,
) -> dict[str, Any]:
    mate1_passed = foundation_payload["mate1_self_accuracy"] >= config.mate1_regression_threshold
    mate2_passed = (
        foundation_payload["mate2_conversion_rate"] >= config.mate2_regression_threshold
        and foundation_payload["mate2_no_confirmed_gate_count"] == 0
    )
    return {
        "mate1_regression_passed": mate1_passed,
        "mate2_regression_passed": mate2_passed,
        "mate1_regression_threshold": config.mate1_regression_threshold,
        "mate2_regression_threshold": config.mate2_regression_threshold,
        "mate1_accuracy": foundation_payload["mate1_self_accuracy"],
        "mate2_conversion_rate": foundation_payload["mate2_conversion_rate"],
        "mate2_no_confirmed_gate_count": foundation_payload["mate2_no_confirmed_gate_count"],
    }

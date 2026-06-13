"""TG26i terminal-native edge/fence validation.

This checkpoint reuses the TG26h terminal foundation as the behavior-changing
path and keeps ActionRanker-family results as reference scaffolding only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
from typing import Any

from .edge_fence_curriculum import (
    EdgeFenceCurriculumConfig,
    _empty_runtime_stats,
    _evaluate_foundation_regression,
    _train_chunk,
)
from .foundation_curriculum import ActionRanker
from .handoff_filter_validation import _artifact_integrity, _edge_config, _with_cache_rates
from .persisted_pool_validation import (
    _build_pool,
    _evaluate_pool,
    _handoff_compatible_config,
)
from .terminal_substrate import (
    TerminalAffordanceLearner,
    TerminalSubstrateConfig,
    train_terminal_foundation_bundle,
)


@dataclass(frozen=True)
class TerminalEdgeFenceValidationConfig:
    seed: int = 20260615
    foundation_seed: int = 20260612
    foundation_mate1_train_count: int = 300
    foundation_mate1_heldout_count: int = 100
    foundation_mate1_mirror_count: int = 40
    foundation_mate2_train_count: int = 300
    foundation_mate2_heldout_count: int = 100
    train_pool_size: int = 32
    fence_rehearsal_pool_size: int = 16
    eval_window_size: int = 16
    train_chunk_size: int = 64
    max_chunks_per_stage: int = 2
    edge_success_threshold: float = 0.80
    fence_success_threshold: float = 0.70
    mate1_regression_threshold: float = 0.95
    mate2_regression_threshold: float = 0.80
    eta_m3: float = 0.06
    terminal_rich_feature_credit_scale: float = 0.25
    max_generation_attempts: int = 220_000
    max_samples: int = 12
    top_k_deep_score: int = 3
    strict_safety_gate: bool = True
    tg26c_main_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg26c_edge_fence_curriculum_handoff.json"
    tg26g_reference_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg26g_fence_boundary_signal.json"


@dataclass(frozen=True)
class TerminalEdgeFenceValidationResult:
    config: TerminalEdgeFenceValidationConfig
    artifact_integrity: dict[str, Any]
    reference: dict[str, Any]
    foundation_payload: dict[str, Any]
    pools: dict[str, Any]
    stages: list[dict[str, Any]]
    regression: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26i_terminal_edge_fence_validation.v0",
            "checkpoint": "TG26i_terminal_edge_fence_validation",
            "config": asdict(self.config),
            "artifact_integrity": self.artifact_integrity,
            "tg26g_action_ranker_reference": self.reference,
            "training_runway": {
                "uses_terminal_native_foundation": True,
                "uses_terminal_native_stage_rankers": True,
                "action_ranker_status": "reference_scaffolding_only",
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
                "foundation_node_type": "TERMINAL",
                "stage_node_type": "TERMINAL",
                "stage_terminal_kind": "feature_vector_pattern",
                "behavior_choice_mediated_by_terminal_activations": True,
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


def run_terminal_edge_fence_validation(
    *,
    config: TerminalEdgeFenceValidationConfig,
) -> TerminalEdgeFenceValidationResult:
    artifact_integrity = _artifact_integrity(Path(config.tg26c_main_artifact_path))
    if not artifact_integrity["parseable_full_json"]:
        raise RuntimeError(f"TG26c main artifact is not parseable: {config.tg26c_main_artifact_path}")
    reference = _reference_summary(Path(config.tg26g_reference_artifact_path))
    foundation_bundle = train_terminal_foundation_bundle(
        config=TerminalSubstrateConfig(
            seed=config.foundation_seed,
            mate1_train_count=config.foundation_mate1_train_count,
            mate1_heldout_count=config.foundation_mate1_heldout_count,
            mate1_mirror_count=config.foundation_mate1_mirror_count,
            mate2_train_count=config.foundation_mate2_train_count,
            mate2_heldout_count=config.foundation_mate2_heldout_count,
            max_generation_attempts=max(500_000, config.max_generation_attempts),
            eta_m3=0.10,
            rich_feature_credit_scale=config.terminal_rich_feature_credit_scale,
            mate1_pass_threshold=config.mate1_regression_threshold,
            mate2_pass_threshold=config.mate2_regression_threshold,
            max_samples=config.max_samples,
        )
    )
    if foundation_bundle.mate2_first_learner is None:
        raise RuntimeError("TG26i requires TG26h terminal Mate_In_2 foundation learner")
    edge_config = _edge_config(_handoff_compatible_config(config))
    edge_stage, edge_pools = _run_terminal_stage(
        label="edge_trap",
        diagnostic_name="Edge_Trap_Terminal_Substrate",
        generator="edge",
        ideal_white_moves=3,
        threshold=config.edge_success_threshold,
        seed=config.seed,
        config=config,
        edge_config=edge_config,
        mate_ranker=foundation_bundle.mate1_learner,
        mate2_ranker=foundation_bundle.mate2_first_learner,
    )
    fence_stage, fence_pools = _run_terminal_fence_stage(
        config=config,
        edge_config=edge_config,
        mate_ranker=foundation_bundle.mate1_learner,
        mate2_ranker=foundation_bundle.mate2_first_learner,
    )
    foundation_payload = _foundation_payload(foundation_bundle.payload)
    regression = _evaluate_foundation_regression({"decision": foundation_payload}, config=edge_config)
    stages = [edge_stage, fence_stage]
    decision = _decision(stages=stages, regression=regression, reference=reference)
    return TerminalEdgeFenceValidationResult(
        config=config,
        artifact_integrity=artifact_integrity,
        reference=reference,
        foundation_payload={
            "source_checkpoint": "TG26h_terminal_substrate_revival",
            **foundation_payload,
            "mate1_terminal_count": foundation_bundle.payload["terminal_substrate"]["terminal_count"],
            "mate2_first_terminal_count": foundation_bundle.payload["mate2_first_terminal_substrate"]["terminal_count"],
        },
        pools={**edge_pools, **fence_pools},
        stages=stages,
        regression=regression,
        decision=decision,
    )


def _run_terminal_stage(
    *,
    label: str,
    diagnostic_name: str,
    generator: str,
    ideal_white_moves: int,
    threshold: float,
    seed: int,
    config: TerminalEdgeFenceValidationConfig,
    edge_config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ranker = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.terminal_rich_feature_credit_scale,
    )
    score_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    runtime_stats = _empty_runtime_stats()
    prefix = "edge" if generator == "edge" else "fence"
    filtered = _build_pool(
        pool_id=f"{prefix}_filtered",
        count=config.train_pool_size + config.eval_window_size,
        seed=seed,
        generator=generator,
        slice_type="filtered_train_like",
        excluded=set(),
        config=edge_config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    excluded = {entry["fen"] for entry in filtered["entries"]}
    unfiltered = _build_pool(
        pool_id=f"{prefix}_unfiltered",
        count=config.eval_window_size,
        seed=seed + 1,
        generator=generator,
        slice_type="unfiltered_curriculum",
        excluded=excluded,
        config=edge_config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    boundary = _build_pool(
        pool_id=f"{prefix}_boundary_near_miss",
        count=config.eval_window_size,
        seed=seed + 2,
        generator=generator,
        slice_type="boundary_near_miss",
        excluded=excluded | {entry["fen"] for entry in unfiltered["entries"]},
        config=edge_config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    filtered_train = [entry["fen"] for entry in filtered["entries"][: config.train_pool_size]]
    filtered_eval = [entry["fen"] for entry in filtered["entries"][config.train_pool_size:]]
    rng = random.Random(seed + len(label))
    train_chunks: list[dict[str, Any]] = []
    m3_before = ranker.m3_update_count
    for _chunk_index in range(config.max_chunks_per_stage):
        sampled = [rng.choice(filtered_train) for _ in range(config.train_chunk_size)]
        train_chunks.append(_train_chunk(
            sampled,
            stage_ranker=ranker,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        ))
    eval_slices = {
        "filtered_train_like": _evaluate_pool(
            filtered_eval,
            ranker=ranker,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
            threshold=threshold,
        ),
        "unfiltered_curriculum": _evaluate_pool(
            [entry["fen"] for entry in unfiltered["entries"]],
            ranker=ranker,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
            threshold=threshold,
        ),
        "boundary_near_miss": _evaluate_pool(
            [entry["fen"] for entry in boundary["entries"]],
            ranker=ranker,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
            threshold=threshold,
        ),
    }
    stage = _stage_payload(
        label=label,
        diagnostic_name=diagnostic_name,
        generator=generator,
        ideal_white_moves=ideal_white_moves,
        threshold=threshold,
        train_pool_id=filtered["pool_id"],
        train_pool_position_count=len(filtered_train),
        rehearsal_pool_ids={},
        rehearsal_position_count=0,
        eval_pool_ids={
            "filtered_train_like": filtered["pool_id"],
            "unfiltered_curriculum": unfiltered["pool_id"],
            "boundary_near_miss": boundary["pool_id"],
        },
        train_chunks=train_chunks,
        eval_slices=eval_slices,
        m3_update_count=ranker.m3_update_count - m3_before,
        ranker=ranker,
        runtime_stats=runtime_stats,
        m4_reason="blocked_until_terminal_filtered_unfiltered_boundary_all_confirm_at_scale",
    )
    return stage, {pool["pool_id"]: pool for pool in (filtered, unfiltered, boundary)}


def _run_terminal_fence_stage(
    *,
    config: TerminalEdgeFenceValidationConfig,
    edge_config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ranker = TerminalAffordanceLearner.create(
        eta_m3=config.eta_m3,
        rich_feature_credit_scale=config.terminal_rich_feature_credit_scale,
    )
    score_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    runtime_stats = _empty_runtime_stats()
    ideal_white_moves = 4
    filtered = _build_pool(
        pool_id="fence_filtered",
        count=config.train_pool_size + config.eval_window_size,
        seed=config.seed + 10,
        generator="fence",
        slice_type="filtered_train_like",
        excluded=set(),
        config=edge_config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    excluded = {entry["fen"] for entry in filtered["entries"]}
    unfiltered_train = _build_pool(
        pool_id="fence_unfiltered_terminal_rehearsal",
        count=config.fence_rehearsal_pool_size,
        seed=config.seed + 11,
        generator="fence",
        slice_type="unfiltered_curriculum",
        excluded=excluded,
        config=edge_config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    boundary_train = _build_pool(
        pool_id="fence_boundary_terminal_rehearsal",
        count=config.fence_rehearsal_pool_size,
        seed=config.seed + 12,
        generator="fence",
        slice_type="boundary_near_miss",
        excluded=excluded | {entry["fen"] for entry in unfiltered_train["entries"]},
        config=edge_config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    unfiltered_eval = _build_pool(
        pool_id="fence_unfiltered",
        count=config.eval_window_size,
        seed=config.seed + 13,
        generator="fence",
        slice_type="unfiltered_curriculum",
        excluded=(
            excluded
            | {entry["fen"] for entry in unfiltered_train["entries"]}
            | {entry["fen"] for entry in boundary_train["entries"]}
        ),
        config=edge_config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    boundary_eval = _build_pool(
        pool_id="fence_boundary_near_miss",
        count=config.eval_window_size,
        seed=config.seed + 14,
        generator="fence",
        slice_type="boundary_near_miss",
        excluded=(
            excluded
            | {entry["fen"] for entry in unfiltered_train["entries"]}
            | {entry["fen"] for entry in boundary_train["entries"]}
            | {entry["fen"] for entry in unfiltered_eval["entries"]}
        ),
        config=edge_config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    filtered_train = [entry["fen"] for entry in filtered["entries"][: config.train_pool_size]]
    filtered_eval = [entry["fen"] for entry in filtered["entries"][config.train_pool_size:]]
    rehearsal = [entry["fen"] for entry in unfiltered_train["entries"]] + [entry["fen"] for entry in boundary_train["entries"]]
    weighted_train = filtered_train + rehearsal + rehearsal
    rng = random.Random(config.seed + 299)
    train_chunks: list[dict[str, Any]] = []
    m3_before = ranker.m3_update_count
    for _chunk_index in range(config.max_chunks_per_stage):
        sampled = [rng.choice(weighted_train) for _ in range(config.train_chunk_size)]
        train_chunks.append(_train_chunk(
            sampled,
            stage_ranker=ranker,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        ))
    eval_slices = {
        "filtered_train_like": _evaluate_pool(
            filtered_eval,
            ranker=ranker,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
            threshold=config.fence_success_threshold,
        ),
        "unfiltered_curriculum": _evaluate_pool(
            [entry["fen"] for entry in unfiltered_eval["entries"]],
            ranker=ranker,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
            threshold=config.fence_success_threshold,
        ),
        "boundary_near_miss": _evaluate_pool(
            [entry["fen"] for entry in boundary_eval["entries"]],
            ranker=ranker,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
            threshold=config.fence_success_threshold,
        ),
    }
    stage = _stage_payload(
        label="fence_hold",
        diagnostic_name="Fence_Hold_Terminal_Substrate",
        generator="fence",
        ideal_white_moves=ideal_white_moves,
        threshold=config.fence_success_threshold,
        train_pool_id=filtered["pool_id"],
        train_pool_position_count=len(filtered_train),
        rehearsal_pool_ids={
            "unfiltered_curriculum": unfiltered_train["pool_id"],
            "boundary_near_miss": boundary_train["pool_id"],
        },
        rehearsal_position_count=len(rehearsal),
        eval_pool_ids={
            "filtered_train_like": filtered["pool_id"],
            "unfiltered_curriculum": unfiltered_eval["pool_id"],
            "boundary_near_miss": boundary_eval["pool_id"],
        },
        train_chunks=train_chunks,
        eval_slices=eval_slices,
        m3_update_count=ranker.m3_update_count - m3_before,
        ranker=ranker,
        runtime_stats=runtime_stats,
        m4_reason="blocked_until_terminal_fence_unfiltered_and_boundary_confirm_at_scale",
    )
    pools = {
        pool["pool_id"]: pool
        for pool in (filtered, unfiltered_train, boundary_train, unfiltered_eval, boundary_eval)
    }
    return stage, pools


def _stage_payload(
    *,
    label: str,
    diagnostic_name: str,
    generator: str,
    ideal_white_moves: int,
    threshold: float,
    train_pool_id: str,
    train_pool_position_count: int,
    rehearsal_pool_ids: dict[str, str],
    rehearsal_position_count: int,
    eval_pool_ids: dict[str, str],
    train_chunks: list[dict[str, Any]],
    eval_slices: dict[str, dict[str, Any]],
    m3_update_count: int,
    ranker: TerminalAffordanceLearner,
    runtime_stats: dict[str, int],
    m4_reason: str,
) -> dict[str, Any]:
    return {
        "label": label,
        "diagnostic_name": diagnostic_name,
        "generator": generator,
        "ideal_white_moves": ideal_white_moves,
        "threshold": threshold,
        "curriculum_labels_learner_visible": False,
        "stage_labels_learner_visible": False,
        "train_pool_id": train_pool_id,
        "train_pool_position_count": train_pool_position_count,
        "rehearsal_pool_ids": rehearsal_pool_ids,
        "rehearsal_position_count": rehearsal_position_count,
        "eval_pool_ids": eval_pool_ids,
        "train_chunks": train_chunks,
        "eval_slices": eval_slices,
        "m3_update_count": m3_update_count,
        "m4_consolidation_event_count": 0,
        "m4_reason": m4_reason,
        "stage_terminal_substrate": ranker.to_dict(max_terminals=24),
        "scoring_cost": _with_cache_rates(runtime_stats),
    }


def _foundation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    mate2 = payload["mate2"]
    return {
        "mate1_heldout_accuracy": payload["mate1"]["heldout"]["accuracy"],
        "mate1_mirror_accuracy": payload["mate1"]["mirror_generalization"]["accuracy"],
        "mate2_conversion_rate": None if not mate2.get("enabled") else mate2["heldout"]["conversion_rate"],
        "mate1_m3_update_count": payload["mate1"]["m3_update_count"],
        "mate1_m4_consolidation_event_count": payload["mate1"]["m4_consolidation_event_count"],
        "mate2_m4_consolidation_event_count": int(mate2.get("m4_consolidation_event_count", 0)),
    }


def _reference_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "path": str(path), "reason": "missing"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary: dict[str, Any] = {
        "available": True,
        "path": str(path),
        "schema_version": payload.get("schema_version"),
        "stage_metrics": {},
    }
    for stage in payload.get("stages", []):
        summary["stage_metrics"][stage["label"]] = {
            name: {
                "conversion_count": metrics["conversion_count"],
                "position_count": metrics["position_count"],
                "rook_loss_count": metrics["rook_loss_count"],
                "confinement_regression_count": metrics["confinement_regression_count"],
            }
            for name, metrics in stage.get("eval_slices", {}).items()
        }
    return summary


def _decision(
    *,
    stages: list[dict[str, Any]],
    regression: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, Any]:
    foundation_ok = regression["mate1_regression_passed"] and regression["mate2_regression_passed"]
    safety_ok = True
    stage_signals: dict[str, dict[str, bool]] = {}
    for stage in stages:
        slices = stage["eval_slices"]
        for metrics in slices.values():
            safety_ok = safety_ok and metrics["rook_loss_count"] == 0
            safety_ok = safety_ok and metrics["stalemate_count"] == 0
            safety_ok = safety_ok and metrics["illegal_or_no_move_count"] == 0
            safety_ok = safety_ok and metrics["confinement_regression_count"] == 0
        stage_signals[stage["label"]] = {
            "filtered_runway_signal": slices["filtered_train_like"]["conversion_count"] > 0,
            "unfiltered_generalization_signal": slices["unfiltered_curriculum"]["conversion_count"] > 0,
            "boundary_bridge_signal": slices["boundary_near_miss"]["conversion_count"] > 0,
        }
    edge = next(stage for stage in stages if stage["label"] == "edge_trap")
    fence = next(stage for stage in stages if stage["label"] == "fence_hold")
    fence_unfiltered = fence["eval_slices"]["unfiltered_curriculum"]["conversion_count"]
    fence_boundary = fence["eval_slices"]["boundary_near_miss"]["conversion_count"]
    edge_unfiltered = edge["eval_slices"]["unfiltered_curriculum"]["conversion_count"]
    edge_boundary = edge["eval_slices"]["boundary_near_miss"]["conversion_count"]
    previous_fence = reference.get("stage_metrics", {}).get("fence_hold", {}) if reference.get("available") else {}
    previous_edge = reference.get("stage_metrics", {}).get("edge_trap", {}) if reference.get("available") else {}
    previous_fence_boundary = previous_fence.get("boundary_near_miss", {}).get("conversion_count")
    previous_fence_unfiltered = previous_fence.get("unfiltered_curriculum", {}).get("conversion_count")
    previous_edge_boundary = previous_edge.get("boundary_near_miss", {}).get("conversion_count")
    previous_edge_unfiltered = previous_edge.get("unfiltered_curriculum", {}).get("conversion_count")
    fence_boundary_nonzero = fence_boundary > 0
    return {
        "status": "tg26i_validation_complete",
        "foundation_regression_passed": foundation_ok,
        "safety_passed": safety_ok,
        "stage_signals": stage_signals,
        "edge_stability_preserved": edge_unfiltered > 0 and edge_boundary > 0,
        "fence_unfiltered_nonzero": fence_unfiltered > 0,
        "fence_boundary_nonzero": fence_boundary_nonzero,
        "edge_unfiltered_delta_vs_tg26g": None if previous_edge_unfiltered is None else edge_unfiltered - int(previous_edge_unfiltered),
        "edge_boundary_delta_vs_tg26g": None if previous_edge_boundary is None else edge_boundary - int(previous_edge_boundary),
        "fence_unfiltered_delta_vs_tg26g": None if previous_fence_unfiltered is None else fence_unfiltered - int(previous_fence_unfiltered),
        "fence_boundary_delta_vs_tg26g": None if previous_fence_boundary is None else fence_boundary - int(previous_fence_boundary),
        "m4_consolidation_event_count": 0,
        "m4_blocked_reason": "edge/fence requires repeated larger confirmation; this checkpoint validates terminal substrate transfer",
        "stage_competence_claim": False,
        "broad_random_krk_enabled": False,
        "ecological_spawning_enabled": False,
        "script_or_lag_expansion_enabled": False,
        "next_recommended_checkpoint": (
            "Repeat terminal-native edge/fence validation across another seed/window before external audit or M4"
            if foundation_ok and safety_ok and fence_boundary_nonzero
            else "Audit terminal-native edge/fence failure before adding SCRIPT/LAG or broad KRK"
        ),
    }

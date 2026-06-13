"""TG26g fence boundary local signal probe."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
from typing import Any

import chess

from recon_lite_chess.training.krk_curriculum import box_min_side, did_box_grow

from .edge_fence_curriculum import (
    _empty_runtime_stats,
    _evaluate_foundation_regression,
    _train_chunk,
)
from .features import extract_learner_features, validate_learner_record
from .foundation_curriculum import (
    ActionRanker,
    FoundationCurriculumConfig,
    _action_feature_keys,
    run_foundation_curriculum,
)
from .handoff_filter_validation import _artifact_integrity, _edge_config, _with_cache_rates
from .persisted_pool_validation import (
    _build_pool,
    _evaluate_pool,
    _handoff_compatible_config,
    _run_stage,
)


@dataclass(frozen=True)
class FenceBoundarySignalConfig:
    seed: int = 20260615
    foundation_seed: int = 20260612
    foundation_mate1_train_count: int = 300
    foundation_mate1_heldout_count: int = 100
    foundation_mate1_mirror_count: int = 40
    foundation_mate2_train_count: int = 100
    foundation_mate2_heldout_count: int = 32
    train_pool_size: int = 64
    fence_rehearsal_pool_size: int = 32
    eval_window_size: int = 32
    train_chunk_size: int = 128
    max_chunks_per_stage: int = 2
    edge_success_threshold: float = 0.80
    fence_success_threshold: float = 0.70
    mate1_regression_threshold: float = 0.95
    mate2_regression_threshold: float = 0.75
    eta_m3: float = 0.06
    max_generation_attempts: int = 300_000
    max_samples: int = 12
    top_k_deep_score: int = 6
    strict_safety_gate: bool = True
    tg26c_main_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg26c_edge_fence_curriculum_handoff.json"
    tg26f_reference_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg26f_fence_boundary_rehearsal.json"


class DeltaActionRanker(ActionRanker):
    """Action ranker with local generic post-move delta terminals."""

    def train_position_rewards(self, board: chess.Board, *, move_rewards: dict[str, float]) -> dict[str, int]:
        updates = {"positive": 0, "negative": 0, "neutral": 0}
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            reward = move_rewards.get(move.uci(), 0.0)
            for key in _delta_action_feature_keys(board, move):
                node = self.get_node(key)
                node.update(reward, self.eta_m3)
                self.m3_update_count += 1
            if reward > 0:
                updates["positive"] += 1
            elif reward < 0:
                updates["negative"] += 1
            else:
                updates["neutral"] += 1
        return updates

    def weight_for_move(self, board: chess.Board, move: chess.Move) -> float:
        return sum(
            0.0 if self.nodes.get(key) is None else self.nodes[key].local_weight
            for key in _delta_action_feature_keys(board, move)
        )


@dataclass(frozen=True)
class FenceBoundarySignalResult:
    config: FenceBoundarySignalConfig
    artifact_integrity: dict[str, Any]
    reference: dict[str, Any]
    foundation_payload: dict[str, Any]
    pools: dict[str, Any]
    stages: list[dict[str, Any]]
    regression: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26g_fence_boundary_signal.v0",
            "checkpoint": "TG26g_fence_boundary_signal",
            "config": asdict(self.config),
            "artifact_integrity": self.artifact_integrity,
            "tg26f_reference": self.reference,
            "training_runway": {
                "persisted_pools": True,
                "fence_delta_action_signal": True,
                "curriculum_filter_is_schedule_only": True,
                "curriculum_labels_learner_visible": False,
                "stage_labels_learner_visible": False,
                "direct_provider_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "broad_random_krk_enabled": False,
                "ecological_spawning_enabled": False,
            },
            "local_signal": {
                "node_type": "ACTION",
                "scope": "fence ranker only",
                "feature_terms": [
                    "post_move_confinement_delta_sign",
                    "post_move_black_edge_distance_delta_sign",
                    "post_move_black_mobility_delta_sign",
                    "post_move_white_king_distance_delta_sign",
                    "post_move_rook_safe",
                ],
                "uses_stage_labels": False,
                "chooses_moves_directly": False,
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


def run_fence_boundary_signal(*, config: FenceBoundarySignalConfig) -> FenceBoundarySignalResult:
    artifact_integrity = _artifact_integrity(Path(config.tg26c_main_artifact_path))
    if not artifact_integrity["parseable_full_json"]:
        raise RuntimeError(f"TG26c main artifact is not parseable: {config.tg26c_main_artifact_path}")
    reference = _reference_summary(Path(config.tg26f_reference_artifact_path))
    foundation = run_foundation_curriculum(
        config=FoundationCurriculumConfig(
            seed=config.foundation_seed,
            mate1_train_count=config.foundation_mate1_train_count,
            mate1_heldout_count=config.foundation_mate1_heldout_count,
            mate1_mirror_count=config.foundation_mate1_mirror_count,
            mate2_train_count=config.foundation_mate2_train_count,
            mate2_heldout_count=config.foundation_mate2_heldout_count,
            max_generation_attempts=max(500_000, config.max_generation_attempts),
            eta_m3=0.10,
            max_samples=config.max_samples,
        )
    )
    foundation_payload = foundation.to_dict()
    mate2_ranker = foundation.mate2_first_ranker
    if mate2_ranker is None:
        raise RuntimeError("TG26g requires TG25 Mate_In_2 foundation ranker")
    edge_config = _edge_config(_handoff_compatible_config(config))
    edge_stage, edge_pools = _run_stage(
        label="edge_trap",
        diagnostic_name="Edge_Trap_Close",
        generator="edge",
        ideal_white_moves=3,
        threshold=config.edge_success_threshold,
        seed=config.seed,
        config=config,
        edge_config=edge_config,
        mate_ranker=foundation.mate1_ranker,
        mate2_ranker=mate2_ranker,
    )
    fence_stage, fence_pools = _run_fence_stage(
        config=config,
        edge_config=edge_config,
        mate_ranker=foundation.mate1_ranker,
        mate2_ranker=mate2_ranker,
    )
    stages = [edge_stage, fence_stage]
    regression = _evaluate_foundation_regression(foundation_payload, config=edge_config)
    decision = _decision(stages=stages, regression=regression, reference=reference)
    return FenceBoundarySignalResult(
        config=config,
        artifact_integrity=artifact_integrity,
        reference=reference,
        foundation_payload={
            "source_checkpoint": "TG25_foundation_curriculum",
            "mate1_heldout_accuracy": foundation_payload["decision"]["mate1_heldout_accuracy"],
            "mate1_mirror_accuracy": foundation_payload["decision"]["mate1_mirror_accuracy"],
            "mate2_conversion_rate": foundation_payload["decision"]["mate2_conversion_rate"],
            "mate1_m3_update_count": foundation_payload["decision"]["mate1_m3_update_count"],
            "mate1_m4_consolidation_event_count": foundation_payload["decision"]["mate1_m4_consolidation_event_count"],
            "mate2_m4_consolidation_event_count": foundation_payload["decision"]["mate2_m4_consolidation_event_count"],
        },
        pools={**edge_pools, **fence_pools},
        stages=stages,
        regression=regression,
        decision=decision,
    )


def _run_fence_stage(
    *,
    config: FenceBoundarySignalConfig,
    edge_config: Any,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ranker = DeltaActionRanker.create(eta_m3=config.eta_m3)
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
        pool_id="fence_unfiltered_signal_rehearsal",
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
        pool_id="fence_boundary_signal_rehearsal",
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
        excluded=excluded | {entry["fen"] for entry in unfiltered_train["entries"]} | {entry["fen"] for entry in boundary_train["entries"]},
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
    rng = random.Random(config.seed + 199)
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
    stage = {
        "label": "fence_hold",
        "diagnostic_name": "Fence_Hold_Boundary_Delta_Signal",
        "generator": "fence",
        "ideal_white_moves": ideal_white_moves,
        "threshold": config.fence_success_threshold,
        "curriculum_labels_learner_visible": False,
        "train_pool_id": filtered["pool_id"],
        "train_pool_position_count": len(filtered_train),
        "rehearsal_pool_ids": {
            "unfiltered_curriculum": unfiltered_train["pool_id"],
            "boundary_near_miss": boundary_train["pool_id"],
        },
        "rehearsal_position_count": len(rehearsal),
        "eval_pool_ids": {
            "filtered_train_like": filtered["pool_id"],
            "unfiltered_curriculum": unfiltered_eval["pool_id"],
            "boundary_near_miss": boundary_eval["pool_id"],
        },
        "train_chunks": train_chunks,
        "eval_slices": eval_slices,
        "m3_update_count": ranker.m3_update_count - m3_before,
        "m4_consolidation_event_count": 0,
        "m4_reason": "blocked_until_fence_unfiltered_and_boundary_confirm_at_scale",
        "stage_ranker": ranker.to_dict(),
        "scoring_cost": _with_cache_rates(runtime_stats),
    }
    pools = {
        pool["pool_id"]: pool
        for pool in (filtered, unfiltered_train, boundary_train, unfiltered_eval, boundary_eval)
    }
    return stage, pools


def _delta_action_feature_keys(board: chess.Board, move: chess.Move) -> tuple[str, ...]:
    keys = list(_action_feature_keys(board, move))
    if move not in board.legal_moves:
        validate_learner_record(keys)
        return tuple(keys)
    before = extract_learner_features(board)
    before_confinement = box_min_side(board)
    after = board.copy(stack=False)
    after.push(move)
    after_features = extract_learner_features(after)
    confinement_delta = _sign(box_min_side(after) - before_confinement)
    edge_delta = _sign(
        after_features["black_king_nearest_edge_distance"]
        - before["black_king_nearest_edge_distance"]
    )
    mobility_delta = _sign(after_features["black_reply_mobility"] - before["black_reply_mobility"])
    king_distance_delta = _sign(
        after_features["white_king_to_black_king_distance"]
        - before["white_king_to_black_king_distance"]
    )
    extras = [
        f"post_move_confinement_delta_sign={confinement_delta}",
        f"post_move_black_edge_distance_delta_sign={edge_delta}",
        f"post_move_black_mobility_delta_sign={mobility_delta}",
        f"post_move_white_king_distance_delta_sign={king_distance_delta}",
        f"post_move_rook_safe={int(after_features['rook_present'] > 0.0 and after_features['rook_attacked_by_black'] <= 0.0)}",
        f"post_move_stalemate={int(after.is_stalemate())}",
        f"post_move_confinement_regressed={int(did_box_grow(board, after))}",
    ]
    keys.extend(extras)
    validate_learner_record(keys)
    return tuple(keys)


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


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


def _decision(*, stages: list[dict[str, Any]], regression: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
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
    fence = next(stage for stage in stages if stage["label"] == "fence_hold")
    edge = next(stage for stage in stages if stage["label"] == "edge_trap")
    fence_boundary = fence["eval_slices"]["boundary_near_miss"]["conversion_count"]
    fence_unfiltered = fence["eval_slices"]["unfiltered_curriculum"]["conversion_count"]
    edge_boundary = edge["eval_slices"]["boundary_near_miss"]["conversion_count"]
    previous_fence = reference.get("stage_metrics", {}).get("fence_hold", {}) if reference.get("available") else {}
    previous_boundary = previous_fence.get("boundary_near_miss", {}).get("conversion_count")
    previous_unfiltered = previous_fence.get("unfiltered_curriculum", {}).get("conversion_count")
    return {
        "status": "tg26g_validation_complete",
        "foundation_regression_passed": foundation_ok,
        "safety_passed": safety_ok,
        "stage_signals": stage_signals,
        "edge_stability_preserved": edge["eval_slices"]["unfiltered_curriculum"]["conversion_count"] > 0 and edge_boundary > 0,
        "fence_unfiltered_nonzero": fence_unfiltered > 0,
        "fence_boundary_nonzero": fence_boundary > 0,
        "fence_boundary_delta_vs_tg26f": None if previous_boundary is None else fence_boundary - int(previous_boundary),
        "fence_unfiltered_delta_vs_tg26f": None if previous_unfiltered is None else fence_unfiltered - int(previous_unfiltered),
        "m4_consolidation_event_count": 0,
        "m4_blocked_reason": "requires repeated larger confirmation; this checkpoint only tests one local delta signal",
        "stage_competence_claim": False,
        "broad_random_krk_enabled": False,
        "next_recommended_checkpoint": (
            "Repeat fence boundary delta signal across another seed/window before M4 or broad KRK"
            if fence_boundary > 0
            else "External audit: fence boundary transfer still lacks a useful local signal"
        ),
    }

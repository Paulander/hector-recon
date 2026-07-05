"""TG26e persisted pool validation for edge/fence handoff curriculum."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
from typing import Any

import chess

from .edge_fence_curriculum import (
    EdgeFenceCurriculumConfig,
    _cached_cheap_action_assessment,
    _cached_score_first_move,
    _empty_runtime_stats,
    _evaluate_foundation_regression,
    _evaluate_stage,
    _has_promising_candidate,
    _random_stage_board,
    _safe_action_feature_keys,
    _top_k_deep_candidates,
    _train_chunk,
    _valid_stage_board,
)
from .foundation_curriculum import ActionRanker, FoundationCurriculumConfig, run_foundation_curriculum
from .features import extract_learner_features
from .handoff_filter_validation import _artifact_integrity, _edge_config, _stats_delta, _with_cache_rates


@dataclass(frozen=True)
class PersistedPoolValidationConfig:
    seed: int = 20260615
    foundation_seed: int = 20260612
    foundation_mate1_train_count: int = 300
    foundation_mate1_heldout_count: int = 100
    foundation_mate1_mirror_count: int = 40
    foundation_mate2_train_count: int = 100
    foundation_mate2_heldout_count: int = 32
    train_pool_size: int = 64
    eval_window_size: int = 32
    train_chunk_size: int = 96
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


@dataclass(frozen=True)
class PersistedPoolValidationResult:
    config: PersistedPoolValidationConfig
    artifact_integrity: dict[str, Any]
    foundation_payload: dict[str, Any]
    pools: dict[str, Any]
    stages: list[dict[str, Any]]
    regression: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26e_persisted_pool_validation.v0",
            "checkpoint": "TG26e_persisted_pool_validation",
            "config": asdict(self.config),
            "artifact_integrity": self.artifact_integrity,
            "training_runway": {
                "persisted_pools": True,
                "curriculum_filter_is_schedule_only": True,
                "curriculum_labels_learner_visible": False,
                "stage_labels_learner_visible": False,
                "direct_provider_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "broad_random_krk_enabled": False,
                "ecological_spawning_enabled": False,
            },
            "interpretation_rules": {
                "keep_edge_and_fence_separate": True,
                "keep_slices_separate": True,
                "filtered_train_like": "curriculum_runway_signal_not_stage_competence",
                "unfiltered_curriculum": "stage_generalization_signal",
                "boundary_near_miss": "bridge_beyond_obvious_handoff_signal",
                "m4_policy": "blocked_unless_filtered_unfiltered_boundary_all_support_advancement",
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


def run_persisted_pool_validation(*, config: PersistedPoolValidationConfig) -> PersistedPoolValidationResult:
    artifact_integrity = _artifact_integrity(Path(config.tg26c_main_artifact_path))
    if not artifact_integrity["parseable_full_json"]:
        raise RuntimeError(f"TG26c main artifact is not parseable: {config.tg26c_main_artifact_path}")

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
            mate1_pass_threshold=config.mate1_regression_threshold,
            mate2_pass_threshold=config.mate2_regression_threshold,
            max_samples=config.max_samples,
        )
    )
    foundation_payload = foundation.to_dict()
    mate2_ranker = foundation.mate2_first_ranker
    if mate2_ranker is None:
        raise RuntimeError("TG26e requires TG25 Mate_In_2 foundation ranker")
    edge_config = _edge_config(_handoff_compatible_config(config))
    pools: dict[str, Any] = {}
    stages: list[dict[str, Any]] = []
    for label, diagnostic_name, generator, ideal_white_moves, threshold, seed in (
        ("edge_trap", "Edge_Trap_Close", "edge", 3, config.edge_success_threshold, config.seed),
        ("fence_hold", "Fence_Hold_Approach", "fence", 4, config.fence_success_threshold, config.seed + 10),
    ):
        stage, stage_pools = _run_stage(
            label=label,
            diagnostic_name=diagnostic_name,
            generator=generator,
            ideal_white_moves=ideal_white_moves,
            threshold=threshold,
            seed=seed,
            config=config,
            edge_config=edge_config,
            mate_ranker=foundation.mate1_ranker,
            mate2_ranker=mate2_ranker,
        )
        stages.append(stage)
        pools.update(stage_pools)
    regression = _evaluate_foundation_regression(foundation_payload, config=edge_config)
    decision = _decision(stages=stages, regression=regression)
    return PersistedPoolValidationResult(
        config=config,
        artifact_integrity=artifact_integrity,
        foundation_payload={
            "source_checkpoint": "TG25_foundation_curriculum",
            "mate1_heldout_accuracy": foundation_payload["decision"]["mate1_heldout_accuracy"],
            "mate1_mirror_accuracy": foundation_payload["decision"]["mate1_mirror_accuracy"],
            "mate2_conversion_rate": foundation_payload["decision"]["mate2_conversion_rate"],
            "mate1_m3_update_count": foundation_payload["decision"]["mate1_m3_update_count"],
            "mate1_m4_consolidation_event_count": foundation_payload["decision"]["mate1_m4_consolidation_event_count"],
            "mate2_m4_consolidation_event_count": foundation_payload["decision"]["mate2_m4_consolidation_event_count"],
        },
        pools=pools,
        stages=stages,
        regression=regression,
        decision=decision,
    )


def _handoff_compatible_config(config: PersistedPoolValidationConfig) -> Any:
    class Compatible:
        pass

    compatible = Compatible()
    for key, value in asdict(config).items():
        setattr(compatible, key, value)
    return compatible


def _run_stage(
    *,
    label: str,
    diagnostic_name: str,
    generator: str,
    ideal_white_moves: int,
    threshold: float,
    seed: int,
    config: PersistedPoolValidationConfig,
    edge_config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ranker = ActionRanker.create(eta_m3=config.eta_m3)
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
    train_fens = [entry["fen"] for entry in filtered["entries"][: config.train_pool_size]]
    filtered_eval_fens = [entry["fen"] for entry in filtered["entries"][config.train_pool_size:]]
    rng = random.Random(seed + len(label))
    train_chunks: list[dict[str, Any]] = []
    m3_before = ranker.m3_update_count
    for _chunk_index in range(config.max_chunks_per_stage):
        sampled = [rng.choice(train_fens) for _ in range(config.train_chunk_size)]
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
            filtered_eval_fens,
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
    stage = {
        "label": label,
        "diagnostic_name": diagnostic_name,
        "generator": generator,
        "ideal_white_moves": ideal_white_moves,
        "threshold": threshold,
        "curriculum_labels_learner_visible": False,
        "train_pool_id": filtered["pool_id"],
        "train_pool_position_count": len(train_fens),
        "eval_pool_ids": {
            "filtered_train_like": filtered["pool_id"],
            "unfiltered_curriculum": unfiltered["pool_id"],
            "boundary_near_miss": boundary["pool_id"],
        },
        "train_chunks": train_chunks,
        "eval_slices": eval_slices,
        "m3_update_count": ranker.m3_update_count - m3_before,
        "m4_consolidation_event_count": 0,
        "m4_reason": "blocked_until_filtered_unfiltered_boundary_all_confirm_at_scale",
        "stage_ranker": ranker.to_dict(),
        "scoring_cost": _with_cache_rates(runtime_stats),
    }
    return stage, {pool["pool_id"]: pool for pool in (filtered, unfiltered, boundary)}


def _evaluate_pool(
    fens: list[str],
    *,
    ranker: ActionRanker,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    score_cache: dict[tuple[str, str, int], dict[str, Any]],
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int],
    threshold: float,
) -> dict[str, Any]:
    metrics = _evaluate_stage(
        fens,
        stage_ranker=ranker,
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    metrics["threshold"] = threshold
    return metrics


def _build_pool(
    *,
    pool_id: str,
    count: int,
    seed: int,
    generator: str,
    slice_type: str,
    excluded: set[str],
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    score_cache: dict[tuple[str, str, int], dict[str, Any]],
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int],
) -> dict[str, Any]:
    rng = random.Random(seed)
    used = set(excluded)
    entries: list[dict[str, Any]] = []
    rejections = {
        "illegal_or_generated_invalid": 0,
        "no_promising_candidate": 0,
        "no_handoff_candidate": 0,
        "safety_rejected": 0,
        "duplicate": 0,
        "has_handoff_candidate": 0,
    }
    before_stats = dict(runtime_stats)
    attempts = 0
    for _ in range(config.max_generation_attempts):
        if len(entries) >= count:
            break
        attempts += 1
        board = _random_stage_board(rng, generator=generator)
        if not _valid_stage_board(board, generator=generator):
            rejections["illegal_or_generated_invalid"] += 1
            continue
        if not _has_promising_candidate(board):
            rejections["no_promising_candidate"] += 1
            continue
        fen = board.fen()
        if fen in used:
            rejections["duplicate"] += 1
            continue
        entry = _pool_entry(
            board,
            generator=generator,
            slice_type=slice_type,
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
        if slice_type == "unfiltered_curriculum":
            pass
        elif not entry["safety_flags"]["has_viable_cheap_candidate"]:
            rejections["safety_rejected"] += 1
            continue
        elif slice_type == "filtered_train_like":
            if entry["handoff_type"] == "none":
                rejections["no_handoff_candidate"] += 1
                continue
        elif slice_type == "boundary_near_miss":
            if entry["handoff_type"] != "none":
                rejections["has_handoff_candidate"] += 1
                continue
        else:
            raise ValueError(f"unknown slice type: {slice_type}")
        entry["acceptance_reason"] = f"accepted_{slice_type}"
        used.add(fen)
        entries.append(entry)
    if len(entries) < count:
        raise RuntimeError(f"generated {len(entries)} {pool_id} positions, needed {count}")
    stats = {
        "generation_attempts": attempts,
        "accepted_count": len(entries),
        "acceptance_rate": 0.0 if attempts == 0 else len(entries) / attempts,
        "rejection_counts": rejections,
        "duplicate_count": rejections["duplicate"],
        "safety_rejected_count": rejections["safety_rejected"],
        "no_handoff_rejected_count": rejections["no_handoff_candidate"],
        "scoring_cost": _with_cache_rates(_stats_delta(before_stats, runtime_stats)),
        "top_k_deep_score": config.top_k_deep_score,
    }
    return {
        "pool_id": pool_id,
        "generator": generator,
        "slice_type": slice_type,
        "seed": seed,
        "position_count": len(entries),
        "stats": stats,
        "entries": entries,
    }


def _pool_entry(
    board: chess.Board,
    *,
    generator: str,
    slice_type: str,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    score_cache: dict[tuple[str, str, int], dict[str, Any]],
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int],
) -> dict[str, Any]:
    cheap_scores = {
        move.uci(): _cached_cheap_action_assessment(
            board,
            move,
            config=config,
            ideal_white_moves=ideal_white_moves,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
        for move in board.legal_moves
    }
    top = _top_k_deep_candidates(cheap_scores, config=config)
    runtime_stats["cheap_pruned_action_count"] += max(0, len(cheap_scores) - len(top))
    deep_scores = {}
    for uci in top:
        deep_scores[uci] = _cached_score_first_move(
            board,
            chess.Move.from_uci(uci),
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            runtime_stats=runtime_stats,
        )
    best_action = _best_action(cheap_scores=cheap_scores, deep_scores=deep_scores)
    best_deep = deep_scores.get(best_action, {})
    handoff_type = str(best_deep.get("handoff", "none")) if best_deep.get("conversion") else "none"
    return {
        "fen": board.fen(),
        "generator_type": generator,
        "slice_type": slice_type,
        "acceptance_reason": "pending",
        "best_candidate_action": best_action,
        "handoff_type": _pretty_handoff(handoff_type),
        "safety_flags": {
            "has_viable_cheap_candidate": any(
                not score.get("safety_filter_rejected", False) and float(score.get("reward", 0.0)) > 0.0
                for score in cheap_scores.values()
            ),
            "any_safety_rejected": any(score.get("safety_filter_rejected", False) for score in cheap_scores.values()),
            "best_safety_rejected": bool(cheap_scores.get(best_action, {}).get("safety_filter_rejected", False)),
        },
        "foundation_ranker_confidence": {
            "available": False,
            "reason": "foundation confidence is represented by deep handoff conversion labels, not a calibrated probability",
        },
        "black_reply_that_breaks_candidate": best_deep.get("black_reply"),
        "cached_feature_keys": sorted(extract_learner_features(board).keys())[:12],
        "cached_action_keys": [] if best_action is None else _safe_action_feature_keys(board, chess.Move.from_uci(best_action))[:12],
        "cheap_candidate_scores": _compact_scores(cheap_scores),
        "deep_candidate_scores": _compact_scores(deep_scores),
    }


def _best_action(*, cheap_scores: dict[str, dict[str, Any]], deep_scores: dict[str, dict[str, Any]]) -> str | None:
    if deep_scores:
        return max(
            deep_scores,
            key=lambda uci: (
                int(bool(deep_scores[uci].get("conversion"))),
                float(deep_scores[uci].get("reward", -1.0)),
                uci,
            ),
        )
    if not cheap_scores:
        return None
    return max(cheap_scores, key=lambda uci: (float(cheap_scores[uci].get("reward", -1.0)), uci))


def _pretty_handoff(handoff: str) -> str:
    if handoff == "mate_in_one":
        return "Mate_In_1"
    if handoff == "mate_in_two":
        return "Mate_In_2"
    return "none"


def _compact_scores(scores: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    compact: dict[str, dict[str, Any]] = {}
    for uci, score in sorted(scores.items()):
        compact[uci] = {
            "reward": round(float(score.get("reward", 0.0)), 6),
            "conversion": bool(score.get("conversion", False)),
            "handoff": _pretty_handoff(str(score.get("handoff", "none"))),
            "reason": score.get("reason"),
            "safety_filter_rejected": bool(score.get("safety_filter_rejected", False)),
            "confinement_regressed": bool(score.get("confinement_regressed", False)),
            "black_reply": score.get("black_reply"),
        }
    return compact


def _decision(*, stages: list[dict[str, Any]], regression: dict[str, Any]) -> dict[str, Any]:
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
        filtered = slices["filtered_train_like"]["conversion_count"] > 0
        unfiltered = slices["unfiltered_curriculum"]["conversion_count"] > 0
        boundary = slices["boundary_near_miss"]["conversion_count"] > 0
        stage_signals[stage["label"]] = {
            "filtered_runway_signal": filtered,
            "unfiltered_generalization_signal": unfiltered,
            "boundary_bridge_signal": boundary,
            "advancement_supported": bool(filtered and unfiltered and boundary),
        }
    edge = stage_signals.get("edge_trap", {})
    fence = stage_signals.get("fence_hold", {})
    fence_boundary = bool(fence.get("boundary_bridge_signal"))
    return {
        "status": "tg26e_validation_complete",
        "foundation_regression_passed": foundation_ok,
        "safety_passed": safety_ok,
        "stage_signals": stage_signals,
        "edge_generalization_survived": bool(edge.get("filtered_runway_signal") and edge.get("unfiltered_generalization_signal")),
        "fence_transferred_beyond_filtered": bool(
            fence.get("unfiltered_generalization_signal") or fence.get("boundary_bridge_signal")
        ),
        "fence_boundary_transfer": fence_boundary,
        "m4_consolidation_event_count": 0,
        "m4_blocked_reason": "requires filtered, unfiltered, and boundary support at scale for each stage",
        "stage_competence_claim": False,
        "broad_random_krk_enabled": False,
        "next_recommended_checkpoint": (
            "Continue fence boundary/near-miss transfer work before broad KRK"
            if not fence_boundary
            else "Repeat larger validation before any M4 consolidation or broad KRK"
        ),
    }

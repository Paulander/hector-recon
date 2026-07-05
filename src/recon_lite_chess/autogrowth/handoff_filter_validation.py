"""TG26d validation for handoff-filtered edge/fence curriculum."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
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
    _top_k_deep_candidates,
    _train_chunk,
    _valid_stage_board,
)
from .foundation_curriculum import ActionRanker, FoundationCurriculumConfig, run_foundation_curriculum


@dataclass(frozen=True)
class HandoffFilterValidationConfig:
    seed: int = 20260614
    foundation_seed: int = 20260612
    foundation_mate1_train_count: int = 300
    foundation_mate1_heldout_count: int = 100
    foundation_mate1_mirror_count: int = 40
    foundation_mate2_train_count: int = 100
    foundation_mate2_heldout_count: int = 32
    train_pool_size: int = 160
    train_chunk_size: int = 160
    eval_window_size: int = 48
    max_chunks_per_stage: int = 2
    edge_success_threshold: float = 0.80
    fence_success_threshold: float = 0.70
    mate1_regression_threshold: float = 0.95
    mate2_regression_threshold: float = 0.75
    eta_m3: float = 0.06
    max_generation_attempts: int = 250_000
    max_samples: int = 12
    top_k_deep_score: int = 6
    strict_safety_gate: bool = True
    tg26c_main_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg26c_edge_fence_curriculum_handoff.json"


@dataclass(frozen=True)
class HandoffFilterValidationResult:
    config: HandoffFilterValidationConfig
    artifact_integrity: dict[str, Any]
    foundation_payload: dict[str, Any]
    stages: list[dict[str, Any]]
    regression: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26d_handoff_filter_validation.v0",
            "checkpoint": "TG26d_handoff_filter_validation",
            "config": asdict(self.config),
            "artifact_integrity": self.artifact_integrity,
            "training_runway": {
                "curriculum_filter_is_schedule_only": True,
                "curriculum_labels_learner_visible": False,
                "stage_labels_learner_visible": False,
                "direct_provider_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "broad_random_krk_enabled": False,
                "ecological_spawning_enabled": False,
            },
            "interpretation_rules": {
                "filtered_train_like": "curriculum_runway_signal_not_stage_competence",
                "unfiltered_curriculum": "stage_generalization_signal",
                "boundary_near_miss": "bridge_beyond_obvious_handoff_signal",
                "m4_policy": "no_m4_from_filtered_heldout_only",
            },
            "foundation": self.foundation_payload,
            "regression": self.regression,
            "stages": self.stages,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_handoff_filter_validation(*, config: HandoffFilterValidationConfig) -> HandoffFilterValidationResult:
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
        raise RuntimeError("TG26d requires TG25 Mate_In_2 foundation ranker")
    base_config = _edge_config(config)

    stages = [
        _run_stage_validation(
            label="edge_trap",
            diagnostic_name="Edge_Trap_Close",
            generator="edge",
            ideal_white_moves=3,
            threshold=config.edge_success_threshold,
            seed=config.seed,
            config=config,
            edge_config=base_config,
            mate_ranker=foundation.mate1_ranker,
            mate2_ranker=mate2_ranker,
        ),
        _run_stage_validation(
            label="fence_hold",
            diagnostic_name="Fence_Hold_Approach",
            generator="fence",
            ideal_white_moves=4,
            threshold=config.fence_success_threshold,
            seed=config.seed + 10,
            config=config,
            edge_config=base_config,
            mate_ranker=foundation.mate1_ranker,
            mate2_ranker=mate2_ranker,
        ),
    ]
    regression = _evaluate_foundation_regression(foundation_payload, config=base_config)
    decision = _decision(stages=stages, regression=regression)
    return HandoffFilterValidationResult(
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
        stages=stages,
        regression=regression,
        decision=decision,
    )


def _edge_config(config: HandoffFilterValidationConfig) -> EdgeFenceCurriculumConfig:
    return EdgeFenceCurriculumConfig(
        seed=config.seed,
        foundation_seed=config.foundation_seed,
        foundation_mate1_train_count=config.foundation_mate1_train_count,
        foundation_mate1_heldout_count=config.foundation_mate1_heldout_count,
        foundation_mate1_mirror_count=config.foundation_mate1_mirror_count,
        foundation_mate2_train_count=config.foundation_mate2_train_count,
        foundation_mate2_heldout_count=config.foundation_mate2_heldout_count,
        train_chunk_size=config.train_chunk_size,
        eval_window_size=config.eval_window_size,
        max_chunks_per_stage=config.max_chunks_per_stage,
        edge_success_threshold=config.edge_success_threshold,
        fence_success_threshold=config.fence_success_threshold,
        mate1_regression_threshold=config.mate1_regression_threshold,
        mate2_regression_threshold=config.mate2_regression_threshold,
        eta_m3=config.eta_m3,
        max_generation_attempts=config.max_generation_attempts,
        max_samples=config.max_samples,
        top_k_deep_score=config.top_k_deep_score,
        strict_safety_gate=config.strict_safety_gate,
        edge_generation_requires_handoff_candidate=True,
        fence_generation_requires_handoff_candidate=True,
    )


def _artifact_integrity(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "parseable_full_json": False,
            "reason": "missing",
        }
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
        parseable = isinstance(payload, dict)
        schema = payload.get("schema_version") if isinstance(payload, dict) else None
        checkpoint = payload.get("checkpoint") if isinstance(payload, dict) else None
    except Exception as exc:  # pragma: no cover - exact parser exception is not important for artifact.
        parseable = False
        schema = None
        checkpoint = None
        return {
            "path": str(path),
            "exists": True,
            "byte_size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "parseable_full_json": False,
            "reason": str(exc),
        }
    return {
        "path": str(path),
        "exists": True,
        "byte_size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "parseable_full_json": parseable,
        "schema_version": schema,
        "checkpoint": checkpoint,
        "stage_count": len(payload.get("stages", [])) if isinstance(payload, dict) else 0,
    }


def _run_stage_validation(
    *,
    label: str,
    diagnostic_name: str,
    generator: str,
    ideal_white_moves: int,
    threshold: float,
    seed: int,
    config: HandoffFilterValidationConfig,
    edge_config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
) -> dict[str, Any]:
    ranker = ActionRanker.create(eta_m3=config.eta_m3)
    score_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    runtime_stats = _empty_runtime_stats()
    train_pool = _generate_pool(
        count=config.train_pool_size,
        seed=seed,
        generator=generator,
        mode="filtered_train_like",
        excluded=set(),
        config=edge_config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
        score_cache=score_cache,
        cheap_cache=cheap_cache,
        runtime_stats=runtime_stats,
    )
    excluded = set(train_pool["fens"])
    eval_pools = {
        "filtered_train_like": _generate_pool(
            count=config.eval_window_size,
            seed=seed + 1,
            generator=generator,
            mode="filtered_train_like",
            excluded=excluded,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        ),
        "unfiltered_curriculum": _generate_pool(
            count=config.eval_window_size,
            seed=seed + 2,
            generator=generator,
            mode="unfiltered_curriculum",
            excluded=excluded,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        ),
        "boundary_near_miss": _generate_pool(
            count=config.eval_window_size,
            seed=seed + 3,
            generator=generator,
            mode="boundary_near_miss",
            excluded=excluded,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        ),
    }
    rng = random.Random(seed + len(label))
    train_chunks: list[dict[str, Any]] = []
    m3_before = ranker.m3_update_count
    for _chunk_index in range(config.max_chunks_per_stage):
        sampled = [rng.choice(train_pool["fens"]) for _ in range(config.train_chunk_size)]
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
    slices = {}
    for slice_name, pool in eval_pools.items():
        evaluated = _evaluate_stage(
            pool["fens"],
            stage_ranker=ranker,
            config=edge_config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
        evaluated["slice_name"] = slice_name
        evaluated["threshold"] = threshold
        slices[slice_name] = evaluated
    m3_updates = ranker.m3_update_count - m3_before
    return {
        "label": label,
        "diagnostic_name": diagnostic_name,
        "generator": generator,
        "ideal_white_moves": ideal_white_moves,
        "threshold": threshold,
        "curriculum_labels_learner_visible": False,
        "train_pool": _pool_summary(train_pool),
        "heldout_pools": {name: _pool_summary(pool) for name, pool in eval_pools.items()},
        "train_chunks": train_chunks,
        "eval_slices": slices,
        "m3_update_count": m3_updates,
        "m4_consolidation_event_count": 0,
        "m4_reason": "blocked_until_unfiltered_or_boundary_heldout_confirms",
        "stage_ranker": ranker.to_dict(),
        "scoring_cost": _with_cache_rates(runtime_stats),
    }


def _generate_pool(
    *,
    count: int,
    seed: int,
    generator: str,
    mode: str,
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
    fens: list[str] = []
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
        if len(fens) >= count:
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
        status = _handoff_status(
            board,
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
        if mode == "unfiltered_curriculum":
            used.add(fen)
            fens.append(fen)
            continue
        if not status["has_viable_cheap_candidate"]:
            rejections["safety_rejected"] += 1
            continue
        if mode == "filtered_train_like":
            if not status["has_handoff_candidate"]:
                rejections["no_handoff_candidate"] += 1
                continue
        elif mode == "boundary_near_miss":
            if status["has_handoff_candidate"]:
                rejections["has_handoff_candidate"] += 1
                continue
        else:
            raise ValueError(f"unknown pool mode: {mode}")
        used.add(fen)
        fens.append(fen)
    if len(fens) < count:
        raise RuntimeError(f"generated {len(fens)} {generator}/{mode} positions, needed {count}")
    return {
        "mode": mode,
        "generator": generator,
        "seed": seed,
        "fens": tuple(fens),
        "stats": {
            "generator_attempts": attempts,
            "accepted_positions": len(fens),
            "acceptance_rate": 0.0 if attempts == 0 else len(fens) / attempts,
            "rejection_reasons": rejections,
            "scoring_cost": _with_cache_rates(_stats_delta(before_stats, runtime_stats)),
            "top_k_deep_score": config.top_k_deep_score,
        },
    }


def _handoff_status(
    board: chess.Board,
    *,
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
    viable = [
        uci for uci, score in cheap_scores.items()
        if not score.get("safety_filter_rejected", False) and float(score.get("reward", 0.0)) > 0.0
    ]
    handoff_types: set[str] = set()
    for uci in top:
        scored = _cached_score_first_move(
            board,
            chess.Move.from_uci(uci),
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            runtime_stats=runtime_stats,
        )
        if scored.get("conversion"):
            handoff_types.add(str(scored.get("handoff", "none")))
    return {
        "has_viable_cheap_candidate": bool(viable),
        "has_handoff_candidate": bool(handoff_types),
        "handoff_types": sorted(handoff_types),
    }


def _pool_summary(pool: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": pool["mode"],
        "generator": pool["generator"],
        "seed": pool["seed"],
        "position_count": len(pool["fens"]),
        **pool["stats"],
        "sample_fens": list(pool["fens"][:5]),
    }


def _stats_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    return {key: int(after.get(key, 0) - before.get(key, 0)) for key in after}


def _with_cache_rates(stats: dict[str, int]) -> dict[str, Any]:
    enriched: dict[str, Any] = dict(stats)
    cheap_total = stats.get("cheap_cache_hits", 0) + stats.get("cheap_cache_misses", 0)
    deep_total = stats.get("deep_cache_hits", 0) + stats.get("deep_cache_misses", 0)
    enriched["cheap_cache_hit_rate"] = 0.0 if cheap_total == 0 else stats.get("cheap_cache_hits", 0) / cheap_total
    enriched["deep_cache_hit_rate"] = 0.0 if deep_total == 0 else stats.get("deep_cache_hits", 0) / deep_total
    return enriched


def _decision(*, stages: list[dict[str, Any]], regression: dict[str, Any]) -> dict[str, Any]:
    foundation_ok = regression["mate1_regression_passed"] and regression["mate2_regression_passed"]
    safety_ok = True
    unfiltered_signal = False
    boundary_signal = False
    filtered_signal = False
    stage_signals: dict[str, dict[str, bool]] = {}
    for stage in stages:
        for metrics in stage["eval_slices"].values():
            safety_ok = safety_ok and metrics["rook_loss_count"] == 0
            safety_ok = safety_ok and metrics["stalemate_count"] == 0
            safety_ok = safety_ok and metrics["illegal_or_no_move_count"] == 0
            safety_ok = safety_ok and metrics["confinement_regression_count"] == 0
        stage_filtered = stage["eval_slices"]["filtered_train_like"]["conversion_count"] > 0
        stage_unfiltered = stage["eval_slices"]["unfiltered_curriculum"]["conversion_count"] > 0
        stage_boundary = stage["eval_slices"]["boundary_near_miss"]["conversion_count"] > 0
        stage_signals[stage["label"]] = {
            "filtered_runway_signal": stage_filtered,
            "unfiltered_generalization_signal": stage_unfiltered,
            "boundary_bridge_signal": stage_boundary,
            "stage_competence_claim": False,
        }
        filtered_signal = filtered_signal or stage_filtered
        unfiltered_signal = unfiltered_signal or stage_unfiltered
        boundary_signal = boundary_signal or stage_boundary
    return {
        "status": "tg26d_validation_complete",
        "foundation_regression_passed": foundation_ok,
        "safety_passed": safety_ok,
        "stage_signals": stage_signals,
        "filtered_runway_signal": filtered_signal,
        "unfiltered_generalization_signal": unfiltered_signal,
        "boundary_bridge_signal": boundary_signal,
        "m4_consolidation_event_count": 0,
        "m4_blocked_reason": "filtered heldout alone is insufficient; bounded unfiltered/boundary signals need larger confirmation",
        "stage_competence_claim": False,
        "stage_competence_blocked_reason": (
            "TG26d separates selection-filter runway from competence; current bounded slices are evidence, not advancement"
        ),
        "broad_random_krk_enabled": False,
        "next_recommended_checkpoint": (
            "Scale the weakest unfiltered/boundary slice safely before broad KRK"
            if unfiltered_signal or boundary_signal
            else "Improve filtered curriculum transfer, then re-run unfiltered and boundary validation"
        ),
    }

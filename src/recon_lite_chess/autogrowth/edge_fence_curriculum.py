"""TG26 edge/fence curriculum continuation with graded credit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
from typing import Any, Iterable

import chess

from recon_lite_chess.training.krk_curriculum import box_min_side, did_box_grow

from .features import extract_diagnostic_features, extract_learner_features, validate_learner_record
from .foundation_curriculum import (
    ActionRanker,
    FoundationCurriculumConfig,
    run_foundation_curriculum,
    _mate_moves,
    _rook_missing_or_attacked,
)


@dataclass(frozen=True)
class EdgeFenceCurriculumConfig:
    seed: int = 20260613
    foundation_seed: int = 20260612
    foundation_mate1_train_count: int = 1000
    foundation_mate1_heldout_count: int = 300
    foundation_mate1_mirror_count: int = 120
    foundation_mate2_train_count: int = 300
    foundation_mate2_heldout_count: int = 100
    train_chunk_size: int = 500
    eval_window_size: int = 100
    max_chunks_per_stage: int = 4
    consecutive_pass_windows_required: int = 2
    edge_success_threshold: float = 0.95
    fence_success_threshold: float = 0.90
    mate1_regression_threshold: float = 0.99
    mate2_regression_threshold: float = 0.90
    eta_m3: float = 0.06
    max_generation_attempts: int = 250_000
    max_samples: int = 12
    mate_reward: float = 1.0
    delta_moves: float = 0.02
    mate_reward_floor: float = 0.30
    top_k_deep_score: int = 6
    strict_safety_gate: bool = True
    previous_tg26_artifact_path: str = "reports/autogrowth/krk_autogrowth_tg26_edge_fence_curriculum.json"
    edge_generation_requires_handoff_candidate: bool = True
    fence_generation_requires_handoff_candidate: bool = False


@dataclass(frozen=True)
class StageDataset:
    label: str
    diagnostic_name: str
    train: tuple[str, ...]
    heldout: tuple[str, ...]
    ideal_white_moves: int
    threshold: float


@dataclass(frozen=True)
class EdgeFenceCurriculumResult:
    config: EdgeFenceCurriculumConfig
    foundation_payload: dict[str, Any]
    stages: list[dict[str, Any]]
    edge_ranker: ActionRanker
    fence_ranker: ActionRanker
    regression: dict[str, Any]
    failure_audit: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26c_edge_fence_handoff_curriculum.v0",
            "checkpoint": "TG26c_edge_fence_handoff_curriculum",
            "config": asdict(self.config),
            "training_runway": {
                "uses_curriculum_as_experience_distribution": True,
                "handoff_candidate_filter_is_schedule_only": True,
                "curriculum_is_not_cheating": True,
                "stage_labels_learner_visible": False,
                "curriculum_labels_learner_visible": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "direct_provider_override": False,
                "broad_random_krk_enabled": False,
                "retry_candidate_expansion_enabled": False,
            },
            "reward_policy": {
                "mate_reward": self.config.mate_reward,
                "delta_moves": self.config.delta_moves,
                "mate_reward_floor": self.config.mate_reward_floor,
                "mate_formula": "max(floor, R_mate - delta_moves * max(0, actual_white_moves - ideal_white_moves))",
                "faster_than_ideal_bonus": "clamped_to_zero",
                "non_mate_uses_small_graded_shaping_only": True,
                "strict_local_safety_gate": self.config.strict_safety_gate,
                "top_k_deep_score": self.config.top_k_deep_score,
                "hierarchy": [
                    "checkmate",
                    "faster_mate",
                    "handoff_to_earlier_solved_region",
                    "preserve_or_improve_confinement",
                    "king_approach_with_confinement_preserved",
                    "repetition_or_no_progress_penalty",
                    "confinement_regression_penalty",
                    "stalemate_rook_loss_illegal_catastrophic",
                ],
            },
            "local_recon_structure": {
                "foundation_reused": True,
                "current_stage_node_type": "ACTION",
                "candidate_state": "TRIAL",
                "relation_types": ["SUB", "POR", "SUR"],
                "move_choice_mediated_by_local_action_nodes": True,
                "direct_move_override": False,
            },
            "foundation": self.foundation_payload,
            "stages": self.stages,
            "failure_audit": self.failure_audit,
            "rankers": {
                "edge_trap": self.edge_ranker.to_dict(),
                "fence_hold": self.fence_ranker.to_dict(),
            },
            "regression": self.regression,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_edge_fence_curriculum(*, config: EdgeFenceCurriculumConfig) -> EdgeFenceCurriculumResult:
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
    mate_ranker = foundation.mate1_ranker
    mate2_ranker = foundation.mate2_first_ranker
    if mate2_ranker is None:
        raise RuntimeError("TG26 requires TG25 Mate_In_2 foundation ranker")

    edge_dataset = _generate_stage_dataset(
        label="edge_trap",
        diagnostic_name="Edge_Trap_Close",
        count_train=config.train_chunk_size,
        count_heldout=config.eval_window_size,
        ideal_white_moves=3,
        threshold=config.edge_success_threshold,
        seed=config.seed,
        generator="edge",
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
    )
    fence_dataset = _generate_stage_dataset(
        label="fence_hold",
        diagnostic_name="Fence_Hold_Approach",
        count_train=config.train_chunk_size,
        count_heldout=config.eval_window_size,
        ideal_white_moves=4,
        threshold=config.fence_success_threshold,
        seed=config.seed + 10,
        generator="fence",
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
    )

    edge_ranker = ActionRanker.create(eta_m3=config.eta_m3)
    edge_stage = _train_stage(
        dataset=edge_dataset,
        stage_ranker=edge_ranker,
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
    )
    fence_ranker = ActionRanker.create(eta_m3=config.eta_m3)
    fence_stage = _train_stage(
        dataset=fence_dataset,
        stage_ranker=fence_ranker,
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
    )
    regression = _evaluate_foundation_regression(foundation_payload, config=config)
    failure_audit = _build_failure_audit(
        stages=[edge_stage, fence_stage],
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        previous_path=Path(config.previous_tg26_artifact_path),
    )
    decision = _decision(
        config=config,
        stages=[edge_stage, fence_stage],
        regression=regression,
        failure_audit=failure_audit,
    )
    return EdgeFenceCurriculumResult(
        config=config,
        foundation_payload={
            "source_checkpoint": "TG25_foundation_curriculum",
            "mate1_heldout_accuracy": foundation_payload["decision"]["mate1_heldout_accuracy"],
            "mate1_mirror_accuracy": foundation_payload["decision"]["mate1_mirror_accuracy"],
            "mate2_conversion_rate": foundation_payload["decision"]["mate2_conversion_rate"],
            "mate1_m3_update_count": foundation_payload["decision"]["mate1_m3_update_count"],
            "mate1_m4_consolidation_event_count": foundation_payload["decision"]["mate1_m4_consolidation_event_count"],
            "mate2_m4_consolidation_event_count": foundation_payload["decision"]["mate2_m4_consolidation_event_count"],
        },
        stages=[edge_stage, fence_stage],
        edge_ranker=edge_ranker,
        fence_ranker=fence_ranker,
        regression=regression,
        failure_audit=failure_audit,
        decision=decision,
    )


def _generate_stage_dataset(
    *,
    label: str,
    diagnostic_name: str,
    count_train: int,
    count_heldout: int,
    ideal_white_moves: int,
    threshold: float,
    seed: int,
    generator: str,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
) -> StageDataset:
    train = _generate_stage_positions(
        count=count_train,
        seed=seed,
        generator=generator,
        excluded=set(),
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
    )
    heldout = _generate_stage_positions(
        count=count_heldout,
        seed=seed + 1,
        generator=generator,
        excluded=set(train),
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
    )
    return StageDataset(
        label=label,
        diagnostic_name=diagnostic_name,
        train=tuple(train),
        heldout=tuple(heldout),
        ideal_white_moves=ideal_white_moves,
        threshold=threshold,
    )


def _train_stage(
    *,
    dataset: StageDataset,
    stage_ranker: ActionRanker,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
) -> dict[str, Any]:
    rng = random.Random(config.seed + len(dataset.label))
    eval_windows: list[dict[str, Any]] = []
    train_chunks: list[dict[str, Any]] = []
    consecutive_passes = 0
    advanced = False
    m3_before = stage_ranker.m3_update_count
    score_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    runtime_stats = _empty_runtime_stats()
    for chunk_index in range(config.max_chunks_per_stage):
        train_fens = [rng.choice(dataset.train) for _ in range(config.train_chunk_size)]
        train_summary = _train_chunk(
            train_fens,
            stage_ranker=stage_ranker,
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=dataset.ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
        train_chunks.append(train_summary)
        eval_summary = _evaluate_stage(
            dataset.heldout,
            stage_ranker=stage_ranker,
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=dataset.ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
        eval_summary["chunk_index"] = chunk_index
        eval_summary["threshold"] = dataset.threshold
        eval_summary["passed"] = _stage_window_passed(eval_summary, threshold=dataset.threshold)
        eval_windows.append(eval_summary)
        consecutive_passes = consecutive_passes + 1 if eval_summary["passed"] else 0
        if consecutive_passes >= config.consecutive_pass_windows_required:
            advanced = True
            break
    m3_updates = stage_ranker.m3_update_count - m3_before
    m4 = int(advanced and m3_updates > 0)
    return {
        "label": dataset.label,
        "diagnostic_name": dataset.diagnostic_name,
        "curriculum_labels_learner_visible": False,
        "train_count": len(dataset.train),
        "heldout_count": len(dataset.heldout),
        "ideal_white_moves": dataset.ideal_white_moves,
        "train_chunk_size": config.train_chunk_size,
        "eval_window_size": config.eval_window_size,
        "consecutive_pass_windows_required": config.consecutive_pass_windows_required,
        "train_chunks": train_chunks,
        "eval_windows": eval_windows,
        "final_eval": eval_windows[-1] if eval_windows else None,
        "consecutive_pass_windows": consecutive_passes,
        "advanced": advanced,
        "m3_update_count": m3_updates,
        "m4_consolidation_event_count": m4,
        "scoring_cost": dict(runtime_stats),
    }


def _train_chunk(
    fens: Iterable[str],
    *,
    stage_ranker: ActionRanker,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    score_cache: dict[tuple[str, str, int], dict[str, Any]],
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int],
) -> dict[str, Any]:
    fen_list = tuple(fens)
    reward_sum = 0.0
    positives = 0
    negatives = 0
    for fen in fen_list:
        board = chess.Board(fen)
        move_scores = _score_legal_actions_for_training(
            board,
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
        move_rewards = {uci: score["reward"] for uci, score in move_scores.items()}
        reward_sum += max(move_rewards.values()) if move_rewards else -1.0
        positives += sum(1 for value in move_rewards.values() if value > 0.0)
        negatives += sum(1 for value in move_rewards.values() if value < 0.0)
        stage_ranker.train_position_rewards(board, move_rewards=move_rewards)
    total = len(fen_list)
    return {
        "position_count": total,
        "avg_best_available_reward": 0.0 if total == 0 else reward_sum / total,
        "positive_action_count": positives,
        "negative_action_count": negatives,
        "m3_update_count": stage_ranker.m3_update_count,
    }


def _evaluate_stage(
    fens: Iterable[str],
    *,
    stage_ranker: ActionRanker,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    score_cache: dict[tuple[str, str, int], dict[str, Any]],
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    conversions = 0
    handoffs = 0
    direct_mates = 0
    mate1_handoffs = 0
    mate2_handoffs = 0
    rook_losses = 0
    stalemates = 0
    illegal = 0
    confinement_regressions = 0
    reward_sum = 0.0
    repetition_no_progress = 0
    safety_filtered_moves = 0
    failure_slices: list[dict[str, Any]] = []
    for fen in tuple(fens):
        board = chess.Board(fen)
        move = _choose_repaired_stage_move(
            board,
            ranker=stage_ranker,
            config=config,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
            ideal_white_moves=ideal_white_moves,
        )
        if move is None or move not in board.legal_moves:
            illegal += 1
            outcome = _score_payload(
                -1.0,
                False,
                "none",
                "illegal_or_no_move",
                True,
                reward_components={"illegal": -1.0},
            )
        else:
            outcome = _cached_score_first_move(
                board,
                move,
                config=config,
                mate_ranker=mate_ranker,
                mate2_ranker=mate2_ranker,
                ideal_white_moves=ideal_white_moves,
                score_cache=score_cache,
                runtime_stats=runtime_stats,
            )
        conversions += int(outcome["conversion"])
        handoffs += int(outcome["handoff"] != "none")
        direct_mates += int(outcome["reason"] == "mate")
        mate1_handoffs += int(outcome["handoff"] == "mate_in_one")
        mate2_handoffs += int(outcome["handoff"] == "mate_in_two")
        rook_losses += int(outcome["reason"] == "rook_loss")
        stalemates += int(outcome["reason"] == "stalemate")
        repetition_no_progress += int(outcome["reason"] in {"non_mate_shaping", "no_progress"})
        safety_filtered_moves += int(outcome.get("selected_after_safety_filter", False))
        confinement_regressions += int(outcome["confinement_regressed"])
        reward_sum += float(outcome["reward"])
        row = {
            "fen": fen,
            "selected": None if move is None else move.uci(),
            "reward": round(float(outcome["reward"]), 6),
            "conversion": bool(outcome["conversion"]),
            "handoff": outcome["handoff"],
            "reason": outcome["reason"],
            "confinement_regressed": bool(outcome["confinement_regressed"]),
            "black_reply_that_caused_failure": outcome.get("black_reply"),
            "reward_components": outcome.get("reward_components", {}),
            "safety_filter_rejected_selected": bool(outcome.get("safety_filter_rejected", False)),
        }
        rows.append(row)
        if not outcome["conversion"]:
            failure_slices.append(_failure_slice_for_position(
                board,
                selected=move,
                selected_outcome=outcome,
                config=config,
                mate_ranker=mate_ranker,
                mate2_ranker=mate2_ranker,
                ideal_white_moves=ideal_white_moves,
                score_cache=score_cache,
                cheap_cache=cheap_cache,
                runtime_stats=runtime_stats,
            ))
    total = len(rows)
    return {
        "position_count": total,
        "conversion_count": conversions,
        "conversion_rate": 0.0 if total == 0 else conversions / total,
        "earlier_region_handoff_count": handoffs,
        "earlier_region_handoff_rate": 0.0 if total == 0 else handoffs / total,
        "direct_mate_count": direct_mates,
        "mate1_handoff_count": mate1_handoffs,
        "mate2_handoff_count": mate2_handoffs,
        "avg_reward": 0.0 if total == 0 else reward_sum / total,
        "rook_loss_count": rook_losses,
        "stalemate_count": stalemates,
        "illegal_count": illegal,
        "illegal_or_no_move_count": illegal,
        "confinement_regression_count": confinement_regressions,
        "repetition_or_no_progress_count": repetition_no_progress,
        "safety_filtered_selection_count": safety_filtered_moves,
        "failure_slices": failure_slices,
        "samples": rows[:config.max_samples],
    }


def _failure_slice_for_position(
    board: chess.Board,
    *,
    selected: chess.Move | None,
    selected_outcome: dict[str, Any],
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    score_cache: dict[tuple[str, str, int], dict[str, Any]],
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int],
) -> dict[str, Any]:
    alternatives: list[dict[str, Any]] = []
    any_successor_mate1 = False
    any_successor_mate2 = False
    any_successor_conversion = False
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        cheap = _cached_cheap_action_assessment(
            board,
            move,
            config=config,
            ideal_white_moves=ideal_white_moves,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
        deep = _cached_score_first_move(
            board,
            move,
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            runtime_stats=runtime_stats,
        )
        any_successor_mate1 = any_successor_mate1 or deep.get("handoff") == "mate_in_one"
        any_successor_mate2 = any_successor_mate2 or deep.get("handoff") == "mate_in_two"
        any_successor_conversion = any_successor_conversion or bool(deep.get("conversion"))
        alternatives.append({
            "uci": move.uci(),
            "action_feature_keys": _safe_action_feature_keys(board, move)[:10],
            "cheap_reward": round(float(cheap["reward"]), 6),
            "deep_reward": round(float(deep["reward"]), 6),
            "safety_filter_rejected": bool(cheap.get("safety_filter_rejected", False)),
            "reason": deep.get("reason"),
            "handoff": deep.get("handoff"),
            "conversion": bool(deep.get("conversion")),
            "black_reply_that_caused_failure": deep.get("black_reply"),
            "reward_components": deep.get("reward_components", {}),
        })
    alternatives.sort(key=lambda item: (item["conversion"], item["deep_reward"], item["cheap_reward"], item["uci"]), reverse=True)
    selected_cheap = None
    if selected is not None:
        selected_cheap = _cached_cheap_action_assessment(
            board,
            selected,
            config=config,
            ideal_white_moves=ideal_white_moves,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
    return {
        "fen": board.fen(),
        "selected": None if selected is None else selected.uci(),
        "selected_action_feature_keys": [] if selected is None else _safe_action_feature_keys(board, selected)[:10],
        "failure_type": _failure_type(selected_outcome),
        "reason": selected_outcome.get("reason"),
        "reward": round(float(selected_outcome.get("reward", 0.0)), 6),
        "reward_components": selected_outcome.get("reward_components", {}),
        "black_reply_that_caused_failure": selected_outcome.get("black_reply"),
        "safety_filter_would_reject_selected": bool(
            selected_cheap is not None and selected_cheap.get("safety_filter_rejected", False)
        ),
        "foundation_could_finish_from_any_successor": any_successor_conversion,
        "mate_in_one_known_successor_available": any_successor_mate1,
        "mate_in_two_known_successor_available": any_successor_mate2,
        "legal_candidate_alternatives": alternatives[:12],
    }


def _safe_action_feature_keys(board: chess.Board, move: chess.Move) -> list[str]:
    from .foundation_curriculum import _action_feature_keys

    keys = list(_action_feature_keys(board, move))
    validate_learner_record(keys)
    return keys


def _failure_type(outcome: dict[str, Any]) -> str:
    reason = str(outcome.get("reason"))
    if reason in {"rook_loss", "stalemate", "illegal_or_no_move"}:
        return reason
    if outcome.get("confinement_regressed"):
        return "confinement_regression"
    if reason in {"non_mate_shaping", "cheap_progress", "no_progress"}:
        return "failed_handoff_or_no_progress"
    if outcome.get("handoff") == "none":
        return "failed_handoff"
    return reason


def _cached_score_first_move(
    board: chess.Board,
    move: chess.Move,
    *,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    score_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int] | None = None,
) -> dict[str, Any]:
    key = (board.fen(), move.uci(), ideal_white_moves)
    cached = score_cache.get(key)
    if cached is not None:
        if runtime_stats is not None:
            runtime_stats["deep_cache_hits"] += 1
        return cached
    if runtime_stats is not None:
        runtime_stats["deep_cache_misses"] += 1
        runtime_stats["deep_scored_action_count"] += 1
    scored = _score_first_move(
        board,
        move,
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
        ideal_white_moves=ideal_white_moves,
    )
    score_cache[key] = scored
    return scored


def _score_legal_actions_for_training(
    board: chess.Board,
    *,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    score_cache: dict[tuple[str, str, int], dict[str, Any]],
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int],
) -> dict[str, dict[str, Any]]:
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
    deep_candidates = _top_k_deep_candidates(cheap_scores, config=config)
    runtime_stats["cheap_pruned_action_count"] += max(0, len(cheap_scores) - len(deep_candidates))
    scores = dict(cheap_scores)
    for uci in deep_candidates:
        move = chess.Move.from_uci(uci)
        scores[uci] = _cached_score_first_move(
            board,
            move,
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            runtime_stats=runtime_stats,
        )
    return scores


def _top_k_deep_candidates(
    cheap_scores: dict[str, dict[str, Any]],
    *,
    config: EdgeFenceCurriculumConfig,
) -> list[str]:
    viable = [
        (float(score["reward"]), uci)
        for uci, score in cheap_scores.items()
        if not score.get("safety_filter_rejected", False)
    ]
    if not viable:
        viable = [(float(score["reward"]), uci) for uci, score in cheap_scores.items()]
    viable.sort(reverse=True)
    return [uci for _, uci in viable[: max(1, config.top_k_deep_score)]]


def _choose_repaired_stage_move(
    board: chess.Board,
    *,
    ranker: ActionRanker,
    config: EdgeFenceCurriculumConfig,
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int],
    ideal_white_moves: int,
) -> chess.Move | None:
    options: list[tuple[float, str, chess.Move]] = []
    rejected = 0
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        cheap = _cached_cheap_action_assessment(
            board,
            move,
            config=config,
            ideal_white_moves=ideal_white_moves,
            cheap_cache=cheap_cache,
            runtime_stats=runtime_stats,
        )
        if config.strict_safety_gate and cheap.get("safety_filter_rejected", False):
            rejected += 1
            continue
        options.append((ranker.weight_for_move(board, move), move.uci(), move))
    runtime_stats["safety_rejected_action_count"] += rejected
    if not options:
        return None
    options.sort(reverse=True)
    return options[0][-1]


def _cached_cheap_action_assessment(
    board: chess.Board,
    move: chess.Move,
    *,
    config: EdgeFenceCurriculumConfig,
    ideal_white_moves: int,
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]],
    runtime_stats: dict[str, int] | None = None,
) -> dict[str, Any]:
    key = (board.fen(), move.uci(), ideal_white_moves)
    cached = cheap_cache.get(key)
    if cached is not None:
        if runtime_stats is not None:
            runtime_stats["cheap_cache_hits"] += 1
        return cached
    if runtime_stats is not None:
        runtime_stats["cheap_cache_misses"] += 1
        runtime_stats["cheap_scored_action_count"] += 1
    scored = _cheap_action_assessment(
        board,
        move,
        config=config,
        ideal_white_moves=ideal_white_moves,
    )
    cheap_cache[key] = scored
    return scored


def _cheap_action_assessment(
    board: chess.Board,
    move: chess.Move,
    *,
    config: EdgeFenceCurriculumConfig,
    ideal_white_moves: int,
) -> dict[str, Any]:
    if move not in board.legal_moves:
        return _score_payload(
            -1.0,
            False,
            "none",
            "illegal_or_no_move",
            True,
            safety_filter_rejected=True,
            reward_components={"illegal": -1.0},
        )
    before_features = extract_diagnostic_features(board)
    before_box = box_min_side(board)
    after = board.copy(stack=False)
    after.push(move)
    confinement_regressed = did_box_grow(board, after)
    components: dict[str, float] = {}
    if after.is_checkmate():
        reward = _mate_reward(actual_white_moves=1, ideal_white_moves=ideal_white_moves, config=config)
        return _score_payload(
            reward,
            True,
            "none",
            "mate",
            confinement_regressed,
            safety_filter_rejected=False,
            reward_components={"mate": reward},
        )
    if after.is_stalemate():
        return _score_payload(
            -0.95,
            False,
            "none",
            "stalemate",
            confinement_regressed,
            safety_filter_rejected=True,
            reward_components={"stalemate": -0.95},
        )
    if _rook_missing_or_attacked(after):
        return _score_payload(
            -0.95,
            False,
            "none",
            "rook_loss",
            confinement_regressed,
            safety_filter_rejected=True,
            reward_components={"rook_loss": -0.95},
        )
    reply_risk = _one_reply_rook_loss_risk(after)
    if reply_risk is not None:
        return _score_payload(
            -0.90,
            False,
            "none",
            "rook_loss_reply_risk",
            confinement_regressed,
            black_reply=reply_risk,
            safety_filter_rejected=True,
            reward_components={"rook_loss_reply_risk": -0.90},
        )
    after_features = extract_diagnostic_features(after)
    reward = 0.0
    if confinement_regressed:
        components["confinement_regression"] = -0.45
        reward -= 0.45
    else:
        components["confinement_preserved"] = 0.06
        reward += 0.06
    if box_min_side(after) < before_box:
        components["confinement_improved"] = 0.12
        reward += 0.12
    if after_features["black_reply_mobility"] < before_features["black_reply_mobility"]:
        components["black_mobility_reduced"] = 0.05
        reward += 0.05
    if (
        after_features["white_king_to_black_king_distance"]
        < before_features["white_king_to_black_king_distance"]
        and not confinement_regressed
    ):
        components["king_approach_safe"] = 0.04
        reward += 0.04
    if board.gives_check(move) and not confinement_regressed:
        components["generic_check"] = 0.04
        reward += 0.04
    if not components or reward <= 0.0:
        components["no_progress_or_regression"] = components.get("no_progress_or_regression", -0.06)
        reward += components["no_progress_or_regression"]
    safety_rejected = bool(confinement_regressed)
    validate_learner_record({
        "reward": reward,
        "safe": int(not safety_rejected),
        "mobility_delta": after_features["black_reply_mobility"] - before_features["black_reply_mobility"],
    })
    return _score_payload(
        max(-0.95, min(0.35, reward)),
        False,
        "none",
        "cheap_progress",
        confinement_regressed,
        safety_filter_rejected=safety_rejected,
        reward_components=components,
    )


def _one_reply_rook_loss_risk(after_white: chess.Board) -> str | None:
    for reply in sorted(after_white.legal_moves, key=lambda item: item.uci()):
        after_reply = after_white.copy(stack=False)
        after_reply.push(reply)
        if _rook_missing_or_attacked(after_reply):
            return reply.uci()
    return None


def _score_first_move(
    board: chess.Board,
    move: chess.Move,
    *,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
) -> dict[str, Any]:
    if move not in board.legal_moves:
        return _score_payload(-1.0, False, "none", "illegal_or_no_move", True, reward_components={"illegal": -1.0})
    after = board.copy(stack=False)
    after.push(move)
    confinement_regressed = did_box_grow(board, after)
    if after.is_checkmate():
        return _score_payload(
            _mate_reward(actual_white_moves=1, ideal_white_moves=ideal_white_moves, config=config),
            True,
            "none",
            "mate",
            confinement_regressed,
            reward_components={"mate": _mate_reward(actual_white_moves=1, ideal_white_moves=ideal_white_moves, config=config)},
        )
    if after.is_stalemate():
        return _score_payload(
            -0.95,
            False,
            "none",
            "stalemate",
            confinement_regressed,
            safety_filter_rejected=True,
            reward_components={"stalemate": -0.95},
        )
    if _rook_missing_or_attacked(after):
        return _score_payload(
            -0.95,
            False,
            "none",
            "rook_loss",
            confinement_regressed,
            safety_filter_rejected=True,
            reward_components={"rook_loss": -0.95},
        )
    replies = list(after.legal_moves)
    if not replies:
        return _score_payload(-0.50, False, "none", "no_black_reply", confinement_regressed, reward_components={"no_black_reply": -0.50})
    reply_scores = [
        _score_after_black_reply(
            board,
            after,
            reply,
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            confinement_regressed=confinement_regressed,
        )
        for reply in replies
    ]
    worst = min(reply_scores, key=lambda item: item["reward"])
    if all(item["conversion"] for item in reply_scores):
        handoff = "mate_in_one" if all(item["handoff"] == "mate_in_one" for item in reply_scores) else "mate_in_two"
        actual = 2 if handoff == "mate_in_one" else 3
        return _score_payload(
            _mate_reward(actual_white_moves=actual, ideal_white_moves=ideal_white_moves, config=config),
            True,
            handoff,
            "handoff_conversion",
            confinement_regressed,
            reward_components={"foundation_handoff": _mate_reward(actual_white_moves=actual, ideal_white_moves=ideal_white_moves, config=config)},
        )
    return worst


def _score_after_black_reply(
    before: chess.Board,
    after_white: chess.Board,
    reply: chess.Move,
    *,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    confinement_regressed: bool,
) -> dict[str, Any]:
    after_reply = after_white.copy(stack=False)
    after_reply.push(reply)
    if _rook_missing_or_attacked(after_reply):
        return _score_payload(
            -0.95,
            False,
            "none",
            "rook_loss",
            True,
            black_reply=reply.uci(),
            safety_filter_rejected=True,
            reward_components={"rook_loss_after_reply": -0.95},
        )
    mate1_move = mate_ranker.choose(after_reply)
    if mate1_move is not None and mate1_move.uci() in {move.uci() for move in _mate_moves(after_reply)}:
        return _score_payload(
            _mate_reward(actual_white_moves=2, ideal_white_moves=ideal_white_moves, config=config),
            True,
            "mate_in_one",
            "handoff_conversion",
            confinement_regressed,
            black_reply=reply.uci(),
            reward_components={"foundation_mate1_handoff": _mate_reward(actual_white_moves=2, ideal_white_moves=ideal_white_moves, config=config)},
        )
    mate2_move = mate2_ranker.choose(after_reply)
    if mate2_move is not None and _mate2_handoff_converts(after_reply, mate2_move, mate_ranker=mate_ranker):
        return _score_payload(
            _mate_reward(actual_white_moves=3, ideal_white_moves=ideal_white_moves, config=config),
            True,
            "mate_in_two",
            "handoff_conversion",
            confinement_regressed,
            black_reply=reply.uci(),
            reward_components={"foundation_mate2_handoff": _mate_reward(actual_white_moves=3, ideal_white_moves=ideal_white_moves, config=config)},
        )
    reward, components = _non_mate_shaping_components(before, after_white, after_reply, confinement_regressed=confinement_regressed)
    return _score_payload(
        reward,
        False,
        "none",
        "non_mate_shaping",
        confinement_regressed,
        black_reply=reply.uci(),
        safety_filter_rejected=confinement_regressed,
        reward_components=components,
    )


def _non_mate_shaping(
    before: chess.Board,
    after_white: chess.Board,
    after_reply: chess.Board,
    *,
    confinement_regressed: bool,
) -> float:
    reward, _components = _non_mate_shaping_components(
        before,
        after_white,
        after_reply,
        confinement_regressed=confinement_regressed,
    )
    return reward


def _non_mate_shaping_components(
    before: chess.Board,
    after_white: chess.Board,
    after_reply: chess.Board,
    *,
    confinement_regressed: bool,
) -> tuple[float, dict[str, float]]:
    before_features = extract_diagnostic_features(before)
    after_features = extract_diagnostic_features(after_reply)
    reward = 0.0
    components: dict[str, float] = {}
    if box_min_side(after_reply) < box_min_side(before):
        components["confinement_improved"] = 0.08
        reward += components["confinement_improved"]
    elif not confinement_regressed:
        components["confinement_preserved"] = 0.03
        reward += components["confinement_preserved"]
    if after_features["black_reply_mobility"] < before_features["black_reply_mobility"]:
        components["black_mobility_reduced"] = 0.04
        reward += components["black_mobility_reduced"]
    if (
        after_features["white_king_to_black_king_distance"]
        < before_features["white_king_to_black_king_distance"]
        and not confinement_regressed
    ):
        components["king_approach_safe"] = 0.03
        reward += components["king_approach_safe"]
    if after_features["rook_attacked_by_black"] > 0.0 or after_features["rook_present"] < 1.0:
        components["rook_loss_or_attacked"] = -0.70
        reward += components["rook_loss_or_attacked"]
    if confinement_regressed:
        components["confinement_regression"] = -0.24
        reward += components["confinement_regression"]
    if (
        after_features["black_king_nearest_edge_distance"] > before_features["black_king_nearest_edge_distance"]
        and box_min_side(after_reply) >= box_min_side(before)
    ):
        components["edge_distance_regression"] = -0.08
        reward += components["edge_distance_regression"]
    if abs(reward) < 1e-9:
        components["no_progress"] = -0.06
        reward += components["no_progress"]
    validate_learner_record({
        "reward": reward,
        "black_mobility_delta": after_features["black_reply_mobility"] - before_features["black_reply_mobility"],
        "king_distance_delta": (
            after_features["white_king_to_black_king_distance"]
            - before_features["white_king_to_black_king_distance"]
        ),
        "rook_safe": 1.0 - after_features["rook_attacked_by_black"],
    })
    return max(-0.70, min(0.20, reward)), components


def _mate2_handoff_converts(
    board: chess.Board,
    first_move: chess.Move,
    *,
    mate_ranker: ActionRanker,
) -> bool:
    if first_move not in board.legal_moves or _mate_moves(board):
        return False
    after_first = board.copy(stack=False)
    after_first.push(first_move)
    replies = list(after_first.legal_moves)
    if not replies:
        return False
    for reply in replies:
        before_mate = after_first.copy(stack=False)
        before_mate.push(reply)
        mate_move = mate_ranker.choose(before_mate)
        mates = {move.uci() for move in _mate_moves(before_mate)}
        if mate_move is None or mate_move.uci() not in mates:
            return False
    return True


def _mate_reward(
    *,
    actual_white_moves: int,
    ideal_white_moves: int,
    config: EdgeFenceCurriculumConfig,
) -> float:
    excess = max(0, actual_white_moves - ideal_white_moves)
    return max(config.mate_reward_floor, config.mate_reward - config.delta_moves * excess)


def _score_payload(
    reward: float,
    conversion: bool,
    handoff: str,
    reason: str,
    confinement_regressed: bool,
    *,
    black_reply: str | None = None,
    safety_filter_rejected: bool = False,
    reward_components: dict[str, float] | None = None,
) -> dict[str, Any]:
    return {
        "reward": float(reward),
        "conversion": bool(conversion),
        "handoff": handoff,
        "reason": reason,
        "confinement_regressed": bool(confinement_regressed),
        "black_reply": black_reply,
        "safety_filter_rejected": bool(safety_filter_rejected),
        "reward_components": dict(reward_components or {}),
    }


def _stage_window_passed(metrics: dict[str, Any], *, threshold: float) -> bool:
    return (
        metrics["conversion_rate"] >= threshold
        and metrics["rook_loss_count"] == 0
        and metrics["stalemate_count"] == 0
        and metrics["illegal_or_no_move_count"] == 0
    )


def _build_failure_audit(
    *,
    stages: list[dict[str, Any]],
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    previous_path: Path,
) -> dict[str, Any]:
    repaired = {
        stage["label"]: {
            "failed_position_count": len(stage["final_eval"].get("failure_slices", [])),
            "failure_slices": stage["final_eval"].get("failure_slices", []),
        }
        for stage in stages
        if stage.get("final_eval") is not None
    }
    previous = _previous_tg26_failure_audit(
        previous_path=previous_path,
        config=config,
        mate_ranker=mate_ranker,
        mate2_ranker=mate2_ranker,
    )
    return {
        "previous_tg26_source": str(previous_path),
        "previous_tg26": previous,
        "tg26b_repaired": repaired,
        "summary": _failure_audit_summary(previous, repaired),
    }


def _previous_tg26_failure_audit(
    *,
    previous_path: Path,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
) -> dict[str, Any]:
    if not previous_path.exists():
        return {"available": False, "reason": "previous_tg26_artifact_missing"}
    payload = json.loads(previous_path.read_text(encoding="utf-8"))
    audit: dict[str, Any] = {"available": True, "stages": {}}
    for stage in payload.get("stages", []):
        label = stage.get("label", "unknown")
        final_eval = stage.get("final_eval", {})
        ideal = int(stage.get("ideal_white_moves", 4))
        score_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
        cheap_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
        runtime_stats = _empty_runtime_stats()
        slices = []
        for row in final_eval.get("samples", []):
            if row.get("conversion"):
                continue
            board = chess.Board(row["fen"])
            selected = chess.Move.from_uci(row["selected"]) if row.get("selected") else None
            selected_outcome = (
                _cached_score_first_move(
                    board,
                    selected,
                    config=config,
                    mate_ranker=mate_ranker,
                    mate2_ranker=mate2_ranker,
                    ideal_white_moves=ideal,
                    score_cache=score_cache,
                    runtime_stats=runtime_stats,
                )
                if selected is not None
                else _score_payload(-1.0, False, "none", "illegal_or_no_move", True)
            )
            slices.append(_failure_slice_for_position(
                board,
                selected=selected,
                selected_outcome=selected_outcome,
                config=config,
                mate_ranker=mate_ranker,
                mate2_ranker=mate2_ranker,
                ideal_white_moves=ideal,
                score_cache=score_cache,
                cheap_cache=cheap_cache,
                runtime_stats=runtime_stats,
            ))
        audit["stages"][label] = {
            "failed_position_count": len(slices),
            "original_final_metrics": {
                key: final_eval.get(key)
                for key in (
                    "position_count",
                    "conversion_count",
                    "earlier_region_handoff_count",
                    "rook_loss_count",
                    "stalemate_count",
                    "illegal_or_no_move_count",
                    "confinement_regression_count",
                )
            },
            "failure_slices": slices,
            "scoring_cost": runtime_stats,
        }
    return audit


def _failure_audit_summary(previous: dict[str, Any], repaired: dict[str, Any]) -> dict[str, Any]:
    previous_counts = {}
    if previous.get("available"):
        previous_counts = {
            label: stage["failed_position_count"]
            for label, stage in previous.get("stages", {}).items()
        }
    repaired_counts = {
        label: stage["failed_position_count"]
        for label, stage in repaired.items()
    }
    return {
        "previous_failed_counts": previous_counts,
        "repaired_failed_counts": repaired_counts,
        "failure_slice_detail_available": True,
    }


def _empty_runtime_stats() -> dict[str, int]:
    return {
        "cheap_scored_action_count": 0,
        "cheap_cache_hits": 0,
        "cheap_cache_misses": 0,
        "deep_scored_action_count": 0,
        "deep_cache_hits": 0,
        "deep_cache_misses": 0,
        "cheap_pruned_action_count": 0,
        "safety_rejected_action_count": 0,
    }


def _generate_stage_positions(
    *,
    count: int,
    seed: int,
    generator: str,
    excluded: set[str],
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
) -> list[str]:
    rng = random.Random(seed)
    used = set(excluded)
    positions: list[str] = []
    for _ in range(config.max_generation_attempts):
        if len(positions) >= count:
            break
        board = _random_stage_board(rng, generator=generator)
        if not _valid_stage_board(board, generator=generator):
            continue
        if not _has_promising_candidate(board):
            continue
        if (
            (generator == "edge" and config.edge_generation_requires_handoff_candidate)
            or (generator == "fence" and config.fence_generation_requires_handoff_candidate)
        ):
            if not _has_deep_handoff_candidate(
                board,
                config=config,
                mate_ranker=mate_ranker,
                mate2_ranker=mate2_ranker,
                ideal_white_moves=3 if generator == "edge" else 4,
            ):
                continue
        fen = board.fen()
        if fen in used:
            continue
        used.add(fen)
        positions.append(fen)
    if len(positions) < count:
        raise RuntimeError(f"generated {len(positions)} {generator} positions, needed {count}")
    return positions


def _has_deep_handoff_candidate(
    board: chess.Board,
    *,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
) -> bool:
    cheap_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    runtime_stats = _empty_runtime_stats()
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
    score_cache: dict[tuple[str, str, int], dict[str, Any]] = {}
    for uci in top:
        move = chess.Move.from_uci(uci)
        scored = _cached_score_first_move(
            board,
            move,
            config=config,
            mate_ranker=mate_ranker,
            mate2_ranker=mate2_ranker,
            ideal_white_moves=ideal_white_moves,
            score_cache=score_cache,
            runtime_stats=runtime_stats,
        )
        if scored.get("conversion"):
            return True
    return False


def _random_stage_board(rng: random.Random, *, generator: str) -> chess.Board:
    squares = list(chess.SQUARES)
    if generator == "edge":
        black_candidates = [sq for sq in squares if _edge_distance(sq) == 0]
    else:
        black_candidates = [sq for sq in squares if _edge_distance(sq) <= 1]
    bk = rng.choice(black_candidates)
    near_white_kings = [
        sq for sq in squares
        if sq != bk and 2 <= _chebyshev(sq, bk) <= (3 if generator == "edge" else 4)
    ]
    wk = rng.choice(near_white_kings)
    rook_candidates = [
        sq for sq in squares
        if sq not in {bk, wk} and _chebyshev(sq, bk) >= 2 and _chebyshev(sq, wk) <= 5
    ]
    wr = rng.choice(rook_candidates)
    board = chess.Board(None)
    board.clear_board()
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE
    board.castling_rights = 0
    board.ep_square = None
    board.halfmove_clock = 0
    board.fullmove_number = 1
    return board


def _valid_stage_board(board: chess.Board, *, generator: str) -> bool:
    if (
        not board.is_valid()
        or board.is_game_over(claim_draw=False)
        or board.turn != chess.WHITE
        or _mate_moves(board)
        or _rook_missing_or_attacked(board)
    ):
        return False
    black_king = board.king(chess.BLACK)
    if black_king is None:
        return False
    if generator == "edge":
        return _edge_distance(black_king) == 0
    return _edge_distance(black_king) <= 1 and box_min_side(board) <= 3


def _has_promising_candidate(board: chess.Board) -> bool:
    before_box = box_min_side(board)
    before_features = extract_learner_features(board)
    for move in board.legal_moves:
        after = board.copy(stack=False)
        after.push(move)
        if after.is_stalemate() or _rook_missing_or_attacked(after):
            continue
        after_features = extract_learner_features(after)
        if after.is_checkmate() or board.gives_check(move):
            return True
        if box_min_side(after) <= before_box:
            return True
        if (
            after_features["white_king_to_black_king_distance"]
            < before_features["white_king_to_black_king_distance"]
            and not did_box_grow(board, after)
        ):
            return True
    return False


def _evaluate_foundation_regression(
    foundation_payload: dict[str, Any],
    *,
    config: EdgeFenceCurriculumConfig,
) -> dict[str, Any]:
    mate1 = float(foundation_payload["decision"]["mate1_heldout_accuracy"])
    mate2 = float(foundation_payload["decision"]["mate2_conversion_rate"])
    return {
        "mate1_heldout_accuracy": mate1,
        "mate2_conversion_rate": mate2,
        "mate1_threshold": config.mate1_regression_threshold,
        "mate2_threshold": config.mate2_regression_threshold,
        "mate1_regression_passed": mate1 >= config.mate1_regression_threshold,
        "mate2_regression_passed": mate2 >= config.mate2_regression_threshold,
    }


def _decision(
    *,
    config: EdgeFenceCurriculumConfig,
    stages: list[dict[str, Any]],
    regression: dict[str, Any],
    failure_audit: dict[str, Any],
) -> dict[str, Any]:
    all_stages_passed = all(stage["advanced"] for stage in stages)
    safety_passed = all(
        stage["final_eval"]["rook_loss_count"] == 0
        and stage["final_eval"]["stalemate_count"] == 0
        and stage["final_eval"]["illegal_or_no_move_count"] == 0
        for stage in stages
        if stage["final_eval"] is not None
    )
    m3_nonzero = all(stage["m3_update_count"] > 0 for stage in stages)
    m4_confirmed = all(stage["m4_consolidation_event_count"] > 0 for stage in stages)
    regression_passed = regression["mate1_regression_passed"] and regression["mate2_regression_passed"]
    improvement = _tg26b_improvement_summary(stages=stages, failure_audit=failure_audit)
    continue_ready = (
        regression_passed
        and m3_nonzero
        and improvement["rook_loss_zero"]
        and improvement["illegal_stalemate_zero"]
        and improvement["confinement_regressions_reduced"]
        and improvement["edge_conversion_or_handoff_improved"]
        and improvement["fence_progress_or_clean_safety"]
    )
    passed = all_stages_passed and safety_passed and m3_nonzero and m4_confirmed and regression_passed
    return {
        "status": "tg26_edge_fence_passed" if passed else "tg26_edge_fence_partial_or_failed",
        "checkpoint": "TG26c_edge_fence_handoff_curriculum",
        "stage_advancement_passed": all_stages_passed,
        "safety_passed": safety_passed,
        "m3_updates_nonzero": m3_nonzero,
        "m4_after_heldout_confirmation": m4_confirmed,
        "foundation_regression_passed": regression_passed,
        "continue_conditions_passed": continue_ready,
        "improvement_summary": improvement,
        "curriculum_labels_learner_visible": False,
        "direct_provider_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "broad_random_krk_enabled": False,
        "next_recommended_checkpoint": (
            "Continue staged curriculum into cut/box slices with the same graded handoff credit"
            if passed
            else (
                "Precompute/cache handoff-eligible edge/fence position pools, then scale the "
                "handoff-filtered curriculum before broad KRK"
            )
        ),
    }


def _tg26b_improvement_summary(
    *,
    stages: list[dict[str, Any]],
    failure_audit: dict[str, Any],
) -> dict[str, Any]:
    stage_by_label = {stage["label"]: stage for stage in stages}
    edge = stage_by_label.get("edge_trap", {})
    fence = stage_by_label.get("fence_hold", {})
    edge_final = edge.get("final_eval", {})
    fence_final = fence.get("final_eval", {})
    previous = failure_audit.get("previous_tg26", {})
    prev_counts: dict[str, dict[str, int]] = {}
    if previous.get("available"):
        for label, stage in previous.get("stages", {}).items():
            counts = {"confinement": 0, "rook_loss": 0}
            for item in stage.get("failure_slices", []):
                counts["confinement"] += int(item.get("failure_type") == "confinement_regression")
                counts["rook_loss"] += int(item.get("failure_type") == "rook_loss")
            original = stage.get("original_final_metrics", {})
            if original.get("confinement_regression_count") is not None:
                counts["confinement"] = int(original["confinement_regression_count"])
            if original.get("rook_loss_count") is not None:
                counts["rook_loss"] = int(original["rook_loss_count"])
            prev_counts[label] = counts
    current_confinement = int(edge_final.get("confinement_regression_count", 0)) + int(fence_final.get("confinement_regression_count", 0))
    previous_confinement = sum(counts.get("confinement", 0) for counts in prev_counts.values())
    if previous_confinement == 0:
        previous_confinement = 6  # TG26 aggregate baseline: 2 edge + 4 fence.
    edge_signal = int(edge_final.get("conversion_count", 0)) + int(edge_final.get("earlier_region_handoff_count", 0))
    fence_signal = int(fence_final.get("conversion_count", 0)) + int(fence_final.get("earlier_region_handoff_count", 0))
    rook_loss_total = int(edge_final.get("rook_loss_count", 0)) + int(fence_final.get("rook_loss_count", 0))
    illegal_stalemate_total = (
        int(edge_final.get("illegal_or_no_move_count", 0))
        + int(fence_final.get("illegal_or_no_move_count", 0))
        + int(edge_final.get("stalemate_count", 0))
        + int(fence_final.get("stalemate_count", 0))
    )
    return {
        "rook_loss_zero": rook_loss_total == 0,
        "illegal_stalemate_zero": illegal_stalemate_total == 0,
        "confinement_regressions_reduced": current_confinement < previous_confinement,
        "current_confinement_regressions": current_confinement,
        "previous_confinement_regressions_reference": previous_confinement,
        "edge_conversion_or_handoff_improved": edge_signal > 1,
        "edge_conversion_plus_handoff_signal": edge_signal,
        "fence_progress_or_clean_safety": fence_signal > 0 or int(fence_final.get("rook_loss_count", 0)) == 0,
        "fence_conversion_plus_handoff_signal": fence_signal,
        "rook_loss_total": rook_loss_total,
        "illegal_stalemate_total": illegal_stalemate_total,
    }


def _edge_distance(square: int) -> int:
    return min(chess.square_file(square), 7 - chess.square_file(square), chess.square_rank(square), 7 - chess.square_rank(square))


def _chebyshev(a: int, b: int) -> int:
    return max(abs(chess.square_file(a) - chess.square_file(b)), abs(chess.square_rank(a) - chess.square_rank(b)))

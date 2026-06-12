"""TG26 edge/fence curriculum continuation with graded credit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
from typing import Any, Iterable

import chess

from recon_lite_chess.training.krk_curriculum import box_min_side, did_box_grow

from .features import extract_learner_features, validate_learner_record
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
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26_edge_fence_curriculum.v0",
            "checkpoint": "TG26_edge_fence_curriculum",
            "config": asdict(self.config),
            "training_runway": {
                "uses_curriculum_as_experience_distribution": True,
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
    decision = _decision(
        config=config,
        stages=[edge_stage, fence_stage],
        regression=regression,
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
) -> dict[str, Any]:
    fen_list = tuple(fens)
    reward_sum = 0.0
    positives = 0
    negatives = 0
    for fen in fen_list:
        board = chess.Board(fen)
        move_rewards = {
            move.uci(): _cached_score_first_move(
                board,
                move,
                config=config,
                mate_ranker=mate_ranker,
                mate2_ranker=mate2_ranker,
                ideal_white_moves=ideal_white_moves,
                score_cache=score_cache,
            )["reward"]
            for move in board.legal_moves
        }
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
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    conversions = 0
    handoffs = 0
    mate1_handoffs = 0
    mate2_handoffs = 0
    rook_losses = 0
    stalemates = 0
    illegal = 0
    confinement_regressions = 0
    reward_sum = 0.0
    for fen in tuple(fens):
        board = chess.Board(fen)
        move = stage_ranker.choose(board)
        if move is None or move not in board.legal_moves:
            illegal += 1
            outcome = {"reward": -1.0, "conversion": False, "handoff": "none", "reason": "illegal_or_no_move"}
        else:
            outcome = _cached_score_first_move(
                board,
                move,
                config=config,
                mate_ranker=mate_ranker,
                mate2_ranker=mate2_ranker,
                ideal_white_moves=ideal_white_moves,
                score_cache=score_cache,
            )
        conversions += int(outcome["conversion"])
        handoffs += int(outcome["handoff"] != "none")
        mate1_handoffs += int(outcome["handoff"] == "mate_in_one")
        mate2_handoffs += int(outcome["handoff"] == "mate_in_two")
        rook_losses += int(outcome["reason"] == "rook_loss")
        stalemates += int(outcome["reason"] == "stalemate")
        confinement_regressions += int(outcome["confinement_regressed"])
        reward_sum += float(outcome["reward"])
        rows.append({
            "fen": fen,
            "selected": None if move is None else move.uci(),
            "reward": round(float(outcome["reward"]), 6),
            "conversion": bool(outcome["conversion"]),
            "handoff": outcome["handoff"],
            "reason": outcome["reason"],
            "confinement_regressed": bool(outcome["confinement_regressed"]),
        })
    total = len(rows)
    return {
        "position_count": total,
        "conversion_count": conversions,
        "conversion_rate": 0.0 if total == 0 else conversions / total,
        "earlier_region_handoff_count": handoffs,
        "earlier_region_handoff_rate": 0.0 if total == 0 else handoffs / total,
        "mate1_handoff_count": mate1_handoffs,
        "mate2_handoff_count": mate2_handoffs,
        "avg_reward": 0.0 if total == 0 else reward_sum / total,
        "rook_loss_count": rook_losses,
        "stalemate_count": stalemates,
        "illegal_or_no_move_count": illegal,
        "confinement_regression_count": confinement_regressions,
        "samples": rows[:config.max_samples],
    }


def _cached_score_first_move(
    board: chess.Board,
    move: chess.Move,
    *,
    config: EdgeFenceCurriculumConfig,
    mate_ranker: ActionRanker,
    mate2_ranker: ActionRanker,
    ideal_white_moves: int,
    score_cache: dict[tuple[str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    key = (board.fen(), move.uci(), ideal_white_moves)
    cached = score_cache.get(key)
    if cached is not None:
        return cached
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
        return _score_payload(-1.0, False, "none", "illegal_or_no_move", True)
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
        )
    if after.is_stalemate():
        return _score_payload(-0.85, False, "none", "stalemate", confinement_regressed)
    if _rook_missing_or_attacked(after):
        return _score_payload(-0.75, False, "none", "rook_loss", confinement_regressed)
    replies = list(after.legal_moves)
    if not replies:
        return _score_payload(-0.50, False, "none", "no_black_reply", confinement_regressed)
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
        return _score_payload(-0.75, False, "none", "rook_loss", True)
    mate1_move = mate_ranker.choose(after_reply)
    if mate1_move is not None and mate1_move.uci() in {move.uci() for move in _mate_moves(after_reply)}:
        return _score_payload(
            _mate_reward(actual_white_moves=2, ideal_white_moves=ideal_white_moves, config=config),
            True,
            "mate_in_one",
            "handoff_conversion",
            confinement_regressed,
        )
    mate2_move = mate2_ranker.choose(after_reply)
    if mate2_move is not None and _mate2_handoff_converts(after_reply, mate2_move, mate_ranker=mate_ranker):
        return _score_payload(
            _mate_reward(actual_white_moves=3, ideal_white_moves=ideal_white_moves, config=config),
            True,
            "mate_in_two",
            "handoff_conversion",
            confinement_regressed,
        )
    reward = _non_mate_shaping(before, after_white, after_reply, confinement_regressed=confinement_regressed)
    return _score_payload(reward, False, "none", "non_mate_shaping", confinement_regressed)


def _non_mate_shaping(
    before: chess.Board,
    after_white: chess.Board,
    after_reply: chess.Board,
    *,
    confinement_regressed: bool,
) -> float:
    before_features = extract_learner_features(before)
    after_features = extract_learner_features(after_reply)
    reward = 0.0
    if box_min_side(after_reply) < box_min_side(before):
        reward += 0.08
    elif not confinement_regressed:
        reward += 0.03
    if after_features["black_reply_mobility"] < before_features["black_reply_mobility"]:
        reward += 0.04
    if (
        after_features["white_king_to_black_king_distance"]
        < before_features["white_king_to_black_king_distance"]
        and not confinement_regressed
    ):
        reward += 0.03
    if after_features["rook_attacked_by_black"] > 0.0 or after_features["rook_present"] < 1.0:
        reward -= 0.70
    if confinement_regressed:
        reward -= 0.18
    if (
        after_features["black_king_nearest_edge_distance"] > before_features["black_king_nearest_edge_distance"]
        and box_min_side(after_reply) >= box_min_side(before)
    ):
        reward -= 0.08
    if abs(reward) < 1e-9:
        reward -= 0.03
    validate_learner_record({
        "reward": reward,
        "black_mobility_delta": after_features["black_reply_mobility"] - before_features["black_reply_mobility"],
        "king_distance_delta": (
            after_features["white_king_to_black_king_distance"]
            - before_features["white_king_to_black_king_distance"]
        ),
        "rook_safe": 1.0 - after_features["rook_attacked_by_black"],
    })
    return max(-0.60, min(0.20, reward))


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
) -> dict[str, Any]:
    return {
        "reward": float(reward),
        "conversion": bool(conversion),
        "handoff": handoff,
        "reason": reason,
        "confinement_regressed": bool(confinement_regressed),
    }


def _stage_window_passed(metrics: dict[str, Any], *, threshold: float) -> bool:
    return (
        metrics["conversion_rate"] >= threshold
        and metrics["rook_loss_count"] == 0
        and metrics["stalemate_count"] == 0
        and metrics["illegal_or_no_move_count"] == 0
    )


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
        fen = board.fen()
        if fen in used:
            continue
        used.add(fen)
        positions.append(fen)
    if len(positions) < count:
        raise RuntimeError(f"generated {len(positions)} {generator} positions, needed {count}")
    return positions


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
    passed = all_stages_passed and safety_passed and m3_nonzero and m4_confirmed and regression_passed
    return {
        "status": "tg26_edge_fence_passed" if passed else "tg26_edge_fence_partial_or_failed",
        "stage_advancement_passed": all_stages_passed,
        "safety_passed": safety_passed,
        "m3_updates_nonzero": m3_nonzero,
        "m4_after_heldout_confirmation": m4_confirmed,
        "foundation_regression_passed": regression_passed,
        "curriculum_labels_learner_visible": False,
        "direct_provider_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "broad_random_krk_enabled": False,
        "next_recommended_checkpoint": (
            "Continue staged curriculum into cut/box slices with the same graded handoff credit"
            if passed
            else "Inspect edge/fence failure slices before adding broader spawning or random KRK"
        ),
    }


def _edge_distance(square: int) -> int:
    return min(chess.square_file(square), 7 - chess.square_file(square), chess.square_rank(square), 7 - chess.square_rank(square))


def _chebyshev(a: int, b: int) -> int:
    return max(abs(chess.square_file(a) - chess.square_file(b)), abs(chess.square_rank(a) - chess.square_rank(b)))

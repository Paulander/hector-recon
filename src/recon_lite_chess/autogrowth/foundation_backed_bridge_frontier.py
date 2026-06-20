"""TG28d foundation-backed bridge frontier checkpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import random
from pathlib import Path
from typing import Any

import chess

from .foundation_curriculum import _forced_mate_in_two_first_moves, _mate_moves
from .frozen_foundation_edge_fence_reentry import (
    _black_edge_distance,
    _build_tg27b_foundation,
    _cheap_candidate_rows,
    _foundation_counts,
    _generate_edge_fence_positions,
)
from .frozen_foundation_response_cache_bridge_retrieval import (
    FrozenFoundationResponseCacheBridgeRetrievalConfig,
    _FoundationResponseCache,
    _as_tg28b_config,
    _cache_bridge_ablations,
    _cache_candidate_rows,
    _decision as _tg28c_decision,
    _evaluate_cache_bridge_layer,
    _sample_foundation_basin,
    _train_cache_bridge_layer,
)
from .frozen_foundation_bridge_pressure import _compact_foundation_sanity
from .internal_handoff_affordance_guard_audit import _mate2_cfg
from .native_quorum_mate2_chaining import _tg26u_config
from .native_quorum_materialization import _tg26t_config
from .shared_atom_utility_voting import _tg26s_config
from .shared_feature_atoms import _scheduler_equivalence


@dataclass(frozen=True)
class FoundationBackedBridgeFrontierConfig:
    seed: int = 20260628
    foundation_seed: int = 20260624
    foundation_mate1_train_count: int = 32
    foundation_mate1_heldout_count: int = 16
    foundation_mate2_train_count: int = 16
    foundation_mate2_heldout_count: int = 8
    bridge_frontier_train_count: int = 8
    bridge_frontier_heldout_count: int = 4
    generic_edge_safety_regression_count: int = 4
    basin_random_count: int = 8
    max_generation_attempts: int = 250_000
    max_cache_candidate_moves: int = 12
    max_reply_envelope_replies_per_candidate: int = 1
    max_mate2_probe_moves_per_state: int = 2
    max_edge_candidates_per_position: int = 12
    max_ablation_positions: int = 2
    max_foundation_sanity_positions: int = 2
    max_foundation_ablation_positions: int = 2
    max_ticks: int = 30
    max_samples: int = 16
    repaired_high_recall_threshold: float = 0.018
    eta_m3_edge: float = 0.06
    eta_m3_bridge: float = 0.08
    edge_terminal_min_score: float = -0.25
    bridge_terminal_min_score: float = 0.10
    materialized_quorum_min_evidence: float = -10000.0
    replay_count: int = 2
    progress_output: str = "reports/autogrowth/krk_autogrowth_tg28d_foundation_backed_bridge_frontier_progress.json"


@dataclass(frozen=True)
class FoundationBackedBridgeFrontierResult:
    config: FoundationBackedBridgeFrontierConfig
    dataset: dict[str, Any]
    foundation_sanity: dict[str, Any]
    cache: dict[str, Any]
    basin_sampling: dict[str, Any]
    bridge_training: dict[str, Any]
    evaluations: dict[str, Any]
    ablation_results: dict[str, Any]
    scheduler_equivalence: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg28d_foundation_backed_bridge_frontier.v0",
            "checkpoint": "TG28d_foundation_backed_bridge_frontier",
            "config": asdict(self.config),
            "purity_boundary": _purity_boundary(),
            "dataset": self.dataset,
            "foundation_sanity": self.foundation_sanity,
            "cache": self.cache,
            "basin_sampling": self.basin_sampling,
            "bridge_training": self.bridge_training,
            "evaluations": self.evaluations,
            "ablation_results": self.ablation_results,
            "scheduler_equivalence": self.scheduler_equivalence,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_foundation_backed_bridge_frontier(
    *,
    config: FoundationBackedBridgeFrontierConfig | None = None,
) -> FoundationBackedBridgeFrontierResult:
    cfg = config or FoundationBackedBridgeFrontierConfig()
    tg28c_cfg = _as_tg28c_config(cfg)
    foundation = _build_tg27b_foundation(_as_tg28b_config(tg28c_cfg))
    graph = foundation["graph"]
    mate1_train = foundation["mate1_train"]
    mate1_heldout = foundation["mate1_heldout"]
    mate2_train = foundation["mate2_train"]
    mate2_heldout = foundation["mate2_heldout"]
    mate2_cfg = _mate2_cfg(foundation["internal_cfg"])
    cache = _FoundationResponseCache(graph, mate2_cfg, tg28c_cfg)
    _write_progress(cfg, {"phase": "foundation_built"})

    foundation_sanity = _compact_foundation_sanity(
        graph,
        mate1_heldout,
        mate2_heldout,
        foundation["attention_cfg"],
        mate2_cfg,
        _as_tg28b_config(tg28c_cfg),
    )
    _write_progress(cfg, {
        "phase": "foundation_sanity_complete",
        "foundation_mate1_accuracy": foundation_sanity["foundation_mate1_accuracy"],
        "foundation_mate2_conversion_rate": foundation_sanity["foundation_mate2_conversion_rate"],
        "foundation_replay_stability_pass": foundation_sanity["foundation_replay_stability_pass"],
    })
    excluded = set((*mate1_train, *mate1_heldout, *mate2_train, *mate2_heldout))
    anchors = tuple(dict.fromkeys((*mate1_train, *mate1_heldout, *mate2_train, *mate2_heldout)))
    _write_progress(cfg, {
        "phase": "foundation_backed_train_generation_started",
        "requested_count": cfg.bridge_frontier_train_count,
        "max_generation_attempts": cfg.max_generation_attempts,
    })
    train_fens, train_stats = _generate_foundation_backed_frontier(
        cache,
        anchors=anchors,
        count=cfg.bridge_frontier_train_count,
        seed=cfg.seed,
        excluded=excluded,
        cfg=tg28c_cfg,
    )
    excluded.update(train_fens)
    _write_progress(cfg, {
        "phase": "foundation_backed_heldout_generation_started",
        "train_accepted_count": len(train_fens),
        "train_attempts": train_stats["attempts"],
        "requested_count": cfg.bridge_frontier_heldout_count,
        "max_generation_attempts": cfg.max_generation_attempts,
    })
    heldout_fens, heldout_stats = _generate_foundation_backed_frontier(
        cache,
        anchors=anchors,
        count=cfg.bridge_frontier_heldout_count,
        seed=cfg.seed + 1,
        excluded=excluded,
        cfg=tg28c_cfg,
    )
    excluded.update(heldout_fens)
    generic_fens = _generate_edge_fence_positions(
        count=cfg.generic_edge_safety_regression_count,
        seed=cfg.seed + 2,
        excluded=excluded,
        cfg=_as_tg28b_config(tg28c_cfg),
    )
    _write_progress(cfg, {
        "phase": "foundation_backed_dataset_complete",
        "bridge_frontier_train_count": len(train_fens),
        "bridge_frontier_heldout_count": len(heldout_fens),
        "bridge_frontier_generation_attempts": train_stats["attempts"] + heldout_stats["attempts"],
        "all_reply_bridge_count": train_stats["all_reply_bridge_count"] + heldout_stats["all_reply_bridge_count"],
        "partial_reply_bridge_count": train_stats["partial_reply_bridge_count"] + heldout_stats["partial_reply_bridge_count"],
    })

    basin = _sample_foundation_basin(
        cache,
        mate1_train=mate1_train,
        mate1_heldout=mate1_heldout,
        mate2_train=mate2_train,
        mate2_heldout=mate2_heldout,
        bridge_train=train_fens,
        bridge_heldout=heldout_fens,
        generic_heldout=generic_fens,
        cfg=tg28c_cfg,
    )
    equivalence = cache.live_equivalence_audit(max_samples=min(8, cfg.max_samples))
    _write_progress(cfg, {
        "phase": "cache_basin_complete",
        "foundation_cache_state_count": cache.state_count,
        "foundation_positive_state_count": basin["foundation_positive_state_count"],
        "foundation_cache_live_mismatch_count": equivalence["foundation_cache_live_mismatch_count"],
    })

    foundation_before_training = _foundation_counts(graph)
    edge_weights: dict[str, float] = {}
    bridge_weights: dict[str, float] = {}
    training = _train_cache_bridge_layer(cache, train_fens, tg28c_cfg, edge_weights, bridge_weights)
    foundation_after_training = _foundation_counts(graph)
    _write_progress(cfg, {
        "phase": "bridge_training_complete",
        "edge_only_m3_update_count": training["edge_only_m3_update_count"],
        "bridge_terminal_m3_update_count": training["bridge_terminal_m3_update_count"],
        "foundation_m3_delta": foundation_after_training["m3"] - foundation_before_training["m3"],
    })

    foundation_before_eval = _foundation_counts(graph)
    baseline = _evaluate_cache_bridge_layer(graph, cache, heldout_fens, tg28c_cfg, edge_weights, {}, cache_retrieval_enabled=False)
    frontier_eval = _evaluate_cache_bridge_layer(graph, cache, heldout_fens, tg28c_cfg, edge_weights, bridge_weights)
    generic_eval = _evaluate_cache_bridge_layer(graph, cache, generic_fens, tg28c_cfg, edge_weights, bridge_weights)
    ablations = _cache_bridge_ablations(graph, cache, heldout_fens, tg28c_cfg, edge_weights, bridge_weights)
    foundation_after_eval = _foundation_counts(graph)
    scheduler_equivalence = (
        {"mismatch_count": 0, "skipped": True, "skip_reason": "max_ablation_positions_zero_smoke_path"}
        if cfg.max_ablation_positions <= 0
        else _scheduler_equivalence(_tg26s_config(_tg26t_config(_tg26u_config(mate2_cfg))), mate1_train, mate1_heldout)
    )
    generation = _merge_generation_stats(train_stats, heldout_stats)
    decision = _decision(
        cfg,
        tg28c_cfg=tg28c_cfg,
        foundation_sanity=foundation_sanity,
        cache=cache,
        equivalence=equivalence,
        basin=basin,
        generation=generation,
        baseline=baseline,
        frontier_eval=frontier_eval,
        generic_eval=generic_eval,
        ablations=ablations,
        scheduler_equivalence=scheduler_equivalence,
        training=training,
        foundation_before_training=foundation_before_training,
        foundation_after_training=foundation_after_training,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
    )
    _write_progress(cfg, {"phase": "complete", "decision": {
        "checkpoint_pass": decision["checkpoint_pass"],
        "selected_move_count": decision["selected_move_count"],
        "bridge_candidate_generated_count": decision["bridge_candidate_generated_count"],
    }})
    return FoundationBackedBridgeFrontierResult(
        config=cfg,
        dataset={
            "source": "foundation-backed bridge/frontier positions generated by frozen-native cache response, labels trainer-side only",
            "bridge_frontier_train_count": len(train_fens),
            "bridge_frontier_heldout_count": len(heldout_fens),
            "generic_edge_safety_regression_count": len(generic_fens),
            "train_generation": train_stats,
            "heldout_generation": heldout_stats,
            "bridge_frontier_train_fens": list(train_fens)[: cfg.max_samples],
            "bridge_frontier_heldout_fens": list(heldout_fens)[: cfg.max_samples],
            "generic_edge_safety_fens": list(generic_fens)[: cfg.max_samples],
            "stage_labels_learner_visible": False,
            "edge_fence_labels_learner_visible": False,
            "bridge_labels_learner_visible": False,
        },
        foundation_sanity=foundation_sanity,
        cache=cache.to_dict(max_entries=cfg.max_samples),
        basin_sampling=basin,
        bridge_training=training,
        evaluations={
            "tg28c_baseline_current_bridge_heldout": baseline,
            "foundation_backed_bridge_frontier": frontier_eval,
            "generic_edge_safety_regression": generic_eval,
        },
        ablation_results=ablations,
        scheduler_equivalence=scheduler_equivalence,
        decision=decision,
    )


def _generate_foundation_backed_frontier(
    cache: _FoundationResponseCache,
    *,
    anchors: tuple[str, ...],
    count: int,
    seed: int,
    excluded: set[str],
    cfg: FrozenFoundationResponseCacheBridgeRetrievalConfig,
) -> tuple[tuple[str, ...], dict[str, Any]]:
    rng = random.Random(seed)
    fens: list[str] = []
    seed_pool_cap = max(4, count * 2)
    seed_boards = _foundation_backed_seed_boards(rng, anchors, max_boards=seed_pool_cap)
    seed_index = 0
    attempts = 0
    seed_pool_attempts = 0
    random_fallback_attempts = 0
    no_bridge = 0
    invalid = 0
    duplicate = 0
    all_reply = 0
    partial = 0
    any_reply = 0
    samples = []
    while len(fens) < count and attempts < cfg.max_generation_attempts:
        attempts += 1
        if seed_index < len(seed_boards):
            board = seed_boards[seed_index]
            seed_index += 1
            seed_pool_attempts += 1
        else:
            board = _anchor_predecessor_board(rng, anchors)
            random_fallback_attempts += 1
        if board is None:
            board = _random_edge_board(rng)
        if board is None:
            invalid += 1
            continue
        fen = board.fen()
        if fen in excluded or fen in fens:
            duplicate += 1
            continue
        if _mate_moves(board) or _forced_mate_in_two_first_moves(board):
            continue
        rows = _foundation_backed_candidate_rows(cache, board, cfg)
        bridge_rows = [row for row in rows if row["reply_envelope_foundation_reachable"]]
        if not bridge_rows:
            no_bridge += 1
            continue
        best = max(bridge_rows, key=lambda row: (row["reply_envelope_foundation_coverage_rate"], row["cheap_score"], row["move"]))
        if best["foundation_handoff_conversion"]:
            all_reply += 1
        elif best["reply_envelope_foundation_reachable"]:
            partial += 1
        any_reply += 1
        fens.append(fen)
        if len(samples) < cfg.max_samples:
            samples.append({
                "fen": fen,
                "best_bridge_move": best["move"],
                "reply_total": best["reply_total"],
                "reply_solved": best["reply_solved"],
                "reply_envelope_success_rate": best["reply_envelope_foundation_coverage_rate"],
            })
    if len(fens) < count:
        raise RuntimeError(f"could only generate {len(fens)} foundation-backed bridge positions after {attempts} attempts")
    return tuple(fens), {
        "attempts": attempts,
        "accepted_count": len(fens),
        "invalid_count": invalid,
        "duplicate_count": duplicate,
        "no_bridge_count": no_bridge,
        "all_reply_bridge_count": all_reply,
        "partial_reply_bridge_count": partial,
        "any_reply_bridge_count": any_reply,
        "seed_pool_size": len(seed_boards),
        "seed_pool_cap": seed_pool_cap,
        "seed_pool_attempts": seed_pool_attempts,
        "seed_pool_exhausted": seed_index >= len(seed_boards),
        "random_fallback_attempts": random_fallback_attempts,
        "generation_timeout_count": 0,
        "average_generation_attempts_per_bridge_position": attempts / max(1, len(fens)),
        "samples": samples,
    }


def _foundation_backed_seed_boards(
    rng: random.Random,
    anchors: tuple[str, ...],
    *,
    max_boards: int,
) -> list[chess.Board]:
    boards: list[chess.Board] = []
    seen: set[str] = set()
    anchor_fens = list(anchors)
    rng.shuffle(anchor_fens)
    for fen in anchor_fens:
        if len(boards) >= max_boards:
            break
        anchor = chess.Board(fen)
        if anchor.turn != chess.WHITE or anchor.is_game_over():
            continue
        black_to_move_states = _reverse_black_reply_states(anchor)
        rng.shuffle(black_to_move_states)
        for after_bridge in black_to_move_states[:2]:
            if len(boards) >= max_boards:
                break
            predecessors = _reverse_white_candidate_states(after_bridge)
            rng.shuffle(predecessors)
            for predecessor in predecessors[:4]:
                if len(boards) >= max_boards:
                    break
                if not (predecessor.is_valid() and not predecessor.is_check() and not predecessor.is_game_over()):
                    continue
                predecessor_fen = predecessor.fen()
                if predecessor_fen in seen:
                    continue
                seen.add(predecessor_fen)
                boards.append(predecessor)
    rng.shuffle(boards)
    return boards


def _anchor_predecessor_board(rng: random.Random, anchors: tuple[str, ...]) -> chess.Board | None:
    if not anchors:
        return None
    anchor = chess.Board(rng.choice(anchors))
    if anchor.turn != chess.WHITE or anchor.is_game_over():
        return None
    black_to_move_states = _reverse_black_reply_states(anchor)
    rng.shuffle(black_to_move_states)
    for after_bridge in black_to_move_states[:8]:
        predecessors = _reverse_white_candidate_states(after_bridge)
        rng.shuffle(predecessors)
        for predecessor in predecessors[:8]:
            if predecessor.is_valid() and not predecessor.is_check() and not predecessor.is_game_over():
                return predecessor
    return None


def _reverse_black_reply_states(anchor: chess.Board) -> list[chess.Board]:
    bk = anchor.king(chess.BLACK)
    if bk is None:
        return []
    states = []
    for from_sq in chess.SquareSet(chess.BB_KING_ATTACKS[bk]):
        if anchor.piece_at(from_sq) is not None:
            continue
        candidate = anchor.copy(stack=False)
        candidate.remove_piece_at(bk)
        candidate.set_piece_at(from_sq, chess.Piece(chess.KING, chess.BLACK))
        candidate.turn = chess.BLACK
        candidate.clear_stack()
        reply = chess.Move(from_sq, bk)
        if candidate.is_valid() and reply in candidate.legal_moves:
            after = candidate.copy(stack=False)
            after.push(reply)
            if _same_position(after, anchor):
                states.append(candidate)
    return states


def _reverse_white_candidate_states(after_bridge: chess.Board) -> list[chess.Board]:
    states = []
    white_targets = [
        square
        for square, piece in after_bridge.piece_map().items()
        if piece.color == chess.WHITE and piece.piece_type in {chess.KING, chess.ROOK}
    ]
    for to_sq in white_targets:
        piece = after_bridge.piece_at(to_sq)
        if piece is None:
            continue
        from_squares = (
            list(chess.SquareSet(chess.BB_KING_ATTACKS[to_sq]))
            if piece.piece_type == chess.KING
            else _rook_reverse_from_squares(to_sq)
        )
        for from_sq in from_squares:
            if from_sq == to_sq or after_bridge.piece_at(from_sq) is not None:
                continue
            predecessor = after_bridge.copy(stack=False)
            predecessor.remove_piece_at(to_sq)
            predecessor.set_piece_at(from_sq, piece)
            predecessor.turn = chess.WHITE
            predecessor.clear_stack()
            move = chess.Move(from_sq, to_sq)
            if predecessor.is_valid() and move in predecessor.legal_moves:
                after = predecessor.copy(stack=False)
                after.push(move)
                if _same_position(after, after_bridge):
                    states.append(predecessor)
    return states


def _rook_reverse_from_squares(to_sq: int) -> list[int]:
    f = chess.square_file(to_sq)
    r = chess.square_rank(to_sq)
    return [
        sq
        for sq in range(64)
        if sq != to_sq and (chess.square_file(sq) == f or chess.square_rank(sq) == r)
    ]


def _same_position(left: chess.Board, right: chess.Board) -> bool:
    return left.board_fen() == right.board_fen() and left.turn == right.turn


def _foundation_backed_candidate_rows(cache, board, cfg):
    rows = _cache_candidate_rows(cache, board, cfg, {}, {}, cache_retrieval_enabled=True)
    return [row for row in rows if row["safety_ok"] and row["after_features"]["stalemate_after"] == 0.0]


def _random_edge_board(rng: random.Random) -> chess.Board | None:
    board = chess.Board.empty()
    board.turn = chess.WHITE
    wk = rng.randrange(64)
    wr = rng.randrange(64)
    bk = rng.randrange(64)
    if len({wk, wr, bk}) != 3:
        return None
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    board.clear_stack()
    if not board.is_valid() or board.is_check() or board.is_game_over() or _black_edge_distance(board) > 3:
        return None
    return board


def _decision(
    cfg,
    *,
    tg28c_cfg,
    foundation_sanity,
    cache,
    equivalence,
    basin,
    generation,
    baseline,
    frontier_eval,
    generic_eval,
    ablations,
    scheduler_equivalence,
    training,
    foundation_before_training,
    foundation_after_training,
    foundation_before_eval,
    foundation_after_eval,
) -> dict[str, Any]:
    base = _tg28c_decision(
        tg28c_cfg,
        foundation_sanity=foundation_sanity,
        cache=cache,
        equivalence=equivalence,
        basin=basin,
        baseline=baseline,
        retrieval=frontier_eval,
        generic_eval=generic_eval,
        ablations=ablations,
        scheduler_equivalence=scheduler_equivalence,
        training=training,
        foundation_before_training=foundation_before_training,
        foundation_after_training=foundation_after_training,
        foundation_before_eval=foundation_before_eval,
        foundation_after_eval=foundation_after_eval,
    )
    selected_bridge = (
        frontier_eval["selected_move_count"] > 0
        and frontier_eval["reply_envelope_foundation_reachable_count"] > 0
    )
    checkpoint_pass = (
        base["foundation_cache_live_mismatch_count"] == 0
        and base["foundation_m3_updates_during_bridge_training"] == 0
        and base["foundation_m3_updates_during_eval"] == 0
        and generation["bridge_frontier_generated_count"] >= cfg.bridge_frontier_train_count + cfg.bridge_frontier_heldout_count
        and frontier_eval["bridge_candidate_generated_count"] > 0
        and selected_bridge
        and frontier_eval["rook_blunder_count"] == 0
        and generic_eval["rook_blunder_count"] == 0
    )
    base.update({
        "checkpoint_pass": checkpoint_pass,
        "checkpoint_interpretation": (
            "foundation_backed_bridge_selected_graph_mediated_handoff"
            if checkpoint_pass
            else "foundation_backed_candidates_generated_but_selection_failed"
        ),
        "foundation_positive_state_count": basin["foundation_positive_state_count"],
        "bridge_frontier_generation_attempts": generation["bridge_frontier_generation_attempts"],
        "bridge_frontier_generated_count": generation["bridge_frontier_generated_count"],
        "all_reply_bridge_count": generation["all_reply_bridge_count"],
        "partial_reply_bridge_count": generation["partial_reply_bridge_count"],
        "any_reply_bridge_count": generation["any_reply_bridge_count"],
        "no_bridge_count": generation["no_bridge_count"],
        "generation_timeout_count": generation["generation_timeout_count"],
        "average_generation_attempts_per_bridge_position": generation["average_generation_attempts_per_bridge_position"],
        "bridge_frontier_train_count": cfg.bridge_frontier_train_count,
        "bridge_frontier_heldout_count": cfg.bridge_frontier_heldout_count,
        "safe_candidate_count": frontier_eval["safety_filtered_candidate_count"],
        "all_reply_foundation_bridge_success_count": sum(
            1
            for sample in frontier_eval["samples"]
            if sample["selected"] is not None and sample["selected"]["foundation_handoff_conversion"]
        ),
        "partial_reply_foundation_bridge_success_count": frontier_eval["reply_envelope_foundation_reachable_count"],
        "purity_boundary": _purity_boundary(),
    })
    return base


def _merge_generation_stats(train: dict[str, Any], heldout: dict[str, Any]) -> dict[str, Any]:
    generated = train["accepted_count"] + heldout["accepted_count"]
    attempts = train["attempts"] + heldout["attempts"]
    return {
        "bridge_frontier_generation_attempts": attempts,
        "bridge_frontier_generated_count": generated,
        "all_reply_bridge_count": train["all_reply_bridge_count"] + heldout["all_reply_bridge_count"],
        "partial_reply_bridge_count": train["partial_reply_bridge_count"] + heldout["partial_reply_bridge_count"],
        "any_reply_bridge_count": train["any_reply_bridge_count"] + heldout["any_reply_bridge_count"],
        "no_bridge_count": train["no_bridge_count"] + heldout["no_bridge_count"],
        "generation_timeout_count": train["generation_timeout_count"] + heldout["generation_timeout_count"],
        "average_generation_attempts_per_bridge_position": attempts / max(1, generated),
    }


def _as_tg28c_config(cfg: FoundationBackedBridgeFrontierConfig) -> FrozenFoundationResponseCacheBridgeRetrievalConfig:
    return FrozenFoundationResponseCacheBridgeRetrievalConfig(
        seed=cfg.seed,
        foundation_seed=cfg.foundation_seed,
        foundation_mate1_train_count=cfg.foundation_mate1_train_count,
        foundation_mate1_heldout_count=cfg.foundation_mate1_heldout_count,
        foundation_mate2_train_count=cfg.foundation_mate2_train_count,
        foundation_mate2_heldout_count=cfg.foundation_mate2_heldout_count,
        bridge_train_count=cfg.bridge_frontier_train_count,
        bridge_heldout_count=cfg.bridge_frontier_heldout_count,
        generic_edge_safety_heldout_count=cfg.generic_edge_safety_regression_count,
        basin_random_count=cfg.basin_random_count,
        max_generation_attempts=cfg.max_generation_attempts,
        max_cache_candidate_moves=cfg.max_cache_candidate_moves,
        max_reply_envelope_replies_per_candidate=cfg.max_reply_envelope_replies_per_candidate,
        max_mate2_probe_moves_per_state=cfg.max_mate2_probe_moves_per_state,
        max_edge_candidates_per_position=cfg.max_edge_candidates_per_position,
        max_ablation_positions=cfg.max_ablation_positions,
        max_foundation_sanity_positions=cfg.max_foundation_sanity_positions,
        max_foundation_ablation_positions=cfg.max_foundation_ablation_positions,
        max_ticks=cfg.max_ticks,
        max_samples=cfg.max_samples,
        repaired_high_recall_threshold=cfg.repaired_high_recall_threshold,
        eta_m3_edge=cfg.eta_m3_edge,
        eta_m3_bridge=cfg.eta_m3_bridge,
        edge_terminal_min_score=cfg.edge_terminal_min_score,
        bridge_terminal_min_score=cfg.bridge_terminal_min_score,
        materialized_quorum_min_evidence=cfg.materialized_quorum_min_evidence,
        replay_count=cfg.replay_count,
        progress_output=cfg.progress_output,
    )


def _write_progress(cfg: FoundationBackedBridgeFrontierConfig, payload: dict[str, Any]) -> None:
    path = Path(cfg.progress_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _purity_boundary() -> dict[str, Any]:
    return {
        "checkpoint": "TG28d",
        "native_recon_graph_execution": True,
        "foundation_frozen": True,
        "foundation_cache_used_as_memoized_graph_response": True,
        "foundation_cache_used_as_provider": False,
        "foundation_backed_generation_trainer_side_only": True,
        "bridge_candidate_choice_mediated_by_native_quorum": True,
        "runtime_tablebase_or_dtm_move_source": False,
        "action_ranker_used_for_runtime": False,
        "direct_provider_override": False,
        "stage_labels_learner_visible": False,
        "edge_fence_labels_learner_visible": False,
        "bridge_labels_learner_visible": False,
    }

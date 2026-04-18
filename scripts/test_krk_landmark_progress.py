"""Evaluate compiled KRK topology against explicit landmark rewards.

This is the Stage-2+ companion to test_stage1_backchain.py. It does not prove
full KRK conversion; it measures whether the currently selected stage-labelled
actuators improve a named landmark reward such as edge pressure, fence gain, box
shrinkage, opposition/tempo, or the blended full_krk score.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Optional

import chess

from recon_lite.engine import ReConEngine
from recon_lite.graph import Graph, NodeState
from recon_lite_chess.graph.builder import build_graph_from_topology
from recon_lite_chess.training.krk_landmarks import (
    LANDMARK_LABELS,
    KRK_LANDMARK_STAGE_SPECS,
    select_stage_position,
    worst_reply_reward,
)


def generate_random_krk_position(rng: random.Random) -> chess.Board:
    """Generate a legal White-to-move KRK position with no initial check."""
    squares = list(chess.SQUARES)
    while True:
        wk, bk, wr = rng.sample(squares, 3)
        board = chess.Board(None)
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
        board.turn = chess.WHITE
        if chess.square_distance(wk, bk) <= 1:
            continue
        if not board.is_valid() or board.is_check():
            continue
        return board


def source_stage_names_for_label(label: str) -> tuple[str, ...]:
    for spec in KRK_LANDMARK_STAGE_SPECS:
        if spec.label == label:
            return spec.source_stage_names
    return ("Full_KRK",)


def choose_move_with_engine(
    graph: Graph,
    engine: ReConEngine,
    board: chess.Board,
    max_ticks: int = 200,
    stage_filter: Optional[int] = None,
) -> Optional[str]:
    env = {
        "board": board,
        "chosen_move": None,
        "suggested_move": None,
        "blackboard": {"stage_filter": stage_filter} if stage_filter is not None else {},
    }

    engine.reset_states()
    root_id = "krk_entry" if "krk_entry" in graph.nodes else None
    if root_id is None:
        for nid, node in graph.nodes.items():
            if node.ntype.name == "SCRIPT" and graph.parent_of(nid) is None:
                root_id = nid
                break
    if root_id:
        graph.nodes[root_id].state = NodeState.REQUESTED

    ticks = 0
    while ticks < max_ticks and env.get("chosen_move") is None:
        ticks += 1
        engine.step(env)
    return env.get("chosen_move") or env.get("suggested_move")


def oracle_best_reward(board: chess.Board, label: str, lookahead_black: bool) -> float:
    best = -float("inf")
    for move in board.legal_moves:
        reward = worst_reply_reward(board, move, label, use_black_reply=lookahead_black)
        if reward > best:
            best = reward
    return best


def choose_black_reply(
    rng: random.Random,
    board: chess.Board,
    label: str,
    policy: str,
) -> chess.Move | None:
    replies = list(board.legal_moves)
    if not replies:
        return None
    if policy == "random":
        return rng.choice(replies)

    # Adversarial Black chooses the reply that gives White the worst next
    # one-ply landmark opportunity. This is intentionally cheap, not tablebase.
    scored = []
    for reply in replies:
        b2 = board.copy()
        b2.push(reply)
        scored.append((oracle_best_reward(b2, label, lookahead_black=False), reply))
    return min(scored, key=lambda item: item[0])[1]


def play_to_mate(
    graph: Graph,
    engine: ReConEngine,
    board: chess.Board,
    rng: random.Random,
    label: str,
    stage_filter: Optional[int],
    max_plies: int,
    black_policy: str,
) -> dict:
    """Run a simple KRK playout using the compiled topology for White moves."""
    b = board.copy()
    for ply in range(max_plies):
        if b.is_checkmate():
            return {"result": "mate", "plies": ply}
        if b.is_stalemate() or b.is_insufficient_material():
            return {"result": "draw", "plies": ply}

        if b.turn == chess.WHITE:
            move_uci = choose_move_with_engine(graph, engine, b, stage_filter=stage_filter)
            if not move_uci:
                return {"result": "no_move", "plies": ply}
            try:
                move = chess.Move.from_uci(move_uci)
            except ValueError:
                return {"result": "illegal_move", "plies": ply}
            if move not in b.legal_moves:
                return {"result": "illegal_move", "plies": ply}
            b.push(move)
        else:
            reply = choose_black_reply(rng, b, label, black_policy)
            if reply is None:
                return {"result": "no_black_reply", "plies": ply}
            b.push(reply)

    return {"result": "max_plies", "plies": max_plies}


def select_eval_position(
    rng: random.Random,
    label: str,
    mode: str,
    source_stage_names: tuple[str, ...],
) -> chess.Board:
    if mode == "random":
        return generate_random_krk_position(rng)
    if mode == "hybrid" and rng.random() < 0.5:
        return generate_random_krk_position(rng)
    try:
        board = select_stage_position(source_stage_names)
        if board.turn != chess.WHITE or not board.is_valid() or board.is_game_over():
            raise ValueError("unsuitable curriculum position")
        return board
    except Exception:
        return generate_random_krk_position(rng)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate KRK landmark reward progress")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--label", choices=LANDMARK_LABELS, default="edge_trap")
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--stage-filter", type=int, default=None)
    parser.add_argument("--eps", type=float, default=1e-3)
    parser.add_argument("--position-mode", choices=["curriculum", "random", "hybrid"], default="curriculum")
    parser.add_argument("--source-stage-names", type=str, default=None,
                        help="Comma-separated override for curriculum source stages")
    parser.add_argument("--lookahead-black", action="store_true", default=True)
    parser.add_argument("--no-lookahead-black", action="store_false", dest="lookahead_black")
    parser.add_argument("--playout-max-plies", type=int, default=0,
                        help="If >0, also run full KRK playouts up to this ply limit")
    parser.add_argument("--black-policy", choices=["random", "adversarial"], default="adversarial")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    random.seed(args.seed)
    source_names = (
        tuple(name.strip() for name in args.source_stage_names.split(",") if name.strip())
        if args.source_stage_names
        else source_stage_names_for_label(args.label)
    )

    graph = build_graph_from_topology(args.topology)
    engine = ReConEngine(graph)

    stats = {
        "total": 0,
        "no_move": 0,
        "improved": 0,
        "flat": 0,
        "worsened": 0,
        "optimal": 0,
        "avg_reward": 0.0,
        "avg_oracle_reward": 0.0,
        "playouts": {},
    }

    for i in range(args.samples):
        board = select_eval_position(rng, args.label, args.position_mode, source_names)
        move_uci = choose_move_with_engine(graph, engine, board, stage_filter=args.stage_filter)
        best_reward = oracle_best_reward(board, args.label, args.lookahead_black)

        stats["total"] += 1
        stats["avg_oracle_reward"] += best_reward
        if not move_uci:
            stats["no_move"] += 1
            continue
        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError:
            stats["no_move"] += 1
            continue
        if move not in board.legal_moves:
            stats["no_move"] += 1
            continue

        reward = worst_reply_reward(board, move, args.label, use_black_reply=args.lookahead_black)
        stats["avg_reward"] += reward
        if reward > args.eps:
            stats["improved"] += 1
        elif reward < -args.eps:
            stats["worsened"] += 1
        else:
            stats["flat"] += 1
        if reward >= best_reward - args.eps:
            stats["optimal"] += 1

        if (i + 1) % 10 == 0:
            print(f"{i + 1:4d}/{args.samples}: improved={stats['improved']} optimal={stats['optimal']}")

        if args.playout_max_plies > 0:
            result = play_to_mate(
                graph,
                engine,
                board,
                rng,
                args.label,
                args.stage_filter,
                args.playout_max_plies,
                args.black_policy,
            )
            key = result["result"]
            stats["playouts"][key] = stats["playouts"].get(key, 0) + 1

    if stats["total"]:
        stats["avg_reward"] /= stats["total"]
        stats["avg_oracle_reward"] /= stats["total"]

    print("\nKRK Landmark Progress Evaluation")
    print("-" * 60)
    print(f"Label: {args.label}")
    print(f"Source stages: {', '.join(source_names)}")
    print(f"Total evaluated: {stats['total']}")
    print(f"No move: {stats['no_move']}")
    print(f"Improved: {stats['improved']} ({stats['improved']/stats['total']*100:.1f}%)")
    print(f"Flat:     {stats['flat']} ({stats['flat']/stats['total']*100:.1f}%)")
    print(f"Worsened: {stats['worsened']} ({stats['worsened']/stats['total']*100:.1f}%)")
    print(f"Optimal:  {stats['optimal']} ({stats['optimal']/stats['total']*100:.1f}%)")
    print(f"Avg chosen reward: {stats['avg_reward']:.4f}")
    print(f"Avg oracle reward: {stats['avg_oracle_reward']:.4f}")
    if args.playout_max_plies > 0:
        print(f"Playout results ({args.black_policy} Black, max {args.playout_max_plies} plies): {stats['playouts']}")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

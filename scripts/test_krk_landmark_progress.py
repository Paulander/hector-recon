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
    if label == "edge_trap":
        return ("Edge_Trap_Close", "Edge_Trap_Enemy_Between", "Edge_Trap_Wrong_Tempo")
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


def evaluate_landmark_progress(
    topology: Path,
    *,
    label: str = "edge_trap",
    samples: int = 100,
    seed: int = 7,
    stage_filter: int | None = None,
    eps: float = 1e-3,
    position_mode: str = "curriculum",
    source_stage_names: tuple[str, ...] | None = None,
    lookahead_black: bool = True,
    playout_max_plies: int = 0,
    black_policy: str = "adversarial",
    verbose: bool = True,
) -> dict:
    rng = random.Random(seed)
    random.seed(seed)
    source_names = (
        source_stage_names
        if source_stage_names
        else source_stage_names_for_label(label)
    )

    graph = build_graph_from_topology(topology)
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

    for i in range(samples):
        board = select_eval_position(rng, label, position_mode, source_names)
        move_uci = choose_move_with_engine(graph, engine, board, stage_filter=stage_filter)
        best_reward = oracle_best_reward(board, label, lookahead_black)

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

        reward = worst_reply_reward(board, move, label, use_black_reply=lookahead_black)
        stats["avg_reward"] += reward
        if reward > eps:
            stats["improved"] += 1
        elif reward < -eps:
            stats["worsened"] += 1
        else:
            stats["flat"] += 1
        if reward >= best_reward - eps:
            stats["optimal"] += 1

        if verbose and (i + 1) % 10 == 0:
            print(f"{i + 1:4d}/{samples}: improved={stats['improved']} optimal={stats['optimal']}")

        if playout_max_plies > 0:
            result = play_to_mate(
                graph,
                engine,
                board,
                rng,
                label,
                stage_filter,
                playout_max_plies,
                black_policy,
            )
            key = result["result"]
            stats["playouts"][key] = stats["playouts"].get(key, 0) + 1

    if stats["total"]:
        stats["avg_reward"] /= stats["total"]
        stats["avg_oracle_reward"] /= stats["total"]

    stats["label"] = label
    stats["source_stage_names"] = list(source_names)
    return stats


def print_landmark_results(stats: dict, *, black_policy: str = "adversarial", playout_max_plies: int = 0) -> None:
    print("\nKRK Landmark Progress Evaluation")
    print("-" * 60)
    print(f"Label: {stats.get('label', '')}")
    print(f"Source stages: {', '.join(stats.get('source_stage_names', []))}")
    print(f"Total evaluated: {stats['total']}")
    print(f"No move: {stats['no_move']}")
    print(f"Improved: {stats['improved']} ({stats['improved']/stats['total']*100:.1f}%)")
    print(f"Flat:     {stats['flat']} ({stats['flat']/stats['total']*100:.1f}%)")
    print(f"Worsened: {stats['worsened']} ({stats['worsened']/stats['total']*100:.1f}%)")
    print(f"Optimal:  {stats['optimal']} ({stats['optimal']/stats['total']*100:.1f}%)")
    print(f"Avg chosen reward: {stats['avg_reward']:.4f}")
    print(f"Avg oracle reward: {stats['avg_oracle_reward']:.4f}")
    if playout_max_plies > 0:
        print(f"Playout results ({black_policy} Black, max {playout_max_plies} plies): {stats['playouts']}")
    print(json.dumps(stats, indent=2))


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
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args()

    source_names = (
        tuple(name.strip() for name in args.source_stage_names.split(",") if name.strip())
        if args.source_stage_names
        else None
    )
    stats = evaluate_landmark_progress(
        args.topology,
        label=args.label,
        samples=args.samples,
        seed=args.seed,
        stage_filter=args.stage_filter,
        eps=args.eps,
        position_mode=args.position_mode,
        source_stage_names=source_names,
        lookahead_black=args.lookahead_black,
        playout_max_plies=args.playout_max_plies,
        black_policy=args.black_policy,
        verbose=True,
    )
    print_landmark_results(stats, black_policy=args.black_policy, playout_max_plies=args.playout_max_plies)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

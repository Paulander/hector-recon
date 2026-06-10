#!/usr/bin/env python3
"""Build non-causal DTM-guided Stage 7 post-box continuation trajectories.

The first-move seed is not enough when the runtime provider can select a good
first move and still fail later. This tool emits multi-ply KRK continuation
examples from the unresolved post-box states:

* White follows shortest-DTM winning moves.
* Black follows adversarial longest-DTM replies within the won table.

The output is offline training evidence only. Runtime policies must not read
DTM/tablebase values, state hashes, or this trajectory file as a controller.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_krk_dtm_oracle import _state_from_board, build_krk_dtm
from recon_lite_chess.krk_baseline_nodes import krk_move_shape_audit


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _dtm_for_board(board: chess.Board, index: dict[Any, int], dtm: list[int]) -> int:
    state = _state_from_board(board)
    if state is None or state not in index:
        return -1
    return int(dtm[index[state]])


def _move_dtm(board: chess.Board, move: chess.Move, index: dict[Any, int], dtm: list[int]) -> int:
    child = board.copy(stack=False)
    child.push(move)
    return _dtm_for_board(child, index, dtm)


def _choose_dtm_move(board: chess.Board, index: dict[Any, int], dtm: list[int]) -> tuple[chess.Move | None, int]:
    moves = []
    for move in board.legal_moves:
        child_dtm = _move_dtm(board, move, index, dtm)
        if child_dtm < 0:
            continue
        moves.append((child_dtm, move))
    if not moves:
        return None, -1
    if board.turn == chess.WHITE:
        child_dtm, move = min(moves, key=lambda item: (item[0], item[1].uci()))
    else:
        child_dtm, move = max(moves, key=lambda item: (item[0], item[1].uci()))
    return move, int(child_dtm)


def _white_training_step(
    board: chess.Board,
    move: chess.Move,
    child_dtm: int,
    ply_index: int,
    index: dict[Any, int],
    dtm: list[int],
) -> dict[str, Any]:
    audit = krk_move_shape_audit(board, move, {}, include_worst_reply=False)
    legal_labels: list[dict[str, Any]] = []
    legal_child_dtms = {
        legal_move.uci(): _move_dtm(board, legal_move, index, dtm)
        for legal_move in board.legal_moves
    }
    winning_dtms = [value for value in legal_child_dtms.values() if value >= 0]
    best_child_dtm = min(winning_dtms) if winning_dtms else -1
    for legal_move in sorted(board.legal_moves, key=lambda item: item.uci()):
        legal_audit = krk_move_shape_audit(board, legal_move, {}, include_worst_reply=False)
        legal_child_dtm = legal_child_dtms[legal_move.uci()]
        piece = board.piece_at(legal_move.from_square)
        from_file = chess.square_file(legal_move.from_square)
        from_rank = chess.square_rank(legal_move.from_square)
        to_file = chess.square_file(legal_move.to_square)
        to_rank = chess.square_rank(legal_move.to_square)
        df = to_file - from_file
        dr = to_rank - from_rank
        coordinate_terms = [
            f"piece.{piece.symbol().upper() if piece else 'unknown'}",
            f"from_file.{from_file}",
            f"from_rank.{from_rank}",
            f"to_file.{to_file}",
            f"to_rank.{to_rank}",
            f"delta_file_sign.{0 if df == 0 else 1 if df > 0 else -1}",
            f"delta_rank_sign.{0 if dr == 0 else 1 if dr > 0 else -1}",
            f"delta_file_abs.{abs(df)}",
            f"delta_rank_abs.{abs(dr)}",
        ]
        legal_labels.append({
            "move": legal_move.uci(),
            "piece": piece.symbol().upper() if piece else None,
            "is_king_move": bool(piece and piece.piece_type == chess.KING),
            "is_rook_move": bool(piece and piece.piece_type == chess.ROOK),
            "label": 1 if legal_child_dtm == best_child_dtm and legal_child_dtm >= 0 else 0,
            "target_class": (
                "optimal_dtm_move"
                if legal_child_dtm == best_child_dtm and legal_child_dtm >= 0
                else "winning_nonoptimal_move"
                if legal_child_dtm >= 0
                else "non_winning_move"
            ),
            "child_dtm": legal_child_dtm,
            "plies_to_mate_if_chosen": legal_child_dtm + 1 if legal_child_dtm >= 0 else None,
            "coordinate_terms": coordinate_terms,
            "move_shape_terms": legal_audit.get("move_shape_terms") or [],
            "post_move_terms": legal_audit.get("post_move_terms") or [],
        })
    return {
        "schema_version": "stage7_post_box_dtm_trajectory_step.v1",
        "ply_index": ply_index,
        "fen": board.fen(),
        "move": move.uci(),
        "piece": board.piece_at(move.from_square).symbol() if board.piece_at(move.from_square) else None,
        "target_skill": "krk.post_box_shrink_continuation",
        "target_class": "dtm_trajectory_white_move",
        "label": 1,
        "child_dtm": child_dtm,
        "plies_to_mate_if_chosen": child_dtm + 1 if child_dtm >= 0 else None,
        "move_shape_terms": audit.get("move_shape_terms") or [],
        "post_move_terms": audit.get("post_move_terms") or [],
        "legal_move_labels": legal_labels,
        "runtime_forbidden_terms": [
            "tablebase_lookup",
            "dtm_oracle_move_selection",
            "state_hash_exception",
        ],
    }


def build_trajectory_seed(
    *,
    oracle_path: Path,
    max_plies: int = 40,
) -> dict[str, Any]:
    oracle = _load_json(oracle_path)
    _, index, dtm = build_krk_dtm()
    trajectories: list[dict[str, Any]] = []
    for record in oracle.get("records") or []:
        if not isinstance(record, dict) or not record.get("fen"):
            continue
        board = chess.Board(str(record["fen"]))
        start_dtm = _dtm_for_board(board, index, dtm)
        plies: list[dict[str, Any]] = []
        white_steps: list[dict[str, Any]] = []
        for ply_index in range(max_plies):
            current_dtm = _dtm_for_board(board, index, dtm)
            if board.is_checkmate() or current_dtm == 0:
                break
            move, child_dtm = _choose_dtm_move(board, index, dtm)
            if move is None:
                break
            step = {
                "ply_index": ply_index,
                "turn": "white" if board.turn == chess.WHITE else "black",
                "fen": board.fen(),
                "move": move.uci(),
                "state_dtm": current_dtm,
                "child_dtm": child_dtm,
            }
            plies.append(step)
            if board.turn == chess.WHITE:
                white_steps.append(_white_training_step(board, move, child_dtm, ply_index, index, dtm))
            board.push(move)
        trajectories.append({
            "schema_version": "stage7_post_box_dtm_trajectory.v1",
            "causal_status": "non_causal_training_evidence",
            "start_fen": record["fen"],
            "start_dtm": start_dtm,
            "ended_in_checkmate": board.is_checkmate(),
            "final_fen": board.fen(),
            "ply_count": len(plies),
            "white_training_step_count": len(white_steps),
            "plies": plies,
            "white_training_steps": white_steps,
            "runtime_forbidden_terms": [
                "tablebase_lookup",
                "dtm_oracle_move_selection",
                "state_hash_exception",
            ],
        })
    return {
        "schema_version": "stage7_post_box_dtm_trajectory_seed.v1",
        "causal_status": "non_causal_training_evidence",
        "oracle_artifact": str(oracle_path),
        "target_skill": "krk.post_box_shrink_continuation",
        "trajectory_count": len(trajectories),
        "white_training_step_count": sum(item["white_training_step_count"] for item in trajectories),
        "trajectories": trajectories,
        "constraints": [
            "offline_training_seed_only",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "do_not_use_state_hash_exception_at_runtime",
            "do_not_promote_without_guardrails",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage 7 DTM trajectory seed")
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--max-plies", type=int, default=40)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--jsonl-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = build_trajectory_seed(oracle_path=args.oracle, max_plies=args.max_plies)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.jsonl_output:
        args.jsonl_output.parent.mkdir(parents=True, exist_ok=True)
        with args.jsonl_output.open("w", encoding="utf-8") as fh:
            for trajectory in payload.get("trajectories") or []:
                for step in trajectory.get("white_training_steps") or []:
                    fh.write(json.dumps(step, sort_keys=True) + "\n")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

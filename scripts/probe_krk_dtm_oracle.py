#!/usr/bin/env python3
"""Non-causal KRK DTM probe for small post-box continuation audits.

This builds a tiny retrograde table for K+R vs K positions and reports
force-mate first moves for requested FENs. It is diagnostic scaffolding only:
the output is evidence for StructuralCandidate evaluation, not a runtime
router or policy.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import deque
from pathlib import Path
from typing import Any

import chess


State = tuple[int, int, int, bool]


def _board_from_state(state: State) -> chess.Board:
    wk, wr, bk, turn = state
    board = chess.Board.empty()
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    board.turn = turn
    board.clear_stack()
    return board


def _state_from_board(board: chess.Board) -> State | None:
    wks = board.pieces(chess.KING, chess.WHITE)
    wrs = board.pieces(chess.ROOK, chess.WHITE)
    bks = board.pieces(chess.KING, chess.BLACK)
    if len(wks) != 1 or len(wrs) != 1 or len(bks) != 1:
        return None
    return (next(iter(wks)), next(iter(wrs)), next(iter(bks)), bool(board.turn))


def _is_valid_krk_state(state: State) -> bool:
    wk, wr, bk, _ = state
    if len({wk, wr, bk}) != 3:
        return False
    board = _board_from_state(state)
    return bool(board.is_valid())


def build_krk_dtm() -> tuple[list[State], dict[State, int], list[int]]:
    start = time.perf_counter()
    states: list[State] = []
    index: dict[State, int] = {}
    for wk in chess.SQUARES:
        for wr in chess.SQUARES:
            if wr == wk:
                continue
            for bk in chess.SQUARES:
                if bk == wk or bk == wr:
                    continue
                for turn in (chess.WHITE, chess.BLACK):
                    state = (wk, wr, bk, bool(turn))
                    if not _is_valid_krk_state(state):
                        continue
                    index[state] = len(states)
                    states.append(state)

    predecessors: list[list[int]] = [[] for _ in states]
    remaining = [0] * len(states)
    turn_is_white = [state[3] for state in states]
    dtm = [-1] * len(states)
    max_child = [-1] * len(states)
    queue: deque[int] = deque()

    for i, state in enumerate(states):
        board = _board_from_state(state)
        if board.is_checkmate():
            dtm[i] = 0
            queue.append(i)
            continue
        moves = list(board.legal_moves)
        remaining[i] = len(moves)
        for move in moves:
            child = board.copy(stack=False)
            child.push(move)
            child_state = _state_from_board(child)
            if child_state is None:
                continue
            child_idx = index.get(child_state)
            if child_idx is not None:
                predecessors[child_idx].append(i)

    while queue:
        child_idx = queue.popleft()
        child_dtm = dtm[child_idx]
        for pred_idx in predecessors[child_idx]:
            if dtm[pred_idx] >= 0:
                continue
            if turn_is_white[pred_idx]:
                dtm[pred_idx] = child_dtm + 1
                queue.append(pred_idx)
            else:
                remaining[pred_idx] -= 1
                if child_dtm > max_child[pred_idx]:
                    max_child[pred_idx] = child_dtm
                if remaining[pred_idx] == 0:
                    dtm[pred_idx] = max_child[pred_idx] + 1
                    queue.append(pred_idx)

    # Keep a compact timing breadcrumb on stdout; JSON carries full metadata.
    print(
        f"KRK DTM built: states={len(states)} winning={sum(1 for item in dtm if item >= 0)} "
        f"seconds={time.perf_counter() - start:.2f}",
        flush=True,
    )
    return states, index, dtm


def probe_fen(fen: str, index: dict[State, int], dtm: list[int]) -> dict[str, Any]:
    board = chess.Board(fen)
    state = _state_from_board(board)
    state_dtm = dtm[index[state]] if state in index else -1
    moves: list[dict[str, Any]] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        child = board.copy(stack=False)
        child.push(move)
        child_state = _state_from_board(child)
        child_dtm = dtm[index[child_state]] if child_state in index else -1
        moves.append({
            "move": move.uci(),
            "child_dtm": child_dtm,
            "forces_mate": child_dtm >= 0,
            "dtm_after_move": child_dtm,
            "plies_to_mate_if_chosen": child_dtm + 1 if child_dtm >= 0 else None,
            "is_check": child.is_check(),
            "is_checkmate": child.is_checkmate(),
        })
    winning = [item for item in moves if item["forces_mate"]]
    winning.sort(key=lambda item: (item["plies_to_mate_if_chosen"], item["move"]))
    return {
        "fen": fen,
        "state_indexed": state in index if state is not None else False,
        "state_dtm": state_dtm,
        "best_winning_moves": winning[:10],
        "winning_move_count": len(winning),
        "legal_move_count": len(moves),
        "legal_moves": moves,
    }


def _load_fens(args: argparse.Namespace) -> list[str]:
    fens: list[str] = []
    for item in args.fen:
        if item.strip():
            fens.append(item.strip())
    if args.diagnosis is not None:
        payload = json.loads(args.diagnosis.read_text(encoding="utf-8"))
        records = payload.get("unique_failed_post_reply_states") or payload.get("families") or []
        for record in records:
            if isinstance(record, dict) and record.get("post_reply_fen"):
                fens.append(str(record["post_reply_fen"]))
    seen: set[str] = set()
    unique: list[str] = []
    for fen in fens:
        if fen in seen:
            continue
        seen.add(fen)
        unique.append(fen)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-causal KRK DTM oracle probe")
    parser.add_argument("--fen", action="append", default=[])
    parser.add_argument("--diagnosis", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    states, index, dtm = build_krk_dtm()
    records = [probe_fen(fen, index, dtm) for fen in _load_fens(args)]
    payload = {
        "schema_version": "krk_dtm_oracle_probe.v1",
        "causal_status": "non_causal_diagnostic",
        "state_count": len(states),
        "winning_state_count": sum(1 for item in dtm if item >= 0),
        "records": records,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

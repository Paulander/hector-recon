"""Learner-visible KRK feature firewall for autogrowth.

This module is intentionally small and strict. It exposes generic board and
outcome features only; curriculum/stage/report vocabulary must stay outside the
learner path.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

import chess


FORBIDDEN_LEARNER_TERMS = (
    "stage7",
    "stage8",
    "box_shrink",
    "opposition_tempo",
    "report_row",
    "report_id",
    "row_id",
    "selector",
    "provider",
    "curriculum",
    "landmark",
)


def _square_file(square: int | None) -> int:
    return -1 if square is None else chess.square_file(square)


def _square_rank(square: int | None) -> int:
    return -1 if square is None else chess.square_rank(square)


def _chebyshev(a: int | None, b: int | None) -> int:
    if a is None or b is None:
        return 8
    return max(
        abs(chess.square_file(a) - chess.square_file(b)),
        abs(chess.square_rank(a) - chess.square_rank(b)),
    )


def _edge_distance(square: int | None) -> int:
    if square is None:
        return 4
    file_idx = chess.square_file(square)
    rank_idx = chess.square_rank(square)
    return min(file_idx, 7 - file_idx, rank_idx, 7 - rank_idx)


def _white_rook_square(board: chess.Board) -> int | None:
    rooks = sorted(board.pieces(chess.ROOK, chess.WHITE))
    return rooks[0] if rooks else None


def _black_mobility(board: chess.Board) -> int:
    if board.turn == chess.BLACK:
        return board.legal_moves.count()
    reply_board = board.copy(stack=False)
    reply_board.turn = chess.BLACK
    return reply_board.legal_moves.count()


def _rook_attacked_by_black(board: chess.Board) -> bool:
    rook = _white_rook_square(board)
    return bool(rook is not None and board.is_attacked_by(chess.BLACK, rook))


def extract_learner_features(board: chess.Board) -> dict[str, float]:
    """Return generic learner-visible features for a KRK board.

    The keys deliberately avoid curriculum/stage/provider/selector names. Values
    are numeric so trace records can be consumed by simple miners without schema
    expansion.
    """

    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    rook = _white_rook_square(board)
    features = {
        "white_king_file": float(_square_file(white_king)),
        "white_king_rank": float(_square_rank(white_king)),
        "white_rook_file": float(_square_file(rook)),
        "white_rook_rank": float(_square_rank(rook)),
        "black_king_file": float(_square_file(black_king)),
        "black_king_rank": float(_square_rank(black_king)),
        "side_white_to_move": 1.0 if board.turn == chess.WHITE else 0.0,
        "white_king_to_black_king_distance": float(_chebyshev(white_king, black_king)),
        "white_rook_to_black_king_distance": float(_chebyshev(rook, black_king)),
        "white_king_to_rook_distance": float(_chebyshev(white_king, rook)),
        "black_king_nearest_edge_distance": float(_edge_distance(black_king)),
        "legal_move_count": float(board.legal_moves.count()),
        "black_reply_mobility": float(_black_mobility(board)),
        "rook_present": 1.0 if rook is not None else 0.0,
        "rook_attacked_by_black": 1.0 if _rook_attacked_by_black(board) else 0.0,
        "is_check": 1.0 if board.is_check() else 0.0,
        "is_checkmate": 1.0 if board.is_checkmate() else 0.0,
        "is_stalemate": 1.0 if board.is_stalemate() else 0.0,
    }
    validate_learner_record(features)
    return features


def make_trace_record(
    *,
    board: chess.Board,
    move: chess.Move | None,
    after_board: chess.Board,
    outcome: str,
    ply: int,
) -> dict[str, Any]:
    """Build a generic before/action/after trace record."""

    piece = board.piece_at(move.from_square) if move is not None else None
    record: dict[str, Any] = {
        "ply": int(ply),
        "before_features": extract_learner_features(board),
        "action": {
            "uci": move.uci() if move is not None else None,
            "from_file": _square_file(move.from_square) if move is not None else -1,
            "from_rank": _square_rank(move.from_square) if move is not None else -1,
            "to_file": _square_file(move.to_square) if move is not None else -1,
            "to_rank": _square_rank(move.to_square) if move is not None else -1,
            "piece_type": 0 if piece is None else int(piece.piece_type),
        },
        "after_features": extract_learner_features(after_board),
        "outcome": str(outcome),
    }
    validate_learner_record(record)
    return record


def validate_learner_record(record: Mapping[str, Any] | list[Any] | str | float | int | None) -> None:
    """Raise if a learner-visible record leaks forbidden vocabulary."""

    serialized = json.dumps(record, sort_keys=True).lower()
    leaked = [term for term in FORBIDDEN_LEARNER_TERMS if term in serialized]
    if leaked:
        raise ValueError(f"learner-visible record contains forbidden terms: {leaked}")

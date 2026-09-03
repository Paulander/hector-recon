"""Environment-only exact KRK defence against mate on White's next move.

This module is an opponent, never a White move provider or reward shaper.
It exposes one legal Black move, not solution moves, values, or mate labels.
It is exact for the current two-White-move task, NOT a full-game WDL/DTM
oracle. Tied defences are ordered by UCI independently of the learner.
"""
from __future__ import annotations

import chess


def choose_mate_horizon_reply(board: chess.Board) -> chess.Move:
    """Avoid an immediate White mate whenever any legal defence permits it.

    All leaves are examined using chess rules, on private board copies. The
    caller must invoke this only after White has committed its chosen move.
    Searching an opponent's own action is allowed; the learner receives only
    the resulting move/board. This function neither accepts learner state nor
    persists a solution table.
    """

    if (
        board.chess960 or board.turn != chess.BLACK or not board.is_valid()
        or len(board.piece_map()) != 3
        or len(board.pieces(chess.KING, chess.WHITE)) != 1
        or len(board.pieces(chess.ROOK, chess.WHITE)) != 1
        or len(board.pieces(chess.KING, chess.BLACK)) != 1
    ):
        raise ValueError("mate-horizon opponent requires a valid Black-to-move KRK board")
    replies = sorted(board.legal_moves, key=lambda move: move.uci())
    if not replies:
        raise ValueError("mate-horizon opponent cannot act in a terminal position")
    if board.can_claim_draw():
        # A draw claim is not represented by chess.Move. Do not silently call
        # a move-only defence perfect on a history requiring that action.
        raise ValueError("mate-horizon move-only opponent does not model draw claims")
    for reply in replies:
        successor = board.copy(stack=False)
        successor.push(reply)
        has_mating_finish = False
        for finish in successor.legal_moves:
            leaf = successor.copy(stack=False)
            leaf.push(finish)
            if leaf.is_checkmate():
                has_mating_finish = True
                break
        if not has_mating_finish:
            return reply
    # Every reply permits mate next. No tied move is privileged according to
    # the learner's blind spots; evaluation must still test every reply.
    return replies[0]

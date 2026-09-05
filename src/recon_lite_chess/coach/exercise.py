"""A chess coach observes only the submitted move and the resulting board."""

from dataclasses import dataclass

import chess

from .interface import BoardSensor, Feedback, Organism, PositionReading


@dataclass(frozen=True)
class Attempt:
    event_id: int
    fen: str
    action: str | None
    after_fen: str
    reward: float
    reason: str
    real_moves: int


def play_mate_one(organism: Organism, fen: str, *, event_id: int, learn: bool) -> Attempt:
    """One White move, +1 for observed mate, -1 for failing this exercise.

    A non-mating legal move is NOT declared a chess loss. No alternative move
    is executed, scored, suggested, or sent back to the organism by the coach.
    Position curation belongs to the separate preparation command.
    """
    board = chess.Board(fen)
    if (not board.is_valid() or board.turn != chess.WHITE
            or board.is_game_over(claim_draw=False)):
        raise ValueError("exercise requires a live legal White-to-move position")
    material = sorted((p.piece_type, p.color) for p in board.piece_map().values())
    if material != sorted(((chess.KING, True), (chess.ROOK, True), (chess.KING, False))):
        raise ValueError("this exercise adapter supports KRK only")
    sensor = BoardSensor(PositionReading(
        pieces=tuple(sorted((sq, p.piece_type, p.color) for sq, p in board.piece_map().items())),
        white_to_move=board.turn,
        halfmove_clock=board.halfmove_clock,
        fullmove_number=board.fullmove_number,
    ))
    action = organism.act(sensor, event_id=event_id, learn=learn)
    reason, moved = "no_action", 0
    if action is not None:
        try:
            move = chess.Move.from_uci(action)
        except (ValueError, TypeError):
            move = None
        if move is None or move not in board.legal_moves:
            reason = "illegal_action"
        else:
            board.push(move)
            moved = 1
            reason = ("checkmate" if board.is_checkmate() else
                      "stalemate" if board.is_stalemate() else "exercise_timeout")
    reward = 1.0 if reason == "checkmate" else -1.0
    if learn:
        organism.observe(Feedback(event_id, action, reward, reason))
    return Attempt(event_id, fen, action, board.fen(), reward, reason, moved)

"""Chess embodiment for the feature-terminal developmental organism.

Only this environment adapter imports chess. Measurements describe the current
board and a primitive action's parameters, never a pushed hypothetical board.
"""
from __future__ import annotations

import chess

from recon_lite_hector.learning.terminal_development import Coordinate, TerminalDevelopment

BOOL = (False, True)
DISTANCE = tuple(range(8))
SCHEMA = tuple(Coordinate(name, domain) for name, domain in (
    ("white_to_move", BOOL),
    ("actuator_moves_rook", BOOL),
    ("kings_file_distance", DISTANCE),
    ("kings_rank_distance", DISTANCE),
    ("rook_black_king_file_distance", DISTANCE),
    ("rook_black_king_rank_distance", DISTANCE),
    ("target_black_king_file_distance", DISTANCE),
    ("target_black_king_rank_distance", DISTANCE),
    ("target_white_king_file_distance", DISTANCE),
    ("target_white_king_rank_distance", DISTANCE),
    ("black_king_on_edge_file", BOOL),
    ("black_king_on_edge_rank", BOOL),
    ("target_aligned_black_king_file", BOOL),
    ("target_aligned_black_king_rank", BOOL),
    ("kings_aligned_file", BOOL),
    ("kings_aligned_rank", BOOL),
))


class ChessFeaturePort:
    schema = SCHEMA

    def __init__(self, board: chess.Board):
        self._board = board
        self._moves = {move.uci(): move for move in board.legal_moves}
        self.executed: str | None = None

    def bindings(self):
        return tuple(sorted(self._moves))

    def measure(self, coordinate, binding):
        if self.executed is not None:
            raise RuntimeError("an action invalidates this observation frame")
        board = self._board
        move = self._moves[binding]
        wk, bk = board.king(chess.WHITE), board.king(chess.BLACK)
        wr = next(iter(board.pieces(chess.ROOK, chess.WHITE)))
        wx, wy = chess.square_file(wk), chess.square_rank(wk)
        bx, by = chess.square_file(bk), chess.square_rank(bk)
        rx, ry = chess.square_file(wr), chess.square_rank(wr)
        tx, ty = chess.square_file(move.to_square), chess.square_rank(move.to_square)
        values = (
            board.turn == chess.WHITE,
            board.piece_type_at(move.from_square) == chess.ROOK,
            abs(wx-bx), abs(wy-by), abs(rx-bx), abs(ry-by),
            abs(tx-bx), abs(ty-by), abs(tx-wx), abs(ty-wy),
            bx in (0, 7), by in (0, 7), tx == bx, ty == by, wx == bx, wy == by,
        )
        return self.schema[coordinate].validate(values[coordinate])

    def execute(self, binding):
        if self.executed is not None:
            raise RuntimeError("one action per environment frame")
        move = self._moves[binding]
        if move not in self._board.legal_moves:
            raise ValueError("stale or illegal actuator binding")
        self._board.push(move)
        self.executed = binding


class TerminalOrganism(TerminalDevelopment):
    """Marker for the typed embodiment, with all learning in the generic core."""

    embodiment = "typed_feature_terminals_v1"

"""Deterministic KRK position generation for autogrowth."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random
from typing import Iterable

import chess


@dataclass(frozen=True)
class KRKPositionSet:
    seed: int
    train: tuple[str, ...]
    heldout_weakness: tuple[str, ...]
    heldout_broader: tuple[str, ...]

    @property
    def heldout(self) -> tuple[str, ...]:
        return self.heldout_weakness + self.heldout_broader

    def digest(self) -> str:
        payload = "\n".join([str(self.seed), *self.train, *self.heldout])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _empty_krk_board(wk: int, wr: int, bk: int) -> chess.Board:
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


def _chebyshev(a: int, b: int) -> int:
    return max(
        abs(chess.square_file(a) - chess.square_file(b)),
        abs(chess.square_rank(a) - chess.square_rank(b)),
    )


def _edge_distance(square: int) -> int:
    file_idx = chess.square_file(square)
    rank_idx = chess.square_rank(square)
    return min(file_idx, 7 - file_idx, rank_idx, 7 - rank_idx)


def can_mate_in_one(board: chess.Board) -> bool:
    return any(_move_checkmates(board, move) for move in board.legal_moves)


def _move_checkmates(board: chess.Board, move: chess.Move) -> bool:
    if move not in board.legal_moves:
        return False
    after = board.copy(stack=False)
    after.push(move)
    return after.is_checkmate()


def is_valid_krk_seed(board: chess.Board) -> bool:
    if board.turn != chess.WHITE:
        return False
    pieces = board.piece_map()
    white_types = sorted(piece.piece_type for piece in pieces.values() if piece.color == chess.WHITE)
    black_types = sorted(piece.piece_type for piece in pieces.values() if piece.color == chess.BLACK)
    if white_types != sorted([chess.KING, chess.ROOK]) or black_types != [chess.KING]:
        return False
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    if white_king is None or black_king is None:
        return False
    if _chebyshev(white_king, black_king) <= 1:
        return False
    if not board.is_valid():
        return False
    if board.is_game_over(claim_draw=False):
        return False
    if board.is_checkmate() or board.is_stalemate():
        return False
    if can_mate_in_one(board):
        return False
    return True


def _weakness_zone_candidate(board: chess.Board) -> bool:
    black_king = board.king(chess.BLACK)
    white_king = board.king(chess.WHITE)
    rook_squares = sorted(board.pieces(chess.ROOK, chess.WHITE))
    if black_king is None or white_king is None or not rook_squares:
        return False
    rook = rook_squares[0]
    return (
        _edge_distance(black_king) >= 1
        and _chebyshev(white_king, black_king) >= 2
        and _chebyshev(rook, black_king) >= 2
        and board.legal_moves.count() >= 8
    )


def generate_krk_board(
    rng: random.Random,
    *,
    weakness_zone: bool = False,
    excluded_fens: Iterable[str] = (),
    max_attempts: int = 100_000,
) -> chess.Board:
    excluded = set(excluded_fens)
    squares = list(chess.SQUARES)
    for _ in range(max_attempts):
        wk, wr, bk = rng.sample(squares, 3)
        board = _empty_krk_board(wk, wr, bk)
        if not is_valid_krk_seed(board):
            continue
        if weakness_zone and not _weakness_zone_candidate(board):
            continue
        if board.fen() in excluded:
            continue
        return board
    raise RuntimeError("could not generate KRK position with requested constraints")


def generate_position_sets(
    *,
    seed: int,
    train_count: int = 200,
    heldout_weakness_count: int = 100,
    heldout_broader_count: int = 100,
) -> KRKPositionSet:
    rng = random.Random(seed)
    used: set[str] = set()

    def take(count: int, *, weakness_zone: bool) -> tuple[str, ...]:
        fens: list[str] = []
        for _ in range(count):
            board = generate_krk_board(rng, weakness_zone=weakness_zone, excluded_fens=used)
            fen = board.fen()
            used.add(fen)
            fens.append(fen)
        return tuple(fens)

    return KRKPositionSet(
        seed=int(seed),
        train=take(train_count, weakness_zone=False),
        heldout_weakness=take(heldout_weakness_count, weakness_zone=True),
        heldout_broader=take(heldout_broader_count, weakness_zone=False),
    )

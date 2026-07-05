"""Learner-visible KRK feature firewall for autogrowth.

This module is intentionally small and strict. It exposes generic board and
outcome features only; curriculum/stage/report vocabulary must stay outside the
learner path.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

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

LEARNER_VISIBLE_FEATURE_NAMES = (
    "white_king_file",
    "white_king_rank",
    "white_rook_file",
    "white_rook_rank",
    "black_king_file",
    "black_king_rank",
    "side_white_to_move",
    "white_king_to_black_king_distance",
    "white_rook_to_black_king_distance",
    "white_king_to_rook_distance",
    "black_king_nearest_edge_distance",
    "rook_present",
    "rook_attacked_by_black",
    "is_check",
    "king_delta_file_abs",
    "king_delta_rank_abs",
    "king_support_l_shape",
    "king_pair_knight_distance_like",
    "king_support_chebyshev_distance",
    "king_support_manhattan_distance",
    "rook_black_king_same_side_of_white_king_on_primary_axis",
    "rook_black_king_opposite_sides_of_white_king_on_primary_axis",
    "rook_distance_to_black_king_edge_line",
    "rook_fence_depth_relative_to_black_king_edge",
    "black_king_on_edge",
    "black_king_corner_distance",
    "bk_neighbor_n_available",
    "bk_neighbor_ne_available",
    "bk_neighbor_e_available",
    "bk_neighbor_se_available",
    "bk_neighbor_s_available",
    "bk_neighbor_sw_available",
    "bk_neighbor_w_available",
    "bk_neighbor_nw_available",
)

REMOVE_MARKED_LEARNER_FEATURES = (
    "legal_move_count",
    "black_reply_mobility",
    "is_checkmate",
    "is_stalemate",
    "rook_lateral_escape_available",
    "white_king_controls_escape_band",
    "feature_hub_opposition_status",
    "feature_hub_mobility",
    "feature_hub_king_tropism",
    "feature_hub_mobility_restriction",
    "feature_hub_tempo_advantage",
    "feature_hub_mating_net_present",
    "feature_hub_enemy_king_mobility",
    "feature_hub_enemy_king_mobility_raw",
    "feature_hub_stalemate_danger",
)

LEARNER_VISIBLE_ACTION_FEATURE_NAMES = (
    "piece_type",
    "file_delta_sign",
    "rank_delta_sign",
    "file_delta_magnitude",
    "rank_delta_magnitude",
    "from_file_edge_distance",
    "from_rank_edge_distance",
    "to_file_edge_distance",
    "to_rank_edge_distance",
    "gives_check",
    "is_capture",
    "black_king_edge_after",
    "white_king_to_black_king_after",
    "white_rook_to_black_king_after",
    "white_king_to_rook_after",
    "rook_attacked_after",
)

LEARNER_VISIBLE_ACTION_COMPOUNDS = (
    "pair:gives_check:black_king_edge_after",
    "pair:piece:gives_check",
    "pair:piece:file_rank_delta",
    "pair:rook_safety:gives_check",
)

_LEARNER_VISIBLE_FEATURE_SET = frozenset(LEARNER_VISIBLE_FEATURE_NAMES)
_REMOVE_MARKED_FEATURE_SET = frozenset(REMOVE_MARKED_LEARNER_FEATURES)
_LEARNER_VISIBLE_ACTION_FEATURE_SET = frozenset(LEARNER_VISIBLE_ACTION_FEATURE_NAMES)
_LEARNER_VISIBLE_ACTION_COMPOUND_SET = frozenset(LEARNER_VISIBLE_ACTION_COMPOUNDS)

_BK_NEIGHBOR_DIRECTIONS = (
    ("n", 0, 1),
    ("ne", 1, 1),
    ("e", 1, 0),
    ("se", 1, -1),
    ("s", 0, -1),
    ("sw", -1, -1),
    ("w", -1, 0),
    ("nw", -1, 1),
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


def _corner_distance(square: int | None) -> int:
    if square is None:
        return 8
    file_idx = chess.square_file(square)
    rank_idx = chess.square_rank(square)
    return min(
        file_idx + rank_idx,
        file_idx + (7 - rank_idx),
        (7 - file_idx) + rank_idx,
        (7 - file_idx) + (7 - rank_idx),
    )


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


def _edge_axis(square: int | None) -> str:
    if square is None:
        return "none"
    file_idx = chess.square_file(square)
    rank_idx = chess.square_rank(square)
    if rank_idx in (0, 7):
        return "rank"
    if file_idx in (0, 7):
        return "file"
    return "none"


def _axis_coord(square: int | None, axis: str) -> int:
    if square is None:
        return -1
    if axis == "rank":
        return chess.square_file(square)
    if axis == "file":
        return chess.square_rank(square)
    return -1


def _sign(value: int) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _rook_lateral_escape_available(board: chess.Board) -> bool:
    rook = _white_rook_square(board)
    if rook is None:
        return False
    for move in board.legal_moves:
        if move.from_square != rook:
            continue
        if chess.square_file(move.from_square) == chess.square_file(move.to_square):
            continue
        after = board.copy(stack=False)
        after.push(move)
        if not _rook_attacked_by_black(after) and bool(after.pieces(chess.ROOK, chess.WHITE)):
            return True
    return False


def _white_king_controls_escape_band(board: chess.Board) -> bool:
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk is None or bk is None:
        return False
    bk_file = chess.square_file(bk)
    bk_rank = chess.square_rank(bk)
    escape_squares: list[int] = []
    if bk_file == 0:
        escape_squares.extend(chess.square(1, rank) for rank in range(max(0, bk_rank - 1), min(7, bk_rank + 1) + 1))
    elif bk_file == 7:
        escape_squares.extend(chess.square(6, rank) for rank in range(max(0, bk_rank - 1), min(7, bk_rank + 1) + 1))
    if bk_rank == 0:
        escape_squares.extend(chess.square(file_idx, 1) for file_idx in range(max(0, bk_file - 1), min(7, bk_file + 1) + 1))
    elif bk_rank == 7:
        escape_squares.extend(chess.square(file_idx, 6) for file_idx in range(max(0, bk_file - 1), min(7, bk_file + 1) + 1))
    return any(chess.square_distance(wk, square) <= 1 for square in set(escape_squares))


def _edge_geometry_features(
    *,
    white_king: int | None,
    black_king: int | None,
    rook: int | None,
    board: chess.Board,
) -> dict[str, float]:
    if white_king is None or black_king is None:
        return {
            "king_delta_file_abs": 8.0,
            "king_delta_rank_abs": 8.0,
            "king_support_l_shape": 0.0,
            "king_pair_knight_distance_like": 0.0,
            "king_support_chebyshev_distance": 8.0,
            "king_support_manhattan_distance": 16.0,
            "rook_black_king_same_side_of_white_king_on_primary_axis": 0.0,
            "rook_black_king_opposite_sides_of_white_king_on_primary_axis": 0.0,
            "rook_distance_to_black_king_edge_line": 8.0,
            "rook_fence_depth_relative_to_black_king_edge": 8.0,
            "black_king_on_edge": 0.0,
            "black_king_corner_distance": 8.0,
        }
    wk_file, wk_rank = chess.square_file(white_king), chess.square_rank(white_king)
    bk_file, bk_rank = chess.square_file(black_king), chess.square_rank(black_king)
    file_abs = abs(wk_file - bk_file)
    rank_abs = abs(wk_rank - bk_rank)
    axis = _edge_axis(black_king)
    rook_coord = _axis_coord(rook, axis)
    wk_coord = _axis_coord(white_king, axis)
    bk_coord = _axis_coord(black_king, axis)
    rook_side = 0 if rook_coord < 0 or wk_coord < 0 else _sign(rook_coord - wk_coord)
    bk_side = 0 if bk_coord < 0 or wk_coord < 0 else _sign(bk_coord - wk_coord)
    rook_file = -1 if rook is None else chess.square_file(rook)
    rook_rank = -1 if rook is None else chess.square_rank(rook)
    if black_king is None or rook is None:
        edge_line_distance = 8
        fence_depth = 8
    elif bk_file in (0, 7):
        edge_line_distance = abs(rook_file - bk_file)
        fence_depth = abs(rook_file - bk_file)
    elif bk_rank in (0, 7):
        edge_line_distance = abs(rook_rank - bk_rank)
        fence_depth = abs(rook_rank - bk_rank)
    else:
        edge_line_distance = _edge_distance(rook)
        fence_depth = _edge_distance(rook)
    l_shape = sorted((file_abs, rank_abs)) == [1, 2]
    return {
        "king_delta_file_abs": float(file_abs),
        "king_delta_rank_abs": float(rank_abs),
        "king_support_l_shape": 1.0 if l_shape else 0.0,
        "king_pair_knight_distance_like": 1.0 if l_shape else 0.0,
        "king_support_chebyshev_distance": float(max(file_abs, rank_abs)),
        "king_support_manhattan_distance": float(file_abs + rank_abs),
        "rook_black_king_same_side_of_white_king_on_primary_axis": 1.0
        if rook_side != 0 and rook_side == bk_side
        else 0.0,
        "rook_black_king_opposite_sides_of_white_king_on_primary_axis": 1.0
        if rook_side != 0 and bk_side != 0 and rook_side != bk_side
        else 0.0,
        "rook_distance_to_black_king_edge_line": float(edge_line_distance),
        "rook_fence_depth_relative_to_black_king_edge": float(fence_depth),
        "black_king_on_edge": 1.0 if _edge_distance(black_king) == 0 else 0.0,
        "black_king_corner_distance": float(_corner_distance(black_king)),
    }


def _black_king_neighbor_features(board: chess.Board, black_king: int | None) -> dict[str, float]:
    features = {
        f"bk_neighbor_{name}_available": 0.0
        for name, _, _ in _BK_NEIGHBOR_DIRECTIONS
    }
    if black_king is None:
        return features

    bk_file = chess.square_file(black_king)
    bk_rank = chess.square_rank(black_king)
    for name, file_delta, rank_delta in _BK_NEIGHBOR_DIRECTIONS:
        file_idx = bk_file + file_delta
        rank_idx = bk_rank + rank_delta
        if not (0 <= file_idx <= 7 and 0 <= rank_idx <= 7):
            continue
        square = chess.square(file_idx, rank_idx)
        if board.piece_at(square) is None and not board.is_attacked_by(
            chess.WHITE,
            square,
        ):
            features[f"bk_neighbor_{name}_available"] = 1.0
    return features


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
        "rook_present": 1.0 if rook is not None else 0.0,
        "rook_attacked_by_black": 1.0 if _rook_attacked_by_black(board) else 0.0,
        "is_check": 1.0 if board.is_check() else 0.0,
    }
    features.update(
        _edge_geometry_features(
            white_king=white_king,
            black_king=black_king,
            rook=rook,
            board=board,
        )
    )
    features.update(_black_king_neighbor_features(board, black_king))
    extra = set(features) - _LEARNER_VISIBLE_FEATURE_SET
    missing = _LEARNER_VISIBLE_FEATURE_SET - set(features)
    if extra or missing:
        raise ValueError(
            f"learner feature firewall mismatch: extra={sorted(extra)} missing={sorted(missing)}"
        )
    validate_learner_record(features)
    return features


def extract_diagnostic_features(board: chess.Board) -> dict[str, float]:
    """Return the full trainer-side feature record, including diagnostics."""

    features = extract_learner_features(board)
    features.update(
        {
            "legal_move_count": float(board.legal_moves.count()),
            "black_reply_mobility": float(_black_mobility(board)),
            "is_checkmate": 1.0 if board.is_checkmate() else 0.0,
            "is_stalemate": 1.0 if board.is_stalemate() else 0.0,
            "rook_lateral_escape_available": 1.0
            if _rook_lateral_escape_available(board)
            else 0.0,
            "white_king_controls_escape_band": 1.0
            if _white_king_controls_escape_band(board)
            else 0.0,
        }
    )
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
    before_features = extract_learner_features(board)
    after_features = extract_learner_features(after_board)
    progress_deltas = {
        key: float(after_features[key] - before_features[key])
        for key in sorted(before_features)
    }
    record: dict[str, Any] = {
        "ply": int(ply),
        "before_features": before_features,
        "action": {
            "uci": move.uci() if move is not None else None,
            "from_file": _square_file(move.from_square) if move is not None else -1,
            "from_rank": _square_rank(move.from_square) if move is not None else -1,
            "to_file": _square_file(move.to_square) if move is not None else -1,
            "to_rank": _square_rank(move.to_square) if move is not None else -1,
            "file_delta": (
                _square_file(move.to_square) - _square_file(move.from_square)
                if move is not None
                else 0
            ),
            "rank_delta": (
                _square_rank(move.to_square) - _square_rank(move.from_square)
                if move is not None
                else 0
            ),
            "piece_type": 0 if piece is None else int(piece.piece_type),
            "is_capture": 1.0 if move is not None and board.is_capture(move) else 0.0,
            "gives_check": 1.0 if move is not None and board.gives_check(move) else 0.0,
        },
        "after_features": after_features,
        "progress_deltas": progress_deltas,
        "recon_growth_view": {
            "before_node_type": "TERMINAL",
            "action_node_type": "ACTION",
            "after_node_type": "TERMINAL",
            "script_node_type": "SCRIPT",
            "allowed_relation_types": ["SUB", "SUR", "POR", "RET"],
            "behavior_change_applied": False,
            "external_action_ranking_applied": False,
            "before_feature_keys": sorted(before_features),
            "after_feature_keys": sorted(after_features),
        },
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


def learner_visible_key_firewall_leaks(keys: Iterable[str]) -> dict[str, list[str]]:
    """Return leaked feature names by key for learner-visible terminal builders."""

    leaks: dict[str, list[str]] = {}
    for key in keys:
        found = _learner_key_leaks(str(key))
        if found:
            leaks[str(key)] = found
    return leaks


def validate_learner_visible_keys(keys: Iterable[str], *, builder: str) -> None:
    """Reject learner-visible keys that bypass the dieted feature boundary."""

    materialized = tuple(str(key) for key in keys)
    leaks = learner_visible_key_firewall_leaks(materialized)
    if leaks:
        flat = sorted({feature for items in leaks.values() for feature in items})
        raise ValueError(f"{builder} learner key firewall rejected leaked features: {flat}")
    validate_learner_record(list(materialized))


def _learner_key_leaks(key: str) -> list[str]:
    if key.startswith(("before_terminal:", "after_terminal:", "delta_terminal:")):
        name = key.split(":", 1)[1].split("=", 1)[0]
        if name not in _LEARNER_VISIBLE_FEATURE_SET:
            return [name]
        return []
    if key.startswith("action_pattern:"):
        action_name = key.split(":", 1)[1].split("=", 1)[0]
        if action_name.startswith("pair:"):
            if action_name in _LEARNER_VISIBLE_ACTION_COMPOUND_SET:
                return []
            return _remove_marked_components(action_name.split(":"))
        if action_name not in _LEARNER_VISIBLE_ACTION_FEATURE_SET:
            return _remove_marked_components((action_name,)) or [action_name]
        return []
    if key.startswith("micro_"):
        return _micro_key_leaks(key)
    if key.startswith("post_move_"):
        return _post_move_key_leaks(key)
    return _remove_marked_components((key.split("=", 1)[0],))


def _remove_marked_components(names: Iterable[str]) -> list[str]:
    leaks: set[str] = set()
    for name in names:
        raw = str(name).split("=", 1)[0]
        canonical = _canonical_remove_marked_name(raw)
        if canonical is not None:
            leaks.add(raw)
        elif raw.startswith("feature_hub_"):
            leaks.add(raw)
    return sorted(leaks)


def _canonical_remove_marked_name(name: str) -> str | None:
    if name in _REMOVE_MARKED_FEATURE_SET:
        return name
    aliases = {
        "black_reply_mobility_after": "black_reply_mobility",
        "black_mobility": "black_reply_mobility",
        "post_move_black_mobility_delta_sign": "black_reply_mobility",
        "is_stalemate_after": "is_stalemate",
        "stalemate_after": "is_stalemate",
        "post_move_stalemate": "is_stalemate",
        "is_checkmate_after": "is_checkmate",
    }
    return aliases.get(name)


def _micro_key_leaks(key: str) -> list[str]:
    head = key.split("=", 1)[0]
    leaks = _remove_marked_components((head.split(":", 1)[-1],))
    if "black_mobility" in key or "|mob=" in key:
        leaks.append("black_mobility")
    if "stalemate_after" in key:
        leaks.append("stalemate_after")
    if "rook_risk_after" in key or "|risk=" in key:
        leaks.append("rook_capturable_by_reply")
    return sorted(set(leaks))


def _post_move_key_leaks(key: str) -> list[str]:
    name = key.split("=", 1)[0]
    return _remove_marked_components((name,))

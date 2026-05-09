"""KRK landmark rewards for staged baseline curriculum growth.

These rewards are deliberately small, explicit shaping signals. They do not
replace mate/basin backchaining; they expose intermediate KRK landmarks such as
edge pressure, stable rook fences, box shrinkage, and opposition/tempo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import chess


LANDMARK_LABELS = (
    "edge_trap",
    "edge_trap_close",
    "edge_trap_enemy_between",
    "edge_trap_wrong_tempo",
    "fence_established",
    "drive_to_edge",
    "box_shrink",
    "opposition_tempo",
    "full_krk",
)


@dataclass(frozen=True)
class KRKLandmarkStageSpec:
    """One non-mate KRK landmark stage."""

    stage_index: int
    label: str
    source_stage_names: tuple[str, ...]
    target_label: str
    description: str


KRK_LANDMARK_STAGE_SPECS: List[KRKLandmarkStageSpec] = [
    KRKLandmarkStageSpec(
        stage_index=2,
        label="edge_trap_close",
        source_stage_names=("Edge_Trap_Close",),
        target_label="stage0_basin",
        description="Convert close edge-trap geometry toward the learned mate basin.",
    ),
    KRKLandmarkStageSpec(
        stage_index=3,
        label="edge_trap_enemy_between",
        source_stage_names=("Edge_Trap_Enemy_Between",),
        target_label="stage0_basin",
        description="Resolve edge traps where the enemy king is between king and rook.",
    ),
    KRKLandmarkStageSpec(
        stage_index=4,
        label="edge_trap_wrong_tempo",
        source_stage_names=("Edge_Trap_Wrong_Tempo",),
        target_label="stage0_basin",
        description="Fix wrong-tempo edge traps without drifting into stalemate.",
    ),
    KRKLandmarkStageSpec(
        stage_index=5,
        label="fence_established",
        source_stage_names=("Fence_Established", "Anchored_Cut", "Edge_Cut_Hold"),
        target_label="edge_trap_wrong_tempo",
        description="Gain or maintain a safe rook fence/cut.",
    ),
    KRKLandmarkStageSpec(
        stage_index=6,
        label="drive_to_edge",
        source_stage_names=("Opposition_Approach", "Tempo_Wait", "King_Close_1"),
        target_label="fence_established",
        description="Drive the enemy king toward the rim while preserving safety.",
    ),
    KRKLandmarkStageSpec(
        stage_index=7,
        label="box_shrink",
        source_stage_names=("Box_Small", "Box_Medium", "Edge_Fence_Deep"),
        target_label="drive_to_edge",
        description="Shrink the confinement box without letting it grow.",
    ),
    KRKLandmarkStageSpec(
        stage_index=8,
        label="opposition_tempo",
        source_stage_names=("Opposition_Approach", "Tempo_Wait", "Edge_Fence_Approach"),
        target_label="box_shrink",
        description="Learn opposition and waiting/tempo motifs.",
    ),
    KRKLandmarkStageSpec(
        stage_index=9,
        label="full_krk",
        source_stage_names=("Full_KRK",),
        target_label="opposition_tempo",
        description="Arbitrary KRK positions routed through learned landmarks.",
    ),
]


def spec_for_stage(stage_index: int) -> KRKLandmarkStageSpec | None:
    for spec in KRK_LANDMARK_STAGE_SPECS:
        if spec.stage_index == stage_index:
            return spec
    return None


def specs_through(max_stage: int) -> List[KRKLandmarkStageSpec]:
    return [spec for spec in KRK_LANDMARK_STAGE_SPECS if spec.stage_index <= max_stage]


def reward_family_for_label(label: str) -> str:
    """Map split curriculum labels onto the shared reward family."""
    if label in {"edge_trap_close", "edge_trap_enemy_between", "edge_trap_wrong_tempo"}:
        return "edge_trap"
    return label


def _wk(board: chess.Board) -> int | None:
    return board.king(chess.WHITE)


def _bk(board: chess.Board) -> int | None:
    return board.king(chess.BLACK)


def _rook(board: chess.Board) -> int | None:
    rooks = list(board.pieces(chess.ROOK, chess.WHITE))
    return rooks[0] if rooks else None


def chebyshev(a: int, b: int) -> int:
    return max(
        abs(chess.square_file(a) - chess.square_file(b)),
        abs(chess.square_rank(a) - chess.square_rank(b)),
    )


def edge_distance(square: int | None) -> int:
    if square is None:
        return 4
    f = chess.square_file(square)
    r = chess.square_rank(square)
    return min(f, 7 - f, r, 7 - r)


def white_has_opposition(board: chess.Board) -> bool:
    wk = _wk(board)
    bk = _bk(board)
    if wk is None or bk is None:
        return False
    same_file = chess.square_file(wk) == chess.square_file(bk)
    same_rank = chess.square_rank(wk) == chess.square_rank(bk)
    return board.turn == chess.BLACK and (same_file or same_rank) and chebyshev(wk, bk) == 2


def white_rook_safe(board: chess.Board) -> bool:
    rook = _rook(board)
    wk = _wk(board)
    bk = _bk(board)
    if rook is None:
        return False
    if wk is None or bk is None:
        return True
    if chebyshev(bk, rook) > 1:
        return True
    capture = chess.Move(bk, rook)
    b = board.copy(stack=False)
    b.turn = chess.BLACK
    if capture in b.legal_moves:
        return chebyshev(wk, rook) <= 1
    return True


def _box_dims(board: chess.Board) -> tuple[int, int]:
    rook = _rook(board)
    bk = _bk(board)
    if rook is None or bk is None:
        return (8, 8)
    rf, rr = chess.square_file(rook), chess.square_rank(rook)
    bf, br = chess.square_file(bk), chess.square_rank(bk)
    width = rf if bf < rf else 7 - rf
    height = rr if br < rr else 7 - rr
    return max(1, width), max(1, height)


def box_area(board: chess.Board) -> int:
    w, h = _box_dims(board)
    return w * h


def box_min_side(board: chess.Board) -> int:
    return min(_box_dims(board))


def white_stable_cut(board: chess.Board) -> bool:
    rook = _rook(board)
    bk = _bk(board)
    if rook is None or bk is None:
        return False
    if edge_distance(bk) == 0 and white_rook_safe(board):
        return True
    same_file = chess.square_file(rook) == chess.square_file(bk)
    same_rank = chess.square_rank(rook) == chess.square_rank(bk)
    return (same_file or same_rank) and chebyshev(rook, bk) >= 2 and white_rook_safe(board)


def rook_fence_distance(board: chess.Board) -> int:
    rook = _rook(board)
    bk = _bk(board)
    if rook is None or bk is None:
        return 8
    bf, br = chess.square_file(bk), chess.square_rank(bk)
    d_file = min(bf, 7 - bf)
    d_rank = min(br, 7 - br)
    if d_file <= d_rank:
        edge = 0 if bf <= 7 - bf else 7
        target_file = 1 if edge == 0 else 6
        return abs(chess.square_file(rook) - target_file)
    edge = 0 if br <= 7 - br else 7
    target_rank = 1 if edge == 0 else 6
    return abs(chess.square_rank(rook) - target_rank)


def can_deliver_mate(board: chess.Board) -> bool:
    for move in board.legal_moves:
        b = board.copy(stack=False)
        b.push(move)
        if b.is_checkmate():
            return True
    return False


def rich_feature_dict(board: chess.Board) -> Dict[str, float]:
    wk = _wk(board)
    bk = _bk(board)
    rook = _rook(board)
    return {
        "king_distance": float(chebyshev(wk, bk) if wk is not None and bk is not None else 8),
        "opposition_status": 1.0 if white_has_opposition(board) else 0.0,
        "enemy_king_edge_distance": float(edge_distance(bk)),
        "side_to_move": 1.0 if board.turn == chess.WHITE else 0.0,
        "box_area": float(box_area(board)),
        "box_min_side": float(box_min_side(board)),
        "rook_fence_distance": float(rook_fence_distance(board)),
        "cut_established": 1.0 if white_stable_cut(board) else 0.0,
        "rook_safe": 1.0 if white_rook_safe(board) else 0.0,
        "king_rook_distance": float(chebyshev(wk, rook) if wk is not None and rook is not None else 8),
        "can_mate_now": 1.0 if can_deliver_mate(board) else 0.0,
        "stalemate_danger": 1.0 if board.is_stalemate() else 0.0,
        "is_check": 1.0 if board.is_check() else 0.0,
        "is_checkmate": 1.0 if board.is_checkmate() else 0.0,
        "black_king_at_edge": 1.0 if edge_distance(bk) == 0 else 0.0,
    }


RICH_FEATURE_NAMES = tuple(rich_feature_dict(chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")).keys())
RICH_GOAL_FEATURE_INDEX = RICH_FEATURE_NAMES.index("is_checkmate")


def rich_feature_vector(board: chess.Board) -> List[float]:
    f = rich_feature_dict(board)
    return [
        f["king_distance"] / 8.0,
        f["opposition_status"],
        f["enemy_king_edge_distance"] / 4.0,
        f["side_to_move"],
        f["box_area"] / 64.0,
        f["box_min_side"] / 8.0,
        f["rook_fence_distance"] / 8.0,
        f["cut_established"],
        f["rook_safe"],
        f["king_rook_distance"] / 8.0,
        f["can_mate_now"],
        f["stalemate_danger"],
        f["is_check"],
        f["is_checkmate"],
        f["black_king_at_edge"],
    ]


def _bool_gain(before: bool, after: bool, maintain_bonus: float = 0.03) -> float:
    if after and not before:
        return 1.0
    if after and before:
        return maintain_bonus
    if before and not after:
        return -1.0
    return 0.0


def landmark_reward(board_before: chess.Board, board_after: chess.Board, label: str) -> float:
    """Compute a dense KRK landmark reward for one white move outcome."""
    label = reward_family_for_label(label)
    if board_after.is_checkmate():
        return 2.0
    if board_after.is_stalemate() or _rook(board_after) is None:
        return -1.0

    fb = rich_feature_dict(board_before)
    fa = rich_feature_dict(board_after)

    edge_reward = (fb["enemy_king_edge_distance"] - fa["enemy_king_edge_distance"]) / 4.0
    box_reward = (fb["box_area"] - fa["box_area"]) / 64.0
    box_side_reward = (fb["box_min_side"] - fa["box_min_side"]) / 8.0
    fence_reward = _bool_gain(bool(fb["cut_established"]), bool(fa["cut_established"]))
    rook_safety = 0.05 if fa["rook_safe"] else -0.3
    coordination = (fb["king_distance"] - fa["king_distance"]) / 8.0
    opposition = _bool_gain(bool(fb["opposition_status"]), bool(fa["opposition_status"]), 0.05)
    can_mate = _bool_gain(bool(fb["can_mate_now"]), bool(fa["can_mate_now"]), 0.05)

    if fa["box_area"] > fb["box_area"]:
        box_reward -= 0.25
    if fa["box_min_side"] > fb["box_min_side"]:
        box_side_reward -= 0.2

    components = {
        "edge_trap": 0.6 * edge_reward + 0.3 * fence_reward + 0.2 * can_mate + rook_safety,
        "fence_established": 0.8 * fence_reward + 0.2 * box_side_reward + rook_safety,
        "drive_to_edge": 0.8 * edge_reward + 0.2 * coordination + 0.2 * fence_reward + rook_safety,
        "box_shrink": 0.7 * box_reward + 0.3 * box_side_reward + 0.2 * fence_reward + rook_safety,
        "opposition_tempo": 0.6 * opposition + 0.2 * coordination + 0.2 * can_mate + rook_safety,
        "full_krk": (
            0.3 * edge_reward
            + 0.25 * box_reward
            + 0.2 * fence_reward
            + 0.15 * coordination
            + 0.1 * opposition
            + rook_safety
        ),
    }
    if label not in components:
        raise ValueError(f"Unknown KRK landmark label: {label}")
    return float(components[label])


def worst_reply_reward(
    board_before: chess.Board,
    white_move: chess.Move,
    label: str,
    *,
    use_black_reply: bool = True,
) -> float:
    """Score a move using the worst black reply when available."""
    b1 = board_before.copy(stack=False)
    b1.push(white_move)
    if not use_black_reply or b1.is_game_over():
        return landmark_reward(board_before, b1, label)

    replies = list(b1.legal_moves)
    if not replies:
        return landmark_reward(board_before, b1, label)
    rewards = []
    for reply in replies:
        b2 = b1.copy(stack=False)
        b2.push(reply)
        rewards.append(landmark_reward(board_before, b2, label))
    return min(rewards)


def select_stage_position(stage_names: Iterable[str]) -> chess.Board:
    """Sample a board from the existing named KRK curriculum stages."""
    from recon_lite_chess.training.krk_curriculum import KRK_STAGES

    candidates = [stage for stage in KRK_STAGES if stage.name in set(stage_names)]
    if not candidates:
        raise ValueError(f"No KRK curriculum stages found for {tuple(stage_names)}")
    import random

    positions = []
    for stage in candidates:
        for pos in stage.positions:
            board = chess.Board(pos.fen)
            if board.turn == chess.WHITE and board.is_valid() and not board.is_game_over():
                positions.append(board)
    if not positions:
        raise ValueError(f"No valid KRK curriculum positions found for {tuple(stage_names)}")
    return random.choice(positions).copy(stack=False)

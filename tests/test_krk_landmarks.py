import chess
import importlib.util
import random
import sys
from pathlib import Path

from recon_lite_chess.baseline_teacher import KRKTeacher
from recon_lite_chess.training.krk_landmarks import (
    RICH_FEATURE_NAMES,
    landmark_reward,
    rich_feature_dict,
    specs_through,
)

_landmark_eval = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location(
        "test_krk_landmark_progress_script",
        Path(__file__).resolve().parents[1] / "scripts" / "test_krk_landmark_progress.py",
    )
)
assert _landmark_eval.__spec__ is not None
assert _landmark_eval.__spec__.loader is not None
sys.modules["test_krk_landmark_progress_script"] = _landmark_eval
_landmark_eval.__spec__.loader.exec_module(_landmark_eval)


def test_rich_feature_teacher_contract():
    teacher = KRKTeacher(feature_set="krk_rich_v1")
    board = chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")

    features = teacher.features(board)

    assert teacher.feature_dim == len(RICH_FEATURE_NAMES)
    assert len(features) == len(RICH_FEATURE_NAMES)
    assert teacher.feature_names == RICH_FEATURE_NAMES
    assert teacher.goal_feature_index == RICH_FEATURE_NAMES.index("is_checkmate")


def test_drive_to_edge_reward_improves_when_enemy_king_reaches_rim():
    before = chess.Board("8/8/8/8/3k4/8/8/R3K3 w - - 0 1")
    after = chess.Board("8/8/8/8/k7/8/8/R3K3 b - - 0 1")

    assert before.is_valid()
    assert after.is_valid()
    assert rich_feature_dict(before)["enemy_king_edge_distance"] > rich_feature_dict(after)["enemy_king_edge_distance"]
    assert landmark_reward(before, after, "drive_to_edge") > 0.0


def test_fence_reward_positive_when_safe_cut_is_gained():
    before = chess.Board("8/8/8/8/3k4/8/8/R3K3 w - - 0 1")
    after = chess.Board("8/8/8/8/3k4/8/8/3RK3 b - - 0 1")

    assert before.is_valid()
    assert after.is_valid()
    assert not rich_feature_dict(before)["cut_established"]
    assert rich_feature_dict(after)["cut_established"]
    assert landmark_reward(before, after, "fence_established") > 0.0


def test_box_reward_penalizes_box_growth():
    before = chess.Board("8/8/8/8/k7/8/1R6/4K3 w - - 0 1")
    after = chess.Board("8/8/8/8/k6R/8/8/4K3 b - - 0 1")

    assert before.is_valid()
    assert after.is_valid()
    assert rich_feature_dict(after)["box_area"] > rich_feature_dict(before)["box_area"]
    assert landmark_reward(before, after, "box_shrink") < 0.0


def test_landmark_stage_specs_are_ordered_after_stage_one():
    specs = specs_through(4)

    assert [spec.stage_index for spec in specs] == [2, 3, 4]
    assert [spec.label for spec in specs] == [
        "edge_trap",
        "fence_established",
        "drive_to_edge",
    ]


def test_landmark_eval_uses_stage_sources_for_label():
    assert _landmark_eval.source_stage_names_for_label("edge_trap") == (
        "Edge_Trap_Close",
        "Edge_Trap_Enemy_Between",
        "Edge_Trap_Wrong_Tempo",
    )
    assert _landmark_eval.source_stage_names_for_label("full_krk") == ("Full_KRK",)


def test_landmark_eval_black_reply_policy_returns_legal_move():
    rng = random.Random(7)
    board = chess.Board("8/8/8/8/3k4/8/8/R3K3 b - - 0 1")

    reply = _landmark_eval.choose_black_reply(rng, board, "drive_to_edge", "adversarial")

    assert reply in board.legal_moves

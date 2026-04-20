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
from recon_lite_chess.training.adaptive_curriculum import (
    StagePassCriteria,
    evaluate_pass_criteria,
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
        "edge_trap_close",
        "edge_trap_enemy_between",
        "edge_trap_wrong_tempo",
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


def test_split_edge_trap_labels_share_edge_trap_reward_family():
    before = chess.Board("8/8/8/8/3k4/8/8/R3K3 w - - 0 1")
    after = chess.Board("8/8/8/8/k7/8/8/R3K3 b - - 0 1")

    assert landmark_reward(before, after, "edge_trap_close") == landmark_reward(before, after, "edge_trap")
    assert landmark_reward(before, after, "edge_trap_enemy_between") == landmark_reward(before, after, "edge_trap")
    assert landmark_reward(before, after, "edge_trap_wrong_tempo") == landmark_reward(before, after, "edge_trap")


def test_stage_pass_criteria_reports_handoff_or_conversion():
    criteria = StagePassCriteria(
        min_improved_rate=0.70,
        max_worsened_rate=0.20,
        min_avg_reward=0.0,
        min_mate_playout_rate=0.65,
        max_draw_rate=0.10,
        max_max_plies_rate=0.25,
    )
    metrics = {
        "total": 100,
        "improved": 80,
        "worsened": 10,
        "avg_reward": 0.1,
        "playouts": {"mate": 40, "draw": 5, "max_plies": 55},
    }

    one_ply_passed, conversion_passed, reasons, conversion_reasons = evaluate_pass_criteria(metrics, criteria)

    assert one_ply_passed is True
    assert conversion_passed is False
    assert reasons == []
    assert "handoff_or_conversion" in conversion_reasons


def test_stage_pass_criteria_reports_conversion_not_checked_without_playouts():
    criteria = StagePassCriteria(
        min_improved_rate=0.70,
        max_worsened_rate=0.20,
        min_avg_reward=0.0,
        min_mate_playout_rate=0.65,
        max_draw_rate=0.10,
        max_max_plies_rate=0.25,
    )
    metrics = {
        "total": 100,
        "improved": 100,
        "worsened": 0,
        "avg_reward": 0.1,
        "playouts": {},
    }

    one_ply_passed, conversion_passed, reasons, conversion_reasons = evaluate_pass_criteria(metrics, criteria)

    assert one_ply_passed is True
    assert conversion_passed is False
    assert reasons == []
    assert conversion_reasons == ["conversion_not_checked"]

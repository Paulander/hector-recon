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
    select_stage_position,
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


def test_select_stage_position_filters_invalid_stage_fens():
    for _ in range(20):
        board = select_stage_position(("Fence_Established", "Anchored_Cut", "Edge_Cut_Hold"))
        assert board.turn == chess.WHITE
        assert board.is_valid()
        assert not board.is_game_over()


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


def test_make_eval_result_reports_conversion_status_not_checked():
    from recon_lite_chess.training.adaptive_curriculum import make_eval_result

    criteria = StagePassCriteria(
        min_improved_rate=0.70,
        max_worsened_rate=0.20,
        min_avg_reward=0.0,
        min_mate_playout_rate=0.65,
    )
    metrics = {
        "total": 100,
        "improved": 100,
        "worsened": 0,
        "avg_reward": 0.1,
        "playouts": {},
    }

    result = make_eval_result("fence_established", 9, metrics, criteria)

    assert result.one_ply_status == "passed"
    assert result.conversion_status == "not_checked"
    assert result.conversion_passed is False
    assert result.passed is False


def test_make_eval_result_requires_conversion_when_conversion_criteria_exist():
    from recon_lite_chess.training.adaptive_curriculum import make_eval_result

    criteria = StagePassCriteria(
        min_improved_rate=0.70,
        max_worsened_rate=0.20,
        min_avg_reward=0.0,
        min_mate_playout_rate=0.65,
        max_max_plies_rate=0.25,
    )
    metrics = {
        "total": 100,
        "improved": 100,
        "worsened": 0,
        "avg_reward": 0.1,
        "playouts": {"mate": 50, "max_plies": 50},
    }

    result = make_eval_result("drive_to_edge", 9, metrics, criteria)

    assert result.one_ply_status == "passed"
    assert result.conversion_status == "failed"
    assert result.conversion_passed is False
    assert result.passed is False


def test_late_krk_landmark_pass_criteria_include_conversion():
    import importlib.util

    module_path = Path(__file__).resolve().parents[1] / "scripts" / "train_baseline_krk_chain.py"
    spec = importlib.util.spec_from_file_location("train_baseline_krk_chain_for_criteria", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["train_baseline_krk_chain_for_criteria"] = module
    spec.loader.exec_module(module)

    criteria = module.pass_criteria_for_label("drive_to_edge")

    assert criteria.min_mate_playout_rate == 0.65
    assert criteria.max_max_plies_rate == 0.25


def test_post_break_candidate_terms_identify_fast_king_support_move():
    sys.modules.setdefault("test_krk_landmark_progress", _landmark_eval)
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_post_break_continuation.py"
    spec = importlib.util.spec_from_file_location("audit_krk_post_break_for_terms", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["audit_krk_post_break_for_terms"] = module
    spec.loader.exec_module(module)

    board = chess.Board("5k2/8/8/K7/7R/8/8/8 w - - 18 10")
    audit = {
        "source_terms": ["escapes_rook_oscillation_pair", "rook_safe_after_move"],
        "current_box_area": 24,
        "post_box_area": 24,
        "current_enemy_edge_distance": 0,
        "post_enemy_edge_distance": 0,
    }

    terms = module._post_break_candidate_terms(board, "a5b6", audit)

    assert "post_break_king_move" in terms
    assert "post_break_king_moves_toward_enemy" in terms
    assert "post_break_king_moves_toward_rook_support" in terms
    assert "post_break_box_unchanged" in terms


def test_candidate_horizon_summary_cross_tabs_converter_terms():
    sys.modules.setdefault("test_krk_landmark_progress", _landmark_eval)
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_post_break_continuation.py"
    spec = importlib.util.spec_from_file_location("audit_krk_post_break_for_summary", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["audit_krk_post_break_for_summary"] = module
    spec.loader.exec_module(module)

    candidates = [
        {
            "move": "a5b6",
            "candidate_terms": ["post_break_king_move", "post_break_king_moves_toward_enemy"],
            "outcomes_by_horizon": {"21": "mate", "40": "mate"},
        },
        {
            "move": "h4f4",
            "candidate_terms": ["post_break_rook_move"],
            "outcomes_by_horizon": {"21": "max_plies", "40": "mate"},
        },
    ]

    summary = module._candidate_horizon_summary(candidates, [21, 40], selected_break_move="h4f4")

    assert summary["loop_breaking_moves_that_convert_by_horizon"]["21"] == ["a5b6"]
    assert summary["fastest_mating_horizon_by_move"] == {"a5b6": 21, "h4f4": 40}
    assert summary["selected_break_move_outcomes"]["fastest_mating_horizon"] == 40
    assert summary["term_outcomes_by_horizon"]["21"]["post_break_king_move"]["mate"] == 1


def test_augment_existing_post_break_audit_adds_candidate_terms():
    sys.modules.setdefault("test_krk_landmark_progress", _landmark_eval)
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_post_break_continuation.py"
    spec = importlib.util.spec_from_file_location("audit_krk_post_break_for_augment", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["audit_krk_post_break_for_augment"] = module
    spec.loader.exec_module(module)

    payload = {
        "first_stagnation_breaker_state": "5k2/8/8/K7/7R/8/8/8 w - - 18 10",
        "first_stagnation_breaker_event": {"move": "h4f4"},
        "horizons": [21],
        "licensed_loop_breaking_moves": [
            {
                "move": "a5b6",
                "source_terms": ["rook_safe_after_move"],
                "outcomes_by_horizon": {"21": "mate"},
            }
        ],
    }

    output = module._augment_existing_audit(payload)

    candidate = output["licensed_loop_breaking_moves"][0]
    assert "post_break_king_moves_toward_enemy" in candidate["candidate_terms"]
    assert output["augmented_with_candidate_terms"] is True
    assert output["loop_breaking_moves_that_convert_by_horizon"]["21"] == ["a5b6"]

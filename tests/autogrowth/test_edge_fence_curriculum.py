import json

import chess

from recon_lite_chess.autogrowth import (
    EdgeFenceCurriculumConfig,
    run_edge_fence_curriculum,
    validate_learner_record,
)
from recon_lite_chess.autogrowth.edge_fence_curriculum import (
    _cheap_action_assessment,
    _mate_reward,
    _non_mate_shaping,
)


def test_tg26_mate_reward_has_floor_and_no_fast_bonus() -> None:
    config = EdgeFenceCurriculumConfig(mate_reward=1.0, delta_moves=0.02, mate_reward_floor=0.30)

    assert _mate_reward(actual_white_moves=2, ideal_white_moves=4, config=config) == 1.0
    assert _mate_reward(actual_white_moves=4, ideal_white_moves=4, config=config) == 1.0
    assert _mate_reward(actual_white_moves=8, ideal_white_moves=4, config=config) == 0.92
    assert _mate_reward(actual_white_moves=100, ideal_white_moves=4, config=config) == 0.30


def test_tg26_non_mate_shaping_is_small_and_penalizes_regression() -> None:
    before = chess.Board("8/8/8/8/2K5/8/1R6/k7 w - - 0 1")
    preserved = chess.Board("8/8/8/8/2K5/1R6/8/k7 b - - 1 1")
    regressed = chess.Board("8/8/8/8/2K5/8/8/k6R b - - 1 1")

    preserved_score = _non_mate_shaping(
        before,
        preserved,
        preserved,
        confinement_regressed=False,
    )
    regressed_score = _non_mate_shaping(
        before,
        regressed,
        regressed,
        confinement_regressed=True,
    )

    assert -0.60 <= preserved_score <= 0.20
    assert -0.60 <= regressed_score <= 0.20
    assert regressed_score < preserved_score


def test_tg26b_cheap_safety_rejects_one_reply_rook_loss() -> None:
    board = chess.Board("4k3/8/3R4/6K1/8/8/8/8 w - - 0 1")
    move = chess.Move.from_uci("g5h4")
    score = _cheap_action_assessment(
        board,
        move,
        config=EdgeFenceCurriculumConfig(),
        ideal_white_moves=3,
    )

    assert score["safety_filter_rejected"] is True
    assert score["reason"] == "rook_loss_reply_risk"
    assert score["black_reply"] == "e8e7"


def test_tg26_smoke_artifact_contract_and_firewall(tmp_path) -> None:
    result = run_edge_fence_curriculum(
        config=EdgeFenceCurriculumConfig(
            seed=41,
            foundation_mate1_train_count=24,
            foundation_mate1_heldout_count=8,
            foundation_mate1_mirror_count=4,
            foundation_mate2_train_count=4,
            foundation_mate2_heldout_count=2,
            train_chunk_size=8,
            eval_window_size=4,
            max_chunks_per_stage=1,
            consecutive_pass_windows_required=1,
            edge_success_threshold=0.0,
            fence_success_threshold=0.0,
            mate1_regression_threshold=0.0,
            mate2_regression_threshold=0.0,
            max_generation_attempts=80_000,
            max_samples=2,
        )
    )
    output = result.write_json(tmp_path / "tg26_edge_fence.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg26c_edge_fence_handoff_curriculum.v0"
    assert payload["training_runway"]["uses_curriculum_as_experience_distribution"] is True
    assert payload["training_runway"]["handoff_candidate_filter_is_schedule_only"] is True
    assert payload["training_runway"]["curriculum_labels_learner_visible"] is False
    assert payload["training_runway"]["broad_random_krk_enabled"] is False
    assert payload["config"]["edge_generation_requires_handoff_candidate"] is True
    assert payload["config"]["fence_generation_requires_handoff_candidate"] is False
    assert payload["reward_policy"]["non_mate_uses_small_graded_shaping_only"] is True
    assert payload["local_recon_structure"]["foundation_reused"] is True
    assert len(payload["stages"]) == 2
    assert payload["stages"][0]["m3_update_count"] > 0
    assert payload["stages"][1]["m3_update_count"] > 0
    assert "scoring_cost" in payload["stages"][0]
    assert payload["stages"][0]["scoring_cost"]["cheap_scored_action_count"] > 0
    assert "failure_audit" in payload
    assert payload["failure_audit"]["summary"]["failure_slice_detail_available"] is True
    assert payload["decision"]["runtime_tablebase_or_dtm_move_source"] is False
    validate_learner_record(payload["rankers"]["edge_trap"]["top_nodes"])
    validate_learner_record(payload["rankers"]["fence_hold"]["top_nodes"])

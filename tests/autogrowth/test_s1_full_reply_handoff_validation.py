from pathlib import Path

from recon_lite_chess.autogrowth import (
    S1FullReplyHandoffValidationConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_s1_full_reply_handoff_validation,
)


def test_tg29n_smoke_validates_s1_full_reply_handoffs_without_shortcuts(tmp_path: Path) -> None:
    result = run_s1_full_reply_handoff_validation(
        config=S1FullReplyHandoffValidationConfig(
            base=TinyOnlineKRKEpisodeRunnerConfig(
                episode_count=2,
                max_white_moves_per_episode=2,
                foundation_mate1_train_count=4,
                foundation_mate1_heldout_count=2,
                foundation_mate2_train_count=1,
                foundation_mate2_heldout_count=1,
                bridge_frontier_train_count=0,
                bridge_frontier_heldout_count=0,
                generic_edge_train_count=0,
                generic_edge_heldout_count=0,
                staged_train_count=0,
                staged_heldout_count=0,
                staged_regression_count=0,
                staged_near_miss_count=0,
                near_miss_heldout_count=0,
                max_ablation_positions=0,
                max_foundation_sanity_positions=1,
                max_foundation_ablation_positions=1,
                max_samples=4,
                max_episode_ablation_count=1,
                schedule_names=("tg29l_minimal_real_context",),
                progress_output=str(tmp_path / "progress.json"),
            ),
            target_train_s1=1,
            target_heldout_s1=1,
            target_near_miss_s1=1,
            minimum_train_s1=1,
            minimum_heldout_s1=1,
            minimum_near_miss_s1=1,
            max_s1_per_slice=1,
            max_audited_candidates_per_s1=10,
            run_max3_diagnostic=False,
        )
    )

    output = result.write_json(tmp_path / "tg29n.json")
    decision = result.decision
    assert output.exists()
    assert decision["dataset_minimum_met"] is True
    assert decision["one_reply_later_failed_count"] >= 1
    assert decision["heldout_selected_one_reply_later_failed_count"] == 0
    assert decision["max2_episode_success_count"] == decision["max2_episode_count"]
    assert decision["rook_blunder_count"] == 0
    assert decision["illegal_move_count"] == 0
    assert decision["stalemate_count"] == 0
    assert decision["selected_arm_ablation_causal"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["validator_driven_runtime_selection"] is False
    assert decision["trajectory_labels_learner_visible"] is False

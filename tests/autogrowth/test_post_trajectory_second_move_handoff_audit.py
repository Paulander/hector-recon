from pathlib import Path

from recon_lite_chess.autogrowth import (
    PostTrajectorySecondMoveHandoffAuditConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_post_trajectory_second_move_handoff_audit,
)


def test_tg29m_smoke_repairs_lost_s1_second_move_without_shortcuts(tmp_path: Path) -> None:
    result = run_post_trajectory_second_move_handoff_audit(
        config=PostTrajectorySecondMoveHandoffAuditConfig(
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
        )
    )

    output = result.write_json(tmp_path / "tg29m.json")
    decision = result.decision
    assert output.exists()
    assert decision["repair_applied"] is True
    assert decision["s1_failure_bucket_before"] == "second_move_bridge_candidate_exists_but_lost_selection"
    assert decision["second_move_selected_before"] != decision["second_move_selected_after"]
    assert decision["max2_episode_success_count"] == decision["max2_episode_count"]
    assert decision["rook_blunder_count"] == 0
    assert decision["illegal_move_count"] == 0
    assert decision["stalemate_count"] == 0
    assert decision["second_move_repair_ablation_causal"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["trajectory_labels_learner_visible"] is False

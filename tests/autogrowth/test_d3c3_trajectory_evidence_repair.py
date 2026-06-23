from pathlib import Path

from recon_lite_chess.autogrowth import (
    D3C3TrajectoryEvidenceRepairConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_d3c3_trajectory_evidence_repair,
)


def test_tg29j_smoke_repairs_d3c3_microprobe_and_no_cheat_fields(tmp_path: Path) -> None:
    result = run_d3c3_trajectory_evidence_repair(
        config=D3C3TrajectoryEvidenceRepairConfig(
            base=TinyOnlineKRKEpisodeRunnerConfig(
                episode_count=1,
                max_white_moves_per_episode=1,
                foundation_mate1_train_count=4,
                foundation_mate1_heldout_count=2,
                foundation_mate2_train_count=1,
                foundation_mate2_heldout_count=1,
                bridge_frontier_train_count=1,
                bridge_frontier_heldout_count=1,
                generic_edge_train_count=1,
                generic_edge_heldout_count=1,
                staged_train_count=0,
                staged_heldout_count=0,
                staged_regression_count=0,
                staged_near_miss_count=0,
                near_miss_heldout_count=0,
                max_ablation_positions=0,
                max_foundation_sanity_positions=1,
                max_foundation_ablation_positions=1,
                max_samples=4,
                max_episode_ablation_count=0,
                schedule_names=("tg28h_mixed_balanced_baseline",),
                progress_output=str(tmp_path / "progress.json"),
            ),
        )
    )

    output = result.write_json(tmp_path / "tg29j.json")
    decision = result.decision
    assert output.exists()
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["trajectory_labels_learner_visible"] is False
    assert decision["e2d3_selected_after"] is True
    assert decision["d3c3_selected_after"] is True
    assert decision["known_trajectory_candidate_selected_after_count"] == 2

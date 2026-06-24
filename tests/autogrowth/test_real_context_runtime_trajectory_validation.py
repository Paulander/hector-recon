from pathlib import Path

from recon_lite_chess.autogrowth import (
    RealContextRuntimeTrajectoryValidationConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_real_context_runtime_trajectory_validation,
)


def test_tg29l_smoke_builds_real_context_and_selects_known_prefixes(tmp_path: Path) -> None:
    result = run_real_context_runtime_trajectory_validation(
        config=RealContextRuntimeTrajectoryValidationConfig(
            base=TinyOnlineKRKEpisodeRunnerConfig(
                episode_count=1,
                max_white_moves_per_episode=1,
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
            run_tiny_episode_check=False,
            run_minimal_ablations=True,
        )
    )

    output = result.write_json(tmp_path / "tg29l.json")
    decision = result.decision
    assert output.exists()
    assert decision["context_built"] is True
    assert decision["context_build_blocker"] is None
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["trajectory_labels_learner_visible"] is False
    assert decision["e2d3_real_context_selected"] is True
    assert decision["d3c3_real_context_selected"] is True
    assert decision["known_trajectory_real_context_selected_count"] == 2
    assert decision["trajectory_repair_connected_to_real_context"] is True
    assert decision["trajectory_repair_ablation_causal"] is True

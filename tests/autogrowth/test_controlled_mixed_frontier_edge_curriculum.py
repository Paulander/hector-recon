from pathlib import Path

from recon_lite_chess.autogrowth import (
    ControlledMixedFrontierEdgeCurriculumConfig,
    run_controlled_mixed_frontier_edge_curriculum,
)


def test_tg28h_smoke_reports_schedule_and_purity_fields(tmp_path: Path) -> None:
    result = run_controlled_mixed_frontier_edge_curriculum(
        config=ControlledMixedFrontierEdgeCurriculumConfig(
            foundation_mate1_train_count=4,
            foundation_mate1_heldout_count=2,
            foundation_mate2_train_count=1,
            foundation_mate2_heldout_count=1,
            bridge_frontier_train_count=1,
            bridge_frontier_heldout_count=1,
            generic_edge_safety_regression_count=1,
            max_cache_candidate_moves=3,
            max_ablation_positions=0,
            max_foundation_sanity_positions=1,
            max_foundation_ablation_positions=1,
            max_samples=4,
            replay_count=1,
            generic_edge_train_count=2,
            generic_edge_heldout_count=1,
            near_miss_train_count=1,
            near_miss_heldout_count=1,
            schedule_names=("mixed_balanced",),
            progress_output=str(tmp_path / "progress.json"),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG28h_controlled_mixed_frontier_edge_curriculum"
    assert Path(tmp_path / "progress.json").exists()
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["stage_labels_learner_visible"] is False
    assert decision["edge_fence_labels_learner_visible"] is False
    assert decision["bridge_labels_learner_visible"] is False
    assert decision["selected_training_schedule"].startswith("mixed")
    assert "mixed_balanced" in payload["schedule_comparison"]
    assert "mask_actuator_terminals" in payload["ablation_results"]
    assert "mask_edge_fence_terminals" in payload["ablation_results"]

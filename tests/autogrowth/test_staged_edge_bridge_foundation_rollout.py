from pathlib import Path

from recon_lite_chess.autogrowth import (
    StagedEdgeBridgeFoundationRolloutConfig,
    run_staged_edge_bridge_foundation_rollout,
)


def test_tg28i_smoke_reports_staged_metrics_and_purity_fields(tmp_path: Path) -> None:
    result = run_staged_edge_bridge_foundation_rollout(
        config=StagedEdgeBridgeFoundationRolloutConfig(
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
            near_miss_train_count=0,
            near_miss_heldout_count=0,
            staged_train_count=0,
            staged_heldout_count=0,
            staged_generation_multiplier=2,
            max_staged_source_positions=4,
            max_staged_first_move_candidates=2,
            max_staged_black_replies_after_edge=1,
            max_staged_black_replies_after_bridge=1,
            schedule_names=("tg28h_mixed_balanced_baseline", "mixed_balanced_plus_staged"),
            progress_output=str(tmp_path / "progress.json"),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG28i_staged_edge_bridge_foundation_rollout"
    assert Path(tmp_path / "progress.json").exists()
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["stage_labels_learner_visible"] is False
    assert decision["edge_fence_labels_learner_visible"] is False
    assert decision["bridge_labels_learner_visible"] is False
    assert "staged_any_reply_success_count" in decision
    assert "staged" in payload["selected_schedule"]
    assert "tg28h_mixed_balanced_baseline" in payload["schedule_comparison"]
    assert "mixed_balanced_plus_staged" in payload["schedule_comparison"]
    assert "mask_actuator_terminals" in payload["ablation_results"]

from pathlib import Path

from recon_lite_chess.autogrowth import (
    FullFrontierValidationNearMissConfig,
    run_full_frontier_validation_near_miss,
)


def test_tg28g_smoke_reports_validation_and_purity_fields(tmp_path: Path) -> None:
    result = run_full_frontier_validation_near_miss(
        config=FullFrontierValidationNearMissConfig(
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
            near_miss_heldout_count=1,
            generic_edge_fence_count=1,
            progress_output=str(tmp_path / "progress.json"),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG28g_full_frontier_validation_near_miss"
    assert Path(tmp_path / "progress.json").exists()
    assert decision["foundation_frozen"] is True
    assert decision["foundation_cache_used_as_memoized_graph_response"] is True
    assert decision["foundation_cache_used_as_provider"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["direct_provider_override"] is False
    assert decision["stage_labels_learner_visible"] is False
    assert decision["edge_fence_labels_learner_visible"] is False
    assert decision["bridge_labels_learner_visible"] is False
    assert "residual_selection_without_reply_envelope_count" in decision
    assert "near_miss_false_positive_count" in decision
    assert "generic_rook_blunder_count" in decision
    assert payload["residual_dependency_audit"]["instrumentation_repair_applied"] is True
    assert "disable_reply_envelope_foundation_checks" in payload["ablation_results"]

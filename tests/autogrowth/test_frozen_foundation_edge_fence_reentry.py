from pathlib import Path

from recon_lite_chess.autogrowth import (
    FrozenFoundationEdgeFenceReentryConfig,
    run_frozen_foundation_edge_fence_reentry,
)


def test_tg28a_smoke_reports_frozen_foundation_edge_fence_fields(tmp_path: Path) -> None:
    progress = tmp_path / "tg28a_progress.json"
    result = run_frozen_foundation_edge_fence_reentry(
        config=FrozenFoundationEdgeFenceReentryConfig(
            foundation_mate1_train_count=4,
            foundation_mate1_heldout_count=2,
            foundation_mate2_train_count=1,
            foundation_mate2_heldout_count=1,
            edge_fence_train_count=3,
            edge_fence_heldout_count=2,
            top_k_deep_foundation_checks=1,
            max_edge_candidates_per_position=3,
            max_ablation_positions=1,
            max_foundation_sanity_positions=1,
            max_foundation_ablation_positions=1,
            max_samples=4,
            replay_count=1,
            progress_output=str(progress),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG28a_frozen_foundation_edge_fence_reentry"
    assert progress.exists()
    for key in (
        "checkpoint_pass",
        "foundation_frozen",
        "foundation_m3_updates_during_edge_training",
        "foundation_m4_promotions_during_edge_training",
        "foundation_m3_updates_during_eval",
        "foundation_m4_promotions_during_eval",
        "foundation_mate1_accuracy",
        "foundation_mate2_conversion_rate",
        "foundation_replay_stability_pass",
        "edge_fence_train_count",
        "edge_fence_heldout_count",
        "edge_fence_success_rate",
        "edge_distance_improvement_rate",
        "confinement_area_improvement_rate",
        "black_king_mobility_reduction_rate",
        "rook_safety_rate",
        "stalemate_avoidance_rate",
        "rook_blunder_count",
        "after_state_foundation_reachable_count",
        "foundation_handoff_conversion_count",
        "same_graph_foundation_continuation_count",
        "selected_move_count",
        "null_move_count",
        "candidate_budget_used",
        "deep_reply_checks_run",
        "failure_bucket_counts",
        "scheduler_equivalence_mismatch_count",
        "m3_update_count_edge_fence_only",
        "m4_promotion_count_by_terminal_kind_edge_fence_only",
        "ablation_results",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "validator_skip_used_during_internal_handoff_eval",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "stage_labels_learner_visible",
        "edge_fence_labels_learner_visible",
        "direct_provider_override",
        "purity_boundary",
    ):
        assert key in decision
    assert decision["foundation_frozen"] is True
    assert decision["guard_used_during_runtime_choice"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["edge_fence_labels_learner_visible"] is False

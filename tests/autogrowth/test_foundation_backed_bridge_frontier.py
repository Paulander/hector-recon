from pathlib import Path

from recon_lite_chess.autogrowth import (
    FoundationBackedBridgeFrontierConfig,
    run_foundation_backed_bridge_frontier,
)


def test_tg28d_smoke_reports_foundation_backed_frontier_fields(tmp_path: Path) -> None:
    progress = tmp_path / "tg28d_progress.json"
    result = run_foundation_backed_bridge_frontier(
        config=FoundationBackedBridgeFrontierConfig(
            foundation_mate1_train_count=4,
            foundation_mate1_heldout_count=2,
            foundation_mate2_train_count=1,
            foundation_mate2_heldout_count=1,
            bridge_frontier_train_count=2,
            bridge_frontier_heldout_count=2,
            generic_edge_safety_regression_count=1,
            basin_random_count=2,
            max_cache_candidate_moves=3,
            max_ablation_positions=0,
            max_foundation_sanity_positions=1,
            max_foundation_ablation_positions=1,
            max_samples=4,
            replay_count=1,
            progress_output=str(progress),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG28d_foundation_backed_bridge_frontier"
    assert progress.exists()
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "foundation_frozen",
        "foundation_cache_state_count",
        "foundation_cache_query_count",
        "foundation_cache_hit_rate",
        "foundation_cache_live_mismatch_count",
        "foundation_cache_used_as_memoized_graph_response",
        "foundation_cache_used_as_provider",
        "foundation_m3_updates_during_bridge_training",
        "foundation_m4_promotions_during_bridge_training",
        "foundation_m3_updates_during_eval",
        "foundation_m4_promotions_during_eval",
        "foundation_mate1_accuracy",
        "foundation_mate2_conversion_rate",
        "foundation_positive_state_count",
        "bridge_frontier_generation_attempts",
        "bridge_frontier_generated_count",
        "all_reply_bridge_count",
        "partial_reply_bridge_count",
        "any_reply_bridge_count",
        "bridge_frontier_train_count",
        "bridge_frontier_heldout_count",
        "bridge_candidate_generated_count",
        "no_bridge_candidate_generated_count",
        "selected_move_count",
        "null_move_count",
        "reply_envelope_foundation_reachable_count",
        "reply_envelope_foundation_coverage_rate",
        "all_reply_foundation_bridge_success_count",
        "partial_reply_foundation_bridge_success_count",
        "foundation_handoff_conversion_count",
        "same_graph_foundation_continuation_count",
        "edge_fence_success_rate",
        "confinement_area_improvement_rate",
        "black_king_mobility_reduction_rate",
        "rook_blunder_count",
        "stalemate_avoidance_rate",
        "deep_reply_checks_run",
        "cache_queries_run",
        "timeout_count",
        "failure_bucket_counts",
        "scheduler_equivalence_mismatch_count",
        "edge_only_m3_update_count",
        "bridge_terminal_m3_update_count",
        "m4_promotion_count_by_terminal_kind_edge_bridge_only",
        "ablation_results",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "validator_skip_used_during_internal_handoff_eval",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "stage_labels_learner_visible",
        "edge_fence_labels_learner_visible",
        "bridge_labels_learner_visible",
        "direct_provider_override",
        "purity_boundary",
    ):
        assert key in decision
    assert decision["foundation_frozen"] is True
    assert decision["foundation_cache_used_as_memoized_graph_response"] is True
    assert decision["foundation_cache_used_as_provider"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["bridge_labels_learner_visible"] is False

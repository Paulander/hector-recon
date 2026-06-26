from pathlib import Path

from recon_lite_chess.autogrowth import (
    TightFollowupSuccessBasinCoverageConfig,
    run_tight_followup_success_basin_coverage,
)


def test_tg29y_tightens_followup_success_without_unfreezing_foundation(tmp_path: Path) -> None:
    result = run_tight_followup_success_basin_coverage(
        config=TightFollowupSuccessBasinCoverageConfig(
            base=TightFollowupSuccessBasinCoverageConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            boundary_pool_path=str(tmp_path / "boundary.jsonl"),
            boundary_pool_index_path=str(tmp_path / "boundary_index.json"),
        )
    )

    output = result.write_json(tmp_path / "tg29y.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert Path(result.config.boundary_pool_path).exists()
    assert Path(result.config.boundary_pool_index_path).exists()

    required = {
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "old_followup_success_count",
        "tightened_followup_success_count",
        "old_success_reclassified_as_weak_count",
        "old_success_reclassified_as_basin_miss_count",
        "weak_followup_support_count",
        "reply_fragile_support_count",
        "one_reply_foundation_hint_count",
        "basin_boundary_hint_count",
        "false_followup_success_count",
        "basin_boundary_pool_entry_count",
        "inside_frozen_foundation_basin_count",
        "basin_boundary_with_partial_support_count",
        "bridge_frontier_not_foundation_count",
        "outside_frozen_foundation_basin_count",
        "foundation_response_present_count",
        "same_graph_foundation_continuation_count",
        "all_reply_foundation_count",
        "partial_reply_foundation_count",
        "worst_reply_foundation_failure_count",
        "missing_evidence_family_counts",
        "followup_success_metric_too_weak_count",
        "foundation_basin_too_narrow_count",
        "bridge_frontier_coverage_gap_count",
        "no_safe_chain_to_basin_count",
        "better_chain_exists_but_not_materialized_count",
        "better_chain_exists_but_lost_selection_count",
        "targeted_episode_count",
        "targeted_episode_success_count",
        "targeted_episode_success_rate",
        "targeted_success_delta_vs_tg29x",
        "max4_success_rate",
        "max5_success_rate",
        "max6_success_rate",
        "max_move_reached_count",
        "foundation_handoff_count",
        "s1_handoff_count",
        "basin_miss_chain_count",
        "false_success_chain_count",
        "rook_blunder_count",
        "illegal_move_count",
        "stalemate_count",
        "unsafe_move_count",
        "decoy_correct_rejection_count",
        "decoy_false_handoff_count",
        "near_miss_false_positive_count",
        "foundation_frozen",
        "foundation_mate1_accuracy",
        "foundation_mate2_conversion_rate",
        "foundation_cache_live_mismatch_count",
        "foundation_m3_updates_during_training",
        "foundation_m4_promotions_during_training",
        "foundation_m3_updates_during_eval",
        "foundation_m4_promotions_during_eval",
        "shadow_child_foundation_used",
        "shadow_child_foundation_used_in_main_eval",
        "foundation_unfrozen_in_main_arm",
        "foundation_sanity_pass",
        "known_trajectory_microprobe_pass",
        "s1_full_reply_validation_pass",
        "frontier_regression_pass",
        "staged_regression_pass",
        "staged_near_miss_regression_pass",
        "generic_edge_regression_pass",
        "decoy_rejection_pass",
        "failure_bucket_counts",
        "phase_timings",
        "scheduler_equivalence_mismatch_count",
        "ablation_results",
        "tight_followup_basin_repair_ablation_causal",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "trainer_side_exploration_used",
        "trainer_side_exploration_used_in_final_eval",
        "validator_skip_used_during_internal_handoff_eval",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "stage_labels_learner_visible",
        "edge_fence_labels_learner_visible",
        "bridge_labels_learner_visible",
        "staged_labels_learner_visible",
        "trajectory_labels_learner_visible",
        "s1_labels_learner_visible",
        "continuation_labels_learner_visible",
        "quality_tier_labels_learner_visible",
        "depth_labels_learner_visible",
        "reply_policy_labels_learner_visible",
        "basin_labels_learner_visible",
        "direct_provider_override",
        "purity_boundary",
    }
    assert required <= set(decision)
    assert decision["checkpoint_pass"] is True
    assert decision["repair_applied"] is False
    assert decision["selected_repair_arm"] == "boundary_pool_only"
    assert decision["old_followup_success_count"] == 1
    assert decision["tightened_followup_success_count"] == 0
    assert decision["false_followup_success_count"] == 1
    assert decision["basin_boundary_pool_entry_count"] == 6
    assert decision["basin_boundary_with_partial_support_count"] == 3
    assert decision["outside_frozen_foundation_basin_count"] == 3
    assert decision["targeted_episode_success_count"] == 0
    assert decision["decoy_false_handoff_count"] == 0
    assert decision["foundation_frozen"] is True
    assert decision["shadow_child_foundation_used"] is False
    assert decision["foundation_unfrozen_in_main_arm"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["basin_labels_learner_visible"] is False
    assert decision["direct_provider_override"] is False

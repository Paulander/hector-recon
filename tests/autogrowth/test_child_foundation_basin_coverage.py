from pathlib import Path

from recon_lite_chess.autogrowth import (
    ChildFoundationBasinCoverageConfig,
    run_child_foundation_basin_coverage_diagnostic,
)


def test_tg29z_child_foundation_diagnostic_keeps_parent_frozen(tmp_path: Path) -> None:
    result = run_child_foundation_basin_coverage_diagnostic(
        config=ChildFoundationBasinCoverageConfig(
            base=ChildFoundationBasinCoverageConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            child_pool_path=str(tmp_path / "child_pool.jsonl"),
            child_pool_index_path=str(tmp_path / "child_pool_index.json"),
        )
    )

    output = result.write_json(tmp_path / "tg29z.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert Path(result.config.child_pool_path).exists()
    assert Path(result.config.child_pool_index_path).exists()

    required = {
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "parent_boundary_state_count",
        "parent_recognized_boundary_count",
        "parent_unrecognized_boundary_count",
        "parent_partial_support_count",
        "parent_outside_basin_count",
        "child_branch_created",
        "child_parent_hash",
        "child_train_count",
        "child_heldout_count",
        "child_regression_count",
        "child_augmented_count",
        "child_m3_update_count",
        "child_m4_promotion_count",
        "child_node_count_delta",
        "child_edge_count_delta",
        "child_quorum_count",
        "child_terminal_count",
        "child_train_recognized_count",
        "child_heldout_recognized_count",
        "child_regression_recognized_count",
        "child_boundary_coverage_rate",
        "child_heldout_boundary_coverage_rate",
        "child_foundation_response_present_count",
        "child_same_graph_continuation_count",
        "child_all_reply_foundation_count",
        "child_partial_reply_foundation_count",
        "child_worst_reply_success_count",
        "child_false_positive_count",
        "child_decoy_false_handoff_count",
        "child_near_miss_false_positive_count",
        "shadow_child_used",
        "shadow_child_used_in_main_eval",
        "parent_main_targeted_success_count",
        "child_shadow_targeted_success_count",
        "child_shadow_foundation_handoff_count",
        "child_shadow_max_move_reached_count",
        "child_shadow_safety_failure_count",
        "child_shadow_decoy_false_handoff_count",
        "child_learns_boundary_cleanly_count",
        "child_learns_train_only_count",
        "child_fails_boundary_count",
        "child_learns_but_breaks_decoys_count",
        "missing_evidence_family_counts",
        "parent_sufficient_runtime_path_missed_count",
        "parent_foundation_frozen",
        "parent_foundation_m3_updates_during_child_training",
        "parent_foundation_m4_promotions_during_child_training",
        "parent_foundation_m3_updates_during_eval",
        "parent_foundation_m4_promotions_during_eval",
        "foundation_unfrozen_in_main_arm",
        "child_used_in_main_runtime",
        "child_used_in_shadow_only",
        "parent_foundation_sanity_pass",
        "child_foundation_sanity_pass",
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
        "child_foundation_coverage_ablation_causal",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "trainer_side_exploration_used",
        "trainer_side_exploration_used_in_final_eval",
        "shadow_child_foundation_used",
        "shadow_child_foundation_used_in_main_eval",
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
    assert decision["selected_repair_arm"] == "child_boundary_diagnostic_only"
    assert decision["parent_boundary_state_count"] == 6
    assert decision["parent_recognized_boundary_count"] == 0
    assert decision["parent_partial_support_count"] == 3
    assert decision["parent_outside_basin_count"] == 3
    assert decision["child_branch_created"] is True
    assert decision["child_train_count"] == 3
    assert decision["child_heldout_count"] == 2
    assert decision["child_regression_count"] == 1
    assert decision["child_train_recognized_count"] == 2
    assert decision["child_heldout_recognized_count"] == 0
    assert decision["child_learns_train_only_count"] == 1
    assert decision["child_false_positive_count"] == 0
    assert decision["child_decoy_false_handoff_count"] == 0
    assert decision["parent_foundation_frozen"] is True
    assert decision["foundation_unfrozen_in_main_arm"] is False
    assert decision["child_used_in_main_runtime"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["basin_labels_learner_visible"] is False
    assert decision["direct_provider_override"] is False

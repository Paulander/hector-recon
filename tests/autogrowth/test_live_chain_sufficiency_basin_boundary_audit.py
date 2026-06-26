from pathlib import Path

from recon_lite_chess.autogrowth import (
    LiveChainSufficiencyBasinBoundaryAuditConfig,
    run_live_chain_sufficiency_basin_boundary_audit,
)


def test_tg29x_audits_live_chain_boundary_without_shortcut_repair(tmp_path: Path) -> None:
    result = run_live_chain_sufficiency_basin_boundary_audit(
        config=LiveChainSufficiencyBasinBoundaryAuditConfig(
            base=LiveChainSufficiencyBasinBoundaryAuditConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            chain_cache_path=str(tmp_path / "chain.jsonl"),
            chain_cache_index_path=str(tmp_path / "chain_index.json"),
            basin_boundary_pool_path=str(tmp_path / "boundary.jsonl"),
            basin_boundary_pool_index_path=str(tmp_path / "boundary_index.json"),
        )
    )

    output = result.write_json(tmp_path / "tg29x.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert Path(result.config.chain_cache_path).exists()
    assert Path(result.config.chain_cache_index_path).exists()
    assert Path(result.config.basin_boundary_pool_path).exists()
    assert Path(result.config.basin_boundary_pool_index_path).exists()

    required = {
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "targeted_episode_count",
        "chain_trace_count",
        "mature_plus_followup_chain_count",
        "chain_reaches_foundation_count",
        "chain_reaches_s1_handoff_count",
        "chain_reaches_bridge_frontier_count",
        "chain_misses_basin_count",
        "chain_reply_fragile_count",
        "chain_horizon_insufficient_count",
        "chain_cache_live_mismatch_count",
        "inside_foundation_basin_count",
        "basin_boundary_count",
        "bridge_frontier_not_foundation_count",
        "outside_known_basin_count",
        "foundation_response_present_count",
        "same_graph_foundation_continuation_count",
        "chain_search_depth_max",
        "basin_reaching_chain_count_by_depth",
        "bridge_frontier_chain_count_by_depth",
        "reply_robust_chain_count_by_depth",
        "better_chain_exists_count",
        "better_chain_materialized_count",
        "better_chain_selected_count",
        "no_safe_chain_to_basin_count",
        "cache_live_mismatch_count",
        "chain_not_sufficient_count",
        "followup_success_metric_too_weak_count",
        "bridge_frontier_found_but_foundation_unrecognized_count",
        "foundation_basin_too_narrow_count",
        "reply_policy_escape_count",
        "better_chain_exists_but_not_materialized_count",
        "better_chain_exists_but_lost_selection_count",
        "no_safe_chain_to_basin_found_count",
        "horizon_too_short_after_all_count",
        "bridge_frontier_boundary_pool_entry_count",
        "targeted_episode_success_count",
        "targeted_episode_success_rate",
        "targeted_success_delta_vs_tg29w",
        "max4_success_rate",
        "max5_success_rate",
        "max6_success_rate",
        "max7_diagnostic_success_rate",
        "max8_diagnostic_success_rate",
        "max_move_reached_count",
        "foundation_handoff_count",
        "s1_handoff_count",
        "rook_blunder_count",
        "illegal_move_count",
        "stalemate_count",
        "unsafe_move_count",
        "decoy_correct_rejection_count",
        "decoy_false_handoff_count",
        "near_miss_false_positive_count",
        "chain_overactivation_on_decoy_count",
        "foundation_frozen",
        "foundation_mate1_accuracy",
        "foundation_mate2_conversion_rate",
        "foundation_cache_live_mismatch_count",
        "foundation_m3_updates_during_training",
        "foundation_m4_promotions_during_training",
        "foundation_m3_updates_during_eval",
        "foundation_m4_promotions_during_eval",
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
        "chain_sufficiency_repair_ablation_causal",
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
    assert decision["chain_trace_count"] == 2
    assert decision["mature_plus_followup_chain_count"] == 1
    assert decision["chain_cache_live_mismatch_count"] == 0
    assert decision["targeted_episode_success_count"] == 0
    assert decision["decoy_false_handoff_count"] == 0
    assert decision["foundation_frozen"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["reply_policy_labels_learner_visible"] is False
    assert decision["basin_labels_learner_visible"] is False
    assert decision["direct_provider_override"] is False

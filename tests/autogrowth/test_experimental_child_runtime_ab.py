from pathlib import Path

from recon_lite_chess.autogrowth import (
    ExperimentalChildRuntimeABConfig,
    run_experimental_child_runtime_ab,
)


def test_tg33_experimental_child_runtime_ab_smoke(tmp_path: Path) -> None:
    result = run_experimental_child_runtime_ab(
        config=ExperimentalChildRuntimeABConfig(
            base=ExperimentalChildRuntimeABConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            branch_online_results_path=str(tmp_path / "branch_results.jsonl"),
            child_intervention_log_path=str(tmp_path / "interventions.jsonl"),
            hard_decoy_stress_path=str(tmp_path / "hard_decoys.jsonl"),
            live_cache_samples_path=str(tmp_path / "live_cache.jsonl"),
            seed_count=5,
            target_tier=1,
        )
    )
    output = result.write_json(tmp_path / "tg33.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert Path(result.config.branch_online_results_path).exists()
    assert Path(result.config.child_intervention_log_path).exists()
    assert Path(result.config.hard_decoy_stress_path).exists()
    assert Path(result.config.live_cache_samples_path).exists()

    required = {
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "branch_count",
        "branch_names",
        "selected_experimental_branch",
        "selected_experimental_branch_reason",
        "total_episode_count",
        "parent_main_success_count",
        "parent_main_success_rate",
        "child_shadow_success_count",
        "child_shadow_success_rate",
        "experimental_child_success_count",
        "experimental_child_success_rate",
        "experimental_child_success_delta_vs_parent",
        "success_by_branch_start_set",
        "success_by_branch_horizon",
        "success_by_branch_reply_policy",
        "worst_seed_experimental_success_rate",
        "mean_seed_experimental_success_rate",
        "std_seed_experimental_success_rate",
        "child_intervention_count",
        "child_intervention_rate",
        "child_changed_selected_move_count",
        "child_changed_outcome_count",
        "child_helped_success_count",
        "child_hurt_success_count",
        "child_no_effect_count",
        "child_false_handoff_count",
        "child_boundary_recognized_count",
        "child_boundary_recognized_and_helped_count",
        "child_boundary_recognized_but_no_online_success_count",
        "decoy_episode_count",
        "hard_decoy_episode_count",
        "parent_decoy_false_handoff_count",
        "parent_hard_decoy_false_handoff_count",
        "experimental_decoy_false_handoff_count",
        "experimental_hard_decoy_false_handoff_count",
        "rook_blunder_count_by_branch",
        "illegal_move_count_by_branch",
        "stalemate_count_by_branch",
        "unsafe_move_count_by_branch",
        "live_cache_sample_count",
        "parent_cache_live_mismatch_count",
        "child_cache_live_mismatch_count",
        "reply_envelope_cache_live_mismatch_count",
        "actuator_cache_live_mismatch_count",
        "ablation_results",
        "child_runtime_ablation_causal",
        "parent_foundation_frozen",
        "parent_foundation_m3_updates_during_experiment",
        "parent_foundation_m4_promotions_during_experiment",
        "parent_foundation_m3_updates_during_eval",
        "parent_foundation_m4_promotions_during_eval",
        "foundation_unfrozen_in_main_arm",
        "parent_artifact_modified",
        "child_used_in_main_runtime",
        "child_used_in_experimental_runtime",
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
        "hard_decoy_rejection_pass",
        "failure_bucket_counts",
        "total_seconds",
        "requested_max_total_seconds",
        "requested_min_target_seconds",
        "long_run_short_finish_reason",
        "adaptive_stress_tiers_completed",
        "adaptive_stress_tiers_skipped",
        "scheduler_equivalence_mismatch_count",
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
    assert decision["branch_count"] == 7
    assert decision["total_episode_count"] == 200
    assert decision["experimental_child_success_delta_vs_parent"] > 0
    assert decision["child_intervention_count"] > 0
    assert decision["child_helped_success_count"] > 0
    assert decision["child_hurt_success_count"] == 0
    assert decision["experimental_decoy_false_handoff_count"] == 0
    assert decision["experimental_hard_decoy_false_handoff_count"] == 0
    assert decision["parent_cache_live_mismatch_count"] == 0
    assert decision["child_cache_live_mismatch_count"] == 0
    assert decision["reply_envelope_cache_live_mismatch_count"] == 0
    assert decision["actuator_cache_live_mismatch_count"] == 0
    assert decision["parent_foundation_frozen"] is True
    assert decision["foundation_unfrozen_in_main_arm"] is False
    assert decision["child_used_in_main_runtime"] is False
    assert decision["child_used_in_experimental_runtime"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["basin_labels_learner_visible"] is False
    assert decision["direct_provider_override"] is False

import gzip
from pathlib import Path

from recon_lite_chess.autogrowth import (
    DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY,
    FeatureFlaggedChildConsensusRuntimeCanaryConfig,
    decide_child_consensus_runtime,
    run_feature_flagged_child_consensus_runtime_canary,
)


def test_child_consensus_runtime_policy_default_and_explicit() -> None:
    evidence = {
        "parent_partial_support": True,
        "child_boundary_recognition": True,
        "child_consensus_evidence": True,
        "child_foundation_response": True,
        "child_same_graph_continuation": True,
        "child_shared_atom_support": True,
        "child_boundary_quorum_activation": True,
        "child_actuator_confirmation": True,
        "reply_envelope_robust": True,
    }
    default = decide_child_consensus_runtime(evidence=evidence)
    canary = decide_child_consensus_runtime(policy_name="child_consensus_canary_balanced", evidence=evidence)
    assert DEFAULT_CHILD_CONSENSUS_RUNTIME_POLICY == "parent_only"
    assert default.final_selected_move == "parent_terminal"
    assert default.child_used_in_main_runtime is False
    assert canary.final_selected_move == "experimental_child_terminal"
    assert canary.child_used_in_experimental_runtime is True


def test_tg35_feature_flagged_child_consensus_runtime_canary_smoke(tmp_path: Path) -> None:
    result = run_feature_flagged_child_consensus_runtime_canary(
        config=FeatureFlaggedChildConsensusRuntimeCanaryConfig(
            base=FeatureFlaggedChildConsensusRuntimeCanaryConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            branch_online_results_path=str(tmp_path / "branch.jsonl.gz"),
            paired_ab_results_path=str(tmp_path / "paired.jsonl.gz"),
            child_intervention_log_path=str(tmp_path / "interventions.jsonl.gz"),
            hard_decoy_stress_path=str(tmp_path / "hard.jsonl.gz"),
            live_cache_samples_path=str(tmp_path / "live.jsonl.gz"),
            canary_gate_log_path=str(tmp_path / "gates.jsonl.gz"),
            artifact_index_path=str(tmp_path / "index.json"),
            episode_tier_start=500,
            episode_tier_max=500,
            seed_count=5,
            live_cache_sample_target=250,
            parity_episode_count=250,
            target_tier=1,
        )
    )
    output = result.write_json(tmp_path / "tg35.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    for path in (
        result.config.branch_online_results_path,
        result.config.paired_ab_results_path,
        result.config.child_intervention_log_path,
        result.config.hard_decoy_stress_path,
        result.config.live_cache_samples_path,
        result.config.canary_gate_log_path,
    ):
        assert Path(path).exists()
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            assert fh.readline()

    required = {
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "artifact_hygiene_applied",
        "large_log_policy",
        "largest_committed_file_bytes",
        "runtime_policy_installed",
        "default_runtime_policy",
        "canary_runtime_policy_name",
        "parent_only_default_unchanged",
        "selected_canary_branch",
        "selected_canary_branch_reason",
        "parity_episode_count",
        "parity_selected_move_match_count",
        "parity_selected_move_mismatch_count",
        "parity_outcome_match_count",
        "parity_outcome_mismatch_count",
        "total_episode_count",
        "paired_episode_count",
        "parent_main_success_count",
        "parent_main_success_rate",
        "canary_success_count",
        "canary_success_rate",
        "canary_success_delta_vs_parent",
        "paired_parent_success_child_success_count",
        "paired_parent_success_child_failure_count",
        "paired_parent_failure_child_success_count",
        "paired_parent_failure_child_failure_count",
        "paired_help_count",
        "paired_hurt_count",
        "paired_net_help",
        "paired_help_hurt_ratio",
        "paired_success_delta",
        "child_intervention_count",
        "child_intervention_rate",
        "child_changed_selected_move_count",
        "child_changed_outcome_count",
        "child_helped_success_count",
        "child_hurt_success_count",
        "child_no_effect_count",
        "child_false_handoff_count",
        "gate_open_count",
        "gate_closed_count",
        "gate_open_help_count",
        "gate_open_hurt_count",
        "gate_closed_missed_help_count",
        "gate_false_open_count",
        "gate_false_close_count",
        "gate_precision",
        "gate_recall_against_helpful_interventions",
        "gate_closed_reason_counts",
        "decoy_episode_count",
        "hard_decoy_episode_count",
        "child_confusable_decoy_episode_count",
        "parent_decoy_false_handoff_count",
        "parent_hard_decoy_false_handoff_count",
        "canary_decoy_false_handoff_count",
        "canary_hard_decoy_false_handoff_count",
        "rook_blunder_count_by_branch",
        "illegal_move_count_by_branch",
        "stalemate_count_by_branch",
        "unsafe_move_count_by_branch",
        "live_cache_sample_count",
        "parent_cache_live_mismatch_count",
        "child_cache_live_mismatch_count",
        "reply_envelope_cache_live_mismatch_count",
        "actuator_cache_live_mismatch_count",
        "rollback_test_count",
        "rollback_test_pass_count",
        "failclosed_test_count",
        "failclosed_test_pass_count",
        "child_disabled_matches_parent",
        "cache_unavailable_falls_back",
        "uncertainty_falls_back",
        "decoy_veto_blocks_child",
        "hard_decoy_veto_blocks_child",
        "ablation_results",
        "canary_runtime_ablation_causal",
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
    assert decision["checkpoint_interpretation"] == "feature_flagged_canary_ready"
    assert decision["runtime_policy_installed"] is True
    assert decision["default_runtime_policy"] == "parent_only"
    assert decision["parent_only_default_unchanged"] is True
    assert decision["paired_episode_count"] == 500
    assert decision["total_episode_count"] == 2500
    assert decision["paired_help_count"] > decision["paired_hurt_count"]
    assert decision["paired_hurt_count"] == 0
    assert decision["parity_selected_move_mismatch_count"] == 0
    assert decision["parity_outcome_mismatch_count"] == 0
    assert decision["parity_gate_mismatch_count"] == 0
    assert decision["canary_decoy_false_handoff_count"] == 0
    assert decision["canary_hard_decoy_false_handoff_count"] == 0
    assert decision["live_cache_sample_count"] >= 250
    assert decision["parent_cache_live_mismatch_count"] == 0
    assert decision["child_cache_live_mismatch_count"] == 0
    assert decision["rollback_test_pass_count"] == decision["rollback_test_count"]
    assert decision["failclosed_test_pass_count"] == decision["failclosed_test_count"]
    assert decision["parent_foundation_frozen"] is True
    assert decision["foundation_unfrozen_in_main_arm"] is False
    assert decision["child_used_in_main_runtime"] is False
    assert decision["child_used_in_experimental_runtime"] is True
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["basin_labels_learner_visible"] is False
    assert decision["direct_provider_override"] is False

#!/usr/bin/env python3
"""Tests for passive KRK suite gate advancement."""

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_advance = _load_module(
    "advance_krk_suite_from_current_gates_v0",
    "scripts/advance_krk_suite_from_current_gates_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_suite_gate_advancement_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_gate_advancement_artifact_is_passive_and_boundary_clean():
    payload = _read_report()

    assert payload["schema_version"] == "krk_suite_gate_advancement.v0"
    assert payload["causal_status"] == "non_causal_passive_gate_advancement"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["all_boundaries_preserved"] is True

    decision = payload["decision"]
    assert decision["runtime_changes_allowed"] is False
    assert decision["label_run_allowed"] is False
    assert decision["selector_allowed"] is False
    assert decision["selector_training_allowed"] is False
    assert decision["stage7_promotion_allowed"] is False
    assert decision["stage8_training_allowed"] is False


def test_gate_advancement_reports_current_stage7_blocker():
    payload = _read_report()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_ready_for_protected_failure_contrast_collection"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["summary"]["stage7_success_controls"] == 11
    assert (
        payload["summary"]["protected_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["summary"]["protected_stack_ready"] is True
    assert payload["summary"]["protected_stack_rollback_paths_preserved"] is True
    assert payload["summary"]["protected_stack_active_paths_safe"] is True
    assert payload["summary"]["protected_stack_active_paths_exist"] is True
    assert payload["summary"]["protected_stack_rollback_paths_safe"] is True
    assert payload["summary"]["protected_stack_rollback_paths_exist"] is True
    assert payload["summary"]["protected_stack_rollback_common_paths_distinct"] is True
    assert payload["summary"]["protected_stack_filesystem_snapshots_replaced"] is False
    assert payload["summary"]["clean_curriculum_run_lineage_passive_ready"] is True
    assert (
        payload["summary"]["clean_curriculum_checkpoint_plan_status"]
        == "clean_curriculum_checkpoint_plan_ready_full_run_requires_review"
    )
    assert (
        payload["summary"]["clean_curriculum_execution_manifest_status"]
        == "clean_retrain_execution_manifest_ready_not_run"
    )
    assert (
        payload["summary"]["clean_curriculum_execution_manifest_full_run_authorized"]
        is False
    )
    assert (
        payload["summary"]["clean_curriculum_preflight_status"]
        == "clean_retrain_preflight_ready_for_run_review"
    )
    assert payload["summary"]["clean_curriculum_preflight_blocker_count"] == 0
    assert (
        payload["summary"]["clean_curriculum_smoke_result_status"]
        == "clean_retrain_smoke_plumbing_passed_semantic_smoke_too_tiny"
    )
    assert (
        payload["summary"]["clean_curriculum_initial_run_status"]
        == "clean_retrain_full_run_incomplete_stage2a_no_promotable_checkpoint"
    )
    assert payload["summary"]["clean_curriculum_initial_run_complete"] is False
    assert (
        payload["summary"]["clean_curriculum_retry1_status"]
        == "clean_retrain_retry1_completed_through_stage6_overlay_compose_basic_checks_passed"
    )
    assert (
        payload["summary"]["clean_curriculum_retry1_complete_through_stage6"]
        is True
    )
    assert (
        payload["summary"]["clean_curriculum_retry1_promoted_by_this_artifact"]
        is False
    )
    assert (
        payload["summary"]["clean_curriculum_guardrail_status"]
        == "clean_retrain_retry1_stage6_overlay_quarantined_guardrails_partial"
    )
    assert (
        payload["summary"]["clean_curriculum_stage6_gap_status"]
        == "stage6_gap_explained_by_validation_profile_mismatch"
    )
    assert (
        payload["summary"]["clean_curriculum_stage5_control_debt_status"]
        == "stage5_one_ply_guardrail_control_debt_confirmed"
    )
    assert (
        payload["summary"]["clean_curriculum_stage4_caveat_control_status"]
        == "stage4_caveat_reproduces_in_base_control_no_overlay_regression"
    )
    assert payload["summary"]["clean_curriculum_stage7_promotion_allowed"] is False
    assert payload["summary"]["clean_curriculum_stage8_training_allowed"] is False
    assert payload["summary"]["strategy_sequence_architecture_passive_ready"] is True
    assert (
        payload["summary"]["strategy_sequence_architecture_review_status"]
        == "broader_krk_strategy_sequence_review_ready"
    )
    assert (
        payload["summary"]["strategy_sequence_architecture_runtime_work_allowed"]
        is False
    )
    assert payload["summary"]["strategy_sequence_architecture_next_objective_ids"] == [
        "strategy_ownership_evidence",
        "sequence_policy_evidence",
        "curriculum_boundary_evidence",
    ]
    assert (
        payload["summary"]["strategy_sequence_evidence_plan_status"]
        == "strategy_sequence_evidence_plan_defined"
    )
    assert (
        payload["summary"]["strategy_sequence_evidence_plan_runtime_work_allowed"]
        is False
    )
    assert (
        payload["summary"]["strategy_sequence_inventory_status"]
        == "replay_free_inventory_state_holdout_gap_blocks_runtime"
    )
    assert payload["summary"]["strategy_sequence_inventory_runtime_work_allowed"] is False
    assert payload["summary"]["strategy_sequence_inventory_clean_gate_closed"] is True
    assert (
        payload["summary"][
            "strategy_sequence_inventory_state_holdout_gap_blocks_runtime"
        ]
        is True
    )
    assert payload["summary"]["strategy_sequence_inventory_stage7_is_held_out"] is True
    assert payload["summary"]["strategy_sequence_runtime_selector_implemented"] is False
    assert payload["summary"]["strategy_sequence_stage7_promotion_allowed"] is False
    assert payload["summary"]["strategy_sequence_stage8_training_allowed"] is False
    assert payload["summary"]["strategy_owner_contrast_passive_probe_ready"] is True
    assert (
        payload["summary"]["strategy_owner_contrast_label_plan_status"]
        == "protected_strategy_owner_contrast_label_plan_defined_execution_review_required"
    )
    assert payload["summary"]["strategy_owner_contrast_label_plan_job_count"] == 12
    assert payload["summary"]["strategy_owner_contrast_label_plan_stage7_job_count"] == 0
    assert (
        payload["summary"]["strategy_owner_contrast_execution_manifest_status"]
        == "contrast_execution_manifest_bound_review_required"
    )
    assert payload["summary"]["strategy_owner_contrast_execution_manifest_stage7_jobs"] == 0
    assert payload["summary"]["strategy_owner_contrast_control_label_count"] == 12
    assert payload["summary"]["strategy_owner_contrast_control_label_stage7_count"] == 0
    assert (
        payload["summary"]["strategy_owner_contrast_dataset_status"]
        == "strategy_owner_contrast_dataset_ready_for_non_causal_probe_selector_sandbox_blocked"
    )
    assert payload["summary"]["strategy_owner_contrast_dataset_row_count"] == 13
    assert payload["summary"]["strategy_owner_contrast_dataset_stage7_training_rows"] == 0
    assert (
        payload["summary"]["strategy_owner_contrast_readiness_selector_sandbox_ready"]
        is False
    )
    assert (
        payload["summary"]["strategy_owner_contrast_probe_status"]
        == "strategy_owner_contrast_signal_present_selector_sandbox_blocked"
    )
    assert payload["summary"]["strategy_owner_contrast_probe_readiness_blockers"] == [
        "insufficient_selected_provider_family_diversity"
    ]
    assert (
        payload["summary"]["strategy_owner_contrast_runtime_arbiter_implemented"]
        is False
    )
    assert payload["summary"]["strategy_owner_contrast_runtime_terminals_added"] is False
    assert payload["summary"]["strategy_owner_contrast_stage7_promotion_allowed"] is False
    assert payload["summary"]["strategy_owner_contrast_stage8_training_allowed"] is False
    assert payload["summary"]["strategy_arbiter_trace_passive_ready"] is True
    assert (
        payload["summary"]["strategy_arbiter_trace_status"]
        == "labeled_controls_mixed_no_sandbox"
    )
    assert (
        payload["summary"]["strategy_arbiter_trace_sandbox_default_enabled"]
        is False
    )
    assert payload["summary"]["strategy_arbiter_trace_smoke_status"] == (
        "observability_skeleton_smoke_passed"
    )
    assert (
        payload["summary"]["strategy_arbiter_trace_smoke_runtime_arbiter_allowed"]
        is False
    )
    assert payload["summary"]["strategy_arbiter_trace_observation_frames_status"] == (
        "observation_frames_collected"
    )
    assert payload["summary"]["strategy_arbiter_trace_observation_frame_count"] == 12
    assert payload["summary"]["strategy_arbiter_trace_selector_probe_status"] == (
        "observation_selector_probe_underlabeled"
    )
    assert (
        payload["summary"]["strategy_arbiter_trace_selector_probe_underlabeled"]
        is True
    )
    assert payload["summary"]["strategy_arbiter_trace_labeled_probe_status"] == (
        "labeled_controls_mixed_no_sandbox"
    )
    assert (
        payload["summary"]["strategy_arbiter_trace_labeled_probe_sandbox_ready"]
        is False
    )
    assert payload["summary"]["strategy_arbiter_trace_protected_matrix_status"] == (
        "protected_control_matrix_passed"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_trace_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_trace_gameplay_topology_mutation"]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_trace_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_trace_stage8_training_allowed"]
        is False
    )
    assert payload["summary"]["strategy_arbiter_semantics_passive_ready"] is True
    assert payload["summary"]["strategy_arbiter_semantics_status"] == (
        "selector_objective_and_label_semantics_review_required"
    )
    assert payload["summary"]["strategy_arbiter_semantics_risk_review_status"] == (
        "runtime_sandbox_blocked_pending_semantics_review"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_semantics_risk_runtime_sandbox_allowed"
        ]
        is False
    )
    assert payload["summary"]["strategy_arbiter_semantics_stratified_probe_status"] == (
        "protected_forced_controls_promising_stage7_gap_confirmed"
    )
    assert (
        payload["summary"]["strategy_arbiter_semantics_stratified_stage7_hit_rate"]
        == 0.5
    )
    assert (
        payload["summary"][
            "strategy_arbiter_semantics_architecture_review_status"
        ]
        == "trace_only_observability_skeleton_allowed"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_semantics_architecture_runtime_arbiter_allowed"
        ]
        is False
    )
    assert payload["summary"]["strategy_arbiter_semantics_sandbox_readiness_status"] == (
        "readiness_criteria_defined_sandbox_still_blocked"
    )
    assert (
        payload["summary"]["strategy_arbiter_semantics_selector_sandbox_ready"]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_semantics_control_plane_labeled_controls"
        ]
        == "mixed"
    )
    assert payload["summary"]["strategy_arbiter_semantics_control_plane_stage7"] == (
        "held_out_unlabeled_challenge"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_semantics_control_plane_runtime_arbiter_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_semantics_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_semantics_gameplay_topology_mutation"]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_semantics_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_semantics_stage8_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_out_of_sample_passive_ready"]
        is True
    )
    assert payload["summary"]["strategy_arbiter_out_of_sample_plan_status"] == (
        "out_of_sample_control_plan_defined_execution_blocked"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_plan_execute_collection_now"
        ]
        is False
    )
    assert payload["summary"]["strategy_arbiter_out_of_sample_manifest_status"] == (
        "execution_manifest_ready_for_review"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_manifest_execute_labels_now"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_out_of_sample_manifest_job_count"]
        == 12
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_manifest_stage7_training_rows"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_manifest_review_status"
        ]
        == "execution_manifest_review_passed_bounded_label_run_allowed"
    )
    assert payload["summary"]["strategy_arbiter_out_of_sample_label_count"] == 12
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_label_stage7_training_rows"
        ]
        == 0
    )
    assert payload["summary"]["strategy_arbiter_out_of_sample_probe_status"] == (
        "out_of_sample_controls_guardrail_positive_selector_sandbox_blocked"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_probe_sandbox_blockers"
        ]
        == [
            "class_imbalance",
            "selected_provider_dominance",
        ]
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_probe_selected_provider_dominance"
        ]
        == 1.0
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_architecture_review_status"
        ]
        == "selector_sandbox_blocked_out_of_sample_controls_not_selector_diverse"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_architecture_selector_signal_status"
        ]
        == "not_ready_due_to_class_imbalance_and_provider_dominance"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_runtime_arbiter_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_out_of_sample_selector_sandbox_ready"]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_runtime_arbiter_implemented"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_gameplay_topology_mutation"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_out_of_sample_stage7_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_out_of_sample_stage8_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_runtime_no_scale_passive_ready"]
        is True
    )
    assert payload["summary"]["strategy_arbiter_runtime_no_scale_status"] == (
        "runtime_sandbox_safe_but_additive_support_not_ready_to_scale"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_default_off_design_status"
        ]
        == "default_off_strategy_arbiter_design_ready_for_external_review"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_runtime_review_packet_status"
        ]
        == "runtime_review_packet_ready"
    )
    assert (
        payload["summary"]["strategy_arbiter_runtime_no_scale_smoke_status"]
        == "runtime_sandbox_smoke_passed"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_protected_matrix_status"
        ]
        == "protected_control_matrix_v2_passed"
    )
    assert (
        payload["summary"]["strategy_arbiter_runtime_no_scale_stage7_holdout_status"]
        == "stage7_holdout_lock_passed"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_stage7_challenge_status"
        ]
        == "stage7_challenge_probe_no_regression"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_support_sensitivity_status"
        ]
        == "support_sensitivity_measured"
    )
    assert payload["summary"]["strategy_arbiter_runtime_no_scale_support_scale_risk"] == (
        "high_support_changes_protected_ownership_before_safe_stage7_evidence"
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_runtime_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_small_support_stage7_effective"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_high_support_scale_risk"
        ]
        is True
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_gameplay_topology_mutation"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_arbiter_runtime_no_scale_stage7_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_arbiter_runtime_no_scale_stage8_training_allowed"]
        is False
    )
    assert payload["summary"]["provider_identity_maturity_passive_ready"] is True
    assert payload["summary"]["provider_identity_maturity_status"] == (
        "provider_identity_signal_requires_provenance_decomposition"
    )
    assert payload["summary"]["provider_identity_maturity_row_count"] == 42
    assert (
        payload["summary"]["provider_identity_maturity_provider_prior_accuracy"]
        == 0.8333333333333334
    )
    assert (
        payload["summary"]["provider_identity_maturity_best_feature_probe_baseline"]
        == "provider_prior_loo"
    )
    assert payload["summary"]["provider_identity_maturity_provider_identity_signal"] == (
        "strong_but_not_causal_ready"
    )
    assert (
        payload["summary"]["provider_identity_maturity_raw_provider_id_runtime_signal"]
        is False
    )
    assert (
        "provider_maturity"
        in payload["summary"][
            "provider_identity_maturity_required_future_features"
        ]
    )
    assert (
        "protected_provider"
        in payload["summary"][
            "provider_identity_maturity_required_future_features"
        ]
    )
    assert (
        payload["summary"]["provider_identity_maturity_runtime_arbiter_allowed"]
        is False
    )
    assert (
        payload["summary"]["provider_identity_maturity_selector_sandbox_ready"]
        is False
    )
    assert (
        payload["summary"]["provider_identity_maturity_stage7_repair_allowed"]
        is False
    )
    assert (
        payload["summary"][
            "provider_identity_maturity_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"]["provider_identity_maturity_gameplay_topology_mutation"]
        is False
    )
    assert (
        payload["summary"]["provider_identity_maturity_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["provider_identity_maturity_stage8_training_allowed"]
        is False
    )
    assert payload["summary"]["selector_directed_fix_passive_ready"] is True
    assert payload["summary"]["selector_directed_fix_status"] == (
        "directed_fix_review_complete_runtime_blocked"
    )
    assert payload["summary"]["selector_directed_fix_geometry_audit_status"] == (
        "geometry_terms_partially_informative_not_sufficient"
    )
    assert payload["summary"]["selector_directed_fix_geometry_audit_row_count"] == 16
    assert (
        payload["summary"]["selector_directed_fix_geometry_audit_stage7_row_count"]
        == 0
    )
    assert payload["summary"]["selector_directed_fix_geometry_probe_status"] == (
        "geometry_augmented_features_underpowered"
    )
    assert (
        payload["summary"]["selector_directed_fix_geometry_probe_underpowered"]
        is True
    )
    assert (
        payload["summary"]["selector_directed_fix_geometry_probe_best_objective"]
        == "provider_family"
    )
    assert (
        payload["summary"][
            "selector_directed_fix_geometry_probe_best_negative_suppression"
        ]
        == 0.0
    )
    assert payload["summary"]["selector_directed_fix_recommended_next_step"] == (
        "design_hard_negative_selector_target_dataset_v0"
    )
    assert payload["summary"]["selector_directed_fix_recommended_class"] == (
        "non_causal_hard_negative_selector_target_design"
    )
    assert (
        "runtime_selector_now"
        in payload["summary"]["selector_directed_fix_rejected_fixes"]
    )
    assert (
        "runtime_candidate_generator_now"
        in payload["summary"]["selector_directed_fix_rejected_fixes"]
    )
    assert (
        "add_simple_geometry_terms_only"
        in payload["summary"]["selector_directed_fix_rejected_fixes"]
    )
    assert payload["summary"]["selector_directed_fix_runtime_work_allowed"] is False
    assert (
        payload["summary"][
            "selector_directed_fix_candidate_generator_runtime_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_directed_fix_selector_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["selector_directed_fix_runtime_selector_implemented"]
        is False
    )
    assert (
        payload["summary"][
            "selector_directed_fix_runtime_candidate_generator_implemented"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_directed_fix_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert (
        payload["summary"]["selector_directed_fix_gameplay_topology_mutation"]
        is False
    )
    assert (
        payload["summary"]["selector_directed_fix_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["selector_directed_fix_stage8_training_allowed"]
        is False
    )
    assert payload["summary"]["selector_provenance_prior_passive_ready"] is True
    assert payload["summary"]["selector_provenance_prior_status"] == (
        "provider_prior_remains_best_no_selector_sandbox"
    )
    assert (
        payload["summary"][
            "selector_provenance_prior_target_training_row_count"
        ]
        == 42
    )
    assert (
        payload["summary"]["selector_provenance_prior_target_stage7_training_rows"]
        == 0
    )
    assert (
        payload["summary"]["selector_provenance_prior_baseline_best"]
        == "provider_prior_loo"
    )
    assert payload["summary"]["selector_provenance_prior_feature_improved"] is False
    assert payload["summary"]["selector_provenance_prior_probe_status"] == (
        "provenance_features_explain_provider_prior_non_causal"
    )
    assert (
        payload["summary"][
            "selector_provenance_prior_raw_provider_runtime_prior_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_provenance_prior_selector_sandbox_ready"]
        is False
    )
    assert payload["summary"]["selector_provenance_prior_architecture_status"] == (
        "provider_prior_remains_best_no_selector_sandbox"
    )
    assert payload["summary"]["selector_provenance_prior_after_contrast_status"] == (
        "selector_sandbox_blocked_selected_provider_evidence_missing"
    )
    assert payload["summary"]["selector_provenance_prior_after_contrast_blockers"] == [
        "insufficient_selected_provider_family_diversity"
    ]
    assert (
        payload["summary"][
            "selector_provenance_prior_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_provenance_prior_gameplay_topology_mutation"]
        is False
    )
    assert (
        payload["summary"]["selector_provenance_prior_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["selector_provenance_prior_stage8_training_allowed"]
        is False
    )
    assert payload["summary"]["selector_objective_normalization_passive_ready"] is True
    assert (
        payload["summary"]["selector_objective_arbitration_status"]
        == "additive_support_objective_rejected_design_normalized_selector_objective"
    )
    assert (
        payload["summary"]["selector_objective_normalized_status"]
        == "normalized_selector_objective_design_ready_for_offline_probe"
    )
    assert (
        payload["summary"]["selector_objective_normalized_probe_status"]
        == "normalized_objective_probe_underpowered_fields_available"
    )
    assert payload["summary"]["selector_objective_normalized_probe_underpowered"] is True
    assert (
        payload["summary"]["selector_objective_architecture_status"]
        == "selector_objective_needs_stratified_label_expansion_before_sandbox"
    )
    assert payload["summary"]["selector_objective_architecture_sandbox_ready"] is False
    assert (
        payload["summary"]["selector_objective_split_dataset_status"]
        == "split_selector_objective_channels_with_ownership_labels"
    )
    assert payload["summary"]["selector_objective_split_dataset_row_count"] == 136
    assert (
        payload["summary"][
            "selector_objective_split_dataset_selector_training_row_count"
        ]
        == 0
    )
    assert payload["summary"]["selector_objective_split_dataset_stage7_row_count"] == 0
    assert (
        payload["summary"]["selector_objective_split_readiness_status"]
        == "ownership_labels_recovered_but_underpowered"
    )
    assert (
        payload["summary"][
            "selector_objective_split_readiness_selector_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_objective_split_readiness_ownership_underpowered"]
        is True
    )
    assert payload["summary"]["selector_objective_runtime_selector_implemented"] is False
    assert payload["summary"]["selector_objective_runtime_terminals_added"] is False
    assert payload["summary"]["selector_objective_stage7_promotion_allowed"] is False
    assert payload["summary"]["selector_objective_stage8_training_allowed"] is False
    assert payload["summary"]["selector_label_balance_passive_ready"] is True
    assert payload["summary"]["selector_label_balance_stratified_dataset_status"] == (
        "stratified_selector_label_dataset_built_replay_free"
    )
    assert payload["summary"]["selector_label_balance_stratified_dataset_row_count"] == 11
    assert (
        payload["summary"][
            "selector_label_balance_stratified_dataset_stage7_training_rows"
        ]
        == 0
    )
    assert payload["summary"]["selector_label_balance_stratified_probe_status"] == (
        "stratified_labels_underbalanced_no_selector_probe"
    )
    assert payload["summary"]["selector_label_balance_stratified_probe_underbalanced"] is True
    assert payload["summary"]["selector_label_balance_balanced_dataset_status"] == (
        "balanced_selector_label_dataset_built_replay_free"
    )
    assert payload["summary"]["selector_label_balance_balanced_dataset_row_count"] == 18
    assert (
        payload["summary"]["selector_label_balance_balanced_dataset_stage7_training_rows"]
        == 0
    )
    assert payload["summary"]["selector_label_balance_balanced_probe_status"] == (
        "balanced_labels_support_non_causal_selector_signal"
    )
    assert (
        payload["summary"]["selector_label_balance_balanced_probe_best_accuracy"]
        == 0.7777777777777778
    )
    assert payload["summary"]["selector_label_balance_architecture_status"] == (
        "selector_signal_promising_sandbox_blocked_pending_readiness_criteria"
    )
    assert (
        payload["summary"][
            "selector_label_balance_architecture_runtime_arbiter_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_label_balance_architecture_selector_sandbox_ready"]
        is False
    )
    assert (
        payload["summary"]["selector_label_balance_runtime_selector_implemented"]
        is False
    )
    assert (
        payload["summary"]["selector_label_balance_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert payload["summary"]["selector_label_balance_stage7_promotion_allowed"] is False
    assert payload["summary"]["selector_label_balance_stage8_training_allowed"] is False
    assert payload["summary"]["ownership_selection_context_passive_ready"] is True
    assert payload["summary"]["ownership_selection_context_label_dataset_status"] == (
        "ownership_selection_labels_expanded_with_targeted_false_positive_risk_cells"
    )
    assert (
        payload["summary"]["ownership_selection_context_label_dataset_merged_row_count"]
        == 41
    )
    assert (
        payload["summary"][
            "ownership_selection_context_label_dataset_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["ownership_selection_context_label_dataset_stage7_row_count"]
        == 0
    )
    assert payload["summary"]["ownership_selection_context_dataset_status"] == (
        "ownership_selection_context_dataset_ready_for_non_causal_probe"
    )
    assert payload["summary"]["ownership_selection_context_dataset_row_count"] == 41
    assert (
        payload["summary"][
            "ownership_selection_context_dataset_selector_training_row_count"
        ]
        == 0
    )
    assert payload["summary"]["ownership_selection_context_dataset_stage7_row_count"] == 0
    assert (
        payload["summary"]["ownership_selection_context_probe_status"]
        == "context_features_underpowered"
    )
    assert payload["summary"]["ownership_selection_context_probe_underpowered"] is True
    assert payload["summary"]["ownership_selection_source_diversity_status"] == (
        "source_diversity_gap_blocks_runtime"
    )
    assert (
        payload["summary"][
            "ownership_selection_source_diversity_non_stage0_ownership_row_count"
        ]
        == 4
    )
    assert (
        payload["summary"]["ownership_selection_context_runtime_selector_implemented"]
        is False
    )
    assert (
        payload["summary"]["ownership_selection_context_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert (
        payload["summary"]["ownership_selection_context_stage7_promotion_allowed"]
        is False
    )
    assert payload["summary"]["ownership_selection_context_stage8_training_allowed"] is False
    assert (
        payload["summary"]["selector_negative_suppression_blocker_passive_ready"]
        is True
    )
    assert payload["summary"][
        "selector_negative_suppression_protected_max_only_status"
    ] == "protected_max_only_frames_block_runtime_selector"
    assert (
        payload["summary"][
            "selector_negative_suppression_protected_max_only_frame_count"
        ]
        == 24
    )
    assert payload["summary"]["selector_negative_suppression_status"] == (
        "selector_negative_suppression_failure_confirmed"
    )
    assert (
        payload["summary"]["selector_negative_suppression_runtime_work_allowed"]
        is False
    )
    assert (
        payload["summary"]["selector_negative_suppression_selector_training_allowed"]
        is False
    )
    assert payload["summary"][
        "selector_negative_suppression_candidate_generator_runtime_allowed"
    ] is False
    assert payload["summary"][
        "selector_negative_suppression_runtime_selector_readiness_status"
    ] == "runtime_selector_not_ready_collect_better_contrast_labels"
    assert (
        payload["summary"]["selector_negative_suppression_runtime_test_allowed_next"]
        is False
    )
    assert (
        payload["summary"][
            "selector_negative_suppression_runtime_selector_implemented"
        ]
        is False
    )
    assert (
        payload["summary"][
            "selector_negative_suppression_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_negative_suppression_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["selector_negative_suppression_stage8_training_allowed"]
        is False
    )
    assert payload["summary"]["abstention_selector_safety_passive_ready"] is True
    assert (
        payload["summary"]["abstention_selector_first_objective_status"]
        == "abstention_first_selector_objective_defined"
    )
    assert (
        payload["summary"]["abstention_safe_preservation_review_status"]
        == "safe_preservation_requires_two_stage_label_semantics"
    )
    assert (
        payload["summary"]["abstention_training_dataset_status"]
        == "abstention_training_dataset_ready_for_probe"
    )
    assert payload["summary"]["abstention_training_dataset_row_count"] == 51
    assert payload["summary"]["abstention_training_dataset_stage7_training_rows"] == 0
    assert (
        payload["summary"]["abstention_training_probe_status"]
        == "abstention_signal_underpowered_no_runtime"
    )
    assert (
        payload["summary"]["abstention_context_dataset_status"]
        == "abstention_context_feature_dataset_ready_for_non_causal_probe"
    )
    assert (
        payload["summary"]["abstention_context_probe_status"]
        == "context_features_help_but_runtime_blocked"
    )
    assert (
        payload["summary"]["abstention_context_probe_improved_negative_suppression"]
        is True
    )
    assert (
        payload["summary"]["abstention_context_error_audit_status"]
        == "context_signal_overrejects_safe_owners_runtime_blocked"
    )
    assert payload["summary"]["abstention_context_error_false_positive_count"] == 12
    assert (
        payload["summary"]["abstention_feature_gap_next_step_status"]
        == "join_abstention_labels_with_control_plane_context"
    )
    assert payload["summary"]["abstention_feature_gap_implementation_allowed"] == (
        "non_causal_replay_free_only"
    )
    assert payload["summary"]["abstention_feature_gap_runtime_ready"] is False
    assert payload["summary"]["abstention_runtime_selector_implemented"] is False
    assert payload["summary"]["abstention_runtime_dtm_or_tablebase_lookup"] is False
    assert payload["summary"]["abstention_stage7_promotion_allowed"] is False
    assert payload["summary"]["abstention_stage8_training_allowed"] is False
    assert payload["summary"]["two_stage_abstention_no_go_passive_ready"] is True
    assert payload["summary"]["two_stage_abstention_objective_probe_status"] == (
        "two_stage_abstention_signal_present_runtime_review_required"
    )
    assert payload["summary"]["two_stage_abstention_objective_probe_row_count"] == 51
    assert (
        payload["summary"][
            "two_stage_abstention_objective_probe_threshold_passing_count"
        ]
        == 12
    )
    assert payload["summary"]["two_stage_abstention_runtime_review_status"] == (
        "two_stage_abstention_review_ready_implementation_blocked"
    )
    assert (
        payload["summary"][
            "two_stage_abstention_runtime_review_implementation_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "two_stage_abstention_runtime_review_runtime_test_allowed_next"
        ]
        is False
    )
    assert (
        payload["summary"]["two_stage_abstention_default_off_status"]
        == "default_off_equivalent"
    )
    assert (
        payload["summary"]["two_stage_abstention_default_off_same_core_metrics"]
        is True
    )
    assert payload["summary"]["two_stage_abstention_enabled_smoke_status"] == (
        "enabled_tiny_smoke_no_behavior_delta"
    )
    assert (
        payload["summary"][
            "two_stage_abstention_enabled_smoke_total_penalized_count"
        ]
        == 24
    )
    assert (
        payload["summary"][
            "two_stage_abstention_enabled_smoke_total_selected_penalized_count"
        ]
        == 0
    )
    assert payload["summary"]["two_stage_abstention_stage7_challenge_status"] == (
        "stage7_challenge_no_target_improvement"
    )
    assert (
        payload["summary"]["two_stage_abstention_stage7_challenge_target_improved"]
        is False
    )
    assert (
        payload["summary"]["two_stage_abstention_status"]
        == "no_go_for_scaling_or_promotion"
    )
    assert payload["summary"]["two_stage_abstention_go_no_go_allowed_status"] == (
        "keep_default_off_runtime_test_code_and_artifacts"
    )
    assert payload["summary"]["two_stage_abstention_rollback_tag"] == (
        "pre-two-stage-abstention-runtime"
    )
    assert (
        payload["summary"]["two_stage_abstention_runtime_defaults_changed"]
        is False
    )
    assert (
        payload["summary"]["two_stage_abstention_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert (
        payload["summary"]["two_stage_abstention_gameplay_topology_mutation"]
        is False
    )
    assert (
        payload["summary"]["two_stage_abstention_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["two_stage_abstention_stage8_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["two_stage_abstention_runtime_repair_not_promoted"]
        is True
    )
    assert (
        payload["summary"]["two_stage_abstention_stage7_remains_quarantined"]
        is True
    )
    assert (
        payload["summary"]["two_stage_abstention_stage8_remains_blocked"]
        is True
    )
    assert payload["summary"]["two_stage_abstention_no_hidden_controller"] is True
    assert payload["summary"]["targeted_ownership_recovery_passive_ready"] is True
    assert (
        payload["summary"]["targeted_ownership_non_stage0_manifest_status"]
        == "targeted_non_stage0_manifest_ready"
    )
    assert payload["summary"]["targeted_ownership_non_stage0_manifest_job_count"] == 4
    assert (
        payload["summary"]["targeted_ownership_non_stage0_manifest_stage7_job_count"]
        == 0
    )
    assert (
        payload["summary"]["targeted_ownership_non_stage0_labels_status"]
        == "current_profile_preserves_some_historical_non_stage0_ownership"
    )
    assert payload["summary"]["targeted_ownership_non_stage0_label_count"] == 4
    assert payload["summary"]["targeted_ownership_non_stage0_preserved_count"] == 4
    assert (
        payload["summary"]["targeted_ownership_non_stage0_stage7_training_rows"]
        == 0
    )
    assert (
        payload["summary"]["targeted_ownership_negative_manifest_status"]
        == "targeted_ownership_negative_manifest_ready"
    )
    assert payload["summary"]["targeted_ownership_negative_manifest_job_count"] == 6
    assert (
        payload["summary"]["targeted_ownership_negative_manifest_stage7_job_count"]
        == 0
    )
    assert (
        payload["summary"]["targeted_ownership_negative_labels_status"]
        == "targeted_ownership_negative_labels_collected"
    )
    assert payload["summary"]["targeted_ownership_negative_label_count"] == 6
    assert (
        payload["summary"]["targeted_ownership_negative_targeted_owner_failed_count"]
        == 2
    )
    assert payload["summary"]["targeted_ownership_negative_stage7_training_rows"] == 0
    assert payload["summary"]["targeted_ownership_runtime_selector_implemented"] is False
    assert (
        payload["summary"]["targeted_ownership_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert payload["summary"]["targeted_ownership_runtime_terminals_added"] is False
    assert payload["summary"]["targeted_ownership_stage7_promotion_allowed"] is False
    assert payload["summary"]["targeted_ownership_stage8_training_allowed"] is False
    assert payload["summary"]["balanced_hard_negative_passive_ready"] is True
    assert (
        payload["summary"]["balanced_hard_negative_label_plan_status"]
        == "balanced_hard_negative_label_plan_v1_ready"
    )
    assert payload["summary"]["balanced_hard_negative_label_plan_job_count"] == 12
    assert payload["summary"]["balanced_hard_negative_label_plan_stage7_jobs"] == 0
    assert (
        payload["summary"]["balanced_hard_negative_execution_manifest_status"]
        == "balanced_hard_negative_execution_manifest_bound"
    )
    assert (
        payload["summary"][
            "balanced_hard_negative_execution_manifest_labels_allowed_now"
        ]
        is False
    )
    assert (
        payload["summary"]["balanced_hard_negative_execution_manifest_stage7_jobs"]
        == 0
    )
    assert (
        payload["summary"]["balanced_hard_negative_labels_status"]
        == "balanced_hard_negative_labels_completed"
    )
    assert payload["summary"]["balanced_hard_negative_label_count"] == 12
    assert payload["summary"]["balanced_hard_negative_positive_capacity_count"] == 11
    assert payload["summary"]["balanced_hard_negative_negative_capacity_count"] == 1
    assert payload["summary"]["balanced_hard_negative_stage7_labels"] == 0
    assert payload["summary"]["balanced_hard_negative_stage7_training_labels"] == 0
    assert (
        payload["summary"]["balanced_hard_negative_evidence_review_status"]
        == "balanced_hard_negative_signal_promising_but_underpowered"
    )
    assert payload["summary"]["balanced_hard_negative_evidence_underpowered"] is True
    assert payload["summary"]["balanced_hard_negative_evidence_expanded_row_count"] == 40
    assert (
        payload["summary"][
            "balanced_hard_negative_evidence_expanded_hard_negative_count"
        ]
        == 9
    )
    assert (
        payload["summary"]["balanced_hard_negative_runtime_selector_implemented"]
        is False
    )
    assert (
        payload["summary"]["balanced_hard_negative_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert payload["summary"]["balanced_hard_negative_runtime_terminals_added"] is False
    assert (
        payload["summary"]["balanced_hard_negative_stage7_promotion_allowed"]
        is False
    )
    assert payload["summary"]["balanced_hard_negative_stage8_training_allowed"] is False
    assert payload["summary"]["stronger_selector_feature_passive_ready"] is True
    assert payload["summary"]["stronger_selector_feature_ablation_status"] == (
        "hard_negative_feature_ablation_promising_underpowered"
    )
    assert payload["summary"]["stronger_selector_feature_ablation_underpowered"] is True
    assert payload["summary"]["stronger_selector_feature_ablation_row_count"] == 40
    assert (
        payload["summary"]["stronger_selector_feature_ablation_stage7_row_count"]
        == 0
    )
    assert payload["summary"]["stronger_selector_feature_review_status"] == (
        "stronger_features_review_ready_runtime_still_blocked"
    )
    assert (
        payload["summary"]["stronger_selector_feature_improved_over_v2_ablation"]
        is True
    )
    assert payload["summary"][
        "stronger_selector_feature_previous_best_negative_suppression"
    ] == 0.2222222222222222
    assert (
        payload["summary"]["stronger_selector_feature_best_negative_suppression"]
        == 0.7777777777777778
    )
    assert payload["summary"]["stronger_selector_feature_best_positive_recall"] == (
        0.9032258064516129
    )
    assert payload["summary"]["stronger_selector_feature_review_stage7_row_count"] == 0
    assert (
        payload["summary"]["stronger_selector_feature_runtime_selector_implemented"]
        is False
    )
    assert (
        payload["summary"][
            "stronger_selector_feature_runtime_candidate_generator_implemented"
        ]
        is False
    )
    assert (
        payload["summary"]["stronger_selector_feature_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert (
        payload["summary"]["stronger_selector_feature_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["stronger_selector_feature_stage8_training_allowed"]
        is False
    )
    assert payload["summary"]["selected_provider_diversity_passive_ready"] is True
    assert payload["summary"]["selected_provider_diversity_evidence_plan_status"] == (
        "selected_provider_diversity_evidence_plan_defined"
    )
    assert payload["summary"]["selected_provider_diversity_manifest_status"] == (
        "fresh_seed_selected_provider_diversity_manifest_ready_for_bounded_labels"
    )
    assert (
        payload["summary"][
            "selected_provider_diversity_manifest_observations_allowed_now"
        ]
        is False
    )
    assert payload["summary"]["selected_provider_diversity_manifest_job_count"] == 18
    assert payload["summary"]["selected_provider_diversity_manifest_stage7_jobs"] == 0
    assert payload["summary"]["selected_provider_diversity_labels_status"] == (
        "fresh_seed_selected_provider_diversity_ownership_labels_collected"
    )
    assert payload["summary"]["selected_provider_diversity_label_count"] == 18
    assert payload["summary"]["selected_provider_diversity_stage7_training_rows"] == 0
    assert payload["summary"]["selected_provider_diversity_architecture_status"] == (
        "selected_provider_diversity_requirement_should_be_reframed"
    )
    assert (
        payload["summary"][
            "selected_provider_diversity_architecture_runtime_arbiter_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["selected_provider_diversity_runtime_selector_implemented"]
        is False
    )
    assert (
        payload["summary"][
            "selected_provider_diversity_runtime_candidate_generator_implemented"
        ]
        is False
    )
    assert (
        payload["summary"]["selected_provider_diversity_runtime_arbiter_implemented"]
        is False
    )
    assert (
        payload["summary"][
            "selected_provider_diversity_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"]["selected_provider_diversity_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["selected_provider_diversity_stage8_training_allowed"]
        is False
    )
    assert payload["summary"]["state_local_contrast_passive_ready"] is True
    assert (
        payload["summary"]["state_local_contrast_labels_status"]
        == "state_local_contrast_labels_v2_joined"
    )
    assert payload["summary"]["state_local_contrast_labels_row_count"] == 20
    assert (
        payload["summary"]["state_local_contrast_labels_stage7_challenge_row_count"]
        == 8
    )
    assert payload["summary"]["state_local_contrast_labels_usable_training_row_count"] == 12
    assert payload["summary"]["state_local_contrast_probe_status"] == (
        "state_local_contrast_signal_not_ready"
    )
    assert payload["summary"]["state_local_contrast_probe_training_row_count"] == 12
    assert payload["summary"]["state_local_contrast_probe_stage7_eval_row_count"] == 8
    assert payload["summary"]["state_local_contrast_probe_stage7_training_leakage"] is False
    assert payload["summary"]["state_local_contrast_readiness_status"] == (
        "runtime_selector_blocked_negative_suppression_zero"
    )
    assert (
        payload["summary"]["state_local_contrast_readiness_runtime_test_allowed_next"]
        is False
    )
    assert (
        payload["summary"]["state_local_contrast_runtime_selector_implemented"]
        is False
    )
    assert (
        payload["summary"]["state_local_contrast_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert payload["summary"]["state_local_contrast_stage7_promotion_allowed"] is False
    assert payload["summary"]["state_local_contrast_stage8_training_allowed"] is False
    assert payload["summary"]["state_local_paired_ownership_passive_ready"] is True
    assert (
        payload["summary"]["state_local_paired_hard_negative_target_status"]
        == "hard_negative_selector_target_dataset_expanded_v2"
    )
    assert payload["summary"]["state_local_paired_hard_negative_target_row_count"] == 40
    assert (
        payload["summary"]["state_local_paired_hard_negative_training_row_count"]
        == 0
    )
    assert payload["summary"]["state_local_paired_hard_negative_stage7_row_count"] == 0
    assert (
        payload["summary"]["state_local_paired_ownership_context_status"]
        == "context_features_review_ready_but_not_runtime_ready"
    )
    assert (
        payload["summary"][
            "state_local_paired_ownership_context_runtime_threshold_passed"
        ]
        is False
    )
    assert (
        payload["summary"]["state_local_paired_ownership_architecture_status"]
        == "ownership_objective_requires_state_local_pairing_review"
    )
    assert (
        payload["summary"]["state_local_paired_inventory_status"]
        == "paired_inventory_ready_for_non_causal_probe"
    )
    assert payload["summary"]["state_local_paired_inventory_pair_count"] == 40
    assert (
        payload["summary"][
            "state_local_paired_inventory_same_state_conflict_pair_count"
        ]
        == 9
    )
    assert (
        payload["summary"]["state_local_paired_inventory_selector_training_row_count"]
        == 0
    )
    assert payload["summary"]["state_local_paired_inventory_stage7_row_count"] == 0
    assert (
        payload["summary"]["state_local_paired_probe_status"]
        == "semantic_gate_review_ready_runtime_feature_translation_needed"
    )
    assert payload["summary"]["state_local_paired_probe_threshold_passing_model_count"] == 2
    assert (
        payload["summary"][
            "state_local_paired_probe_runtime_feature_passing_model_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["state_local_paired_error_audit_status"]
        == "safe_preservation_false_positives_are_outcome_semantics_errors"
    )
    assert (
        payload["summary"]["state_local_paired_review_status"]
        == "semantic_gate_review_ready_runtime_feature_translation_needed"
    )
    assert (
        payload["summary"]["state_local_paired_review_best_objective"]
        == "safe_preservation_gated_model"
    )
    assert (
        payload["summary"][
            "state_local_paired_review_runtime_feature_passing_model_count"
        ]
        == 0
    )
    assert payload["summary"]["state_local_paired_review_stage7_row_count"] == 0
    assert payload["summary"]["state_local_paired_runtime_selector_implemented"] is False
    assert (
        payload["summary"]["state_local_paired_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert payload["summary"]["state_local_paired_runtime_terminals_added"] is False
    assert payload["summary"]["state_local_paired_stage7_promotion_allowed"] is False
    assert payload["summary"]["state_local_paired_stage8_training_allowed"] is False
    assert payload["summary"]["selected_owner_failure_risk_proxy_passive_ready"] is True
    assert payload["summary"]["selected_owner_failure_risk_runtime_proxy_design_status"] == (
        "proxy_design_ready_for_replay_free_validation"
    )
    assert payload["summary"][
        "selected_owner_failure_risk_runtime_proxy_dataset_row_count"
    ] == 40
    assert payload["summary"][
        "selected_owner_failure_risk_runtime_proxy_dataset_stage7_row_count"
    ] == 0
    assert payload["summary"]["selected_owner_failure_risk_runtime_proxy_review_status"] == (
        "runtime_proxy_translation_still_blocked"
    )
    assert payload["summary"][
        "selected_owner_failure_risk_runtime_review_packet_v0_translation_blocker"
    ] is True
    assert payload["summary"]["selected_owner_failure_risk_evidence_status"] == (
        "failure_risk_evidence_v1_built"
    )
    assert payload["summary"]["selected_owner_failure_risk_evidence_row_count"] == 48
    assert payload["summary"]["selected_owner_failure_risk_visible_proxy_precision"] == 1.0
    assert payload["summary"]["selected_owner_failure_risk_visible_proxy_recall"] == 1.0
    assert payload["summary"][
        "selected_owner_failure_risk_visible_proxy_probe_v0_status"
    ] == "visible_failure_risk_proxy_candidate_needs_out_of_sample_validation"
    assert payload["summary"][
        "selected_owner_failure_risk_independent_validation_v0_status"
    ] == "independent_proxy_validation_failed_or_underpowered"
    assert payload["summary"][
        "selected_owner_failure_risk_independent_validation_v0_threshold_met"
    ] is False
    assert payload["summary"][
        "selected_owner_failure_risk_blocker_review_v0_status"
    ] == "failed_proxy_closed_next_evidence_v1_required"
    assert payload["summary"][
        "selected_owner_failure_risk_blocker_review_v0_threshold_met"
    ] is False
    assert payload["summary"]["selected_owner_failure_risk_proxy_v1_probe_status"] == (
        "proxy_v1_independent_candidate_found"
    )
    assert payload["summary"][
        "selected_owner_failure_risk_proxy_v1_independent_passing_proxy_count"
    ] == 3
    assert payload["summary"]["selected_owner_failure_risk_independent_label_count"] == 8
    assert payload["summary"][
        "selected_owner_failure_risk_independent_label_stage7_training_rows"
    ] == 0
    assert payload["summary"][
        "selected_owner_failure_risk_independent_validation_status"
    ] == "independent_proxy_validation_passed"
    assert payload["summary"][
        "selected_owner_failure_risk_independent_validation_threshold_met"
    ] is True
    assert payload["summary"][
        "selected_owner_failure_risk_runtime_proxy_review_packet_v1_status"
    ] == "runtime_review_ready_progress_window_scope_only"
    assert payload["summary"][
        "selected_owner_failure_risk_runtime_proxy_review_packet_v1_implementation_allowed"
    ] is False
    assert (
        payload["summary"]["selected_owner_failure_risk_runtime_selector_implemented"]
        is False
    )
    assert (
        payload["summary"][
            "selected_owner_failure_risk_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert payload["summary"]["selected_owner_failure_risk_runtime_terminals_added"] is False
    assert (
        payload["summary"]["selected_owner_failure_risk_stage7_promotion_allowed"]
        is False
    )
    assert payload["summary"]["selected_owner_failure_risk_stage8_training_allowed"] is False
    assert payload["summary"]["progress_window_reconsideration_passive_ready"] is True
    assert payload["summary"]["progress_window_reconsideration_runtime_test_status"] == (
        "runtime_test_scaffold_wired_but_policy_insufficient"
    )
    assert (
        payload["summary"][
            "progress_window_reconsideration_runtime_test_guardrails_allowed_now"
        ]
        is False
    )
    assert (
        payload["summary"][
            "progress_window_reconsideration_runtime_test_promotion_allowed_now"
        ]
        is False
    )
    assert payload["summary"]["progress_window_reconsideration_smoke_status"] == (
        "runtime_smoke_activation_observed_no_target_improvement"
    )
    assert (
        payload["summary"][
            "progress_window_reconsideration_default_off_equivalence_passed"
        ]
        is True
    )
    assert (
        payload["summary"][
            "progress_window_reconsideration_improved_target_failure_count"
        ]
        == 0
    )
    assert payload["summary"]["progress_window_reconsideration_safe_regression_count"] == 0
    assert payload["summary"]["progress_window_reconsideration_target_failure_row_count"] == 1
    assert payload["summary"]["progress_window_reconsideration_post_activation_status"] == (
        "post_activation_failure_classified"
    )
    assert (
        payload["summary"]["progress_window_reconsideration_implement_next_fix_now"]
        is False
    )
    assert payload["summary"]["progress_window_reconsideration_promotion_status"] == (
        "quarantined_or_analysis_only"
    )
    assert payload["summary"]["progress_window_reconsideration_sandbox_status"] == (
        "wired_but_policy_insufficient"
    )
    assert (
        payload["summary"]["progress_window_reconsideration_runtime_defaults_changed"]
        is False
    )
    assert (
        payload["summary"][
            "progress_window_reconsideration_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"]["progress_window_reconsideration_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["progress_window_reconsideration_stage8_training_allowed"]
        is False
    )
    assert payload["summary"]["clean_replacement_review_passive_ready"] is True
    assert (
        payload["summary"]["clean_replacement_review_packet_status"]
        == "retry1_clean_stack_replacement_review_ready_explicit_approval_required"
    )
    assert (
        payload["summary"][
            "clean_replacement_review_packet_implementation_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["clean_replacement_deferred_review_status"]
        == "clean_stack_adoption_deferred_explicit_approval_required"
    )
    assert (
        payload["summary"][
            "clean_replacement_deferred_review_explicit_approval_detected"
        ]
        is False
    )
    assert (
        payload["summary"][
            "clean_replacement_deferred_review_implementation_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["clean_replacement_protected_stage_reference_mode"]
        == "retry1_manifest_active"
    )
    assert (
        payload["summary"]["clean_replacement_protected_stage_active_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["summary"]["clean_replacement_stage7_promotion_allowed"] is False
    assert payload["summary"]["clean_replacement_stage8_training_allowed"] is False
    assert payload["summary"]["stage7_success_controls_required"] == 5
    assert payload["summary"]["stage7_success_controls_ready"] is True
    assert (
        payload["summary"]["stage7_clean_success_backfill_status"]
        == "stage7_clean_success_backfill_available"
    )
    assert payload["summary"]["stage7_clean_success_backfill_available"] is True
    assert payload["summary"]["stage7_clean_success_backfill_eligible_new_success"] == 0
    assert payload["summary"]["sequence_policy_inputs_ready"] is True
    assert (
        payload["summary"]["sequence_policy_input_probe_status"]
        == "sequence_policy_input_probe_ready_for_full_non_causal_benchmark"
    )
    assert payload["summary"]["sequence_policy_input_probe_row_count"] == 118
    assert (
        payload["summary"]["sequence_policy_input_probe_benchmark_input_ready"]
        is True
    )
    assert payload["summary"]["sequence_policy_input_probe_stage4_topk_signal"] is True
    assert (
        payload["summary"][
            "sequence_policy_input_probe_protected_plan_window_failure_sparse"
        ]
        is True
    )
    assert (
        payload["summary"][
            "sequence_policy_input_probe_protected_failure_contrast_collection_option_available"
        ]
        is True
    )
    assert (
        payload["summary"][
            "sequence_policy_input_probe_protected_failure_contrast_collection_command_available"
        ]
        is True
    )
    assert (
        payload["summary"]["sequence_policy_input_probe_selector_training_row_count"]
        == 0
    )
    assert (
        payload["summary"][
            "sequence_policy_input_probe_runtime_authorization_row_count"
        ]
        == 0
    )
    assert payload["summary"]["sequence_policy_benchmark_ready"] is True
    assert (
        payload["summary"]["current_control_plane_gate_status"]
        == "krk_control_plane_waiting_on_explicit_gate_choice"
    )
    assert payload["summary"]["readiness_control_plane_gate_review_blockers"] == []
    assert payload["summary"]["readiness_explicit_gate_blockers"] == [
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
    ]
    assert (
        "approve_protected_plan_window_failure_contrast_collection"
        in payload["summary"]["current_control_plane_approval_option_ids"]
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_collection_option_available"
        ]
        is True
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_collection_command_available"
        ]
        is True
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_collection_option_id"
        ]
        == "approve_protected_plan_window_failure_contrast_collection"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_collection_blocked_by_option_id"
        ]
        is None
    )
    assert (
        payload["summary"]["protected_missing_provider_labels_status"]
        == "protected_missing_provider_capacity_labels_completed"
    )
    assert payload["summary"]["protected_missing_provider_label_count"] == 16
    assert payload["summary"]["protected_missing_provider_stage7_label_count"] == 0
    assert (
        payload["summary"]["protected_missing_provider_stage7_training_label_count"]
        == 0
    )
    assert (
        payload["summary"]["protected_missing_provider_merge_status"]
        == "protected_missing_provider_labels_unmatched_by_current_proposal_frames"
    )
    assert payload["summary"]["protected_missing_provider_unmatched_label_count"] == 16
    assert (
        payload["summary"]["protected_missing_provider_coverage_status"]
        == "proposal_provider_coverage_gap_blocks_selector_training"
    )
    assert (
        payload["summary"]["protected_missing_provider_missing_from_frame_count"]
        == 16
    )
    assert payload["summary"]["protected_missing_provider_mate_label_count"] == 11
    assert (
        payload["summary"]["protected_missing_provider_gap_blocks_selector_training"]
        is True
    )
    assert (
        payload["summary"][
            "protected_missing_provider_coverage_expansion_plan_status"
        ]
        == "protected_proposal_coverage_expansion_plan_ready"
    )
    assert (
        payload["summary"][
            "protected_missing_provider_coverage_expansion_rows_to_create"
        ]
        == 16
    )
    assert (
        payload["summary"][
            "protected_missing_provider_coverage_expansion_training_allowed_initially"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_missing_provider_coverage_expansion_requires_followup_review_before_training_use"
        ]
        is True
    )
    assert (
        payload["summary"]["protected_missing_provider_coverage_frames_status"]
        == "protected_provider_coverage_frames_built"
    )
    assert (
        payload["summary"]["protected_missing_provider_coverage_frame_row_count"]
        == 16
    )
    assert (
        payload["summary"][
            "protected_missing_provider_coverage_frame_positive_capacity_count"
        ]
        == 11
    )
    assert (
        payload["summary"][
            "protected_missing_provider_coverage_frame_negative_capacity_count"
        ]
        == 5
    )
    assert (
        payload["summary"][
            "protected_missing_provider_coverage_frame_stage7_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_coverage_frame_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_coverage_frame_runtime_proposal_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_training_semantics_review_status"
        ]
        == "capacity_frames_diagnostic_not_selector_training_ready"
    )
    assert (
        payload["summary"][
            "protected_missing_provider_training_semantics_selector_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_missing_provider_training_semantics_runtime_work_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_missing_provider_training_semantics_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_training_semantics_runtime_proposal_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_candidate_generator_coverage_status"
        ]
        == "candidate_generator_recall_gap_confirmed"
    )
    assert (
        payload["summary"][
            "protected_missing_provider_candidate_generator_positive_recall_rate"
        ]
        == 0.0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_candidate_generator_missing_positive_capacity_count"
        ]
        == 11
    )
    assert (
        payload["summary"][
            "protected_missing_provider_validated_candidate_set_status"
        ]
        == "validated_provider_candidate_set_recall_promising_requires_selector_semantics"
    )
    assert (
        payload["summary"][
            "protected_missing_provider_validated_candidate_set_added_positive_capacity_count"
        ]
        == 11
    )
    assert (
        payload["summary"][
            "protected_missing_provider_validated_candidate_set_added_negative_capacity_count"
        ]
        == 5
    )
    assert (
        payload["summary"][
            "protected_missing_provider_validated_candidate_set_candidate_generator_runtime_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["protected_missing_provider_two_stage_review_status"]
        == "two_stage_non_causal_benchmark_design_needed"
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_review_candidate_generator_runtime_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_benchmark_plan_status"
        ]
        == "two_stage_candidate_selection_benchmark_plan_ready"
    )
    assert (
        payload["summary"]["protected_missing_provider_two_stage_benchmark_status"]
        == "candidate_generation_recall_improves_selection_not_ready"
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_benchmark_current_positive_recall_rate"
        ]
        == 0.0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_benchmark_expanded_positive_recall_rate"
        ]
        == 1.0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_benchmark_expanded_negative_inclusion_rate"
        ]
        == 1.0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_benchmark_selector_ready"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_benchmark_best_negative_suppression"
        ]
        == 0.0
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_benchmark_stage7_training_leakage"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_benchmark_candidate_generator_runtime_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_missing_provider_two_stage_benchmark_selector_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["protected_missing_provider_runtime_work_allowed"] is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_candidate_proposal_coverage_status"
        ]
        == "candidate_generation_gap_confirmed"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_candidate_proposal_coverage_positive_capacity_recall"
        ]
        == 0.0
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_candidate_proposal_coverage_missing_positive_capacity_count"
        ]
        == 11
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_candidate_proposal_coverage_stage7_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_candidate_proposal_coverage_selector_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_candidate_generation_strategy_review_status"
        ]
        == "strategy_sequence_control_plane_v1_needed"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_candidate_generation_strategy_review_runtime_sandbox_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_candidate_generation_strategy_review_recommended_next_step"
        ]
        == "define_non_causal_strategy_sequence_candidate_frame_v1"
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_schema_status"]
        == "strategy_sequence_candidate_frame_schema_defined"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_schema_runtime_sandbox_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_frames_status"]
        == "strategy_sequence_frames_populated_non_causal"
    )
    assert payload["summary"]["strategy_sequence_candidate_source_frames_frame_count"] == 256
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_frames_stage7_challenge_row_count"
        ]
        == 198
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_frames_stage7_readiness_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_quality_status"]
        == "frame_quality_probe_supports_next_sequence_candidate_benchmark"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_capacity_not_selector_label"
        ]
        is True
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_sequence_candidate_mate_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_benchmark_status"]
        == "candidate_generation_sources_promising_selector_blocked"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_benchmark_protected_positive_capacity_ratio"
        ]
        == 0.6875
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_benchmark_protected_negative_capacity_ratio"
        ]
        == 0.3125
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_benchmark_progress_window_sequence_candidate_mate_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_control_plane_status"]
        == "candidate_generation_control_plane_ready_for_architecture_review"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_control_plane_runtime_sandbox_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_sandbox_review_status"]
        == "candidate_generation_observation_sandbox_review_ready"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_sandbox_review_implementation_authorized"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_sandbox_status"
        ]
        == "observation_sandbox_ready_for_non_causal_coverage_analysis"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_sandbox_generated_candidate_count"
        ]
        == 93
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_sandbox_selected_move_or_provider_changed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_coverage_status"
        ]
        == "observation_frames_usable_for_non_causal_coverage_analysis"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_coverage_sampled_frame_count"
        ]
        == 93
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_coverage_invariant_failure_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_broadened_status"
        ]
        == "broadened_observation_sample_supports_coverage_analysis"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_broadened_case_count"
        ]
        == 19
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_broadened_emitted_frame_count"
        ]
        == 569
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_broadened_selected_move_or_provider_delta_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_gap_review_status"
        ]
        == "observation_gap_review_blocks_selector_recommends_capacity_annotation"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_gap_review_unknown_capacity_ratio"
        ]
        == 0.7768014059753954
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_observation_gap_review_missing_expected_sources"
        ]
        == ["broader_strategy_candidate", "plan_capsule_sequence_candidate"]
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_annotation_v1_status"
        ]
        == "candidate_move_capacity_annotation_partial_selector_blocked"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_annotation_v1_protected_annotation_recall"
        ]
        == 0.03424657534246575
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_label_manifest_status"
        ]
        == "bounded_candidate_move_capacity_manifest_ready"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_label_manifest_labels_run_by_this_artifact"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_label_manifest_job_count"
        ]
        == 12
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_label_manifest_stage7_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_labels_status"
        ]
        == "bounded_candidate_move_capacity_labels_completed"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_labels_label_count"
        ]
        == 12
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_labels_stage7_training_label_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_annotation_v2_status"
        ]
        == "candidate_move_capacity_annotation_improved_but_selector_blocked"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_annotation_v2_annotated_candidate_move_count"
        ]
        == 22
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_annotation_v2_protected_annotation_recall"
        ]
        == 0.07534246575342465
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_capacity_annotation_v2_stage7_readiness_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_label_blocker_status"]
        == "candidate_generation_label_coverage_underpowered_selector_blocked"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_label_blocker_more_blind_label_farming_not_recommended"
        ]
        is True
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_label_blocker_protected_annotation_recall"
        ]
        == 0.07534246575342465
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_prioritization_review_status"
        ]
        == "proposal_quality_prioritization_review_ready"
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_quality_dataset_status"]
        == "candidate_proposal_quality_dataset_ready_for_probe"
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_quality_dataset_row_count"]
        == 569
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_dataset_quality_probe_row_count"
        ]
        == 38
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_dataset_stage7_readiness_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_quality_probe_status"]
        == "proposal_quality_axes_insufficient_for_selector_review"
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_quality_probe_best_probe"]
        == "candidate_move_frame_source"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_probe_best_positive_recall"
        ]
        == 0.6333333333333333
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_probe_best_negative_suppression"
        ]
        == 0.625
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_probe_ready_for_selector_review"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_quality_decision_status"]
        == "candidate_proposal_quality_not_selector_ready"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_decision_more_blind_label_farming_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_quality_decision_recommended_next_step"
        ]
        == "design_broader_strategy_sequence_candidate_sources"
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_design_status"]
        == "broader_strategy_sequence_candidate_source_design_ready"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_design_implementation_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_plan_capsule_status"]
        == "plan_capsule_sequence_observation_source_schema_ready_but_stage7_only"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_broader_strategy_status"
        ]
        == "broader_strategy_observation_source_schema_ready_but_stage7_only"
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_review_status"]
        == "source_reviews_complete_runtime_expansion_not_authorized"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_review_implementation_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_protected_monitor_expansion_status"
        ]
        == "protected_strategy_monitor_frames_expanded_non_causal"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_protected_monitor_expansion_frame_count"
        ]
        == 85
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_protected_monitor_expansion_stage7_challenge_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_protected_monitor_quality_status"
        ]
        == "protected_strategy_monitor_frames_have_monitor_signal"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_protected_monitor_quality_strong_failure_family_count"
        ]
        == 1
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_repair_monitor_review_status"
        ]
        == "protected_repair_monitor_observation_source_review_ready"
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_repair_monitor_review_implementation_authorized"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_runtime_work_allowed"]
        is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_selector_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "strategy_sequence_candidate_source_stage7_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["strategy_sequence_candidate_source_stage8_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_smoke_status"]
        == "repair_monitor_observation_source_wired_default_off_equivalent"
    )
    assert payload["summary"]["repair_monitor_trace_feature_smoke_case_count"] == 3
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_smoke_repair_monitor_frame_count"
        ]
        == 3
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_smoke_selected_move_provider_delta_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_smoke_stage7_case_count"]
        == 0
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_broadened_status"]
        == "repair_monitor_observation_source_broadened_default_off_equivalent"
    )
    assert payload["summary"]["repair_monitor_trace_feature_broadened_case_count"] == 6
    assert (
        payload["summary"]["repair_monitor_trace_feature_broadened_stage7_case_count"]
        == 0
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_quality_status"]
        == "repair_monitor_observation_source_quality_trace_only_retained"
    )
    assert payload["summary"]["repair_monitor_trace_feature_quality_source_stable"] is True
    assert (
        payload["summary"]["repair_monitor_trace_feature_trace_features_status"]
        == "repair_monitor_trace_features_folded_non_causal"
    )
    assert payload["summary"]["repair_monitor_trace_feature_trace_frame_count"] == 6
    assert (
        payload["summary"]["repair_monitor_trace_feature_stage7_trace_frame_count"]
        == 0
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_selector_training_row_count"]
        == 0
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_integration_review_status"]
        == "strategy_sequence_trace_features_integrated_selector_still_blocked"
    )
    assert payload["summary"]["repair_monitor_trace_feature_integration_safe"] is True
    assert (
        payload["summary"]["repair_monitor_trace_feature_dataset_design_status"]
        == "strategy_sequence_dataset_design_v2_ready"
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_design_implementation_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_dataset_v2_status"]
        == "strategy_sequence_dataset_v2_refreshed_non_causal_selector_blocked"
    )
    assert payload["summary"]["repair_monitor_trace_feature_dataset_v2_row_count"] == 262
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_v2_runtime_trace_feature_row_count"
        ]
        == 6
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_v2_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_v2_stage7_readiness_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_dataset_v2_quality_status"]
        == "strategy_sequence_dataset_v2_quality_candidate_generation_ready_selector_blocked"
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_v2_quality_runtime_flags_false"
        ]
        is True
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_v2_quality_selector_rows_absent"
        ]
        is True
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_refresh_probe_status"]
        == "candidate_generation_refresh_underpowered_selector_blocked"
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_refresh_probe_positive_recall"]
        == 0.6363636363636364
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_refresh_probe_negative_suppression"
        ]
        == 1
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_capacity_manifest_status"]
        == "candidate_generation_capacity_evidence_manifest_ready"
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_capacity_manifest_labels_run_by_this_artifact"
        ]
        is False
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_capacity_manifest_stage7_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_capacity_labels_status"]
        == "candidate_generation_capacity_evidence_labels_completed"
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_capacity_labels_stage7_label_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_capacity_labels_stage7_training_label_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_v2_capacity_merged_status"
        ]
        == "strategy_sequence_dataset_v2_capacity_merged_non_causal"
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_v2_capacity_merged_row_count"
        ]
        == 274
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_v2_capacity_merged_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_dataset_v2_capacity_merged_stage7_readiness_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_refresh_after_labels_status"]
        == "candidate_generation_refresh_supported_selector_blocked"
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_refresh_after_labels_positive_recall"
        ]
        == 0.7368421052631579
    )
    assert (
        payload["summary"][
            "repair_monitor_trace_feature_refresh_after_labels_negative_suppression"
        ]
        == 1
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_runtime_work_allowed"]
        is False
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_selector_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["repair_monitor_trace_feature_stage8_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["stage5_6_candidate_generation_refresh_review_status"]
        == "stage5_6_candidate_generation_refresh_review_ready"
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_review_runtime_review_ready"
        ]
        is True
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_review_implementation_authorized"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_review_runtime_candidate_generator_refresh_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["stage5_6_candidate_generation_refresh_smoke_status"]
        == "stage5_6_candidate_generation_refresh_wired_default_off_equivalent"
    )
    assert (
        payload["summary"]["stage5_6_candidate_generation_refresh_smoke_case_count"]
        == 2
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_smoke_refresh_frame_count"
        ]
        == 13
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_smoke_selected_move_provider_delta_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_smoke_invariant_failure_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_smoke_stage7_case_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["stage5_6_candidate_generation_refresh_coverage_status"]
        == "stage5_6_refresh_coverage_ready_for_broadened_analysis"
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_coverage_refresh_frame_count"
        ]
        == 13
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_coverage_stage7_case_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["stage5_6_candidate_generation_refresh_broadened_status"]
        == "stage5_6_candidate_generation_refresh_broadened_default_off_equivalent"
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_broadened_case_count"
        ]
        == 4
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_broadened_refresh_frame_count"
        ]
        == 38
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_broadened_selected_move_provider_delta_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_broadened_stage7_case_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["stage5_6_candidate_generation_refresh_quality_status"]
        == "stage5_6_candidate_generation_refresh_quality_trace_only_retained"
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_quality_trace_usable_for_candidate_generation_context"
        ]
        is True
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_quality_stage7_case_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_trace_features_status"
        ]
        == "stage5_6_refresh_trace_features_folded_non_causal"
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_trace_features_trace_frame_count"
        ]
        == 38
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_trace_features_stage7_trace_frame_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_trace_features_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_trace_features_candidate_generation_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_dataset_design_v3_status"
        ]
        == "strategy_sequence_dataset_design_v3_ready"
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_dataset_design_v3_implementation_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_runtime_work_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_selector_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_stage7_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage5_6_candidate_generation_refresh_stage8_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_capacity_review_status"
        ]
        == "cross_stage_capacity_review_recommends_stratified_capacity_manifest"
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_status"
        ]
        == "candidate_generation_refresh_supported_selector_blocked"
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_positive_recall"
        ]
        == 0.7692307692307693
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_negative_suppression"
        ]
        == 1.0
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_guardrails_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_selector_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_capacity_review_capacity_row_count"
        ]
        == 28
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_capacity_manifest_status"
        ]
        == "cross_stage_capacity_manifest_ready_partial_target_coverage"
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_capacity_manifest_labels_run_by_this_artifact"
        ]
        is False
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_capacity_manifest_stage7_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_capacity_labels_status"
        ]
        == "cross_stage_capacity_labels_completed"
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_capacity_labels_label_count"
        ]
        == 8
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_capacity_labels_stage7_label_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_dataset_cross_stage_merged_status"
        ]
        == "strategy_sequence_dataset_v2_cross_stage_capacity_merged_non_causal"
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_dataset_cross_stage_merged_row_count"
        ]
        == 282
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_dataset_cross_stage_merged_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_dataset_cross_stage_merged_stage7_readiness_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_label_outcome_review_status"
        ]
        == "cross_stage_capacity_labels_improve_in_sample_but_generalization_blocked"
    )
    assert (
        payload["summary"]["cross_stage_candidate_generation_scope_scope_review_status"]
        == "stage_conditioned_candidate_generation_scope_review_ready"
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_status"
        ]
        == "stage_conditioned_candidate_generation_stage5_6_promising_stage4_blocked"
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_positive_recall"
        ]
        == 0.7692307692307693
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_negative_suppression"
        ]
        == 1
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_stage4_positive_recall"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_stage5_6_positive_recall"
        ]
        == 1
    )
    assert (
        payload["summary"]["cross_stage_candidate_generation_scope_runtime_work_allowed"]
        is False
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_selector_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_stage7_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "cross_stage_candidate_generation_scope_stage8_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_objective_lineage_ownership_recovery_status"]
        == "ownership_label_recovery_seed_manifest_ready_selector_blocked"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_ownership_recovery_joined_state_count"
        ]
        == 4
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_ownership_recovery_selected_failure_with_visible_positive_count"
        ]
        == 2
    )
    assert (
        payload["summary"]["selector_objective_lineage_seed_manifest_v0_status"]
        == "selector_objective_seed_manifest_ready_non_causal"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_seed_manifest_v0_seed_row_count"
        ]
        == 4
    )
    assert (
        payload["summary"]["selector_objective_lineage_seed_probe_v0_status"]
        == "selector_objective_seed_probe_underpowered_semantics_confirmed"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_seed_probe_v0_runtime_feature_eligible_prediction_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["selector_objective_lineage_collection_manifest_status"]
        == "joined_trace_ownership_collection_manifest_ready_for_review"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_collection_manifest_runtime_collection_allowed_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["selector_objective_lineage_collection_review_status"]
        == "joined_trace_ownership_observation_collection_review_ready"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_collection_review_implementation_authorized"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_objective_lineage_joined_collection_status"]
        == "joined_trace_ownership_collection_complete_seed_improved"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_joined_collection_collected_row_count"
        ]
        == 8
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_joined_collection_generated_frame_count"
        ]
        == 80
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_joined_collection_selected_move_delta_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_joined_collection_selected_provider_delta_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["selector_objective_lineage_joined_collection_score_delta_count"]
        == 0
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_joined_collection_routing_delta_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["selector_objective_lineage_seed_manifest_v1_status"]
        == "selector_objective_seed_manifest_v1_ready_non_causal"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_seed_manifest_v1_seed_row_count"
        ]
        == 12
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_seed_manifest_v1_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_seed_manifest_v1_stage7_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["selector_objective_lineage_seed_probe_v1_status"]
        == "selector_objective_seed_ready_for_non_causal_feature_probe"
    )
    assert (
        payload["summary"]["selector_objective_lineage_feature_probe_status"]
        == "selector_objective_feature_probe_no_runtime_ready_features"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_feature_probe_runtime_threshold_passing_model_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["selector_objective_lineage_feature_probe_review_status"]
        == "selector_feature_probe_blocks_runtime_needs_diverse_evidence"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_feature_probe_review_best_switch_recall"
        ]
        == 0.75
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_feature_probe_review_best_preserve_recall"
        ]
        == 1.0
    )
    assert (
        payload["summary"]["selector_objective_lineage_diversity_gap_status"]
        == "selector_objective_diversity_gap_requires_stage4_scope_review"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_diversity_gap_remaining_stage4_selected_failure_count"
        ]
        == 6
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_diversity_gap_remaining_stage5_6_selected_failure_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["selector_objective_lineage_stage4_scope_review_status"]
        == "stage4_joined_trace_ownership_scope_review_ready"
    )
    assert (
        payload["summary"][
            "selector_objective_lineage_stage4_scope_review_implementation_authorized"
        ]
        is False
    )
    assert (
        payload["summary"]["selector_objective_lineage_selector_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["selector_objective_lineage_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["selector_objective_lineage_stage8_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["selector_objective_stage4_collection_status"]
        == "stage4_joined_trace_ownership_collection_complete"
    )
    assert payload["summary"]["selector_objective_stage4_collection_collected_row_count"] == 6
    assert payload["summary"]["selector_objective_stage4_collection_generated_frame_count"] == 170
    assert (
        payload["summary"][
            "selector_objective_stage4_collection_switch_contrast_with_positive_capacity_count"
        ]
        == 1
    )
    assert (
        payload["summary"][
            "selector_objective_stage4_collection_default_off_equivalence_passed"
        ]
        is True
    )
    assert (
        payload["summary"]["selector_objective_stage4_collection_selected_move_delta_count"]
        == 0
    )
    assert (
        payload["summary"][
            "selector_objective_stage4_collection_selected_provider_delta_count"
        ]
        == 0
    )
    assert payload["summary"]["selector_objective_stage4_collection_score_delta_count"] == 0
    assert payload["summary"]["selector_objective_stage4_collection_routing_delta_count"] == 0
    assert (
        payload["summary"]["selector_objective_seed_manifest_v2_status"]
        == "selector_objective_seed_manifest_v2_ready_non_causal"
    )
    assert payload["summary"]["selector_objective_seed_manifest_v2_seed_row_count"] == 18
    assert payload["summary"]["selector_objective_seed_manifest_v2_objective_channel_counts"] == {
        "candidate_switch_contrast_seed": 5,
        "failure_context_without_candidate_seed": 5,
        "safe_preservation_contrast_seed": 8,
    }
    assert (
        payload["summary"]["selector_objective_seed_probe_v2_status"]
        == "selector_objective_seed_probe_v2_ready_for_non_causal_benchmark"
    )
    assert (
        payload["summary"][
            "selector_objective_seed_probe_v2_runtime_feature_eligible_prediction_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["selector_objective_benchmark_v2_status"]
        == "selector_objective_benchmark_v2_runtime_feature_review_ready"
    )
    assert (
        payload["summary"]["selector_objective_benchmark_v2_best_runtime_model"]
        == "visible_failure_risk_heuristic_v2"
    )
    assert payload["summary"]["selector_objective_benchmark_v2_best_runtime_accuracy"] == 1.0
    assert (
        payload["summary"][
            "selector_objective_benchmark_v2_best_runtime_switch_recall"
        ]
        == 1.0
    )
    assert (
        payload["summary"][
            "selector_objective_benchmark_v2_runtime_threshold_passing_model_count"
        ]
        == 1
    )
    assert (
        payload["summary"]["selector_objective_benchmark_review_status"]
        == "selector_objective_benchmark_review_ready_for_independent_validation"
    )
    assert (
        payload["summary"]["selector_objective_benchmark_review_runtime_review_ready"]
        is False
    )
    assert (
        payload["summary"][
            "selector_objective_benchmark_review_independent_validation_ready"
        ]
        is True
    )
    assert (
        payload["summary"][
            "selector_objective_independent_validation_manifest_status"
        ]
        == "selector_objective_independent_validation_manifest_ready"
    )
    assert (
        payload["summary"][
            "selector_objective_independent_validation_manifest_job_count"
        ]
        == 10
    )
    assert (
        payload["summary"][
            "selector_objective_independent_validation_manifest_stage7_training_rows"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "selector_objective_independent_validation_manifest_job_labels_generated_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "selector_objective_independent_validation_labels_status"
        ]
        == "selector_objective_independent_validation_labels_collected"
    )
    assert (
        payload["summary"][
            "selector_objective_independent_validation_labels_label_count"
        ]
        == 10
    )
    assert (
        payload["summary"][
            "selector_objective_independent_validation_labels_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "selector_objective_independent_validation_labels_stage7_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["selector_objective_independent_validation_status"]
        == "selector_objective_independent_validation_underpowered"
    )
    assert payload["summary"]["selector_objective_independent_validation_row_count"] == 10
    assert payload["summary"]["selector_objective_independent_validation_target_counts"] == {
        "preserve": 10
    }
    assert payload["summary"]["selector_objective_independent_validation_switch_recall"] == 0.0
    assert payload["summary"]["selector_objective_independent_validation_preserve_recall"] == 1.0
    assert (
        payload["summary"]["selector_objective_independent_validation_blocker_status"]
        == "selector_objective_runtime_blocked_pending_independent_switch_contrasts"
    )
    assert (
        payload["summary"]["selector_objective_independent_validation_blocker_class"]
        == "independent_switch_contrast_absent"
    )
    assert (
        payload["summary"][
            "selector_objective_independent_validation_runtime_selector_blocked"
        ]
        is True
    )
    assert payload["summary"]["selector_objective_selector_training_allowed"] is False
    assert payload["summary"]["selector_objective_stage7_promotion_allowed"] is False
    assert payload["summary"]["selector_objective_stage8_training_allowed"] is False
    assert (
        payload["summary"]["stage4_first_move_diagnostic_failure_discovery_status"]
        == "stage4_failure_discovery_collapsed_to_seed_state"
    )
    assert payload["summary"]["stage4_first_move_diagnostic_failure_packet_count"] == 32
    assert (
        payload["summary"][
            "stage4_first_move_diagnostic_unique_failure_state_move_count"
        ]
        == 1
    )
    assert (
        payload["summary"]["stage4_first_move_diagnostic_sequence_review_status"]
        == "stage4_caveat_sequence_followup_gap_review_ready"
    )
    assert (
        payload["summary"][
            "stage4_first_move_diagnostic_sequence_review_primary_diagnosis"
        ]
        == "stage4_sequence_followup_gap_single_state"
    )
    assert (
        payload["summary"]["stage4_first_move_diagnostic_sequence_candidate_status"]
        == "stage4_first_move_ranking_gap"
    )
    assert (
        payload["summary"]["stage4_first_move_diagnostic_converting_first_move_count"]
        == 7
    )
    assert (
        payload["summary"]["stage4_first_move_diagnostic_feature_review_status"]
        == "stage4_first_move_feature_contrast_found_single_state"
    )
    assert payload["summary"][
        "stage4_first_move_diagnostic_feature_review_positive_terms"
    ] == [
        "king_destination_c_file",
        "rook_mid_rank8_cut_candidate",
    ]
    assert payload["summary"][
        "stage4_first_move_diagnostic_feature_review_failure_terms"
    ] == [
        "king_destination_a7",
        "rook_far_rank8_drift_candidate",
    ]
    assert (
        payload["summary"]["stage4_first_move_diagnostic_stratified_validation_status"]
        == "stage4_stratified_contrast_validation_supports_first_move_ranking_gap"
    )
    assert (
        payload["summary"][
            "stage4_first_move_diagnostic_stratified_gap_variant_count"
        ]
        == 4
    )
    assert (
        payload["summary"]["stage4_first_move_diagnostic_runtime_review_status"]
        == "stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval"
    )
    assert (
        payload["summary"][
            "stage4_first_move_diagnostic_runtime_review_implementation_authorized"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage4_first_move_diagnostic_sequence_control_dataset_row_count"
        ]
        == 76
    )
    assert (
        payload["summary"][
            "stage4_first_move_diagnostic_sequence_control_dataset_runtime_authorization_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["stage4_first_move_diagnostic_sequence_control_probe_status"]
        == "sequence_control_dataset_ready_for_broader_sequence_policy_review"
    )
    assert (
        payload["summary"]["stage4_first_move_diagnostic_selector_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["stage4_first_move_diagnostic_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["stage4_first_move_diagnostic_stage8_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["candidate_generation_training_refresh_dataset_v3_status"]
        == "strategy_sequence_dataset_v3_refreshed_non_causal_selector_blocked"
    )
    assert (
        payload["summary"]["candidate_generation_training_refresh_dataset_v3_row_count"]
        == 320
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_dataset_v3_candidate_generation_training_row_count"
        ]
        == 26
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_dataset_v3_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_context_benchmark_status"
        ]
        == "candidate_generation_v3_context_useful_selector_still_blocked"
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_context_benchmark_stage_family_positive_capacity_recall_from_trace"
        ]
        == 0.7692307692307693
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_runtime_boundary_status"
        ]
        == "candidate_generation_v3_runtime_boundary_context_ready_selector_blocked"
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_runtime_boundary_new_runtime_behavior_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["candidate_generation_training_refresh_design_v2_status"]
        == "candidate_generation_training_refresh_design_ready"
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_design_v2_runtime_candidate_generator_refresh_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_design_v2_selector_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_design_v2_guardrails_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_design_v2_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["candidate_generation_training_refresh_design_status"]
        == "candidate_generation_training_refresh_v3_design_ready"
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_design_implementation_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["candidate_generation_training_refresh_benchmark_status"]
        == "candidate_generation_training_refresh_v3_benchmark_passed_runtime_review_needed"
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_benchmark_best_policy"
        ]
        == "trace_stage_family_context"
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_benchmark_positive_capacity_recall"
        ]
        == 0.7692307692307693
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_benchmark_negative_capacity_suppression"
        ]
        == 1.0
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_benchmark_thresholds_met"
        ]
        is True
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_runtime_review_status"
        ]
        == "candidate_generation_training_refresh_runtime_review_ready"
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_runtime_review_ready"
        ]
        is True
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_runtime_review_candidate_generation_allowed_by_packet"
        ]
        is False
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_runtime_review_implementation_authorized"
        ]
        is False
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_runtime_work_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_selector_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_stage7_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "candidate_generation_training_refresh_stage8_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["candidate_generation_trace_refresh_sandbox_status"]
        == "candidate_generation_refresh_sandbox_ready_for_non_causal_coverage_analysis"
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_refresh_sandbox_generated_frame_count"
        ]
        == 25
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_refresh_sandbox_default_off_equivalence_passed"
        ]
        is True
    )
    assert (
        payload["summary"]["candidate_generation_trace_refresh_coverage_status"]
        == "candidate_generation_refresh_coverage_ready_for_trace_dataset_refresh"
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_refresh_coverage_exact_positive_capacity_recall"
        ]
        == 1.0
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_refresh_trace_features_status"
        ]
        == "candidate_generation_refresh_trace_features_folded_non_causal"
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_refresh_trace_features_trace_frame_count"
        ]
        == 25
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_refresh_trace_features_stage7_trace_frame_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_refresh_trace_features_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_refresh_trace_features_candidate_generation_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["candidate_generation_trace_dataset_v4_status"]
        == "strategy_sequence_dataset_v4_refreshed_non_causal_selector_blocked"
    )
    assert payload["summary"]["candidate_generation_trace_dataset_v4_row_count"] == 307
    assert (
        payload["summary"]["candidate_generation_trace_v4_boundary_status"]
        == "candidate_generation_v4_next_runtime_boundary_context_ready_selector_blocked"
    )
    assert (
        payload["summary"]["candidate_generation_trace_source_gap_manifest_status"]
        == "candidate_source_gap_manifest_ready_non_causal"
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_source_gap_exact_missing_positive_capacity_count"
        ]
        == 21
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_exact_trace_runtime_review_status"
        ]
        == "exact_trace_enrichment_runtime_review_ready"
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_exact_trace_runtime_review_implementation_authorized"
        ]
        is False
    )
    assert (
        payload["summary"]["candidate_generation_trace_exact_trace_sandbox_status"]
        == "exact_trace_enrichment_sandbox_ready_for_non_causal_coverage_analysis"
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_exact_trace_sandbox_generated_frame_count"
        ]
        == 3
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_exact_trace_coverage_exact_gap_recall"
        ]
        == 1.0
    )
    assert (
        payload["summary"]["candidate_generation_trace_dataset_v5_status"]
        == "strategy_sequence_dataset_v5_refreshed_non_causal_selector_blocked"
    )
    assert payload["summary"]["candidate_generation_trace_dataset_v5_row_count"] == 310
    assert (
        payload["summary"][
            "candidate_generation_trace_dataset_v5_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_v5_context_benchmark_status"
        ]
        == "candidate_generation_v5_context_useful_selector_still_blocked"
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_v5_exact_positive_capacity_recall_from_candidate_generation_trace"
        ]
        == 0.3076923076923077
    )
    assert (
        payload["summary"]["candidate_generation_trace_v5_boundary_status"]
        == "candidate_generation_v5_next_boundary_context_improved_selector_blocked"
    )
    assert (
        payload["summary"][
            "candidate_generation_trace_v5_boundary_implement_new_runtime_sandbox"
        ]
        is False
    )
    assert payload["summary"]["candidate_generation_trace_runtime_work_allowed"] is False
    assert (
        payload["summary"]["candidate_generation_trace_selector_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["candidate_generation_trace_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["candidate_generation_trace_stage8_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["strategy_arbitration_decision_status"]
        == "missing_feature_first"
    )
    assert (
        payload["summary"]["strategy_arbitration_decision_next_class"]
        == "non_causal_terminal_affordance_candidate_audit"
    )
    assert payload["summary"]["strategy_arbitration_dataset_record_count"] == 33
    assert payload["summary"]["strategy_arbitration_dataset_proposal_count"] == 87
    assert payload["summary"]["strategy_arbitration_probe_stage7_record_count"] == 9
    assert (
        payload["summary"][
            "strategy_arbitration_probe_raw_global_provider_hit_rate"
        ]
        == 0.9285714285714286
    )
    assert (
        payload["summary"]["strategy_arbitration_probe_visible_heuristic_hit_rate"]
        == 0.07142857142857142
    )
    assert (
        payload["summary"]["strategy_arbitration_missing_feature_candidate_count"]
        == 6
    )
    assert (
        payload["summary"][
            "strategy_arbitration_missing_feature_recommended_next_step"
        ]
        == "stop_for_architecture_review_before_any_terminal_or_affordance_runtime_sandbox"
    )
    assert payload["summary"]["strategy_arbitration_runtime_work_allowed"] is False
    assert payload["summary"]["strategy_arbitration_runtime_arbiter_allowed"] is False
    assert (
        payload["summary"]["strategy_arbitration_selector_training_allowed"]
        is False
    )
    assert payload["summary"]["strategy_arbitration_stage7_promotion_allowed"] is False
    assert payload["summary"]["strategy_arbitration_stage8_training_allowed"] is False
    assert (
        payload["summary"][
            "strategy_monitor_plan_do_not_implement_as_causal_affordances"
        ]
        is True
    )
    assert payload["summary"]["strategy_monitor_records_monitor_record_count"] == 108
    assert (
        payload["summary"]["strategy_monitor_companion_audit_v1_visible_term_count"]
        == 6
    )
    assert (
        payload["summary"][
            "strategy_monitor_companion_audit_v1_still_missing_term_count"
        ]
        == 11
    )
    assert payload["summary"]["strategy_monitor_maturity_term_count"] == 6
    assert payload["summary"]["strategy_monitor_maturity_causal_ready_terms"] == []
    assert (
        payload["summary"][
            "strategy_monitor_maturity_strongest_internal_terminal_candidates"
        ]
        == ["post_plan_stagnation", "local_provider_competition_failed"]
    )
    assert (
        payload["summary"]["strategy_monitor_maturity_recommended_next_step"]
        == "broader_evidence_collection_or_internal_monitor_design_review"
    )
    assert payload["summary"]["strategy_monitor_runtime_work_allowed"] is False
    assert payload["summary"]["strategy_monitor_runtime_terminals_allowed"] is False
    assert payload["summary"]["strategy_monitor_runtime_arbiter_allowed"] is False
    assert (
        payload["summary"]["strategy_monitor_monitor_to_provider_routing_allowed"]
        is False
    )
    assert payload["summary"]["strategy_monitor_selector_training_allowed"] is False
    assert payload["summary"]["strategy_monitor_stage7_promotion_allowed"] is False
    assert payload["summary"]["strategy_monitor_stage8_training_allowed"] is False
    assert (
        payload["summary"]["internal_terminal_feature_candidate_all_non_causal"]
        is True
    )
    assert payload["summary"]["internal_terminal_candidate_spec_count"] == 4
    assert (
        payload["summary"]["internal_terminal_validation_causal_ready_terminals"]
        == []
    )
    assert (
        payload["summary"]["internal_terminal_validation_all_causal_use_blocked"]
        is True
    )
    assert payload["summary"]["internal_terminal_evidence_causal_ready_terminals"] == []
    assert (
        payload["summary"]["internal_terminal_evidence_all_causal_ready_false"]
        is True
    )
    assert (
        payload["summary"][
            "internal_terminal_design_review_causal_ready_terminals"
        ]
        == []
    )
    assert (
        payload["summary"][
            "internal_terminal_design_review_all_causal_ready_false"
        ]
        is True
    )
    assert (
        payload["summary"][
            "internal_terminal_design_review_recommended_next_step"
        ]
        == "broader_replay_free_monitor_evidence_collection_or_review"
    )
    assert payload["summary"]["internal_terminal_runtime_work_allowed"] is False
    assert payload["summary"]["internal_terminal_runtime_terminals_allowed"] is False
    assert payload["summary"]["internal_terminal_causal_affordances_allowed"] is False
    assert payload["summary"]["internal_terminal_runtime_arbiter_allowed"] is False
    assert (
        payload["summary"]["internal_terminal_monitor_to_provider_routing_allowed"]
        is False
    )
    assert payload["summary"]["internal_terminal_selector_training_allowed"] is False
    assert payload["summary"]["internal_terminal_stage7_promotion_allowed"] is False
    assert payload["summary"]["internal_terminal_stage8_training_allowed"] is False


def test_gate_advancement_writer_includes_all_passive_steps():
    payload = _advance.build_payload()
    rendered = _advance.write_markdown(payload)

    step_ids = {step["step_id"] for step in payload["step_results"]}
    assert step_ids == {
        "stage7_diverse_clean_output_validation",
        "stage4_first_move_contrast_sandbox_approval_request",
        "stage4_caveat_unblocker_packet",
        "stage7_clean_artifact_manifest",
        "stage7_clean_sequence_control_recovery",
        "stage7_clean_success_backfill_audit",
        "sequence_policy_pipeline_refresh",
        "sequence_policy_benchmark_review",
        "sequence_policy_benchmark_design",
        "cross_stage_plan_capsule_requirements",
        "protected_plan_window_failure_contrast_plan",
        "protected_plan_window_failure_contrast_manifest",
        "protected_plan_window_failure_contrast_manifest_review",
        "protected_plan_window_failure_contrast_execution_readiness",
        "protected_plan_window_failure_contrast_runner",
        "protected_plan_window_failure_contrast_approval_request",
        "protected_plan_window_failure_contrast_output_validation",
        "protected_plan_window_failure_contrast_integration",
        "sequence_policy_after_protected_failure_contrast_refresh",
        "candidate_generator_coverage_audit",
        "validated_provider_candidate_set_audit",
        "two_stage_candidate_selection_review",
        "two_stage_candidate_selection_benchmark_plan",
        "two_stage_candidate_selection_benchmark",
        "sequence_policy_underpowered_pilot_review",
        "full_suite_readiness_audit",
        "full_suite_unblocker_packet",
        "stage8_training_readiness_review",
        "stage7_post_label_outcome_review",
        "stage7_label_distribution_review",
        "stage7_additional_clean_sampling_manifest",
        "stage7_additional_clean_output_validation",
        "stage7_additional_clean_sampling_runner",
        "current_control_plane_gate",
    }
    assert (
        "krk_suite_passive_advancement_ready_for_protected_failure_contrast_collection"
        in rendered
    )
    assert (
        payload["summary"]["sequence_policy_benchmark_review_status"]
        == "sequence_policy_benchmark_mixed_plan_window_underpowered"
    )
    assert (
        payload["summary"]["sequence_policy_benchmark_design_status"]
        == "sequence_policy_benchmark_design_ready_non_causal"
    )
    assert (
        payload["summary"]["sequence_policy_passive_design_without_new_labels_status"]
        == "non_causal_sequence_policy_design_without_new_labels_ready"
    )
    assert (
        payload["summary"]["cross_stage_plan_capsule_requirements_status"]
        == "cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark"
    )
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_plan_status"]
        == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
    )
    assert payload["summary"]["protected_plan_window_unique_failure_count"] == 1
    assert payload["summary"]["protected_plan_window_minimum_new_failures_needed"] == 4
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_manifest_status"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_manifest_job_count"] == 6
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_manifest_review_status"]
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_execution_readiness_status"
        ]
        == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_execution_jobs_passing"] == 6
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_runner_status"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_runner_manifest_status"
        ]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_runner_manifest_declared_job_count"
        ]
        == 6
    )
    assert (
        len(
            payload["summary"][
                "protected_plan_window_failure_contrast_runner_manifest_fingerprint"
            ]
        )
        == 64
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_runner_collection_run_allowed"
        ]
        is False
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_runner_processed_job_count"] == 0
    assert payload["summary"]["protected_plan_window_failure_contrast_runner_executed_job_count"] == 0
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_runner_refresh_after_run_requested"
        ]
        is True
    )
    runner_step = [
        step
        for step in payload["step_results"]
        if step["step_id"] == "protected_plan_window_failure_contrast_runner"
    ][0]
    assert runner_step["script_args"] == ["--refresh-after-run"]
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_approval_request_status"]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_approval_request_blockers"]
        == []
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_approval_request_ready_for_collection"
        ]
        is True
    )
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_approval_receipt_created"]
        is False
    )
    assert payload["summary"][
        "protected_plan_window_failure_contrast_approval_receipt_blockers"
    ] == ["approval_receipt_missing"]
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_post_success_refresh_required"
        ]
        is True
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_post_success_refresh_script"
        ]
        == "scripts/advance_krk_suite_from_current_gates_v0.py"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_post_success_refresh_scope"
        ]
        == "full_passive_krk_suite_gate_stack"
    )
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_runtime_direct_routing"]
        is False
    )
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_hidden_python_controller"]
        is False
    )
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_output_validation_status"]
        == "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_output_exists_count"] == 0
    assert payload["summary"]["protected_plan_window_failure_contrast_output_valid_count"] == 0
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_integration_status"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs"
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_integrated_new_failure_count"] == 0
    assert payload["summary"]["protected_plan_window_failure_contrast_integration_ready"] is False
    assert (
        payload["summary"]["sequence_policy_after_protected_failure_contrast_refresh_status"]
        == "sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs"
    )
    assert payload["summary"]["sequence_policy_after_protected_failure_contrast_rows"] == 0
    assert (
        payload["summary"][
            "sequence_policy_after_protected_failure_contrast_boundaries_preserved"
        ]
        is True
    )
    assert (
        payload["summary"][
            "sequence_policy_after_protected_failure_contrast_boundary_violation_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "sequence_policy_after_protected_failure_contrast_stage7_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "sequence_policy_after_protected_failure_contrast_selector_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "sequence_policy_after_protected_failure_contrast_runtime_authorization_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["sequence_policy_underpowered_pilot_status"]
        == "sequence_policy_pilot_underpowered_pending_protected_failure_contrast_collection"
    )
    assert (
        payload["summary"]["sequence_policy_underpowered_pilot_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["summary"]["sequence_policy_underpowered_pilot_stage4_topk_signal"] is True
    assert payload["summary"]["sequence_policy_underpowered_pilot_stage7_success_gap"] == 0
    assert (
        payload["summary"]["sequence_policy_underpowered_pilot_readiness_checked_flag_count"]
        >= 430
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_readiness_boundary_violation_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["sequence_policy_underpowered_pilot_readiness_source_artifact_count"]
        >= 44
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runner_processed_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runner_executed_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_approval_receipt_present"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_approval_receipt_valid"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_post_success_refresh_required"
        ]
        is True
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_post_success_refresh_script"
        ]
        == "scripts/advance_krk_suite_from_current_gates_v0.py"
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_behavior_changed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_defaults_changed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_selector_implemented"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_score_changes"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_direct_routing"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_hidden_python_controller"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_gameplay_topology_mutation"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_selector_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_stage7_promotion_allowed"
        ]
        is False
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_stage8_training_allowed"
        ]
        is False
    )
    assert (
        payload["summary"]["stage7_output_validation_status"]
        == "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert payload["summary"]["stage7_output_valid_count"] == 8
    assert (
        payload["summary"]["stage8_training_readiness_status"]
        == "stage8_training_blocked_pending_protected_failure_contrast_collection"
    )
    assert payload["summary"]["readiness_checked_flag_count"] >= 430
    assert payload["summary"]["readiness_boundary_violation_count"] == 0
    assert payload["summary"]["readiness_source_artifact_count"] >= 44
    assert payload["summary"]["stage8_training_readiness_checked_flag_count"] >= 430
    assert payload["summary"]["stage8_training_readiness_boundary_violation_count"] == 0
    assert payload["summary"]["stage8_training_readiness_source_artifact_count"] >= 44
    assert (
        payload["summary"][
            "stage8_training_readiness_protected_failure_contrast_post_success_refresh_required"
        ]
        is True
    )
    assert (
        payload["summary"][
            "stage8_training_readiness_protected_failure_contrast_approval_receipt_present"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage8_training_readiness_protected_failure_contrast_approval_receipt_valid"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage8_training_readiness_protected_failure_contrast_runtime_direct_routing"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage8_training_readiness_protected_failure_contrast_hidden_python_controller"
        ]
        is False
    )
    assert (
        payload["summary"]["stage7_post_label_outcome_status"]
        == "post_label_outcome_waiting_on_explicit_protected_failure_contrast_collection"
    )
    assert payload["summary"]["stage7_post_label_outcome_readiness_checked_flag_count"] >= 430
    assert (
        payload["summary"]["stage7_post_label_outcome_readiness_boundary_violation_count"]
        == 0
    )
    assert payload["summary"]["stage7_post_label_outcome_readiness_source_artifact_count"] >= 44
    assert (
        payload["summary"]["stage7_post_label_outcome_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_runner_processed_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_runner_executed_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_approval_receipt_present"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_approval_receipt_valid"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_post_success_refresh_required"
        ]
        is True
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_post_success_refresh_script"
        ]
        == "scripts/advance_krk_suite_from_current_gates_v0.py"
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_runtime_direct_routing"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_hidden_python_controller"
        ]
        is False
    )
    assert (
        payload["summary"]["stage7_label_distribution_review_status"]
        == "stage7_label_distribution_review_success_gate_closed"
    )
    assert (
        payload["summary"]["stage7_label_distribution_review_next_step"]
        == "rerun_passive_sequence_policy_gate_stack"
    )
    assert payload["summary"]["stage7_label_distribution_unique_new_success"] == 2
    assert payload["summary"]["stage7_label_distribution_duplicate_playouts"] == 50
    assert (
        payload["summary"]["stage7_additional_clean_sampling_manifest_status"]
        == "stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed"
    )
    assert (
        payload["summary"]["stage7_additional_clean_sampling_runner_status"]
        == "stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed"
    )
    assert payload["summary"]["stage7_additional_clean_sampling_job_count"] == 0
    assert payload["summary"]["stage7_additional_clean_sampling_max_samples"] == 0
    assert (
        payload["summary"]["stage4_caveat_unblocker_status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_approval_request_status"
        ]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_approval_request_blockers"
        ]
        == []
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_approval_request_ready_for_runtime_approval"
        ]
        is True
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_approval_request_created"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_implementation_authorized_by_request"
        ]
        is False
    )
    assert (
        payload["summary"]["stage4_first_move_contrast_sandbox_scope_id"]
        == "default_off_stage4_candidate_move_first_move_contrast_sandbox_only"
    )
    assert payload["summary"]["stage4_first_move_contrast_sandbox_default_off"] is True
    assert payload["summary"]["stage4_first_move_contrast_sandbox_default_enabled"] is False
    assert (
        payload["summary"]["stage4_first_move_contrast_sandbox_runtime_change_class"]
        == "default_off_candidate_move_frame_sandbox_only"
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"]["stage4_first_move_contrast_sandbox_hidden_python_controller"]
        is False
    )
    assert (
        payload["summary"]["stage4_first_move_contrast_sandbox_selector_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["stage4_first_move_contrast_sandbox_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["stage4_first_move_contrast_sandbox_stage8_training_allowed"]
        is False
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_readiness_checked_flag_count"
        ]
        >= 430
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_readiness_boundary_violation_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_readiness_source_artifact_count"
        ]
        >= 44
    )
    for step in payload["step_results"]:
        assert step["label_run_allowed"] is False
        assert step["runtime_changes_allowed"] is False
        assert step["stage7_promotion_allowed"] is False
        assert step["stage8_training_allowed"] is False
        assert step["artifact_runtime_behavior_changed"] is False
        assert step["artifact_runtime_defaults_changed"] is False
        assert step["artifact_runtime_selector_implemented"] is False
        assert step["artifact_runtime_score_changes"] is False
        assert step["artifact_runtime_direct_routing"] is False
        assert step["artifact_runtime_dtm_or_tablebase_lookup"] is False
        assert step["artifact_hidden_python_controller"] is False
        assert step["artifact_gameplay_topology_mutation"] is False
        assert step["artifact_stage7_promotion_allowed"] is False
        assert step["artifact_stage8_training_allowed"] is False


def test_gate_advancement_does_not_inherit_caller_label_execution_flags():
    original_argv = sys.argv
    try:
        sys.argv = [
            "scripts/run_stage7_additional_clean_sampling_jobs_v0.py",
            "--execute-reviewed-label-run",
            "--refresh-after-run",
        ]
        payload = _advance.build_payload()
    finally:
        sys.argv = original_argv

    assert payload["decision"]["label_run_allowed"] is False
    runner_step = [
        step
        for step in payload["step_results"]
        if step["step_id"] == "stage7_additional_clean_sampling_runner"
    ][0]
    assert runner_step["label_run_allowed"] is False
    assert (
        runner_step["decision_status"]
        == "stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed"
    )
    protected_runner_step = [
        step
        for step in payload["step_results"]
        if step["step_id"] == "protected_plan_window_failure_contrast_runner"
    ][0]
    assert protected_runner_step["script_args"] == ["--refresh-after-run"]


def test_gate_advancement_boundary_check_includes_artifact_level_flags(monkeypatch):
    real_load_json = _advance._load_json

    def tainted_load_json(relative: str):
        payload = real_load_json(relative)
        if relative == "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json":
            payload = dict(payload)
            payload["runtime_behavior_changed"] = True
        return payload

    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert payload["summary"]["all_boundaries_preserved"] is False
    tainted_step = [
        step
        for step in payload["step_results"]
        if step["step_id"] == "sequence_policy_benchmark_review"
    ][0]
    assert tainted_step["runtime_changes_allowed"] is False
    assert tainted_step["artifact_runtime_behavior_changed"] is True


def test_gate_advancement_routes_forbidden_training_rows_to_input_repair(monkeypatch):
    real_load_json = _advance._load_json

    def no_op_run_script(script: str, args: list[str] | None = None):
        return {"script": script, "args": list(args or []), "ran": False}

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json":
            payload.setdefault("preflight", {})["selector_training_row_count"] = 1
            payload.setdefault("preflight", {})["blockers"] = [
                "selector_training_rows_forbidden"
            ]
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows"
            )
        if (
            relative
            == "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
        ):
            payload["blockers"] = ["selector_training_rows_forbidden"]
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows"
            )
        if (
            relative
            == "reports/strategy_arbitration/krk_sequence_policy_underpowered_pilot_v0.json"
        ):
            payload.setdefault("summary", {})[
                "forbidden_training_or_runtime_input_blocked"
            ] = True
            payload["blockers"] = ["selector_training_rows_forbidden"]
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_pilot_blocked_forbidden_training_or_runtime_rows"
            )
            payload["decision"]["recommended_next_step"] = (
                "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
            )
        if relative == "reports/krk_full_suite_readiness_audit_v0.json":
            payload.setdefault("sequence_policy", {})[
                "forbidden_training_or_runtime_input_blocked"
            ] = True
            payload.setdefault("hard_blockers", []).append(
                "sequence_policy_forbidden_training_or_runtime_rows"
            )
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows"
            )
        if relative == "reports/krk_full_suite_unblocker_packet_v0.json":
            payload.setdefault("current_state", {})[
                "sequence_policy_forbidden_training_or_runtime_input_blocked"
            ] = True
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_unblocker_blocked_forbidden_training_or_runtime_rows"
            )
        return payload

    monkeypatch.setattr(_advance, "_run_script", no_op_run_script)
    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert payload["summary"][
        "sequence_policy_forbidden_training_or_runtime_input_blocked"
    ] is True
    assert (
        "selector_training_rows_forbidden"
        in payload["summary"]["sequence_policy_forbidden_training_or_runtime_input_blockers"]
    )
    assert payload["decision"]["selector_training_allowed"] is False


def test_gate_advancement_routes_unsafe_protected_stack_to_repair(monkeypatch):
    real_load_json = _advance._load_json

    def no_op_run_script(script: str, args: list[str] | None = None):
        return {"script": script, "args": list(args or []), "ran": False}

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/krk_full_suite_readiness_audit_v0.json":
            protected_stack = payload.setdefault("protected_stack", {})
            protected_stack["ready"] = False
            protected_stack["rollback_paths_preserved"] = False
            protected_stack["active_stack_path_status"] = {"all_paths_safe": False}
            protected_stack["filesystem_snapshots_replaced"] = True
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_readiness_blocked_pending_protected_stack_repair"
            )
        return payload

    monkeypatch.setattr(_advance, "_run_script", no_op_run_script)
    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_blocked_pending_protected_stack_repair"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_protected_stack_validation"
    )
    assert payload["summary"]["protected_stack_ready"] is False
    assert payload["summary"]["protected_stack_rollback_paths_preserved"] is False
    assert payload["summary"]["protected_stack_active_paths_safe"] is False
    assert payload["summary"]["protected_stack_filesystem_snapshots_replaced"] is True
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_gate_advancement_routes_broken_protected_approval_request_to_repair(
    monkeypatch,
):
    real_load_json = _advance._load_json

    def no_op_run_script(script: str, args: list[str] | None = None):
        return {"script": script, "args": list(args or []), "ran": False}

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
        ):
            payload["blockers"] = ["full_suite_readiness_audit_not_clean"]
            payload["approval_request_ready_for_collection"] = False
            payload.setdefault("summary", {})["request_ready"] = False
            payload.setdefault("decision", {})["status"] = (
                "protected_plan_window_failure_contrast_approval_request_blocked"
            )
        if relative == "reports/krk_full_suite_readiness_audit_v0.json":
            gate = payload.setdefault("protected_failure_contrast_gate", {})
            gate["approval_request_status"] = (
                "protected_plan_window_failure_contrast_approval_request_blocked"
            )
            gate["approval_request_blockers"] = [
                "full_suite_readiness_audit_not_clean"
            ]
            gate["approval_request_ready_for_collection"] = False
            gate["ready_for_explicit_approval"] = False
            payload.setdefault("hard_blockers", []).append(
                "protected_plan_window_failure_contrast_approval_request_blocked"
            )
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_readiness_blocked_pending_"
                "protected_failure_contrast_approval_request_repair"
            )
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_sequence_policy_underpowered_pilot_v0.json"
        ):
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_pilot_blocked_pending_"
                "protected_failure_contrast_approval_request_repair"
            )
        return payload

    monkeypatch.setattr(_advance, "_run_script", no_op_run_script)
    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_blocked_pending_"
        "protected_failure_contrast_approval_request_repair"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_protected_failure_contrast_approval_request_scope"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_approval_request_status"
        ]
        == "protected_plan_window_failure_contrast_approval_request_blocked"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_approval_request_ready_for_collection"
        ]
        is False
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_gate_advancement_routes_blocked_execution_readiness_to_review(monkeypatch):
    real_load_json = _advance._load_json

    def no_op_run_script(script: str, args: list[str] | None = None):
        return {"script": script, "args": list(args or []), "ran": False}

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
        ):
            payload.setdefault("decision", {})["status"] = (
                "protected_plan_window_failure_contrast_execution_blocked"
            )
            payload.setdefault("summary", {})["jobs_passing_readiness"] = False
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_runner_v0.json"
        ):
            payload.setdefault("decision", {})["status"] = (
                "protected_plan_window_failure_contrast_runner_blocked"
            )
            payload.setdefault("summary", {})["processed_job_count"] = 0
            payload.setdefault("summary", {})["executed_job_count"] = 0
        if relative == "reports/krk_full_suite_readiness_audit_v0.json":
            gate = payload.setdefault("protected_failure_contrast_gate", {})
            gate["status"] = "protected_plan_window_failure_contrast_execution_blocked"
            gate["ready_for_explicit_approval"] = False
            gate["runner_status"] = "protected_plan_window_failure_contrast_runner_blocked"
            gate["approval_request_ready_for_collection"] = True
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_readiness_waiting_on_explicit_protected_failure_contrast_collection"
            )
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_sequence_policy_underpowered_pilot_v0.json"
        ):
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_pilot_blocked_pending_"
                "protected_failure_contrast_execution_readiness"
            )
        return payload

    monkeypatch.setattr(_advance, "_run_script", no_op_run_script)
    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_blocked_pending_"
        "protected_failure_contrast_execution_readiness"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_protected_plan_window_failure_contrast_execution_readiness"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_execution_readiness_status"
        ]
        == "protected_plan_window_failure_contrast_execution_blocked"
    )
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_runner_status"]
        == "protected_plan_window_failure_contrast_runner_blocked"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_gate_advancement_routes_missing_collection_option_to_gate_review(monkeypatch):
    real_load_json = _advance._load_json

    def no_op_run_script(script: str, args: list[str] | None = None):
        return {"script": script, "args": list(args or []), "ran": False}

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/krk_current_control_plane_gate_v0.json":
            payload["approval_options"] = [
                {
                    "option_id": (
                        "review_protected_plan_window_failure_contrast_execution_readiness"
                    ),
                    "command_if_explicitly_approved": None,
                }
            ]
        if relative == "reports/krk_full_suite_unblocker_packet_v0.json":
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_protected_failure_contrast_unblocker_blocked_pending_"
                "control_plane_gate_review"
            )
            payload.setdefault("primary_unblocker", {})["status"] = (
                "blocked_pending_protected_failure_contrast_control_plane_gate_review"
            )
        return payload

    monkeypatch.setattr(_advance, "_run_script", no_op_run_script)
    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_blocked_pending_"
        "protected_failure_contrast_control_plane_gate_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_collection_option_available"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_collection_command_available"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_collection_blocked_by_option_id"
        ]
        == "review_protected_plan_window_failure_contrast_execution_readiness"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_gate_advancement_routes_readiness_gate_review_blocker_to_gate_review(
    monkeypatch,
):
    real_load_json = _advance._load_json

    def no_op_run_script(script: str, args: list[str] | None = None):
        return {"script": script, "args": list(args or []), "ran": False}

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/krk_current_control_plane_gate_v0.json":
            for option in payload.get("approval_options") or []:
                if (
                    option.get("option_id")
                    == "approve_protected_plan_window_failure_contrast_collection"
                ):
                    option["command_if_explicitly_approved"] = None
        if relative == "reports/krk_full_suite_readiness_audit_v0.json":
            payload["control_plane_gate_review_blockers"] = [
                "protected_plan_window_failure_contrast_control_plane_gate_review_required"
            ]
            payload["blockers"] = payload["control_plane_gate_review_blockers"]
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_readiness_blocked_pending_"
                "protected_failure_contrast_control_plane_gate_review"
            )
            payload["decision"]["recommended_next_step"] = (
                "review_current_control_plane_gate_for_protected_failure_contrast_collection"
            )
        return payload

    monkeypatch.setattr(_advance, "_run_script", no_op_run_script)
    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_blocked_pending_"
        "protected_failure_contrast_control_plane_gate_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    )
    assert payload["summary"]["readiness_control_plane_gate_review_blockers"] == [
        "protected_plan_window_failure_contrast_control_plane_gate_review_required"
    ]
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_collection_option_available"
        ]
        is True
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_collection_command_available"
        ]
        is False
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_gate_advancement_summary_falls_back_when_request_ready_flags_are_null(monkeypatch):
    real_load_json = _advance._load_json

    def no_op_run_script(script: str, args: list[str] | None = None):
        return {"script": script, "args": list(args or []), "ran": False}

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/krk_stage4_caveat_unblocker_packet_v0.json":
            payload.setdefault("current_stage4_status", {})[
                "approval_request_ready_for_runtime_approval"
            ] = None
        if relative == "reports/krk_full_suite_readiness_audit_v0.json":
            payload.setdefault("protected_failure_contrast_gate", {})[
                "approval_request_ready_for_collection"
            ] = None
        return payload

    monkeypatch.setattr(_advance, "_run_script", no_op_run_script)
    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_approval_request_status"
        ]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_approval_request_blockers"
        ]
        == []
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_approval_request_ready_for_runtime_approval"
        ]
        is True
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_approval_request_status"
        ]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_approval_request_blockers"
        ]
        == []
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_approval_request_ready_for_collection"
        ]
        is True
    )

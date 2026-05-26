#!/usr/bin/env python3
"""Tests for the KRK full-suite readiness audit."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_audit = _load_module(
    "write_krk_full_suite_readiness_audit_v0",
    "scripts/write_krk_full_suite_readiness_audit_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_full_suite_readiness_audit_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_full_suite_readiness_artifact_preserves_boundaries():
    payload = _read_report()

    assert payload["schema_version"] == "krk_full_suite_readiness_audit.v0"
    assert payload["causal_status"] == "non_causal_readiness_audit"
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
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False

    boundaries = payload["runtime_and_training_boundaries"]
    assert boundaries["checked_flag_count"] >= 430
    assert boundaries["violation_count"] == 0
    assert boundaries["runtime_behavior_changed"] is False
    assert boundaries["runtime_selector_implemented"] is False
    assert boundaries["runtime_score_changes"] is False
    assert boundaries["runtime_direct_routing"] is False
    assert boundaries["runtime_dtm_or_tablebase_lookup"] is False
    assert boundaries["hidden_python_controller"] is False
    assert boundaries["gameplay_topology_mutation"] is False
    assert (
        payload["source_artifacts"]["control_plane_filtered_frames"]
        == "reports/krk_control_plane_filtered_frames_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_forced_controls"]
        == "reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json"
    )
    assert (
        payload["source_artifacts"]["sequence_benchmark_inputs"]
        == "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
    )
    assert (
        payload["source_artifacts"]["stage7_sampling_manifest"]
        == "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"]["protected_proposal_coverage_expansion_plan"]
        == "reports/krk_protected_proposal_coverage_expansion_plan_v0.json"
    )
    assert (
        payload["source_artifacts"]["protected_provider_coverage_frames"]
        == "reports/krk_protected_provider_coverage_frames_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "protected_provider_capacity_frame_training_semantics_review"
        ]
        == "reports/krk_protected_provider_capacity_frame_training_semantics_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["candidate_generator_coverage_audit"]
        == "reports/krk_candidate_generator_coverage_audit_v0.json"
    )
    assert (
        payload["source_artifacts"]["validated_provider_candidate_set_audit"]
        == "reports/krk_validated_provider_candidate_set_audit_v0.json"
    )
    assert (
        payload["source_artifacts"]["two_stage_candidate_selection_benchmark"]
        == "reports/krk_two_stage_candidate_selection_benchmark_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_sequence_candidate_frames_v1"]
        == "reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json"
    )
    assert (
        payload["source_artifacts"]["candidate_frame_source_benchmark_v1"]
        == "reports/strategy_arbitration/krk_candidate_frame_source_benchmark_v1.json"
    )
    assert (
        payload["source_artifacts"]["candidate_generation_sandbox_review"]
        == "reports/strategy_arbitration/krk_candidate_generation_sandbox_review_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "protected_strategy_monitor_observation_source_review_packet_v1"
        ]
        == "reports/strategy_arbitration/krk_protected_strategy_monitor_observation_source_review_packet_v1.json"
    )
    assert (
        payload["source_artifacts"]["repair_monitor_observation_source_smoke_v1"]
        == "reports/strategy_arbitration/krk_repair_monitor_observation_source_smoke_v1.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_sequence_repair_monitor_trace_features_v1"
        ]
        == "reports/strategy_arbitration/krk_strategy_sequence_repair_monitor_trace_features_v1.json"
    )
    assert (
        payload["source_artifacts"]["strategy_sequence_dataset_v2"]
        == "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2.json"
    )
    assert (
        payload["source_artifacts"][
            "candidate_generation_refresh_probe_v2_after_labels"
        ]
        == "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_after_labels.json"
    )
    assert (
        payload["source_artifacts"][
            "stage5_6_candidate_generation_refresh_review_packet_v3"
        ]
        == "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_review_packet_v3.json"
    )
    assert (
        payload["source_artifacts"][
            "stage5_6_candidate_generation_refresh_broadened"
        ]
        == "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_broadened_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_sequence_stage5_6_refresh_trace_features"
        ]
        == "reports/strategy_arbitration/krk_strategy_sequence_stage5_6_refresh_trace_features_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_sequence_dataset_design_v3"]
        == "reports/strategy_arbitration/krk_strategy_sequence_dataset_design_v3.json"
    )
    assert (
        payload["source_artifacts"][
            "candidate_generation_cross_stage_capacity_review_v2"
        ]
        == "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_review_v2.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_sequence_dataset_v2_cross_stage_capacity_merged"
        ]
        == "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_cross_stage_capacity_merged.json"
    )
    assert (
        payload["source_artifacts"][
            "stage_conditioned_candidate_generation_benchmark_v3"
        ]
        == "reports/strategy_arbitration/krk_stage_conditioned_candidate_generation_benchmark_v3.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_sequence_candidate_generation_refresh_trace_features"
        ]
        == "reports/strategy_arbitration/krk_strategy_sequence_candidate_generation_refresh_trace_features_v1.json"
    )
    assert (
        payload["source_artifacts"]["ownership_label_recovery_review"]
        == "reports/strategy_arbitration/krk_ownership_label_recovery_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_objective_seed_manifest_v0"]
        == "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"]["joined_trace_ownership_collection"]
        == "reports/strategy_arbitration/krk_joined_trace_ownership_collection_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_objective_feature_probe_review"]
        == "reports/strategy_arbitration/krk_selector_objective_feature_probe_review_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "stage4_joined_trace_ownership_scope_review_packet"
        ]
        == "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_scope_review_packet_v0.json"
    )
    assert (
        payload["source_artifacts"]["stage4_joined_trace_ownership_collection"]
        == "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_collection_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_objective_seed_manifest_v2"]
        == "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json"
    )
    assert (
        payload["source_artifacts"]["selector_objective_independent_validation_blocker"]
        == "reports/strategy_arbitration/krk_selector_objective_independent_validation_blocker_v0.json"
    )
    assert (
        payload["source_artifacts"]["stage4_failure_discovery"]
        == "reports/krk_stage4_failure_discovery_v0.json"
    )
    assert (
        payload["source_artifacts"]["stage4_stratified_contrast_validation"]
        == "reports/krk_stage4_stratified_contrast_validation_v0.json"
    )
    assert (
        payload["source_artifacts"]["sequence_control_contrast_dataset"]
        == "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_sequence_dataset_v3"]
        == "reports/strategy_arbitration/krk_strategy_sequence_dataset_v3.json"
    )
    assert (
        payload["source_artifacts"]["candidate_generation_training_refresh_benchmark_v3"]
        == "reports/strategy_arbitration/krk_candidate_generation_training_refresh_benchmark_v3.json"
    )
    assert (
        payload["source_artifacts"][
            "candidate_generation_training_refresh_runtime_review_v3"
        ]
        == "reports/strategy_arbitration/krk_candidate_generation_training_refresh_runtime_review_packet_v3.json"
    )
    assert (
        payload["source_artifacts"]["candidate_generation_refresh_sandbox"]
        == "reports/strategy_arbitration/krk_candidate_generation_refresh_sandbox_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_sequence_dataset_v5"]
        == "reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.json"
    )
    assert (
        payload["source_artifacts"]["candidate_generation_v5_next_boundary_review"]
        == "reports/strategy_arbitration/krk_candidate_generation_v5_next_boundary_review_v0.json"
    )


def test_full_suite_readiness_identifies_current_gate():
    payload = _read_report()

    assert payload["protected_stack"]["ready"] is True
    assert payload["protected_stack"]["clean_stack_adopted"] is True
    assert payload["protected_stack"]["clean_stack_adopted_and_validated"] is True
    assert payload["protected_stack"]["post_adoption_validation_required"] is True
    assert payload["protected_stack"]["rollback_paths_preserved"] is True
    assert payload["protected_stack"]["active_stack_path_status"]["all_paths_safe"] is True
    assert payload["protected_stack"]["active_stack_path_status"]["all_paths_exist"] is True
    assert payload["protected_stack"]["rollback_stack_path_status"]["all_paths_safe"] is True
    assert payload["protected_stack"]["rollback_stack_path_status"]["all_paths_exist"] is True
    assert payload["protected_stack"]["rollback_common_paths_distinct"] is True
    assert payload["protected_stack"]["m1_m4_preservation_passed"] is True
    assert payload["protected_stack"]["kpk_kqk_bridge_preservation_passed"] is True

    stage7 = payload["stage7_sampling_gate"]
    assert stage7["runner_status"] == "stage7_diverse_clean_sampling_runner_executed_success"
    assert stage7["processed_job_count"] == 0
    assert stage7["executed_job_count"] == 0
    assert stage7["historical_processed_job_count"] == 8
    assert stage7["historical_executed_job_count"] == 8
    assert stage7["output_validation_status"] == (
        "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert stage7["runner_output_validation_status"] == (
        "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert stage7["output_valid_count"] == 8
    assert stage7["execution_readiness_source"] == "live_recomputed"
    assert (
        stage7["execution_readiness_status"]
        == "not_applicable_stage7_success_gate_closed"
    )
    assert (
        stage7["historical_execution_readiness_status"]
        == "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
    )
    assert stage7["execution_readiness_jobs_passing"] == 8
    assert stage7["invalid_existing_output_count"] == 0
    assert stage7["job_timeout_seconds"] == 900
    assert stage7["timed_out_job_count"] == 0
    assert stage7["overwrite_existing_outputs"] is False
    assert stage7["success_controls_ready"] is True
    assert stage7["label_gate_status"] == "stage7_success_gate_closed_no_current_label_approval"
    assert stage7["label_run_allowed_by_artifact"] is False
    assert stage7["historical_label_run_allowed_by_runner"] is True
    assert stage7["combined_success_controls"] == 11
    assert stage7["combined_success_controls"] >= stage7["success_controls_required"]

    stage4 = payload["stage_status"]["stage4"]
    assert (
        stage4["status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    assert stage4["ready_for_explicit_runtime_approval"] is True
    assert stage4["implementation_allowed_by_current_artifact"] is False
    assert stage4["approval_request_artifact"] == (
        "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
    )
    assert (
        stage4["approval_request_status"]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert stage4["approval_request_blockers"] == []
    assert stage4["approval_request_ready_for_runtime_approval"] is True
    assert stage4["approval_request_created"] is False
    assert stage4["implementation_authorized_by_approval_request"] is False

    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_waiting_on_explicit_protected_failure_contrast_collection"
    )
    assert payload["hard_blockers"] == []
    assert payload["control_plane_gate_review_blockers"] == []
    assert payload["explicit_gate_blockers"] == [
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
    ]
    assert payload["blockers"] == payload["explicit_gate_blockers"]
    assert payload["stage_status"]["stage8"]["blocker"] == (
        "Protected plan-window failure-contrast evidence is not integrated; "
        "Stage 8 remains blocked pending explicit protected failure-contrast "
        "collection and passive integration."
    )
    assert payload["approval_gates"]["stage8_training"]["why"] == (
        "Protected plan-window failure-contrast evidence is not integrated; "
        "Stage 8 training remains blocked even though Stage 7 held-out controls "
        "are balanced."
    )
    assert payload["current_control_plane_gate"]["selector_allowed"] is False
    assert payload["current_control_plane_gate"]["runtime_direct_routing"] is False
    assert payload["current_control_plane_gate"]["hidden_python_controller"] is False
    assert (
        "approve_protected_plan_window_failure_contrast_collection"
        in payload["current_control_plane_gate"]["approval_option_ids"]
    )
    assert (
        payload["current_control_plane_gate"][
            "protected_failure_contrast_collection_option_available"
        ]
        is True
    )
    assert (
        payload["current_control_plane_gate"][
            "protected_failure_contrast_collection_command_available"
        ]
        is True
    )
    assert (
        payload["current_control_plane_gate"][
            "protected_failure_contrast_collection_option_id"
        ]
        == "approve_protected_plan_window_failure_contrast_collection"
    )
    assert (
        payload["current_control_plane_gate"][
            "protected_failure_contrast_collection_blocked_by_option_id"
        ]
        is None
    )

    sequence = payload["sequence_policy"]
    assert (
        sequence["benchmark_design_status"]
        == "sequence_policy_benchmark_design_ready_non_causal"
    )
    assert (
        sequence["post_failure_contrast_refresh_status"]
        == "sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs"
    )
    assert (
        sequence["post_failure_contrast_refresh_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert sequence["post_failure_contrast_refresh_boundaries_preserved"] is True
    assert sequence["post_failure_contrast_refresh_boundary_violation_count"] == 0
    assert (
        sequence["post_failure_contrast_refresh_integration_status"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs"
    )
    assert sequence["post_failure_contrast_refresh_integration_ready"] is False
    assert sequence["post_failure_contrast_refresh_integrated_new_failure_count"] == 0
    assert sequence["post_failure_contrast_refresh_row_count"] == 0
    assert sequence["post_failure_contrast_refresh_stage7_training_row_count"] == 0
    assert (
        sequence["passive_design_without_new_labels_status"]
        == "non_causal_sequence_policy_design_without_new_labels_ready"
    )
    assert (
        sequence["passive_design_current_evidence_limit"]
        == "protected_plan_window_failure_evidence_sparse"
    )
    assert sequence["passive_design_depends_on_new_label_execution"] is False
    assert (
        sequence["passive_design_depends_on_protected_failure_contrast_collection"]
        is False
    )
    assert (
        sequence["cross_stage_requirements_status"]
        == "cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark"
    )
    assert sequence["replay_free_protected_cross_stage_evidence"] is True
    assert sequence["cross_stage_sequence_evidence_met"] is True

    protected_failure_contrast = payload["protected_failure_contrast_gate"]
    assert (
        protected_failure_contrast["plan_status"]
        == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
    )
    assert protected_failure_contrast["unique_failure_count"] == 1
    assert protected_failure_contrast["minimum_new_failures_needed"] == 4
    assert (
        protected_failure_contrast["manifest_status"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert protected_failure_contrast["manifest_job_count"] == 6
    assert (
        protected_failure_contrast["manifest_review_status"]
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    )
    assert (
        protected_failure_contrast["execution_readiness_status"]
        == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
    )
    assert protected_failure_contrast["execution_jobs_passing"] == 6
    assert (
        protected_failure_contrast["runner_status"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert (
        protected_failure_contrast["runner_manifest_status"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert protected_failure_contrast["runner_manifest_declared_job_count"] == 6
    assert len(protected_failure_contrast["runner_manifest_fingerprint"]) == 64
    assert protected_failure_contrast["runner_collection_run_allowed"] is False
    assert protected_failure_contrast["runner_processed_job_count"] == 0
    assert protected_failure_contrast["runner_executed_job_count"] == 0
    assert (
        protected_failure_contrast["output_validation_status"]
        == "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert protected_failure_contrast["output_exists_count"] == 0
    assert protected_failure_contrast["output_valid_count"] == 0
    assert (
        protected_failure_contrast["integration_status"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs"
    )
    assert protected_failure_contrast["integrated_new_failure_count"] == 0
    assert protected_failure_contrast["integration_ready"] is False
    assert protected_failure_contrast["ready_for_explicit_approval"] is True
    assert protected_failure_contrast["approval_request_ready_for_collection"] is True
    assert protected_failure_contrast["current_artifact_allows_collection"] is False
    assert protected_failure_contrast["approval_receipt_required"] is True
    assert protected_failure_contrast["approval_receipt_path"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert protected_failure_contrast["approval_receipt_present"] is False
    assert protected_failure_contrast["approval_receipt_valid"] is False
    assert protected_failure_contrast["approval_receipt_blockers"] == [
        "approval_receipt_missing"
    ]
    assert protected_failure_contrast["approval_request_artifact"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
    )
    assert (
        protected_failure_contrast["approval_request_status"]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert protected_failure_contrast["approval_request_blockers"] == []
    assert protected_failure_contrast["approval_receipt_created_by_request"] is False
    assert protected_failure_contrast["post_success_refresh_required"] is True
    assert protected_failure_contrast["post_success_refresh_script"] == (
        "scripts/advance_krk_suite_from_current_gates_v0.py"
    )
    assert protected_failure_contrast["post_success_refresh_scope"] == (
        "full_passive_krk_suite_gate_stack"
    )
    assert len(protected_failure_contrast["expected_manifest_fingerprint"]) == 64
    assert len(protected_failure_contrast["expected_readiness_fingerprint"]) == 64
    assert protected_failure_contrast["command_if_explicitly_approved"] == (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection --refresh-after-run "
        "--approval-receipt "
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert protected_failure_contrast["runtime_behavior_changed"] is False
    assert protected_failure_contrast["runtime_defaults_changed"] is False
    assert protected_failure_contrast["runtime_selector_implemented"] is False
    assert protected_failure_contrast["runtime_score_changes"] is False
    assert protected_failure_contrast["runtime_direct_routing"] is False
    assert protected_failure_contrast["runtime_dtm_or_tablebase_lookup"] is False
    assert protected_failure_contrast["hidden_python_controller"] is False
    assert protected_failure_contrast["gameplay_topology_mutation"] is False
    assert protected_failure_contrast["selector_training_allowed"] is False
    assert protected_failure_contrast["stage7_promotion_allowed"] is False
    assert protected_failure_contrast["stage8_training_allowed"] is False

    missing_provider = payload["protected_missing_provider_gate"]
    assert (
        missing_provider["labels_status"]
        == "protected_missing_provider_capacity_labels_completed"
    )
    assert missing_provider["label_count"] == 16
    assert missing_provider["label_result_counts"] == {"mate": 11, "max_plies": 5}
    assert missing_provider["stage7_label_count"] == 0
    assert missing_provider["stage7_training_label_count"] == 0
    assert (
        missing_provider["merge_status"]
        == "protected_missing_provider_labels_unmatched_by_current_proposal_frames"
    )
    assert missing_provider["matched_label_count"] == 0
    assert missing_provider["unmatched_label_count"] == 16
    assert (
        missing_provider["coverage_status"]
        == "proposal_provider_coverage_gap_blocks_selector_training"
    )
    assert missing_provider["coverage_label_count"] == 16
    assert missing_provider["coverage_frames_present_count"] == 16
    assert missing_provider["provider_present_in_frame_count"] == 0
    assert missing_provider["provider_missing_from_frame_count"] == 16
    assert missing_provider["missing_provider_mate_label_count"] == 11
    assert missing_provider["current_gap_blocks_selector_training"] is True
    assert (
        missing_provider["coverage_expansion_plan_status"]
        == "protected_proposal_coverage_expansion_plan_ready"
    )
    assert missing_provider["coverage_expansion_rows_to_create"] == 16
    assert missing_provider["coverage_expansion_training_allowed_initially"] is False
    assert (
        missing_provider[
            "coverage_expansion_requires_followup_review_before_training_use"
        ]
        is True
    )
    assert (
        missing_provider["coverage_frames_status"]
        == "protected_provider_coverage_frames_built"
    )
    assert missing_provider["coverage_frame_row_count"] == 16
    assert missing_provider["coverage_frame_positive_capacity_count"] == 11
    assert missing_provider["coverage_frame_negative_capacity_count"] == 5
    assert missing_provider["coverage_frame_stage7_row_count"] == 0
    assert missing_provider["coverage_frame_training_row_count"] == 0
    assert missing_provider["coverage_frame_runtime_proposal_row_count"] == 0
    assert (
        missing_provider["training_semantics_review_status"]
        == "capacity_frames_diagnostic_not_selector_training_ready"
    )
    assert missing_provider["training_semantics_selector_training_allowed"] is False
    assert missing_provider["training_semantics_runtime_work_allowed"] is False
    assert missing_provider["training_semantics_row_count"] == 16
    assert missing_provider["training_semantics_positive_capacity_count"] == 11
    assert missing_provider["training_semantics_negative_capacity_count"] == 5
    assert missing_provider["training_semantics_stage7_row_count"] == 0
    assert missing_provider["training_semantics_training_row_count"] == 0
    assert missing_provider["training_semantics_runtime_proposal_row_count"] == 0
    assert (
        "direct_selector_training_positive"
        in missing_provider["training_semantics_blocked_uses"]
    )
    assert (
        missing_provider["candidate_generator_coverage_status"]
        == "candidate_generator_recall_gap_confirmed"
    )
    assert missing_provider["candidate_generator_positive_recall_count"] == 0
    assert missing_provider["candidate_generator_positive_recall_rate"] == 0.0
    assert missing_provider["candidate_generator_missing_positive_capacity_count"] == 11
    assert (
        missing_provider["validated_candidate_set_status"]
        == "validated_provider_candidate_set_recall_promising_requires_selector_semantics"
    )
    assert missing_provider["validated_candidate_set_state_count"] == 6
    assert missing_provider["validated_candidate_set_added_candidate_count"] == 16
    assert missing_provider["validated_candidate_set_added_positive_capacity_count"] == 11
    assert missing_provider["validated_candidate_set_added_negative_capacity_count"] == 5
    assert missing_provider["validated_candidate_set_candidate_generator_runtime_allowed"] is False
    assert missing_provider["validated_candidate_set_selector_training_allowed"] is False
    assert missing_provider["validated_candidate_set_positive_capacity_recall_if_included"] == 1.0
    assert (
        missing_provider["two_stage_review_status"]
        == "two_stage_non_causal_benchmark_design_needed"
    )
    assert missing_provider["two_stage_review_candidate_generator_runtime_allowed"] is False
    assert missing_provider["two_stage_review_selector_training_allowed"] is False
    assert missing_provider["two_stage_review_positive_capacity_recovered"] == 11
    assert missing_provider["two_stage_review_negative_capacity_also_included"] == 5
    assert (
        missing_provider["two_stage_benchmark_plan_status"]
        == "two_stage_candidate_selection_benchmark_plan_ready"
    )
    assert (
        missing_provider["two_stage_benchmark_status"]
        == "candidate_generation_recall_improves_selection_not_ready"
    )
    assert missing_provider["two_stage_benchmark_current_positive_recall_rate"] == 0.0
    assert missing_provider["two_stage_benchmark_expanded_positive_recall_rate"] == 1.0
    assert missing_provider["two_stage_benchmark_expanded_negative_inclusion_rate"] == 1.0
    assert missing_provider["two_stage_benchmark_selector_ready"] is False
    assert missing_provider["two_stage_benchmark_best_negative_suppression"] == 0.0
    assert missing_provider["two_stage_benchmark_stage7_training_leakage"] is False
    assert missing_provider["two_stage_benchmark_candidate_generator_runtime_allowed"] is False
    assert missing_provider["two_stage_benchmark_selector_training_allowed"] is False
    assert missing_provider["runtime_work_allowed"] is False
    assert missing_provider["selector_training_allowed"] is False
    assert missing_provider["stage7_promotion_allowed"] is False
    assert missing_provider["stage8_training_allowed"] is False

    strategy_source = payload["strategy_sequence_candidate_source_gate"]
    assert (
        strategy_source["schema_status"]
        == "strategy_sequence_candidate_frame_schema_defined"
    )
    assert strategy_source["schema_runtime_sandbox_allowed"] is False
    assert (
        strategy_source["frames_status"]
        == "strategy_sequence_frames_populated_non_causal"
    )
    assert strategy_source["frames_frame_count"] == 256
    assert strategy_source["frames_frame_type_counts"] == {
        "broader_krk_strategy_candidate": 13,
        "candidate_move_hypothesis": 140,
        "validated_provider_candidate": 103,
    }
    assert strategy_source["frames_capacity_evidence_row_count"] == 16
    assert strategy_source["frames_candidate_generation_training_row_count"] == 11
    assert strategy_source["frames_stage7_challenge_row_count"] == 198
    assert strategy_source["frames_stage7_readiness_training_row_count"] == 0
    assert (
        strategy_source["quality_status"]
        == "frame_quality_probe_supports_next_sequence_candidate_benchmark"
    )
    assert strategy_source["quality_capacity_not_selector_label"] is True
    assert strategy_source["quality_runtime_flags_false"] is True
    assert strategy_source["quality_protected_frame_count"] == 58
    assert strategy_source["quality_protected_positive_capacity_candidate_count"] == 11
    assert strategy_source["quality_sequence_candidate_count"] == 140
    assert strategy_source["quality_sequence_candidate_mate_count"] == 0
    assert (
        strategy_source["source_benchmark_status"]
        == "candidate_generation_sources_promising_selector_blocked"
    )
    assert strategy_source["source_benchmark_protected_positive_capacity_ratio"] == 0.6875
    assert strategy_source["source_benchmark_protected_negative_capacity_ratio"] == 0.3125
    assert (
        strategy_source[
            "source_benchmark_progress_window_sequence_candidate_mate_count"
        ]
        == 0
    )
    assert (
        strategy_source["control_plane_status"]
        == "candidate_generation_control_plane_ready_for_architecture_review"
    )
    assert strategy_source["control_plane_runtime_sandbox_allowed"] is False
    assert (
        strategy_source["sandbox_review_status"]
        == "candidate_generation_observation_sandbox_review_ready"
    )
    assert strategy_source["sandbox_review_implementation_authorized"] is False
    assert (
        strategy_source["sandbox_review_recommended_first_sandbox"]
        == "default_off_observation_only_candidate_generation"
    )
    assert (
        strategy_source["source_design_status"]
        == "broader_strategy_sequence_candidate_source_design_ready"
    )
    assert strategy_source["source_design_implementation_allowed"] is False
    assert (
        strategy_source["plan_capsule_source_status"]
        == "plan_capsule_sequence_observation_source_schema_ready_but_stage7_only"
    )
    assert (
        strategy_source["broader_strategy_source_status"]
        == "broader_strategy_observation_source_schema_ready_but_stage7_only"
    )
    assert (
        strategy_source["source_review_status"]
        == "source_reviews_complete_runtime_expansion_not_authorized"
    )
    assert strategy_source["source_review_implementation_allowed"] is False
    assert (
        strategy_source["protected_monitor_expansion_status"]
        == "protected_strategy_monitor_frames_expanded_non_causal"
    )
    assert strategy_source["protected_monitor_expansion_frame_count"] == 85
    assert strategy_source["protected_monitor_expansion_stage7_challenge_row_count"] == 0
    assert (
        strategy_source["protected_monitor_quality_status"]
        == "protected_strategy_monitor_frames_have_monitor_signal"
    )
    assert strategy_source["protected_monitor_quality_strong_failure_family_count"] == 1
    assert (
        strategy_source["repair_monitor_review_status"]
        == "protected_repair_monitor_observation_source_review_ready"
    )
    assert strategy_source["repair_monitor_review_implementation_authorized"] is False
    assert strategy_source["runtime_work_allowed"] is False
    assert strategy_source["runtime_candidate_generation_allowed"] is False
    assert strategy_source["selector_allowed"] is False
    assert strategy_source["selector_training_allowed"] is False
    assert strategy_source["stage7_promotion_allowed"] is False
    assert strategy_source["stage8_training_allowed"] is False

    repair_monitor_trace = payload["repair_monitor_trace_feature_gate"]
    assert (
        repair_monitor_trace["smoke_status"]
        == "repair_monitor_observation_source_wired_default_off_equivalent"
    )
    assert repair_monitor_trace["smoke_case_count"] == 3
    assert repair_monitor_trace["smoke_repair_monitor_frame_count"] == 3
    assert repair_monitor_trace["smoke_selected_move_provider_delta_count"] == 0
    assert repair_monitor_trace["smoke_invariant_failure_count"] == 0
    assert repair_monitor_trace["smoke_stage7_case_count"] == 0
    assert (
        repair_monitor_trace["coverage_status"]
        == "repair_monitor_observation_source_coverage_ready_for_guarded_analysis"
    )
    assert repair_monitor_trace["coverage_repair_monitor_frame_count"] == 3
    assert repair_monitor_trace["coverage_stage7_case_count"] == 0
    assert (
        repair_monitor_trace["broadened_status"]
        == "repair_monitor_observation_source_broadened_default_off_equivalent"
    )
    assert repair_monitor_trace["broadened_case_count"] == 6
    assert repair_monitor_trace["broadened_case_count_by_stage"] == {
        "stage4": 1,
        "stage5": 4,
        "stage6": 1,
    }
    assert repair_monitor_trace["broadened_repair_monitor_frame_count"] == 6
    assert repair_monitor_trace["broadened_selected_move_provider_delta_count"] == 0
    assert repair_monitor_trace["broadened_invariant_failure_count"] == 0
    assert repair_monitor_trace["broadened_stage7_case_count"] == 0
    assert (
        repair_monitor_trace["quality_status"]
        == "repair_monitor_observation_source_quality_trace_only_retained"
    )
    assert repair_monitor_trace["quality_source_stable"] is True
    assert repair_monitor_trace["quality_risk_term_set_count"] == 1
    assert repair_monitor_trace["quality_stage7_case_count"] == 0
    assert (
        repair_monitor_trace["trace_features_status"]
        == "repair_monitor_trace_features_folded_non_causal"
    )
    assert repair_monitor_trace["trace_features_trace_frame_count"] == 6
    assert repair_monitor_trace["trace_features_stage7_trace_frame_count"] == 0
    assert repair_monitor_trace["trace_features_selector_training_row_count"] == 0
    assert (
        repair_monitor_trace[
            "trace_features_candidate_generation_training_row_count"
        ]
        == 0
    )
    assert (
        repair_monitor_trace["integration_review_status"]
        == "strategy_sequence_trace_features_integrated_selector_still_blocked"
    )
    assert repair_monitor_trace["integration_review_trace_integration_safe"] is True
    assert repair_monitor_trace["integration_review_trace_frame_count"] == 6
    assert repair_monitor_trace["integration_review_trace_selector_training_row_count"] == 0
    assert repair_monitor_trace["integration_review_trace_stage7_frame_count"] == 0
    assert (
        repair_monitor_trace["dataset_design_status"]
        == "strategy_sequence_dataset_design_v2_ready"
    )
    assert repair_monitor_trace["dataset_design_implementation_allowed"] is False
    assert (
        repair_monitor_trace["dataset_v2_status"]
        == "strategy_sequence_dataset_v2_refreshed_non_causal_selector_blocked"
    )
    assert repair_monitor_trace["dataset_v2_row_count"] == 262
    assert repair_monitor_trace["dataset_v2_runtime_trace_feature_row_count"] == 6
    assert repair_monitor_trace["dataset_v2_candidate_generation_training_row_count"] == 11
    assert repair_monitor_trace["dataset_v2_selector_training_row_count"] == 0
    assert repair_monitor_trace["dataset_v2_stage7_challenge_row_count"] == 198
    assert repair_monitor_trace["dataset_v2_stage7_readiness_training_row_count"] == 0
    assert (
        repair_monitor_trace["dataset_v2_quality_status"]
        == "strategy_sequence_dataset_v2_quality_candidate_generation_ready_selector_blocked"
    )
    assert repair_monitor_trace["dataset_v2_quality_runtime_flags_false"] is True
    assert repair_monitor_trace["dataset_v2_quality_selector_rows_absent"] is True
    assert repair_monitor_trace["dataset_v2_quality_stage7_excluded_from_readiness"] is True
    assert (
        repair_monitor_trace["refresh_probe_status"]
        == "candidate_generation_refresh_underpowered_selector_blocked"
    )
    assert (
        repair_monitor_trace["refresh_probe_best_policy"]
        == "stage_family_pure_positive_with_support_2"
    )
    assert repair_monitor_trace["refresh_probe_positive_recall"] == 0.6363636363636364
    assert repair_monitor_trace["refresh_probe_negative_suppression"] == 1
    assert (
        repair_monitor_trace["capacity_manifest_status"]
        == "candidate_generation_capacity_evidence_manifest_ready"
    )
    assert repair_monitor_trace["capacity_manifest_labels_run_by_this_artifact"] is False
    assert repair_monitor_trace["capacity_manifest_job_count"] == 12
    assert repair_monitor_trace["capacity_manifest_stage7_job_count"] == 0
    assert (
        repair_monitor_trace["capacity_labels_status"]
        == "candidate_generation_capacity_evidence_labels_completed"
    )
    assert repair_monitor_trace["capacity_labels_label_count"] == 12
    assert repair_monitor_trace["capacity_labels_stage7_label_count"] == 0
    assert repair_monitor_trace["capacity_labels_stage7_training_label_count"] == 0
    assert (
        repair_monitor_trace["dataset_v2_capacity_merged_status"]
        == "strategy_sequence_dataset_v2_capacity_merged_non_causal"
    )
    assert repair_monitor_trace["dataset_v2_capacity_merged_row_count"] == 274
    assert (
        repair_monitor_trace[
            "dataset_v2_capacity_merged_candidate_generation_training_row_count"
        ]
        == 19
    )
    assert repair_monitor_trace["dataset_v2_capacity_merged_selector_training_row_count"] == 0
    assert (
        repair_monitor_trace[
            "dataset_v2_capacity_merged_stage7_readiness_training_row_count"
        ]
        == 0
    )
    assert (
        repair_monitor_trace["refresh_after_labels_status"]
        == "candidate_generation_refresh_supported_selector_blocked"
    )
    assert (
        repair_monitor_trace["refresh_after_labels_best_policy"]
        == "stage_family_pure_positive_with_support_2"
    )
    assert repair_monitor_trace["refresh_after_labels_positive_recall"] == 0.7368421052631579
    assert repair_monitor_trace["refresh_after_labels_negative_suppression"] == 1
    assert repair_monitor_trace["runtime_work_allowed"] is False
    assert repair_monitor_trace["runtime_candidate_generation_allowed"] is False
    assert repair_monitor_trace["selector_allowed"] is False
    assert repair_monitor_trace["selector_training_allowed"] is False
    assert repair_monitor_trace["stage7_promotion_allowed"] is False
    assert repair_monitor_trace["stage8_training_allowed"] is False

    stage5_6_refresh = payload["stage5_6_candidate_generation_refresh_gate"]
    assert (
        stage5_6_refresh["review_status"]
        == "stage5_6_candidate_generation_refresh_review_ready"
    )
    assert stage5_6_refresh["review_runtime_review_ready"] is True
    assert stage5_6_refresh["review_implementation_authorized"] is False
    assert (
        stage5_6_refresh["review_runtime_candidate_generator_refresh_allowed"]
        is False
    )
    assert (
        stage5_6_refresh["smoke_status"]
        == "stage5_6_candidate_generation_refresh_wired_default_off_equivalent"
    )
    assert stage5_6_refresh["smoke_case_count"] == 2
    assert stage5_6_refresh["smoke_refresh_frame_count"] == 13
    assert stage5_6_refresh["smoke_selected_move_provider_delta_count"] == 0
    assert stage5_6_refresh["smoke_invariant_failure_count"] == 0
    assert stage5_6_refresh["smoke_stage7_case_count"] == 0
    assert (
        stage5_6_refresh["coverage_status"]
        == "stage5_6_refresh_coverage_ready_for_broadened_analysis"
    )
    assert stage5_6_refresh["coverage_refresh_frame_count"] == 13
    assert stage5_6_refresh["coverage_selected_move_provider_delta_count"] == 0
    assert stage5_6_refresh["coverage_invariant_failure_count"] == 0
    assert stage5_6_refresh["coverage_stage7_case_count"] == 0
    assert (
        stage5_6_refresh["broadened_status"]
        == "stage5_6_candidate_generation_refresh_broadened_default_off_equivalent"
    )
    assert stage5_6_refresh["broadened_case_count"] == 4
    assert stage5_6_refresh["broadened_case_count_by_stage"] == {
        "stage5": 3,
        "stage6": 1,
    }
    assert stage5_6_refresh["broadened_refresh_frame_count"] == 38
    assert stage5_6_refresh["broadened_selected_move_provider_delta_count"] == 0
    assert stage5_6_refresh["broadened_invariant_failure_count"] == 0
    assert stage5_6_refresh["broadened_stage7_case_count"] == 0
    assert (
        stage5_6_refresh["quality_status"]
        == "stage5_6_candidate_generation_refresh_quality_trace_only_retained"
    )
    assert (
        stage5_6_refresh["quality_trace_usable_for_candidate_generation_context"]
        is True
    )
    assert stage5_6_refresh["quality_refresh_frame_count"] == 38
    assert stage5_6_refresh["quality_selected_move_provider_delta_count"] == 0
    assert stage5_6_refresh["quality_invariant_failure_count"] == 0
    assert stage5_6_refresh["quality_stage7_case_count"] == 0
    assert (
        stage5_6_refresh["trace_features_status"]
        == "stage5_6_refresh_trace_features_folded_non_causal"
    )
    assert stage5_6_refresh["trace_features_trace_frame_count"] == 38
    assert stage5_6_refresh["trace_features_stage_counts"] == {
        "stage5": 37,
        "stage6": 1,
    }
    assert stage5_6_refresh["trace_features_stage7_trace_frame_count"] == 0
    assert stage5_6_refresh["trace_features_selector_training_row_count"] == 0
    assert (
        stage5_6_refresh[
            "trace_features_candidate_generation_training_row_count"
        ]
        == 0
    )
    assert (
        stage5_6_refresh["dataset_design_v3_status"]
        == "strategy_sequence_dataset_design_v3_ready"
    )
    assert stage5_6_refresh["dataset_design_v3_implementation_allowed"] is False
    assert stage5_6_refresh["runtime_work_allowed"] is False
    assert stage5_6_refresh["runtime_candidate_generation_allowed"] is False
    assert stage5_6_refresh["selector_allowed"] is False
    assert stage5_6_refresh["selector_training_allowed"] is False
    assert stage5_6_refresh["stage7_promotion_allowed"] is False
    assert stage5_6_refresh["stage8_training_allowed"] is False

    cross_stage_scope = payload["cross_stage_candidate_generation_scope_gate"]
    assert (
        cross_stage_scope["capacity_review_status"]
        == "cross_stage_capacity_review_recommends_stratified_capacity_manifest"
    )
    assert cross_stage_scope["capacity_review_capacity_row_count"] == 28
    assert cross_stage_scope["capacity_review_stage_family_cell_count"] == 9
    assert cross_stage_scope["capacity_review_stage7_readiness_training_row_count"] == 0
    assert (
        cross_stage_scope["capacity_manifest_status"]
        == "cross_stage_capacity_manifest_ready_partial_target_coverage"
    )
    assert cross_stage_scope["capacity_manifest_labels_run_by_this_artifact"] is False
    assert cross_stage_scope["capacity_manifest_job_count"] == 8
    assert cross_stage_scope["capacity_manifest_stage7_job_count"] == 0
    assert cross_stage_scope["capacity_manifest_stage7_readiness_training_row_count"] == 0
    assert (
        cross_stage_scope["capacity_labels_status"]
        == "cross_stage_capacity_labels_completed"
    )
    assert cross_stage_scope["capacity_labels_label_count"] == 8
    assert cross_stage_scope["capacity_labels_stage7_label_count"] == 0
    assert cross_stage_scope["capacity_labels_stage7_training_label_count"] == 0
    assert cross_stage_scope["capacity_labels_result_counts"] == {
        "mate": 7,
        "max_plies": 1,
    }
    assert (
        cross_stage_scope["dataset_cross_stage_merged_status"]
        == "strategy_sequence_dataset_v2_cross_stage_capacity_merged_non_causal"
    )
    assert cross_stage_scope["dataset_cross_stage_merged_row_count"] == 282
    assert (
        cross_stage_scope[
            "dataset_cross_stage_merged_candidate_generation_training_row_count"
        ]
        == 26
    )
    assert cross_stage_scope["dataset_cross_stage_merged_selector_training_row_count"] == 0
    assert cross_stage_scope["dataset_cross_stage_merged_stage7_challenge_row_count"] == 198
    assert (
        cross_stage_scope[
            "dataset_cross_stage_merged_stage7_readiness_training_row_count"
        ]
        == 0
    )
    assert (
        cross_stage_scope["label_outcome_review_status"]
        == "cross_stage_capacity_labels_improve_in_sample_but_generalization_blocked"
    )
    assert (
        cross_stage_scope["label_outcome_runtime_candidate_generator_refresh_allowed"]
        is False
    )
    assert (
        cross_stage_scope["scope_review_status"]
        == "stage_conditioned_candidate_generation_scope_review_ready"
    )
    assert (
        cross_stage_scope["scope_review_runtime_candidate_generator_refresh_allowed"]
        is False
    )
    assert (
        cross_stage_scope["stage_conditioned_benchmark_status"]
        == "stage_conditioned_candidate_generation_stage5_6_promising_stage4_blocked"
    )
    assert (
        cross_stage_scope["stage_conditioned_benchmark_best_policy"]
        == "stage_conditioned_positive_scope"
    )
    assert cross_stage_scope["stage_conditioned_benchmark_positive_recall"] == 0.7692307692307693
    assert cross_stage_scope["stage_conditioned_benchmark_negative_suppression"] == 1
    assert cross_stage_scope["stage_conditioned_benchmark_stage4_positive_recall"] == 0
    assert cross_stage_scope["stage_conditioned_benchmark_stage5_6_positive_recall"] == 1
    assert (
        cross_stage_scope[
            "stage_conditioned_benchmark_stage7_readiness_training_row_count"
        ]
        == 0
    )
    assert cross_stage_scope["runtime_work_allowed"] is False
    assert cross_stage_scope["runtime_candidate_generation_allowed"] is False
    assert cross_stage_scope["selector_allowed"] is False
    assert cross_stage_scope["selector_training_allowed"] is False
    assert cross_stage_scope["stage7_promotion_allowed"] is False
    assert cross_stage_scope["stage8_training_allowed"] is False

    lineage = payload["selector_objective_lineage_gate"]
    assert (
        lineage["ownership_recovery_status"]
        == "ownership_label_recovery_seed_manifest_ready_selector_blocked"
    )
    assert lineage["ownership_recovery_joined_state_count"] == 4
    assert lineage["ownership_recovery_selected_failure_with_visible_positive_count"] == 2
    assert lineage["ownership_recovery_safe_preservation_with_visible_positive_count"] == 2
    assert lineage["ownership_recovery_selector_training_row_count"] == 0
    assert lineage["ownership_recovery_stage7_row_count"] == 0
    assert (
        lineage["seed_manifest_v0_status"]
        == "selector_objective_seed_manifest_ready_non_causal"
    )
    assert lineage["seed_manifest_v0_seed_row_count"] == 4
    assert lineage["seed_manifest_v0_candidate_switch_count"] == 2
    assert lineage["seed_manifest_v0_safe_preservation_count"] == 2
    assert (
        lineage["seed_probe_v0_status"]
        == "selector_objective_seed_probe_underpowered_semantics_confirmed"
    )
    assert lineage["seed_probe_v0_runtime_feature_eligible_prediction_count"] == 0
    assert lineage["seed_probe_v0_benchmark_underpowered"] is True
    assert (
        lineage["collection_manifest_status"]
        == "joined_trace_ownership_collection_manifest_ready_for_review"
    )
    assert lineage["collection_manifest_approved_observation_scope_candidate_count"] == 18
    assert lineage["collection_manifest_excluded_requires_separate_review_count"] == 19
    assert lineage["collection_manifest_runtime_collection_allowed_row_count"] == 0
    assert (
        lineage["collection_review_status"]
        == "joined_trace_ownership_observation_collection_review_ready"
    )
    assert lineage["collection_review_runtime_review_ready"] is True
    assert lineage["collection_review_implementation_authorized"] is False
    assert lineage["collection_review_max_rows_if_later_authorized"] == 8
    assert (
        lineage["joined_collection_status"]
        == "joined_trace_ownership_collection_complete_seed_improved"
    )
    assert lineage["joined_collection_collected_row_count"] == 8
    assert lineage["joined_collection_generated_frame_count"] == 80
    assert lineage["joined_collection_default_off_equivalence_passed"] is True
    assert lineage["joined_collection_selected_move_delta_count"] == 0
    assert lineage["joined_collection_selected_provider_delta_count"] == 0
    assert lineage["joined_collection_score_delta_count"] == 0
    assert lineage["joined_collection_routing_delta_count"] == 0
    assert (
        lineage["seed_manifest_v1_status"]
        == "selector_objective_seed_manifest_v1_ready_non_causal"
    )
    assert lineage["seed_manifest_v1_seed_row_count"] == 12
    assert lineage["seed_manifest_v1_candidate_switch_count"] == 4
    assert lineage["seed_manifest_v1_safe_preservation_count"] == 8
    assert lineage["seed_manifest_v1_selector_training_row_count"] == 0
    assert lineage["seed_manifest_v1_stage7_training_row_count"] == 0
    assert (
        lineage["seed_probe_v1_status"]
        == "selector_objective_seed_ready_for_non_causal_feature_probe"
    )
    assert lineage["seed_probe_v1_runtime_feature_eligible_prediction_count"] == 0
    assert (
        lineage["feature_probe_status"]
        == "selector_objective_feature_probe_no_runtime_ready_features"
    )
    assert lineage["feature_probe_runtime_threshold_passing_model_count"] == 0
    assert lineage["feature_probe_best_switch_recall"] == 0.75
    assert (
        lineage["feature_probe_review_status"]
        == "selector_feature_probe_blocks_runtime_needs_diverse_evidence"
    )
    assert lineage["feature_probe_review_best_switch_recall"] == 0.75
    assert lineage["feature_probe_review_best_preserve_recall"] == 1.0
    assert lineage["feature_probe_review_runtime_threshold_passing_model_count"] == 0
    assert (
        lineage["diversity_gap_status"]
        == "selector_objective_diversity_gap_requires_stage4_scope_review"
    )
    assert lineage["diversity_gap_remaining_stage4_selected_failure_count"] == 6
    assert lineage["diversity_gap_remaining_stage5_6_selected_failure_count"] == 0
    assert (
        lineage["stage4_scope_review_status"]
        == "stage4_joined_trace_ownership_scope_review_ready"
    )
    assert lineage["stage4_scope_review_runtime_review_ready"] is True
    assert lineage["stage4_scope_review_implementation_authorized"] is False
    assert lineage["stage4_scope_review_max_rows_if_later_authorized"] == 6
    assert lineage["runtime_work_allowed"] is False
    assert lineage["selector_allowed"] is False
    assert lineage["selector_training_allowed"] is False
    assert lineage["stage7_promotion_allowed"] is False
    assert lineage["stage8_training_allowed"] is False

    selector = payload["selector_objective_gate"]
    assert (
        selector["stage4_collection_status"]
        == "stage4_joined_trace_ownership_collection_complete"
    )
    assert selector["stage4_collection_collected_row_count"] == 6
    assert selector["stage4_collection_generated_frame_count"] == 170
    assert selector["stage4_collection_switch_contrast_with_positive_capacity_count"] == 1
    assert selector["stage4_collection_default_off_equivalence_passed"] is True
    assert selector["stage4_collection_selected_move_delta_count"] == 0
    assert selector["stage4_collection_selected_provider_delta_count"] == 0
    assert selector["stage4_collection_score_delta_count"] == 0
    assert selector["stage4_collection_routing_delta_count"] == 0
    assert selector["stage4_collection_selector_training_row_count"] == 0
    assert selector["stage4_collection_stage7_training_row_count"] == 0
    assert (
        selector["seed_manifest_v2_status"]
        == "selector_objective_seed_manifest_v2_ready_non_causal"
    )
    assert selector["seed_manifest_v2_seed_row_count"] == 18
    assert selector["seed_manifest_v2_objective_channel_counts"] == {
        "candidate_switch_contrast_seed": 5,
        "failure_context_without_candidate_seed": 5,
        "safe_preservation_contrast_seed": 8,
    }
    assert selector["seed_manifest_v2_selector_training_row_count"] == 0
    assert selector["seed_manifest_v2_stage7_training_row_count"] == 0
    assert (
        selector["seed_probe_v2_status"]
        == "selector_objective_seed_probe_v2_ready_for_non_causal_benchmark"
    )
    assert selector["seed_probe_v2_runtime_feature_eligible_prediction_count"] == 0
    assert (
        selector["selector_benchmark_v2_status"]
        == "selector_objective_benchmark_v2_runtime_feature_review_ready"
    )
    assert selector["selector_benchmark_v2_best_runtime_model"] == (
        "visible_failure_risk_heuristic_v2"
    )
    assert selector["selector_benchmark_v2_best_runtime_accuracy"] == 1.0
    assert selector["selector_benchmark_v2_best_runtime_switch_recall"] == 1.0
    assert selector["selector_benchmark_v2_runtime_threshold_passing_model_count"] == 1
    assert selector["selector_benchmark_v2_selector_training_row_count"] == 0
    assert selector["selector_benchmark_v2_stage7_training_row_count"] == 0
    assert (
        selector["selector_benchmark_review_status"]
        == "selector_objective_benchmark_review_ready_for_independent_validation"
    )
    assert selector["selector_benchmark_review_runtime_review_ready"] is False
    assert selector["selector_benchmark_review_independent_validation_ready"] is True
    assert (
        selector["independent_validation_status"]
        == "selector_objective_independent_validation_underpowered"
    )
    assert selector["independent_validation_row_count"] == 10
    assert selector["independent_validation_target_counts"] == {"preserve": 10}
    assert selector["independent_validation_switch_recall"] == 0.0
    assert selector["independent_validation_preserve_recall"] == 1.0
    assert selector["independent_validation_selector_training_row_count"] == 0
    assert selector["independent_validation_stage7_training_row_count"] == 0
    assert (
        selector["independent_validation_blocker_status"]
        == "selector_objective_runtime_blocked_pending_independent_switch_contrasts"
    )
    assert selector["independent_validation_blocker_class"] == (
        "independent_switch_contrast_absent"
    )
    assert selector["independent_validation_runtime_selector_blocked"] is True
    assert selector["runtime_work_allowed"] is False
    assert selector["selector_allowed"] is False
    assert selector["selector_training_allowed"] is False
    assert selector["stage7_promotion_allowed"] is False
    assert selector["stage8_training_allowed"] is False

    stage4_diagnostic = payload["stage4_first_move_diagnostic_gate"]
    assert (
        stage4_diagnostic["failure_discovery_status"]
        == "stage4_failure_discovery_collapsed_to_seed_state"
    )
    assert stage4_diagnostic["failure_packet_count"] == 32
    assert stage4_diagnostic["unique_failure_state_move_count"] == 1
    assert (
        stage4_diagnostic["all_unique_failures_already_in_selector_seed"] is True
    )
    assert (
        stage4_diagnostic["sequence_review_status"]
        == "stage4_caveat_sequence_followup_gap_review_ready"
    )
    assert (
        stage4_diagnostic["sequence_review_primary_diagnosis"]
        == "stage4_sequence_followup_gap_single_state"
    )
    assert stage4_diagnostic["sequence_review_single_unique_failure"] is True
    assert (
        stage4_diagnostic["sequence_review_base_control_reproduces_failure_count"]
        is True
    )
    assert (
        stage4_diagnostic["sequence_candidate_status"]
        == "stage4_first_move_ranking_gap"
    )
    assert stage4_diagnostic["sequence_candidate_legal_first_move_count"] == 12
    assert stage4_diagnostic["sequence_candidate_converting_first_move_count"] == 7
    assert stage4_diagnostic["sequence_candidate_non_converting_first_move_count"] == 5
    assert (
        stage4_diagnostic["feature_review_status"]
        == "stage4_first_move_feature_contrast_found_single_state"
    )
    assert stage4_diagnostic["feature_review_single_state_only"] is True
    assert stage4_diagnostic["feature_review_positive_terms"] == [
        "king_destination_c_file",
        "rook_mid_rank8_cut_candidate",
    ]
    assert stage4_diagnostic["feature_review_failure_terms"] == [
        "king_destination_a7",
        "rook_far_rank8_drift_candidate",
    ]
    assert (
        stage4_diagnostic["stratified_validation_status"]
        == "stage4_stratified_contrast_validation_supports_first_move_ranking_gap"
    )
    assert stage4_diagnostic["stratified_validation_variant_count"] == 4
    assert stage4_diagnostic["stratified_validation_gap_variant_count"] == 4
    assert stage4_diagnostic["stratified_validation_candidate_row_count"] == 48
    assert (
        stage4_diagnostic["runtime_review_status"]
        == "stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval"
    )
    assert stage4_diagnostic["runtime_review_ready"] is True
    assert stage4_diagnostic["runtime_review_implementation_authorized"] is False
    assert (
        stage4_diagnostic["sequence_control_dataset_status"]
        == "krk_sequence_control_contrast_dataset_ready_non_causal"
    )
    assert stage4_diagnostic["sequence_control_dataset_row_count"] == 76
    assert (
        stage4_diagnostic["sequence_control_dataset_runtime_authorization_row_count"]
        == 0
    )
    assert (
        stage4_diagnostic["sequence_control_probe_status"]
        == "sequence_control_dataset_ready_for_broader_sequence_policy_review"
    )
    assert (
        stage4_diagnostic[
            "sequence_control_probe_stage4_review_ready_pending_approval"
        ]
        is True
    )
    assert (
        stage4_diagnostic[
            "sequence_control_probe_stage7_rows_are_current_gate_evidence_not_promotion"
        ]
        is True
    )
    assert stage4_diagnostic["selector_training_allowed"] is False
    assert stage4_diagnostic["stage7_promotion_allowed"] is False
    assert stage4_diagnostic["stage8_training_allowed"] is False

    candidate_generation = payload["candidate_generation_training_refresh_gate"]
    assert (
        candidate_generation["dataset_v3_status"]
        == "strategy_sequence_dataset_v3_refreshed_non_causal_selector_blocked"
    )
    assert candidate_generation["dataset_v3_row_count"] == 320
    assert (
        candidate_generation["dataset_v3_candidate_generation_training_row_count"]
        == 26
    )
    assert candidate_generation["dataset_v3_selector_training_row_count"] == 0
    assert candidate_generation["dataset_v3_stage7_readiness_training_row_count"] == 0
    assert candidate_generation["dataset_v3_runtime_trace_feature_row_count"] == 44
    assert (
        candidate_generation["quality_probe_status"]
        == "strategy_sequence_dataset_v3_quality_candidate_generation_context_ready_selector_blocked"
    )
    assert (
        "no_explicit_ownership_selector_rows"
        in candidate_generation["quality_probe_selector_blockers"]
    )
    assert (
        candidate_generation["context_review_status"]
        == "strategy_sequence_dataset_v3_context_integrated_selector_still_blocked"
    )
    assert (
        candidate_generation["context_benchmark_status"]
        == "candidate_generation_v3_context_useful_selector_still_blocked"
    )
    assert (
        candidate_generation[
            "context_benchmark_exact_positive_capacity_recall_from_trace"
        ]
        == 0.3076923076923077
    )
    assert (
        candidate_generation[
            "context_benchmark_stage_family_positive_capacity_recall_from_trace"
        ]
        == 0.7692307692307693
    )
    assert (
        candidate_generation[
            "context_benchmark_stage_family_negative_capacity_exposure_from_trace"
        ]
        == 0.0
    )
    assert (
        candidate_generation["runtime_boundary_status"]
        == "candidate_generation_v3_runtime_boundary_context_ready_selector_blocked"
    )
    assert candidate_generation["runtime_boundary_new_runtime_behavior_allowed"] is False
    assert candidate_generation["runtime_boundary_selector_allowed"] is False
    assert (
        candidate_generation["training_refresh_review_status"]
        == "candidate_generation_v3_training_refresh_design_ready_non_causal"
    )
    assert (
        candidate_generation["training_refresh_design_status"]
        == "candidate_generation_training_refresh_v3_design_ready"
    )
    assert (
        candidate_generation["training_refresh_design_implementation_allowed"]
        is False
    )
    assert (
        candidate_generation["benchmark_status"]
        == "candidate_generation_training_refresh_v3_benchmark_passed_runtime_review_needed"
    )
    assert candidate_generation["benchmark_best_policy"] == "trace_stage_family_context"
    assert candidate_generation["benchmark_positive_capacity_recall"] == 0.7692307692307693
    assert candidate_generation["benchmark_positive_precision"] == 1.0
    assert candidate_generation["benchmark_negative_capacity_suppression"] == 1.0
    assert (
        candidate_generation["benchmark_leave_stage_out_positive_capacity_recall"]
        == 0.7692307692307693
    )
    assert candidate_generation["benchmark_thresholds_met"] is True
    assert candidate_generation["benchmark_selector_training_row_count"] == 0
    assert candidate_generation["benchmark_stage7_training_row_count"] == 0
    assert (
        candidate_generation["runtime_review_status"]
        == "candidate_generation_training_refresh_runtime_review_ready"
    )
    assert candidate_generation["runtime_review_ready"] is True
    assert (
        candidate_generation["runtime_review_candidate_generation_allowed_by_packet"]
        is False
    )
    assert candidate_generation["runtime_review_implementation_authorized"] is False
    assert (
        candidate_generation["runtime_review_sandbox_type"]
        == "default_off_candidate_generation_refresh"
    )
    assert candidate_generation["runtime_review_protected_stages"] == [
        "stage5",
        "stage6",
    ]
    assert candidate_generation["runtime_review_direct_request"] is False
    assert candidate_generation["runtime_review_score_delta"] == 0.0
    assert candidate_generation["runtime_work_allowed"] is False
    assert candidate_generation["runtime_candidate_generation_allowed"] is False
    assert candidate_generation["selector_allowed"] is False
    assert candidate_generation["selector_training_allowed"] is False
    assert candidate_generation["stage7_promotion_allowed"] is False
    assert candidate_generation["stage8_training_allowed"] is False

    trace_context = payload["candidate_generation_trace_context_gate"]
    assert (
        trace_context["refresh_sandbox_status"]
        == "candidate_generation_refresh_sandbox_ready_for_non_causal_coverage_analysis"
    )
    assert trace_context["refresh_sandbox_default_off_equivalence_passed"] is True
    assert trace_context["refresh_sandbox_generated_frame_count"] == 25
    assert trace_context["refresh_sandbox_stage7_held_out_frame_count"] == 0
    assert trace_context["refresh_sandbox_selected_move_delta_count"] == 0
    assert trace_context["refresh_sandbox_selected_provider_delta_count"] == 0
    assert trace_context["refresh_sandbox_score_delta_count"] == 0
    assert (
        trace_context["refresh_coverage_status"]
        == "candidate_generation_refresh_coverage_ready_for_trace_dataset_refresh"
    )
    assert trace_context["refresh_coverage_exact_positive_capacity_recall"] == 1.0
    assert trace_context["refresh_coverage_exact_negative_capacity_exposure_rate"] == 0.0
    assert trace_context["refresh_coverage_stage4_frame_count"] == 0
    assert trace_context["refresh_coverage_stage7_frame_count"] == 0
    assert (
        trace_context["refresh_trace_features_status"]
        == "candidate_generation_refresh_trace_features_folded_non_causal"
    )
    assert trace_context["refresh_trace_features_trace_frame_count"] == 25
    assert trace_context["refresh_trace_features_stage_counts"] == {
        "stage5": 24,
        "stage6": 1,
    }
    assert trace_context["refresh_trace_features_stage7_trace_frame_count"] == 0
    assert trace_context["refresh_trace_features_selector_training_row_count"] == 0
    assert (
        trace_context[
            "refresh_trace_features_candidate_generation_training_row_count"
        ]
        == 0
    )
    assert (
        trace_context["dataset_v4_status"]
        == "strategy_sequence_dataset_v4_refreshed_non_causal_selector_blocked"
    )
    assert trace_context["dataset_v4_row_count"] == 307
    assert trace_context["dataset_v4_runtime_trace_feature_row_count"] == 31
    assert trace_context["dataset_v4_selector_training_row_count"] == 0
    assert trace_context["dataset_v4_stage7_readiness_training_row_count"] == 0
    assert (
        trace_context["v4_boundary_status"]
        == "candidate_generation_v4_next_runtime_boundary_context_ready_selector_blocked"
    )
    assert trace_context["v4_boundary_new_runtime_sandbox_allowed"] is False
    assert (
        trace_context["scope_gap_status"]
        == "candidate_generation_scope_gap_review_blocks_new_runtime_boundary"
    )
    assert (
        trace_context["source_gap_manifest_status"]
        == "candidate_source_gap_manifest_ready_non_causal"
    )
    assert trace_context["source_gap_exact_covered_positive_capacity_count"] == 5
    assert trace_context["source_gap_exact_missing_positive_capacity_count"] == 21
    assert trace_context["source_gap_policy_cell_covered_exact_missing_count"] == 15
    assert (
        trace_context["source_expansion_options_status"]
        == "candidate_source_expansion_options_review_complete_runtime_packet_required"
    )
    assert (
        trace_context["source_expansion_preferred_next_review"]
        == "exact_trace_enrichment_within_existing_policy_cells"
    )
    assert (
        trace_context["exact_trace_runtime_review_status"]
        == "exact_trace_enrichment_runtime_review_ready"
    )
    assert trace_context["exact_trace_runtime_review_ready"] is True
    assert trace_context["exact_trace_runtime_review_implementation_authorized"] is False
    assert (
        trace_context["exact_trace_sandbox_status"]
        == "exact_trace_enrichment_sandbox_ready_for_non_causal_coverage_analysis"
    )
    assert trace_context["exact_trace_sandbox_default_off_equivalence_passed"] is True
    assert trace_context["exact_trace_sandbox_generated_frame_count"] == 3
    assert trace_context["exact_trace_sandbox_selected_move_delta_count"] == 0
    assert trace_context["exact_trace_sandbox_selected_provider_delta_count"] == 0
    assert trace_context["exact_trace_sandbox_score_delta_count"] == 0
    assert (
        trace_context["exact_trace_coverage_status"]
        == "exact_trace_enrichment_coverage_ready_for_trace_dataset_refresh"
    )
    assert trace_context["exact_trace_coverage_exact_gap_recall"] == 1.0
    assert trace_context["exact_trace_coverage_stage4_frame_count"] == 0
    assert trace_context["exact_trace_coverage_stage7_frame_count"] == 0
    assert (
        trace_context["dataset_v5_status"]
        == "strategy_sequence_dataset_v5_refreshed_non_causal_selector_blocked"
    )
    assert trace_context["dataset_v5_row_count"] == 310
    assert trace_context["dataset_v5_runtime_trace_feature_row_count"] == 34
    assert trace_context["dataset_v5_exact_trace_enrichment_row_count"] == 3
    assert trace_context["dataset_v5_selector_training_row_count"] == 0
    assert trace_context["dataset_v5_stage7_readiness_training_row_count"] == 0
    assert (
        trace_context["dataset_v5_quality_status"]
        == "strategy_sequence_dataset_v5_quality_candidate_generation_context_ready_selector_blocked"
    )
    assert (
        trace_context["dataset_v5_context_status"]
        == "strategy_sequence_dataset_v5_context_integrated_selector_still_blocked"
    )
    assert (
        trace_context["v5_context_benchmark_status"]
        == "candidate_generation_v5_context_useful_selector_still_blocked"
    )
    assert (
        trace_context[
            "v5_exact_positive_capacity_recall_from_candidate_generation_trace"
        ]
        == 0.3076923076923077
    )
    assert trace_context["v5_exact_positive_capacity_recall_delta_vs_v4"] == (
        0.11538461538461539
    )
    assert trace_context["v5_policy_cell_negative_capacity_exposure"] == 0.0
    assert (
        trace_context["v5_boundary_status"]
        == "candidate_generation_v5_next_boundary_context_improved_selector_blocked"
    )
    assert trace_context["v5_boundary_implement_new_runtime_sandbox"] is False
    assert trace_context["v5_boundary_selector_allowed"] is False
    assert trace_context["runtime_work_allowed"] is False
    assert trace_context["runtime_candidate_generation_allowed"] is False
    assert trace_context["selector_allowed"] is False
    assert trace_context["selector_training_allowed"] is False
    assert trace_context["stage7_promotion_allowed"] is False
    assert trace_context["stage8_training_allowed"] is False


def test_full_suite_readiness_writer_helpers_are_deterministic():
    payload = _audit.build_payload()
    rendered = _audit.write_markdown(payload)

    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["stage_status"]["stage7"]["ready_for_promotion"] is False
    assert payload["stage_status"]["stage7"]["sampling_runner_invalid_existing_output_count"] == 0
    assert payload["stage_status"]["stage7"]["sampling_runner_timed_out_job_count"] == 0
    assert (
        payload["stage_status"]["stage7"]["sampling_runner_execution_readiness_source"]
        == "live_recomputed"
    )
    assert payload["stage_status"]["stage8"]["ready_for_training"] is False
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"]["status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
            "approval_request_status"
        ]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
            "approval_request_blockers"
        ]
        == []
    )
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
            "approval_request_ready_for_runtime_approval"
        ]
        is True
    )
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
            "implementation_authorized_by_approval_request"
        ]
        is False
    )
    stage4_scope = payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
        "safety_scope"
    ]
    assert (
        stage4_scope["sandbox_scope_id"]
        == "default_off_stage4_candidate_move_first_move_contrast_sandbox_only"
    )
    assert stage4_scope["approval_request_blockers"] == []
    assert stage4_scope["approval_request_ready_for_runtime_approval"] is True
    assert stage4_scope["default_off"] is True
    assert stage4_scope["default_enabled"] is False
    assert stage4_scope["implementation_authorized_by_request"] is False
    assert stage4_scope["runtime_change_class"] == "default_off_candidate_move_frame_sandbox_only"
    assert stage4_scope["exact_state_or_exact_move_exception"] is False
    assert stage4_scope["runtime_dtm_or_tablebase_lookup"] is False
    assert stage4_scope["hidden_python_controller"] is False
    assert stage4_scope["selector_training_allowed"] is False
    assert stage4_scope["gameplay_topology_mutation"] is False
    assert stage4_scope["stage7_promotion_allowed"] is False
    assert stage4_scope["stage8_training_allowed"] is False
    assert (
        stage4_scope["readiness_audit"]
        == "reports/krk_full_suite_readiness_audit_v0.json"
    )
    assert stage4_scope["readiness_checked_flag_count"] >= 430
    assert stage4_scope["readiness_boundary_violation_count"] == 0
    assert stage4_scope["readiness_source_artifact_count"] >= 44
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "ready_for_explicit_approval"
        ]
        is True
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "approval_request_ready_for_collection"
        ]
        is True
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "post_success_refresh_required"
        ]
        is True
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "post_success_refresh_script"
        ]
        == "scripts/advance_krk_suite_from_current_gates_v0.py"
    )
    assert "krk_suite_readiness_waiting_on_explicit_protected_failure_contrast_collection" in rendered
    assert "protected_plan_window_failure_contrast_runner_dry_run_ready" in rendered
    assert "approval_receipt_blockers: `['approval_receipt_missing']`" in rendered
    assert (
        "approval_request_status: "
        "`protected_plan_window_failure_contrast_approval_request_ready`"
        in rendered
    )
    assert "approval_receipt_created_by_request: `False`" in rendered
    assert "post_success_refresh_required: `True`" in rendered
    assert (
        "post_success_refresh_script: "
        "`scripts/advance_krk_suite_from_current_gates_v0.py`"
        in rendered
    )
    assert "post_success_refresh_scope: `full_passive_krk_suite_gate_stack`" in rendered
    assert "runtime_behavior_changed: `False`" in rendered
    assert "runtime_defaults_changed: `False`" in rendered
    assert "runtime_selector_implemented: `False`" in rendered
    assert "runtime_score_changes: `False`" in rendered
    assert "runtime_direct_routing: `False`" in rendered
    assert "runtime_dtm_or_tablebase_lookup: `False`" in rendered
    assert "hidden_python_controller: `False`" in rendered
    assert "gameplay_topology_mutation: `False`" in rendered
    assert "selector_training_allowed: `False`" in rendered
    assert "stage7_promotion_allowed: `False`" in rendered
    assert "stage8_training_allowed: `False`" in rendered
    assert "## Protected Missing-Provider Evidence" in rendered
    assert "label_count: `16`" in rendered
    assert "stage7_training_label_count: `0`" in rendered
    assert (
        "coverage_status: "
        "`proposal_provider_coverage_gap_blocks_selector_training`"
        in rendered
    )
    assert "current_gap_blocks_selector_training: `True`" in rendered
    assert (
        "passive_design_without_new_labels_status: "
        "`non_causal_sequence_policy_design_without_new_labels_ready`"
        in rendered
    )
    assert (
        "post_failure_contrast_refresh_status: "
        "`sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs`"
        in rendered
    )
    assert "post_failure_contrast_refresh_boundaries_preserved: `True`" in rendered
    assert "post_failure_contrast_refresh_row_count: `0`" in rendered
    assert (
        "approval_request_status: "
        "`stage4_first_move_contrast_sandbox_approval_request_ready`"
        in rendered
    )
    assert "approval_request_created: `False`" in rendered
    assert "label_run_allowed: `false`" in rendered


def test_full_suite_readiness_reports_current_gate_blocking_option(monkeypatch):
    real_load_json = _audit.load_json

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/krk_current_control_plane_gate_v0.json":
            payload["approval_options"] = [
                {
                    "option_id": "repair_protected_stack_validation",
                    "command_if_explicitly_approved": None,
                }
            ]
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()
    current_gate = payload["current_control_plane_gate"]

    assert current_gate["approval_option_ids"] == ["repair_protected_stack_validation"]
    assert (
        current_gate["protected_failure_contrast_collection_option_available"]
        is False
    )
    assert (
        current_gate["protected_failure_contrast_collection_command_available"]
        is False
    )
    assert current_gate["protected_failure_contrast_collection_option_id"] is None
    assert (
        current_gate["protected_failure_contrast_collection_blocked_by_option_id"]
        == "repair_protected_stack_validation"
    )
    assert payload["hard_blockers"] == []
    assert payload["control_plane_gate_review_blockers"] == [
        "protected_plan_window_failure_contrast_control_plane_gate_review_required"
    ]
    assert payload["explicit_gate_blockers"] == []
    assert payload["blockers"] == payload["control_plane_gate_review_blockers"]
    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_blocked_pending_protected_failure_contrast_control_plane_gate_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_full_suite_readiness_routes_forbidden_training_rows_to_input_repair(monkeypatch):
    real_load_json = _audit.load_json

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
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert "sequence_policy_forbidden_training_or_runtime_rows" in payload["hard_blockers"]
    assert payload["sequence_policy"]["forbidden_training_or_runtime_input_blocked"] is True
    assert payload["protected_failure_contrast_gate"]["ready_for_explicit_approval"] is False
    assert payload["protected_failure_contrast_gate"]["command_if_explicitly_approved"] is None
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "ready_for_explicit_approval"
        ]
        is False
    )
    assert payload["decision"]["selector_training_allowed"] is False


def test_full_suite_readiness_routes_blocked_protected_collection_request_to_repair(monkeypatch):
    real_load_json = _audit.load_json

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
        ):
            payload.setdefault("decision", {})["status"] = (
                "protected_plan_window_failure_contrast_approval_request_blocked"
            )
            payload["blockers"] = ["full_suite_readiness_audit_not_clean"]
            payload["approval_request_ready_for_collection"] = False
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()
    gate = payload["protected_failure_contrast_gate"]

    assert gate["approval_request_status"] == (
        "protected_plan_window_failure_contrast_approval_request_blocked"
    )
    assert gate["approval_request_blockers"] == [
        "full_suite_readiness_audit_not_clean"
    ]
    assert gate["approval_request_ready_for_collection"] is False
    assert gate["ready_for_explicit_approval"] is False
    assert gate["command_if_explicitly_approved"] is None
    assert (
        "protected_plan_window_failure_contrast_approval_request_blocked"
        in payload["hard_blockers"]
    )
    assert payload["explicit_gate_blockers"] == []
    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_blocked_pending_protected_failure_contrast_approval_request_repair"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_protected_failure_contrast_approval_request_scope"
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "ready_for_explicit_approval"
        ]
        is False
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "approval_request_ready_for_collection"
        ]
        is False
    )
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_full_suite_readiness_gates_stage4_runtime_on_approval_request_not_ready(monkeypatch):
    real_load_json = _audit.load_json

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json":
            payload.setdefault("decision", {})["status"] = (
                "stage4_first_move_contrast_sandbox_approval_request_ready"
            )
            payload["blockers"] = []
            payload["approval_request_ready_for_runtime_approval"] = False
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()
    stage4 = payload["stage_status"]["stage4"]
    stage4_gate = payload["approval_gates"]["stage4_first_move_contrast_sandbox"]

    assert stage4["ready_for_explicit_runtime_approval"] is False
    assert stage4["approval_request_ready_for_runtime_approval"] is False
    assert stage4["approval_request_blockers"] == []
    assert stage4_gate["ready_for_explicit_approval"] is False
    assert stage4_gate["approval_request_ready_for_runtime_approval"] is False
    assert (
        stage4_gate["safety_scope"]["approval_request_ready_for_runtime_approval"]
        is False
    )
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_full_suite_readiness_blocks_post_failure_refresh_boundary_violation(monkeypatch):
    real_load_json = _audit.load_json

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
        ):
            payload.setdefault("summary", {})["all_boundaries_preserved"] = False
            payload.setdefault("summary", {})["boundary_violation_count"] = 1
            payload.setdefault("summary", {})["boundary_violations"] = [
                {
                    "step_id": "sequence_policy_benchmark",
                    "field": "runtime_changes_allowed",
                    "script": "scripts/run_krk_sequence_policy_benchmark_v0.py",
                }
            ]
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_after_protected_failure_contrast_refresh_blocked_boundary_violation"
            )
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()

    assert payload["sequence_policy"][
        "post_failure_contrast_refresh_boundaries_preserved"
    ] is False
    assert (
        payload["sequence_policy"][
            "post_failure_contrast_refresh_boundary_violation_count"
        ]
        == 1
    )
    assert (
        "post_failure_contrast_sequence_refresh_boundary_violation"
        in payload["hard_blockers"]
    )
    assert payload["decision"]["status"].startswith("krk_suite_readiness_blocked")
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_full_suite_readiness_blocks_unsafe_protected_stack_paths(monkeypatch):
    real_load_json = _audit.load_json

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/krk_active_protected_stack_v0.json":
            payload["active_protected_stack"]["stage6_drive_overlay"][
                "topology"
            ] = "../unsafe_topology.json"
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
        ):
            payload.setdefault("decision", {})["status"] = (
                "protected_plan_window_failure_contrast_approval_request_blocked"
            )
            payload["blockers"] = ["full_suite_readiness_audit_not_clean"]
            payload["approval_request_ready_for_collection"] = False
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()

    assert payload["protected_stack"]["ready"] is False
    assert payload["protected_stack"]["active_stack_path_status"]["all_paths_safe"] is False
    assert "stage6_drive_overlay.topology" in payload["protected_stack"][
        "active_stack_path_status"
    ]["unsafe_paths"]
    assert "protected_retry1_stage5_6_stack_not_validated" in payload["hard_blockers"]
    assert (
        "protected_plan_window_failure_contrast_approval_request_blocked"
        not in payload["hard_blockers"]
    )
    assert payload["explicit_gate_blockers"] == []
    assert payload["protected_failure_contrast_gate"]["ready_for_explicit_approval"] is False
    assert (
        payload["protected_failure_contrast_gate"]["command_if_explicitly_approved"]
        is None
    )
    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_blocked_pending_protected_stack_repair"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_protected_stack_validation"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False

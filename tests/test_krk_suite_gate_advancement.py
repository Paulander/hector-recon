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
    assert payload["summary"]["stage7_success_controls_required"] == 5
    assert payload["summary"]["stage7_success_controls_ready"] is True
    assert (
        payload["summary"]["stage7_clean_success_backfill_status"]
        == "stage7_clean_success_backfill_available"
    )
    assert payload["summary"]["stage7_clean_success_backfill_available"] is True
    assert payload["summary"]["stage7_clean_success_backfill_eligible_new_success"] == 0
    assert payload["summary"]["sequence_policy_inputs_ready"] is True
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

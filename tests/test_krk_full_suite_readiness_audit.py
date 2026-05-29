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
        payload["source_artifacts"]["self_expansion_architecture_gate"]
        == "reports/krk_self_expansion_architecture_gate_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_evidence_contract"]
        == "reports/krk_control_plane_evidence_contract_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_manifest"]
        == "reports/krk_control_plane_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_gap_report"]
        == "reports/krk_control_plane_gap_report_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_frames"]
        == "reports/krk_control_plane_frames_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_frame_quality"]
        == "reports/krk_control_plane_frame_quality_report_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_filtered_frames"]
        == "reports/krk_control_plane_filtered_frames_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_forced_controls"]
        == "reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_strategy_probe"]
        == "reports/krk_control_plane_strategy_arbitration_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["provider_label_coverage_plan"]
        == "reports/krk_provider_label_coverage_plan_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_strategy_baseline"]
        == "reports/krk_control_plane_strategy_arbitration_baseline_v1.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_stage7_boundary_refresh"]
        == "reports/krk_control_plane_stage7_boundary_refresh_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "protected_missing_provider_execution_manifest"
        ]
        == "reports/krk_protected_missing_provider_capacity_execution_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "protected_missing_provider_execution_manifest_review"
        ]
        == "reports/krk_protected_missing_provider_capacity_execution_manifest_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["sequence_benchmark_inputs"]
        == "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
    )
    assert (
        payload["source_artifacts"]["sequence_policy_input_probe"]
        == "reports/strategy_arbitration/krk_sequence_policy_input_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbitration_dataset"]
        == "reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbitration_probe"]
        == "reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbitration_decision_gate"]
        == "reports/strategy_arbitration/krk_strategy_arbitration_decision_gate.json"
    )
    assert (
        payload["source_artifacts"]["strategy_missing_feature_candidates"]
        == "reports/strategy_arbitration/krk_strategy_missing_feature_candidates.json"
    )
    assert (
        payload["source_artifacts"]["strategy_monitor_v0_plan"]
        == "reports/strategy_arbitration/krk_strategy_monitor_v0_plan.json"
    )
    assert (
        payload["source_artifacts"]["strategy_monitor_records_v0"]
        == "reports/strategy_arbitration/krk_strategy_monitor_records_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_monitor_companion_terms_v0"]
        == "reports/strategy_arbitration/krk_strategy_monitor_companion_terms_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_monitor_companion_audit_v0"]
        == "reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v0.json"
    )
    assert (
        payload["source_artifacts"]["visible_monitor_terms_v0"]
        == "reports/strategy_arbitration/krk_visible_monitor_terms_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_monitor_companion_audit_v1"]
        == "reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v1.json"
    )
    assert (
        payload["source_artifacts"]["strategy_monitor_maturity_gate_v0"]
        == "reports/strategy_arbitration/krk_strategy_monitor_maturity_gate_v0.json"
    )
    assert (
        payload["source_artifacts"]["feature_candidate_validation"]
        == "reports/strategy_arbitration/krk_feature_candidate_validation_v0.json"
    )
    assert (
        payload["source_artifacts"]["internal_terminal_candidates"]
        == "reports/strategy_arbitration/krk_internal_terminal_candidates_v0.json"
    )
    assert (
        payload["source_artifacts"]["internal_terminal_validation"]
        == "reports/strategy_arbitration/krk_internal_terminal_validation_v0.json"
    )
    assert (
        payload["source_artifacts"]["internal_terminal_evidence_v1"]
        == "reports/strategy_arbitration/krk_internal_terminal_evidence_v1.json"
    )
    assert (
        payload["source_artifacts"]["internal_terminal_design_review_v1"]
        == "reports/strategy_arbitration/krk_internal_terminal_design_review_v1.json"
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
        payload["source_artifacts"]["candidate_proposal_coverage"]
        == "reports/strategy_arbitration/krk_candidate_proposal_coverage_v0.json"
    )
    assert (
        payload["source_artifacts"]["candidate_generation_strategy_review"]
        == "reports/strategy_arbitration/krk_candidate_generation_strategy_review_v0.json"
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
        payload["source_artifacts"]["candidate_generation_observation_sandbox"]
        == "reports/strategy_arbitration/krk_candidate_generation_observation_sandbox_v0.json"
    )
    assert (
        payload["source_artifacts"]["candidate_generation_observation_gap_review"]
        == "reports/strategy_arbitration/krk_candidate_generation_observation_gap_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["candidate_move_capacity_annotation_v2"]
        == "reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.json"
    )
    assert (
        payload["source_artifacts"]["candidate_move_capacity_labels_v1"]
        == "reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.json"
    )
    assert (
        payload["source_artifacts"]["candidate_generation_label_blocker_review"]
        == "reports/strategy_arbitration/krk_candidate_generation_label_blocker_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["candidate_proposal_quality_dataset"]
        == "reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.json"
    )
    assert (
        payload["source_artifacts"]["candidate_proposal_quality_decision"]
        == "reports/strategy_arbitration/krk_candidate_proposal_quality_decision_v1.json"
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
            "candidate_generation_refresh_probe_v2_cross_stage_labels"
        ]
        == "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_cross_stage_labels.json"
    )
    assert (
        payload["source_artifacts"]["candidate_generation_training_refresh_design_v2"]
        == "reports/strategy_arbitration/krk_candidate_generation_training_refresh_design_v2.json"
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
        payload["source_artifacts"]["selector_objective_independent_validation_manifest"]
        == "reports/strategy_arbitration/krk_selector_objective_independent_validation_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_objective_independent_validation_labels"]
        == "reports/strategy_arbitration/krk_selector_objective_independent_validation_labels_v0.json"
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
    assert (
        payload["source_artifacts"]["clean_curriculum_checkpoint_plan"]
        == "reports/krk_clean_curriculum_checkpoint_plan_v0.json"
    )
    assert (
        payload["source_artifacts"]["clean_retrain_execution_manifest"]
        == "reports/krk_clean_retrain_execution_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"]["stage6_overlay_compose_manifest"]
        == "reports/krk_stage6_overlay_compose_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"]["clean_retrain_retry1_result"]
        == "reports/krk_clean_retrain_retry1_result_v1.json"
    )
    assert (
        payload["source_artifacts"]["clean_retrain_retry1_stage6_gap_inspection"]
        == "reports/krk_clean_retrain_retry1_stage6_gap_inspection_v1.json"
    )
    assert (
        payload["source_artifacts"]["stage5_guardrail_semantics_split"]
        == "reports/krk_stage5_guardrail_semantics_split_v0.json"
    )
    assert (
        payload["source_artifacts"]["stage4_caveat_decision_gate"]
        == "reports/krk_stage4_caveat_decision_gate_v0.json"
    )
    assert (
        payload["source_artifacts"]["stage4_caveat_diagnostic_matrix"]
        == "reports/krk_stage4_caveat_diagnostic_matrix_v0.json"
    )
    assert (
        payload["source_artifacts"]["curriculum_next_milestone_decision"]
        == "reports/krk_curriculum_next_milestone_decision_v0.json"
    )
    assert (
        payload["source_artifacts"]["stage7_to_stage8_blocker_review"]
        == "reports/structural_candidates/stage7_to_stage8_blocker_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_sequence_architecture_review"]
        == "reports/krk_strategy_sequence_architecture_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_sequence_evidence_plan"]
        == "reports/krk_strategy_sequence_evidence_plan_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_sequence_inventory"]
        == "reports/krk_strategy_sequence_inventory_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_owner_contrast_label_plan"]
        == "reports/krk_strategy_owner_contrast_label_plan_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_owner_contrast_execution_manifest"]
        == "reports/krk_strategy_owner_contrast_execution_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_owner_contrast_control_labels"]
        == "reports/krk_strategy_owner_contrast_control_labels_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_owner_contrast_dataset"]
        == "reports/krk_strategy_owner_contrast_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_owner_contrast_probe"]
        == "reports/krk_strategy_owner_contrast_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_sandbox_design_v0"]
        == "reports/krk_strategy_arbiter_sandbox_design_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_observability_smoke_v0"]
        == "reports/krk_strategy_arbiter_observability_smoke_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_observation_frames_v0"]
        == "reports/krk_strategy_arbiter_observation_frames_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_observation_separability_review_v0"
        ]
        == "reports/krk_strategy_arbiter_observation_separability_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_observation_selector_probe_v0"]
        == "reports/krk_strategy_arbiter_observation_selector_probe_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_labeled_observation_controls_v0"
        ]
        == "reports/krk_strategy_arbiter_labeled_observation_controls_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_labeled_controls_probe_v0"]
        == "reports/krk_strategy_arbiter_labeled_controls_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_protected_control_matrix_v1"]
        == "reports/krk_strategy_arbiter_protected_control_matrix_v1.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_evidence_risk_review_v0"]
        == "reports/krk_strategy_arbiter_evidence_risk_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_stratified_probe_v2"]
        == "reports/krk_strategy_arbiter_stratified_probe_v2.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_architecture_review_v1"]
        == "reports/krk_strategy_arbiter_architecture_review_v1.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_sandbox_readiness_criteria_v0"
        ]
        == "reports/krk_strategy_arbiter_sandbox_readiness_criteria_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_control_plane_review_v0"]
        == "reports/krk_strategy_arbiter_control_plane_review_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_out_of_sample_control_plan_v0"
        ]
        == "reports/krk_strategy_arbiter_out_of_sample_control_plan_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_out_of_sample_plan_review_v0"
        ]
        == "reports/krk_strategy_arbiter_out_of_sample_plan_review_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_out_of_sample_execution_manifest_v0"
        ]
        == "reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_out_of_sample_execution_manifest_review_v0"
        ]
        == "reports/krk_strategy_arbiter_out_of_sample_execution_manifest_review_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_out_of_sample_control_labels_v0"
        ]
        == "reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_out_of_sample_control_probe_v0"
        ]
        == "reports/krk_strategy_arbiter_out_of_sample_control_probe_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "strategy_arbiter_out_of_sample_architecture_review_v0"
        ]
        == "reports/krk_strategy_arbiter_out_of_sample_architecture_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_default_off_design_review_v1"]
        == "reports/krk_strategy_arbiter_default_off_design_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_runtime_review_packet_v1"]
        == "reports/krk_strategy_arbiter_runtime_review_packet_v1.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_runtime_sandbox_smoke_v1"]
        == "reports/krk_strategy_arbiter_runtime_sandbox_smoke_v1.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_protected_control_matrix_v2"]
        == "reports/krk_strategy_arbiter_protected_control_matrix_v2.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_stage7_holdout_lock_v1"]
        == "reports/krk_strategy_arbiter_stage7_holdout_lock_v1.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_stage7_challenge_probe_v1"]
        == "reports/krk_strategy_arbiter_stage7_challenge_probe_v1.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_support_sensitivity_v1"]
        == "reports/krk_strategy_arbiter_support_sensitivity_v1.json"
    )
    assert (
        payload["source_artifacts"]["strategy_arbiter_runtime_test_review_v2"]
        == "reports/krk_strategy_arbiter_runtime_test_review_v2.json"
    )
    assert (
        payload["source_artifacts"]["arbitration_objective_review_v1"]
        == "reports/krk_arbitration_objective_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["normalized_strategy_selector_objective_v1"]
        == "reports/krk_normalized_strategy_selector_objective_v1.json"
    )
    assert (
        payload["source_artifacts"]["normalized_selector_probe_review_v1"]
        == "reports/krk_normalized_selector_probe_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_objective_architecture_review_v1"]
        == "reports/krk_selector_objective_architecture_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_target_dataset_v0"]
        == "reports/krk_selector_target_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_target_probe_v0"]
        == "reports/krk_selector_target_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_baseline_probe_v0"]
        == "reports/krk_selector_baseline_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_feature_dataset_v0"]
        == "reports/krk_selector_feature_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_feature_baseline_probe_v0"]
        == "reports/krk_selector_feature_baseline_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["provider_identity_maturity_review_v0"]
        == "reports/krk_provider_identity_maturity_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["capacity_geometry_feature_audit_v0"]
        == "reports/krk_capacity_geometry_feature_audit_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "geometry_augmented_selector_feature_probe_v0"
        ]
        == "reports/krk_geometry_augmented_selector_feature_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_directed_fix_review_v0"]
        == "reports/krk_selector_directed_fix_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["forced_provider_control_label_plan_v0"]
        == "reports/krk_forced_provider_control_label_plan_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "forced_provider_label_execution_manifest_v0"
        ]
        == "reports/krk_forced_provider_label_execution_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"]["forced_provider_control_labels_v0"]
        == "reports/krk_forced_provider_control_labels_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_provenance_feature_dataset_v0"]
        == "reports/krk_selector_provenance_feature_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_provenance_feature_probe_v0"]
        == "reports/krk_selector_provenance_feature_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_feature_architecture_review_v0"]
        == "reports/krk_selector_feature_architecture_review_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "selector_readiness_after_contrast_probe_review_v0"
        ]
        == "reports/krk_selector_readiness_after_contrast_probe_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["split_selector_objective_dataset_v0"]
        == "reports/krk_split_selector_objective_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["split_selector_objective_readiness_v0"]
        == "reports/krk_split_selector_objective_readiness_v0.json"
    )
    assert (
        payload["source_artifacts"]["split_selector_objective_dataset_v1"]
        == "reports/krk_split_selector_objective_dataset_v1.json"
    )
    assert (
        payload["source_artifacts"]["split_selector_objective_readiness_v1"]
        == "reports/krk_split_selector_objective_readiness_v1.json"
    )
    assert (
        payload["source_artifacts"]["split_selector_objective_dataset_v2"]
        == "reports/krk_split_selector_objective_dataset_v2.json"
    )
    assert (
        payload["source_artifacts"]["split_selector_objective_readiness_v2"]
        == "reports/krk_split_selector_objective_readiness_v2.json"
    )
    assert (
        payload["source_artifacts"]["split_selector_objective_dataset_v3"]
        == "reports/krk_split_selector_objective_dataset_v3.json"
    )
    assert (
        payload["source_artifacts"]["split_selector_objective_readiness_v3"]
        == "reports/krk_split_selector_objective_readiness_v3.json"
    )
    assert (
        payload["source_artifacts"]["selector_stratified_label_plan_v1"]
        == "reports/krk_selector_stratified_label_plan_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_label_plan_replay_free_review_v1"]
        == "reports/krk_selector_label_plan_replay_free_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_negative_control_manifest_v1"]
        == "reports/krk_selector_negative_control_manifest_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_stratified_label_dataset_v1"]
        == "reports/krk_selector_stratified_label_dataset_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_stratified_label_balance_probe_v1"]
        == "reports/krk_selector_stratified_label_balance_probe_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_balanced_label_dataset_v1"]
        == "reports/krk_selector_balanced_label_dataset_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_balanced_label_probe_v1"]
        == "reports/krk_selector_balanced_label_probe_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_balanced_architecture_review_v1"]
        == "reports/krk_selector_balanced_architecture_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_label_dataset_v0"]
        == "reports/krk_ownership_selection_label_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_feature_probe_v0"]
        == "reports/krk_ownership_selection_feature_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_label_dataset_v1"]
        == "reports/krk_ownership_selection_label_dataset_v1.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_feature_probe_v1"]
        == "reports/krk_ownership_selection_feature_probe_v1.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_label_dataset_v2"]
        == "reports/krk_ownership_selection_label_dataset_v2.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_feature_probe_v2"]
        == "reports/krk_ownership_selection_feature_probe_v2.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_provider_diversity_ownership_labels_v0"
        ]
        == "reports/krk_selected_provider_diversity_ownership_labels_v0.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_context_dataset_v0"]
        == "reports/krk_ownership_selection_context_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_context_feature_probe_v0"]
        == "reports/krk_ownership_selection_context_feature_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["ownership_context_feature_review_v0"]
        == "reports/krk_ownership_context_feature_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_context_dataset_v1"]
        == "reports/krk_ownership_selection_context_dataset_v1.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_context_feature_probe_v1"]
        == "reports/krk_ownership_selection_context_feature_probe_v1.json"
    )
    assert (
        payload["source_artifacts"]["ownership_context_feature_review_v1"]
        == "reports/krk_ownership_context_feature_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_context_dataset_v2"]
        == "reports/krk_ownership_selection_context_dataset_v2.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_context_feature_probe_v2"]
        == "reports/krk_ownership_selection_context_feature_probe_v2.json"
    )
    assert (
        payload["source_artifacts"]["ownership_context_feature_review_v2"]
        == "reports/krk_ownership_context_feature_review_v2.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_label_dataset_v3"]
        == "reports/krk_ownership_selection_label_dataset_v3.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_label_dataset_v4"]
        == "reports/krk_ownership_selection_label_dataset_v4.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_label_dataset_v5"]
        == "reports/krk_ownership_selection_label_dataset_v5.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_context_dataset_v3"]
        == "reports/krk_ownership_selection_context_dataset_v3.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_context_feature_probe_v3"]
        == "reports/krk_ownership_selection_context_feature_probe_v3.json"
    )
    assert (
        payload["source_artifacts"]["ownership_selection_labeling_review_v0"]
        == "reports/krk_ownership_selection_labeling_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["ownership_source_diversity_review_v0"]
        == "reports/krk_ownership_source_diversity_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["protected_max_only_frame_review_v0"]
        == "reports/krk_protected_max_only_frame_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["protected_missing_provider_capacity_audit_plan"]
        == "reports/krk_protected_missing_provider_capacity_audit_plan_v0.json"
    )
    assert (
        payload["source_artifacts"]["selector_negative_suppression_evidence_v0"]
        == "reports/krk_selector_negative_suppression_evidence_v0.json"
    )
    assert (
        payload["source_artifacts"]["runtime_selector_readiness_review_v1"]
        == "reports/krk_runtime_selector_readiness_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["runtime_test_architecture_review_v3"]
        == "reports/krk_runtime_test_architecture_review_v3.json"
    )
    assert (
        payload["source_artifacts"]["abstention_first_selector_objective_v0"]
        == "reports/krk_abstention_first_selector_objective_v0.json"
    )
    assert (
        payload["source_artifacts"]["abstention_training_dataset_v0"]
        == "reports/krk_abstention_training_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["abstention_training_probe_v0"]
        == "reports/krk_abstention_training_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["abstention_training_dataset_v1"]
        == "reports/krk_abstention_training_dataset_v1.json"
    )
    assert (
        payload["source_artifacts"]["abstention_context_feature_probe_v0"]
        == "reports/krk_abstention_context_feature_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["abstention_feature_gap_review_v0"]
        == "reports/krk_abstention_feature_gap_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["two_stage_abstention_objective_probe_v0"]
        == "reports/krk_two_stage_abstention_objective_probe_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "two_stage_abstention_runtime_review_packet_v0"
        ]
        == "reports/krk_two_stage_abstention_runtime_review_packet_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "two_stage_abstention_default_off_equivalence_v0"
        ]
        == "reports/krk_two_stage_abstention_default_off_equivalence_v0.json"
    )
    assert (
        payload["source_artifacts"]["two_stage_abstention_enabled_smoke_v0"]
        == "reports/krk_two_stage_abstention_enabled_smoke_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "two_stage_abstention_stage7_challenge_smoke_v0"
        ]
        == "reports/krk_two_stage_abstention_stage7_challenge_smoke_v0.json"
    )
    assert (
        payload["source_artifacts"]["two_stage_abstention_runtime_go_no_go_v0"]
        == "reports/krk_two_stage_abstention_runtime_go_no_go_v0.json"
    )
    assert (
        payload["source_artifacts"]["targeted_non_stage0_ownership_labels_v0"]
        == "reports/krk_targeted_non_stage0_ownership_labels_v0.json"
    )
    assert (
        payload["source_artifacts"]["targeted_non_stage0_ownership_review_v0"]
        == "reports/krk_targeted_non_stage0_ownership_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["targeted_ownership_negative_labels_v0"]
        == "reports/krk_targeted_ownership_negative_labels_v0.json"
    )
    assert (
        payload["source_artifacts"]["hard_negative_selector_target_dataset_v1"]
        == "reports/krk_hard_negative_selector_target_dataset_v1.json"
    )
    assert (
        payload["source_artifacts"]["hard_negative_selector_feature_ablation_v1"]
        == "reports/krk_hard_negative_selector_feature_ablation_v1.json"
    )
    assert (
        payload["source_artifacts"]["hard_negative_selector_target_dataset_v0"]
        == "reports/krk_hard_negative_selector_target_dataset_v0.json"
    )
    assert (
        payload["source_artifacts"]["hard_negative_selector_feature_ablation_v0"]
        == "reports/krk_hard_negative_selector_feature_ablation_v0.json"
    )
    assert (
        payload["source_artifacts"]["balanced_hard_negative_label_plan_v0"]
        == "reports/krk_balanced_hard_negative_label_plan_v0.json"
    )
    assert (
        payload["source_artifacts"]["balanced_hard_negative_execution_manifest_v0"]
        == "reports/krk_balanced_hard_negative_execution_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "balanced_hard_negative_execution_manifest_review_v0"
        ]
        == "reports/krk_balanced_hard_negative_execution_manifest_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["balanced_hard_negative_labels_v0"]
        == "reports/krk_balanced_hard_negative_labels_v0.json"
    )
    assert (
        payload["source_artifacts"]["balanced_hard_negative_label_plan_v1"]
        == "reports/krk_balanced_hard_negative_label_plan_v1.json"
    )
    assert (
        payload["source_artifacts"]["balanced_hard_negative_labels_v1"]
        == "reports/krk_balanced_hard_negative_labels_v1.json"
    )
    assert (
        payload["source_artifacts"]["balanced_hard_negative_evidence_review_v0"]
        == "reports/krk_balanced_hard_negative_evidence_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["hard_negative_label_semantics_review_v1"]
        == "reports/krk_hard_negative_label_semantics_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["hard_negative_selector_feature_ablation_v2"]
        == "reports/krk_hard_negative_selector_feature_ablation_v2.json"
    )
    assert (
        payload["source_artifacts"]["stronger_selector_feature_review_v0"]
        == "reports/krk_stronger_selector_feature_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["selected_provider_diversity_evidence_plan_v0"]
        == "reports/krk_selected_provider_diversity_evidence_plan_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_provider_diversity_replay_free_scan_v0"
        ]
        == "reports/krk_selected_provider_diversity_replay_free_scan_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_provider_diversity_sampling_manifest_v0"
        ]
        == "reports/krk_selected_provider_diversity_sampling_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_provider_diversity_sampling_manifest_review_v0"
        ]
        == "reports/krk_selected_provider_diversity_sampling_manifest_review_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_provider_diversity_observation_scan_v0"
        ]
        == "reports/krk_selected_provider_diversity_observation_scan_v0.json"
    )
    assert (
        payload["source_artifacts"]["selected_provider_diversity_sampling_manifest_v1"]
        == "reports/krk_selected_provider_diversity_sampling_manifest_v1.json"
    )
    assert (
        payload["source_artifacts"]["selected_provider_diversity_ownership_labels_v1"]
        == "reports/krk_selected_provider_diversity_ownership_labels_v1.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_provider_diversity_architecture_review_v0"
        ]
        == "reports/krk_selected_provider_diversity_architecture_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["diverse_contrast_label_plan_v1"]
        == "reports/krk_diverse_contrast_label_plan_v1.json"
    )
    assert (
        payload["source_artifacts"]["diverse_contrast_execution_manifest_v1"]
        == "reports/krk_diverse_contrast_execution_manifest_v1.json"
    )
    assert (
        payload["source_artifacts"]["diverse_contrast_labels_v1"]
        == "reports/krk_diverse_contrast_labels_v1.json"
    )
    assert (
        payload["source_artifacts"]["selector_readiness_v3_plan"]
        == "reports/krk_selector_readiness_v3_plan.json"
    )
    assert (
        payload["source_artifacts"]["state_local_contrast_labels_v1"]
        == "reports/krk_state_local_contrast_labels_v1.json"
    )
    assert (
        payload["source_artifacts"]["state_local_contrast_selector_probe_v1"]
        == "reports/krk_state_local_contrast_selector_probe_v1.json"
    )
    assert (
        payload["source_artifacts"]["state_local_contrast_labels_v2"]
        == "reports/krk_state_local_contrast_labels_v2.json"
    )
    assert (
        payload["source_artifacts"]["state_local_contrast_selector_probe_v2"]
        == "reports/krk_state_local_contrast_selector_probe_v2.json"
    )
    assert (
        payload["source_artifacts"]["state_local_contrast_readiness_review_v2"]
        == "reports/krk_state_local_contrast_readiness_review_v2.json"
    )
    assert (
        payload["source_artifacts"]["hard_negative_selector_target_dataset_v2"]
        == "reports/krk_hard_negative_selector_target_dataset_v2.json"
    )
    assert (
        payload["source_artifacts"]["ownership_context_feature_review_v3"]
        == "reports/krk_ownership_context_feature_review_v3.json"
    )
    assert (
        payload["source_artifacts"]["state_local_paired_ownership_inventory_v0"]
        == "reports/krk_state_local_paired_ownership_inventory_v0.json"
    )
    assert (
        payload["source_artifacts"]["state_local_paired_ownership_probe_v0"]
        == "reports/krk_state_local_paired_ownership_probe_v0.json"
    )
    assert (
        payload["source_artifacts"]["state_local_paired_ownership_review_v0"]
        == "reports/krk_state_local_paired_ownership_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["state_local_paired_ownership_inventory_v1"]
        == "reports/krk_state_local_paired_ownership_inventory_v1.json"
    )
    assert (
        payload["source_artifacts"]["state_local_paired_ownership_review_v1"]
        == "reports/krk_state_local_paired_ownership_review_v1.json"
    )
    assert (
        payload["source_artifacts"]["state_local_paired_runtime_proxy_review_v0"]
        == "reports/krk_state_local_paired_runtime_proxy_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["selected_owner_failure_risk_evidence_v1"]
        == "reports/krk_selected_owner_failure_risk_evidence_v1.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_owner_failure_risk_visible_proxy_probe_v0"
        ]
        == "reports/krk_selected_owner_failure_risk_visible_proxy_probe_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_owner_failure_risk_proxy_independent_validation_v0"
        ]
        == "reports/krk_selected_owner_failure_risk_proxy_independent_validation_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_owner_failure_risk_proxy_independent_manifest_v0"
        ]
        == "reports/krk_selected_owner_failure_risk_proxy_independent_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_owner_failure_risk_proxy_blocker_review_v0"
        ]
        == "reports/krk_selected_owner_failure_risk_proxy_blocker_review_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "selected_owner_failure_risk_proxy_independent_validation_v1"
        ]
        == "reports/krk_selected_owner_failure_risk_proxy_independent_validation_v1.json"
    )
    assert (
        payload["source_artifacts"][
            "state_local_paired_selector_runtime_proxy_review_packet_v1"
        ]
        == "reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v1.json"
    )
    assert (
        payload["source_artifacts"][
            "progress_window_reconsideration_runtime_test_review_v0"
        ]
        == "reports/krk_progress_window_reconsideration_runtime_test_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["progress_window_reconsideration_runtime_smoke_v0"]
        == "reports/krk_progress_window_reconsideration_runtime_smoke_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "progress_window_reconsideration_post_activation_audit_v0"
        ]
        == "reports/krk_progress_window_reconsideration_post_activation_audit_v0.json"
    )
    assert (
        payload["source_artifacts"]["runtime_sandbox_policy_update_v0"]
        == "reports/krk_runtime_sandbox_policy_update_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "clean_retrain_retry1_replacement_readiness_review"
        ]
        == "reports/krk_clean_retrain_retry1_replacement_readiness_review_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "clean_retrain_retry1_protected_stack_snapshot_manifest"
        ]
        == "reports/krk_clean_retrain_retry1_protected_stack_snapshot_manifest_v0.json"
    )
    assert (
        payload["source_artifacts"][
            "clean_retrain_retry1_clean_stack_replacement_review_packet"
        ]
        == "reports/krk_clean_retrain_retry1_clean_stack_replacement_review_packet_v0.json"
    )
    assert (
        payload["source_artifacts"]["clean_stack_replacement_deferred_review"]
        == "reports/krk_clean_stack_replacement_deferred_review_v0.json"
    )
    assert (
        payload["source_artifacts"]["protected_stage_status"]
        == "reports/krk_protected_stage_status.json"
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

    clean_curriculum = payload["clean_curriculum_run_lineage_gate"]
    assert clean_curriculum["passive_lineage_ready"] is True
    assert (
        clean_curriculum["checkpoint_plan_status"]
        == "clean_curriculum_checkpoint_plan_ready_full_run_requires_review"
    )
    assert (
        clean_curriculum["execution_manifest_status"]
        == "clean_retrain_execution_manifest_ready_not_run"
    )
    assert clean_curriculum["execution_manifest_full_run_authorized"] is False
    assert (
        clean_curriculum["stage6_compose_manifest_status"]
        == "stage6_overlay_compose_manifest_ready_not_run"
    )
    assert clean_curriculum["stage6_compose_manifest_run_authorized"] is False
    assert (
        clean_curriculum["preflight_status"]
        == "clean_retrain_preflight_ready_for_run_review"
    )
    assert clean_curriculum["preflight_blocker_count"] == 0
    assert clean_curriculum["preflight_command_violation_count"] == 0
    assert clean_curriculum["preflight_protected_overwrite_count"] == 0
    assert (
        clean_curriculum["smoke_result_status"]
        == "clean_retrain_smoke_plumbing_passed_semantic_smoke_too_tiny"
    )
    assert clean_curriculum["smoke_command_plumbing_validated"] is True
    assert clean_curriculum["smoke_curriculum_semantics_validated"] is False
    assert (
        clean_curriculum["initial_run_status"]
        == "clean_retrain_full_run_incomplete_stage2a_no_promotable_checkpoint"
    )
    assert clean_curriculum["initial_run_full_clean_retrain_complete"] is False
    assert clean_curriculum["initial_run_stage2a_complete"] is False
    assert (
        clean_curriculum["retry1_status"]
        == "clean_retrain_retry1_completed_through_stage6_overlay_compose_basic_checks_passed"
    )
    assert clean_curriculum["retry1_complete_through_stage6"] is True
    assert clean_curriculum["retry1_stage_count"] == 6
    assert clean_curriculum["retry1_promoted_by_this_artifact"] is False
    assert clean_curriculum["retry1_protected_snapshots_overwritten"] is False
    assert clean_curriculum["retry1_stage7_training_or_promotion"] is False
    assert clean_curriculum["retry1_stage8_training"] is False
    assert clean_curriculum["retry1_runtime_selector_or_routing_change"] is False
    assert (
        clean_curriculum["guardrail_status"]
        == "clean_retrain_retry1_stage6_overlay_quarantined_guardrails_partial"
    )
    assert clean_curriculum["guardrail_promotion_status"] == "quarantine"
    assert clean_curriculum["guardrail_retry1_can_replace_protected_stack"] is False
    assert (
        clean_curriculum["stage6_gap_status"]
        == "stage6_gap_explained_by_validation_profile_mismatch"
    )
    assert clean_curriculum["stage6_gap_corrected_profile_restores_conversion"] is True
    assert clean_curriculum["stage6_gap_retry1_can_replace_protected_stack"] is False
    assert (
        clean_curriculum["stage5_control_debt_status"]
        == "stage5_one_ply_guardrail_control_debt_confirmed"
    )
    assert clean_curriculum["stage5_control_debt_conversion_preserved"] is True
    assert clean_curriculum["stage5_control_debt_quarantines_stage6_overlay"] is False
    assert (
        clean_curriculum["stage5_semantics_status"]
        == "stage5_guardrail_semantics_split_defined"
    )
    assert clean_curriculum["stage5_semantics_overlay_use_allowed_as_overlay_only"] is True
    assert clean_curriculum["stage5_semantics_clean_stack_replacement_allowed"] is False
    assert clean_curriculum["stage4_caveat_diagnostic_matrix_ready"] is True
    assert (
        clean_curriculum["stage4_caveat_diagnostic_status"]
        == "stage4_caveat_diagnostic_matrix_ready"
    )
    assert clean_curriculum["stage4_caveat_diagnostic_total"] == 300
    assert clean_curriculum["stage4_caveat_diagnostic_mate_count"] == 268
    assert clean_curriculum["stage4_caveat_diagnostic_max_plies_count"] == 32
    assert clean_curriculum["stage4_caveat_diagnostic_mate_delta"] == 0
    assert clean_curriculum["stage4_caveat_diagnostic_max_plies_delta"] == 0
    assert (
        clean_curriculum["stage4_caveat_diagnostic_candidate_gap_confidence"]
        == "high"
    )
    assert clean_curriculum[
        "stage4_caveat_diagnostic_candidate_gap_next_test"
    ] == "approve_stage4_observation_only_trace_collection_max_6_rows"
    assert (
        clean_curriculum["stage4_caveat_diagnostic_runtime_behavior_changed"]
        is False
    )
    assert (
        clean_curriculum["stage4_caveat_diagnostic_runtime_defaults_changed"]
        is False
    )
    assert (
        clean_curriculum["stage4_caveat_diagnostic_runtime_selector_implemented"]
        is False
    )
    assert (
        clean_curriculum[
            "stage4_caveat_diagnostic_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        clean_curriculum["stage4_caveat_diagnostic_gameplay_topology_mutation"]
        is False
    )
    assert clean_curriculum["stage4_caveat_decision_passive_ready"] is True
    assert clean_curriculum["stage4_caveat_decision_status"] == (
        "stage4_candidate_generation_gap_with_known_residual_guardrail"
    )
    assert "stage4_candidate_generation_gap" in (
        clean_curriculum["stage4_caveat_decision_selected"]
    )
    assert "stage4_known_residual_keep_as_guardrail" in (
        clean_curriculum["stage4_caveat_decision_selected"]
    )
    assert "stage4_runtime_sandbox_review_ready" in (
        clean_curriculum["stage4_caveat_decision_rejected"]
    )
    assert clean_curriculum["stage4_caveat_decision_next_action"] == (
        "explicit_approval_for_stage4_observation_only_trace_collection_or_keep_as_known_guardrail"
    )
    assert clean_curriculum["stage4_caveat_runtime_or_training_authorized"] is False
    assert clean_curriculum["stage4_caveat_runtime_behavior_changed"] is False
    assert clean_curriculum["stage4_caveat_runtime_defaults_changed"] is False
    assert clean_curriculum["stage4_caveat_runtime_selector_implemented"] is False
    assert clean_curriculum["stage4_caveat_runtime_dtm_or_tablebase_lookup"] is False
    assert clean_curriculum["stage4_caveat_gameplay_topology_mutation"] is False
    assert clean_curriculum["stage4_caveat_stage7_promotion"] is False
    assert clean_curriculum["stage4_caveat_stage8_training"] is False
    assert (
        clean_curriculum["stage4_caveat_control_status"]
        == "stage4_caveat_reproduces_in_base_control_no_overlay_regression"
    )
    assert (
        clean_curriculum["stage4_caveat_overlay_regressed_vs_base_control"] is False
    )
    assert (
        clean_curriculum["curriculum_stage7_status"]
        == "stage7_unlock_path_identified_broader_sequence_control_not_micro_repair"
    )
    assert clean_curriculum["curriculum_stage8_status"] == "stage8_remains_blocked_with_review"
    assert clean_curriculum["stage7_promotion_allowed"] is False
    assert clean_curriculum["stage8_training_allowed"] is False

    strategy_sequence = payload["strategy_sequence_architecture_gate"]
    assert strategy_sequence["passive_architecture_ready"] is True
    assert (
        strategy_sequence["architecture_review_status"]
        == "broader_krk_strategy_sequence_review_ready"
    )
    assert strategy_sequence["architecture_runtime_work_allowed"] is False
    assert strategy_sequence["architecture_recommended_next_slice_id"] == (
        "krk_strategy_sequence_evidence_plan_v0"
    )
    assert strategy_sequence["architecture_next_objective_ids"] == [
        "strategy_ownership_evidence",
        "sequence_policy_evidence",
        "curriculum_boundary_evidence",
    ]
    assert (
        strategy_sequence["evidence_plan_status"]
        == "strategy_sequence_evidence_plan_defined"
    )
    assert strategy_sequence["evidence_plan_runtime_work_allowed"] is False
    assert (
        strategy_sequence["inventory_status"]
        == "replay_free_inventory_state_holdout_gap_blocks_runtime"
    )
    assert strategy_sequence["inventory_runtime_work_allowed"] is False
    assert strategy_sequence["inventory_sequence_policy_clean_gate_closed"] is True
    assert strategy_sequence["inventory_sequence_policy_has_clean_success_gap"] is False
    assert strategy_sequence["inventory_state_holdout_gap_blocks_runtime"] is True
    assert strategy_sequence["inventory_strategy_ownership_has_some_signal"] is True
    assert strategy_sequence["inventory_strategy_ownership_state_holdout_ready"] is False
    assert strategy_sequence["inventory_stage7_is_held_out"] is True
    assert strategy_sequence["runtime_behavior_changed"] is False
    assert strategy_sequence["runtime_defaults_changed"] is False
    assert strategy_sequence["runtime_selector_implemented"] is False
    assert strategy_sequence["runtime_dtm_or_tablebase_lookup"] is False
    assert strategy_sequence["stage7_promotion_allowed"] is False
    assert strategy_sequence["stage8_training_allowed"] is False

    strategy_owner = payload["strategy_owner_contrast_gate"]
    assert strategy_owner["passive_probe_ready"] is True
    assert (
        strategy_owner["label_plan_status"]
        == "protected_strategy_owner_contrast_label_plan_defined_execution_review_required"
    )
    assert strategy_owner["label_plan_job_count"] == 12
    assert strategy_owner["label_plan_stage7_job_count"] == 0
    assert strategy_owner["label_plan_labels_generated"] is False
    assert strategy_owner["label_plan_runtime_arbiter_allowed"] is False
    assert strategy_owner["label_plan_selector_sandbox_ready"] is False
    assert (
        strategy_owner["label_plan_review_status"]
        == "contrast_label_plan_review_passed_binding_required"
    )
    assert strategy_owner["label_plan_review_allowed_to_bind_manifest"] is True
    assert strategy_owner["label_plan_review_allowed_to_run_labels"] is False
    assert strategy_owner["label_plan_review_stage7_jobs"] == 0
    assert (
        strategy_owner["execution_manifest_status"]
        == "contrast_execution_manifest_bound_review_required"
    )
    assert strategy_owner["execution_manifest_labels_allowed_now"] is False
    assert strategy_owner["execution_manifest_all_bindings_valid"] is True
    assert strategy_owner["execution_manifest_missing_path_count"] == 0
    assert strategy_owner["execution_manifest_stage7_jobs"] == 0
    assert (
        strategy_owner["execution_manifest_review_status"]
        == "contrast_execution_manifest_review_passed_labels_allowed"
    )
    assert strategy_owner["execution_manifest_review_labels_allowed"] is True
    assert strategy_owner["execution_manifest_review_stage7_jobs"] == 0
    assert strategy_owner["control_label_count"] == 12
    assert strategy_owner["control_label_stage7_count"] == 0
    assert strategy_owner["control_label_trace_failures_only"] is True
    assert (
        strategy_owner["dataset_status"]
        == "strategy_owner_contrast_dataset_ready_for_non_causal_probe_selector_sandbox_blocked"
    )
    assert strategy_owner["dataset_row_count"] == 13
    assert strategy_owner["dataset_training_eligible_row_count"] == 9
    assert strategy_owner["dataset_held_out_challenge_row_count"] == 4
    assert strategy_owner["dataset_stage7_training_rows"] == 0
    assert strategy_owner["readiness_contrast_probe_ready"] is True
    assert strategy_owner["readiness_selector_sandbox_ready"] is False
    assert strategy_owner["readiness_stage7_training_rows"] == 0
    assert strategy_owner["readiness_blockers"] == [
        "insufficient_selected_provider_family_diversity"
    ]
    assert (
        strategy_owner["probe_status"]
        == "strategy_owner_contrast_signal_present_selector_sandbox_blocked"
    )
    assert strategy_owner["probe_training_row_count"] == 9
    assert strategy_owner["probe_heldout_row_count"] == 4
    assert strategy_owner["probe_readiness_blockers"] == [
        "insufficient_selected_provider_family_diversity"
    ]
    assert strategy_owner["runtime_arbiter_implemented"] is False
    assert strategy_owner["runtime_behavior_changed"] is False
    assert strategy_owner["runtime_defaults_changed"] is False
    assert strategy_owner["runtime_dtm_or_tablebase_lookup"] is False
    assert strategy_owner["runtime_terminals_added"] is False
    assert strategy_owner["stage7_promotion_allowed"] is False
    assert strategy_owner["stage8_training_allowed"] is False

    arbiter_trace = payload["strategy_arbiter_trace_observability_gate"]
    assert arbiter_trace["passive_trace_observability_ready"] is True
    assert arbiter_trace["status"] == "labeled_controls_mixed_no_sandbox"
    assert arbiter_trace["sandbox_design_status"] == "proposed_for_review"
    assert arbiter_trace["sandbox_default_enabled"] is False
    assert "implement_runtime_arbiter_without_review" in (
        arbiter_trace["sandbox_blocked_next_steps"]
    )
    assert "promote_stage7" in arbiter_trace["sandbox_blocked_next_steps"]
    assert "train_stage8" in arbiter_trace["sandbox_blocked_next_steps"]
    assert (
        arbiter_trace["smoke_status"] == "observability_skeleton_smoke_passed"
    )
    assert arbiter_trace["smoke_runtime_arbiter_allowed"] is False
    assert arbiter_trace["smoke_selected_behavior_metrics_match"] is True
    assert arbiter_trace["smoke_outcome_metrics_match"] is True
    assert arbiter_trace["smoke_observation_is_only_expected_delta"] is True
    assert arbiter_trace["smoke_direct_request"] is False
    assert arbiter_trace["smoke_score_delta"] == 0.0
    assert arbiter_trace["smoke_recommendation_only"] is True
    assert arbiter_trace["observation_frames_status"] == "observation_frames_collected"
    assert arbiter_trace["observation_frames_runtime_arbiter_allowed"] is False
    assert arbiter_trace["observation_frame_count"] == 12
    assert arbiter_trace["observation_stage_counts"] == {
        "stage4": 2,
        "stage5": 1,
        "stage7": 9,
    }
    assert arbiter_trace["observation_proposal_count_min"] == 10
    assert arbiter_trace["observation_proposal_count_max"] == 10
    assert arbiter_trace["separability_status"] == (
        "observation_frames_ready_for_non_causal_selector_probe"
    )
    assert arbiter_trace["separability_runtime_arbiter_allowed"] is False
    assert arbiter_trace["separability_sandbox_ready"] is False
    assert arbiter_trace["separability_underinstrumented_record_count"] == 0
    assert arbiter_trace["separability_single_provider_record_count"] == 0
    assert arbiter_trace["selector_probe_status"] == (
        "observation_selector_probe_underlabeled"
    )
    assert arbiter_trace["selector_probe_runtime_arbiter_allowed"] is False
    assert arbiter_trace["selector_probe_sandbox_ready"] is False
    assert arbiter_trace["selector_probe_underlabeled"] is True
    assert arbiter_trace["selector_probe_labeled_row_count"] == 3
    assert arbiter_trace["selector_probe_selected_unknown_count"] == 10
    assert (
        arbiter_trace["labeled_controls_status"]
        == "labeled_observation_controls_collected"
    )
    assert arbiter_trace["labeled_controls_runtime_arbiter_allowed"] is False
    assert arbiter_trace["labeled_controls_record_count"] == 21
    assert arbiter_trace["labeled_controls_stage_counts"] == {
        "stage4": 5,
        "stage5": 6,
        "stage6": 4,
        "stage7": 6,
    }
    assert arbiter_trace["labeled_controls_selected_label_counts"] == {
        "negative": 5,
        "positive": 9,
        "unknown": 7,
    }
    assert arbiter_trace["labeled_probe_status"] == "labeled_controls_mixed_no_sandbox"
    assert arbiter_trace["labeled_probe_runtime_arbiter_allowed"] is False
    assert arbiter_trace["labeled_probe_sandbox_ready"] is False
    assert arbiter_trace["labeled_probe_record_count"] == 21
    assert arbiter_trace["labeled_probe_labeled_record_count"] == 14
    assert arbiter_trace["labeled_probe_stage7_unknown_count"] == 6
    assert arbiter_trace["labeled_probe_selected_positive_rate"] == 0.6428571428571429
    assert arbiter_trace["protected_matrix_status"] == "protected_control_matrix_passed"
    assert arbiter_trace["protected_matrix_default_off_equivalence_passed"] is True
    assert arbiter_trace["protected_matrix_enabled_conversion_not_worse"] is True
    assert arbiter_trace["protected_matrix_no_no_move_or_draw_spike"] is True
    assert arbiter_trace["protected_matrix_stage7_rows"] == 0
    assert arbiter_trace["runtime_arbiter_implemented"] is False
    assert arbiter_trace["runtime_behavior_changed"] is False
    assert arbiter_trace["runtime_defaults_changed"] is False
    assert arbiter_trace["runtime_dtm_or_tablebase_lookup"] is False
    assert arbiter_trace["gameplay_topology_mutation"] is False
    assert arbiter_trace["stage7_promotion_allowed"] is False
    assert arbiter_trace["stage8_training_allowed"] is False

    arbiter_semantics = payload["strategy_arbiter_semantics_blocker_gate"]
    assert arbiter_semantics["passive_semantics_blocker_ready"] is True
    assert (
        arbiter_semantics["status"]
        == "selector_objective_and_label_semantics_review_required"
    )
    assert (
        arbiter_semantics["risk_review_status"]
        == "runtime_sandbox_blocked_pending_semantics_review"
    )
    assert arbiter_semantics["risk_review_runtime_sandbox_allowed"] is False
    assert arbiter_semantics["risk_review_benchmark_frame_count"] == 28
    assert arbiter_semantics["risk_review_max_only_frame_count"] == 14
    assert arbiter_semantics["risk_review_provider_mate_frame_count"] == 14
    assert arbiter_semantics["risk_review_label_semantic_counts"] == {
        "forced_provider_outcome": 24,
        "same_move_unselected_provider_playout": 18,
        "selected_provider_playout": 24,
    }
    assert "runtime_arbiter" in arbiter_semantics["risk_review_blocked_next_steps"]
    assert "runtime_internal_terminal" in (
        arbiter_semantics["risk_review_blocked_next_steps"]
    )
    assert "runtime_dtm_or_tablebase" in (
        arbiter_semantics["risk_review_blocked_next_steps"]
    )
    assert (
        arbiter_semantics["stratified_probe_status"]
        == "protected_forced_controls_promising_stage7_gap_confirmed"
    )
    assert arbiter_semantics["stratified_probe_runtime_sandbox_allowed"] is False
    assert arbiter_semantics["stratified_probe_selected_provider_hit_rate"] == 1.0
    assert arbiter_semantics["stratified_probe_forced_control_hit_rate"] == 1.0
    assert (
        arbiter_semantics["stratified_probe_stage7_forced_provider_hit_rate"]
        == 0.5
    )
    assert (
        arbiter_semantics["architecture_review_status"]
        == "trace_only_observability_skeleton_allowed"
    )
    assert arbiter_semantics["architecture_runtime_arbiter_allowed"] is False
    assert arbiter_semantics["architecture_runtime_defaults_may_change"] is False
    assert arbiter_semantics["architecture_stage7_gap_status"] == (
        "held_out_challenge_gap"
    )
    assert arbiter_semantics["architecture_allowed_next_scope"] == (
        "default_off_trace_only"
    )
    assert arbiter_semantics["architecture_allowed_next_default_enabled"] is False
    assert arbiter_semantics["architecture_allowed_next_may_change_scores"] is False
    assert arbiter_semantics["architecture_allowed_next_may_request_provider"] is False
    assert (
        arbiter_semantics["sandbox_readiness_decision_status"]
        == "readiness_criteria_defined_sandbox_still_blocked"
    )
    assert arbiter_semantics["sandbox_readiness_runtime_arbiter_allowed"] is False
    assert arbiter_semantics["sandbox_readiness_selector_sandbox_ready"] is False
    assert arbiter_semantics["sandbox_readiness_stage7_repair_allowed"] is False
    assert arbiter_semantics["sandbox_readiness_stage7_promotion_allowed"] is False
    assert arbiter_semantics["sandbox_readiness_stage8_training_allowed"] is False
    assert arbiter_semantics["sandbox_readiness_stage7_holdout_status"] == "met"
    assert (
        arbiter_semantics["sandbox_readiness_out_of_sample_controls_status"]
        == "missing"
    )
    assert arbiter_semantics["control_plane_observability_skeleton"] == (
        "implemented_default_off_trace_only"
    )
    assert arbiter_semantics["control_plane_labeled_controls"] == "mixed"
    assert arbiter_semantics["control_plane_stage7"] == (
        "held_out_unlabeled_challenge"
    )
    assert arbiter_semantics["control_plane_runtime_arbiter_allowed"] is False
    assert arbiter_semantics["control_plane_sandbox_ready"] is False
    assert arbiter_semantics["control_plane_observability_smoke_status"] == "passed"
    assert (
        arbiter_semantics["control_plane_observability_behavior_metrics_match"]
        is True
    )
    assert arbiter_semantics["control_plane_labeled_controls_probe_status"] == (
        "labeled_controls_mixed_no_sandbox"
    )
    assert arbiter_semantics["control_plane_stage7_unknown_count"] == 6
    assert arbiter_semantics["control_plane_recommended_next_step_id"] == (
        "krk_selector_objective_label_semantics_v0"
    )
    assert arbiter_semantics["control_plane_must_remain_non_causal"] is True
    assert "default_off_selector_sandbox" in (
        arbiter_semantics["control_plane_blocked_next_work"]
    )
    assert "stage7_promotion" in arbiter_semantics["control_plane_blocked_next_work"]
    assert "stage8_training" in arbiter_semantics["control_plane_blocked_next_work"]
    assert "runtime_dtm_or_tablebase" in (
        arbiter_semantics["control_plane_blocked_next_work"]
    )
    assert arbiter_semantics["runtime_arbiter_implemented"] is False
    assert arbiter_semantics["runtime_behavior_changed"] is False
    assert arbiter_semantics["runtime_defaults_changed"] is False
    assert arbiter_semantics["runtime_dtm_or_tablebase_lookup"] is False
    assert arbiter_semantics["gameplay_topology_mutation"] is False
    assert arbiter_semantics["stage7_promotion_allowed"] is False
    assert arbiter_semantics["stage8_training_allowed"] is False

    out_of_sample = payload["strategy_arbiter_out_of_sample_gate"]
    assert out_of_sample["passive_out_of_sample_ready"] is True
    assert (
        out_of_sample["plan_status"]
        == "out_of_sample_control_plan_defined_execution_blocked"
    )
    assert out_of_sample["plan_execute_collection_now"] is False
    assert out_of_sample["plan_stage7_training_rows"] == 0
    assert (
        out_of_sample["plan_review_status"]
        == "plan_review_passed_execution_manifest_needed"
    )
    assert out_of_sample["plan_review_execute_collection_now"] is False
    assert out_of_sample["manifest_status"] == "execution_manifest_ready_for_review"
    assert out_of_sample["manifest_execute_labels_now"] is False
    assert out_of_sample["manifest_job_count"] == 12
    assert out_of_sample["manifest_job_count_by_stage"] == {
        "stage4": 4,
        "stage5": 4,
        "stage6": 4,
    }
    assert out_of_sample["manifest_required_stage_coverage_met"] is True
    assert out_of_sample["manifest_missing_path_count"] == 0
    assert out_of_sample["manifest_stage7_training_rows"] == 0
    assert out_of_sample["manifest_labels_generated_in_this_slice"] is False
    assert out_of_sample["manifest_review_status"] == (
        "execution_manifest_review_passed_bounded_label_run_allowed"
    )
    assert out_of_sample["manifest_review_execute_labels_now"] is False
    assert out_of_sample["manifest_review_stage7_training_rows"] == 0
    assert out_of_sample["label_count"] == 12
    assert out_of_sample["label_stage7_training_rows"] == 0
    assert out_of_sample["label_trace_failures_only"] is True
    assert out_of_sample["label_selected_result_counts"] == {
        "mate": 11,
        "max_plies": 1,
    }
    assert out_of_sample["probe_status"] == (
        "out_of_sample_controls_guardrail_positive_selector_sandbox_blocked"
    )
    assert out_of_sample["probe_sandbox_blockers"] == [
        "class_imbalance",
        "selected_provider_dominance",
    ]
    assert out_of_sample["probe_selected_provider_dominance"] == 1.0
    assert (
        out_of_sample["architecture_review_status"]
        == "selector_sandbox_blocked_out_of_sample_controls_not_selector_diverse"
    )
    assert out_of_sample["architecture_selector_signal_status"] == (
        "not_ready_due_to_class_imbalance_and_provider_dominance"
    )
    assert "runtime_arbiter" in out_of_sample["blocked_next_steps"]
    assert "selector_sandbox" in out_of_sample["blocked_next_steps"]
    assert "runtime_dtm_or_tablebase" in out_of_sample["blocked_next_steps"]
    assert "gameplay_topology_mutation" in out_of_sample["blocked_next_steps"]
    assert "stage7_promotion" in out_of_sample["blocked_next_steps"]
    assert "stage8_training" in out_of_sample["blocked_next_steps"]
    assert out_of_sample["runtime_arbiter_allowed"] is False
    assert out_of_sample["selector_sandbox_ready"] is False
    assert out_of_sample["runtime_arbiter_implemented"] is False
    assert out_of_sample["runtime_behavior_changed"] is False
    assert out_of_sample["runtime_defaults_changed"] is False
    assert out_of_sample["runtime_dtm_or_tablebase_lookup"] is False
    assert out_of_sample["runtime_terminals_added"] is False
    assert out_of_sample["gameplay_topology_mutation"] is False
    assert out_of_sample["stage7_promotion_allowed"] is False
    assert out_of_sample["stage8_training_allowed"] is False

    runtime_no_scale = payload["strategy_arbiter_runtime_no_scale_gate"]
    assert runtime_no_scale["passive_no_scale_ready"] is True
    assert (
        runtime_no_scale["status"]
        == "runtime_sandbox_safe_but_additive_support_not_ready_to_scale"
    )
    assert (
        runtime_no_scale["default_off_design_status"]
        == "default_off_strategy_arbiter_design_ready_for_external_review"
    )
    assert runtime_no_scale["default_off_design_implementation_allowed"] is False
    assert runtime_no_scale["default_off_design_runtime_arbiter_allowed"] is False
    assert runtime_no_scale["default_off_design_selector_sandbox_ready"] is False
    assert runtime_no_scale["default_off_future_contract_default_enabled"] is False
    assert (
        runtime_no_scale["runtime_review_packet_status"]
        == "runtime_review_packet_ready"
    )
    assert runtime_no_scale["runtime_review_packet_implementation_allowed"] is False
    assert runtime_no_scale["runtime_review_packet_runtime_arbiter_allowed"] is False
    assert runtime_no_scale["runtime_review_packet_selector_sandbox_ready"] is False
    assert runtime_no_scale["runtime_review_packet_blocked_until_review"] is True
    assert runtime_no_scale["runtime_review_packet_stage7_heldout_row_count"] == 4
    assert (
        runtime_no_scale["runtime_sandbox_smoke_status"]
        == "runtime_sandbox_smoke_passed"
    )
    assert runtime_no_scale["runtime_sandbox_default_off_equivalence_passed"] is True
    assert runtime_no_scale["runtime_sandbox_enabled_support_trace_visible"] is True
    assert (
        runtime_no_scale[
            "runtime_sandbox_flag_present_default_off_decision_matches_baseline"
        ]
        is True
    )
    assert (
        runtime_no_scale[
            "runtime_sandbox_flag_present_default_off_outcome_matches_baseline"
        ]
        is True
    )
    assert runtime_no_scale["runtime_sandbox_direct_request"] is False
    assert runtime_no_scale["runtime_sandbox_support_was_applied"] is True
    assert (
        runtime_no_scale["protected_control_matrix_status"]
        == "protected_control_matrix_v2_passed"
    )
    assert runtime_no_scale["protected_control_default_off_equivalence_passed"] is True
    assert runtime_no_scale["protected_control_no_conversion_regression"] is True
    assert runtime_no_scale["protected_control_no_no_move_or_draw_spike"] is True
    assert runtime_no_scale["protected_control_stage7_rows"] == 0
    assert (
        runtime_no_scale["stage7_holdout_status"] == "stage7_holdout_lock_passed"
    )
    assert (
        runtime_no_scale["stage7_holdout_enabled_blocked_matches_baseline"] is True
    )
    assert runtime_no_scale["stage7_holdout_support_blocked"] is True
    assert runtime_no_scale["stage7_holdout_allow_stage7_challenge"] is False
    assert (
        runtime_no_scale["stage7_challenge_status"]
        == "stage7_challenge_probe_no_regression"
    )
    assert runtime_no_scale["stage7_challenge_conversion_delta"] == 0
    assert runtime_no_scale["stage7_challenge_selected_supported_count"] == 0
    assert runtime_no_scale["stage7_challenge_no_no_move_or_draw_spike"] is True
    assert (
        runtime_no_scale["support_sensitivity_status"]
        == "support_sensitivity_measured"
    )
    assert (
        runtime_no_scale["support_sensitivity_protected_control_status"]
        == "high_support_changes_protected_one_ply_ownership"
    )
    assert (
        runtime_no_scale["support_sensitivity_stage7_runtime_test_status"]
        == "no_low_support_ownership_effect"
    )
    assert runtime_no_scale["support_sensitivity_low_support_cap"] == 5.0
    assert (
        runtime_no_scale["support_sensitivity_stage7_changes_under_low_support_cap"]
        is False
    )
    assert runtime_no_scale["support_sensitivity_scale_risk"] == (
        "high_support_changes_protected_ownership_before_safe_stage7_evidence"
    )
    assert (
        runtime_no_scale["runtime_test_review_status"]
        == "runtime_sandbox_safe_but_additive_support_not_ready_to_scale"
    )
    assert runtime_no_scale["runtime_test_review_runtime_promotion_allowed"] is False
    assert (
        runtime_no_scale["runtime_test_review_small_support_protected_no_regression"]
        is True
    )
    assert (
        runtime_no_scale["runtime_test_review_small_support_stage7_effective"]
        is False
    )
    assert runtime_no_scale["runtime_test_review_high_support_scale_risk"] is True
    assert (
        runtime_no_scale["runtime_test_review_stage7_holdout_locked_by_default"]
        is True
    )
    assert runtime_no_scale["runtime_test_blocked_path"] == (
        "raise_additive_support_bonus"
    )
    assert "increase_broad_additive_support" in runtime_no_scale["blocked_next_steps"]
    assert "stage7_promotion" in runtime_no_scale["blocked_next_steps"]
    assert "stage8_training" in runtime_no_scale["blocked_next_steps"]
    assert "runtime_dtm_or_tablebase" in runtime_no_scale["blocked_next_steps"]
    assert "gameplay_topology_mutation" in runtime_no_scale["blocked_next_steps"]
    assert runtime_no_scale["runtime_defaults_changed"] is False
    assert runtime_no_scale["runtime_dtm_or_tablebase_lookup"] is False
    assert runtime_no_scale["gameplay_topology_mutation"] is False
    assert runtime_no_scale["stage7_promotion_allowed"] is False
    assert runtime_no_scale["stage8_training_allowed"] is False

    provider_identity = payload["provider_identity_maturity_blocker_gate"]
    assert provider_identity["passive_provider_identity_maturity_ready"] is True
    assert (
        provider_identity["status"]
        == "provider_identity_signal_requires_provenance_decomposition"
    )
    assert provider_identity["row_count"] == 42
    assert provider_identity["provider_prior_accuracy"] == 0.8333333333333334
    assert provider_identity["best_feature_probe_baseline"] == "provider_prior_loo"
    assert provider_identity["best_feature_probe_accuracy"] == 0.8333333333333334
    assert provider_identity["provider_identity_signal"] == "strong_but_not_causal_ready"
    assert (
        provider_identity["raw_provider_id_is_principled_runtime_signal"]
        is False
    )
    assert provider_identity["stage0_basin_positive_rate"] == 0.7333333333333333
    assert provider_identity["edge_trap_positive_rates"] == [
        0.1111111111111111,
        0.1111111111111111,
        0.1111111111111111,
    ]
    for feature in [
        "provider_maturity",
        "provider_version",
        "source_stage",
        "validated_profile",
        "frozen_provider",
        "overlay_provider",
        "guardrail_status",
        "plasticity_scope",
        "promotion_status",
        "protected_provider",
    ]:
        assert feature in provider_identity["required_future_features"]
    for blocked in [
        "runtime_arbiter",
        "selector_sandbox",
        "raw_provider_id_runtime_prior",
        "provider_support_adapter",
        "score_bonus_or_penalty",
        "stage7_repair",
        "stage7_promotion",
        "stage8_training",
        "runtime_dtm_or_tablebase",
        "gameplay_topology_mutation",
    ]:
        assert blocked in provider_identity["blocked_next_work"]
    assert provider_identity["runtime_arbiter_allowed"] is False
    assert provider_identity["selector_sandbox_ready"] is False
    assert provider_identity["stage7_repair_allowed"] is False
    assert provider_identity["runtime_arbiter_implemented"] is False
    assert provider_identity["runtime_behavior_changed"] is False
    assert provider_identity["runtime_defaults_changed"] is False
    assert provider_identity["runtime_dtm_or_tablebase_lookup"] is False
    assert provider_identity["gameplay_topology_mutation"] is False
    assert provider_identity["stage7_promotion_allowed"] is False
    assert provider_identity["stage8_training_allowed"] is False

    directed_fix = payload["selector_directed_fix_blocker_gate"]
    assert directed_fix["passive_selector_directed_fix_ready"] is True
    assert directed_fix["status"] == "directed_fix_review_complete_runtime_blocked"
    assert (
        directed_fix["geometry_audit_status"]
        == "geometry_terms_partially_informative_not_sufficient"
    )
    assert directed_fix["geometry_audit_row_count"] == 16
    assert directed_fix["geometry_audit_stage7_row_count"] == 0
    assert directed_fix["geometry_audit_capacity_label_counts"] == {
        "negative_capacity": 5,
        "positive_capacity": 11,
    }
    assert (
        directed_fix["geometry_probe_status"]
        == "geometry_augmented_features_underpowered"
    )
    assert directed_fix["geometry_probe_row_count"] == 16
    assert directed_fix["geometry_probe_state_count"] == 6
    assert directed_fix["geometry_probe_positive_count"] == 11
    assert directed_fix["geometry_probe_negative_count"] == 5
    assert directed_fix["geometry_probe_stage7_row_count"] == 0
    assert directed_fix["geometry_probe_underpowered"] is True
    assert directed_fix["geometry_probe_best_objective"] == "provider_family"
    assert directed_fix["geometry_probe_best_accuracy"] == 0.6875
    assert directed_fix["geometry_probe_best_negative_suppression"] == 0.0
    assert (
        directed_fix["directed_fix_recommended_next_step"]
        == "design_hard_negative_selector_target_dataset_v0"
    )
    assert (
        directed_fix["directed_fix_recommended_class"]
        == "non_causal_hard_negative_selector_target_design"
    )
    assert directed_fix["directed_fix_recommended_not_runtime"] is True
    for rejected in [
        "runtime_selector_now",
        "runtime_candidate_generator_now",
        "train_selector_on_forced_capacity_as_positive",
        "add_simple_geometry_terms_only",
        "return_to_stage7_patch",
    ]:
        assert rejected in directed_fix["directed_fix_rejected_fixes"]
    for requirement in [
        "keep candidate generation and selection as separate channels",
        "create a hard-negative selector target dataset from protected capacity negatives",
        "keep forced-capacity labels distinct from selected-playout labels",
        "add move/post-move geometry only as non-causal scoring features",
        "evaluate leave-state-out suppression before any sandbox",
        "keep Stage 7 held out",
    ]:
        assert requirement in directed_fix["directed_fix_requirements"]
    assert directed_fix["runtime_work_allowed"] is False
    assert directed_fix["candidate_generator_runtime_allowed"] is False
    assert directed_fix["selector_training_allowed"] is False
    assert directed_fix["runtime_behavior_changed"] is False
    assert directed_fix["runtime_defaults_changed"] is False
    assert directed_fix["runtime_selector_implemented"] is False
    assert directed_fix["runtime_candidate_generator_implemented"] is False
    assert directed_fix["runtime_terminals_added"] is False
    assert directed_fix["runtime_dtm_or_tablebase_lookup"] is False
    assert directed_fix["gameplay_topology_mutation"] is False
    assert directed_fix["stage7_promotion_allowed"] is False
    assert directed_fix["stage8_training_allowed"] is False

    forced_provider = payload["forced_provider_control_label_lineage_gate"]
    assert forced_provider["passive_forced_provider_control_lineage_ready"] is True
    assert (
        forced_provider["status"]
        == "merge_forced_provider_control_labels_and_rerun_stratified_probe"
    )
    assert forced_provider["plan_causal_status"] == "non_causal_label_plan"
    assert forced_provider["plan_selected_job_count"] == 12
    assert forced_provider["plan_selected_job_count_by_stage"] == {
        "stage5": 6,
        "stage6": 6,
    }
    assert forced_provider["plan_current_label_result_counts"] == {
        "mate": 8,
        "max_plies": 4,
    }
    assert forced_provider["plan_target_stages"] == ["stage5", "stage6"]
    assert (
        forced_provider["manifest_causal_status"]
        == "non_causal_execution_manifest"
    )
    assert forced_provider["manifest_all_bindings_valid"] is True
    assert forced_provider["manifest_job_count"] == 12
    assert forced_provider["manifest_missing_path_count"] == 0
    assert forced_provider["labels_causal_status"] == "non_causal_label_run"
    assert forced_provider["label_count"] == 12
    assert forced_provider["label_stage_counts"] == {
        "stage4": 0,
        "stage5": 6,
        "stage6": 6,
        "stage7": 0,
    }
    assert forced_provider["result_counts"] == {"mate": 9, "max_plies": 3}
    assert forced_provider["result_counts_by_stage"] == {
        "stage5:mate": 6,
        "stage6:mate": 3,
        "stage6:max_plies": 3,
    }
    assert forced_provider["trace_failures_only"] is True
    assert forced_provider["trace_included_count"] == 0
    assert forced_provider["forced_successor_available_count"] == 12
    assert forced_provider["provider_ids"] == [
        "krk.edge_trap_close",
        "krk.edge_trap_enemy_between",
        "krk.edge_trap_wrong_tempo",
        "krk.stage0_basin",
    ]
    for blocked in [
        "runtime_arbiter",
        "runtime_internal_terminal",
        "stage7_promotion",
        "stage8_training",
        "runtime_dtm_or_tablebase",
        "gameplay_topology_mutation",
    ]:
        assert blocked in forced_provider["blocked_next_steps"]
    assert forced_provider["runtime_behavior_changed"] is False
    assert forced_provider["runtime_defaults_changed"] is False
    assert forced_provider["runtime_dtm_or_tablebase_lookup"] is False
    assert forced_provider["gameplay_topology_mutation"] is False
    assert forced_provider["stage7_promotion_allowed"] is False
    assert forced_provider["stage8_training_allowed"] is False

    selector_prior = payload["selector_provenance_prior_blocker_gate"]
    assert selector_prior["passive_provenance_prior_blocker_ready"] is True
    assert (
        selector_prior["status"] == "provider_prior_remains_best_no_selector_sandbox"
    )
    assert selector_prior["target_dataset_status"] == "selector_target_dataset_built"
    assert selector_prior["target_dataset_training_row_count"] == 42
    assert selector_prior["target_dataset_stage7_training_rows"] == 0
    assert selector_prior["target_dataset_target_kind_counts"] == {
        "forced_provider_conversion": 12,
        "held_out_challenge": 9,
        "selected_playout_success": 42,
    }
    assert (
        selector_prior["target_probe_status"]
        == "target_dataset_ready_for_non_causal_baseline_probe"
    )
    assert selector_prior["target_probe_training_label_counts"] == {
        "negative": 28,
        "positive": 14,
    }
    assert selector_prior["target_probe_heldout_training_row_count"] == 0
    assert (
        selector_prior["baseline_probe_status"]
        == "simple_selector_baseline_promising_non_causal"
    )
    assert selector_prior["baseline_probe_best_baseline"] == "provider_prior_loo"
    assert selector_prior["baseline_probe_best_accuracy"] == 0.8333333333333334
    assert selector_prior["feature_dataset_status"] == "selector_feature_dataset_built"
    assert selector_prior["feature_dataset_training_row_count"] == 42
    assert selector_prior["feature_dataset_stage7_training_rows"] == 0
    assert selector_prior["feature_dataset_rows_with_observation"] == 60
    assert (
        selector_prior["feature_baseline_status"]
        == "provider_prior_remains_best_non_causal_baseline"
    )
    assert selector_prior["feature_baseline_best_name"] == "provider_prior_loo"
    assert selector_prior["feature_baseline_best_accuracy"] == 0.8333333333333334
    assert selector_prior["feature_baseline_improved_over_provider_prior"] is False
    assert (
        selector_prior["provenance_dataset_status"]
        == "selector_provenance_feature_dataset_built"
    )
    assert selector_prior["provenance_dataset_rows_with_provider_provenance"] == 54
    assert selector_prior["provenance_dataset_training_row_count"] == 42
    assert selector_prior["provenance_dataset_stage7_training_rows"] == 0
    assert (
        selector_prior["provenance_probe_status"]
        == "provenance_features_explain_provider_prior_non_causal"
    )
    assert selector_prior["provenance_probe_raw_provider_id_runtime_prior_allowed"] is False
    assert selector_prior["provenance_probe_runtime_arbiter_allowed"] is False
    assert selector_prior["provenance_probe_selector_sandbox_ready"] is False
    assert selector_prior["provenance_probe_best_name"] == "provider_id_loo"
    assert selector_prior["provenance_probe_best_accuracy"] == 0.8333333333333334
    assert "runtime_arbiter" in selector_prior["provenance_probe_blocked_next_work"]
    assert "selector_sandbox" in selector_prior["provenance_probe_blocked_next_work"]
    assert (
        "raw_provider_id_runtime_prior"
        in selector_prior["provenance_probe_blocked_next_work"]
    )
    assert "stage7_promotion" in selector_prior["provenance_probe_blocked_next_work"]
    assert "stage8_training" in selector_prior["provenance_probe_blocked_next_work"]
    assert (
        selector_prior["architecture_review_status"]
        == "provider_prior_remains_best_no_selector_sandbox"
    )
    assert selector_prior["architecture_best_baseline"] == "provider_prior_loo"
    assert (
        selector_prior["architecture_best_baseline_accuracy"] == 0.8333333333333334
    )
    assert (
        selector_prior["architecture_observation_features_improved_over_provider_prior"]
        is False
    )
    assert selector_prior["architecture_must_remain_non_causal"] is True
    assert "runtime_arbiter" in selector_prior["architecture_blocked_next_work"]
    assert (
        "default_off_selector_sandbox"
        in selector_prior["architecture_blocked_next_work"]
    )
    assert (
        "runtime_dtm_or_tablebase" in selector_prior["architecture_blocked_next_work"]
    )
    assert (
        "gameplay_topology_mutation"
        in selector_prior["architecture_blocked_next_work"]
    )
    assert "stage7_promotion" in selector_prior["architecture_blocked_next_work"]
    assert "stage8_training" in selector_prior["architecture_blocked_next_work"]
    assert (
        selector_prior["after_contrast_status"]
        == "selector_sandbox_blocked_selected_provider_evidence_missing"
    )
    assert selector_prior["after_contrast_runtime_arbiter_allowed"] is False
    assert selector_prior["after_contrast_selector_sandbox_ready"] is False
    assert selector_prior["after_contrast_training_row_count"] == 9
    assert selector_prior["after_contrast_heldout_row_count"] == 4
    assert selector_prior["after_contrast_readiness_blockers"] == [
        "insufficient_selected_provider_family_diversity"
    ]
    assert selector_prior["after_contrast_selected_training_provider_families"] == [
        "edge_trap"
    ]
    assert "runtime_arbiter" in selector_prior["after_contrast_blocked_next_steps"]
    assert "selector_sandbox" in selector_prior["after_contrast_blocked_next_steps"]
    assert (
        "runtime_dtm_or_tablebase"
        in selector_prior["after_contrast_blocked_next_steps"]
    )
    assert (
        "gameplay_topology_mutation"
        in selector_prior["after_contrast_blocked_next_steps"]
    )
    assert "stage7_promotion" in selector_prior["after_contrast_blocked_next_steps"]
    assert "stage8_training" in selector_prior["after_contrast_blocked_next_steps"]
    assert selector_prior["runtime_arbiter_implemented"] is False
    assert selector_prior["runtime_behavior_changed"] is False
    assert selector_prior["runtime_defaults_changed"] is False
    assert selector_prior["runtime_dtm_or_tablebase_lookup"] is False
    assert selector_prior["gameplay_topology_mutation"] is False
    assert selector_prior["stage7_promotion_allowed"] is False
    assert selector_prior["stage8_training_allowed"] is False

    selector_objective = payload["selector_objective_normalization_gate"]
    assert selector_objective["passive_objective_ready"] is True
    assert (
        selector_objective["arbitration_objective_status"]
        == "additive_support_objective_rejected_design_normalized_selector_objective"
    )
    assert selector_objective["arbitration_runtime_test_allowed_next"] is False
    assert selector_objective["arbitration_contrast_positive_provider_families"] == [
        "drive_to_edge",
        "edge_trap",
        "fence_established",
    ]
    assert (
        selector_objective["normalized_objective_status"]
        == "normalized_selector_objective_design_ready_for_offline_probe"
    )
    assert selector_objective["normalized_objective_runtime_test_allowed_next"] is False
    assert (
        selector_objective["normalized_probe_status"]
        == "normalized_objective_probe_underpowered_fields_available"
    )
    assert selector_objective["normalized_probe_benchmark_underpowered"] is True
    assert selector_objective["normalized_probe_fields_available"] is True
    assert (
        selector_objective["normalized_probe_review_status"]
        == "normalized_selector_signal_promising_more_ranked_frames_required"
    )
    assert selector_objective["normalized_probe_review_stage7_training_leakage"] is False
    assert (
        selector_objective["selector_architecture_status"]
        == "selector_objective_needs_stratified_label_expansion_before_sandbox"
    )
    assert selector_objective["selector_architecture_runtime_arbiter_allowed"] is False
    assert selector_objective["selector_architecture_sandbox_ready"] is False
    assert selector_objective["selector_label_semantics_sandbox_ready"] is False
    assert selector_objective["selector_label_semantics_target_kind_count"] == 6
    assert (
        selector_objective["split_dataset_v0_status"]
        == "split_selector_objective_channels_built"
    )
    assert selector_objective["split_dataset_v0_objective_row_count"] == 103
    assert selector_objective["split_dataset_v0_ownership_selection_available"] is False
    assert selector_objective["split_dataset_v0_selector_training_row_count"] == 0
    assert selector_objective["split_dataset_v0_stage7_row_count"] == 0
    assert selector_objective["split_readiness_v0_status"] == (
        "split_objectives_fixed_semantics_runtime_still_blocked"
    )
    assert selector_objective["split_readiness_v0_ownership_available"] is False
    assert selector_objective["split_readiness_v0_selector_training_allowed"] is False
    assert selector_objective["split_readiness_v0_selector_training_row_count"] == 0
    assert selector_objective["split_readiness_v0_stage7_row_count"] == 0
    assert selector_objective["split_dataset_v1_status"] == (
        "split_selector_objective_channels_with_ownership_labels"
    )
    assert selector_objective["split_dataset_v1_objective_row_count"] == 116
    assert selector_objective["split_dataset_v1_ownership_selection_row_count"] == 14
    assert selector_objective["split_dataset_v1_selector_training_row_count"] == 0
    assert selector_objective["split_dataset_v1_stage7_row_count"] == 0
    assert selector_objective["split_readiness_v1_status"] == (
        "ownership_labels_recovered_but_underpowered"
    )
    assert selector_objective["split_readiness_v1_ownership_row_count"] == 14
    assert selector_objective["split_readiness_v1_ownership_probe_underpowered"] is True
    assert selector_objective["split_readiness_v1_selector_training_row_count"] == 0
    assert selector_objective["split_readiness_v1_stage7_row_count"] == 0
    assert selector_objective["split_dataset_v2_status"] == (
        "split_selector_objective_channels_with_ownership_labels"
    )
    assert selector_objective["split_dataset_v2_objective_row_count"] == 136
    assert selector_objective["split_dataset_v2_ownership_selection_row_count"] == 34
    assert selector_objective["split_dataset_v2_selector_training_row_count"] == 0
    assert selector_objective["split_dataset_v2_stage7_row_count"] == 0
    assert selector_objective["split_readiness_v2_status"] == (
        "ownership_labels_recovered_but_underpowered"
    )
    assert selector_objective["split_readiness_v2_ownership_row_count"] == 34
    assert selector_objective["split_readiness_v2_ownership_probe_underpowered"] is True
    assert selector_objective["split_readiness_v2_selector_training_row_count"] == 0
    assert selector_objective["split_readiness_v2_stage7_row_count"] == 0
    assert (
        selector_objective["split_dataset_status"]
        == "split_selector_objective_channels_with_ownership_labels"
    )
    assert selector_objective["split_dataset_objective_row_count"] == 136
    assert selector_objective["split_dataset_ownership_selection_row_count"] == 34
    assert selector_objective["split_dataset_selector_training_row_count"] == 0
    assert selector_objective["split_dataset_stage7_row_count"] == 0
    assert selector_objective["split_readiness_status"] == (
        "ownership_labels_recovered_but_underpowered"
    )
    assert selector_objective["split_readiness_runtime_work_allowed"] is False
    assert selector_objective["split_readiness_selector_training_allowed"] is False
    assert selector_objective["split_readiness_ownership_available"] is True
    assert selector_objective["split_readiness_ownership_row_count"] == 34
    assert selector_objective["split_readiness_ownership_probe_underpowered"] is True
    assert selector_objective["split_readiness_selector_training_row_count"] == 0
    assert selector_objective["split_readiness_stage7_row_count"] == 0
    assert selector_objective["runtime_behavior_changed"] is False
    assert selector_objective["runtime_defaults_changed"] is False
    assert selector_objective["runtime_selector_implemented"] is False
    assert selector_objective["runtime_candidate_generator_implemented"] is False
    assert selector_objective["runtime_terminals_added"] is False
    assert selector_objective["stage7_promotion_allowed"] is False
    assert selector_objective["stage8_training_allowed"] is False

    replay_free = payload["selector_replay_free_label_lineage_gate"]
    assert replay_free["passive_replay_free_label_lineage_ready"] is True
    assert replay_free["status"] == (
        "selector_signal_promising_sandbox_blocked_pending_readiness_criteria"
    )
    assert replay_free["plan_status"] == "bounded_selector_stratified_label_plan_ready"
    assert replay_free["plan_execute_labels_now"] is False
    assert replay_free["plan_job_count"] == 11
    assert replay_free["plan_job_stage_counts"] == {
        "stage4": 4,
        "stage5": 4,
        "stage6": 3,
        "stage7": 0,
    }
    assert replay_free["review_status"] == "planned_labels_replay_free_fillable"
    assert replay_free["review_execute_labels_now"] is False
    assert replay_free["review_missing_replay_free_label_count"] == 0
    assert replay_free["review_fill_status_counts"] == {
        "compatible_target_label_available": 11
    }
    assert replay_free["negative_control_status"] == (
        "negative_protected_controls_identified_replay_free"
    )
    assert replay_free["negative_control_count"] == 9
    assert replay_free["negative_control_stage_counts"] == {
        "stage4": 2,
        "stage5": 4,
        "stage6": 3,
    }
    assert replay_free["stratified_dataset_status"] == (
        "stratified_selector_label_dataset_built_replay_free"
    )
    assert replay_free["stratified_dataset_row_count"] == 11
    assert replay_free["stratified_dataset_label_counts"] == {
        "negative": 1,
        "positive": 10,
    }
    assert replay_free["stratified_dataset_stage7_training_rows"] == 0
    assert replay_free["balanced_dataset_status"] == (
        "balanced_selector_label_dataset_built_replay_free"
    )
    assert replay_free["balanced_dataset_row_count"] == 18
    assert replay_free["balanced_dataset_label_counts"] == {
        "negative": 9,
        "positive": 9,
    }
    assert replay_free["balanced_dataset_stage7_training_rows"] == 0
    assert replay_free["balanced_probe_status"] == (
        "balanced_labels_support_non_causal_selector_signal"
    )
    assert replay_free["balanced_probe_best_baseline"] == "provider_id_loo"
    assert replay_free["balanced_probe_best_accuracy"] == 0.7777777777777778
    assert replay_free["architecture_status"] == (
        "selector_signal_promising_sandbox_blocked_pending_readiness_criteria"
    )
    assert replay_free["architecture_selector_sandbox_ready"] is False
    assert replay_free["architecture_runtime_arbiter_allowed"] is False
    assert replay_free["architecture_stage7_repair_allowed"] is False
    assert replay_free["runtime_behavior_changed"] is False
    assert replay_free["runtime_defaults_changed"] is False
    assert replay_free["runtime_arbiter_implemented"] is False
    assert replay_free["runtime_dtm_or_tablebase_lookup"] is False
    assert replay_free["gameplay_topology_mutation"] is False
    assert replay_free["stage7_promotion_allowed"] is False
    assert replay_free["stage8_training_allowed"] is False

    selector_balance = payload["selector_label_balance_gate"]
    assert selector_balance["passive_label_balance_ready"] is True
    assert (
        selector_balance["stratified_dataset_status"]
        == "stratified_selector_label_dataset_built_replay_free"
    )
    assert selector_balance["stratified_dataset_row_count"] == 11
    assert selector_balance["stratified_dataset_stage7_training_rows"] == 0
    assert (
        selector_balance["stratified_probe_status"]
        == "stratified_labels_underbalanced_no_selector_probe"
    )
    assert selector_balance["stratified_probe_label_counts"] == {
        "negative": 1,
        "positive": 10,
    }
    assert selector_balance["stratified_probe_underbalanced"] is True
    assert selector_balance["stratified_probe_runtime_arbiter_allowed"] is False
    assert selector_balance["stratified_probe_selector_sandbox_ready"] is False
    assert (
        selector_balance["balanced_dataset_status"]
        == "balanced_selector_label_dataset_built_replay_free"
    )
    assert selector_balance["balanced_dataset_row_count"] == 18
    assert selector_balance["balanced_dataset_stage7_training_rows"] == 0
    assert selector_balance["balanced_dataset_provider_family_counts"] == {
        "edge_trap": 9,
        "stage0_basin": 9,
    }
    assert (
        selector_balance["balanced_probe_status"]
        == "balanced_labels_support_non_causal_selector_signal"
    )
    assert selector_balance["balanced_probe_label_counts"] == {
        "negative": 9,
        "positive": 9,
    }
    assert selector_balance["balanced_probe_best_baseline"] == "provider_id_loo"
    assert selector_balance["balanced_probe_best_accuracy"] == 0.7777777777777778
    assert selector_balance["balanced_probe_runtime_arbiter_allowed"] is False
    assert selector_balance["balanced_probe_selector_sandbox_ready"] is False
    assert selector_balance["architecture_status"] == (
        "selector_signal_promising_sandbox_blocked_pending_readiness_criteria"
    )
    assert (
        selector_balance["architecture_recommended_next_step"]
        == "define_strategy_arbiter_sandbox_readiness_criteria"
    )
    assert selector_balance["architecture_runtime_arbiter_allowed"] is False
    assert selector_balance["architecture_selector_sandbox_ready"] is False
    assert selector_balance["architecture_stage7_training_rows"] == 0
    assert "runtime_arbiter" in selector_balance["blocked_next_work"]
    assert "runtime_dtm_or_tablebase" in selector_balance["blocked_next_work"]
    assert "stage7_promotion" in selector_balance["blocked_next_work"]
    assert "stage8_training" in selector_balance["blocked_next_work"]
    assert selector_balance["runtime_behavior_changed"] is False
    assert selector_balance["runtime_defaults_changed"] is False
    assert selector_balance["runtime_selector_implemented"] is False
    assert selector_balance["runtime_dtm_or_tablebase_lookup"] is False
    assert selector_balance["runtime_terminals_added"] is False
    assert selector_balance["stage7_promotion_allowed"] is False
    assert selector_balance["stage8_training_allowed"] is False

    ownership_context = payload["ownership_selection_context_gate"]
    assert ownership_context["passive_context_ready"] is True
    assert ownership_context["label_dataset_status"] == (
        "ownership_selection_labels_expanded_with_targeted_false_positive_risk_cells"
    )
    assert ownership_context["label_dataset_merged_row_count"] == 41
    assert ownership_context["label_dataset_target_label_counts"] == {
        "selected_owner_converted": 31,
        "selected_owner_failed": 10,
    }
    assert ownership_context["label_dataset_targeted_added_row_count"] == 6
    assert ownership_context["label_dataset_selector_training_row_count"] == 0
    assert ownership_context["label_dataset_stage7_row_count"] == 0
    assert ownership_context["label_dataset_v0_status"] == (
        "ownership_selection_labels_recovered"
    )
    assert ownership_context["label_dataset_v0_deduplicated_row_count"] == 14
    assert ownership_context["label_dataset_v0_selector_training_row_count"] == 0
    assert ownership_context["label_dataset_v0_stage7_row_count"] == 0
    assert ownership_context["feature_probe_v0_status"] == (
        "ownership_selection_probe_promising_underpowered"
    )
    assert ownership_context["feature_probe_v0_underpowered"] is True
    assert ownership_context["selected_provider_diversity_labels_v0_status"] == (
        "selected_provider_diversity_ownership_labels_collected"
    )
    assert ownership_context["selected_provider_diversity_labels_v0_label_count"] == 20
    assert (
        ownership_context[
            "selected_provider_diversity_labels_v0_stage7_training_rows"
        ]
        == 0
    )
    assert ownership_context["label_dataset_v1_status"] == (
        "ownership_selection_labels_expanded_with_diversity_negatives"
    )
    assert ownership_context["label_dataset_v1_merged_row_count"] == 34
    assert ownership_context["label_dataset_v1_selector_training_row_count"] == 0
    assert ownership_context["label_dataset_v1_stage7_row_count"] == 0
    assert ownership_context["feature_probe_v1_status"] == (
        "ownership_selection_signal_underpowered"
    )
    assert ownership_context["feature_probe_v1_row_count"] == 34
    assert ownership_context["feature_probe_v1_underpowered"] is True
    assert ownership_context["feature_probe_v1_stage7_row_count"] == 0
    assert ownership_context["label_dataset_v2_status"] == (
        "ownership_selection_labels_expanded_with_second_diversity_slice"
    )
    assert ownership_context["label_dataset_v2_merged_row_count"] == 34
    assert ownership_context["label_dataset_v2_selector_training_row_count"] == 0
    assert ownership_context["label_dataset_v2_stage7_row_count"] == 0
    assert ownership_context["feature_probe_v2_status"] == (
        "ownership_selection_signal_underpowered"
    )
    assert ownership_context["feature_probe_v2_row_count"] == 34
    assert ownership_context["feature_probe_v2_underpowered"] is True
    assert ownership_context["feature_probe_v2_stage7_row_count"] == 0
    assert ownership_context["label_dataset_v3_status"] == (
        "ownership_selection_labels_supplemented_from_selected_provider_groups"
    )
    assert ownership_context["label_dataset_v3_merged_row_count"] == 35
    assert ownership_context["label_dataset_v3_selector_training_row_count"] == 0
    assert ownership_context["label_dataset_v3_stage7_row_count"] == 0
    assert ownership_context["label_dataset_v4_status"] == (
        "ownership_selection_labels_refreshed_with_targeted_non_stage0_current_profile_h40"
    )
    assert ownership_context["label_dataset_v4_merged_row_count"] == 35
    assert ownership_context["label_dataset_v4_selector_training_row_count"] == 0
    assert ownership_context["label_dataset_v4_stage7_row_count"] == 0
    assert ownership_context["context_dataset_v0_status"] == (
        "ownership_selection_context_dataset_ready_for_non_causal_probe"
    )
    assert ownership_context["context_dataset_v0_row_count"] == 34
    assert ownership_context["context_dataset_v0_selector_training_row_count"] == 0
    assert ownership_context["context_dataset_v0_stage7_row_count"] == 0
    assert ownership_context["context_probe_v0_status"] == "context_features_underpowered"
    assert ownership_context["context_probe_v0_underpowered"] is True
    assert ownership_context["context_review_v0_status"] == (
        "context_features_review_ready_but_not_runtime_ready"
    )
    assert ownership_context["context_review_v0_runtime_threshold_passed"] is False
    assert ownership_context["context_dataset_v1_status"] == (
        "ownership_selection_context_dataset_ready_for_non_causal_probe"
    )
    assert ownership_context["context_dataset_v1_row_count"] == 35
    assert ownership_context["context_dataset_v1_selector_training_row_count"] == 0
    assert ownership_context["context_dataset_v1_stage7_row_count"] == 0
    assert ownership_context["context_probe_v1_status"] == "context_features_underpowered"
    assert ownership_context["context_probe_v1_underpowered"] is True
    assert ownership_context["context_review_v1_status"] == (
        "context_features_review_ready_but_not_runtime_ready"
    )
    assert ownership_context["context_review_v1_runtime_threshold_passed"] is False
    assert ownership_context["context_dataset_v2_status"] == (
        "ownership_selection_context_dataset_ready_for_non_causal_probe"
    )
    assert ownership_context["context_dataset_v2_row_count"] == 35
    assert ownership_context["context_dataset_v2_selector_training_row_count"] == 0
    assert ownership_context["context_dataset_v2_stage7_row_count"] == 0
    assert ownership_context["context_probe_v2_status"] == "context_features_underpowered"
    assert ownership_context["context_probe_v2_underpowered"] is True
    assert ownership_context["context_review_v2_status"] == (
        "context_features_review_ready_but_not_runtime_ready"
    )
    assert ownership_context["context_review_v2_runtime_threshold_passed"] is False
    assert ownership_context["context_dataset_status"] == (
        "ownership_selection_context_dataset_ready_for_non_causal_probe"
    )
    assert ownership_context["context_dataset_row_count"] == 41
    assert ownership_context["context_dataset_exact_move_context_count"] == 41
    assert ownership_context["context_dataset_label_counts"] == {
        "selected_owner_converted": 31,
        "selected_owner_failed": 10,
    }
    assert ownership_context["context_dataset_provider_family_counts"] == {
        "edge_trap": 3,
        "fence_established": 1,
        "stage0_basin": 37,
    }
    assert ownership_context["context_dataset_selector_training_row_count"] == 0
    assert ownership_context["context_dataset_stage7_row_count"] == 0
    assert ownership_context["context_probe_status"] == "context_features_underpowered"
    assert ownership_context["context_probe_underpowered"] is True
    assert ownership_context["context_probe_row_count"] == 41
    assert ownership_context["context_probe_positive_owner_count"] == 31
    assert ownership_context["context_probe_negative_owner_count"] == 10
    assert ownership_context["context_probe_stage7_row_count"] == 0
    assert ownership_context["labeling_review_status"] == (
        "ownership_labels_improved_but_selector_runtime_blocked"
    )
    assert ownership_context["labeling_review_selector_training_rows"] == 0
    assert ownership_context["labeling_review_stage7_rows"] == 0
    assert ownership_context["source_diversity_status"] == (
        "source_diversity_gap_blocks_runtime"
    )
    assert ownership_context["source_diversity_non_stage0_ownership_row_count"] == 4
    assert ownership_context["source_diversity_ownership_row_count"] == 35
    assert ownership_context["runtime_behavior_changed"] is False
    assert ownership_context["runtime_defaults_changed"] is False
    assert ownership_context["runtime_selector_implemented"] is False
    assert ownership_context["runtime_dtm_or_tablebase_lookup"] is False
    assert ownership_context["runtime_terminals_added"] is False
    assert ownership_context["stage7_promotion_allowed"] is False
    assert ownership_context["stage8_training_allowed"] is False

    negative_suppression = payload["selector_negative_suppression_blocker_gate"]
    assert negative_suppression["passive_blocker_ready"] is True
    assert (
        negative_suppression["protected_max_only_status"]
        == "protected_max_only_frames_block_runtime_selector"
    )
    assert negative_suppression["protected_max_only_frame_count"] == 24
    assert negative_suppression["protected_max_only_frames_with_only_max_plies"] == 12
    assert negative_suppression["protected_max_only_frames_with_mate_provider"] == 12
    assert negative_suppression["protected_max_only_by_stage"] == {
        "stage4": 3,
        "stage5": 4,
        "stage6": 5,
    }
    assert negative_suppression["protected_max_only_runtime_work_allowed"] is False
    assert negative_suppression["negative_suppression_status"] == (
        "selector_negative_suppression_failure_confirmed"
    )
    assert negative_suppression["negative_suppression_runtime_work_allowed"] is False
    assert (
        negative_suppression["negative_suppression_selector_training_allowed"]
        is False
    )
    assert (
        negative_suppression[
            "negative_suppression_candidate_generator_runtime_allowed"
        ]
        is False
    )
    assert negative_suppression["runtime_selector_readiness_status"] == (
        "runtime_selector_not_ready_collect_better_contrast_labels"
    )
    assert (
        negative_suppression["runtime_selector_readiness_runtime_test_allowed_next"]
        is False
    )
    assert negative_suppression["runtime_behavior_changed"] is False
    assert negative_suppression["runtime_defaults_changed"] is False
    assert negative_suppression["runtime_selector_implemented"] is False
    assert negative_suppression["runtime_dtm_or_tablebase_lookup"] is False
    assert negative_suppression["runtime_terminals_added"] is False
    assert negative_suppression["stage7_promotion_allowed"] is False
    assert negative_suppression["stage8_training_allowed"] is False

    abstention = payload["abstention_selector_safety_gate"]
    assert abstention["passive_safety_ready"] is True
    assert abstention["runtime_architecture_lineage_ready"] is True
    assert (
        abstention["runtime_architecture_review_status"]
        == "design_abstention_first_selector_objective"
    )
    assert abstention["runtime_architecture_implementation_allowed"] == "design_only"
    assert (
        "reports/krk_abstention_first_selector_objective_v0.json"
        in abstention["runtime_architecture_next_artifacts"]
    )
    assert abstention["runtime_architecture_selector_ready"] is False
    assert abstention["runtime_architecture_stage7_repair_ready"] is False
    assert abstention["runtime_architecture_internal_terminal_ready"] is False
    assert "runtime_selector" in abstention["runtime_architecture_blocked_next_steps"]
    assert "stage7_promotion" in abstention["runtime_architecture_blocked_next_steps"]
    assert "stage8_training" in abstention["runtime_architecture_blocked_next_steps"]
    assert (
        "runtime_dtm_or_tablebase"
        in abstention["runtime_architecture_blocked_next_steps"]
    )
    assert (
        "gameplay_topology_mutation"
        in abstention["runtime_architecture_blocked_next_steps"]
    )
    assert abstention["runtime_architecture_runtime_behavior_changed"] is False
    assert abstention["runtime_architecture_runtime_defaults_changed"] is False
    assert abstention["runtime_architecture_selector_implemented"] is False
    assert abstention["runtime_architecture_dtm_or_tablebase_lookup"] is False
    assert abstention["runtime_architecture_gameplay_topology_mutation"] is False
    assert abstention["runtime_architecture_stage7_promotion_allowed"] is False
    assert abstention["runtime_architecture_stage8_training_allowed"] is False
    assert (
        abstention["first_objective_status"]
        == "abstention_first_selector_objective_defined"
    )
    assert (
        abstention["safe_preservation_review_status"]
        == "safe_preservation_requires_two_stage_label_semantics"
    )
    assert abstention["safe_preservation_false_positive_count"] == 12
    assert (
        abstention["training_dataset_v0_status"]
        == "abstention_training_dataset_under_minimum_requirements"
    )
    assert abstention["training_dataset_v0_row_count"] == 28
    assert abstention["training_dataset_v0_safe_owner_count"] == 23
    assert abstention["training_dataset_v0_unsafe_owner_count"] == 5
    assert abstention["training_dataset_v0_stage7_training_rows"] == 0
    assert (
        abstention["training_probe_v0_status"]
        == "abstention_signal_underpowered_no_runtime"
    )
    assert abstention["training_probe_v0_under_minimum_requirements"] is True
    assert (
        abstention["training_dataset_status"]
        == "abstention_training_dataset_ready_for_probe"
    )
    assert abstention["training_dataset_row_count"] == 51
    assert abstention["training_dataset_safe_owner_count"] == 34
    assert abstention["training_dataset_unsafe_owner_count"] == 17
    assert abstention["training_dataset_stage7_training_rows"] == 0
    assert abstention["training_probe_status"] == "abstention_signal_underpowered_no_runtime"
    assert abstention["training_probe_under_minimum_requirements"] is False
    assert (
        abstention["context_dataset_status"]
        == "abstention_context_feature_dataset_ready_for_non_causal_probe"
    )
    assert abstention["context_dataset_row_count"] == 51
    assert abstention["context_dataset_stage7_training_rows"] == 0
    assert abstention["context_dataset_terminal_context_proxy_count"] == 51
    assert abstention["context_probe_status"] == "context_features_help_but_runtime_blocked"
    assert abstention["context_probe_improved_negative_suppression"] is True
    assert (
        abstention["context_error_audit_status"]
        == "context_signal_overrejects_safe_owners_runtime_blocked"
    )
    assert abstention["context_error_false_positive_count"] == 12
    assert abstention["context_error_false_negative_count"] == 3
    assert (
        abstention["feature_gap_next_step_status"]
        == "join_abstention_labels_with_control_plane_context"
    )
    assert abstention["feature_gap_implementation_allowed"] == (
        "non_causal_replay_free_only"
    )
    assert abstention["feature_gap_runtime_ready"] is False
    assert "runtime_selector" in abstention["blocked_next_steps"]
    assert "stage7_promotion" in abstention["blocked_next_steps"]
    assert "stage8_training" in abstention["blocked_next_steps"]
    assert "runtime_dtm_or_tablebase" in abstention["blocked_next_steps"]
    assert abstention["runtime_behavior_changed"] is False
    assert abstention["runtime_defaults_changed"] is False
    assert abstention["runtime_selector_implemented"] is False
    assert abstention["runtime_dtm_or_tablebase_lookup"] is False
    assert abstention["stage7_promotion_allowed"] is False
    assert abstention["stage8_training_allowed"] is False

    two_stage_abstention = payload["two_stage_abstention_no_go_gate"]
    assert two_stage_abstention["passive_no_go_ready"] is True
    assert two_stage_abstention["objective_probe_status"] == (
        "two_stage_abstention_signal_present_runtime_review_required"
    )
    assert two_stage_abstention["objective_probe_row_count"] == 51
    assert (
        two_stage_abstention["objective_probe_threshold_passing_objective_count"]
        == 12
    )
    assert two_stage_abstention["runtime_review_status"] == (
        "two_stage_abstention_review_ready_implementation_blocked"
    )
    assert two_stage_abstention["runtime_review_implementation_allowed"] is False
    assert two_stage_abstention["runtime_review_runtime_test_allowed_next"] is False
    assert two_stage_abstention["runtime_review_evidence_row_count"] == 51
    assert two_stage_abstention["default_off_status"] == "default_off_equivalent"
    assert two_stage_abstention["default_off_same_core_metrics"] is True
    assert two_stage_abstention["default_off_stop_condition_fired"] is False
    assert (
        two_stage_abstention["enabled_smoke_status"]
        == "enabled_tiny_smoke_no_behavior_delta"
    )
    assert two_stage_abstention["enabled_smoke_total_penalized_count"] == 24
    assert two_stage_abstention["enabled_smoke_total_selected_penalized_count"] == 0
    assert two_stage_abstention["enabled_smoke_conversion_regressions"] == []
    assert two_stage_abstention["stage7_challenge_status"] == (
        "stage7_challenge_no_target_improvement"
    )
    assert two_stage_abstention["stage7_challenge_conversion_delta_mates"] == 0
    assert two_stage_abstention["stage7_challenge_target_improved"] is False
    assert two_stage_abstention["stage7_challenge_no_regression_detected"] is True
    assert two_stage_abstention["status"] == "no_go_for_scaling_or_promotion"
    assert two_stage_abstention["go_no_go_allowed_status"] == (
        "keep_default_off_runtime_test_code_and_artifacts"
    )
    assert two_stage_abstention["rollback_tag"] == (
        "pre-two-stage-abstention-runtime"
    )
    assert two_stage_abstention["runtime_defaults_changed"] is False
    assert two_stage_abstention["runtime_dtm_or_tablebase_lookup"] is False
    assert two_stage_abstention["gameplay_topology_mutation"] is False
    assert two_stage_abstention["stage7_promotion_allowed"] is False
    assert two_stage_abstention["stage8_training_allowed"] is False
    assert two_stage_abstention["runtime_repair_not_promoted"] is True
    assert two_stage_abstention["stage7_remains_quarantined"] is True
    assert two_stage_abstention["stage8_remains_blocked"] is True
    assert two_stage_abstention["no_hidden_controller"] is True

    targeted_ownership = payload["targeted_ownership_recovery_gate"]
    assert targeted_ownership["passive_recovery_ready"] is True
    assert (
        targeted_ownership["non_stage0_manifest_status"]
        == "targeted_non_stage0_manifest_ready"
    )
    assert targeted_ownership["non_stage0_manifest_job_count"] == 4
    assert targeted_ownership["non_stage0_manifest_stage7_job_count"] == 0
    assert targeted_ownership["non_stage0_manifest_labels_generated"] is False
    assert (
        targeted_ownership["non_stage0_labels_status"]
        == "current_profile_preserves_some_historical_non_stage0_ownership"
    )
    assert targeted_ownership["non_stage0_label_count"] == 4
    assert targeted_ownership["non_stage0_preserved_count"] == 4
    assert targeted_ownership["non_stage0_stage0_collapse_count"] == 0
    assert targeted_ownership["non_stage0_selected_owner_failed_count"] == 1
    assert targeted_ownership["non_stage0_stage7_training_rows"] == 0
    assert (
        targeted_ownership["negative_manifest_status"]
        == "targeted_ownership_negative_manifest_ready"
    )
    assert targeted_ownership["negative_manifest_job_count"] == 6
    assert targeted_ownership["negative_manifest_stage7_job_count"] == 0
    assert targeted_ownership["negative_manifest_labels_generated"] is False
    assert (
        targeted_ownership["negative_labels_status"]
        == "targeted_ownership_negative_labels_collected"
    )
    assert targeted_ownership["negative_label_count"] == 6
    assert targeted_ownership["negative_preselection_preserved_count"] == 6
    assert targeted_ownership["negative_targeted_owner_converted_count"] == 4
    assert targeted_ownership["negative_targeted_owner_failed_count"] == 2
    assert targeted_ownership["negative_stage7_training_rows"] == 0
    assert targeted_ownership["runtime_behavior_changed"] is False
    assert targeted_ownership["runtime_defaults_changed"] is False
    assert targeted_ownership["runtime_selector_implemented"] is False
    assert targeted_ownership["runtime_dtm_or_tablebase_lookup"] is False
    assert targeted_ownership["runtime_terminals_added"] is False
    assert targeted_ownership["stage7_promotion_allowed"] is False
    assert targeted_ownership["stage8_training_allowed"] is False

    balanced_hard_negative = payload["balanced_hard_negative_gate"]
    assert balanced_hard_negative["passive_evidence_ready"] is True
    assert balanced_hard_negative["hard_negative_target_dataset_v0_status"] == (
        "hard_negative_selector_target_candidates_built"
    )
    assert balanced_hard_negative["hard_negative_target_dataset_v0_row_count"] == 16
    assert balanced_hard_negative["hard_negative_target_dataset_v0_training_row_count"] == 0
    assert balanced_hard_negative["hard_negative_target_dataset_v0_stage7_row_count"] == 0
    assert balanced_hard_negative["hard_negative_feature_ablation_v0_status"] == (
        "hard_negative_feature_ablation_no_runtime_ready_signal"
    )
    assert balanced_hard_negative["hard_negative_feature_ablation_v0_underpowered"] is True
    assert balanced_hard_negative["hard_negative_feature_ablation_v0_stage7_row_count"] == 0
    assert balanced_hard_negative["hard_negative_target_dataset_v1_status"] == (
        "hard_negative_selector_target_dataset_expanded"
    )
    assert balanced_hard_negative["hard_negative_target_dataset_v1_row_count"] == 28
    assert balanced_hard_negative["hard_negative_target_dataset_v1_training_row_count"] == 0
    assert balanced_hard_negative["hard_negative_target_dataset_v1_stage7_row_count"] == 0
    assert balanced_hard_negative["hard_negative_feature_ablation_v1_status"] == (
        "hard_negative_feature_ablation_still_not_runtime_ready"
    )
    assert balanced_hard_negative["hard_negative_feature_ablation_v1_underpowered"] is True
    assert balanced_hard_negative["hard_negative_feature_ablation_v1_stage7_row_count"] == 0
    assert balanced_hard_negative["label_plan_v0_status"] == (
        "balanced_hard_negative_label_plan_ready"
    )
    assert balanced_hard_negative["label_plan_v0_job_count"] == 12
    assert balanced_hard_negative["label_plan_v0_stage7_jobs"] == 0
    assert balanced_hard_negative["execution_manifest_v0_status"] == (
        "balanced_hard_negative_execution_manifest_bound"
    )
    assert balanced_hard_negative["execution_manifest_v0_labels_allowed_now"] is False
    assert balanced_hard_negative["execution_manifest_v0_job_count"] == 12
    assert balanced_hard_negative["execution_manifest_v0_stage7_jobs"] == 0
    assert balanced_hard_negative["execution_manifest_review_v0_status"] == (
        "balanced_hard_negative_manifest_review_passed_labels_allowed"
    )
    assert balanced_hard_negative["labels_v0_status"] == (
        "balanced_hard_negative_labels_completed"
    )
    assert balanced_hard_negative["label_v0_count"] == 12
    assert balanced_hard_negative["stage7_labels_v0"] == 0
    assert balanced_hard_negative["stage7_training_labels_v0"] == 0
    assert (
        balanced_hard_negative["label_plan_status"]
        == "balanced_hard_negative_label_plan_v1_ready"
    )
    assert balanced_hard_negative["label_plan_job_count"] == 12
    assert balanced_hard_negative["label_plan_stage7_jobs"] == 0
    assert (
        balanced_hard_negative["execution_manifest_status"]
        == "balanced_hard_negative_execution_manifest_bound"
    )
    assert balanced_hard_negative["execution_manifest_labels_allowed_now"] is False
    assert balanced_hard_negative["execution_manifest_all_bindings_valid"] is True
    assert balanced_hard_negative["execution_manifest_job_count"] == 12
    assert balanced_hard_negative["execution_manifest_stage7_jobs"] == 0
    assert (
        balanced_hard_negative["execution_manifest_review_status"]
        == "balanced_hard_negative_manifest_review_passed_labels_allowed"
    )
    assert (
        balanced_hard_negative["labels_status"]
        == "balanced_hard_negative_labels_completed"
    )
    assert balanced_hard_negative["label_count"] == 12
    assert balanced_hard_negative["positive_capacity_count"] == 11
    assert balanced_hard_negative["negative_capacity_count"] == 1
    assert balanced_hard_negative["stage7_labels"] == 0
    assert balanced_hard_negative["stage7_training_labels"] == 0
    assert balanced_hard_negative["trace_failures_only"] is True
    assert (
        balanced_hard_negative["evidence_review_status"]
        == "balanced_hard_negative_signal_promising_but_underpowered"
    )
    assert balanced_hard_negative["evidence_underpowered"] is True
    assert balanced_hard_negative["evidence_expanded_row_count"] == 40
    assert balanced_hard_negative["evidence_expanded_hard_negative_count"] == 9
    assert balanced_hard_negative["evidence_expanded_positive_context_count"] == 31
    assert balanced_hard_negative["evidence_stage7_row_count"] == 0
    assert balanced_hard_negative["runtime_behavior_changed"] is False
    assert balanced_hard_negative["runtime_defaults_changed"] is False
    assert balanced_hard_negative["runtime_selector_implemented"] is False
    assert balanced_hard_negative["runtime_dtm_or_tablebase_lookup"] is False
    assert balanced_hard_negative["runtime_terminals_added"] is False
    assert balanced_hard_negative["stage7_promotion_allowed"] is False
    assert balanced_hard_negative["stage8_training_allowed"] is False

    hard_negative_semantics = payload["hard_negative_label_semantics_gate"]
    assert hard_negative_semantics["passive_semantics_ready"] is True
    assert hard_negative_semantics["status"] == (
        "capacity_labels_not_direct_selector_targets"
    )
    assert hard_negative_semantics["recommended_next_step"] == (
        "run_stronger_capacity_risk_feature_review_non_causal"
    )
    assert hard_negative_semantics["runtime_work_allowed"] is False
    assert hard_negative_semantics["selector_training_allowed"] is False
    assert hard_negative_semantics["row_count"] == 40
    assert hard_negative_semantics["state_count"] == 14
    assert hard_negative_semantics["stage7_row_count"] == 0
    assert hard_negative_semantics["capacity_negative_count"] == 9
    assert hard_negative_semantics["capacity_positive_count"] == 31
    assert hard_negative_semantics["state_local_contrast_state_count"] == 2
    assert hard_negative_semantics["best_ablation_negative_suppression"] == (
        0.2222222222222222
    )
    assert hard_negative_semantics["best_ablation_positive_recall"] == 1.0
    assert hard_negative_semantics["capacity_recall_objective"] == (
        "which validated providers should be present in candidate set"
    )
    assert hard_negative_semantics["capacity_risk_objective"] == (
        "which forced-provider paths are risky under current h40 continuation"
    )
    assert hard_negative_semantics["blocked_use_by_label_channel"] == {
        "forced_provider_capacity_label": (
            "direct_runtime_owner_selection_or_suppression"
        ),
        "state_local_capacity_contrast": "global provider-family suppression",
        "hard_negative_capacity": (
            "selector training target until safe-owner preservation is separately "
            "validated"
        ),
    }
    assert hard_negative_semantics["stronger_feature_review_consumes_semantics"] is True
    assert hard_negative_semantics["runtime_behavior_changed"] is False
    assert hard_negative_semantics["runtime_defaults_changed"] is False
    assert hard_negative_semantics["runtime_selector_implemented"] is False
    assert (
        hard_negative_semantics["runtime_candidate_generator_implemented"]
        is False
    )
    assert hard_negative_semantics["runtime_dtm_or_tablebase_lookup"] is False
    assert hard_negative_semantics["runtime_terminals_added"] is False
    assert hard_negative_semantics["gameplay_topology_mutation"] is False
    assert hard_negative_semantics["stage7_promotion_allowed"] is False
    assert hard_negative_semantics["stage8_training_allowed"] is False

    stronger_feature = payload["stronger_selector_feature_gate"]
    assert stronger_feature["passive_feature_review_ready"] is True
    assert stronger_feature["feature_ablation_status"] == (
        "hard_negative_feature_ablation_promising_underpowered"
    )
    assert stronger_feature["feature_ablation_underpowered"] is True
    assert stronger_feature["feature_ablation_row_count"] == 40
    assert stronger_feature["feature_ablation_state_count"] == 14
    assert stronger_feature["feature_ablation_hard_negative_count"] == 9
    assert stronger_feature["feature_ablation_positive_context_count"] == 31
    assert stronger_feature["feature_ablation_stage7_row_count"] == 0
    assert stronger_feature["feature_ablation_best_objective"] == (
        "provider_piece_king_delta@0.5"
    )
    assert stronger_feature["feature_ablation_best_negative_suppression"] == (
        0.2222222222222222
    )
    assert stronger_feature["feature_review_status"] == (
        "stronger_features_review_ready_runtime_still_blocked"
    )
    assert stronger_feature["feature_review_recommended_next_step"] == (
        "architecture_review_before_selector_training_or_runtime"
    )
    assert stronger_feature["feature_review_improved_over_v2_ablation"] is True
    assert stronger_feature["feature_review_row_count"] == 40
    assert stronger_feature["feature_review_state_count"] == 14
    assert stronger_feature["feature_review_hard_negative_count"] == 9
    assert stronger_feature["feature_review_positive_context_count"] == 31
    assert stronger_feature["feature_review_stage7_row_count"] == 0
    assert stronger_feature["feature_review_previous_best_negative_suppression"] == (
        0.2222222222222222
    )
    assert stronger_feature["feature_review_best_negative_suppression"] == (
        0.7777777777777778
    )
    assert stronger_feature["feature_review_previous_best_positive_recall"] == 1.0
    assert stronger_feature["feature_review_best_positive_recall"] == (
        0.9032258064516129
    )
    assert stronger_feature["feature_review_best_objective"] == "piece_motion@0.5"
    assert stronger_feature["feature_review_best_accuracy"] == 0.875
    assert stronger_feature["feature_review_best_false_negative"] == 3
    assert stronger_feature["feature_review_best_false_positive"] == 2
    assert stronger_feature["runtime_behavior_changed"] is False
    assert stronger_feature["runtime_defaults_changed"] is False
    assert stronger_feature["runtime_selector_implemented"] is False
    assert stronger_feature["runtime_candidate_generator_implemented"] is False
    assert stronger_feature["runtime_dtm_or_tablebase_lookup"] is False
    assert stronger_feature["runtime_terminals_added"] is False
    assert stronger_feature["gameplay_topology_mutation"] is False
    assert stronger_feature["stage7_promotion_allowed"] is False
    assert stronger_feature["stage8_training_allowed"] is False

    provider_diversity = payload["selected_provider_diversity_gate"]
    assert provider_diversity["passive_diversity_review_ready"] is True
    assert provider_diversity["evidence_plan_status"] == (
        "selected_provider_diversity_evidence_plan_defined"
    )
    assert provider_diversity["evidence_plan_runtime_arbiter_allowed"] is False
    assert provider_diversity["evidence_plan_selector_sandbox_ready"] is False
    assert provider_diversity["replay_free_scan_status"] == (
        "selected_provider_diversity_replay_free_insufficient"
    )
    assert provider_diversity["replay_free_selected_record_count"] == 23
    assert provider_diversity["replay_free_stage7_records"] == 0
    assert (
        provider_diversity["replay_free_max_selected_provider_family_dominance"]
        == 0.7826
    )
    assert provider_diversity["observation_manifest_status"] == (
        "selected_provider_diversity_sampling_manifest_review_required"
    )
    assert provider_diversity["observation_manifest_job_count"] == 20
    assert provider_diversity["observation_manifest_stage7_jobs"] == 0
    assert provider_diversity["observation_manifest_review_status"] == (
        "selected_provider_diversity_sampling_manifest_review_passed"
    )
    assert (
        provider_diversity["observation_manifest_review_observations_allowed"]
        is True
    )
    assert provider_diversity["observation_scan_status"] == (
        "selected_provider_diversity_observation_insufficient"
    )
    assert provider_diversity["observation_scan_count"] == 20
    assert provider_diversity["observation_scan_stage7_observations"] == 0
    assert (
        provider_diversity["observation_scan_max_selected_provider_family_dominance"]
        == 1.0
    )
    assert provider_diversity["manifest_status"] == (
        "fresh_seed_selected_provider_diversity_manifest_ready_for_bounded_labels"
    )
    assert provider_diversity["manifest_observations_allowed_now"] is False
    assert provider_diversity["manifest_bounded_labels_allowed_by_script"] is True
    assert provider_diversity["manifest_runtime_arbiter_allowed"] is False
    assert provider_diversity["manifest_all_bindings_valid"] is True
    assert provider_diversity["manifest_job_count"] == 18
    assert provider_diversity["manifest_job_count_by_stage"] == {
        "stage4": 8,
        "stage5": 6,
        "stage6": 4,
    }
    assert provider_diversity["manifest_stage7_jobs"] == 0
    assert provider_diversity["manifest_observation_only"] is True
    assert provider_diversity["labels_status"] == (
        "fresh_seed_selected_provider_diversity_ownership_labels_collected"
    )
    assert provider_diversity["label_count"] == 18
    assert provider_diversity["ownership_label_counts"] == {
        "selected_owner_converted": 15,
        "selected_owner_failed": 3,
    }
    assert provider_diversity["selected_result_counts"] == {
        "mate": 15,
        "max_plies": 3,
    }
    assert provider_diversity["selected_result_counts_by_stage"] == {
        "stage4:mate": 6,
        "stage4:max_plies": 2,
        "stage5:mate": 6,
        "stage6:mate": 3,
        "stage6:max_plies": 1,
    }
    assert provider_diversity["selected_provider_counts"] == {"krk.stage0_basin": 18}
    assert provider_diversity["stage7_training_rows"] == 0
    assert provider_diversity["trace_failures_only"] is True
    assert provider_diversity["diverse_contrast_plan_status"] == (
        "diverse_contrast_label_plan_ready"
    )
    assert provider_diversity["diverse_contrast_manifest_status"] == (
        "diverse_contrast_execution_manifest_ready"
    )
    assert provider_diversity["diverse_contrast_manifest_job_count"] == 12
    assert provider_diversity["diverse_contrast_labels_status"] == (
        "diverse_contrast_labels_completed"
    )
    assert provider_diversity["diverse_contrast_label_count"] == 12
    assert provider_diversity["diverse_contrast_training_label_count"] == 4
    assert provider_diversity["diverse_contrast_stage7_eval_only_label_count"] == 8
    assert provider_diversity["diverse_contrast_result_counts_by_stage"] == {
        "stage5:mate": 2,
        "stage6:mate": 2,
        "stage7:max_plies": 8,
    }
    assert provider_diversity["diverse_contrast_trace_failures_only"] is True
    assert provider_diversity["diverse_contrast_full_failure_traces_elided"] is True
    assert provider_diversity["architecture_status"] == (
        "selected_provider_diversity_requirement_should_be_reframed"
    )
    assert provider_diversity["architecture_recommended_next_step"] == (
        "define_selector_readiness_v3_proposal_diversity_criteria"
    )
    assert provider_diversity["architecture_runtime_arbiter_allowed"] is False
    assert provider_diversity["architecture_selector_sandbox_ready"] is False
    assert provider_diversity["runtime_behavior_changed"] is False
    assert provider_diversity["runtime_defaults_changed"] is False
    assert provider_diversity["runtime_selector_implemented"] is False
    assert provider_diversity["runtime_candidate_generator_implemented"] is False
    assert provider_diversity["runtime_arbiter_implemented"] is False
    assert provider_diversity["runtime_dtm_or_tablebase_lookup"] is False
    assert provider_diversity["runtime_terminals_added"] is False
    assert provider_diversity["gameplay_topology_mutation"] is False
    assert provider_diversity["stage7_promotion_allowed"] is False
    assert provider_diversity["stage8_training_allowed"] is False

    readiness_v3 = payload["selector_readiness_v3_design_gate"]
    assert readiness_v3["passive_design_review_ready"] is True
    assert readiness_v3["status"] == (
        "selector_readiness_v3_sandbox_design_review_allowed"
    )
    assert readiness_v3["recommended_next_step"] == (
        "design_default_off_strategy_arbiter_sandbox_for_review"
    )
    assert readiness_v3["runtime_arbiter_allowed"] is False
    assert readiness_v3["selector_sandbox_ready"] is False
    assert readiness_v3["hard_blocker_count"] == 0
    assert readiness_v3["passed_checks"] == [
        "proposal_family_diversity",
        "conversion_positive_provider_diversity",
        "label_balance",
        "protected_stage_coverage",
        "stage7_heldout_boundary",
    ]
    assert readiness_v3["diagnostic_only_checks"] == [
        "current_selected_provider_diversity"
    ]
    assert readiness_v3["label_balance"] == {"negative": 11, "positive": 13}
    assert readiness_v3["stage_coverage"] == {
        "stage4": 2,
        "stage5": 4,
        "stage6": 3,
        "stage7": 4,
    }
    assert readiness_v3["stage7_training_rows"] == 0
    assert readiness_v3["conversion_positive_provider_family_count"] == 3
    assert readiness_v3["conversion_positive_provider_families"] == [
        "drive_to_edge",
        "edge_trap",
        "fence_established",
    ]
    assert "runtime_arbiter" in readiness_v3["blocked_next_steps"]
    assert "runtime_dtm_or_tablebase" in readiness_v3["blocked_next_steps"]
    assert "gameplay_topology_mutation" in readiness_v3["blocked_next_steps"]
    assert "default_off" in readiness_v3["sandbox_design_requirements"]
    assert (
        "stage7_held_out_challenge_only"
        in readiness_v3["sandbox_design_requirements"]
    )
    assert readiness_v3["default_off_design_status"] == (
        "default_off_strategy_arbiter_design_ready_for_external_review"
    )
    assert readiness_v3["default_off_design_implementation_allowed"] is False
    assert readiness_v3["runtime_review_packet_readiness_v3_status"] == (
        "selector_readiness_v3_sandbox_design_review_allowed"
    )
    assert readiness_v3["runtime_behavior_changed"] is False
    assert readiness_v3["runtime_defaults_changed"] is False
    assert readiness_v3["runtime_arbiter_implemented"] is False
    assert readiness_v3["runtime_dtm_or_tablebase_lookup"] is False
    assert readiness_v3["runtime_terminals_added"] is False
    assert readiness_v3["gameplay_topology_mutation"] is False
    assert readiness_v3["stage7_promotion_allowed"] is False
    assert readiness_v3["stage8_training_allowed"] is False

    state_local_contrast = payload["state_local_contrast_gate"]
    assert state_local_contrast["passive_contrast_ready"] is True
    assert state_local_contrast["labels_v1_status"] == "state_local_contrast_labels_joined"
    assert state_local_contrast["labels_v1_row_count"] == 28
    assert state_local_contrast["labels_v1_contrast_label_counts"] == {
        "negative": 15,
        "positive": 13,
    }
    assert state_local_contrast["labels_v1_stage7_challenge_row_count"] == 0
    assert state_local_contrast["labels_v1_usable_training_row_count"] == 28
    assert state_local_contrast["labels_v1_runtime_test_allowed_next"] is False
    assert state_local_contrast["probe_v1_status"] == "state_local_contrast_signal_not_ready"
    assert state_local_contrast["probe_v1_row_count"] == 28
    assert state_local_contrast["probe_v1_stage7_training_leakage"] is False
    assert state_local_contrast["probe_v1_runtime_test_allowed_next"] is False
    assert state_local_contrast["labels_status"] == "state_local_contrast_labels_v2_joined"
    assert state_local_contrast["labels_row_count"] == 20
    assert state_local_contrast["labels_state_count"] == 10
    assert state_local_contrast["labels_contrast_label_counts"] == {
        "negative": 11,
        "positive": 9,
    }
    assert state_local_contrast["labels_training_contrast_label_counts"] == {
        "negative": 3,
        "positive": 9,
    }
    assert state_local_contrast["labels_stage7_challenge_row_count"] == 8
    assert state_local_contrast["labels_stage7_contrast_label_counts"] == {
        "negative": 8,
    }
    assert state_local_contrast["labels_usable_training_row_count"] == 12
    assert state_local_contrast["labels_runtime_test_allowed_next"] is False
    assert state_local_contrast["probe_status"] == "state_local_contrast_signal_not_ready"
    assert state_local_contrast["probe_row_count"] == 20
    assert state_local_contrast["probe_training_row_count"] == 12
    assert state_local_contrast["probe_stage7_eval_row_count"] == 8
    assert state_local_contrast["probe_stage7_training_leakage"] is False
    assert state_local_contrast["probe_training_label_counts"] == {
        "negative": 3,
        "positive": 9,
    }
    assert state_local_contrast["probe_stage7_label_counts"] == {"negative": 8}
    assert state_local_contrast["probe_runtime_test_allowed_next"] is False
    assert state_local_contrast["readiness_status"] == (
        "runtime_selector_blocked_negative_suppression_zero"
    )
    assert state_local_contrast["readiness_recommended_next_step"] == (
        "architecture_review_before_more_runtime_tests"
    )
    assert state_local_contrast["readiness_runtime_test_allowed_next"] is False
    assert "runtime_selector" in state_local_contrast["readiness_blocked_next_steps"]
    assert state_local_contrast["runtime_behavior_changed"] is False
    assert state_local_contrast["runtime_defaults_changed"] is False
    assert state_local_contrast["runtime_selector_implemented"] is False
    assert state_local_contrast["runtime_dtm_or_tablebase_lookup"] is False
    assert state_local_contrast["stage7_promotion_allowed"] is False
    assert state_local_contrast["stage8_training_allowed"] is False

    state_local = payload["state_local_paired_ownership_gate"]
    assert state_local["passive_semantic_gate_ready"] is True
    assert (
        state_local["hard_negative_target_dataset_status"]
        == "hard_negative_selector_target_dataset_expanded_v2"
    )
    assert state_local["hard_negative_target_row_count"] == 40
    assert state_local["hard_negative_training_row_count"] == 0
    assert state_local["hard_negative_stage7_row_count"] == 0
    assert (
        state_local["hard_negative_semantics_status"]
        == "hard_negative_targets_approved_for_offline_benchmark_only"
    )
    assert state_local["hard_negative_semantics_current_training_row_count"] == 0
    assert (
        state_local["ownership_context_status"]
        == "context_features_review_ready_but_not_runtime_ready"
    )
    assert state_local["ownership_context_row_count"] == 41
    assert state_local["ownership_context_runtime_threshold_passed"] is False
    assert state_local["ownership_context_targeted_negative_label_count"] == 6
    assert (
        state_local["ownership_architecture_status"]
        == "ownership_objective_requires_state_local_pairing_review"
    )
    assert state_local["ownership_architecture_runtime_threshold_passed"] is False
    assert state_local["ownership_architecture_stage7_rows"] == 0
    assert (
        state_local["objective_plan_status"]
        == "state_local_paired_ownership_objective_plan_ready"
    )
    assert state_local["work_package_status"] == "work_package_ready"
    assert state_local["inventory_v0_status"] == "paired_inventory_underpowered"
    assert state_local["inventory_v0_pair_count"] == 15
    assert state_local["inventory_v0_selector_training_row_count"] == 0
    assert state_local["inventory_v0_stage7_row_count"] == 0
    assert (
        state_local["probe_v0_status"]
        == "paired_objective_feature_model_insufficient"
    )
    assert state_local["probe_v0_inventory_ready"] is True
    assert state_local["probe_v0_stage7_row_count"] == 0
    assert state_local["review_v0_status"] == "feature_model_insufficient"
    assert state_local["review_v0_best_balanced_objective"] == (
        "owner_family_pair@0.25"
    )
    assert state_local["review_v0_stage7_row_count"] == 0
    assert state_local["inventory_status"] == "paired_inventory_ready_for_non_causal_probe"
    assert state_local["inventory_pair_count"] == 40
    assert state_local["inventory_state_count"] == 14
    assert state_local["inventory_same_state_conflict_pair_count"] == 9
    assert state_local["inventory_safe_preservation_pair_count"] == 23
    assert state_local["inventory_selector_training_row_count"] == 0
    assert state_local["inventory_stage7_row_count"] == 0
    assert (
        state_local["probe_status"]
        == "semantic_gate_review_ready_runtime_feature_translation_needed"
    )
    assert state_local["probe_row_count"] == 32
    assert state_local["probe_threshold_passing_model_count"] == 2
    assert state_local["probe_runtime_feature_passing_model_count"] == 0
    assert state_local["probe_stage7_row_count"] == 0
    assert (
        state_local["error_audit_status"]
        == "safe_preservation_false_positives_are_outcome_semantics_errors"
    )
    assert state_local["error_audit_false_positive_count"] == 6
    assert state_local["error_audit_false_negative_count"] == 1
    assert (
        state_local["review_status"]
        == "semantic_gate_review_ready_runtime_feature_translation_needed"
    )
    assert state_local["review_best_objective"] == "safe_preservation_gated_model"
    assert state_local["review_prefer_capacity_recall"] == 1.0
    assert state_local["review_safe_preservation_recall"] == 1.0
    assert state_local["review_selected_preservation_recall"] == 1.0
    assert state_local["review_runtime_feature_passing_model_count"] == 0
    assert state_local["review_stage7_row_count"] == 0
    assert state_local["runtime_behavior_changed"] is False
    assert state_local["runtime_defaults_changed"] is False
    assert state_local["runtime_selector_implemented"] is False
    assert state_local["runtime_dtm_or_tablebase_lookup"] is False
    assert state_local["runtime_terminals_added"] is False
    assert state_local["stage7_promotion_allowed"] is False
    assert state_local["stage8_training_allowed"] is False

    failure_risk = payload["selected_owner_failure_risk_proxy_gate"]
    assert failure_risk["passive_proxy_review_ready"] is True
    assert (
        failure_risk["runtime_proxy_design_status"]
        == "proxy_design_ready_for_replay_free_validation"
    )
    assert (
        failure_risk["runtime_proxy_dataset_status"]
        == "runtime_proxy_dataset_ready_for_non_causal_probe"
    )
    assert failure_risk["runtime_proxy_dataset_row_count"] == 40
    assert failure_risk["runtime_proxy_dataset_selector_training_row_count"] == 0
    assert failure_risk["runtime_proxy_dataset_stage7_row_count"] == 0
    assert failure_risk["runtime_proxy_probe_status"] == (
        "visible_runtime_proxy_features_insufficient"
    )
    assert failure_risk["runtime_proxy_probe_visible_review_ready"] is False
    assert failure_risk["runtime_proxy_review_status"] == (
        "runtime_proxy_translation_still_blocked"
    )
    assert failure_risk["runtime_proxy_review_visible_review_ready"] is False
    assert failure_risk["runtime_review_packet_v0_status"] == (
        "runtime_review_packet_ready_with_translation_blocker"
    )
    assert failure_risk["runtime_review_packet_v0_implementation_allowed"] is False
    assert failure_risk["runtime_review_packet_v0_translation_blocker"] is True
    assert (
        failure_risk["runtime_review_packet_v0_runtime_feature_passing_model_count"]
        == 0
    )
    assert failure_risk["failure_risk_evidence_status"] == (
        "failure_risk_evidence_v1_built"
    )
    assert failure_risk["failure_risk_evidence_row_count"] == 48
    assert failure_risk["failure_risk_evidence_target_counts"] == {
        "failure_risk": 8,
        "safe_preservation": 40,
    }
    assert failure_risk["failure_risk_evidence_selector_training_row_count"] == 0
    assert failure_risk["failure_risk_evidence_stage7_row_count"] == 0
    assert failure_risk["visible_terms_status"] == (
        "visible_failure_risk_terms_extracted_for_probe"
    )
    assert failure_risk["visible_terms_row_count"] == 40
    assert failure_risk["visible_terms_stage7_row_count"] == 0
    assert failure_risk["visible_proxy_precision"] == 1.0
    assert failure_risk["visible_proxy_recall"] == 1.0
    assert failure_risk["visible_proxy_safe_preservation_recall"] == 1.0
    assert failure_risk["visible_proxy_review_status"] == (
        "visible_failure_risk_proxy_candidate_identified_not_runtime_ready"
    )
    assert failure_risk["visible_proxy_review_threshold_met"] is True
    assert failure_risk["visible_proxy_probe_v0_status"] == (
        "visible_failure_risk_proxy_candidate_needs_out_of_sample_validation"
    )
    assert failure_risk["visible_proxy_probe_v0_review_threshold_met"] is True
    assert failure_risk["visible_proxy_probe_v0_row_count"] == 40
    assert failure_risk["visible_proxy_probe_v0_stage7_row_count"] == 0
    assert failure_risk["independent_manifest_status"] == (
        "independent_proxy_validation_manifest_ready"
    )
    assert failure_risk["independent_manifest_execute_labels_now"] is True
    assert failure_risk["independent_manifest_implementation_allowed"] is False
    assert failure_risk["independent_manifest_labels_generated_in_this_slice"] is False
    assert failure_risk["independent_manifest_all_bindings_valid"] is True
    assert failure_risk["independent_manifest_job_count"] == 8
    assert failure_risk["independent_manifest_stage7_job_count"] == 0
    assert failure_risk["independent_manifest_stage7_training_rows"] == 0
    assert failure_risk["independent_validation_v0_status"] == (
        "independent_proxy_validation_failed_or_underpowered"
    )
    assert failure_risk["independent_validation_v0_threshold_met"] is False
    assert failure_risk["independent_validation_v0_proxy_precision"] == 0.0
    assert failure_risk["independent_validation_v0_proxy_recall"] == 0.0
    assert (
        failure_risk["independent_validation_v0_safe_preservation_recall"]
        == 0.42857142857142855
    )
    assert failure_risk["independent_validation_v0_stage7_row_count"] == 0
    assert failure_risk["blocker_review_v0_status"] == (
        "failed_proxy_closed_next_evidence_v1_required"
    )
    assert failure_risk["blocker_review_v0_threshold_met"] is False
    assert failure_risk["blocker_review_v0_false_positive_count"] == 4
    assert failure_risk["blocker_review_v0_false_negative_count"] == 1
    assert failure_risk["blocker_review_v0_stage7_row_count"] == 0
    assert failure_risk["proxy_v1_probe_status"] == "proxy_v1_independent_candidate_found"
    assert failure_risk["proxy_v1_probe_row_count"] == 48
    assert failure_risk["proxy_v1_independent_passing_proxy_count"] == 3
    assert failure_risk["independent_labels_status"] == (
        "independent_proxy_validation_labels_collected"
    )
    assert failure_risk["independent_label_count"] == 8
    assert failure_risk["independent_label_target_failure_risk_count"] == 1
    assert failure_risk["independent_label_stage7_training_rows"] == 0
    assert failure_risk["independent_validation_status"] == (
        "independent_proxy_validation_passed"
    )
    assert failure_risk["independent_validation_threshold_met"] is True
    assert failure_risk["independent_validation_runtime_scope"] == (
        "progress_window_monitor_or_reconsideration_only"
    )
    assert failure_risk["independent_validation_stage7_row_count"] == 0
    assert failure_risk["runtime_proxy_review_packet_v1_status"] == (
        "runtime_review_ready_progress_window_scope_only"
    )
    assert failure_risk["runtime_proxy_review_packet_v1_implementation_allowed"] is False
    assert failure_risk["runtime_proxy_review_packet_v1_precision"] == 1.0
    assert failure_risk["runtime_proxy_review_packet_v1_recall"] == 1.0
    assert failure_risk["runtime_proxy_review_packet_v1_safe_preservation_recall"] == 1.0
    assert failure_risk["runtime_proxy_review_packet_v1_stage7_row_count"] == 0
    assert failure_risk["runtime_behavior_changed"] is False
    assert failure_risk["runtime_defaults_changed"] is False
    assert failure_risk["runtime_selector_implemented"] is False
    assert failure_risk["runtime_dtm_or_tablebase_lookup"] is False
    assert failure_risk["runtime_terminals_added"] is False
    assert failure_risk["stage7_promotion_allowed"] is False
    assert failure_risk["stage8_training_allowed"] is False

    progress_reconsideration = payload["progress_window_reconsideration_gate"]
    assert progress_reconsideration["passive_review_ready"] is True
    assert progress_reconsideration["runtime_test_review_status"] == (
        "runtime_test_scaffold_wired_but_policy_insufficient"
    )
    assert progress_reconsideration["runtime_test_guardrails_allowed_now"] is False
    assert progress_reconsideration["runtime_test_promotion_allowed_now"] is False
    assert (
        progress_reconsideration["runtime_test_default_off_equivalence_passed"] is True
    )
    assert progress_reconsideration["runtime_test_activation_observed"] is True
    assert progress_reconsideration["runtime_test_target_improvement_observed"] is False
    assert progress_reconsideration["runtime_test_safe_regression_observed"] is False
    assert progress_reconsideration["smoke_status"] == (
        "runtime_smoke_activation_observed_no_target_improvement"
    )
    assert progress_reconsideration["smoke_default_off_equivalence_passed"] is True
    assert progress_reconsideration["smoke_improved_target_failure_count"] == 0
    assert progress_reconsideration["smoke_safe_regression_count"] == 0
    assert progress_reconsideration["smoke_target_failure_row_count"] == 1
    assert progress_reconsideration["smoke_protected_label_count"] == 3
    assert progress_reconsideration["smoke_enabled_supported_total"] == 518
    assert progress_reconsideration["smoke_enabled_selected_supported_total"] == 14
    assert progress_reconsideration["post_activation_status"] == (
        "post_activation_failure_classified"
    )
    assert progress_reconsideration["post_activation_implement_next_fix_now"] is False
    assert progress_reconsideration["post_activation_recommended_next_step"] == (
        "return_to_candidate_generation_or_broader_strategy_sequence_track"
    )
    assert (
        progress_reconsideration["classification_primary"]
        == "candidate_set_missing_good_alternative"
    )
    assert progress_reconsideration["classification_labels"] == [
        "candidate_set_missing_good_alternative",
        "visible_support_terms_overbroad",
    ]
    assert progress_reconsideration["promotion_status"] == (
        "quarantined_or_analysis_only"
    )
    assert (
        progress_reconsideration["sandbox_status"]
        == "wired_but_policy_insufficient"
    )
    assert progress_reconsideration["runtime_defaults_changed"] is False
    assert progress_reconsideration["runtime_dtm_or_tablebase_lookup"] is False
    assert progress_reconsideration["gameplay_topology_mutation"] is False
    assert progress_reconsideration["stage7_promotion_allowed"] is False
    assert progress_reconsideration["stage8_training_allowed"] is False

    runtime_policy = payload["runtime_sandbox_policy_update_gate"]
    assert runtime_policy["passive_policy_update_ready"] is True
    assert runtime_policy["status"] == "reviewed_default_off_runtime_sandbox_allowed"
    assert (
        runtime_policy["allowed_scope"]
        == "progress_window_selected_owner_reconsideration"
    )
    assert runtime_policy["broad_runtime_changes_allowed"] is False
    assert runtime_policy["default_policy_changes_allowed"] is False
    assert runtime_policy["stage7_promotion_allowed"] is False
    assert runtime_policy["stage8_training_allowed"] is False
    assert (
        runtime_policy["test_result_status"]
        == "runtime_test_scaffold_wired_but_policy_insufficient"
    )
    assert runtime_policy["test_result_default_off_equivalence_passed"] is True
    assert runtime_policy["test_result_activation_observed"] is True
    assert runtime_policy["test_result_target_improvement_observed"] is False
    assert runtime_policy["test_result_guardrails_allowed_now"] is False
    assert runtime_policy["source_review_packet"] == (
        "reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v1.json"
    )
    assert runtime_policy["progress_window_passive_review_ready"] is True
    assert runtime_policy["hard_boundaries"] == {
        "hidden_python_controller": False,
        "runtime_dtm_or_tablebase": False,
        "gameplay_topology_mutation": False,
        "general_predecision_selector": False,
        "stage7_repair_or_promotion": False,
        "stage8_training": False,
    }
    assert "prove_default_off_equivalence" in runtime_policy["immediate_plan"]
    assert (
        "run_protected_guardrails_only_if_target_improves"
        in runtime_policy["immediate_plan"]
    )
    assert runtime_policy["hidden_python_controller"] is False
    assert runtime_policy["runtime_dtm_or_tablebase_lookup"] is False
    assert runtime_policy["gameplay_topology_mutation"] is False
    assert runtime_policy["general_predecision_selector"] is False
    assert runtime_policy["stage7_repair_or_promotion"] is False
    assert runtime_policy["stage8_training"] is False

    clean_replacement = payload["clean_replacement_review_gate"]
    assert clean_replacement["passive_review_ready"] is True
    assert (
        clean_replacement["replacement_readiness_status"]
        == "retry1_ready_for_remaining_preservation_checks_not_replacement"
    )
    assert (
        clean_replacement["replacement_readiness_clean_stack_replacement_allowed"]
        is False
    )
    assert (
        clean_replacement["snapshot_manifest_status"]
        == "retry1_protected_stack_snapshot_manifest_ready_no_replacement"
    )
    assert clean_replacement["snapshot_manifest_all_referenced_paths_exist"] is True
    assert clean_replacement["snapshot_manifest_replacement_allowed"] is False
    assert clean_replacement["snapshot_current_stack_path_status"]["all_paths_exist"] is True
    assert clean_replacement["snapshot_retry1_stack_path_status"]["all_paths_exist"] is True
    assert (
        clean_replacement["review_packet_status"]
        == "retry1_clean_stack_replacement_review_ready_explicit_approval_required"
    )
    assert clean_replacement["review_packet_replacement_review_ready"] is True
    assert clean_replacement["review_packet_implementation_allowed"] is False
    assert clean_replacement["review_packet_explicit_human_approval_required"] is True
    assert (
        clean_replacement["deferred_review_status"]
        == "clean_stack_adoption_deferred_explicit_approval_required"
    )
    assert clean_replacement["deferred_review_explicit_approval_detected"] is False
    assert clean_replacement["deferred_review_implementation_allowed"] is False
    assert clean_replacement["protected_stage_reference_mode"] == "retry1_manifest_active"
    assert (
        clean_replacement["protected_stage_active_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert clean_replacement["runtime_behavior_changed"] is False
    assert clean_replacement["runtime_defaults_changed"] is False
    assert clean_replacement["runtime_dtm_or_tablebase_lookup"] is False
    assert clean_replacement["gameplay_topology_mutation"] is False
    assert clean_replacement["stage7_promotion_allowed"] is False
    assert clean_replacement["stage8_training_allowed"] is False

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
    contract = payload["control_plane_contract_lineage_gate"]
    assert contract["passive_contract_lineage_ready"] is True
    assert contract["architecture_goal_id"] == "krk_control_plane_evidence_contract_v0"
    assert contract["architecture_goal_type"] == (
        "non_causal_data_contract_and_review"
    )
    assert contract["architecture_must_remain_non_causal"] is True
    assert contract["architecture_runtime_defaults_must_remain_unchanged"] is True
    assert "runtime_arbiter" in contract["architecture_forbidden_next_steps"]
    assert "runtime_internal_terminal" in contract["architecture_forbidden_next_steps"]
    assert "runtime_dtm_or_tablebase" in contract["architecture_forbidden_next_steps"]
    assert "gameplay_topology_mutation" in contract["architecture_forbidden_next_steps"]
    assert "stage7_promotion" in contract["architecture_forbidden_next_steps"]
    assert "stage8_training" in contract["architecture_forbidden_next_steps"]
    assert (
        contract["contract_recommended_next_slice"]
        == "control_plane_manifest_from_existing_artifacts_v0"
    )
    assert contract["contract_causal_status"] == "non_causal_schema_contract"
    assert "all_records_causal_status_non_causal" in (
        contract["contract_validation_requirements"]
    )
    assert contract["manifest_causal_status"] == "non_causal_manifest"
    assert contract["manifest_records_from_existing_artifacts_only"] is True
    assert contract["manifest_new_playouts_added"] == 0
    assert contract["manifest_missing_required_fields_after_manifest"] == []
    assert (
        contract["manifest_recommended_next_slice"]
        == "stratified_control_plane_gap_report_v0"
    )
    assert contract["runtime_behavior_changed"] is False
    assert contract["runtime_defaults_changed"] is False
    assert contract["runtime_selector_implemented"] is False
    assert contract["runtime_dtm_or_tablebase_lookup"] is False
    assert contract["hidden_python_controller"] is False
    assert contract["gameplay_topology_mutation"] is False
    assert contract["stage7_promotion_allowed"] is False
    assert contract["stage8_training_allowed"] is False
    frame_export = payload["control_plane_frame_export_gate"]
    assert frame_export["passive_frame_export_ready"] is True
    assert (
        frame_export["gap_report_next_slice_id"]
        == "export_replay_free_control_plane_frames_v0"
    )
    assert frame_export["gap_report_next_slice_allowed"] is True
    assert frame_export["gap_report_next_slice_causal"] is False
    assert frame_export["gap_report_new_playouts_allowed"] is False
    assert frame_export["gap_report_new_playouts_added"] == 0
    assert frame_export["frame_export_frame_count"] == 33
    assert frame_export["frame_export_frames_by_source_stage"] == {
        "stage4": 6,
        "stage5": 8,
        "stage6": 10,
        "stage7": 9,
    }
    assert frame_export["frame_export_new_playouts_added"] == 0
    assert frame_export["frame_export_strategy_proposal_frame_count"] == 87
    assert frame_export["frame_export_internal_monitor_record_count"] == 224
    assert (
        frame_export["frame_quality_next_slice_id"]
        == "control_plane_frame_dedupe_and_quality_filters_v0"
    )
    assert frame_export["frame_quality_runtime_sandbox"] == "blocked"
    assert frame_export["frame_quality_stage7_promotion"] == "blocked"
    assert frame_export["frame_quality_stage8_training"] == "blocked"
    assert "plan_windows_stage7_only" in frame_export["frame_quality_flag_ids"]
    assert "sequence_examples_stage7_only" in frame_export["frame_quality_flag_ids"]
    assert frame_export["filtered_frame_count"] == 33
    assert frame_export["filtered_strategy_ready_frame_count"] == 24
    assert frame_export["filtered_stage7_boundary_heldout_frame_count"] == 7
    assert frame_export["filtered_new_playouts_added"] == 0
    assert frame_export["filtered_runtime_sandbox"] == "blocked"
    assert frame_export["forced_control_labels_attached"] == 12
    assert frame_export["forced_control_missing_label_job_ids"] == []
    assert frame_export["forced_control_runtime_sandbox"] == "blocked"
    assert frame_export["runtime_behavior_changed"] is False
    assert frame_export["runtime_defaults_changed"] is False
    assert frame_export["runtime_selector_implemented"] is False
    assert frame_export["runtime_dtm_or_tablebase_lookup"] is False
    assert frame_export["hidden_python_controller"] is False
    assert frame_export["gameplay_topology_mutation"] is False
    assert frame_export["stage7_promotion_allowed"] is False
    assert frame_export["stage8_training_allowed"] is False
    strategy_baseline = payload["control_plane_strategy_baseline_gate"]
    assert strategy_baseline["passive_strategy_baseline_ready"] is True
    assert strategy_baseline["provider_label_coverage_plan_ready"] is True
    assert (
        strategy_baseline["provider_label_coverage_status"]
        == "sufficient_for_current_small_probe"
    )
    assert strategy_baseline["provider_label_coverage_benchmark_frame_count"] == 28
    assert strategy_baseline["provider_label_coverage_labeled_frame_count"] == 28
    assert strategy_baseline["provider_label_coverage_known_provider_mate_count"] == 14
    assert strategy_baseline["provider_label_coverage_unknown_examples"] == []
    assert (
        strategy_baseline["provider_label_coverage_recommended_next_slice"]
        == "offline_strategy_arbitration_baseline_v1"
    )
    assert (
        strategy_baseline["provider_label_coverage_labels_generated_in_this_slice"]
        is False
    )
    assert (
        strategy_baseline["provider_label_coverage_runtime_behavior_changed"]
        is False
    )
    assert (
        strategy_baseline["provider_label_coverage_runtime_defaults_changed"]
        is False
    )
    assert strategy_baseline["provider_label_coverage_runtime_arbiter_added"] is False
    assert (
        strategy_baseline["provider_label_coverage_runtime_dtm_or_tablebase_lookup"]
        is False
    )
    assert (
        strategy_baseline["provider_label_coverage_gameplay_topology_mutation"]
        is False
    )
    assert (
        strategy_baseline["provider_label_coverage_stage7_promotion_allowed"]
        is False
    )
    assert (
        strategy_baseline["provider_label_coverage_stage8_training_allowed"]
        is False
    )
    assert strategy_baseline["probe_status"] == (
        "provider_labels_sufficient_for_small_probe"
    )
    assert strategy_baseline["probe_causal_next_step_allowed"] is False
    assert (
        strategy_baseline["probe_recommended_next_slice"]
        == "offline_strategy_arbitration_baseline_v1"
    )
    assert strategy_baseline["probe_strategy_benchmark_frame_count"] == 24
    assert strategy_baseline["probe_provider_labeled_frame_count"] == 24
    assert strategy_baseline["probe_frames_with_known_provider_mate"] == 12
    assert strategy_baseline["baseline_status"] == "strategy_arbitration_promising"
    assert strategy_baseline["baseline_causal_next_step_allowed"] is False
    assert strategy_baseline["baseline_recommended_next_class"] == (
        "non_causal_strategy_arbiter_sandbox_design"
    )
    assert strategy_baseline["baseline_strategy_benchmark_frame_count"] == 24
    assert strategy_baseline["baseline_frames_with_provider_mate"] == 12
    assert strategy_baseline["baseline_frames_with_only_provider_max_plies"] == 12
    assert strategy_baseline["baseline_stage_counts"] == {
        "stage4": 6,
        "stage5": 8,
        "stage6": 10,
    }
    assert strategy_baseline["baseline_selector_names"] == [
        "raw_global_score",
        "normalized_score",
        "provider_local_rank",
        "visible_context_heuristic",
        "stage_prior_heuristic",
    ]
    assert strategy_baseline["baseline_selector_hit_rates"] == {
        "raw_global_score": 1.0,
        "normalized_score": 1.0,
        "provider_local_rank": 1.0,
        "visible_context_heuristic": 0.0,
        "stage_prior_heuristic": 1.0,
    }
    assert strategy_baseline["runtime_behavior_changed"] is False
    assert strategy_baseline["runtime_defaults_changed"] is False
    assert strategy_baseline["runtime_selector_implemented"] is False
    assert strategy_baseline["runtime_dtm_or_tablebase_lookup"] is False
    assert strategy_baseline["hidden_python_controller"] is False
    assert strategy_baseline["gameplay_topology_mutation"] is False
    assert strategy_baseline["stage7_promotion_allowed"] is False
    assert strategy_baseline["stage8_training_allowed"] is False
    stage7_boundary = payload["control_plane_stage7_boundary_gate"]
    assert stage7_boundary["passive_stage7_boundary_ready"] is True
    assert stage7_boundary["boundary_decision_status"] == (
        "box_shrink_reclassified_as_local_evidence_handoff_trigger"
    )
    assert stage7_boundary["boundary_recommended_next_step"] == (
        "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert stage7_boundary["stage7_clean_success_controls_met"] is True
    assert stage7_boundary["stage7_clean_hard_negatives_met"] is True
    assert stage7_boundary["stage7_clean_review_status"] == (
        "stage7_clean_control_collection_closed_heldout_only"
    )
    assert stage7_boundary["strategy_sequence_inventory_status"] == (
        "replay_free_inventory_state_holdout_gap_blocks_runtime"
    )
    assert stage7_boundary["strategy_ready_frame_count"] == 24
    assert stage7_boundary["strategy_ready_by_stage"] == {
        "stage4": 6,
        "stage5": 8,
        "stage6": 10,
    }
    assert stage7_boundary["stage7_boundary_heldout_frame_count"] == 7
    assert stage7_boundary["strategy_probe_status"] == (
        "provider_labels_sufficient_for_small_probe"
    )
    assert stage7_boundary["strategy_baseline_status"] == (
        "strategy_arbitration_promising"
    )
    assert stage7_boundary["approval_receipt_present"] is False
    assert stage7_boundary["approval_receipt_valid"] is False
    assert stage7_boundary["runner_execution_requested"] is False
    assert stage7_boundary["runner_collection_run_allowed"] is False
    assert stage7_boundary["runner_processed_job_count"] == 0
    assert stage7_boundary["runner_executed_job_count"] == 0
    assert stage7_boundary["runtime_behavior_changed"] is False
    assert stage7_boundary["runtime_defaults_changed"] is False
    assert stage7_boundary["runtime_selector_implemented"] is False
    assert stage7_boundary["runtime_dtm_or_tablebase_lookup"] is False
    assert stage7_boundary["hidden_python_controller"] is False
    assert stage7_boundary["gameplay_topology_mutation"] is False
    assert stage7_boundary["stage7_promotion_allowed"] is False
    assert stage7_boundary["stage8_training_allowed"] is False

    sequence = payload["sequence_policy"]
    assert (
        sequence["input_probe_status"]
        == "sequence_policy_input_probe_ready_for_full_non_causal_benchmark"
    )
    assert sequence["input_probe_row_count"] == 118
    assert sequence["input_probe_benchmark_input_ready"] is True
    assert sequence["input_probe_stage4_topk_signal"] is True
    assert sequence["input_probe_protected_plan_window_failure_sparse"] is True
    assert (
        sequence[
            "input_probe_protected_failure_contrast_collection_option_available"
        ]
        is True
    )
    assert (
        sequence[
            "input_probe_protected_failure_contrast_collection_command_available"
        ]
        is True
    )
    assert sequence["input_probe_selector_training_row_count"] == 0
    assert sequence["input_probe_runtime_authorization_row_count"] == 0
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
    assert missing_provider["audit_plan_ready"] is True
    assert (
        missing_provider["audit_plan_status"]
        == "protected_missing_provider_capacity_audit_plan_ready"
    )
    assert missing_provider["audit_plan_job_count"] == 16
    assert missing_provider["audit_plan_source_frame_count"] == 6
    assert missing_provider["audit_plan_stage_counts"] == {
        "stage4": 6,
        "stage5": 7,
        "stage6": 3,
    }
    assert missing_provider["audit_plan_runtime_work_allowed"] is False
    assert missing_provider["audit_plan_runtime_behavior_changed"] is False
    assert missing_provider["audit_plan_runtime_defaults_changed"] is False
    assert missing_provider["audit_plan_runtime_selector_implemented"] is False
    assert missing_provider["audit_plan_runtime_dtm_or_tablebase_lookup"] is False
    assert missing_provider["audit_plan_gameplay_topology_mutation"] is False
    assert missing_provider["audit_plan_stage7_promotion_allowed"] is False
    assert missing_provider["audit_plan_stage8_training_allowed"] is False
    assert (
        missing_provider["execution_manifest_status"]
        == "protected_missing_provider_capacity_execution_manifest_bound"
    )
    assert missing_provider["execution_manifest_job_count"] == 16
    assert missing_provider["execution_manifest_stage7_job_count"] == 0
    assert missing_provider["execution_manifest_labels_allowed_now"] is False
    assert missing_provider["execution_manifest_runtime_work_allowed"] is False
    assert missing_provider["execution_manifest_review_passive_ready"] is True
    assert (
        missing_provider["execution_manifest_review_status"]
        == "protected_missing_provider_capacity_manifest_review_passed_labels_allowed"
    )
    assert missing_provider["execution_manifest_review_labels_allowed"] is True
    assert missing_provider["execution_manifest_review_runtime_work_allowed"] is False
    assert missing_provider["execution_manifest_review_violation_count"] == 0
    assert (
        missing_provider["execution_manifest_review_runtime_behavior_changed"]
        is False
    )
    assert (
        missing_provider["execution_manifest_review_runtime_defaults_changed"]
        is False
    )
    assert (
        missing_provider["execution_manifest_review_runtime_selector_implemented"]
        is False
    )
    assert (
        missing_provider[
            "execution_manifest_review_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        missing_provider["execution_manifest_review_gameplay_topology_mutation"]
        is False
    )
    assert (
        missing_provider["execution_manifest_review_stage7_promotion_allowed"]
        is False
    )
    assert (
        missing_provider["execution_manifest_review_stage8_training_allowed"]
        is False
    )
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
        strategy_source["candidate_proposal_coverage_status"]
        == "candidate_generation_gap_confirmed"
    )
    assert strategy_source["candidate_proposal_coverage_positive_capacity_recall"] == 0.0
    assert strategy_source["candidate_proposal_coverage_missing_positive_capacity_count"] == 11
    assert strategy_source["candidate_proposal_coverage_stage7_row_count"] == 0
    assert strategy_source["candidate_proposal_coverage_selector_training_allowed"] is False
    assert (
        strategy_source["candidate_generation_strategy_review_status"]
        == "strategy_sequence_control_plane_v1_needed"
    )
    assert (
        strategy_source[
            "candidate_generation_strategy_review_runtime_sandbox_allowed"
        ]
        is False
    )
    assert (
        strategy_source[
            "candidate_generation_strategy_review_recommended_next_step"
        ]
        == "define_non_causal_strategy_sequence_candidate_frame_v1"
    )
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
        strategy_source["observation_sandbox_status"]
        == "observation_sandbox_ready_for_non_causal_coverage_analysis"
    )
    assert strategy_source["observation_sandbox_generated_candidate_count"] == 93
    assert strategy_source["observation_sandbox_selected_move_or_provider_changed"] is False
    assert (
        strategy_source["observation_coverage_status"]
        == "observation_frames_usable_for_non_causal_coverage_analysis"
    )
    assert strategy_source["observation_coverage_sampled_frame_count"] == 93
    assert strategy_source["observation_coverage_invariant_failure_count"] == 0
    assert (
        strategy_source["observation_broadened_status"]
        == "broadened_observation_sample_supports_coverage_analysis"
    )
    assert strategy_source["observation_broadened_case_count"] == 19
    assert strategy_source["observation_broadened_emitted_frame_count"] == 569
    assert (
        strategy_source[
            "observation_broadened_selected_move_or_provider_delta_count"
        ]
        == 0
    )
    assert (
        strategy_source["observation_gap_review_status"]
        == "observation_gap_review_blocks_selector_recommends_capacity_annotation"
    )
    assert (
        strategy_source["observation_gap_review_unknown_capacity_ratio"]
        == 0.7768014059753954
    )
    assert strategy_source["observation_gap_review_missing_expected_sources"] == [
        "broader_strategy_candidate",
        "plan_capsule_sequence_candidate",
    ]
    assert (
        strategy_source["capacity_annotation_v1_status"]
        == "candidate_move_capacity_annotation_partial_selector_blocked"
    )
    assert (
        strategy_source["capacity_annotation_v1_protected_annotation_recall"]
        == 0.03424657534246575
    )
    assert (
        strategy_source["capacity_label_manifest_status"]
        == "bounded_candidate_move_capacity_manifest_ready"
    )
    assert strategy_source["capacity_label_manifest_labels_run_by_this_artifact"] is False
    assert strategy_source["capacity_label_manifest_job_count"] == 12
    assert strategy_source["capacity_label_manifest_stage7_job_count"] == 0
    assert (
        strategy_source["capacity_labels_status"]
        == "bounded_candidate_move_capacity_labels_completed"
    )
    assert strategy_source["capacity_labels_label_count"] == 12
    assert strategy_source["capacity_labels_stage7_training_label_count"] == 0
    assert (
        strategy_source["capacity_annotation_v2_status"]
        == "candidate_move_capacity_annotation_improved_but_selector_blocked"
    )
    assert strategy_source["capacity_annotation_v2_annotated_candidate_move_count"] == 22
    assert (
        strategy_source["capacity_annotation_v2_protected_annotation_recall"]
        == 0.07534246575342465
    )
    assert strategy_source["capacity_annotation_v2_stage7_readiness_training_row_count"] == 0
    assert (
        strategy_source["label_blocker_status"]
        == "candidate_generation_label_coverage_underpowered_selector_blocked"
    )
    assert (
        strategy_source["label_blocker_more_blind_label_farming_not_recommended"]
        is True
    )
    assert (
        strategy_source["label_blocker_protected_annotation_recall"]
        == 0.07534246575342465
    )
    assert (
        strategy_source["quality_prioritization_review_status"]
        == "proposal_quality_prioritization_review_ready"
    )
    assert (
        strategy_source["quality_dataset_status"]
        == "candidate_proposal_quality_dataset_ready_for_probe"
    )
    assert strategy_source["quality_dataset_row_count"] == 569
    assert strategy_source["quality_dataset_quality_probe_row_count"] == 38
    assert strategy_source["quality_dataset_stage7_readiness_training_row_count"] == 0
    assert (
        strategy_source["quality_probe_status"]
        == "proposal_quality_axes_insufficient_for_selector_review"
    )
    assert strategy_source["quality_probe_best_probe"] == "candidate_move_frame_source"
    assert strategy_source["quality_probe_best_positive_recall"] == 0.6333333333333333
    assert strategy_source["quality_probe_best_negative_suppression"] == 0.625
    assert strategy_source["quality_probe_ready_for_selector_review"] is False
    assert (
        strategy_source["quality_decision_status"]
        == "candidate_proposal_quality_not_selector_ready"
    )
    assert strategy_source["quality_decision_more_blind_label_farming_allowed"] is False
    assert (
        strategy_source["quality_decision_recommended_next_step"]
        == "design_broader_strategy_sequence_candidate_sources"
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

    strategy_arbitration = payload["strategy_arbitration_gate"]
    assert strategy_arbitration["dataset_record_count"] == 33
    assert strategy_arbitration["dataset_proposal_count"] == 87
    assert strategy_arbitration["dataset_records_by_source_stage"] == {
        "stage4": 6,
        "stage5": 8,
        "stage6": 10,
        "stage7": 9,
    }
    assert strategy_arbitration["dataset_records_with_terminal_context"] == 33
    assert strategy_arbitration["probe_status"] == "missing_feature_first"
    assert strategy_arbitration["probe_stage7_record_count"] == 9
    assert strategy_arbitration["probe_raw_global_provider_hit_rate"] == (
        0.9285714285714286
    )
    assert strategy_arbitration["probe_normalized_provider_hit_rate"] == (
        0.9285714285714286
    )
    assert strategy_arbitration["probe_visible_heuristic_hit_rate"] == (
        0.07142857142857142
    )
    assert strategy_arbitration["probe_provider_local_rank1_coverage_rate"] == 1.0
    assert strategy_arbitration["probe_missing_terms_obvious"] is True
    assert (
        strategy_arbitration["probe_stage7_failures_cluster_by_phase_boundary"]
        is True
    )
    assert strategy_arbitration["decision_status"] == "missing_feature_first"
    assert strategy_arbitration["decision_next_class"] == (
        "non_causal_terminal_affordance_candidate_audit"
    )
    assert strategy_arbitration["decision_stop_after_next_class"] is True
    assert (
        "implement_runtime_arbiter"
        in strategy_arbitration["decision_forbidden_next_steps"]
    )
    assert "train_stage8" in strategy_arbitration["decision_forbidden_next_steps"]
    assert "promote_stage7" in strategy_arbitration["decision_forbidden_next_steps"]
    assert "use_runtime_dtm_or_tablebase" in (
        strategy_arbitration["decision_forbidden_next_steps"]
    )
    assert strategy_arbitration["missing_feature_candidate_count"] == 6
    assert strategy_arbitration["missing_feature_challenge_family_count"] == 6
    assert (
        strategy_arbitration["missing_feature_source_decision_status"]
        == "missing_feature_first"
    )
    assert strategy_arbitration["missing_feature_recommended_next_step"] == (
        "stop_for_architecture_review_before_any_terminal_or_affordance_runtime_sandbox"
    )
    assert "add_causal_terminal" in (
        strategy_arbitration["missing_feature_blocked_next_steps"]
    )
    assert strategy_arbitration["runtime_work_allowed"] is False
    assert strategy_arbitration["runtime_arbiter_allowed"] is False
    assert strategy_arbitration["runtime_dtm_or_tablebase_lookup"] is False
    assert strategy_arbitration["selector_training_allowed"] is False
    assert strategy_arbitration["stage7_promotion_allowed"] is False
    assert strategy_arbitration["stage8_training_allowed"] is False

    strategy_monitor = payload["strategy_monitor_maturity_gate"]
    assert strategy_monitor["plan_do_not_implement_as_causal_affordances"] is True
    assert (
        "implement_runtime_arbiter" in strategy_monitor["plan_blocked_next_steps"]
    )
    assert strategy_monitor["records_dataset_record_count"] == 33
    assert strategy_monitor["records_monitor_definition_count"] == 5
    assert strategy_monitor["records_monitor_record_count"] == 108
    assert strategy_monitor["records_by_monitor_type"] == {
        "OwnerExitMonitor": 25,
        "PhaseBoundaryMonitor": 52,
        "PlanSelectionNeededMonitor": 9,
        "RepairNeededMonitor": 22,
    }
    assert strategy_monitor["records_rejected_definition_count"] == 1
    assert strategy_monitor["companion_terms_causal_terms_authorized"] is False
    assert strategy_monitor["companion_terms_runtime_arbiter_authorized"] is False
    assert strategy_monitor["companion_terms_stage7_repair_authorized"] is False
    assert strategy_monitor["companion_audit_v0_all_terms_available"] is False
    assert strategy_monitor["visible_terms_record_count"] == 33
    assert strategy_monitor["visible_terms_term_names"] == [
        "king_support_improves_after_move",
        "cut_or_fence_restored_after_move",
        "safe_repair_move_exists",
        "box_area_no_longer_decision_relevant",
        "post_plan_stagnation",
        "local_provider_competition_failed",
    ]
    assert strategy_monitor["companion_audit_v1_all_terms_available"] is False
    assert strategy_monitor["companion_audit_v1_visible_terms_applied"] is True
    assert strategy_monitor["companion_audit_v1_visible_term_count"] == 6
    assert strategy_monitor["companion_audit_v1_still_missing_term_count"] == 11
    assert strategy_monitor["maturity_term_count"] == 6
    assert strategy_monitor["maturity_causal_ready_terms"] == []
    assert strategy_monitor["maturity_strongest_internal_terminal_candidates"] == [
        "post_plan_stagnation",
        "local_provider_competition_failed",
    ]
    assert strategy_monitor["maturity_recommended_next_step"] == (
        "broader_evidence_collection_or_internal_monitor_design_review"
    )
    assert "runtime_terminals" in strategy_monitor["maturity_blocked_next_steps"]
    assert strategy_monitor["runtime_work_allowed"] is False
    assert strategy_monitor["runtime_terminals_allowed"] is False
    assert strategy_monitor["runtime_arbiter_allowed"] is False
    assert strategy_monitor["monitor_to_provider_routing_allowed"] is False
    assert strategy_monitor["runtime_dtm_or_tablebase_lookup"] is False
    assert strategy_monitor["selector_training_allowed"] is False
    assert strategy_monitor["stage7_promotion_allowed"] is False
    assert strategy_monitor["stage8_training_allowed"] is False

    internal_terminal = payload["internal_terminal_readiness_gate"]
    assert internal_terminal["feature_candidate_all_non_causal"] is True
    assert internal_terminal["feature_candidate_count"] == 6
    assert internal_terminal["feature_candidate_sandbox_ready_candidate_ids"] == []
    assert internal_terminal["feature_candidate_recommended_next_step"] == (
        "architecture_review_or_refine_companion_terms_before_any_runtime_sandbox"
    )
    assert internal_terminal["candidate_spec_count"] == 4
    assert internal_terminal["candidate_terminal_ids"] == [
        "terminal.krk.local_provider_competition_failed",
        "terminal.krk.post_plan_stagnation",
        "terminal.krk.box_shrink_owner_exit_pressure",
        "terminal.krk.repair_needed_monitor",
    ]
    assert internal_terminal["candidate_maturity_statuses"] == [
        "internal_terminal_candidate",
        "internal_terminal_candidate",
        "needs_more_evidence",
        "monitoring_only",
    ]
    assert "runtime_terminals" in internal_terminal["candidate_blocked_next_steps"]
    assert internal_terminal["validation_terminal_count"] == 4
    assert internal_terminal["validation_record_count"] == 30
    assert internal_terminal["validation_causal_ready_terminals"] == []
    assert internal_terminal["validation_strongest_internal_terminal_candidates"] == [
        "terminal.krk.local_provider_competition_failed",
        "terminal.krk.post_plan_stagnation",
    ]
    assert internal_terminal["validation_all_causal_use_blocked"] is True
    assert internal_terminal["evidence_terminal_count"] == 4
    assert internal_terminal["evidence_combined_record_count"] == 24
    assert internal_terminal["evidence_causal_ready_terminals"] == []
    assert internal_terminal["evidence_monitoring_only_candidates"] == [
        "terminal.krk.box_shrink_owner_exit_pressure",
        "terminal.krk.repair_needed_monitor",
    ]
    assert internal_terminal["evidence_stage7_only_candidates"] == [
        "terminal.krk.local_provider_competition_failed",
        "terminal.krk.post_plan_stagnation",
        "terminal.krk.box_shrink_owner_exit_pressure",
    ]
    assert internal_terminal["evidence_all_causal_ready_false"] is True
    assert internal_terminal["evidence_recommended_next_step"] == (
        "internal_terminal_design_review_before_any_runtime_work"
    )
    assert internal_terminal["design_review_causal_ready_terminals"] == []
    assert internal_terminal["design_review_all_causal_ready_false"] is True
    assert internal_terminal["design_review_recommended_next_step"] == (
        "broader_replay_free_monitor_evidence_collection_or_review"
    )
    assert "runtime_terminals" in internal_terminal["design_review_blocked_next_steps"]
    assert internal_terminal["runtime_work_allowed"] is False
    assert internal_terminal["runtime_terminals_allowed"] is False
    assert internal_terminal["causal_affordances_allowed"] is False
    assert internal_terminal["runtime_arbiter_allowed"] is False
    assert internal_terminal["monitor_to_provider_routing_allowed"] is False
    assert internal_terminal["runtime_dtm_or_tablebase_lookup"] is False
    assert internal_terminal["selector_training_allowed"] is False
    assert internal_terminal["stage7_promotion_allowed"] is False
    assert internal_terminal["stage8_training_allowed"] is False

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
        cross_stage_scope["cross_stage_label_probe_status"]
        == "candidate_generation_refresh_supported_selector_blocked"
    )
    assert (
        cross_stage_scope["cross_stage_label_probe_best_policy"]
        == "stage_family_pure_positive_with_support_2"
    )
    assert cross_stage_scope["cross_stage_label_probe_positive_recall"] == (
        0.7692307692307693
    )
    assert cross_stage_scope["cross_stage_label_probe_negative_suppression"] == 1.0
    assert cross_stage_scope["cross_stage_label_probe_capacity_row_count"] == 36
    assert cross_stage_scope["cross_stage_label_probe_source_stage_counts"] == {
        "stage4": 11,
        "stage5": 16,
        "stage6": 9,
    }
    assert cross_stage_scope["cross_stage_label_probe_capacity_label_counts"] == {
        "negative_capacity": 10,
        "positive_capacity": 26,
    }
    assert cross_stage_scope["cross_stage_label_probe_guardrails_allowed"] is False
    assert cross_stage_scope["cross_stage_label_probe_selector_allowed"] is False
    assert cross_stage_scope["cross_stage_label_probe_promotion_allowed"] is False
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
        selector["independent_validation_manifest_status"]
        == "selector_objective_independent_validation_manifest_ready"
    )
    assert selector["independent_validation_manifest_labels_allowed_by_review"] is True
    assert selector["independent_validation_manifest_job_count"] == 10
    assert selector["independent_validation_manifest_job_count_by_stage"] == {
        "stage4": 7,
        "stage6": 3,
    }
    assert selector["independent_validation_manifest_all_bindings_valid"] is True
    assert selector["independent_validation_manifest_excluded_stages"] == [
        "stage7",
        "stage8",
    ]
    assert selector["independent_validation_manifest_stage7_training_rows"] == 0
    assert selector["independent_validation_manifest_job_labels_generated_count"] == 0
    assert (
        selector["independent_validation_labels_status"]
        == "selector_objective_independent_validation_labels_collected"
    )
    assert selector["independent_validation_labels_label_count"] == 10
    assert selector["independent_validation_labels_selected_result_counts"] == {
        "mate": 10
    }
    assert selector["independent_validation_labels_result_counts_by_stage"] == {
        "stage4:mate": 7,
        "stage6:mate": 3,
    }
    assert selector["independent_validation_labels_selector_training_row_count"] == 0
    assert selector["independent_validation_labels_stage7_training_row_count"] == 0
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
        candidate_generation["training_refresh_design_v2_status"]
        == "candidate_generation_training_refresh_design_ready"
    )
    assert (
        candidate_generation["training_refresh_design_v2_next_step"]
        == "candidate_generation_training_refresh_benchmark_or_cross_stage_capacity_review"
    )
    assert (
        candidate_generation[
            "training_refresh_design_v2_runtime_candidate_generator_refresh_allowed"
        ]
        is False
    )
    assert candidate_generation["training_refresh_design_v2_selector_allowed"] is False
    assert candidate_generation["training_refresh_design_v2_guardrails_allowed"] is False
    assert candidate_generation["training_refresh_design_v2_promotion_allowed"] is False
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

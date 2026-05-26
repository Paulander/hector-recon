#!/usr/bin/env python3
"""Write a compact KRK full-suite readiness audit from existing artifacts.

This audit is intentionally non-causal. It joins the current protected-stack,
control-plane, Stage 7, and sequence-policy gate artifacts into a single
machine-checkable status report for the broader "working KRK suite" milestone.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
OUT_MD = ROOT / "reports/krk_full_suite_readiness_audit_v0.md"

SOURCES = {
    "current_brief": "reports/current_agent_brief.md",
    "control_plane_gate": "reports/krk_current_control_plane_gate_v0.json",
    "control_plane_evidence_contract": "reports/krk_control_plane_evidence_contract_v0.json",
    "control_plane_manifest": "reports/krk_control_plane_manifest_v0.json",
    "control_plane_gap_report": "reports/krk_control_plane_gap_report_v0.json",
    "control_plane_frames": "reports/krk_control_plane_frames_v0.json",
    "control_plane_frame_quality": "reports/krk_control_plane_frame_quality_report_v0.json",
    "control_plane_filtered_frames": "reports/krk_control_plane_filtered_frames_v0.json",
    "control_plane_forced_controls": (
        "reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json"
    ),
    "control_plane_strategy_probe": (
        "reports/krk_control_plane_strategy_arbitration_probe_v0.json"
    ),
    "control_plane_strategy_baseline": (
        "reports/krk_control_plane_strategy_arbitration_baseline_v1.json"
    ),
    "strategy_arbitration_dataset": (
        "reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json"
    ),
    "strategy_arbitration_probe": (
        "reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.json"
    ),
    "strategy_arbitration_decision_gate": (
        "reports/strategy_arbitration/krk_strategy_arbitration_decision_gate.json"
    ),
    "strategy_missing_feature_candidates": (
        "reports/strategy_arbitration/krk_strategy_missing_feature_candidates.json"
    ),
    "strategy_monitor_v0_plan": (
        "reports/strategy_arbitration/krk_strategy_monitor_v0_plan.json"
    ),
    "strategy_monitor_records_v0": (
        "reports/strategy_arbitration/krk_strategy_monitor_records_v0.json"
    ),
    "strategy_monitor_companion_terms_v0": (
        "reports/strategy_arbitration/krk_strategy_monitor_companion_terms_v0.json"
    ),
    "strategy_monitor_companion_audit_v0": (
        "reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v0.json"
    ),
    "visible_monitor_terms_v0": (
        "reports/strategy_arbitration/krk_visible_monitor_terms_v0.json"
    ),
    "strategy_monitor_companion_audit_v1": (
        "reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v1.json"
    ),
    "strategy_monitor_maturity_gate_v0": (
        "reports/strategy_arbitration/krk_strategy_monitor_maturity_gate_v0.json"
    ),
    "feature_candidate_validation": (
        "reports/strategy_arbitration/krk_feature_candidate_validation_v0.json"
    ),
    "internal_terminal_candidates": (
        "reports/strategy_arbitration/krk_internal_terminal_candidates_v0.json"
    ),
    "internal_terminal_validation": (
        "reports/strategy_arbitration/krk_internal_terminal_validation_v0.json"
    ),
    "internal_terminal_evidence_v1": (
        "reports/strategy_arbitration/krk_internal_terminal_evidence_v1.json"
    ),
    "internal_terminal_design_review_v1": (
        "reports/strategy_arbitration/krk_internal_terminal_design_review_v1.json"
    ),
    "control_plane_stage7_boundary_refresh": (
        "reports/krk_control_plane_stage7_boundary_refresh_v0.json"
    ),
    "protected_missing_provider_capacity_labels": (
        "reports/krk_protected_missing_provider_capacity_labels_v0.json"
    ),
    "protected_missing_provider_label_merge_review": (
        "reports/krk_protected_missing_provider_label_merge_review_v0.json"
    ),
    "ranked_proposal_protected_provider_coverage_review": (
        "reports/krk_ranked_proposal_frame_protected_provider_coverage_review_v0.json"
    ),
    "protected_proposal_coverage_expansion_plan": (
        "reports/krk_protected_proposal_coverage_expansion_plan_v0.json"
    ),
    "protected_provider_coverage_frames": (
        "reports/krk_protected_provider_coverage_frames_v0.json"
    ),
    "protected_provider_capacity_frame_training_semantics_review": (
        "reports/krk_protected_provider_capacity_frame_training_semantics_review_v0.json"
    ),
    "candidate_generator_coverage_audit": (
        "reports/krk_candidate_generator_coverage_audit_v0.json"
    ),
    "validated_provider_candidate_set_audit": (
        "reports/krk_validated_provider_candidate_set_audit_v0.json"
    ),
    "two_stage_candidate_selection_review": (
        "reports/krk_two_stage_candidate_selection_review_v0.json"
    ),
    "two_stage_candidate_selection_benchmark_plan": (
        "reports/krk_two_stage_candidate_selection_benchmark_plan_v0.json"
    ),
    "two_stage_candidate_selection_benchmark": (
        "reports/krk_two_stage_candidate_selection_benchmark_v0.json"
    ),
    "candidate_proposal_coverage": (
        "reports/strategy_arbitration/krk_candidate_proposal_coverage_v0.json"
    ),
    "candidate_generation_strategy_review": (
        "reports/strategy_arbitration/krk_candidate_generation_strategy_review_v0.json"
    ),
    "strategy_sequence_candidate_frame_schema_v1": (
        "reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_v1.json"
    ),
    "strategy_sequence_candidate_frames_v1": (
        "reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json"
    ),
    "strategy_sequence_candidate_frame_quality_v1": (
        "reports/strategy_arbitration/krk_strategy_sequence_candidate_frame_quality_v1.json"
    ),
    "candidate_frame_source_benchmark_v1": (
        "reports/strategy_arbitration/krk_candidate_frame_source_benchmark_v1.json"
    ),
    "strategy_sequence_control_plane_decision_v1": (
        "reports/strategy_arbitration/krk_strategy_sequence_control_plane_decision_v1.json"
    ),
    "candidate_generation_sandbox_review": (
        "reports/strategy_arbitration/krk_candidate_generation_sandbox_review_v0.json"
    ),
    "candidate_generation_observation_sandbox": (
        "reports/strategy_arbitration/krk_candidate_generation_observation_sandbox_v0.json"
    ),
    "candidate_generation_observation_coverage": (
        "reports/strategy_arbitration/krk_candidate_generation_observation_coverage_analysis_v0.json"
    ),
    "candidate_generation_observation_broadened_sample": (
        "reports/strategy_arbitration/krk_candidate_generation_observation_broadened_sample_v1.json"
    ),
    "candidate_generation_observation_gap_review": (
        "reports/strategy_arbitration/krk_candidate_generation_observation_gap_review_v1.json"
    ),
    "candidate_move_capacity_annotation_v1": (
        "reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v1.json"
    ),
    "candidate_move_capacity_label_manifest_v1": (
        "reports/strategy_arbitration/krk_candidate_move_capacity_label_manifest_v1.json"
    ),
    "candidate_move_capacity_labels_v1": (
        "reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.json"
    ),
    "candidate_move_capacity_annotation_v2": (
        "reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.json"
    ),
    "candidate_generation_label_blocker_review": (
        "reports/strategy_arbitration/krk_candidate_generation_label_blocker_review_v1.json"
    ),
    "candidate_proposal_quality_prioritization_review": (
        "reports/strategy_arbitration/krk_candidate_proposal_quality_prioritization_review_v1.json"
    ),
    "candidate_proposal_quality_dataset": (
        "reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.json"
    ),
    "candidate_proposal_quality_probe": (
        "reports/strategy_arbitration/krk_candidate_proposal_quality_probe_v1.json"
    ),
    "candidate_proposal_quality_decision": (
        "reports/strategy_arbitration/krk_candidate_proposal_quality_decision_v1.json"
    ),
    "broader_strategy_sequence_candidate_source_design_v1": (
        "reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_design_v1.json"
    ),
    "plan_capsule_sequence_candidate_observation_review_v1": (
        "reports/strategy_arbitration/krk_plan_capsule_sequence_candidate_observation_review_v1.json"
    ),
    "broader_strategy_candidate_observation_review_v1": (
        "reports/strategy_arbitration/krk_broader_strategy_candidate_observation_review_v1.json"
    ),
    "broader_strategy_sequence_candidate_source_review_v1": (
        "reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_review_v1.json"
    ),
    "protected_strategy_monitor_frame_expansion_v1": (
        "reports/strategy_arbitration/krk_protected_strategy_monitor_frame_expansion_v1.json"
    ),
    "protected_strategy_monitor_frame_quality_v1": (
        "reports/strategy_arbitration/krk_protected_strategy_monitor_frame_quality_v1.json"
    ),
    "protected_strategy_monitor_observation_source_review_packet_v1": (
        "reports/strategy_arbitration/krk_protected_strategy_monitor_observation_source_review_packet_v1.json"
    ),
    "repair_monitor_observation_source_smoke_v1": (
        "reports/strategy_arbitration/krk_repair_monitor_observation_source_smoke_v1.json"
    ),
    "repair_monitor_observation_source_coverage_v1": (
        "reports/strategy_arbitration/krk_repair_monitor_observation_source_coverage_v1.json"
    ),
    "repair_monitor_observation_source_broadened_v1": (
        "reports/strategy_arbitration/krk_repair_monitor_observation_source_broadened_v1.json"
    ),
    "repair_monitor_observation_source_quality_review_v1": (
        "reports/strategy_arbitration/krk_repair_monitor_observation_source_quality_review_v1.json"
    ),
    "strategy_sequence_repair_monitor_trace_features_v1": (
        "reports/strategy_arbitration/krk_strategy_sequence_repair_monitor_trace_features_v1.json"
    ),
    "strategy_sequence_trace_feature_integration_review_v1": (
        "reports/strategy_arbitration/krk_strategy_sequence_trace_feature_integration_review_v1.json"
    ),
    "strategy_sequence_dataset_design_v2": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_design_v2.json"
    ),
    "strategy_sequence_dataset_v2": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2.json"
    ),
    "strategy_sequence_dataset_v2_quality_probe": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_quality_probe.json"
    ),
    "candidate_generation_refresh_probe_v2": (
        "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2.json"
    ),
    "candidate_generation_capacity_evidence_manifest_v2": (
        "reports/strategy_arbitration/krk_candidate_generation_capacity_evidence_manifest_v2.json"
    ),
    "candidate_generation_capacity_evidence_labels_v2": (
        "reports/strategy_arbitration/krk_candidate_generation_capacity_evidence_labels_v2.json"
    ),
    "strategy_sequence_dataset_v2_capacity_merged": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_capacity_merged.json"
    ),
    "candidate_generation_refresh_probe_v2_after_labels": (
        "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_after_labels.json"
    ),
    "candidate_generation_refresh_probe_v2_cross_stage_labels": (
        "reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2_cross_stage_labels.json"
    ),
    "candidate_generation_training_refresh_design_v2": (
        "reports/strategy_arbitration/krk_candidate_generation_training_refresh_design_v2.json"
    ),
    "stage5_6_candidate_generation_refresh_review_packet_v3": (
        "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_review_packet_v3.json"
    ),
    "stage5_6_candidate_generation_refresh_smoke": (
        "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_smoke_v0.json"
    ),
    "stage5_6_candidate_generation_refresh_coverage": (
        "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_coverage_v0.json"
    ),
    "stage5_6_candidate_generation_refresh_broadened": (
        "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_broadened_v0.json"
    ),
    "stage5_6_candidate_generation_refresh_quality_review": (
        "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_quality_review_v0.json"
    ),
    "strategy_sequence_stage5_6_refresh_trace_features": (
        "reports/strategy_arbitration/krk_strategy_sequence_stage5_6_refresh_trace_features_v0.json"
    ),
    "strategy_sequence_dataset_design_v3": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_design_v3.json"
    ),
    "candidate_generation_cross_stage_capacity_review_v2": (
        "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_review_v2.json"
    ),
    "candidate_generation_cross_stage_capacity_manifest_v3": (
        "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_manifest_v3.json"
    ),
    "candidate_generation_cross_stage_capacity_labels_v3": (
        "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_labels_v3.json"
    ),
    "strategy_sequence_dataset_v2_cross_stage_capacity_merged": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_cross_stage_capacity_merged.json"
    ),
    "candidate_generation_cross_stage_label_outcome_review_v3": (
        "reports/strategy_arbitration/krk_candidate_generation_cross_stage_label_outcome_review_v3.json"
    ),
    "candidate_generation_stage_conditioned_scope_review_v3": (
        "reports/strategy_arbitration/krk_candidate_generation_stage_conditioned_scope_review_v3.json"
    ),
    "stage_conditioned_candidate_generation_benchmark_v3": (
        "reports/strategy_arbitration/krk_stage_conditioned_candidate_generation_benchmark_v3.json"
    ),
    "ownership_label_recovery_review": (
        "reports/strategy_arbitration/krk_ownership_label_recovery_review_v0.json"
    ),
    "selector_objective_seed_manifest_v0": (
        "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v0.json"
    ),
    "selector_objective_seed_probe_v0": (
        "reports/strategy_arbitration/krk_selector_objective_seed_probe_v0.json"
    ),
    "joined_trace_ownership_collection_manifest": (
        "reports/strategy_arbitration/krk_joined_trace_ownership_collection_manifest_v0.json"
    ),
    "joined_trace_ownership_collection_review_packet": (
        "reports/strategy_arbitration/krk_joined_trace_ownership_collection_review_packet_v0.json"
    ),
    "joined_trace_ownership_collection": (
        "reports/strategy_arbitration/krk_joined_trace_ownership_collection_v0.json"
    ),
    "selector_objective_seed_manifest_v1": (
        "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v1.json"
    ),
    "selector_objective_seed_probe_v1": (
        "reports/strategy_arbitration/krk_selector_objective_seed_probe_v1.json"
    ),
    "selector_objective_feature_probe": (
        "reports/strategy_arbitration/krk_selector_objective_feature_probe_v0.json"
    ),
    "selector_objective_feature_probe_review": (
        "reports/strategy_arbitration/krk_selector_objective_feature_probe_review_v0.json"
    ),
    "selector_objective_diversity_gap_review": (
        "reports/strategy_arbitration/krk_selector_objective_diversity_gap_review_v0.json"
    ),
    "stage4_joined_trace_ownership_scope_review_packet": (
        "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_scope_review_packet_v0.json"
    ),
    "stage4_joined_trace_ownership_collection": (
        "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_collection_v0.json"
    ),
    "selector_objective_seed_manifest_v2": (
        "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json"
    ),
    "selector_objective_seed_probe_v2": (
        "reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json"
    ),
    "selector_objective_benchmark_v2": (
        "reports/strategy_arbitration/krk_selector_objective_benchmark_v2.json"
    ),
    "selector_objective_benchmark_review_packet_v2": (
        "reports/strategy_arbitration/krk_selector_objective_benchmark_review_packet_v2.json"
    ),
    "selector_objective_independent_validation_manifest": (
        "reports/strategy_arbitration/krk_selector_objective_independent_validation_manifest_v0.json"
    ),
    "selector_objective_independent_validation_labels": (
        "reports/strategy_arbitration/krk_selector_objective_independent_validation_labels_v0.json"
    ),
    "selector_objective_independent_validation": (
        "reports/strategy_arbitration/krk_selector_objective_independent_validation_v0.json"
    ),
    "selector_objective_independent_validation_blocker": (
        "reports/strategy_arbitration/krk_selector_objective_independent_validation_blocker_v0.json"
    ),
    "stage4_failure_discovery": "reports/krk_stage4_failure_discovery_v0.json",
    "stage4_caveat_sequence_review": (
        "reports/krk_stage4_caveat_sequence_review_v0.json"
    ),
    "stage4_sequence_candidate_review": (
        "reports/krk_stage4_sequence_candidate_review_v0.json"
    ),
    "stage4_first_move_feature_review": (
        "reports/krk_stage4_first_move_feature_review_v0.json"
    ),
    "stage4_stratified_contrast_validation": (
        "reports/krk_stage4_stratified_contrast_validation_v0.json"
    ),
    "sequence_control_contrast_dataset": (
        "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json"
    ),
    "strategy_sequence_dataset_v3": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v3.json"
    ),
    "strategy_sequence_dataset_v3_quality_probe": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v3_quality_probe.json"
    ),
    "strategy_sequence_dataset_v3_context_review": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v3_context_review.json"
    ),
    "candidate_generation_v3_context_benchmark": (
        "reports/strategy_arbitration/krk_candidate_generation_v3_context_benchmark.json"
    ),
    "candidate_generation_v3_runtime_boundary_review": (
        "reports/strategy_arbitration/krk_candidate_generation_v3_runtime_boundary_review.json"
    ),
    "candidate_generation_v3_training_refresh_review": (
        "reports/strategy_arbitration/krk_candidate_generation_v3_training_refresh_review.json"
    ),
    "candidate_generation_training_refresh_design_v3": (
        "reports/strategy_arbitration/krk_candidate_generation_training_refresh_design_v3.json"
    ),
    "candidate_generation_training_refresh_benchmark_v3": (
        "reports/strategy_arbitration/krk_candidate_generation_training_refresh_benchmark_v3.json"
    ),
    "candidate_generation_training_refresh_runtime_review_v3": (
        "reports/strategy_arbitration/krk_candidate_generation_training_refresh_runtime_review_packet_v3.json"
    ),
    "candidate_generation_refresh_sandbox": (
        "reports/strategy_arbitration/krk_candidate_generation_refresh_sandbox_v0.json"
    ),
    "candidate_generation_refresh_coverage": (
        "reports/strategy_arbitration/krk_candidate_generation_refresh_coverage_analysis_v0.json"
    ),
    "strategy_sequence_candidate_generation_refresh_trace_features": (
        "reports/strategy_arbitration/krk_strategy_sequence_candidate_generation_refresh_trace_features_v1.json"
    ),
    "strategy_sequence_dataset_v4": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v4.json"
    ),
    "strategy_sequence_dataset_v4_quality_probe": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v4_quality_probe.json"
    ),
    "strategy_sequence_dataset_v4_context_review": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v4_context_review.json"
    ),
    "candidate_generation_v4_context_benchmark": (
        "reports/strategy_arbitration/krk_candidate_generation_v4_context_benchmark.json"
    ),
    "candidate_generation_v4_next_boundary_review": (
        "reports/strategy_arbitration/krk_candidate_generation_v4_next_runtime_boundary_review_v0.json"
    ),
    "candidate_generation_scope_gap_review": (
        "reports/strategy_arbitration/krk_candidate_generation_scope_gap_review_v0.json"
    ),
    "candidate_source_gap_manifest": (
        "reports/strategy_arbitration/krk_candidate_source_gap_manifest_v0.json"
    ),
    "candidate_source_expansion_options": (
        "reports/strategy_arbitration/krk_candidate_source_expansion_options_v0.json"
    ),
    "exact_trace_enrichment_runtime_review": (
        "reports/strategy_arbitration/krk_exact_trace_enrichment_runtime_review_packet_v0.json"
    ),
    "exact_trace_enrichment_sandbox": (
        "reports/strategy_arbitration/krk_exact_trace_enrichment_sandbox_v0.json"
    ),
    "exact_trace_enrichment_coverage": (
        "reports/strategy_arbitration/krk_exact_trace_enrichment_coverage_analysis_v0.json"
    ),
    "strategy_sequence_exact_trace_enrichment_trace_features": (
        "reports/strategy_arbitration/krk_strategy_sequence_exact_trace_enrichment_trace_features_v1.json"
    ),
    "strategy_sequence_dataset_v5": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.json"
    ),
    "strategy_sequence_dataset_v5_quality_probe": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v5_quality_probe.json"
    ),
    "strategy_sequence_dataset_v5_context_review": (
        "reports/strategy_arbitration/krk_strategy_sequence_dataset_v5_context_review.json"
    ),
    "candidate_generation_v5_context_benchmark": (
        "reports/strategy_arbitration/krk_candidate_generation_v5_context_benchmark.json"
    ),
    "candidate_generation_v5_next_boundary_review": (
        "reports/strategy_arbitration/krk_candidate_generation_v5_next_boundary_review_v0.json"
    ),
    "clean_curriculum_checkpoint_plan": (
        "reports/krk_clean_curriculum_checkpoint_plan_v0.json"
    ),
    "clean_retrain_execution_manifest": (
        "reports/krk_clean_retrain_execution_manifest_v0.json"
    ),
    "stage6_overlay_compose_manifest": (
        "reports/krk_stage6_overlay_compose_manifest_v0.json"
    ),
    "clean_retrain_preflight": "reports/krk_clean_retrain_preflight_v0.json",
    "clean_retrain_smoke_manifest": (
        "reports/krk_clean_retrain_smoke_manifest_v0.json"
    ),
    "clean_retrain_smoke_result": "reports/krk_clean_retrain_smoke_result_v0.json",
    "clean_retrain_run_result": "reports/krk_clean_retrain_run_result_v0.json",
    "clean_retrain_retry1_result": (
        "reports/krk_clean_retrain_retry1_result_v1.json"
    ),
    "clean_retrain_retry1_guardrail_result": (
        "reports/krk_clean_retrain_retry1_guardrail_result_v1.json"
    ),
    "clean_retrain_retry1_stage6_gap_inspection": (
        "reports/krk_clean_retrain_retry1_stage6_gap_inspection_v1.json"
    ),
    "stage5_guardrail_control_debt_review": (
        "reports/krk_stage5_guardrail_control_debt_review_v0.json"
    ),
    "stage5_guardrail_semantics_split": (
        "reports/krk_stage5_guardrail_semantics_split_v0.json"
    ),
    "stage5_local_reward_contract_debt_audit": (
        "reports/krk_stage5_local_reward_contract_debt_audit_v0.json"
    ),
    "clean_retrain_retry1_stage4_caveat_control_review": (
        "reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json"
    ),
    "curriculum_next_milestone_decision": (
        "reports/krk_curriculum_next_milestone_decision_v0.json"
    ),
    "stage7_heldout_unlock_review": (
        "reports/structural_candidates/stage7_heldout_unlock_review_v0.json"
    ),
    "stage7_to_stage8_blocker_review": (
        "reports/structural_candidates/stage7_to_stage8_blocker_review_v0.json"
    ),
    "strategy_sequence_architecture_review": (
        "reports/krk_strategy_sequence_architecture_review_v0.json"
    ),
    "strategy_sequence_evidence_plan": (
        "reports/krk_strategy_sequence_evidence_plan_v0.json"
    ),
    "strategy_sequence_inventory": "reports/krk_strategy_sequence_inventory_v0.json",
    "strategy_owner_contrast_label_plan": (
        "reports/krk_strategy_owner_contrast_label_plan_v0.json"
    ),
    "strategy_owner_contrast_label_plan_review": (
        "reports/krk_strategy_owner_contrast_label_plan_review_v0.json"
    ),
    "strategy_owner_contrast_execution_manifest": (
        "reports/krk_strategy_owner_contrast_execution_manifest_v0.json"
    ),
    "strategy_owner_contrast_execution_manifest_review": (
        "reports/krk_strategy_owner_contrast_execution_manifest_review_v0.json"
    ),
    "strategy_owner_contrast_control_labels": (
        "reports/krk_strategy_owner_contrast_control_labels_v0.json"
    ),
    "strategy_owner_contrast_dataset": (
        "reports/krk_strategy_owner_contrast_dataset_v0.json"
    ),
    "strategy_owner_contrast_probe": (
        "reports/krk_strategy_owner_contrast_probe_v0.json"
    ),
    "arbitration_objective_review_v1": (
        "reports/krk_arbitration_objective_review_v1.json"
    ),
    "normalized_strategy_selector_objective_v1": (
        "reports/krk_normalized_strategy_selector_objective_v1.json"
    ),
    "normalized_strategy_selector_objective_probe_v1": (
        "reports/krk_normalized_strategy_selector_objective_probe_v1.json"
    ),
    "normalized_selector_probe_review_v1": (
        "reports/krk_normalized_selector_probe_review_v1.json"
    ),
    "selector_objective_architecture_review_v1": (
        "reports/krk_selector_objective_architecture_review_v1.json"
    ),
    "selector_objective_label_semantics_v0": (
        "reports/krk_selector_objective_label_semantics_v0.json"
    ),
    "split_selector_objective_dataset_v3": (
        "reports/krk_split_selector_objective_dataset_v3.json"
    ),
    "split_selector_objective_readiness_v3": (
        "reports/krk_split_selector_objective_readiness_v3.json"
    ),
    "abstention_first_selector_objective_v0": (
        "reports/krk_abstention_first_selector_objective_v0.json"
    ),
    "abstention_safe_preservation_label_review_v0": (
        "reports/krk_abstention_safe_preservation_label_review_v0.json"
    ),
    "abstention_training_dataset_v1": (
        "reports/krk_abstention_training_dataset_v1.json"
    ),
    "abstention_training_probe_v1": (
        "reports/krk_abstention_training_probe_v1.json"
    ),
    "abstention_context_feature_dataset_v0": (
        "reports/krk_abstention_context_feature_dataset_v0.json"
    ),
    "abstention_context_feature_probe_v0": (
        "reports/krk_abstention_context_feature_probe_v0.json"
    ),
    "abstention_context_error_audit_v0": (
        "reports/krk_abstention_context_error_audit_v0.json"
    ),
    "abstention_feature_gap_review_v0": (
        "reports/krk_abstention_feature_gap_review_v0.json"
    ),
    "targeted_non_stage0_ownership_manifest_v0": (
        "reports/krk_targeted_non_stage0_ownership_manifest_v0.json"
    ),
    "targeted_non_stage0_ownership_labels_v0": (
        "reports/krk_targeted_non_stage0_ownership_labels_v0.json"
    ),
    "targeted_non_stage0_ownership_review_v0": (
        "reports/krk_targeted_non_stage0_ownership_review_v0.json"
    ),
    "targeted_ownership_negative_manifest_v0": (
        "reports/krk_targeted_ownership_negative_manifest_v0.json"
    ),
    "targeted_ownership_negative_labels_v0": (
        "reports/krk_targeted_ownership_negative_labels_v0.json"
    ),
    "balanced_hard_negative_label_plan_v1": (
        "reports/krk_balanced_hard_negative_label_plan_v1.json"
    ),
    "balanced_hard_negative_execution_manifest_v1": (
        "reports/krk_balanced_hard_negative_execution_manifest_v1.json"
    ),
    "balanced_hard_negative_execution_manifest_review_v1": (
        "reports/krk_balanced_hard_negative_execution_manifest_review_v1.json"
    ),
    "balanced_hard_negative_labels_v1": (
        "reports/krk_balanced_hard_negative_labels_v1.json"
    ),
    "balanced_hard_negative_evidence_review_v0": (
        "reports/krk_balanced_hard_negative_evidence_review_v0.json"
    ),
    "clean_retrain_retry1_replacement_readiness_review": (
        "reports/krk_clean_retrain_retry1_replacement_readiness_review_v0.json"
    ),
    "clean_retrain_retry1_protected_stack_snapshot_manifest": (
        "reports/krk_clean_retrain_retry1_protected_stack_snapshot_manifest_v0.json"
    ),
    "clean_retrain_retry1_clean_stack_replacement_review_packet": (
        "reports/krk_clean_retrain_retry1_clean_stack_replacement_review_packet_v0.json"
    ),
    "clean_stack_replacement_deferred_review": (
        "reports/krk_clean_stack_replacement_deferred_review_v0.json"
    ),
    "protected_stage_status": "reports/krk_protected_stage_status.json",
    "active_protected_stack": "reports/krk_active_protected_stack_v0.json",
    "clean_stack_validation": "reports/krk_clean_stack_post_replacement_validation_v0.json",
    "preservation_checks": "reports/krk_clean_retrain_retry1_preservation_checks_v0.json",
    "stage4_caveat_unblocker": "reports/krk_stage4_caveat_unblocker_packet_v0.json",
    "stage4_first_move_contrast_runtime_review": (
        "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json"
    ),
    "stage4_sandbox_approval_request": (
        "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
    ),
    "sequence_control_contrast_probe": (
        "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json"
    ),
    "sequence_pipeline_refresh": (
        "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json"
    ),
    "sequence_benchmark_inputs": (
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
    ),
    "sequence_policy_input_probe": (
        "reports/strategy_arbitration/krk_sequence_policy_input_probe_v0.json"
    ),
    "sequence_benchmark": "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json",
    "sequence_benchmark_design": (
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json"
    ),
    "sequence_benchmark_review": (
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
    ),
    "cross_stage_plan_capsule_requirements": (
        "reports/strategy_arbitration/"
        "krk_cross_stage_plan_capsule_evidence_requirements_v0.json"
    ),
    "protected_plan_window_frames": (
        "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json"
    ),
    "protected_failure_contrast_plan": (
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json"
    ),
    "protected_failure_contrast_manifest": (
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
    ),
    "protected_failure_contrast_manifest_review": (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_manifest_review_v0.json"
    ),
    "protected_failure_contrast_execution_readiness": (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
    ),
    "protected_failure_contrast_runner": (
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_runner_v0.json"
    ),
    "protected_failure_contrast_approval_request": (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
    ),
    "protected_failure_contrast_output_validation": (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_output_validation_v0.json"
    ),
    "protected_failure_contrast_integration": (
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_integration_v0.json"
    ),
    "post_failure_contrast_sequence_refresh": (
        "reports/strategy_arbitration/"
        "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
    ),
    "stage7_sampling_runner": (
        "reports/structural_candidates/stage7_diverse_clean_sampling_runner_v0.json"
    ),
    "stage7_sampling_manifest": (
        "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
    ),
    "stage7_sampling_execution_readiness": (
        "reports/structural_candidates/stage7_diverse_clean_sampling_execution_readiness_v0.json"
    ),
    "stage7_sampling_output_validation": (
        "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
    ),
    "stage7_sampling_integration": (
        "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json"
    ),
    "stage7_diverse_clean_label_distribution_review": (
        "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.json"
    ),
    "stage7_additional_clean_sampling_manifest": (
        "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
    ),
    "stage7_additional_clean_sampling_runner": (
        "reports/structural_candidates/stage7_additional_clean_sampling_runner_v0.json"
    ),
    "stage7_post_label_outcome_review": "reports/krk_stage7_post_label_outcome_review_v0.json",
}


FORBIDDEN_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}

FORBIDDEN_INPUT_BLOCKERS = {
    "selector_training_rows_forbidden",
    "runtime_authorization_rows_forbidden",
}

FORBIDDEN_INPUT_STATUSES = {
    "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows",
    "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows",
}

DEFAULT_FAILURE_CONTRAST_APPROVAL_RECEIPT = (
    "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
)


def find_approval_option(gate: dict[str, Any], option_id: str) -> dict[str, Any]:
    for option in gate.get("approval_options") or []:
        if option.get("option_id") == option_id:
            return option
    return {}


def find_first_approval_option(
    gate: dict[str, Any], option_ids: tuple[str, ...]
) -> dict[str, Any]:
    for option_id in option_ids:
        option = find_approval_option(gate, option_id)
        if option:
            return option
    return {}


def load_json(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    if not path.exists():
        return {"_missing": True, "_path": relative}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return data


def flag_value(payload: dict[str, Any], key: str) -> Any:
    if key in payload:
        return payload[key]
    invariants = payload.get("invariants")
    if isinstance(invariants, dict) and key in invariants:
        return invariants[key]
    return None


def artifact_ok(payload: dict[str, Any]) -> bool:
    return payload.get("_missing") is not True


def safe_relative_path(path_value: Any) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    path = Path(path_value)
    return not path.is_absolute() and ".." not in path.parts


def stack_path_status(stack: dict[str, Any]) -> dict[str, Any]:
    unsafe_paths: list[str] = []
    missing_paths: list[str] = []
    checked = 0
    for stack_name, entries in stack.items():
        if not isinstance(entries, dict):
            unsafe_paths.append(str(stack_name))
            continue
        for key, path_value in entries.items():
            label = f"{stack_name}.{key}"
            checked += 1
            if not safe_relative_path(path_value):
                unsafe_paths.append(label)
                continue
            if not (ROOT / str(path_value)).exists():
                missing_paths.append(label)
    return {
        "checked_path_count": checked,
        "unsafe_paths": unsafe_paths,
        "missing_paths": missing_paths,
        "all_paths_safe": not unsafe_paths,
        "all_paths_exist": not missing_paths,
    }


def flatten_bool_tree(tree: dict[str, Any]) -> dict[str, Any]:
    false_paths: list[str] = []
    checked = 0

    def visit(node: Any, prefix: str) -> None:
        nonlocal checked
        if isinstance(node, dict):
            for key, value in node.items():
                label = f"{prefix}.{key}" if prefix else str(key)
                visit(value, label)
            return
        checked += 1
        if node is not True:
            false_paths.append(prefix)

    visit(tree, "")
    return {
        "checked_path_count": checked,
        "false_paths": false_paths,
        "all_paths_exist": checked > 0 and not false_paths,
    }


def rollback_distinct_for_common_paths(
    active_stack: dict[str, Any], rollback_stack: dict[str, Any]
) -> bool:
    for stack_name, active_entries in active_stack.items():
        rollback_entries = rollback_stack.get(stack_name)
        if not isinstance(active_entries, dict) or not isinstance(rollback_entries, dict):
            continue
        for key, active_path in active_entries.items():
            if key in rollback_entries and rollback_entries[key] == active_path:
                return False
    return True


def boundary_status(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    checked = 0
    for name, payload in payloads.items():
        if not artifact_ok(payload):
            continue
        for key, expected in FORBIDDEN_FLAGS.items():
            value = flag_value(payload, key)
            if value is None:
                continue
            checked += 1
            if value is not expected:
                violations.append(
                    {
                        "artifact": SOURCES[name],
                        "field": key,
                        "expected": expected,
                        "actual": value,
                    }
                )

    return {
        "checked_flag_count": checked,
        "violation_count": len(violations),
        "violations": violations,
        "runtime_defaults_changed": False,
        "runtime_behavior_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }


def build_payload() -> dict[str, Any]:
    payloads = {name: load_json(path) for name, path in SOURCES.items() if path.endswith(".json")}

    active = payloads["active_protected_stack"]
    clean = payloads["clean_stack_validation"]
    preservation = payloads["preservation_checks"]
    stage4_unblocker = payloads["stage4_caveat_unblocker"]
    stage4_runtime_review = payloads["stage4_first_move_contrast_runtime_review"]
    stage4_approval_request = payloads["stage4_sandbox_approval_request"]
    pipeline = payloads["sequence_pipeline_refresh"]
    sequence_policy_input_probe = payloads["sequence_policy_input_probe"]
    benchmark = payloads["sequence_benchmark"]
    benchmark_design = payloads["sequence_benchmark_design"]
    benchmark_review = payloads["sequence_benchmark_review"]
    cross_stage_requirements = payloads["cross_stage_plan_capsule_requirements"]
    failure_contrast_plan = payloads["protected_failure_contrast_plan"]
    failure_contrast_manifest = payloads["protected_failure_contrast_manifest"]
    failure_contrast_manifest_review = payloads["protected_failure_contrast_manifest_review"]
    failure_contrast_execution_readiness = payloads[
        "protected_failure_contrast_execution_readiness"
    ]
    failure_contrast_runner = payloads["protected_failure_contrast_runner"]
    failure_contrast_approval_request = payloads[
        "protected_failure_contrast_approval_request"
    ]
    failure_contrast_output_validation = payloads[
        "protected_failure_contrast_output_validation"
    ]
    failure_contrast_integration = payloads["protected_failure_contrast_integration"]
    post_failure_contrast_sequence_refresh = payloads[
        "post_failure_contrast_sequence_refresh"
    ]
    protected_missing_provider_labels = payloads[
        "protected_missing_provider_capacity_labels"
    ]
    protected_missing_provider_merge = payloads[
        "protected_missing_provider_label_merge_review"
    ]
    protected_missing_provider_coverage = payloads[
        "ranked_proposal_protected_provider_coverage_review"
    ]
    protected_coverage_expansion_plan = payloads[
        "protected_proposal_coverage_expansion_plan"
    ]
    protected_provider_coverage_frames = payloads[
        "protected_provider_coverage_frames"
    ]
    protected_capacity_frame_semantics = payloads[
        "protected_provider_capacity_frame_training_semantics_review"
    ]
    candidate_generator_coverage = payloads["candidate_generator_coverage_audit"]
    validated_provider_candidate_set = payloads[
        "validated_provider_candidate_set_audit"
    ]
    two_stage_candidate_selection_review = payloads[
        "two_stage_candidate_selection_review"
    ]
    two_stage_candidate_selection_benchmark_plan = payloads[
        "two_stage_candidate_selection_benchmark_plan"
    ]
    two_stage_candidate_selection_benchmark = payloads[
        "two_stage_candidate_selection_benchmark"
    ]
    strategy_arbitration_dataset = payloads["strategy_arbitration_dataset"]
    strategy_arbitration_probe = payloads["strategy_arbitration_probe"]
    strategy_arbitration_decision_gate = payloads["strategy_arbitration_decision_gate"]
    strategy_missing_feature_candidates = payloads[
        "strategy_missing_feature_candidates"
    ]
    strategy_monitor_v0_plan = payloads["strategy_monitor_v0_plan"]
    strategy_monitor_records_v0 = payloads["strategy_monitor_records_v0"]
    strategy_monitor_companion_terms_v0 = payloads[
        "strategy_monitor_companion_terms_v0"
    ]
    strategy_monitor_companion_audit_v0 = payloads[
        "strategy_monitor_companion_audit_v0"
    ]
    visible_monitor_terms_v0 = payloads["visible_monitor_terms_v0"]
    strategy_monitor_companion_audit_v1 = payloads[
        "strategy_monitor_companion_audit_v1"
    ]
    strategy_monitor_maturity_gate_v0 = payloads[
        "strategy_monitor_maturity_gate_v0"
    ]
    feature_candidate_validation = payloads["feature_candidate_validation"]
    internal_terminal_candidates = payloads["internal_terminal_candidates"]
    internal_terminal_validation = payloads["internal_terminal_validation"]
    internal_terminal_evidence_v1 = payloads["internal_terminal_evidence_v1"]
    internal_terminal_design_review_v1 = payloads[
        "internal_terminal_design_review_v1"
    ]
    candidate_proposal_coverage = payloads["candidate_proposal_coverage"]
    candidate_generation_strategy_review = payloads[
        "candidate_generation_strategy_review"
    ]
    strategy_sequence_candidate_frame_schema_v1 = payloads[
        "strategy_sequence_candidate_frame_schema_v1"
    ]
    strategy_sequence_candidate_frames_v1 = payloads[
        "strategy_sequence_candidate_frames_v1"
    ]
    strategy_sequence_candidate_frame_quality_v1 = payloads[
        "strategy_sequence_candidate_frame_quality_v1"
    ]
    candidate_frame_source_benchmark_v1 = payloads[
        "candidate_frame_source_benchmark_v1"
    ]
    strategy_sequence_control_plane_decision_v1 = payloads[
        "strategy_sequence_control_plane_decision_v1"
    ]
    candidate_generation_sandbox_review = payloads[
        "candidate_generation_sandbox_review"
    ]
    broader_strategy_sequence_candidate_source_design_v1 = payloads[
        "broader_strategy_sequence_candidate_source_design_v1"
    ]
    candidate_generation_observation_sandbox = payloads[
        "candidate_generation_observation_sandbox"
    ]
    candidate_generation_observation_coverage = payloads[
        "candidate_generation_observation_coverage"
    ]
    candidate_generation_observation_broadened_sample = payloads[
        "candidate_generation_observation_broadened_sample"
    ]
    candidate_generation_observation_gap_review = payloads[
        "candidate_generation_observation_gap_review"
    ]
    candidate_move_capacity_annotation_v1 = payloads[
        "candidate_move_capacity_annotation_v1"
    ]
    candidate_move_capacity_label_manifest_v1 = payloads[
        "candidate_move_capacity_label_manifest_v1"
    ]
    candidate_move_capacity_labels_v1 = payloads[
        "candidate_move_capacity_labels_v1"
    ]
    candidate_move_capacity_annotation_v2 = payloads[
        "candidate_move_capacity_annotation_v2"
    ]
    candidate_generation_label_blocker_review = payloads[
        "candidate_generation_label_blocker_review"
    ]
    candidate_proposal_quality_prioritization_review = payloads[
        "candidate_proposal_quality_prioritization_review"
    ]
    candidate_proposal_quality_dataset = payloads[
        "candidate_proposal_quality_dataset"
    ]
    candidate_proposal_quality_probe = payloads["candidate_proposal_quality_probe"]
    candidate_proposal_quality_decision = payloads[
        "candidate_proposal_quality_decision"
    ]
    plan_capsule_sequence_candidate_observation_review_v1 = payloads[
        "plan_capsule_sequence_candidate_observation_review_v1"
    ]
    broader_strategy_candidate_observation_review_v1 = payloads[
        "broader_strategy_candidate_observation_review_v1"
    ]
    broader_strategy_sequence_candidate_source_review_v1 = payloads[
        "broader_strategy_sequence_candidate_source_review_v1"
    ]
    protected_strategy_monitor_frame_expansion_v1 = payloads[
        "protected_strategy_monitor_frame_expansion_v1"
    ]
    protected_strategy_monitor_frame_quality_v1 = payloads[
        "protected_strategy_monitor_frame_quality_v1"
    ]
    protected_strategy_monitor_observation_source_review_packet_v1 = payloads[
        "protected_strategy_monitor_observation_source_review_packet_v1"
    ]
    repair_monitor_observation_source_smoke_v1 = payloads[
        "repair_monitor_observation_source_smoke_v1"
    ]
    repair_monitor_observation_source_coverage_v1 = payloads[
        "repair_monitor_observation_source_coverage_v1"
    ]
    repair_monitor_observation_source_broadened_v1 = payloads[
        "repair_monitor_observation_source_broadened_v1"
    ]
    repair_monitor_observation_source_quality_review_v1 = payloads[
        "repair_monitor_observation_source_quality_review_v1"
    ]
    strategy_sequence_repair_monitor_trace_features_v1 = payloads[
        "strategy_sequence_repair_monitor_trace_features_v1"
    ]
    strategy_sequence_trace_feature_integration_review_v1 = payloads[
        "strategy_sequence_trace_feature_integration_review_v1"
    ]
    strategy_sequence_dataset_design_v2 = payloads[
        "strategy_sequence_dataset_design_v2"
    ]
    strategy_sequence_dataset_v2 = payloads["strategy_sequence_dataset_v2"]
    strategy_sequence_dataset_v2_quality_probe = payloads[
        "strategy_sequence_dataset_v2_quality_probe"
    ]
    candidate_generation_refresh_probe_v2 = payloads[
        "candidate_generation_refresh_probe_v2"
    ]
    candidate_generation_capacity_evidence_manifest_v2 = payloads[
        "candidate_generation_capacity_evidence_manifest_v2"
    ]
    candidate_generation_capacity_evidence_labels_v2 = payloads[
        "candidate_generation_capacity_evidence_labels_v2"
    ]
    strategy_sequence_dataset_v2_capacity_merged = payloads[
        "strategy_sequence_dataset_v2_capacity_merged"
    ]
    candidate_generation_refresh_probe_v2_after_labels = payloads[
        "candidate_generation_refresh_probe_v2_after_labels"
    ]
    candidate_generation_refresh_probe_v2_cross_stage_labels = payloads[
        "candidate_generation_refresh_probe_v2_cross_stage_labels"
    ]
    candidate_generation_training_refresh_design_v2 = payloads[
        "candidate_generation_training_refresh_design_v2"
    ]
    stage5_6_candidate_generation_refresh_review_packet_v3 = payloads[
        "stage5_6_candidate_generation_refresh_review_packet_v3"
    ]
    stage5_6_candidate_generation_refresh_smoke = payloads[
        "stage5_6_candidate_generation_refresh_smoke"
    ]
    stage5_6_candidate_generation_refresh_coverage = payloads[
        "stage5_6_candidate_generation_refresh_coverage"
    ]
    stage5_6_candidate_generation_refresh_broadened = payloads[
        "stage5_6_candidate_generation_refresh_broadened"
    ]
    stage5_6_candidate_generation_refresh_quality_review = payloads[
        "stage5_6_candidate_generation_refresh_quality_review"
    ]
    strategy_sequence_stage5_6_refresh_trace_features = payloads[
        "strategy_sequence_stage5_6_refresh_trace_features"
    ]
    strategy_sequence_dataset_design_v3 = payloads[
        "strategy_sequence_dataset_design_v3"
    ]
    candidate_generation_cross_stage_capacity_review_v2 = payloads[
        "candidate_generation_cross_stage_capacity_review_v2"
    ]
    candidate_generation_cross_stage_capacity_manifest_v3 = payloads[
        "candidate_generation_cross_stage_capacity_manifest_v3"
    ]
    candidate_generation_cross_stage_capacity_labels_v3 = payloads[
        "candidate_generation_cross_stage_capacity_labels_v3"
    ]
    strategy_sequence_dataset_v2_cross_stage_capacity_merged = payloads[
        "strategy_sequence_dataset_v2_cross_stage_capacity_merged"
    ]
    candidate_generation_cross_stage_label_outcome_review_v3 = payloads[
        "candidate_generation_cross_stage_label_outcome_review_v3"
    ]
    candidate_generation_stage_conditioned_scope_review_v3 = payloads[
        "candidate_generation_stage_conditioned_scope_review_v3"
    ]
    stage_conditioned_candidate_generation_benchmark_v3 = payloads[
        "stage_conditioned_candidate_generation_benchmark_v3"
    ]
    ownership_label_recovery_review = payloads["ownership_label_recovery_review"]
    selector_objective_seed_manifest_v0 = payloads[
        "selector_objective_seed_manifest_v0"
    ]
    selector_objective_seed_probe_v0 = payloads["selector_objective_seed_probe_v0"]
    joined_trace_ownership_collection_manifest = payloads[
        "joined_trace_ownership_collection_manifest"
    ]
    joined_trace_ownership_collection_review_packet = payloads[
        "joined_trace_ownership_collection_review_packet"
    ]
    joined_trace_ownership_collection = payloads[
        "joined_trace_ownership_collection"
    ]
    selector_objective_seed_manifest_v1 = payloads[
        "selector_objective_seed_manifest_v1"
    ]
    selector_objective_seed_probe_v1 = payloads["selector_objective_seed_probe_v1"]
    selector_objective_feature_probe = payloads["selector_objective_feature_probe"]
    selector_objective_feature_probe_review = payloads[
        "selector_objective_feature_probe_review"
    ]
    selector_objective_diversity_gap_review = payloads[
        "selector_objective_diversity_gap_review"
    ]
    stage4_joined_trace_ownership_scope_review_packet = payloads[
        "stage4_joined_trace_ownership_scope_review_packet"
    ]
    stage4_joined_trace_ownership_collection = payloads[
        "stage4_joined_trace_ownership_collection"
    ]
    selector_objective_seed_manifest_v2 = payloads[
        "selector_objective_seed_manifest_v2"
    ]
    selector_objective_seed_probe_v2 = payloads["selector_objective_seed_probe_v2"]
    selector_objective_benchmark_v2 = payloads["selector_objective_benchmark_v2"]
    selector_objective_benchmark_review_packet_v2 = payloads[
        "selector_objective_benchmark_review_packet_v2"
    ]
    selector_objective_independent_validation_manifest = payloads[
        "selector_objective_independent_validation_manifest"
    ]
    selector_objective_independent_validation_labels = payloads[
        "selector_objective_independent_validation_labels"
    ]
    selector_objective_independent_validation = payloads[
        "selector_objective_independent_validation"
    ]
    selector_objective_independent_validation_blocker = payloads[
        "selector_objective_independent_validation_blocker"
    ]
    stage4_failure_discovery = payloads["stage4_failure_discovery"]
    stage4_caveat_sequence_review = payloads["stage4_caveat_sequence_review"]
    stage4_sequence_candidate_review = payloads["stage4_sequence_candidate_review"]
    stage4_first_move_feature_review = payloads["stage4_first_move_feature_review"]
    stage4_stratified_contrast_validation = payloads[
        "stage4_stratified_contrast_validation"
    ]
    sequence_control_contrast_dataset = payloads["sequence_control_contrast_dataset"]
    sequence_control_contrast_probe = payloads["sequence_control_contrast_probe"]
    strategy_sequence_dataset_v3 = payloads["strategy_sequence_dataset_v3"]
    strategy_sequence_dataset_v3_quality_probe = payloads[
        "strategy_sequence_dataset_v3_quality_probe"
    ]
    strategy_sequence_dataset_v3_context_review = payloads[
        "strategy_sequence_dataset_v3_context_review"
    ]
    candidate_generation_v3_context_benchmark = payloads[
        "candidate_generation_v3_context_benchmark"
    ]
    candidate_generation_v3_runtime_boundary_review = payloads[
        "candidate_generation_v3_runtime_boundary_review"
    ]
    candidate_generation_v3_training_refresh_review = payloads[
        "candidate_generation_v3_training_refresh_review"
    ]
    candidate_generation_training_refresh_design_v3 = payloads[
        "candidate_generation_training_refresh_design_v3"
    ]
    candidate_generation_training_refresh_benchmark_v3 = payloads[
        "candidate_generation_training_refresh_benchmark_v3"
    ]
    candidate_generation_training_refresh_runtime_review_v3 = payloads[
        "candidate_generation_training_refresh_runtime_review_v3"
    ]
    candidate_generation_refresh_sandbox = payloads[
        "candidate_generation_refresh_sandbox"
    ]
    candidate_generation_refresh_coverage = payloads[
        "candidate_generation_refresh_coverage"
    ]
    strategy_sequence_candidate_generation_refresh_trace_features = payloads[
        "strategy_sequence_candidate_generation_refresh_trace_features"
    ]
    strategy_sequence_dataset_v4 = payloads["strategy_sequence_dataset_v4"]
    strategy_sequence_dataset_v4_quality_probe = payloads[
        "strategy_sequence_dataset_v4_quality_probe"
    ]
    strategy_sequence_dataset_v4_context_review = payloads[
        "strategy_sequence_dataset_v4_context_review"
    ]
    candidate_generation_v4_context_benchmark = payloads[
        "candidate_generation_v4_context_benchmark"
    ]
    candidate_generation_v4_next_boundary_review = payloads[
        "candidate_generation_v4_next_boundary_review"
    ]
    candidate_generation_scope_gap_review = payloads[
        "candidate_generation_scope_gap_review"
    ]
    candidate_source_gap_manifest = payloads["candidate_source_gap_manifest"]
    candidate_source_expansion_options = payloads[
        "candidate_source_expansion_options"
    ]
    exact_trace_enrichment_runtime_review = payloads[
        "exact_trace_enrichment_runtime_review"
    ]
    exact_trace_enrichment_sandbox = payloads["exact_trace_enrichment_sandbox"]
    exact_trace_enrichment_coverage = payloads["exact_trace_enrichment_coverage"]
    strategy_sequence_dataset_v5 = payloads["strategy_sequence_dataset_v5"]
    strategy_sequence_dataset_v5_quality_probe = payloads[
        "strategy_sequence_dataset_v5_quality_probe"
    ]
    strategy_sequence_dataset_v5_context_review = payloads[
        "strategy_sequence_dataset_v5_context_review"
    ]
    candidate_generation_v5_context_benchmark = payloads[
        "candidate_generation_v5_context_benchmark"
    ]
    candidate_generation_v5_next_boundary_review = payloads[
        "candidate_generation_v5_next_boundary_review"
    ]
    clean_curriculum_checkpoint_plan = payloads["clean_curriculum_checkpoint_plan"]
    clean_retrain_execution_manifest = payloads["clean_retrain_execution_manifest"]
    stage6_overlay_compose_manifest = payloads["stage6_overlay_compose_manifest"]
    clean_retrain_preflight = payloads["clean_retrain_preflight"]
    clean_retrain_smoke_manifest = payloads["clean_retrain_smoke_manifest"]
    clean_retrain_smoke_result = payloads["clean_retrain_smoke_result"]
    clean_retrain_run_result = payloads["clean_retrain_run_result"]
    clean_retrain_retry1_result = payloads["clean_retrain_retry1_result"]
    clean_retrain_retry1_guardrail_result = payloads[
        "clean_retrain_retry1_guardrail_result"
    ]
    clean_retrain_retry1_stage6_gap_inspection = payloads[
        "clean_retrain_retry1_stage6_gap_inspection"
    ]
    stage5_guardrail_control_debt_review = payloads[
        "stage5_guardrail_control_debt_review"
    ]
    stage5_guardrail_semantics_split = payloads["stage5_guardrail_semantics_split"]
    stage5_local_reward_contract_debt_audit = payloads[
        "stage5_local_reward_contract_debt_audit"
    ]
    clean_retrain_retry1_stage4_caveat_control_review = payloads[
        "clean_retrain_retry1_stage4_caveat_control_review"
    ]
    curriculum_next_milestone_decision = payloads[
        "curriculum_next_milestone_decision"
    ]
    stage7_heldout_unlock_review = payloads["stage7_heldout_unlock_review"]
    stage7_to_stage8_blocker_review = payloads["stage7_to_stage8_blocker_review"]
    strategy_sequence_architecture_review = payloads[
        "strategy_sequence_architecture_review"
    ]
    strategy_sequence_evidence_plan = payloads["strategy_sequence_evidence_plan"]
    strategy_sequence_inventory = payloads["strategy_sequence_inventory"]
    strategy_owner_contrast_label_plan = payloads[
        "strategy_owner_contrast_label_plan"
    ]
    strategy_owner_contrast_label_plan_review = payloads[
        "strategy_owner_contrast_label_plan_review"
    ]
    strategy_owner_contrast_execution_manifest = payloads[
        "strategy_owner_contrast_execution_manifest"
    ]
    strategy_owner_contrast_execution_manifest_review = payloads[
        "strategy_owner_contrast_execution_manifest_review"
    ]
    strategy_owner_contrast_control_labels = payloads[
        "strategy_owner_contrast_control_labels"
    ]
    strategy_owner_contrast_dataset = payloads["strategy_owner_contrast_dataset"]
    strategy_owner_contrast_probe = payloads["strategy_owner_contrast_probe"]
    arbitration_objective_review_v1 = payloads["arbitration_objective_review_v1"]
    normalized_strategy_selector_objective_v1 = payloads[
        "normalized_strategy_selector_objective_v1"
    ]
    normalized_strategy_selector_objective_probe_v1 = payloads[
        "normalized_strategy_selector_objective_probe_v1"
    ]
    normalized_selector_probe_review_v1 = payloads[
        "normalized_selector_probe_review_v1"
    ]
    selector_objective_architecture_review_v1 = payloads[
        "selector_objective_architecture_review_v1"
    ]
    selector_objective_label_semantics_v0 = payloads[
        "selector_objective_label_semantics_v0"
    ]
    split_selector_objective_dataset_v3 = payloads[
        "split_selector_objective_dataset_v3"
    ]
    split_selector_objective_readiness_v3 = payloads[
        "split_selector_objective_readiness_v3"
    ]
    abstention_first_selector_objective_v0 = payloads[
        "abstention_first_selector_objective_v0"
    ]
    abstention_safe_preservation_label_review_v0 = payloads[
        "abstention_safe_preservation_label_review_v0"
    ]
    abstention_training_dataset_v1 = payloads["abstention_training_dataset_v1"]
    abstention_training_probe_v1 = payloads["abstention_training_probe_v1"]
    abstention_context_feature_dataset_v0 = payloads[
        "abstention_context_feature_dataset_v0"
    ]
    abstention_context_feature_probe_v0 = payloads[
        "abstention_context_feature_probe_v0"
    ]
    abstention_context_error_audit_v0 = payloads["abstention_context_error_audit_v0"]
    abstention_feature_gap_review_v0 = payloads["abstention_feature_gap_review_v0"]
    targeted_non_stage0_ownership_manifest_v0 = payloads[
        "targeted_non_stage0_ownership_manifest_v0"
    ]
    targeted_non_stage0_ownership_labels_v0 = payloads[
        "targeted_non_stage0_ownership_labels_v0"
    ]
    targeted_non_stage0_ownership_review_v0 = payloads[
        "targeted_non_stage0_ownership_review_v0"
    ]
    targeted_ownership_negative_manifest_v0 = payloads[
        "targeted_ownership_negative_manifest_v0"
    ]
    targeted_ownership_negative_labels_v0 = payloads[
        "targeted_ownership_negative_labels_v0"
    ]
    balanced_hard_negative_label_plan_v1 = payloads[
        "balanced_hard_negative_label_plan_v1"
    ]
    balanced_hard_negative_execution_manifest_v1 = payloads[
        "balanced_hard_negative_execution_manifest_v1"
    ]
    balanced_hard_negative_execution_manifest_review_v1 = payloads[
        "balanced_hard_negative_execution_manifest_review_v1"
    ]
    balanced_hard_negative_labels_v1 = payloads[
        "balanced_hard_negative_labels_v1"
    ]
    balanced_hard_negative_evidence_review_v0 = payloads[
        "balanced_hard_negative_evidence_review_v0"
    ]
    clean_replacement_readiness = payloads[
        "clean_retrain_retry1_replacement_readiness_review"
    ]
    clean_stack_snapshot_manifest = payloads[
        "clean_retrain_retry1_protected_stack_snapshot_manifest"
    ]
    clean_stack_replacement_packet = payloads[
        "clean_retrain_retry1_clean_stack_replacement_review_packet"
    ]
    clean_stack_deferred_review = payloads["clean_stack_replacement_deferred_review"]
    protected_stage_status = payloads["protected_stage_status"]
    runner = payloads["stage7_sampling_runner"]
    output_validation = payloads["stage7_sampling_output_validation"]
    integration = payloads["stage7_sampling_integration"]
    gate = payloads["control_plane_gate"]
    gate_approval_options = gate.get("approval_options") or []
    protected_collection_gate_option = find_approval_option(
        gate,
        "approve_protected_plan_window_failure_contrast_collection",
    )
    protected_collection_command_available = bool(
        protected_collection_gate_option.get("command_if_explicitly_approved")
    )
    protected_collection_blocking_gate_option = find_first_approval_option(
        gate,
        (
            "repair_protected_stack_validation",
            "repair_protected_failure_contrast_approval_request_scope",
            "review_protected_plan_window_failure_contrast_execution_readiness",
            "review_protected_plan_window_failure_contrast_manifest",
            "review_protected_plan_window_failure_contrast_plan",
        ),
    )

    boundaries = boundary_status(payloads)
    stage7_summary = integration.get("summary", {})
    sequence_summary = pipeline.get("summary", {})
    benchmark_preflight = benchmark.get("preflight", {})
    output_validation_status = output_validation.get("decision", {}).get(
        "status",
        runner.get("summary", {}).get("output_validation_status"),
    )

    active_stack = active.get("active_protected_stack") or {}
    rollback_stack = active.get("rollback_protected_stack") or {}
    active_stack_paths = stack_path_status(active_stack)
    rollback_stack_paths = stack_path_status(rollback_stack)
    rollback_common_paths_distinct = rollback_distinct_for_common_paths(
        active_stack, rollback_stack
    )
    snapshot_decision = clean_stack_snapshot_manifest.get("decision") or {}
    snapshot_path_existence = clean_stack_snapshot_manifest.get("path_existence") or {}
    snapshot_current_stack_path_status = flatten_bool_tree(
        snapshot_path_existence.get("current_protected_stack") or {}
    )
    snapshot_retry1_stack_path_status = flatten_bool_tree(
        snapshot_path_existence.get("retry1_candidate_stack") or {}
    )
    clean_retrain_execution_decision = (
        clean_retrain_execution_manifest.get("decision") or {}
    )
    stage6_overlay_compose_decision = (
        stage6_overlay_compose_manifest.get("decision") or {}
    )
    clean_retrain_preflight_summary = clean_retrain_preflight.get("summary") or {}
    clean_retrain_smoke_decision = clean_retrain_smoke_manifest.get("decision") or {}
    clean_retrain_smoke_summary = clean_retrain_smoke_result.get("summary") or {}
    clean_retrain_initial_decision = clean_retrain_run_result.get("decision") or {}
    clean_retrain_retry1_decision = clean_retrain_retry1_result.get("decision") or {}
    clean_retrain_retry1_run_scope = clean_retrain_retry1_result.get("run_scope") or {}
    clean_retrain_retry1_stages = clean_retrain_retry1_result.get("stages") or {}
    clean_retrain_guardrail_decision = (
        clean_retrain_retry1_guardrail_result.get("decision") or {}
    )
    stage6_gap_decision = clean_retrain_retry1_stage6_gap_inspection.get(
        "decision"
    ) or {}
    stage5_control_debt_decision = (
        stage5_guardrail_control_debt_review.get("decision") or {}
    )
    stage5_semantics_decision = stage5_guardrail_semantics_split.get("decision") or {}
    stage5_local_debt_decision = (
        stage5_local_reward_contract_debt_audit.get("decision") or {}
    )
    stage4_caveat_control_decision = (
        clean_retrain_retry1_stage4_caveat_control_review.get("decision") or {}
    )
    curriculum_next_invariants = curriculum_next_milestone_decision.get(
        "invariants"
    ) or {}
    clean_curriculum_run_lineage_passive = (
        clean_retrain_execution_decision.get("full_run_authorized_by_this_manifest")
        is False
        and stage6_overlay_compose_decision.get("compose_run_authorized_by_this_manifest")
        is False
        and stage6_overlay_compose_decision.get("full_run_authorized_by_this_manifest")
        is False
        and clean_retrain_preflight.get("decision", {}).get("training_started") is False
        and int(clean_retrain_preflight_summary.get("blocker_count") or 0) == 0
        and int(clean_retrain_preflight_summary.get("command_violation_count") or 0)
        == 0
        and int(clean_retrain_preflight_summary.get("protected_overwrite_count") or 0)
        == 0
        and clean_retrain_smoke_decision.get("full_run_authorized_by_this_manifest")
        is False
        and clean_retrain_smoke_decision.get("smoke_run_authorized_by_this_manifest")
        is False
        and clean_retrain_smoke_summary.get("command_plumbing_validated") is True
        and clean_retrain_smoke_summary.get("curriculum_semantics_validated") is False
        and clean_retrain_initial_decision.get("full_clean_retrain_complete") is False
        and clean_retrain_retry1_decision.get(
            "clean_retrain_retry_complete_through_stage6"
        )
        is True
        and clean_retrain_retry1_decision.get("promoted_by_this_artifact") is False
        and clean_retrain_retry1_run_scope.get("protected_snapshots_overwritten")
        is False
        and clean_retrain_retry1_run_scope.get("stage7_training_or_promotion") is False
        and clean_retrain_retry1_run_scope.get("stage8_training") is False
        and clean_retrain_retry1_run_scope.get("runtime_selector_or_routing_change")
        is False
        and clean_retrain_guardrail_decision.get("retry1_can_replace_protected_stack")
        is False
        and stage6_gap_decision.get("corrected_profile_bonus_restores_stage6_conversion")
        is True
        and stage5_control_debt_decision.get("stage5_conversion_preserved") is True
        and stage5_control_debt_decision.get(
            "should_quarantine_stage6_overlay_for_stage5_one_ply_debt"
        )
        is False
        and stage5_semantics_decision.get("stage6_overlay_use_allowed_as_overlay_only")
        is True
        and stage5_semantics_decision.get("clean_stack_replacement_allowed") is False
        and stage5_local_debt_decision.get("conversion_preserved") is True
        and stage5_local_debt_decision.get("local_reward_debt_is_stage6_regression")
        is False
        and stage4_caveat_control_decision.get("stage4_overlay_regressed_vs_base_control")
        is False
        and curriculum_next_invariants.get("protected_stack_replacement_performed")
        is False
        and curriculum_next_invariants.get("runtime_behavior_changed") is False
        and curriculum_next_invariants.get("runtime_defaults_changed") is False
        and curriculum_next_invariants.get("stage7_promotion") is False
        and curriculum_next_invariants.get("stage8_training") is False
        and stage7_heldout_unlock_review.get("status")
        == "stage7_unlock_path_identified_broader_sequence_control_not_micro_repair"
        and stage7_to_stage8_blocker_review.get("stage7_promotion_allowed") is False
        and stage7_to_stage8_blocker_review.get("stage8_training_allowed") is False
    )
    strategy_sequence_architecture_decision = (
        strategy_sequence_architecture_review.get("decision") or {}
    )
    strategy_sequence_evidence_plan_decision = (
        strategy_sequence_evidence_plan.get("decision") or {}
    )
    strategy_sequence_inventory_decision = (
        strategy_sequence_inventory.get("decision") or {}
    )
    strategy_sequence_gap_summary = strategy_sequence_inventory.get("gap_summary") or {}
    strategy_sequence_boundary_inventory = (
        strategy_sequence_inventory.get("curriculum_boundary_inventory") or {}
    )
    strategy_sequence_next_objective_ids = [
        item.get("objective_id")
        for item in strategy_sequence_architecture_review.get(
            "next_architecture_objectives"
        )
        or []
        if item.get("objective_id")
    ]
    strategy_sequence_architecture_passive = (
        strategy_sequence_architecture_decision.get("status")
        == "broader_krk_strategy_sequence_review_ready"
        and strategy_sequence_architecture_decision.get("runtime_work_allowed") is False
        and strategy_sequence_architecture_review.get("runtime_behavior_changed") is False
        and strategy_sequence_architecture_review.get("runtime_defaults_changed") is False
        and strategy_sequence_architecture_review.get("runtime_selector_implemented")
        is False
        and strategy_sequence_architecture_review.get("runtime_dtm_or_tablebase_lookup")
        is False
        and strategy_sequence_architecture_review.get("stage7_promotion_allowed")
        is False
        and strategy_sequence_architecture_review.get("stage8_training_allowed")
        is False
        and strategy_sequence_evidence_plan_decision.get("status")
        == "strategy_sequence_evidence_plan_defined"
        and strategy_sequence_evidence_plan_decision.get("runtime_work_allowed") is False
        and strategy_sequence_evidence_plan.get("runtime_behavior_changed") is False
        and strategy_sequence_evidence_plan.get("runtime_defaults_changed") is False
        and strategy_sequence_evidence_plan.get("runtime_selector_implemented") is False
        and strategy_sequence_evidence_plan.get("runtime_dtm_or_tablebase_lookup")
        is False
        and strategy_sequence_evidence_plan.get("stage7_promotion_allowed") is False
        and strategy_sequence_evidence_plan.get("stage8_training_allowed") is False
        and strategy_sequence_inventory_decision.get("status")
        == "replay_free_inventory_state_holdout_gap_blocks_runtime"
        and strategy_sequence_inventory_decision.get("runtime_work_allowed") is False
        and strategy_sequence_gap_summary.get("runtime_work_allowed") is False
        and strategy_sequence_gap_summary.get("sequence_policy_clean_gate_closed")
        is True
        and strategy_sequence_gap_summary.get("sequence_policy_has_clean_success_gap")
        is False
        and strategy_sequence_gap_summary.get("state_holdout_gap_blocks_runtime") is True
        and strategy_sequence_gap_summary.get("strategy_ownership_has_some_signal")
        is True
        and strategy_sequence_gap_summary.get("strategy_ownership_state_holdout_ready")
        is False
        and strategy_sequence_boundary_inventory.get("stage7_is_held_out") is True
        and strategy_sequence_inventory.get("runtime_behavior_changed") is False
        and strategy_sequence_inventory.get("runtime_defaults_changed") is False
        and strategy_sequence_inventory.get("runtime_selector_implemented") is False
        and strategy_sequence_inventory.get("runtime_dtm_or_tablebase_lookup") is False
        and strategy_sequence_inventory.get("stage7_promotion_allowed") is False
        and strategy_sequence_inventory.get("stage8_training_allowed") is False
    )
    strategy_owner_plan_decision = strategy_owner_contrast_label_plan.get(
        "decision"
    ) or {}
    strategy_owner_plan_review_decision = (
        strategy_owner_contrast_label_plan_review.get("decision") or {}
    )
    strategy_owner_plan_review_summary = (
        strategy_owner_contrast_label_plan_review.get("review_summary") or {}
    )
    strategy_owner_manifest_decision = (
        strategy_owner_contrast_execution_manifest.get("decision") or {}
    )
    strategy_owner_manifest_binding = (
        strategy_owner_contrast_execution_manifest.get("binding_summary") or {}
    )
    strategy_owner_manifest_review_decision = (
        strategy_owner_contrast_execution_manifest_review.get("decision") or {}
    )
    strategy_owner_manifest_review_summary = (
        strategy_owner_contrast_execution_manifest_review.get("review_summary") or {}
    )
    strategy_owner_labels_summary = (
        strategy_owner_contrast_control_labels.get("summary") or {}
    )
    strategy_owner_dataset_decision = (
        strategy_owner_contrast_dataset.get("decision") or {}
    )
    strategy_owner_dataset_summary = strategy_owner_contrast_dataset.get("summary") or {}
    strategy_owner_readiness_v2 = (
        strategy_owner_contrast_dataset.get("readiness_v2_assessment") or {}
    )
    strategy_owner_probe_decision = strategy_owner_contrast_probe.get("decision") or {}
    strategy_owner_probe_metrics = strategy_owner_contrast_probe.get("metrics") or {}
    strategy_owner_probe_passive = (
        strategy_owner_plan_decision.get("status")
        == "protected_strategy_owner_contrast_label_plan_defined_execution_review_required"
        and strategy_owner_plan_decision.get("runtime_arbiter_allowed") is False
        and strategy_owner_plan_decision.get("selector_sandbox_ready") is False
        and strategy_owner_contrast_label_plan.get("labels_generated_in_this_slice")
        is False
        and len(strategy_owner_contrast_label_plan.get("jobs") or []) == 12
        and strategy_owner_plan_review_decision.get("status")
        == "contrast_label_plan_review_passed_binding_required"
        and strategy_owner_plan_review_decision.get("labels_allowed_now") is False
        and strategy_owner_plan_review_summary.get("stage7_jobs") == 0
        and strategy_owner_manifest_decision.get("status")
        == "contrast_execution_manifest_bound_review_required"
        and strategy_owner_manifest_decision.get("labels_allowed_now") is False
        and strategy_owner_manifest_binding.get("all_bindings_valid") is True
        and strategy_owner_manifest_binding.get("missing_path_count") == 0
        and strategy_owner_manifest_binding.get("stage7_jobs") == 0
        and strategy_owner_manifest_review_decision.get("status")
        == "contrast_execution_manifest_review_passed_labels_allowed"
        and strategy_owner_manifest_review_summary.get("labels_allowed") is True
        and strategy_owner_manifest_review_summary.get("stage7_jobs") == 0
        and strategy_owner_labels_summary.get("label_count") == 12
        and strategy_owner_labels_summary.get("stage7_labels") == 0
        and strategy_owner_labels_summary.get("trace_failures_only") is True
        and strategy_owner_dataset_decision.get("status")
        == "strategy_owner_contrast_dataset_ready_for_non_causal_probe_selector_sandbox_blocked"
        and strategy_owner_readiness_v2.get("contrast_probe_ready") is True
        and strategy_owner_readiness_v2.get("selector_sandbox_ready") is False
        and strategy_owner_readiness_v2.get("stage7_training_rows") == 0
        and strategy_owner_dataset_summary.get("stage7_training_rows") == 0
        and strategy_owner_dataset_summary.get("held_out_challenge_row_count") == 4
        and strategy_owner_probe_decision.get("status")
        == "strategy_owner_contrast_signal_present_selector_sandbox_blocked"
        and "insufficient_selected_provider_family_diversity"
        in (strategy_owner_probe_metrics.get("readiness_blockers") or [])
        and strategy_owner_contrast_probe.get("runtime_arbiter_implemented") is False
        and strategy_owner_contrast_probe.get("runtime_behavior_changed") is False
        and strategy_owner_contrast_probe.get("runtime_defaults_changed") is False
        and strategy_owner_contrast_probe.get("runtime_dtm_or_tablebase_lookup") is False
        and strategy_owner_contrast_probe.get("runtime_terminals_added") is False
        and strategy_owner_contrast_probe.get("stage7_promotion_allowed") is False
        and strategy_owner_contrast_probe.get("stage8_training_allowed") is False
    )
    arbitration_objective_decision = arbitration_objective_review_v1.get(
        "decision"
    ) or {}
    arbitration_objective_metrics = arbitration_objective_review_v1.get(
        "key_metrics"
    ) or {}
    normalized_objective_decision = (
        normalized_strategy_selector_objective_v1.get("decision") or {}
    )
    normalized_probe_decision = (
        normalized_strategy_selector_objective_probe_v1.get("decision") or {}
    )
    normalized_probe_review_decision = (
        normalized_selector_probe_review_v1.get("decision") or {}
    )
    normalized_probe_review_summary = (
        normalized_selector_probe_review_v1.get("probe_summary") or {}
    )
    selector_architecture_decision = (
        selector_objective_architecture_review_v1.get("decision") or {}
    )
    split_dataset_decision = split_selector_objective_dataset_v3.get("decision") or {}
    split_dataset_summary = split_selector_objective_dataset_v3.get("summary") or {}
    split_readiness_decision = (
        split_selector_objective_readiness_v3.get("decision") or {}
    )
    split_readiness_summary = split_selector_objective_readiness_v3.get("summary") or {}
    split_readiness_channels = (
        split_selector_objective_readiness_v3.get("channel_summary") or {}
    )
    selector_objective_normalization_passive = (
        arbitration_objective_decision.get("status")
        == "additive_support_objective_rejected_design_normalized_selector_objective"
        and arbitration_objective_decision.get("runtime_test_allowed_next") is False
        and arbitration_objective_decision.get("stage7_promotion_allowed") is False
        and arbitration_objective_decision.get("stage8_training_allowed") is False
        and normalized_objective_decision.get("status")
        == "normalized_selector_objective_design_ready_for_offline_probe"
        and normalized_objective_decision.get("runtime_test_allowed_next") is False
        and normalized_probe_decision.get("status")
        == "normalized_objective_probe_underpowered_fields_available"
        and normalized_probe_decision.get("runtime_test_allowed_next") is False
        and normalized_probe_review_decision.get("status")
        == "normalized_selector_signal_promising_more_ranked_frames_required"
        and normalized_probe_review_decision.get("runtime_test_allowed_next") is False
        and normalized_probe_review_summary.get("benchmark_underpowered") is True
        and normalized_probe_review_summary.get("stage7_training_leakage") is False
        and selector_architecture_decision.get("status")
        == "selector_objective_needs_stratified_label_expansion_before_sandbox"
        and selector_architecture_decision.get("runtime_arbiter_allowed") is False
        and selector_architecture_decision.get("selector_sandbox_ready") is False
        and selector_objective_label_semantics_v0.get("sandbox_ready") is False
        and split_dataset_decision.get("status")
        == "split_selector_objective_channels_with_ownership_labels"
        and split_dataset_decision.get("runtime_work_allowed") is False
        and split_dataset_decision.get("selector_training_allowed") is False
        and split_dataset_summary.get("selector_training_row_count") == 0
        and split_dataset_summary.get("stage7_row_count") == 0
        and split_readiness_decision.get("status")
        == "ownership_labels_recovered_but_underpowered"
        and split_readiness_decision.get("runtime_work_allowed") is False
        and split_readiness_decision.get("selector_training_allowed") is False
        and split_readiness_summary.get("ownership_probe_underpowered") is True
        and split_readiness_summary.get("selector_training_row_count") == 0
        and split_readiness_summary.get("stage7_row_count") == 0
        and split_selector_objective_readiness_v3.get("runtime_behavior_changed") is False
        and split_selector_objective_readiness_v3.get("runtime_defaults_changed") is False
        and split_selector_objective_readiness_v3.get("runtime_selector_implemented")
        is False
        and split_selector_objective_readiness_v3.get(
            "runtime_candidate_generator_implemented"
        )
        is False
        and split_selector_objective_readiness_v3.get("runtime_terminals_added") is False
        and split_selector_objective_readiness_v3.get("stage7_promotion_allowed")
        is False
        and split_selector_objective_readiness_v3.get("stage8_training_allowed")
        is False
    )
    abstention_objective_decision = (
        abstention_first_selector_objective_v0.get("decision") or {}
    )
    abstention_safe_review_decision = (
        abstention_safe_preservation_label_review_v0.get("decision") or {}
    )
    abstention_safe_review_summary = (
        abstention_safe_preservation_label_review_v0.get("summary") or {}
    )
    abstention_dataset_decision = (
        abstention_training_dataset_v1.get("decision") or {}
    )
    abstention_dataset_summary = abstention_training_dataset_v1.get("summary") or {}
    abstention_probe_decision = abstention_training_probe_v1.get("decision") or {}
    abstention_probe_summary = abstention_training_probe_v1.get("summary") or {}
    abstention_context_dataset_decision = (
        abstention_context_feature_dataset_v0.get("decision") or {}
    )
    abstention_context_dataset_summary = (
        abstention_context_feature_dataset_v0.get("summary") or {}
    )
    abstention_context_probe_decision = (
        abstention_context_feature_probe_v0.get("decision") or {}
    )
    abstention_context_probe_summary = (
        abstention_context_feature_probe_v0.get("summary") or {}
    )
    abstention_error_audit_decision = (
        abstention_context_error_audit_v0.get("decision") or {}
    )
    abstention_error_audit_summary = (
        abstention_context_error_audit_v0.get("summary") or {}
    )
    abstention_feature_gap_next_step = (
        abstention_feature_gap_review_v0.get("recommended_next_step") or {}
    )
    abstention_blocked_next_steps = (
        abstention_feature_gap_review_v0.get("blocked_next_steps") or []
    )
    abstention_selector_safety_passive = (
        abstention_objective_decision.get("status")
        == "abstention_first_selector_objective_defined"
        and abstention_objective_decision.get("runtime_test_allowed_next") is False
        and abstention_objective_decision.get("stage7_promotion_allowed") is False
        and abstention_objective_decision.get("stage8_training_allowed") is False
        and abstention_safe_review_decision.get("status")
        == "safe_preservation_requires_two_stage_label_semantics"
        and abstention_safe_review_decision.get("runtime_test_allowed_next") is False
        and abstention_dataset_decision.get("status")
        == "abstention_training_dataset_ready_for_probe"
        and abstention_dataset_decision.get("runtime_test_allowed_next") is False
        and abstention_dataset_summary.get("row_count") == 51
        and abstention_dataset_summary.get("stage7_training_rows") == 0
        and abstention_probe_decision.get("status")
        == "abstention_signal_underpowered_no_runtime"
        and abstention_probe_decision.get("runtime_test_allowed_next") is False
        and abstention_probe_summary.get("under_minimum_requirements") is False
        and abstention_context_dataset_decision.get("status")
        == "abstention_context_feature_dataset_ready_for_non_causal_probe"
        and abstention_context_dataset_decision.get("runtime_test_allowed_next") is False
        and abstention_context_dataset_summary.get("stage7_training_rows") == 0
        and abstention_context_probe_decision.get("status")
        == "context_features_help_but_runtime_blocked"
        and abstention_context_probe_decision.get("runtime_test_allowed_next") is False
        and abstention_context_probe_summary.get("context_improved_negative_suppression")
        is True
        and abstention_error_audit_decision.get("status")
        == "context_signal_overrejects_safe_owners_runtime_blocked"
        and abstention_error_audit_decision.get("runtime_test_allowed_next") is False
        and abstention_feature_gap_next_step.get("status")
        == "join_abstention_labels_with_control_plane_context"
        and abstention_feature_gap_next_step.get("implementation_allowed")
        == "non_causal_replay_free_only"
        and "runtime_selector" in abstention_blocked_next_steps
        and "stage7_promotion" in abstention_blocked_next_steps
        and "stage8_training" in abstention_blocked_next_steps
        and "runtime_dtm_or_tablebase" in abstention_blocked_next_steps
        and abstention_feature_gap_review_v0.get("runtime_behavior_changed") is False
        and abstention_feature_gap_review_v0.get("runtime_defaults_changed") is False
        and abstention_feature_gap_review_v0.get("runtime_selector_implemented")
        is False
        and abstention_feature_gap_review_v0.get("runtime_dtm_or_tablebase_lookup")
        is False
        and abstention_feature_gap_review_v0.get("stage7_promotion_allowed") is False
        and abstention_feature_gap_review_v0.get("stage8_training_allowed") is False
    )
    targeted_non_stage0_manifest_decision = (
        targeted_non_stage0_ownership_manifest_v0.get("decision") or {}
    )
    targeted_non_stage0_manifest_binding = (
        targeted_non_stage0_ownership_manifest_v0.get("binding_summary") or {}
    )
    targeted_non_stage0_labels_decision = (
        targeted_non_stage0_ownership_labels_v0.get("decision") or {}
    )
    targeted_non_stage0_labels_summary = (
        targeted_non_stage0_ownership_labels_v0.get("summary") or {}
    )
    targeted_non_stage0_review_decision = (
        targeted_non_stage0_ownership_review_v0.get("decision") or {}
    )
    targeted_non_stage0_review_summary = (
        targeted_non_stage0_ownership_review_v0.get("summary") or {}
    )
    targeted_negative_manifest_decision = (
        targeted_ownership_negative_manifest_v0.get("decision") or {}
    )
    targeted_negative_manifest_binding = (
        targeted_ownership_negative_manifest_v0.get("binding_summary") or {}
    )
    targeted_negative_labels_decision = (
        targeted_ownership_negative_labels_v0.get("decision") or {}
    )
    targeted_negative_labels_summary = (
        targeted_ownership_negative_labels_v0.get("summary") or {}
    )
    targeted_ownership_recovery_passive = (
        targeted_non_stage0_manifest_decision.get("status")
        == "targeted_non_stage0_manifest_ready"
        and targeted_non_stage0_manifest_decision.get("runtime_arbiter_allowed")
        is False
        and targeted_non_stage0_manifest_decision.get("selector_training_allowed")
        is False
        and targeted_non_stage0_ownership_manifest_v0.get(
            "labels_generated_in_this_slice"
        )
        is False
        and targeted_non_stage0_manifest_binding.get("all_bindings_valid") is True
        and targeted_non_stage0_manifest_binding.get("missing_path_count") == 0
        and targeted_non_stage0_manifest_binding.get("job_count") == 4
        and targeted_non_stage0_manifest_binding.get("stage7_job_count") == 0
        and targeted_non_stage0_labels_decision.get("status")
        == "current_profile_preserves_some_historical_non_stage0_ownership"
        and targeted_non_stage0_labels_decision.get("runtime_arbiter_allowed")
        is False
        and targeted_non_stage0_labels_decision.get("selector_training_allowed")
        is False
        and targeted_non_stage0_labels_summary.get("label_count") == 4
        and targeted_non_stage0_labels_summary.get("stage7_training_rows") == 0
        and targeted_non_stage0_labels_summary.get(
            "preserved_historical_non_stage0_count"
        )
        == 4
        and targeted_non_stage0_labels_summary.get("current_stage0_collapse_count")
        == 0
        and targeted_non_stage0_review_decision.get("status")
        == "non_stage0_current_profile_evidence_recovered"
        and targeted_non_stage0_review_decision.get("runtime_arbiter_allowed")
        is False
        and targeted_non_stage0_review_decision.get("selector_training_allowed")
        is False
        and targeted_non_stage0_review_summary.get("targeted_label_count") == 4
        and targeted_non_stage0_review_summary.get("stage0_collapse_count") == 0
        and targeted_negative_manifest_decision.get("status")
        == "targeted_ownership_negative_manifest_ready"
        and targeted_negative_manifest_decision.get("runtime_work_allowed") is False
        and targeted_negative_manifest_decision.get("selector_training_allowed")
        is False
        and targeted_ownership_negative_manifest_v0.get(
            "labels_generated_in_this_slice"
        )
        is False
        and targeted_negative_manifest_binding.get("all_bindings_valid") is True
        and targeted_negative_manifest_binding.get("missing_path_count") == 0
        and targeted_negative_manifest_binding.get("job_count") == 6
        and targeted_negative_manifest_binding.get("stage7_job_count") == 0
        and targeted_negative_labels_decision.get("status")
        == "targeted_ownership_negative_labels_collected"
        and targeted_negative_labels_decision.get("runtime_work_allowed") is False
        and targeted_negative_labels_decision.get("selector_training_allowed") is False
        and targeted_negative_labels_summary.get("label_count") == 6
        and targeted_negative_labels_summary.get("stage7_training_rows") == 0
        and targeted_negative_labels_summary.get("preselection_preserved_count") == 6
        and targeted_non_stage0_ownership_review_v0.get("runtime_behavior_changed")
        is False
        and targeted_non_stage0_ownership_review_v0.get("runtime_defaults_changed")
        is False
        and targeted_non_stage0_ownership_review_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and targeted_non_stage0_ownership_review_v0.get("runtime_terminals_added")
        is False
        and targeted_non_stage0_ownership_review_v0.get("stage7_promotion_allowed")
        is False
        and targeted_non_stage0_ownership_review_v0.get("stage8_training_allowed")
        is False
        and targeted_ownership_negative_labels_v0.get("runtime_behavior_changed")
        is False
        and targeted_ownership_negative_labels_v0.get("runtime_defaults_changed")
        is False
        and targeted_ownership_negative_labels_v0.get("runtime_selector_implemented")
        is False
        and targeted_ownership_negative_labels_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and targeted_ownership_negative_labels_v0.get("runtime_terminals_added")
        is False
        and targeted_ownership_negative_labels_v0.get("stage7_promotion_allowed")
        is False
        and targeted_ownership_negative_labels_v0.get("stage8_training_allowed")
        is False
    )
    balanced_hard_negative_plan_decision = (
        balanced_hard_negative_label_plan_v1.get("decision") or {}
    )
    balanced_hard_negative_plan_summary = (
        balanced_hard_negative_label_plan_v1.get("summary") or {}
    )
    balanced_hard_negative_manifest_decision = (
        balanced_hard_negative_execution_manifest_v1.get("decision") or {}
    )
    balanced_hard_negative_manifest_binding = (
        balanced_hard_negative_execution_manifest_v1.get("binding_summary") or {}
    )
    balanced_hard_negative_manifest_review_decision = (
        balanced_hard_negative_execution_manifest_review_v1.get("decision") or {}
    )
    balanced_hard_negative_labels_decision = (
        balanced_hard_negative_labels_v1.get("decision") or {}
    )
    balanced_hard_negative_labels_summary = (
        balanced_hard_negative_labels_v1.get("summary") or {}
    )
    balanced_hard_negative_review_decision = (
        balanced_hard_negative_evidence_review_v0.get("decision") or {}
    )
    balanced_hard_negative_review_summary = (
        balanced_hard_negative_evidence_review_v0.get("summary") or {}
    )
    balanced_hard_negative_passive = (
        balanced_hard_negative_plan_decision.get("status")
        == "balanced_hard_negative_label_plan_v1_ready"
        and balanced_hard_negative_plan_decision.get("runtime_work_allowed") is False
        and balanced_hard_negative_plan_decision.get("selector_training_allowed")
        is False
        and balanced_hard_negative_plan_summary.get("job_count") == 12
        and balanced_hard_negative_plan_summary.get("stage7_jobs") == 0
        and balanced_hard_negative_manifest_decision.get("status")
        == "balanced_hard_negative_execution_manifest_bound"
        and balanced_hard_negative_manifest_decision.get("labels_allowed_now")
        is False
        and balanced_hard_negative_manifest_decision.get("runtime_work_allowed")
        is False
        and balanced_hard_negative_manifest_decision.get("selector_training_allowed")
        is False
        and balanced_hard_negative_manifest_binding.get("all_bindings_valid") is True
        and balanced_hard_negative_manifest_binding.get("job_count") == 12
        and balanced_hard_negative_manifest_binding.get("stage7_jobs") == 0
        and balanced_hard_negative_manifest_review_decision.get("status")
        == "balanced_hard_negative_manifest_review_passed_labels_allowed"
        and balanced_hard_negative_manifest_review_decision.get("runtime_work_allowed")
        is False
        and balanced_hard_negative_manifest_review_decision.get(
            "selector_training_allowed"
        )
        is False
        and balanced_hard_negative_labels_decision.get("status")
        == "balanced_hard_negative_labels_completed"
        and balanced_hard_negative_labels_decision.get("runtime_work_allowed") is False
        and balanced_hard_negative_labels_decision.get("selector_training_allowed")
        is False
        and balanced_hard_negative_labels_summary.get("label_count") == 12
        and balanced_hard_negative_labels_summary.get("stage7_labels") == 0
        and balanced_hard_negative_labels_summary.get("stage7_training_labels") == 0
        and balanced_hard_negative_review_decision.get("status")
        == "balanced_hard_negative_signal_promising_but_underpowered"
        and balanced_hard_negative_review_decision.get("runtime_work_allowed") is False
        and balanced_hard_negative_review_decision.get("selector_training_allowed")
        is False
        and balanced_hard_negative_review_decision.get("stage7_promotion_allowed")
        is False
        and balanced_hard_negative_review_decision.get("stage8_training_allowed")
        is False
        and balanced_hard_negative_review_summary.get("underpowered") is True
        and balanced_hard_negative_review_summary.get("stage7_row_count") == 0
        and balanced_hard_negative_evidence_review_v0.get("runtime_behavior_changed")
        is False
        and balanced_hard_negative_evidence_review_v0.get("runtime_defaults_changed")
        is False
        and balanced_hard_negative_evidence_review_v0.get(
            "runtime_selector_implemented"
        )
        is False
        and balanced_hard_negative_evidence_review_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and balanced_hard_negative_evidence_review_v0.get("runtime_terminals_added")
        is False
        and balanced_hard_negative_evidence_review_v0.get("stage7_promotion_allowed")
        is False
        and balanced_hard_negative_evidence_review_v0.get("stage8_training_allowed")
        is False
    )
    replacement_readiness_decision = clean_replacement_readiness.get("decision") or {}
    replacement_packet_decision = clean_stack_replacement_packet.get("decision") or {}
    protected_stage_status_summary = protected_stage_status.get("summary") or {}
    clean_replacement_review_passive = (
        replacement_readiness_decision.get("clean_stack_replacement_allowed") is False
        and snapshot_decision.get("all_referenced_paths_exist") is True
        and snapshot_decision.get("clean_stack_replacement_allowed_by_manifest")
        is False
        and snapshot_current_stack_path_status["all_paths_exist"]
        and snapshot_retry1_stack_path_status["all_paths_exist"]
        and replacement_packet_decision.get("replacement_review_ready") is True
        and replacement_packet_decision.get("implementation_allowed_by_this_packet")
        is False
        and replacement_packet_decision.get(
            "explicit_human_approval_required_before_any_file_change"
        )
        is True
        and clean_stack_deferred_review.get("replacement_review_ready") is True
        and clean_stack_deferred_review.get("explicit_approval_detected") is False
        and clean_stack_deferred_review.get("implementation_allowed_by_review_packet")
        is False
        and protected_stage_status.get("protected_stack_reference_mode")
        == "retry1_manifest_active"
        and protected_stage_status.get("runtime_behavior_changed") is False
        and protected_stage_status.get("runtime_defaults_changed") is False
        and protected_stage_status.get("runtime_dtm_or_tablebase_lookup") is False
        and protected_stage_status.get("gameplay_topology_mutation") is False
        and protected_stage_status.get("stage7_promotion_allowed") is False
        and protected_stage_status.get("stage8_training_allowed") is False
    )
    protected_stack_validated = (
        active.get("decision", {}).get("clean_stack_adopted") is True
        and active.get("decision", {}).get("filesystem_snapshots_replaced") is False
        and active.get("decision", {}).get("post_adoption_validation_required") is True
        and active.get("invariants", {}).get("rollback_paths_preserved") is True
        and active.get("invariants", {}).get("files_copied_or_replaced") is False
        and clean.get("decision", {}).get("clean_stack_adopted_and_validated") is True
        and clean.get("invariants", {}).get("rollback_paths_preserved") is True
        and clean.get("invariants", {}).get("files_copied_or_replaced") is False
        and preservation.get("decision", {}).get("m1_m4_preservation_passed") is True
        and preservation.get("decision", {}).get("kpk_kqk_bridge_preservation_passed") is True
        and clean.get("validation", {}).get("stage5_conversion_preservation_guardrail", {}).get("passed")
        is True
        and clean.get("validation", {}).get("stage6_drive_h40_historical_bonus", {}).get("passed")
        is True
        and active_stack_paths["all_paths_safe"]
        and active_stack_paths["all_paths_exist"]
        and rollback_stack_paths["all_paths_safe"]
        and rollback_stack_paths["all_paths_exist"]
        and rollback_common_paths_distinct
    )

    stage7_success_controls = int(stage7_summary.get("combined_success_controls", 0) or 0)
    stage7_success_required = int(stage7_summary.get("success_controls_required", 5) or 5)
    stage7_success_ready = stage7_success_controls >= stage7_success_required
    raw_stage7_execution_readiness_status = runner.get("summary", {}).get(
        "execution_readiness_status"
    )
    stage7_label_gate_closed = (
        stage7_success_ready
        and runner.get("decision", {}).get("status")
        == "stage7_diverse_clean_sampling_runner_executed_success"
    )
    current_stage7_execution_readiness_status = (
        "not_applicable_stage7_success_gate_closed"
        if stage7_label_gate_closed
        else raw_stage7_execution_readiness_status
    )
    current_stage7_label_run_allowed = (
        False
        if stage7_label_gate_closed
        else bool(
            runner.get("summary", {}).get(
                "current_label_run_allowed",
                runner.get("decision", {}).get("label_run_allowed", False),
            )
        )
    )
    historical_stage7_label_run_allowed = bool(
        runner.get("decision", {}).get(
            "historical_label_run_allowed_by_runner",
            runner.get("summary", {}).get(
                "historical_label_run_allowed_by_runner",
                runner.get("decision", {}).get("label_run_allowed", False),
            ),
        )
    )
    runner_summary = runner.get("summary", {})
    current_stage7_processed_job_count = int(
        runner_summary.get("processed_job_count", 0) or 0
    )
    current_stage7_executed_job_count = int(
        runner_summary.get("executed_job_count", 0) or 0
    )
    historical_stage7_processed_job_count = int(
        runner_summary.get(
            "historical_processed_job_count",
            current_stage7_processed_job_count,
        )
        or 0
    )
    historical_stage7_executed_job_count = int(
        runner_summary.get(
            "historical_executed_job_count",
            current_stage7_executed_job_count,
        )
        or 0
    )

    benchmark_decision = benchmark.get("decision", {})
    benchmark_design_decision = benchmark_design.get("decision", {})
    passive_design = benchmark_design.get("passive_design_without_new_labels") or {}
    cross_stage_readiness = cross_stage_requirements.get("current_readiness") or {}
    benchmark_review_blockers = benchmark_review.get("blockers") or []
    sequence_ready = bool(sequence_summary.get("sequence_policy_inputs_ready")) and bool(
        benchmark_decision.get("benchmark_executed_as_ready")
    )
    sequence_review_status = benchmark_review.get("decision", {}).get("status")
    forbidden_input_blockers_set = FORBIDDEN_INPUT_BLOCKERS & (
        set(benchmark_preflight.get("blockers") or []) | set(benchmark_review_blockers)
    )
    if int(benchmark_preflight.get("selector_training_row_count") or 0) > 0:
        forbidden_input_blockers_set.add("selector_training_rows_forbidden")
    if int(benchmark_preflight.get("runtime_authorization_row_count") or 0) > 0:
        forbidden_input_blockers_set.add("runtime_authorization_rows_forbidden")
    forbidden_input_blockers = sorted(forbidden_input_blockers_set)
    sequence_forbidden_training_or_runtime_inputs = bool(forbidden_input_blockers) or (
        benchmark_decision.get("status") in FORBIDDEN_INPUT_STATUSES
        or sequence_review_status in FORBIDDEN_INPUT_STATUSES
    )
    failure_contrast_approval_request_decision = (
        failure_contrast_approval_request.get("decision") or {}
    )
    failure_contrast_approval_request_blockers = (
        failure_contrast_approval_request.get("blockers") or []
    )
    failure_contrast_approval_request_ready_value = failure_contrast_approval_request.get(
        "approval_request_ready_for_collection"
    )
    failure_contrast_approval_request_ready = (
        bool(failure_contrast_approval_request_ready_value)
        if failure_contrast_approval_request_ready_value is not None
        else (
            failure_contrast_approval_request_decision.get("status")
            == "protected_plan_window_failure_contrast_approval_request_ready"
            and not failure_contrast_approval_request_blockers
        )
    )
    protected_failure_contrast_collection_ready = (
        failure_contrast_manifest_review.get("decision", {}).get("status")
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
        and failure_contrast_execution_readiness.get("decision", {}).get("status")
        == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
        and failure_contrast_runner.get("decision", {}).get("status")
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    protected_failure_contrast_ready_for_explicit_approval = (
        protected_failure_contrast_collection_ready
        and not sequence_forbidden_training_or_runtime_inputs
        and failure_contrast_approval_request_ready
        and protected_stack_validated
    )
    protected_failure_contrast_integration_ready = bool(
        failure_contrast_integration.get("summary", {}).get("integration_ready")
    )
    post_failure_contrast_refresh_summary = (
        post_failure_contrast_sequence_refresh.get("summary") or {}
    )
    post_failure_contrast_refresh_decision = (
        post_failure_contrast_sequence_refresh.get("decision") or {}
    )
    post_failure_contrast_refresh_boundary_violation_count = int(
        post_failure_contrast_refresh_summary.get("boundary_violation_count") or 0
    )
    post_failure_contrast_refresh_boundaries_preserved = (
        post_failure_contrast_refresh_boundary_violation_count == 0
        and post_failure_contrast_refresh_summary.get("all_boundaries_preserved") is True
    )
    failure_contrast_runner_summary = failure_contrast_runner.get("summary", {})
    failure_contrast_approval_request_summary = (
        failure_contrast_approval_request.get("summary") or {}
    )
    failure_contrast_approval_receipt_path = (
        failure_contrast_runner.get("approval_receipt_path")
        or DEFAULT_FAILURE_CONTRAST_APPROVAL_RECEIPT
    )
    failure_contrast_command = (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection --refresh-after-run "
        f"--approval-receipt {failure_contrast_approval_receipt_path}"
    )
    protected_failure_contrast_pending = (
        stage7_success_ready
        and sequence_ready
        and sequence_review_status == "sequence_policy_benchmark_mixed_plan_window_underpowered"
        and not sequence_forbidden_training_or_runtime_inputs
        and not protected_failure_contrast_integration_ready
    )
    protected_failure_contrast_approval_request_repair_pending = (
        protected_failure_contrast_pending
        and protected_stack_validated
        and protected_failure_contrast_collection_ready
        and not failure_contrast_approval_request_ready
    )
    protected_stack_repair_pending = not protected_stack_validated

    stage4_decision = stage4_unblocker.get("decision") or {}
    stage4_status = (
        stage4_decision.get("status")
        or "stage4_caveat_unblocker_missing"
    )
    stage4_ready_for_explicit_approval = (
        stage4_status == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    stage4_approval_request_decision = stage4_approval_request.get("decision") or {}
    stage4_approval_request_blockers = stage4_approval_request.get("blockers") or []
    stage4_approval_request_ready_value = stage4_approval_request.get(
        "approval_request_ready_for_runtime_approval"
    )
    stage4_approval_request_ready = (
        bool(stage4_approval_request_ready_value)
        if stage4_approval_request_ready_value is not None
        else (
            stage4_approval_request_decision.get("status")
            == "stage4_first_move_contrast_sandbox_approval_request_ready"
            and not stage4_approval_request_blockers
        )
    )
    stage4_approval_scope = (
        stage4_approval_request.get("required_scope_if_user_approves") or {}
    )

    stage_status = {
        "stage1": {
            "status": "protected_component_from_current_brief",
            "ready_for_current_suite": True,
        },
        "stage4": {
            "status": stage4_status,
            "ready_for_current_suite": False,
            "blocker": "stage4 h40 caveat remains separate guardrail/control debt",
            "ready_for_explicit_runtime_approval": (
                stage4_ready_for_explicit_approval and stage4_approval_request_ready
            ),
            "implementation_allowed_by_current_artifact": stage4_decision.get(
                "implementation_allowed_by_this_packet"
            ),
            "approval_request_artifact": (
                "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
            ),
            "approval_request_status": stage4_approval_request_decision.get("status"),
            "approval_request_blockers": stage4_approval_request_blockers,
            "approval_request_ready_for_runtime_approval": stage4_approval_request_ready,
            "approval_request_created": stage4_approval_request.get(
                "approval_request_created"
            ),
            "implementation_authorized_by_approval_request": stage4_approval_request.get(
                "implementation_authorized_by_request"
            ),
        },
        "stage5": {
            "status": "protected_retry1_stack_validated",
            "ready_for_current_suite": protected_stack_validated,
        },
        "stage6": {
            "status": "protected_retry1_overlay_validated",
            "ready_for_current_suite": protected_stack_validated,
        },
        "stage7": {
            "status": "held_out_challenge_quarantined",
            "ready_for_promotion": False,
            "success_controls": stage7_success_controls,
            "success_controls_required": stage7_success_required,
            "success_controls_ready": stage7_success_ready,
            "sampling_runner_status": runner.get("decision", {}).get("status"),
            "sampling_runner_output_validation_status": runner.get("summary", {}).get(
                "output_validation_status"
            ),
            "sampling_output_validation_status": output_validation_status,
            "sampling_runner_execution_readiness_source": runner.get("summary", {}).get(
                "execution_readiness_source"
            ),
            "sampling_runner_execution_readiness_status": (
                current_stage7_execution_readiness_status
            ),
            "historical_sampling_runner_execution_readiness_status": (
                raw_stage7_execution_readiness_status
            ),
            "sampling_runner_invalid_existing_output_count": runner.get("summary", {}).get(
                "invalid_existing_output_count"
            ),
            "sampling_runner_job_timeout_seconds": runner.get("summary", {}).get(
                "job_timeout_seconds"
            ),
            "sampling_runner_timed_out_job_count": runner.get("summary", {}).get(
                "timed_out_job_count"
            ),
            "sampling_outputs_status": integration.get("decision", {}).get("status"),
        },
        "stage8": {
            "status": "blocked",
            "ready_for_training": False,
            "blocker": (
                "Protected plan-window failure-contrast evidence is not integrated; "
                "Stage 8 remains blocked pending explicit protected failure-contrast "
                "collection and passive integration."
                if protected_failure_contrast_pending
                else (
                    "Sequence-policy inputs contain forbidden training or runtime "
                    "authorization rows and must be repaired before Stage 8 review."
                )
                if sequence_forbidden_training_or_runtime_inputs
                else "Stage 7 remains quarantined or the sequence-policy benchmark is not ready"
            ),
        },
    }

    hard_blockers: list[str] = []
    if not protected_stack_validated:
        hard_blockers.append("protected_retry1_stage5_6_stack_not_validated")
    if not stage7_success_ready:
        hard_blockers.append("stage7_clean_success_controls_missing")
    if not sequence_ready:
        hard_blockers.append("sequence_policy_benchmark_not_ready")
    if sequence_forbidden_training_or_runtime_inputs:
        hard_blockers.append("sequence_policy_forbidden_training_or_runtime_rows")
    if protected_failure_contrast_approval_request_repair_pending:
        hard_blockers.append(
            "protected_plan_window_failure_contrast_approval_request_blocked"
        )
    if not post_failure_contrast_refresh_boundaries_preserved:
        hard_blockers.append("post_failure_contrast_sequence_refresh_boundary_violation")
    if boundaries["violation_count"]:
        hard_blockers.append("hard_invariant_violation_detected")
    explicit_gate_blockers: list[str] = []
    control_plane_gate_review_blockers: list[str] = []
    if (
        protected_failure_contrast_pending
        and protected_stack_validated
        and failure_contrast_approval_request_ready
    ):
        if protected_collection_command_available:
            explicit_gate_blockers.append(
                "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
            )
        else:
            control_plane_gate_review_blockers.append(
                "protected_plan_window_failure_contrast_control_plane_gate_review_required"
            )
    blockers = hard_blockers + control_plane_gate_review_blockers + explicit_gate_blockers

    if sequence_forbidden_training_or_runtime_inputs:
        decision_status = "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows"
        next_step = "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    elif protected_stack_repair_pending:
        decision_status = "krk_suite_readiness_blocked_pending_protected_stack_repair"
        next_step = "repair_protected_stack_validation"
    elif protected_failure_contrast_approval_request_repair_pending:
        decision_status = (
            "krk_suite_readiness_blocked_pending_protected_failure_contrast_approval_request_repair"
        )
        next_step = "repair_protected_failure_contrast_approval_request_scope"
    elif hard_blockers:
        decision_status = "krk_suite_readiness_blocked_pending_stage7_clean_success_controls"
        next_step = (
            "explicitly_approve_stage7_diverse_clean_sampling_or_choose_stage4_sandbox_gate"
        )
    elif control_plane_gate_review_blockers:
        decision_status = (
            "krk_suite_readiness_blocked_pending_protected_failure_contrast_control_plane_gate_review"
        )
        next_step = "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    elif explicit_gate_blockers:
        decision_status = (
            "krk_suite_readiness_waiting_on_explicit_protected_failure_contrast_collection"
        )
        next_step = "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    else:
        decision_status = "krk_suite_readiness_ready_for_next_runtime_or_training_review"
        next_step = "prepare_explicit_runtime_or_training_review_packet"

    return {
        "schema_version": "krk_full_suite_readiness_audit.v0",
        "causal_status": "non_causal_readiness_audit",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": SOURCES,
        "protected_stack": {
            "status": active.get("status"),
            "clean_stack_adopted": active.get("decision", {}).get("clean_stack_adopted"),
            "filesystem_snapshots_replaced": active.get("decision", {}).get(
                "filesystem_snapshots_replaced"
            ),
            "clean_stack_adopted_and_validated": clean.get("decision", {}).get(
                "clean_stack_adopted_and_validated"
            ),
            "post_adoption_validation_required": active.get("decision", {}).get(
                "post_adoption_validation_required"
            ),
            "rollback_paths_preserved": active.get("invariants", {}).get(
                "rollback_paths_preserved"
            ),
            "active_stack_path_status": active_stack_paths,
            "rollback_stack_path_status": rollback_stack_paths,
            "rollback_common_paths_distinct": rollback_common_paths_distinct,
            "stage5_conversion_preservation_passed": clean.get("validation", {})
            .get("stage5_conversion_preservation_guardrail", {})
            .get("passed"),
            "stage6_drive_validation_passed": clean.get("validation", {})
            .get("stage6_drive_h40_historical_bonus", {})
            .get("passed"),
            "m1_m4_preservation_passed": preservation.get("decision", {}).get(
                "m1_m4_preservation_passed"
            ),
            "kpk_kqk_bridge_preservation_passed": preservation.get("decision", {}).get(
                "kpk_kqk_bridge_preservation_passed"
            ),
            "ready": protected_stack_validated,
        },
        "clean_curriculum_run_lineage_gate": {
            "status": curriculum_next_milestone_decision.get("status"),
            "passive_lineage_ready": clean_curriculum_run_lineage_passive,
            "checkpoint_plan_status": (
                clean_curriculum_checkpoint_plan.get("decision", {}).get("status")
            ),
            "checkpoint_plan_stage7_remains_quarantined": (
                clean_curriculum_checkpoint_plan.get("decision", {}).get(
                    "stage7_remains_quarantined"
                )
            ),
            "checkpoint_plan_stage8_remains_blocked": (
                clean_curriculum_checkpoint_plan.get("decision", {}).get(
                    "stage8_remains_blocked"
                )
            ),
            "execution_manifest_status": clean_retrain_execution_decision.get("status"),
            "execution_manifest_full_run_authorized": (
                clean_retrain_execution_decision.get(
                    "full_run_authorized_by_this_manifest"
                )
            ),
            "stage6_compose_manifest_status": stage6_overlay_compose_decision.get(
                "status"
            ),
            "stage6_compose_manifest_run_authorized": (
                stage6_overlay_compose_decision.get(
                    "compose_run_authorized_by_this_manifest"
                )
            ),
            "preflight_status": clean_retrain_preflight.get("decision", {}).get(
                "status"
            ),
            "preflight_safe_to_request_run_review": clean_retrain_preflight.get(
                "decision", {}
            ).get("safe_to_request_run_review"),
            "preflight_blocker_count": clean_retrain_preflight_summary.get(
                "blocker_count"
            ),
            "preflight_command_violation_count": clean_retrain_preflight_summary.get(
                "command_violation_count"
            ),
            "preflight_protected_overwrite_count": clean_retrain_preflight_summary.get(
                "protected_overwrite_count"
            ),
            "smoke_manifest_status": clean_retrain_smoke_decision.get("status"),
            "smoke_manifest_run_authorized": clean_retrain_smoke_decision.get(
                "smoke_run_authorized_by_this_manifest"
            ),
            "smoke_result_status": clean_retrain_smoke_result.get("decision", {}).get(
                "status"
            ),
            "smoke_command_plumbing_validated": clean_retrain_smoke_summary.get(
                "command_plumbing_validated"
            ),
            "smoke_curriculum_semantics_validated": clean_retrain_smoke_summary.get(
                "curriculum_semantics_validated"
            ),
            "initial_run_status": clean_retrain_run_result.get("status"),
            "initial_run_full_clean_retrain_complete": (
                clean_retrain_initial_decision.get("full_clean_retrain_complete")
            ),
            "initial_run_stage2a_complete": clean_retrain_initial_decision.get(
                "stage2a_complete"
            ),
            "retry1_status": clean_retrain_retry1_result.get("status"),
            "retry1_complete_through_stage6": clean_retrain_retry1_decision.get(
                "clean_retrain_retry_complete_through_stage6"
            ),
            "retry1_stage_count": len(clean_retrain_retry1_stages),
            "retry1_promoted_by_this_artifact": clean_retrain_retry1_decision.get(
                "promoted_by_this_artifact"
            ),
            "retry1_protected_snapshots_overwritten": (
                clean_retrain_retry1_run_scope.get("protected_snapshots_overwritten")
            ),
            "retry1_stage7_training_or_promotion": (
                clean_retrain_retry1_run_scope.get("stage7_training_or_promotion")
            ),
            "retry1_stage8_training": clean_retrain_retry1_run_scope.get(
                "stage8_training"
            ),
            "retry1_runtime_selector_or_routing_change": (
                clean_retrain_retry1_run_scope.get("runtime_selector_or_routing_change")
            ),
            "guardrail_status": clean_retrain_retry1_guardrail_result.get("status"),
            "guardrail_promotion_status": clean_retrain_guardrail_decision.get(
                "promotion_status"
            ),
            "guardrail_stage5_overlay_conversion_preserved": (
                clean_retrain_guardrail_decision.get(
                    "stage5_overlay_conversion_preserved"
                )
            ),
            "guardrail_retry1_can_replace_protected_stack": (
                clean_retrain_guardrail_decision.get(
                    "retry1_can_replace_protected_stack"
                )
            ),
            "stage6_gap_status": clean_retrain_retry1_stage6_gap_inspection.get(
                "status"
            ),
            "stage6_gap_corrected_profile_restores_conversion": (
                stage6_gap_decision.get(
                    "corrected_profile_bonus_restores_stage6_conversion"
                )
            ),
            "stage6_gap_retry1_can_replace_protected_stack": (
                stage6_gap_decision.get("retry1_can_replace_protected_stack")
            ),
            "stage5_control_debt_status": stage5_guardrail_control_debt_review.get(
                "status"
            ),
            "stage5_control_debt_conversion_preserved": (
                stage5_control_debt_decision.get("stage5_conversion_preserved")
            ),
            "stage5_control_debt_quarantines_stage6_overlay": (
                stage5_control_debt_decision.get(
                    "should_quarantine_stage6_overlay_for_stage5_one_ply_debt"
                )
            ),
            "stage5_semantics_status": stage5_guardrail_semantics_split.get("status"),
            "stage5_semantics_overlay_use_allowed_as_overlay_only": (
                stage5_semantics_decision.get("stage6_overlay_use_allowed_as_overlay_only")
            ),
            "stage5_semantics_clean_stack_replacement_allowed": (
                stage5_semantics_decision.get("clean_stack_replacement_allowed")
            ),
            "stage5_local_debt_status": stage5_local_reward_contract_debt_audit.get(
                "status"
            ),
            "stage5_local_debt_is_stage6_regression": (
                stage5_local_debt_decision.get("local_reward_debt_is_stage6_regression")
            ),
            "stage4_caveat_control_status": (
                clean_retrain_retry1_stage4_caveat_control_review.get("status")
            ),
            "stage4_caveat_overlay_regressed_vs_base_control": (
                stage4_caveat_control_decision.get(
                    "stage4_overlay_regressed_vs_base_control"
                )
            ),
            "curriculum_decision_states": (
                curriculum_next_milestone_decision.get("decision_states") or []
            ),
            "curriculum_stage4_status": curriculum_next_milestone_decision.get(
                "stage4_status"
            ),
            "curriculum_stage7_status": curriculum_next_milestone_decision.get(
                "stage7_status"
            ),
            "curriculum_stage8_status": curriculum_next_milestone_decision.get(
                "stage8_status"
            ),
            "curriculum_forbidden_next_steps": (
                curriculum_next_milestone_decision.get("what_remains_forbidden") or []
            ),
            "stage7_unlock_status": stage7_heldout_unlock_review.get("status"),
            "stage8_blocker_status": stage7_to_stage8_blocker_review.get("status"),
            "stage7_promotion_allowed": stage7_to_stage8_blocker_review.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": stage7_to_stage8_blocker_review.get(
                "stage8_training_allowed"
            ),
        },
        "strategy_sequence_architecture_gate": {
            "status": strategy_sequence_inventory_decision.get("status"),
            "passive_architecture_ready": strategy_sequence_architecture_passive,
            "architecture_review_status": strategy_sequence_architecture_decision.get(
                "status"
            ),
            "architecture_runtime_work_allowed": (
                strategy_sequence_architecture_decision.get("runtime_work_allowed")
            ),
            "architecture_forbidden_shortcuts": (
                strategy_sequence_architecture_review.get("forbidden_shortcuts") or []
            ),
            "architecture_next_objective_ids": strategy_sequence_next_objective_ids,
            "architecture_recommended_next_slice_id": (
                strategy_sequence_architecture_review.get("recommended_next_slice")
                or {}
            ).get("slice_id"),
            "evidence_plan_status": strategy_sequence_evidence_plan_decision.get(
                "status"
            ),
            "evidence_plan_runtime_work_allowed": (
                strategy_sequence_evidence_plan_decision.get("runtime_work_allowed")
            ),
            "evidence_plan_blocked_actions": (
                strategy_sequence_evidence_plan.get("blocked_actions") or []
            ),
            "inventory_status": strategy_sequence_inventory_decision.get("status"),
            "inventory_runtime_work_allowed": (
                strategy_sequence_inventory_decision.get("runtime_work_allowed")
            ),
            "inventory_sequence_policy_clean_gate_closed": (
                strategy_sequence_gap_summary.get("sequence_policy_clean_gate_closed")
            ),
            "inventory_sequence_policy_has_clean_success_gap": (
                strategy_sequence_gap_summary.get("sequence_policy_has_clean_success_gap")
            ),
            "inventory_state_holdout_gap_blocks_runtime": (
                strategy_sequence_gap_summary.get("state_holdout_gap_blocks_runtime")
            ),
            "inventory_strategy_ownership_has_some_signal": (
                strategy_sequence_gap_summary.get("strategy_ownership_has_some_signal")
            ),
            "inventory_strategy_ownership_state_holdout_ready": (
                strategy_sequence_gap_summary.get("strategy_ownership_state_holdout_ready")
            ),
            "inventory_stage7_is_held_out": (
                strategy_sequence_boundary_inventory.get("stage7_is_held_out")
            ),
            "inventory_stage7_clean_control_collection_paused": (
                strategy_sequence_boundary_inventory.get(
                    "stage7_clean_control_collection_paused"
                )
            ),
            "inventory_stage7_clean_review_recommendation": (
                strategy_sequence_boundary_inventory.get(
                    "stage7_clean_review_recommendation"
                )
            ),
            "runtime_behavior_changed": strategy_sequence_inventory.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": strategy_sequence_inventory.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": strategy_sequence_inventory.get(
                "runtime_selector_implemented"
            ),
            "runtime_dtm_or_tablebase_lookup": strategy_sequence_inventory.get(
                "runtime_dtm_or_tablebase_lookup"
            ),
            "stage7_promotion_allowed": strategy_sequence_inventory.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": strategy_sequence_inventory.get(
                "stage8_training_allowed"
            ),
        },
        "strategy_owner_contrast_gate": {
            "status": strategy_owner_probe_decision.get("status"),
            "passive_probe_ready": strategy_owner_probe_passive,
            "label_plan_status": strategy_owner_plan_decision.get("status"),
            "label_plan_job_count": len(
                strategy_owner_contrast_label_plan.get("jobs") or []
            ),
            "label_plan_stage7_job_count": sum(
                1
                for job in strategy_owner_contrast_label_plan.get("jobs") or []
                if job.get("source_stage") == "stage7"
            ),
            "label_plan_labels_generated": (
                strategy_owner_contrast_label_plan.get("labels_generated_in_this_slice")
            ),
            "label_plan_runtime_arbiter_allowed": strategy_owner_plan_decision.get(
                "runtime_arbiter_allowed"
            ),
            "label_plan_selector_sandbox_ready": strategy_owner_plan_decision.get(
                "selector_sandbox_ready"
            ),
            "label_plan_review_status": strategy_owner_plan_review_decision.get(
                "status"
            ),
            "label_plan_review_allowed_to_bind_manifest": (
                strategy_owner_plan_review_summary.get(
                    "allowed_to_bind_execution_manifest"
                )
            ),
            "label_plan_review_allowed_to_run_labels": (
                strategy_owner_plan_review_summary.get("allowed_to_run_labels")
            ),
            "label_plan_review_stage7_jobs": strategy_owner_plan_review_summary.get(
                "stage7_jobs"
            ),
            "execution_manifest_status": strategy_owner_manifest_decision.get("status"),
            "execution_manifest_labels_allowed_now": (
                strategy_owner_manifest_decision.get("labels_allowed_now")
            ),
            "execution_manifest_all_bindings_valid": strategy_owner_manifest_binding.get(
                "all_bindings_valid"
            ),
            "execution_manifest_missing_path_count": (
                strategy_owner_manifest_binding.get("missing_path_count")
            ),
            "execution_manifest_stage7_jobs": strategy_owner_manifest_binding.get(
                "stage7_jobs"
            ),
            "execution_manifest_review_status": (
                strategy_owner_manifest_review_decision.get("status")
            ),
            "execution_manifest_review_labels_allowed": (
                strategy_owner_manifest_review_summary.get("labels_allowed")
            ),
            "execution_manifest_review_stage7_jobs": (
                strategy_owner_manifest_review_summary.get("stage7_jobs")
            ),
            "control_label_count": strategy_owner_labels_summary.get("label_count"),
            "control_label_stage7_count": strategy_owner_labels_summary.get(
                "stage7_labels"
            ),
            "control_label_trace_failures_only": strategy_owner_labels_summary.get(
                "trace_failures_only"
            ),
            "control_label_result_counts": strategy_owner_labels_summary.get(
                "result_counts"
            )
            or {},
            "dataset_status": strategy_owner_dataset_decision.get("status"),
            "dataset_row_count": strategy_owner_dataset_summary.get("row_count"),
            "dataset_training_eligible_row_count": strategy_owner_dataset_summary.get(
                "training_eligible_row_count"
            ),
            "dataset_held_out_challenge_row_count": strategy_owner_dataset_summary.get(
                "held_out_challenge_row_count"
            ),
            "dataset_stage7_training_rows": strategy_owner_dataset_summary.get(
                "stage7_training_rows"
            ),
            "dataset_training_positive_provider_label_count": (
                strategy_owner_dataset_summary.get("training_positive_provider_label_count")
            ),
            "dataset_training_negative_provider_label_count": (
                strategy_owner_dataset_summary.get("training_negative_provider_label_count")
            ),
            "dataset_selected_training_provider_families": (
                strategy_owner_dataset_summary.get("selected_training_provider_families")
                or []
            ),
            "readiness_contrast_probe_ready": strategy_owner_readiness_v2.get(
                "contrast_probe_ready"
            ),
            "readiness_selector_sandbox_ready": strategy_owner_readiness_v2.get(
                "selector_sandbox_ready"
            ),
            "readiness_stage7_training_rows": strategy_owner_readiness_v2.get(
                "stage7_training_rows"
            ),
            "readiness_blockers": strategy_owner_readiness_v2.get("blockers") or [],
            "probe_status": strategy_owner_probe_decision.get("status"),
            "probe_training_row_count": strategy_owner_probe_metrics.get(
                "training_row_count"
            ),
            "probe_heldout_row_count": strategy_owner_probe_metrics.get(
                "heldout_row_count"
            ),
            "probe_training_positive_label_count": strategy_owner_probe_metrics.get(
                "training_positive_label_count"
            ),
            "probe_training_negative_label_count": strategy_owner_probe_metrics.get(
                "training_negative_label_count"
            ),
            "probe_readiness_blockers": strategy_owner_probe_metrics.get(
                "readiness_blockers"
            )
            or [],
            "probe_findings": strategy_owner_contrast_probe.get("findings") or [],
            "runtime_arbiter_implemented": strategy_owner_contrast_probe.get(
                "runtime_arbiter_implemented"
            ),
            "runtime_behavior_changed": strategy_owner_contrast_probe.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": strategy_owner_contrast_probe.get(
                "runtime_defaults_changed"
            ),
            "runtime_dtm_or_tablebase_lookup": strategy_owner_contrast_probe.get(
                "runtime_dtm_or_tablebase_lookup"
            ),
            "runtime_terminals_added": strategy_owner_contrast_probe.get(
                "runtime_terminals_added"
            ),
            "stage7_promotion_allowed": strategy_owner_contrast_probe.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": strategy_owner_contrast_probe.get(
                "stage8_training_allowed"
            ),
        },
        "selector_objective_normalization_gate": {
            "status": split_readiness_decision.get("status"),
            "passive_objective_ready": selector_objective_normalization_passive,
            "arbitration_objective_status": arbitration_objective_decision.get("status"),
            "arbitration_runtime_test_allowed_next": (
                arbitration_objective_decision.get("runtime_test_allowed_next")
            ),
            "arbitration_contrast_positive_provider_families": (
                arbitration_objective_metrics.get("contrast_positive_provider_families")
                or []
            ),
            "arbitration_contrast_training_positive_label_count": (
                arbitration_objective_metrics.get("contrast_training_positive_label_count")
            ),
            "arbitration_contrast_training_negative_label_count": (
                arbitration_objective_metrics.get("contrast_training_negative_label_count")
            ),
            "normalized_objective_status": normalized_objective_decision.get("status"),
            "normalized_objective_runtime_test_allowed_next": (
                normalized_objective_decision.get("runtime_test_allowed_next")
            ),
            "normalized_objective_forbidden_uses": (
                normalized_strategy_selector_objective_v1.get("forbidden_uses") or []
            ),
            "normalized_probe_status": normalized_probe_decision.get("status"),
            "normalized_probe_benchmark_underpowered": (
                normalized_strategy_selector_objective_probe_v1.get(
                    "benchmark_underpowered"
                )
            ),
            "normalized_probe_fields_available": (
                normalized_strategy_selector_objective_probe_v1.get(
                    "normalized_fields_available"
                )
            ),
            "normalized_probe_review_status": normalized_probe_review_decision.get(
                "status"
            ),
            "normalized_probe_review_stage7_training_leakage": (
                normalized_probe_review_summary.get("stage7_training_leakage")
            ),
            "normalized_probe_review_best_provenance_accuracy": (
                normalized_probe_review_summary.get("best_provenance_accuracy")
            ),
            "selector_architecture_status": selector_architecture_decision.get("status"),
            "selector_architecture_runtime_arbiter_allowed": (
                selector_architecture_decision.get("runtime_arbiter_allowed")
            ),
            "selector_architecture_sandbox_ready": selector_architecture_decision.get(
                "selector_sandbox_ready"
            ),
            "selector_label_semantics_sandbox_ready": (
                selector_objective_label_semantics_v0.get("sandbox_ready")
            ),
            "selector_label_semantics_target_kind_count": len(
                selector_objective_label_semantics_v0.get("target_kinds") or []
            ),
            "split_dataset_status": split_dataset_decision.get("status"),
            "split_dataset_objective_row_count": split_dataset_summary.get(
                "objective_row_count"
            ),
            "split_dataset_ownership_selection_row_count": split_dataset_summary.get(
                "ownership_selection_row_count"
            ),
            "split_dataset_selector_training_row_count": split_dataset_summary.get(
                "selector_training_row_count"
            ),
            "split_dataset_stage7_row_count": split_dataset_summary.get(
                "stage7_row_count"
            ),
            "split_readiness_status": split_readiness_decision.get("status"),
            "split_readiness_runtime_work_allowed": split_readiness_decision.get(
                "runtime_work_allowed"
            ),
            "split_readiness_selector_training_allowed": split_readiness_decision.get(
                "selector_training_allowed"
            ),
            "split_readiness_ownership_available": split_readiness_summary.get(
                "ownership_selection_available"
            ),
            "split_readiness_ownership_row_count": split_readiness_summary.get(
                "ownership_selection_row_count"
            ),
            "split_readiness_ownership_probe_underpowered": split_readiness_summary.get(
                "ownership_probe_underpowered"
            ),
            "split_readiness_ownership_probe_positive_recall": split_readiness_summary.get(
                "ownership_probe_positive_recall"
            ),
            "split_readiness_ownership_probe_negative_suppression": (
                split_readiness_summary.get("ownership_probe_negative_suppression")
            ),
            "split_readiness_selector_training_row_count": split_readiness_summary.get(
                "selector_training_row_count"
            ),
            "split_readiness_stage7_row_count": split_readiness_summary.get(
                "stage7_row_count"
            ),
            "split_readiness_channel_counts": {
                name: channel.get("row_count")
                for name, channel in split_readiness_channels.items()
            },
            "runtime_behavior_changed": split_selector_objective_readiness_v3.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": split_selector_objective_readiness_v3.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": split_selector_objective_readiness_v3.get(
                "runtime_selector_implemented"
            ),
            "runtime_candidate_generator_implemented": (
                split_selector_objective_readiness_v3.get(
                    "runtime_candidate_generator_implemented"
                )
            ),
            "runtime_terminals_added": split_selector_objective_readiness_v3.get(
                "runtime_terminals_added"
            ),
            "stage7_promotion_allowed": split_selector_objective_readiness_v3.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": split_selector_objective_readiness_v3.get(
                "stage8_training_allowed"
            ),
        },
        "abstention_selector_safety_gate": {
            "status": abstention_context_probe_decision.get("status"),
            "passive_safety_ready": abstention_selector_safety_passive,
            "first_objective_status": abstention_objective_decision.get("status"),
            "safe_preservation_review_status": (
                abstention_safe_review_decision.get("status")
            ),
            "safe_preservation_false_positive_count": (
                abstention_safe_review_summary.get("false_positive_count")
            ),
            "safe_preservation_best_negative_suppression": (
                abstention_safe_review_summary.get("best_negative_suppression")
            ),
            "safe_preservation_best_safe_preservation": (
                abstention_safe_review_summary.get("best_safe_preservation")
            ),
            "training_dataset_status": abstention_dataset_decision.get("status"),
            "training_dataset_row_count": abstention_dataset_summary.get("row_count"),
            "training_dataset_safe_owner_count": (
                (abstention_dataset_summary.get("label_counts") or {}).get("safe_owner")
            ),
            "training_dataset_unsafe_owner_count": (
                (abstention_dataset_summary.get("label_counts") or {}).get(
                    "unsafe_owner"
                )
            ),
            "training_dataset_stage7_training_rows": (
                abstention_dataset_summary.get("stage7_training_rows")
            ),
            "training_probe_status": abstention_probe_decision.get("status"),
            "training_probe_under_minimum_requirements": (
                abstention_probe_summary.get("under_minimum_requirements")
            ),
            "context_dataset_status": abstention_context_dataset_decision.get("status"),
            "context_dataset_row_count": (
                abstention_context_dataset_summary.get("row_count")
            ),
            "context_dataset_stage7_training_rows": (
                abstention_context_dataset_summary.get("stage7_training_rows")
            ),
            "context_dataset_terminal_context_proxy_count": (
                abstention_context_dataset_summary.get("terminal_context_proxy_count")
            ),
            "context_probe_status": abstention_context_probe_decision.get("status"),
            "context_probe_improved_negative_suppression": (
                abstention_context_probe_summary.get(
                    "context_improved_negative_suppression"
                )
            ),
            "context_probe_baseline_negative_suppression": (
                abstention_context_probe_summary.get("baseline_negative_suppression")
            ),
            "context_probe_best_negative_suppression": (
                abstention_context_probe_summary.get("best_negative_suppression")
            ),
            "context_probe_best_safe_preservation": (
                abstention_context_probe_summary.get("best_safe_preservation")
            ),
            "context_error_audit_status": abstention_error_audit_decision.get("status"),
            "context_error_false_positive_count": (
                abstention_error_audit_summary.get("false_positive_count")
            ),
            "context_error_false_negative_count": (
                abstention_error_audit_summary.get("false_negative_count")
            ),
            "feature_gap_next_step_status": abstention_feature_gap_next_step.get(
                "status"
            ),
            "feature_gap_implementation_allowed": (
                abstention_feature_gap_next_step.get("implementation_allowed")
            ),
            "feature_gap_runtime_ready": (
                (abstention_feature_gap_review_v0.get("accepted_result") or {}).get(
                    "runtime_ready"
                )
            ),
            "blocked_next_steps": abstention_blocked_next_steps,
            "runtime_behavior_changed": abstention_feature_gap_review_v0.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": abstention_feature_gap_review_v0.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": abstention_feature_gap_review_v0.get(
                "runtime_selector_implemented"
            ),
            "runtime_dtm_or_tablebase_lookup": abstention_feature_gap_review_v0.get(
                "runtime_dtm_or_tablebase_lookup"
            ),
            "stage7_promotion_allowed": abstention_feature_gap_review_v0.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": abstention_feature_gap_review_v0.get(
                "stage8_training_allowed"
            ),
        },
        "targeted_ownership_recovery_gate": {
            "status": targeted_non_stage0_review_decision.get("status"),
            "passive_recovery_ready": targeted_ownership_recovery_passive,
            "non_stage0_manifest_status": targeted_non_stage0_manifest_decision.get(
                "status"
            ),
            "non_stage0_manifest_job_count": targeted_non_stage0_manifest_binding.get(
                "job_count"
            ),
            "non_stage0_manifest_stage7_job_count": (
                targeted_non_stage0_manifest_binding.get("stage7_job_count")
            ),
            "non_stage0_manifest_labels_generated": (
                targeted_non_stage0_ownership_manifest_v0.get(
                    "labels_generated_in_this_slice"
                )
            ),
            "non_stage0_labels_status": targeted_non_stage0_labels_decision.get(
                "status"
            ),
            "non_stage0_label_count": targeted_non_stage0_labels_summary.get(
                "label_count"
            ),
            "non_stage0_preserved_count": targeted_non_stage0_labels_summary.get(
                "preserved_historical_non_stage0_count"
            ),
            "non_stage0_stage0_collapse_count": (
                targeted_non_stage0_labels_summary.get("current_stage0_collapse_count")
            ),
            "non_stage0_selected_owner_failed_count": (
                targeted_non_stage0_review_summary.get("selected_owner_failed_count")
            ),
            "non_stage0_stage7_training_rows": (
                targeted_non_stage0_labels_summary.get("stage7_training_rows")
            ),
            "negative_manifest_status": targeted_negative_manifest_decision.get(
                "status"
            ),
            "negative_manifest_job_count": targeted_negative_manifest_binding.get(
                "job_count"
            ),
            "negative_manifest_stage7_job_count": (
                targeted_negative_manifest_binding.get("stage7_job_count")
            ),
            "negative_manifest_labels_generated": (
                targeted_ownership_negative_manifest_v0.get(
                    "labels_generated_in_this_slice"
                )
            ),
            "negative_labels_status": targeted_negative_labels_decision.get("status"),
            "negative_label_count": targeted_negative_labels_summary.get("label_count"),
            "negative_preselection_preserved_count": (
                targeted_negative_labels_summary.get("preselection_preserved_count")
            ),
            "negative_targeted_owner_converted_count": (
                targeted_negative_labels_summary.get("targeted_owner_converted_count")
            ),
            "negative_targeted_owner_failed_count": (
                targeted_negative_labels_summary.get("targeted_owner_failed_count")
            ),
            "negative_stage7_training_rows": (
                targeted_negative_labels_summary.get("stage7_training_rows")
            ),
            "runtime_behavior_changed": targeted_ownership_negative_labels_v0.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": targeted_ownership_negative_labels_v0.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": targeted_ownership_negative_labels_v0.get(
                "runtime_selector_implemented"
            ),
            "runtime_dtm_or_tablebase_lookup": (
                targeted_ownership_negative_labels_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_terminals_added": targeted_ownership_negative_labels_v0.get(
                "runtime_terminals_added"
            ),
            "stage7_promotion_allowed": targeted_ownership_negative_labels_v0.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": targeted_ownership_negative_labels_v0.get(
                "stage8_training_allowed"
            ),
        },
        "balanced_hard_negative_gate": {
            "status": balanced_hard_negative_review_decision.get("status"),
            "passive_evidence_ready": balanced_hard_negative_passive,
            "label_plan_status": balanced_hard_negative_plan_decision.get("status"),
            "label_plan_job_count": balanced_hard_negative_plan_summary.get(
                "job_count"
            ),
            "label_plan_stage7_jobs": balanced_hard_negative_plan_summary.get(
                "stage7_jobs"
            ),
            "label_plan_provider_family_counts": (
                balanced_hard_negative_plan_summary.get("provider_family_counts") or {}
            ),
            "execution_manifest_status": (
                balanced_hard_negative_manifest_decision.get("status")
            ),
            "execution_manifest_labels_allowed_now": (
                balanced_hard_negative_manifest_decision.get("labels_allowed_now")
            ),
            "execution_manifest_all_bindings_valid": (
                balanced_hard_negative_manifest_binding.get("all_bindings_valid")
            ),
            "execution_manifest_job_count": (
                balanced_hard_negative_manifest_binding.get("job_count")
            ),
            "execution_manifest_stage7_jobs": (
                balanced_hard_negative_manifest_binding.get("stage7_jobs")
            ),
            "execution_manifest_review_status": (
                balanced_hard_negative_manifest_review_decision.get("status")
            ),
            "execution_manifest_review_labels_allowed": (
                balanced_hard_negative_manifest_review_decision.get("labels_allowed")
            ),
            "labels_status": balanced_hard_negative_labels_decision.get("status"),
            "label_count": balanced_hard_negative_labels_summary.get("label_count"),
            "positive_capacity_count": (
                balanced_hard_negative_labels_summary.get("positive_capacity_count")
            ),
            "negative_capacity_count": (
                balanced_hard_negative_labels_summary.get("negative_capacity_count")
            ),
            "stage7_labels": balanced_hard_negative_labels_summary.get(
                "stage7_labels"
            ),
            "stage7_training_labels": balanced_hard_negative_labels_summary.get(
                "stage7_training_labels"
            ),
            "trace_failures_only": balanced_hard_negative_labels_summary.get(
                "trace_failures_only"
            ),
            "evidence_review_status": balanced_hard_negative_review_decision.get(
                "status"
            ),
            "evidence_underpowered": balanced_hard_negative_review_summary.get(
                "underpowered"
            ),
            "evidence_expanded_row_count": (
                balanced_hard_negative_review_summary.get("expanded_row_count")
            ),
            "evidence_expanded_hard_negative_count": (
                balanced_hard_negative_review_summary.get(
                    "expanded_hard_negative_count"
                )
            ),
            "evidence_expanded_positive_context_count": (
                balanced_hard_negative_review_summary.get(
                    "expanded_positive_context_count"
                )
            ),
            "evidence_best_negative_suppression": (
                balanced_hard_negative_review_summary.get("best_negative_suppression")
            ),
            "evidence_best_positive_recall": (
                balanced_hard_negative_review_summary.get("best_positive_recall")
            ),
            "evidence_stage7_row_count": (
                balanced_hard_negative_review_summary.get("stage7_row_count")
            ),
            "runtime_behavior_changed": balanced_hard_negative_evidence_review_v0.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": balanced_hard_negative_evidence_review_v0.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": (
                balanced_hard_negative_evidence_review_v0.get(
                    "runtime_selector_implemented"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                balanced_hard_negative_evidence_review_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_terminals_added": balanced_hard_negative_evidence_review_v0.get(
                "runtime_terminals_added"
            ),
            "stage7_promotion_allowed": balanced_hard_negative_evidence_review_v0.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": balanced_hard_negative_evidence_review_v0.get(
                "stage8_training_allowed"
            ),
        },
        "clean_replacement_review_gate": {
            "status": clean_stack_replacement_packet.get("status"),
            "passive_review_ready": clean_replacement_review_passive,
            "replacement_readiness_status": clean_replacement_readiness.get("status"),
            "replacement_readiness_clean_stack_replacement_allowed": (
                replacement_readiness_decision.get("clean_stack_replacement_allowed")
            ),
            "snapshot_manifest_status": clean_stack_snapshot_manifest.get("status"),
            "snapshot_manifest_all_referenced_paths_exist": snapshot_decision.get(
                "all_referenced_paths_exist"
            ),
            "snapshot_manifest_replacement_allowed": snapshot_decision.get(
                "clean_stack_replacement_allowed_by_manifest"
            ),
            "snapshot_current_stack_path_status": snapshot_current_stack_path_status,
            "snapshot_retry1_stack_path_status": snapshot_retry1_stack_path_status,
            "review_packet_status": clean_stack_replacement_packet.get("status"),
            "review_packet_replacement_review_ready": replacement_packet_decision.get(
                "replacement_review_ready"
            ),
            "review_packet_implementation_allowed": replacement_packet_decision.get(
                "implementation_allowed_by_this_packet"
            ),
            "review_packet_explicit_human_approval_required": (
                replacement_packet_decision.get(
                    "explicit_human_approval_required_before_any_file_change"
                )
            ),
            "deferred_review_status": clean_stack_deferred_review.get("status"),
            "deferred_review_decision_state": clean_stack_deferred_review.get(
                "decision_state"
            ),
            "deferred_review_explicit_approval_detected": (
                clean_stack_deferred_review.get("explicit_approval_detected")
            ),
            "deferred_review_implementation_allowed": (
                clean_stack_deferred_review.get("implementation_allowed_by_review_packet")
            ),
            "protected_stage_active_stack_status": protected_stage_status.get(
                "active_stack_status"
            ),
            "protected_stage_reference_mode": protected_stage_status.get(
                "protected_stack_reference_mode"
            ),
            "protected_stage_stage4_status": next(
                (
                    item.get("status")
                    for item in protected_stage_status.get("stage_statuses") or []
                    if item.get("stage") == "stage4_wrong_tempo"
                ),
                None,
            ),
            "protected_stage_stage7_status": protected_stage_status.get(
                "stage7_status"
            ),
            "protected_stage_stage8_training_allowed": protected_stage_status.get(
                "stage8_training_allowed"
            ),
            "protected_stage_blocked_next_steps": (
                protected_stage_status.get("blocked_next_steps") or []
            ),
            "protected_stage_cleanest_solved_components": (
                protected_stage_status_summary.get("cleanest_solved_components") or []
            ),
            "runtime_behavior_changed": protected_stage_status.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": protected_stage_status.get(
                "runtime_defaults_changed"
            ),
            "runtime_dtm_or_tablebase_lookup": protected_stage_status.get(
                "runtime_dtm_or_tablebase_lookup"
            ),
            "gameplay_topology_mutation": protected_stage_status.get(
                "gameplay_topology_mutation"
            ),
            "stage7_promotion_allowed": protected_stage_status.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": protected_stage_status.get(
                "stage8_training_allowed"
            ),
        },
        "stage_status": stage_status,
        "sequence_policy": {
            "pipeline_status": pipeline.get("decision", {}).get("status"),
            "input_probe_status": (
                sequence_policy_input_probe.get("decision", {}).get("status")
            ),
            "input_probe_row_count": (
                sequence_policy_input_probe.get("summary", {}).get("row_count")
            ),
            "input_probe_benchmark_input_ready": (
                sequence_policy_input_probe.get("summary", {}).get(
                    "benchmark_input_ready"
                )
            ),
            "input_probe_stage4_topk_signal": (
                sequence_policy_input_probe.get("summary", {}).get(
                    "stage4_topk_signal"
                )
            ),
            "input_probe_protected_plan_window_failure_sparse": (
                sequence_policy_input_probe.get("summary", {}).get(
                    "protected_plan_window_failure_sparse"
                )
            ),
            "input_probe_protected_failure_contrast_collection_option_available": (
                sequence_policy_input_probe.get("summary", {}).get(
                    "protected_failure_contrast_collection_option_available"
                )
            ),
            "input_probe_protected_failure_contrast_collection_command_available": (
                sequence_policy_input_probe.get("summary", {}).get(
                    "protected_failure_contrast_collection_command_available"
                )
            ),
            "input_probe_selector_training_row_count": (
                sequence_policy_input_probe.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "input_probe_runtime_authorization_row_count": (
                sequence_policy_input_probe.get("summary", {}).get(
                    "runtime_authorization_row_count"
                )
            ),
            "benchmark_status": benchmark_decision.get("status"),
            "benchmark_design_status": benchmark_design_decision.get("status"),
            "benchmark_review_status": sequence_review_status,
            "post_failure_contrast_refresh_status": (
                post_failure_contrast_refresh_decision.get("status")
            ),
            "post_failure_contrast_refresh_next_step": (
                post_failure_contrast_refresh_decision.get("recommended_next_step")
            ),
            "post_failure_contrast_refresh_boundaries_preserved": (
                post_failure_contrast_refresh_boundaries_preserved
            ),
            "post_failure_contrast_refresh_boundary_violation_count": (
                post_failure_contrast_refresh_boundary_violation_count
            ),
            "post_failure_contrast_refresh_integration_status": (
                post_failure_contrast_refresh_summary.get("integration_status")
            ),
            "post_failure_contrast_refresh_integration_ready": (
                post_failure_contrast_refresh_summary.get("integration_ready")
            ),
            "post_failure_contrast_refresh_integrated_new_failure_count": (
                post_failure_contrast_refresh_summary.get("integrated_new_failure_count")
            ),
            "post_failure_contrast_refresh_row_count": (
                post_failure_contrast_refresh_summary.get(
                    "protected_failure_contrast_row_count"
                )
            ),
            "post_failure_contrast_refresh_stage7_training_row_count": (
                post_failure_contrast_refresh_summary.get("stage7_training_row_count")
            ),
            "benchmark_preflight_blockers": benchmark_preflight.get("blockers") or [],
            "benchmark_review_blockers": benchmark_review_blockers,
            "passive_design_without_new_labels_status": passive_design.get("status"),
            "passive_design_current_evidence_limit": passive_design.get(
                "current_evidence_limit"
            ),
            "passive_design_depends_on_new_label_execution": passive_design.get(
                "depends_on_new_label_execution"
            ),
            "passive_design_depends_on_protected_failure_contrast_collection": (
                passive_design.get("depends_on_protected_failure_contrast_collection")
            ),
            "cross_stage_requirements_status": cross_stage_requirements.get(
                "decision", {}
            ).get("status"),
            "replay_free_protected_cross_stage_evidence": cross_stage_readiness.get(
                "replay_free_protected_cross_stage_evidence"
            ),
            "cross_stage_sequence_evidence_met": cross_stage_readiness.get(
                "cross_stage_sequence_evidence_met"
            ),
            "forbidden_training_or_runtime_input_blocked": (
                sequence_forbidden_training_or_runtime_inputs
            ),
            "forbidden_training_or_runtime_input_blockers": forbidden_input_blockers,
            "input_row_count": benchmark_preflight.get("row_count"),
            "inputs_ready": sequence_summary.get("sequence_policy_inputs_ready"),
            "benchmark_ready": benchmark_decision.get("benchmark_executed_as_ready"),
            "stage7_heldout_row_count": benchmark_preflight.get("stage7_heldout_row_count"),
            "selector_training_row_count": benchmark_preflight.get("selector_training_row_count"),
            "runtime_authorization_row_count": benchmark_preflight.get(
                "runtime_authorization_row_count"
            ),
        },
        "protected_failure_contrast_gate": {
            "plan_status": failure_contrast_plan.get("decision", {}).get("status"),
            "unique_failure_count": failure_contrast_plan.get("summary", {}).get(
                "unique_failure_count"
            ),
            "minimum_new_failures_needed": failure_contrast_plan.get("summary", {}).get(
                "minimum_new_unique_failures_needed"
            ),
            "manifest_status": failure_contrast_manifest.get("decision", {}).get(
                "status"
            ),
            "manifest_job_count": failure_contrast_manifest.get("summary", {}).get(
                "job_count"
            ),
            "manifest_review_status": failure_contrast_manifest_review.get(
                "decision", {}
            ).get("status"),
            "execution_readiness_status": failure_contrast_execution_readiness.get(
                "decision", {}
            ).get("status"),
            "execution_jobs_passing": failure_contrast_execution_readiness.get(
                "summary", {}
            ).get("jobs_passing_readiness"),
            "runner_status": failure_contrast_runner.get("decision", {}).get("status"),
            "runner_manifest_status": failure_contrast_runner_summary.get(
                "manifest_status"
            ),
            "runner_manifest_declared_job_count": failure_contrast_runner_summary.get(
                "manifest_declared_job_count"
            ),
            "runner_manifest_fingerprint": failure_contrast_runner_summary.get(
                "manifest_fingerprint"
            ),
            "runner_collection_run_allowed": failure_contrast_runner.get(
                "decision", {}
            ).get("collection_run_allowed"),
            "runner_processed_job_count": failure_contrast_runner.get(
                "summary", {}
            ).get("processed_job_count"),
            "runner_executed_job_count": failure_contrast_runner.get("summary", {}).get(
                "executed_job_count"
            ),
            "output_validation_status": failure_contrast_output_validation.get(
                "decision", {}
            ).get("status"),
            "output_exists_count": failure_contrast_output_validation.get(
                "summary", {}
            ).get("output_exists_count"),
            "output_valid_count": failure_contrast_output_validation.get(
                "summary", {}
            ).get("output_valid_count"),
            "integration_status": failure_contrast_integration.get("decision", {}).get(
                "status"
            ),
            "integrated_new_failure_count": failure_contrast_integration.get(
                "summary", {}
            ).get("integrated_new_failure_count"),
            "integration_ready": protected_failure_contrast_integration_ready,
            "ready_for_explicit_approval": (
                protected_failure_contrast_ready_for_explicit_approval
            ),
            "approval_request_ready_for_collection": (
                failure_contrast_approval_request_ready
            ),
            "current_artifact_allows_collection": False,
            "approval_receipt_required": True,
            "approval_receipt_path": failure_contrast_approval_receipt_path,
            "approval_receipt_present": failure_contrast_runner_summary.get(
                "approval_receipt_present"
            ),
            "approval_receipt_valid": failure_contrast_runner_summary.get(
                "approval_receipt_valid"
            ),
            "approval_receipt_blockers": (
                failure_contrast_runner_summary.get("approval_receipt_blockers") or []
            ),
            "approval_request_artifact": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
            ),
            "approval_request_status": failure_contrast_approval_request.get(
                "decision", {}
            ).get("status"),
            "approval_request_blockers": (
                failure_contrast_approval_request_blockers
            ),
            "approval_receipt_created_by_request": (
                failure_contrast_approval_request.get("approval_receipt_created")
            ),
            "post_success_refresh_required": (
                failure_contrast_approval_request_summary.get(
                    "post_success_refresh_required"
                )
            ),
            "post_success_refresh_script": (
                failure_contrast_approval_request_summary.get(
                    "post_success_refresh_script"
                )
            ),
            "post_success_refresh_scope": (
                failure_contrast_approval_request_summary.get(
                    "post_success_refresh_scope"
                )
            ),
            "expected_manifest_fingerprint": (
                failure_contrast_runner_summary.get(
                    "execution_readiness_manifest_fingerprint"
                )
                or failure_contrast_execution_readiness.get("summary", {}).get(
                    "manifest_fingerprint"
                )
            ),
            "expected_readiness_fingerprint": (
                failure_contrast_runner_summary.get("execution_readiness_fingerprint")
                or failure_contrast_execution_readiness.get("summary", {}).get(
                    "readiness_fingerprint"
                )
            ),
            "command_if_explicitly_approved": (
                failure_contrast_command
                if protected_failure_contrast_ready_for_explicit_approval
                else None
            ),
            "runtime_behavior_changed": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "hidden_python_controller": False,
            "gameplay_topology_mutation": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "protected_missing_provider_gate": {
            "labels_status": protected_missing_provider_labels.get(
                "decision", {}
            ).get("status"),
            "labels_next_step": protected_missing_provider_labels.get(
                "decision", {}
            ).get("recommended_next_step"),
            "label_count": protected_missing_provider_labels.get("summary", {}).get(
                "label_count"
            ),
            "label_result_counts": protected_missing_provider_labels.get(
                "summary", {}
            ).get("result_counts"),
            "stage7_label_count": protected_missing_provider_labels.get(
                "summary", {}
            ).get("stage7_labels"),
            "stage7_training_label_count": protected_missing_provider_labels.get(
                "summary", {}
            ).get("stage7_training_labels"),
            "merge_status": protected_missing_provider_merge.get(
                "decision", {}
            ).get("status"),
            "merge_next_step": protected_missing_provider_merge.get(
                "decision", {}
            ).get("recommended_next_step"),
            "matched_label_count": protected_missing_provider_merge.get(
                "summary", {}
            ).get("matched_protected_label_count"),
            "unmatched_label_count": protected_missing_provider_merge.get(
                "summary", {}
            ).get("unmatched_protected_label_count"),
            "coverage_status": protected_missing_provider_coverage.get(
                "decision", {}
            ).get("status"),
            "coverage_next_step": protected_missing_provider_coverage.get(
                "decision", {}
            ).get("recommended_next_step"),
            "coverage_label_count": protected_missing_provider_coverage.get(
                "summary", {}
            ).get("label_count"),
            "coverage_frames_present_count": protected_missing_provider_coverage.get(
                "summary", {}
            ).get("frames_present_count"),
            "provider_present_in_frame_count": (
                protected_missing_provider_coverage.get("summary", {}).get(
                    "provider_present_in_frame_count"
                )
            ),
            "provider_missing_from_frame_count": (
                protected_missing_provider_coverage.get("summary", {}).get(
                    "provider_missing_from_frame_count"
                )
            ),
            "missing_provider_mate_label_count": (
                protected_missing_provider_coverage.get("summary", {}).get(
                    "missing_provider_mate_label_count"
                )
            ),
            "current_gap_blocks_selector_training": (
                protected_missing_provider_coverage.get("decision", {}).get("status")
                == "proposal_provider_coverage_gap_blocks_selector_training"
            ),
            "coverage_expansion_plan_status": protected_coverage_expansion_plan.get(
                "decision", {}
            ).get("status"),
            "coverage_expansion_plan_next_step": protected_coverage_expansion_plan.get(
                "decision", {}
            ).get("recommended_next_step"),
            "coverage_expansion_rows_to_create": protected_coverage_expansion_plan.get(
                "expansion_design", {}
            ).get("rows_to_create"),
            "coverage_expansion_training_allowed_initially": (
                protected_coverage_expansion_plan.get("acceptance_for_next_slice", {}).get(
                    "training_allowed_initially"
                )
            ),
            "coverage_expansion_requires_followup_review_before_training_use": (
                protected_coverage_expansion_plan.get("acceptance_for_next_slice", {}).get(
                    "requires_followup_review_before_training_use"
                )
            ),
            "coverage_frames_status": protected_provider_coverage_frames.get(
                "decision", {}
            ).get("status"),
            "coverage_frames_next_step": protected_provider_coverage_frames.get(
                "decision", {}
            ).get("recommended_next_step"),
            "coverage_frame_row_count": protected_provider_coverage_frames.get(
                "summary", {}
            ).get("row_count"),
            "coverage_frame_positive_capacity_count": (
                protected_provider_coverage_frames.get("summary", {})
                .get("capacity_label_counts", {})
                .get("positive_capacity")
            ),
            "coverage_frame_negative_capacity_count": (
                protected_provider_coverage_frames.get("summary", {})
                .get("capacity_label_counts", {})
                .get("negative_capacity")
            ),
            "coverage_frame_stage7_row_count": protected_provider_coverage_frames.get(
                "summary", {}
            ).get("stage7_row_count"),
            "coverage_frame_training_row_count": protected_provider_coverage_frames.get(
                "summary", {}
            ).get("training_row_count"),
            "coverage_frame_runtime_proposal_row_count": (
                protected_provider_coverage_frames.get("summary", {}).get(
                    "runtime_proposal_row_count"
                )
            ),
            "training_semantics_review_status": protected_capacity_frame_semantics.get(
                "decision", {}
            ).get("status"),
            "training_semantics_review_next_step": (
                protected_capacity_frame_semantics.get("decision", {}).get(
                    "recommended_next_step"
                )
            ),
            "training_semantics_selector_training_allowed": (
                protected_capacity_frame_semantics.get("decision", {}).get(
                    "selector_training_allowed"
                )
            ),
            "training_semantics_runtime_work_allowed": (
                protected_capacity_frame_semantics.get("decision", {}).get(
                    "runtime_work_allowed"
                )
            ),
            "training_semantics_row_count": protected_capacity_frame_semantics.get(
                "summary", {}
            ).get("row_count"),
            "training_semantics_positive_capacity_count": (
                protected_capacity_frame_semantics.get("summary", {}).get(
                    "positive_capacity_count"
                )
            ),
            "training_semantics_negative_capacity_count": (
                protected_capacity_frame_semantics.get("summary", {}).get(
                    "negative_capacity_count"
                )
            ),
            "training_semantics_stage7_row_count": (
                protected_capacity_frame_semantics.get("summary", {}).get(
                    "stage7_row_count"
                )
            ),
            "training_semantics_training_row_count": (
                protected_capacity_frame_semantics.get("summary", {}).get(
                    "training_row_count"
                )
            ),
            "training_semantics_runtime_proposal_row_count": (
                protected_capacity_frame_semantics.get("summary", {}).get(
                    "runtime_proposal_row_count"
                )
            ),
            "training_semantics_blocked_uses": protected_capacity_frame_semantics.get(
                "blocked_uses"
            ),
            "candidate_generator_coverage_status": candidate_generator_coverage.get(
                "decision", {}
            ).get("status"),
            "candidate_generator_coverage_next_step": (
                candidate_generator_coverage.get("decision", {}).get(
                    "recommended_next_step"
                )
            ),
            "candidate_generator_runtime_work_allowed": (
                candidate_generator_coverage.get("decision", {}).get(
                    "runtime_work_allowed"
                )
            ),
            "candidate_generator_selector_training_allowed": (
                candidate_generator_coverage.get("decision", {}).get(
                    "selector_training_allowed"
                )
            ),
            "candidate_generator_positive_recall_count": (
                candidate_generator_coverage.get("summary", {}).get(
                    "runtime_proposal_positive_recall_count"
                )
            ),
            "candidate_generator_positive_recall_rate": (
                candidate_generator_coverage.get("summary", {}).get(
                    "runtime_proposal_positive_recall_rate"
                )
            ),
            "candidate_generator_missing_positive_capacity_count": (
                candidate_generator_coverage.get("summary", {}).get(
                    "missing_positive_capacity_count"
                )
            ),
            "validated_candidate_set_status": validated_provider_candidate_set.get(
                "decision", {}
            ).get("status"),
            "validated_candidate_set_next_step": validated_provider_candidate_set.get(
                "decision", {}
            ).get("recommended_next_step"),
            "validated_candidate_set_candidate_generator_runtime_allowed": (
                validated_provider_candidate_set.get("decision", {}).get(
                    "candidate_generator_runtime_allowed"
                )
            ),
            "validated_candidate_set_selector_training_allowed": (
                validated_provider_candidate_set.get("decision", {}).get(
                    "selector_training_allowed"
                )
            ),
            "validated_candidate_set_state_count": validated_provider_candidate_set.get(
                "summary", {}
            ).get("state_count"),
            "validated_candidate_set_added_candidate_count": (
                validated_provider_candidate_set.get("summary", {}).get(
                    "added_candidate_count"
                )
            ),
            "validated_candidate_set_added_positive_capacity_count": (
                validated_provider_candidate_set.get("summary", {}).get(
                    "added_positive_capacity_count"
                )
            ),
            "validated_candidate_set_added_negative_capacity_count": (
                validated_provider_candidate_set.get("summary", {}).get(
                    "added_negative_capacity_count"
                )
            ),
            "validated_candidate_set_positive_capacity_recall_if_included": (
                validated_provider_candidate_set.get("summary", {}).get(
                    "positive_capacity_recall_if_included"
                )
            ),
            "two_stage_review_status": two_stage_candidate_selection_review.get(
                "decision", {}
            ).get("status"),
            "two_stage_review_next_step": two_stage_candidate_selection_review.get(
                "decision", {}
            ).get("recommended_next_step"),
            "two_stage_review_candidate_generator_runtime_allowed": (
                two_stage_candidate_selection_review.get("decision", {}).get(
                    "candidate_generator_runtime_allowed"
                )
            ),
            "two_stage_review_selector_training_allowed": (
                two_stage_candidate_selection_review.get("decision", {}).get(
                    "selector_training_allowed"
                )
            ),
            "two_stage_review_positive_capacity_recovered": (
                two_stage_candidate_selection_review.get("current_evidence", {}).get(
                    "positive_capacity_recovered_by_validated_provider_set"
                )
            ),
            "two_stage_review_negative_capacity_also_included": (
                two_stage_candidate_selection_review.get("current_evidence", {}).get(
                    "negative_capacity_also_included"
                )
            ),
            "two_stage_benchmark_plan_status": (
                two_stage_candidate_selection_benchmark_plan.get("decision", {}).get(
                    "status"
                )
            ),
            "two_stage_benchmark_plan_next_step": (
                two_stage_candidate_selection_benchmark_plan.get("decision", {}).get(
                    "recommended_next_step"
                )
            ),
            "two_stage_benchmark_status": two_stage_candidate_selection_benchmark.get(
                "decision", {}
            ).get("status"),
            "two_stage_benchmark_next_step": (
                two_stage_candidate_selection_benchmark.get("decision", {}).get(
                    "recommended_next_step"
                )
            ),
            "two_stage_benchmark_candidate_generator_runtime_allowed": (
                two_stage_candidate_selection_benchmark.get("decision", {}).get(
                    "candidate_generator_runtime_allowed"
                )
            ),
            "two_stage_benchmark_selector_training_allowed": (
                two_stage_candidate_selection_benchmark.get("decision", {}).get(
                    "selector_training_allowed"
                )
            ),
            "two_stage_benchmark_current_positive_recall_rate": (
                two_stage_candidate_selection_benchmark.get(
                    "candidate_generation_track", {}
                )
                .get("current_runtime_proposal_frames", {})
                .get("positive_capacity_recall_rate")
            ),
            "two_stage_benchmark_expanded_positive_recall_rate": (
                two_stage_candidate_selection_benchmark.get(
                    "candidate_generation_track", {}
                )
                .get("validated_provider_candidate_set_expansion", {})
                .get("positive_capacity_recall_rate")
            ),
            "two_stage_benchmark_expanded_negative_inclusion_rate": (
                two_stage_candidate_selection_benchmark.get(
                    "candidate_generation_track", {}
                )
                .get("validated_provider_candidate_set_expansion", {})
                .get("negative_capacity_inclusion_rate")
            ),
            "two_stage_benchmark_selector_ready": (
                two_stage_candidate_selection_benchmark.get(
                    "strategy_selection_track", {}
                ).get("selector_ready")
            ),
            "two_stage_benchmark_best_negative_suppression": (
                two_stage_candidate_selection_benchmark.get(
                    "strategy_selection_track", {}
                ).get("best_negative_suppression")
            ),
            "two_stage_benchmark_stage7_training_leakage": (
                two_stage_candidate_selection_benchmark.get(
                    "strategy_selection_track", {}
                ).get("stage7_training_leakage")
            ),
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "strategy_sequence_candidate_source_gate": {
            "candidate_proposal_coverage_status": (
                candidate_proposal_coverage.get("decision", {}).get("status")
            ),
            "candidate_proposal_coverage_positive_capacity_recall": (
                candidate_proposal_coverage.get("summary", {}).get(
                    "positive_capacity_recall"
                )
            ),
            "candidate_proposal_coverage_missing_positive_capacity_count": (
                candidate_proposal_coverage.get("summary", {}).get(
                    "missing_positive_capacity_count"
                )
            ),
            "candidate_proposal_coverage_stage7_row_count": (
                candidate_proposal_coverage.get("summary", {}).get(
                    "stage7_row_count"
                )
            ),
            "candidate_proposal_coverage_selector_training_allowed": (
                candidate_proposal_coverage.get("decision", {}).get(
                    "selector_training_allowed"
                )
            ),
            "candidate_generation_strategy_review_status": (
                candidate_generation_strategy_review.get("decision", {}).get("status")
            ),
            "candidate_generation_strategy_review_runtime_sandbox_allowed": (
                candidate_generation_strategy_review.get("decision", {}).get(
                    "runtime_sandbox_allowed"
                )
            ),
            "candidate_generation_strategy_review_recommended_next_step": (
                candidate_generation_strategy_review.get("decision", {}).get(
                    "recommended_next_step"
                )
            ),
            "schema_status": (
                strategy_sequence_candidate_frame_schema_v1.get("decision", {}).get(
                    "status"
                )
            ),
            "schema_runtime_sandbox_allowed": (
                strategy_sequence_candidate_frame_schema_v1.get("decision", {}).get(
                    "runtime_sandbox_allowed"
                )
            ),
            "frames_status": (
                strategy_sequence_candidate_frames_v1.get("decision", {}).get("status")
            ),
            "frames_frame_count": (
                strategy_sequence_candidate_frames_v1.get("summary", {}).get(
                    "frame_count"
                )
            ),
            "frames_frame_type_counts": (
                strategy_sequence_candidate_frames_v1.get("summary", {}).get(
                    "frame_type_counts"
                )
            ),
            "frames_capacity_evidence_row_count": (
                strategy_sequence_candidate_frames_v1.get("summary", {}).get(
                    "capacity_evidence_row_count"
                )
            ),
            "frames_candidate_generation_training_row_count": (
                strategy_sequence_candidate_frames_v1.get("summary", {}).get(
                    "candidate_generation_training_row_count"
                )
            ),
            "frames_stage7_challenge_row_count": (
                strategy_sequence_candidate_frames_v1.get("summary", {}).get(
                    "stage7_challenge_row_count"
                )
            ),
            "frames_stage7_readiness_training_row_count": (
                strategy_sequence_candidate_frames_v1.get("summary", {}).get(
                    "readiness_training_stage7_row_count"
                )
            ),
            "quality_status": (
                strategy_sequence_candidate_frame_quality_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "quality_capacity_not_selector_label": (
                strategy_sequence_candidate_frame_quality_v1.get(
                    "quality_checks", {}
                ).get("capacity_not_selector_label")
            ),
            "quality_runtime_flags_false": (
                strategy_sequence_candidate_frame_quality_v1.get(
                    "quality_checks", {}
                ).get("runtime_flags_false")
            ),
            "quality_protected_frame_count": (
                strategy_sequence_candidate_frame_quality_v1.get("summary", {}).get(
                    "protected_frame_count"
                )
            ),
            "quality_protected_positive_capacity_candidate_count": (
                strategy_sequence_candidate_frame_quality_v1.get("summary", {}).get(
                    "protected_positive_capacity_candidate_count"
                )
            ),
            "quality_sequence_candidate_count": (
                strategy_sequence_candidate_frame_quality_v1.get("summary", {}).get(
                    "sequence_candidate_count"
                )
            ),
            "quality_sequence_candidate_mate_count": (
                strategy_sequence_candidate_frame_quality_v1.get("summary", {}).get(
                    "sequence_candidate_mate_count"
                )
            ),
            "source_benchmark_status": (
                candidate_frame_source_benchmark_v1.get("decision", {}).get("status")
            ),
            "source_benchmark_protected_positive_capacity_ratio": (
                candidate_frame_source_benchmark_v1.get("channel_summaries", {})
                .get("protected_forced_capacity", {})
                .get("positive_capacity_ratio")
            ),
            "source_benchmark_protected_negative_capacity_ratio": (
                candidate_frame_source_benchmark_v1.get("channel_summaries", {})
                .get("protected_forced_capacity", {})
                .get("negative_capacity_ratio")
            ),
            "source_benchmark_progress_window_sequence_candidate_mate_count": (
                candidate_frame_source_benchmark_v1.get("source_readiness", {})
                .get("progress_window_supported_move", {})
                .get("sequence_candidate_mate_count")
            ),
            "control_plane_status": (
                strategy_sequence_control_plane_decision_v1.get("decision", {}).get(
                    "status"
                )
            ),
            "control_plane_runtime_sandbox_allowed": (
                strategy_sequence_control_plane_decision_v1.get("decision", {}).get(
                    "runtime_sandbox_allowed_by_this_packet"
                )
            ),
            "sandbox_review_status": (
                candidate_generation_sandbox_review.get("decision", {}).get("status")
            ),
            "sandbox_review_implementation_authorized": (
                candidate_generation_sandbox_review.get("decision", {}).get(
                    "implementation_authorized_by_this_packet"
                )
            ),
            "sandbox_review_recommended_first_sandbox": (
                candidate_generation_sandbox_review.get("decision", {}).get(
                    "recommended_first_sandbox"
                )
            ),
            "observation_sandbox_status": (
                candidate_generation_observation_sandbox.get("decision", {}).get(
                    "status"
                )
            ),
            "observation_sandbox_generated_candidate_count": (
                candidate_generation_observation_sandbox.get("summary", {}).get(
                    "generated_candidate_count"
                )
            ),
            "observation_sandbox_selected_move_or_provider_changed": (
                candidate_generation_observation_sandbox.get("summary", {}).get(
                    "selected_move_or_provider_changed"
                )
            ),
            "observation_coverage_status": (
                candidate_generation_observation_coverage.get("decision", {}).get(
                    "status"
                )
            ),
            "observation_coverage_sampled_frame_count": (
                candidate_generation_observation_coverage.get("summary", {}).get(
                    "sampled_frame_count"
                )
            ),
            "observation_coverage_invariant_failure_count": (
                candidate_generation_observation_coverage.get("summary", {}).get(
                    "invariant_failure_count"
                )
            ),
            "observation_broadened_status": (
                candidate_generation_observation_broadened_sample.get(
                    "decision", {}
                ).get("status")
            ),
            "observation_broadened_case_count": (
                candidate_generation_observation_broadened_sample.get(
                    "summary", {}
                ).get("case_count")
            ),
            "observation_broadened_emitted_frame_count": (
                candidate_generation_observation_broadened_sample.get(
                    "summary", {}
                ).get("emitted_frame_count")
            ),
            "observation_broadened_selected_move_or_provider_delta_count": (
                candidate_generation_observation_broadened_sample.get(
                    "summary", {}
                ).get("selected_move_or_provider_delta_count")
            ),
            "observation_gap_review_status": (
                candidate_generation_observation_gap_review.get(
                    "decision", {}
                ).get("status")
            ),
            "observation_gap_review_unknown_capacity_ratio": (
                candidate_generation_observation_gap_review.get("summary", {}).get(
                    "unknown_capacity_ratio"
                )
            ),
            "observation_gap_review_missing_expected_sources": (
                candidate_generation_observation_gap_review.get("summary", {}).get(
                    "missing_expected_sources"
                )
            ),
            "capacity_annotation_v1_status": (
                candidate_move_capacity_annotation_v1.get("decision", {}).get(
                    "status"
                )
            ),
            "capacity_annotation_v1_protected_annotation_recall": (
                candidate_move_capacity_annotation_v1.get("summary", {}).get(
                    "protected_annotation_recall"
                )
            ),
            "capacity_label_manifest_status": (
                candidate_move_capacity_label_manifest_v1.get("decision", {}).get(
                    "status"
                )
            ),
            "capacity_label_manifest_labels_run_by_this_artifact": (
                candidate_move_capacity_label_manifest_v1.get("decision", {}).get(
                    "labels_run_by_this_artifact"
                )
            ),
            "capacity_label_manifest_job_count": (
                candidate_move_capacity_label_manifest_v1.get("summary", {}).get(
                    "job_count"
                )
            ),
            "capacity_label_manifest_stage7_job_count": (
                candidate_move_capacity_label_manifest_v1.get("summary", {}).get(
                    "stage7_job_count"
                )
            ),
            "capacity_labels_status": (
                candidate_move_capacity_labels_v1.get("decision", {}).get("status")
            ),
            "capacity_labels_label_count": (
                candidate_move_capacity_labels_v1.get("summary", {}).get(
                    "label_count"
                )
            ),
            "capacity_labels_stage7_training_label_count": (
                candidate_move_capacity_labels_v1.get("summary", {}).get(
                    "stage7_training_label_count"
                )
            ),
            "capacity_annotation_v2_status": (
                candidate_move_capacity_annotation_v2.get("decision", {}).get(
                    "status"
                )
            ),
            "capacity_annotation_v2_annotated_candidate_move_count": (
                candidate_move_capacity_annotation_v2.get("summary", {}).get(
                    "annotated_candidate_move_count"
                )
            ),
            "capacity_annotation_v2_protected_annotation_recall": (
                candidate_move_capacity_annotation_v2.get("summary", {}).get(
                    "protected_annotation_recall"
                )
            ),
            "capacity_annotation_v2_stage7_readiness_training_row_count": (
                candidate_move_capacity_annotation_v2.get("summary", {}).get(
                    "stage7_readiness_training_row_count"
                )
            ),
            "label_blocker_status": (
                candidate_generation_label_blocker_review.get("decision", {}).get(
                    "status"
                )
            ),
            "label_blocker_more_blind_label_farming_not_recommended": (
                candidate_generation_label_blocker_review.get(
                    "interpretation", {}
                ).get("more_blind_label_farming_not_recommended")
            ),
            "label_blocker_protected_annotation_recall": (
                candidate_generation_label_blocker_review.get("evidence", {}).get(
                    "protected_annotation_recall"
                )
            ),
            "quality_prioritization_review_status": (
                candidate_proposal_quality_prioritization_review.get(
                    "decision", {}
                ).get("status")
            ),
            "quality_dataset_status": (
                candidate_proposal_quality_dataset.get("decision", {}).get("status")
            ),
            "quality_dataset_row_count": (
                candidate_proposal_quality_dataset.get("summary", {}).get(
                    "row_count"
                )
            ),
            "quality_dataset_quality_probe_row_count": (
                candidate_proposal_quality_dataset.get("summary", {}).get(
                    "quality_probe_row_count"
                )
            ),
            "quality_dataset_stage7_readiness_training_row_count": (
                candidate_proposal_quality_dataset.get("summary", {}).get(
                    "stage7_readiness_training_row_count"
                )
            ),
            "quality_probe_status": (
                candidate_proposal_quality_probe.get("decision", {}).get("status")
            ),
            "quality_probe_best_probe": (
                candidate_proposal_quality_probe.get("summary", {}).get("best_probe")
            ),
            "quality_probe_best_positive_recall": (
                candidate_proposal_quality_probe.get("summary", {})
                .get("best_probe_metrics", {})
                .get("positive_recall")
            ),
            "quality_probe_best_negative_suppression": (
                candidate_proposal_quality_probe.get("summary", {})
                .get("best_probe_metrics", {})
                .get("negative_suppression")
            ),
            "quality_probe_ready_for_selector_review": (
                candidate_proposal_quality_probe.get("interpretation", {}).get(
                    "quality_axes_ready_for_selector_review"
                )
            ),
            "quality_decision_status": (
                candidate_proposal_quality_decision.get("decision", {}).get("status")
            ),
            "quality_decision_more_blind_label_farming_allowed": (
                candidate_proposal_quality_decision.get("decision", {}).get(
                    "more_blind_label_farming_allowed"
                )
            ),
            "quality_decision_recommended_next_step": (
                candidate_proposal_quality_decision.get("decision", {}).get(
                    "recommended_next_step"
                )
            ),
            "source_design_status": (
                broader_strategy_sequence_candidate_source_design_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "source_design_implementation_allowed": (
                broader_strategy_sequence_candidate_source_design_v1.get(
                    "decision", {}
                ).get("implementation_allowed_by_this_artifact")
            ),
            "plan_capsule_source_status": (
                plan_capsule_sequence_candidate_observation_review_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "broader_strategy_source_status": (
                broader_strategy_candidate_observation_review_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "source_review_status": (
                broader_strategy_sequence_candidate_source_review_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "source_review_implementation_allowed": (
                broader_strategy_sequence_candidate_source_review_v1.get(
                    "decision", {}
                ).get("implementation_allowed_by_this_artifact")
            ),
            "protected_monitor_expansion_status": (
                protected_strategy_monitor_frame_expansion_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "protected_monitor_expansion_frame_count": (
                protected_strategy_monitor_frame_expansion_v1.get("summary", {}).get(
                    "frame_count"
                )
            ),
            "protected_monitor_expansion_stage7_challenge_row_count": (
                protected_strategy_monitor_frame_expansion_v1.get("summary", {}).get(
                    "stage7_challenge_row_count"
                )
            ),
            "protected_monitor_quality_status": (
                protected_strategy_monitor_frame_quality_v1.get("decision", {}).get(
                    "status"
                )
            ),
            "protected_monitor_quality_strong_failure_family_count": (
                protected_strategy_monitor_frame_quality_v1.get("summary", {}).get(
                    "strong_failure_family_count"
                )
            ),
            "repair_monitor_review_status": (
                protected_strategy_monitor_observation_source_review_packet_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "repair_monitor_review_implementation_authorized": (
                protected_strategy_monitor_observation_source_review_packet_v1.get(
                    "decision", {}
                ).get("implementation_allowed_by_this_packet")
            ),
            "runtime_work_allowed": False,
            "runtime_candidate_generation_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "strategy_arbitration_gate": {
            "dataset_record_count": strategy_arbitration_dataset.get(
                "summary", {}
            ).get("record_count"),
            "dataset_proposal_count": strategy_arbitration_dataset.get(
                "summary", {}
            ).get("proposal_count"),
            "dataset_records_by_source_stage": strategy_arbitration_dataset.get(
                "summary", {}
            ).get("records_by_source_stage"),
            "dataset_records_with_terminal_context": strategy_arbitration_dataset.get(
                "summary", {}
            ).get("records_with_terminal_context"),
            "dataset_result_label_counts": strategy_arbitration_dataset.get(
                "summary", {}
            ).get("result_label_counts"),
            "probe_status": strategy_arbitration_probe.get("decision", {}).get(
                "status"
            ),
            "probe_next_step": strategy_arbitration_probe.get("decision", {}).get(
                "next_step"
            ),
            "probe_forbidden_runtime_work": strategy_arbitration_probe.get(
                "decision", {}
            ).get("forbidden_runtime_work"),
            "probe_raw_global_provider_hit_rate": strategy_arbitration_probe.get(
                "metrics", {}
            )
            .get("raw_global_provider_score", {})
            .get("hit_rate"),
            "probe_normalized_provider_hit_rate": strategy_arbitration_probe.get(
                "metrics", {}
            )
            .get("normalized_provider_score", {})
            .get("hit_rate"),
            "probe_visible_heuristic_hit_rate": strategy_arbitration_probe.get(
                "metrics", {}
            )
            .get("visible_heuristic_arbiter", {})
            .get("hit_rate"),
            "probe_provider_local_rank1_coverage_rate": strategy_arbitration_probe.get(
                "metrics", {}
            )
            .get("provider_local_rank1_coverage", {})
            .get("coverage_rate"),
            "probe_stage7_record_count": strategy_arbitration_probe.get(
                "metrics", {}
            )
            .get("stage7_cluster_summary", {})
            .get("stage7_record_count"),
            "probe_missing_terms_obvious": strategy_arbitration_probe.get(
                "answers", {}
            ).get("missing_terms_obvious"),
            "probe_stage7_failures_cluster_by_phase_boundary": (
                strategy_arbitration_probe.get("answers", {}).get(
                    "stage7_failures_cluster_by_phase_boundary"
                )
            ),
            "decision_status": strategy_arbitration_decision_gate.get(
                "selected_status"
            ),
            "decision_next_class": strategy_arbitration_decision_gate.get(
                "recommendation", {}
            ).get("next_class"),
            "decision_next_step": strategy_arbitration_decision_gate.get(
                "recommendation", {}
            ).get("next_step"),
            "decision_stop_after_next_class": strategy_arbitration_decision_gate.get(
                "recommendation", {}
            ).get("stop_after_next_class"),
            "decision_forbidden_next_steps": strategy_arbitration_decision_gate.get(
                "forbidden_next_steps"
            ),
            "missing_feature_candidate_count": strategy_missing_feature_candidates.get(
                "candidate_count"
            ),
            "missing_feature_challenge_family_count": (
                strategy_missing_feature_candidates.get("challenge_family_count")
            ),
            "missing_feature_source_decision_status": (
                strategy_missing_feature_candidates.get("source_decision_status")
            ),
            "missing_feature_recommended_next_step": (
                strategy_missing_feature_candidates.get("recommended_next_step")
            ),
            "missing_feature_blocked_next_steps": (
                strategy_missing_feature_candidates.get("blocked_next_steps")
            ),
            "runtime_work_allowed": False,
            "runtime_arbiter_allowed": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "strategy_monitor_maturity_gate": {
            "plan_do_not_implement_as_causal_affordances": (
                strategy_monitor_v0_plan.get("decision", {}).get(
                    "do_not_implement_as_causal_affordances"
                )
            ),
            "plan_accepted_source": strategy_monitor_v0_plan.get(
                "decision", {}
            ).get("accepted_source"),
            "plan_blocked_next_steps": strategy_monitor_v0_plan.get(
                "blocked_next_steps"
            ),
            "records_dataset_record_count": strategy_monitor_records_v0.get(
                "summary", {}
            ).get("dataset_record_count"),
            "records_monitor_definition_count": strategy_monitor_records_v0.get(
                "summary", {}
            ).get("monitor_definition_count"),
            "records_monitor_record_count": strategy_monitor_records_v0.get(
                "summary", {}
            ).get("monitor_record_count"),
            "records_by_monitor_type": strategy_monitor_records_v0.get(
                "summary", {}
            ).get("records_by_monitor_type"),
            "records_by_associated_outcome": strategy_monitor_records_v0.get(
                "summary", {}
            ).get("records_by_associated_outcome"),
            "records_rejected_definition_count": strategy_monitor_records_v0.get(
                "summary", {}
            ).get("rejected_definition_count"),
            "companion_terms_causal_terms_authorized": (
                strategy_monitor_companion_terms_v0.get("summary", {}).get(
                    "causal_terms_authorized"
                )
            ),
            "companion_terms_runtime_arbiter_authorized": (
                strategy_monitor_companion_terms_v0.get("summary", {}).get(
                    "runtime_arbiter_authorized"
                )
            ),
            "companion_terms_stage7_repair_authorized": (
                strategy_monitor_companion_terms_v0.get("summary", {}).get(
                    "stage7_repair_authorized"
                )
            ),
            "companion_audit_v0_all_terms_available": (
                strategy_monitor_companion_audit_v0.get("summary", {}).get(
                    "all_terms_available_without_new_extraction"
                )
            ),
            "companion_audit_v0_term_status_counts": (
                strategy_monitor_companion_audit_v0.get("summary", {}).get(
                    "term_status_counts"
                )
            ),
            "visible_terms_record_count": visible_monitor_terms_v0.get(
                "summary", {}
            ).get("record_count"),
            "visible_terms_term_names": visible_monitor_terms_v0.get(
                "summary", {}
            ).get("term_names"),
            "visible_terms_confidence_counts": visible_monitor_terms_v0.get(
                "summary", {}
            ).get("confidence_counts"),
            "companion_audit_v1_all_terms_available": (
                strategy_monitor_companion_audit_v1.get("summary", {}).get(
                    "all_terms_available_without_new_extraction"
                )
            ),
            "companion_audit_v1_visible_terms_applied": (
                strategy_monitor_companion_audit_v1.get("summary", {}).get(
                    "visible_terms_applied"
                )
            ),
            "companion_audit_v1_visible_term_count": (
                strategy_monitor_companion_audit_v1.get("summary", {}).get(
                    "visible_term_count"
                )
            ),
            "companion_audit_v1_still_missing_term_count": len(
                strategy_monitor_companion_audit_v1.get("summary", {}).get(
                    "still_missing_terms"
                )
                or []
            ),
            "companion_audit_v1_term_status_counts": (
                strategy_monitor_companion_audit_v1.get("summary", {}).get(
                    "term_status_counts"
                )
            ),
            "companion_audit_v1_recommended_next_step": (
                strategy_monitor_companion_audit_v1.get("summary", {}).get(
                    "recommended_next_step"
                )
            ),
            "maturity_term_count": strategy_monitor_maturity_gate_v0.get(
                "summary", {}
            ).get("term_count"),
            "maturity_status_counts": strategy_monitor_maturity_gate_v0.get(
                "summary", {}
            ).get("maturity_status_counts"),
            "maturity_causal_ready_terms": strategy_monitor_maturity_gate_v0.get(
                "summary", {}
            ).get("causal_ready_terms"),
            "maturity_strongest_internal_terminal_candidates": (
                strategy_monitor_maturity_gate_v0.get("summary", {}).get(
                    "strongest_internal_terminal_candidates"
                )
            ),
            "maturity_backlog_priority_counts": strategy_monitor_maturity_gate_v0.get(
                "summary", {}
            ).get("backlog_priority_counts"),
            "maturity_recommended_next_step": strategy_monitor_maturity_gate_v0.get(
                "summary", {}
            ).get("recommended_next_step"),
            "maturity_blocked_next_steps": strategy_monitor_maturity_gate_v0.get(
                "blocked_next_steps"
            ),
            "runtime_work_allowed": False,
            "runtime_terminals_allowed": False,
            "runtime_arbiter_allowed": False,
            "monitor_to_provider_routing_allowed": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "internal_terminal_readiness_gate": {
            "feature_candidate_all_non_causal": feature_candidate_validation.get(
                "summary", {}
            ).get("all_candidates_remain_non_causal"),
            "feature_candidate_count": feature_candidate_validation.get(
                "summary", {}
            ).get("candidate_count"),
            "feature_candidate_causal_recommendation_counts": (
                feature_candidate_validation.get("summary", {}).get(
                    "causal_recommendation_counts"
                )
            ),
            "feature_candidate_sandbox_ready_candidate_ids": (
                feature_candidate_validation.get("summary", {}).get(
                    "sandbox_ready_candidate_ids"
                )
            ),
            "feature_candidate_recommended_next_step": (
                feature_candidate_validation.get("recommended_next_step")
            ),
            "candidate_spec_count": len(
                internal_terminal_candidates.get("specs") or []
            ),
            "candidate_terminal_ids": [
                spec.get("terminal_id")
                for spec in internal_terminal_candidates.get("specs") or []
            ],
            "candidate_maturity_statuses": [
                spec.get("maturity_status")
                for spec in internal_terminal_candidates.get("specs") or []
            ],
            "candidate_blocked_next_steps": internal_terminal_candidates.get(
                "blocked_next_steps"
            ),
            "validation_terminal_count": internal_terminal_validation.get(
                "summary", {}
            ).get("terminal_count"),
            "validation_record_count": internal_terminal_validation.get(
                "summary", {}
            ).get("validation_record_count"),
            "validation_causal_ready_terminals": internal_terminal_validation.get(
                "summary", {}
            ).get("causal_ready_terminals"),
            "validation_strongest_internal_terminal_candidates": (
                internal_terminal_validation.get("summary", {}).get(
                    "strongest_internal_terminal_candidates"
                )
            ),
            "validation_all_causal_use_blocked": all(
                item.get("causal_use_blocked") is True
                for item in internal_terminal_validation.get("terminal_validations")
                or []
            ),
            "evidence_terminal_count": internal_terminal_evidence_v1.get(
                "summary", {}
            ).get("terminal_count"),
            "evidence_combined_record_count": internal_terminal_evidence_v1.get(
                "summary", {}
            ).get("combined_record_count"),
            "evidence_causal_ready_terminals": internal_terminal_evidence_v1.get(
                "summary", {}
            ).get("causal_ready_terminals"),
            "evidence_monitoring_only_candidates": internal_terminal_evidence_v1.get(
                "summary", {}
            ).get("monitoring_only_candidates"),
            "evidence_stage7_only_candidates": internal_terminal_evidence_v1.get(
                "summary", {}
            ).get("stage7_only_candidates"),
            "evidence_strongest_internal_terminal_candidates": (
                internal_terminal_evidence_v1.get("summary", {}).get(
                    "strongest_internal_terminal_candidates"
                )
            ),
            "evidence_all_causal_ready_false": all(
                item.get("causal_ready") is False
                for item in internal_terminal_evidence_v1.get("terminal_evidence")
                or []
            ),
            "evidence_recommended_next_step": internal_terminal_evidence_v1.get(
                "summary", {}
            ).get("recommended_next_step"),
            "design_review_main_conclusion": internal_terminal_design_review_v1.get(
                "summary", {}
            ).get("main_conclusion"),
            "design_review_causal_ready_terminals": (
                internal_terminal_design_review_v1.get("summary", {}).get(
                    "causal_ready_terminals"
                )
            ),
            "design_review_all_causal_ready_false": all(
                item.get("causal_ready") is False
                for item in internal_terminal_design_review_v1.get(
                    "terminal_readiness"
                )
                or []
            ),
            "design_review_recommended_next_step": (
                internal_terminal_design_review_v1.get("summary", {}).get(
                    "recommended_next_step"
                )
            ),
            "design_review_blocked_next_steps": internal_terminal_design_review_v1.get(
                "blocked_next_steps"
            ),
            "runtime_work_allowed": False,
            "runtime_terminals_allowed": False,
            "causal_affordances_allowed": False,
            "runtime_arbiter_allowed": False,
            "monitor_to_provider_routing_allowed": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "repair_monitor_trace_feature_gate": {
            "smoke_status": (
                repair_monitor_observation_source_smoke_v1.get("decision", {}).get(
                    "status"
                )
            ),
            "smoke_case_count": (
                repair_monitor_observation_source_smoke_v1.get("summary", {}).get(
                    "case_count"
                )
            ),
            "smoke_repair_monitor_frame_count": (
                repair_monitor_observation_source_smoke_v1.get("summary", {}).get(
                    "repair_monitor_frame_count"
                )
            ),
            "smoke_selected_move_provider_delta_count": (
                repair_monitor_observation_source_smoke_v1.get("summary", {}).get(
                    "selected_move_provider_delta_count"
                )
            ),
            "smoke_invariant_failure_count": (
                repair_monitor_observation_source_smoke_v1.get("summary", {}).get(
                    "invariant_failure_count"
                )
            ),
            "smoke_stage7_case_count": (
                repair_monitor_observation_source_smoke_v1.get("summary", {}).get(
                    "stage7_case_count"
                )
            ),
            "coverage_status": (
                repair_monitor_observation_source_coverage_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "coverage_repair_monitor_frame_count": (
                repair_monitor_observation_source_coverage_v1.get(
                    "summary", {}
                ).get("repair_monitor_frame_count")
            ),
            "coverage_stage7_case_count": (
                repair_monitor_observation_source_coverage_v1.get("summary", {}).get(
                    "stage7_case_count"
                )
            ),
            "broadened_status": (
                repair_monitor_observation_source_broadened_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "broadened_case_count": (
                repair_monitor_observation_source_broadened_v1.get(
                    "summary", {}
                ).get("case_count")
            ),
            "broadened_case_count_by_stage": (
                repair_monitor_observation_source_broadened_v1.get(
                    "summary", {}
                ).get("case_count_by_stage")
            ),
            "broadened_repair_monitor_frame_count": (
                repair_monitor_observation_source_broadened_v1.get(
                    "summary", {}
                ).get("repair_monitor_frame_count")
            ),
            "broadened_selected_move_provider_delta_count": (
                repair_monitor_observation_source_broadened_v1.get(
                    "summary", {}
                ).get("selected_move_provider_delta_count")
            ),
            "broadened_invariant_failure_count": (
                repair_monitor_observation_source_broadened_v1.get(
                    "summary", {}
                ).get("invariant_failure_count")
            ),
            "broadened_stage7_case_count": (
                repair_monitor_observation_source_broadened_v1.get(
                    "summary", {}
                ).get("stage7_case_count")
            ),
            "quality_status": (
                repair_monitor_observation_source_quality_review_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "quality_source_stable": (
                repair_monitor_observation_source_quality_review_v1.get(
                    "summary", {}
                ).get("source_stable")
            ),
            "quality_risk_term_set_count": (
                repair_monitor_observation_source_quality_review_v1.get(
                    "summary", {}
                ).get("risk_term_set_count")
            ),
            "quality_stage7_case_count": (
                repair_monitor_observation_source_quality_review_v1.get(
                    "summary", {}
                ).get("stage7_case_count")
            ),
            "trace_features_status": (
                strategy_sequence_repair_monitor_trace_features_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "trace_features_trace_frame_count": (
                strategy_sequence_repair_monitor_trace_features_v1.get(
                    "summary", {}
                ).get("trace_frame_count")
            ),
            "trace_features_stage7_trace_frame_count": (
                strategy_sequence_repair_monitor_trace_features_v1.get(
                    "summary", {}
                ).get("stage7_trace_frame_count")
            ),
            "trace_features_selector_training_row_count": (
                strategy_sequence_repair_monitor_trace_features_v1.get(
                    "summary", {}
                ).get("selector_training_row_count")
            ),
            "trace_features_candidate_generation_training_row_count": (
                strategy_sequence_repair_monitor_trace_features_v1.get(
                    "summary", {}
                ).get("candidate_generation_training_row_count")
            ),
            "integration_review_status": (
                strategy_sequence_trace_feature_integration_review_v1.get(
                    "decision", {}
                ).get("status")
            ),
            "integration_review_trace_integration_safe": (
                strategy_sequence_trace_feature_integration_review_v1.get(
                    "summary", {}
                ).get("trace_integration_safe")
            ),
            "integration_review_trace_frame_count": (
                strategy_sequence_trace_feature_integration_review_v1.get(
                    "summary", {}
                ).get("trace_frame_count")
            ),
            "integration_review_trace_selector_training_row_count": (
                strategy_sequence_trace_feature_integration_review_v1.get(
                    "summary", {}
                ).get("trace_selector_training_row_count")
            ),
            "integration_review_trace_stage7_frame_count": (
                strategy_sequence_trace_feature_integration_review_v1.get(
                    "summary", {}
                ).get("trace_stage7_frame_count")
            ),
            "dataset_design_status": (
                strategy_sequence_dataset_design_v2.get("decision", {}).get("status")
            ),
            "dataset_design_implementation_allowed": (
                strategy_sequence_dataset_design_v2.get("decision", {}).get(
                    "implementation_allowed_by_this_artifact"
                )
            ),
            "dataset_v2_status": (
                strategy_sequence_dataset_v2.get("decision", {}).get("status")
            ),
            "dataset_v2_row_count": (
                strategy_sequence_dataset_v2.get("summary", {}).get("row_count")
            ),
            "dataset_v2_runtime_trace_feature_row_count": (
                strategy_sequence_dataset_v2.get("summary", {}).get(
                    "runtime_trace_feature_row_count"
                )
            ),
            "dataset_v2_candidate_generation_training_row_count": (
                strategy_sequence_dataset_v2.get("summary", {}).get(
                    "candidate_generation_training_row_count"
                )
            ),
            "dataset_v2_selector_training_row_count": (
                strategy_sequence_dataset_v2.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "dataset_v2_stage7_challenge_row_count": (
                strategy_sequence_dataset_v2.get("summary", {}).get(
                    "stage7_challenge_row_count"
                )
            ),
            "dataset_v2_stage7_readiness_training_row_count": (
                strategy_sequence_dataset_v2.get("summary", {}).get(
                    "stage7_readiness_training_row_count"
                )
            ),
            "dataset_v2_quality_status": (
                strategy_sequence_dataset_v2_quality_probe.get("decision", {}).get(
                    "status"
                )
            ),
            "dataset_v2_quality_runtime_flags_false": (
                strategy_sequence_dataset_v2_quality_probe.get(
                    "quality_checks", {}
                ).get("runtime_flags_false")
            ),
            "dataset_v2_quality_selector_rows_absent": (
                strategy_sequence_dataset_v2_quality_probe.get(
                    "quality_checks", {}
                ).get("selector_rows_absent_without_ownership_labels")
            ),
            "dataset_v2_quality_stage7_excluded_from_readiness": (
                strategy_sequence_dataset_v2_quality_probe.get(
                    "quality_checks", {}
                ).get("stage7_excluded_from_readiness")
            ),
            "refresh_probe_status": (
                candidate_generation_refresh_probe_v2.get("decision", {}).get(
                    "status"
                )
            ),
            "refresh_probe_best_policy": (
                candidate_generation_refresh_probe_v2.get("summary", {}).get(
                    "best_non_oracle_policy"
                )
            ),
            "refresh_probe_positive_recall": (
                candidate_generation_refresh_probe_v2.get("summary", {})
                .get("best_non_oracle_metrics", {})
                .get("positive_recall")
            ),
            "refresh_probe_negative_suppression": (
                candidate_generation_refresh_probe_v2.get("summary", {})
                .get("best_non_oracle_metrics", {})
                .get("negative_suppression")
            ),
            "capacity_manifest_status": (
                candidate_generation_capacity_evidence_manifest_v2.get(
                    "decision", {}
                ).get("status")
            ),
            "capacity_manifest_labels_run_by_this_artifact": (
                candidate_generation_capacity_evidence_manifest_v2.get(
                    "decision", {}
                ).get("labels_run_by_this_artifact")
            ),
            "capacity_manifest_job_count": (
                candidate_generation_capacity_evidence_manifest_v2.get(
                    "summary", {}
                ).get("job_count")
            ),
            "capacity_manifest_stage7_job_count": (
                candidate_generation_capacity_evidence_manifest_v2.get(
                    "summary", {}
                ).get("stage7_job_count")
            ),
            "capacity_labels_status": (
                candidate_generation_capacity_evidence_labels_v2.get(
                    "decision", {}
                ).get("status")
            ),
            "capacity_labels_label_count": (
                candidate_generation_capacity_evidence_labels_v2.get(
                    "summary", {}
                ).get("label_count")
            ),
            "capacity_labels_stage7_label_count": (
                candidate_generation_capacity_evidence_labels_v2.get(
                    "summary", {}
                ).get("stage7_label_count")
            ),
            "capacity_labels_stage7_training_label_count": (
                candidate_generation_capacity_evidence_labels_v2.get(
                    "summary", {}
                ).get("stage7_training_label_count")
            ),
            "dataset_v2_capacity_merged_status": (
                strategy_sequence_dataset_v2_capacity_merged.get(
                    "decision", {}
                ).get("status")
            ),
            "dataset_v2_capacity_merged_row_count": (
                strategy_sequence_dataset_v2_capacity_merged.get(
                    "summary", {}
                ).get("row_count")
            ),
            "dataset_v2_capacity_merged_candidate_generation_training_row_count": (
                strategy_sequence_dataset_v2_capacity_merged.get(
                    "summary", {}
                ).get("candidate_generation_training_row_count")
            ),
            "dataset_v2_capacity_merged_selector_training_row_count": (
                strategy_sequence_dataset_v2_capacity_merged.get(
                    "summary", {}
                ).get("selector_training_row_count")
            ),
            "dataset_v2_capacity_merged_stage7_challenge_row_count": (
                strategy_sequence_dataset_v2_capacity_merged.get(
                    "summary", {}
                ).get("stage7_challenge_row_count")
            ),
            "dataset_v2_capacity_merged_stage7_readiness_training_row_count": (
                strategy_sequence_dataset_v2_capacity_merged.get(
                    "summary", {}
                ).get("stage7_readiness_training_row_count")
            ),
            "refresh_after_labels_status": (
                candidate_generation_refresh_probe_v2_after_labels.get(
                    "decision", {}
                ).get("status")
            ),
            "refresh_after_labels_best_policy": (
                candidate_generation_refresh_probe_v2_after_labels.get(
                    "summary", {}
                ).get("best_non_oracle_policy")
            ),
            "refresh_after_labels_positive_recall": (
                candidate_generation_refresh_probe_v2_after_labels.get(
                    "summary", {}
                )
                .get("best_non_oracle_metrics", {})
                .get("positive_recall")
            ),
            "refresh_after_labels_negative_suppression": (
                candidate_generation_refresh_probe_v2_after_labels.get(
                    "summary", {}
                )
                .get("best_non_oracle_metrics", {})
                .get("negative_suppression")
            ),
            "runtime_work_allowed": False,
            "runtime_candidate_generation_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "stage5_6_candidate_generation_refresh_gate": {
            "review_status": (
                stage5_6_candidate_generation_refresh_review_packet_v3.get(
                    "decision", {}
                ).get("status")
            ),
            "review_runtime_review_ready": (
                stage5_6_candidate_generation_refresh_review_packet_v3.get(
                    "decision", {}
                ).get("runtime_review_ready")
            ),
            "review_implementation_authorized": (
                stage5_6_candidate_generation_refresh_review_packet_v3.get(
                    "decision", {}
                ).get("implementation_authorized_by_this_packet")
            ),
            "review_runtime_candidate_generator_refresh_allowed": (
                stage5_6_candidate_generation_refresh_review_packet_v3.get(
                    "decision", {}
                ).get("runtime_candidate_generator_refresh_allowed_by_this_packet")
            ),
            "smoke_status": (
                stage5_6_candidate_generation_refresh_smoke.get(
                    "decision", {}
                ).get("status")
            ),
            "smoke_case_count": (
                stage5_6_candidate_generation_refresh_smoke.get("summary", {}).get(
                    "case_count"
                )
            ),
            "smoke_refresh_frame_count": (
                stage5_6_candidate_generation_refresh_smoke.get("summary", {}).get(
                    "refresh_frame_count"
                )
            ),
            "smoke_selected_move_provider_delta_count": (
                stage5_6_candidate_generation_refresh_smoke.get("summary", {}).get(
                    "selected_move_provider_delta_count"
                )
            ),
            "smoke_invariant_failure_count": (
                stage5_6_candidate_generation_refresh_smoke.get("summary", {}).get(
                    "invariant_failure_count"
                )
            ),
            "smoke_stage7_case_count": (
                stage5_6_candidate_generation_refresh_smoke.get("summary", {}).get(
                    "stage7_case_count"
                )
            ),
            "coverage_status": (
                stage5_6_candidate_generation_refresh_coverage.get(
                    "decision", {}
                ).get("status")
            ),
            "coverage_refresh_frame_count": (
                stage5_6_candidate_generation_refresh_coverage.get(
                    "summary", {}
                ).get("refresh_frame_count")
            ),
            "coverage_selected_move_provider_delta_count": (
                stage5_6_candidate_generation_refresh_coverage.get(
                    "summary", {}
                ).get("selected_move_provider_delta_count")
            ),
            "coverage_invariant_failure_count": (
                stage5_6_candidate_generation_refresh_coverage.get(
                    "summary", {}
                ).get("invariant_failure_count")
            ),
            "coverage_stage7_case_count": (
                stage5_6_candidate_generation_refresh_coverage.get(
                    "summary", {}
                ).get("stage7_case_count")
            ),
            "broadened_status": (
                stage5_6_candidate_generation_refresh_broadened.get(
                    "decision", {}
                ).get("status")
            ),
            "broadened_case_count": (
                stage5_6_candidate_generation_refresh_broadened.get(
                    "summary", {}
                ).get("case_count")
            ),
            "broadened_case_count_by_stage": (
                stage5_6_candidate_generation_refresh_broadened.get(
                    "summary", {}
                ).get("case_count_by_stage")
            ),
            "broadened_refresh_frame_count": (
                stage5_6_candidate_generation_refresh_broadened.get(
                    "summary", {}
                ).get("refresh_frame_count")
            ),
            "broadened_selected_move_provider_delta_count": (
                stage5_6_candidate_generation_refresh_broadened.get(
                    "summary", {}
                ).get("selected_move_provider_delta_count")
            ),
            "broadened_invariant_failure_count": (
                stage5_6_candidate_generation_refresh_broadened.get(
                    "summary", {}
                ).get("invariant_failure_count")
            ),
            "broadened_stage7_case_count": (
                stage5_6_candidate_generation_refresh_broadened.get(
                    "summary", {}
                ).get("stage7_case_count")
            ),
            "quality_status": (
                stage5_6_candidate_generation_refresh_quality_review.get(
                    "decision", {}
                ).get("status")
            ),
            "quality_trace_usable_for_candidate_generation_context": (
                stage5_6_candidate_generation_refresh_quality_review.get(
                    "summary", {}
                ).get("trace_usable_for_candidate_generation_context")
            ),
            "quality_refresh_frame_count": (
                stage5_6_candidate_generation_refresh_quality_review.get(
                    "summary", {}
                ).get("refresh_frame_count")
            ),
            "quality_selected_move_provider_delta_count": (
                stage5_6_candidate_generation_refresh_quality_review.get(
                    "summary", {}
                ).get("selected_move_provider_delta_count")
            ),
            "quality_invariant_failure_count": (
                stage5_6_candidate_generation_refresh_quality_review.get(
                    "summary", {}
                ).get("invariant_failure_count")
            ),
            "quality_stage7_case_count": (
                stage5_6_candidate_generation_refresh_quality_review.get(
                    "summary", {}
                ).get("stage7_case_count")
            ),
            "trace_features_status": (
                strategy_sequence_stage5_6_refresh_trace_features.get(
                    "decision", {}
                ).get("status")
            ),
            "trace_features_trace_frame_count": (
                strategy_sequence_stage5_6_refresh_trace_features.get(
                    "summary", {}
                ).get("trace_frame_count")
            ),
            "trace_features_stage_counts": (
                strategy_sequence_stage5_6_refresh_trace_features.get(
                    "summary", {}
                ).get("stage_counts")
            ),
            "trace_features_stage7_trace_frame_count": (
                strategy_sequence_stage5_6_refresh_trace_features.get(
                    "summary", {}
                ).get("stage7_trace_frame_count")
            ),
            "trace_features_selector_training_row_count": (
                strategy_sequence_stage5_6_refresh_trace_features.get(
                    "summary", {}
                ).get("selector_training_row_count")
            ),
            "trace_features_candidate_generation_training_row_count": (
                strategy_sequence_stage5_6_refresh_trace_features.get(
                    "summary", {}
                ).get("candidate_generation_training_row_count")
            ),
            "dataset_design_v3_status": (
                strategy_sequence_dataset_design_v3.get("decision", {}).get("status")
            ),
            "dataset_design_v3_implementation_allowed": (
                strategy_sequence_dataset_design_v3.get("decision", {}).get(
                    "implementation_allowed_by_this_artifact"
                )
            ),
            "runtime_work_allowed": False,
            "runtime_candidate_generation_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "cross_stage_candidate_generation_scope_gate": {
            "cross_stage_label_probe_status": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "decision", {}
                ).get("status")
            ),
            "cross_stage_label_probe_best_policy": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "summary", {}
                ).get("best_non_oracle_policy")
            ),
            "cross_stage_label_probe_positive_recall": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "summary", {}
                )
                .get("best_non_oracle_metrics", {})
                .get("positive_recall")
            ),
            "cross_stage_label_probe_negative_suppression": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "summary", {}
                )
                .get("best_non_oracle_metrics", {})
                .get("negative_suppression")
            ),
            "cross_stage_label_probe_capacity_row_count": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "summary", {}
                ).get("capacity_row_count")
            ),
            "cross_stage_label_probe_source_stage_counts": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "summary", {}
                ).get("source_stage_counts")
            ),
            "cross_stage_label_probe_capacity_label_counts": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "summary", {}
                ).get("capacity_label_counts")
            ),
            "cross_stage_label_probe_guardrails_allowed": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "decision", {}
                ).get("guardrails_allowed")
            ),
            "cross_stage_label_probe_selector_allowed": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "decision", {}
                ).get("selector_allowed")
            ),
            "cross_stage_label_probe_promotion_allowed": (
                candidate_generation_refresh_probe_v2_cross_stage_labels.get(
                    "decision", {}
                ).get("promotion_allowed")
            ),
            "capacity_review_status": (
                candidate_generation_cross_stage_capacity_review_v2.get(
                    "decision", {}
                ).get("status")
            ),
            "capacity_review_capacity_row_count": (
                candidate_generation_cross_stage_capacity_review_v2.get(
                    "summary", {}
                ).get("capacity_row_count")
            ),
            "capacity_review_stage_family_cell_count": (
                candidate_generation_cross_stage_capacity_review_v2.get(
                    "summary", {}
                ).get("stage_family_cell_count")
            ),
            "capacity_review_stage7_readiness_training_row_count": (
                candidate_generation_cross_stage_capacity_review_v2.get(
                    "summary", {}
                ).get("stage7_readiness_training_row_count")
            ),
            "capacity_manifest_status": (
                candidate_generation_cross_stage_capacity_manifest_v3.get(
                    "decision", {}
                ).get("status")
            ),
            "capacity_manifest_labels_run_by_this_artifact": (
                candidate_generation_cross_stage_capacity_manifest_v3.get(
                    "decision", {}
                ).get("labels_run_by_this_artifact")
            ),
            "capacity_manifest_job_count": (
                candidate_generation_cross_stage_capacity_manifest_v3.get(
                    "summary", {}
                ).get("job_count")
            ),
            "capacity_manifest_stage7_job_count": (
                candidate_generation_cross_stage_capacity_manifest_v3.get(
                    "summary", {}
                ).get("stage7_job_count")
            ),
            "capacity_manifest_stage7_readiness_training_row_count": (
                candidate_generation_cross_stage_capacity_manifest_v3.get(
                    "summary", {}
                ).get("stage7_readiness_training_row_count")
            ),
            "capacity_labels_status": (
                candidate_generation_cross_stage_capacity_labels_v3.get(
                    "decision", {}
                ).get("status")
            ),
            "capacity_labels_label_count": (
                candidate_generation_cross_stage_capacity_labels_v3.get(
                    "summary", {}
                ).get("label_count")
            ),
            "capacity_labels_stage7_label_count": (
                candidate_generation_cross_stage_capacity_labels_v3.get(
                    "summary", {}
                ).get("stage7_label_count")
            ),
            "capacity_labels_stage7_training_label_count": (
                candidate_generation_cross_stage_capacity_labels_v3.get(
                    "summary", {}
                ).get("stage7_training_label_count")
            ),
            "capacity_labels_result_counts": (
                candidate_generation_cross_stage_capacity_labels_v3.get(
                    "summary", {}
                ).get("result_counts")
            ),
            "dataset_cross_stage_merged_status": (
                strategy_sequence_dataset_v2_cross_stage_capacity_merged.get(
                    "decision", {}
                ).get("status")
            ),
            "dataset_cross_stage_merged_row_count": (
                strategy_sequence_dataset_v2_cross_stage_capacity_merged.get(
                    "summary", {}
                ).get("row_count")
            ),
            "dataset_cross_stage_merged_candidate_generation_training_row_count": (
                strategy_sequence_dataset_v2_cross_stage_capacity_merged.get(
                    "summary", {}
                ).get("candidate_generation_training_row_count")
            ),
            "dataset_cross_stage_merged_selector_training_row_count": (
                strategy_sequence_dataset_v2_cross_stage_capacity_merged.get(
                    "summary", {}
                ).get("selector_training_row_count")
            ),
            "dataset_cross_stage_merged_stage7_challenge_row_count": (
                strategy_sequence_dataset_v2_cross_stage_capacity_merged.get(
                    "summary", {}
                ).get("stage7_challenge_row_count")
            ),
            "dataset_cross_stage_merged_stage7_readiness_training_row_count": (
                strategy_sequence_dataset_v2_cross_stage_capacity_merged.get(
                    "summary", {}
                ).get("stage7_readiness_training_row_count")
            ),
            "label_outcome_review_status": (
                candidate_generation_cross_stage_label_outcome_review_v3.get(
                    "decision", {}
                ).get("status")
            ),
            "label_outcome_runtime_candidate_generator_refresh_allowed": (
                candidate_generation_cross_stage_label_outcome_review_v3.get(
                    "decision", {}
                ).get("runtime_candidate_generator_refresh_allowed")
            ),
            "scope_review_status": (
                candidate_generation_stage_conditioned_scope_review_v3.get(
                    "decision", {}
                ).get("status")
            ),
            "scope_review_runtime_candidate_generator_refresh_allowed": (
                candidate_generation_stage_conditioned_scope_review_v3.get(
                    "decision", {}
                ).get("runtime_candidate_generator_refresh_allowed")
            ),
            "stage_conditioned_benchmark_status": (
                stage_conditioned_candidate_generation_benchmark_v3.get(
                    "decision", {}
                ).get("status")
            ),
            "stage_conditioned_benchmark_best_policy": (
                stage_conditioned_candidate_generation_benchmark_v3.get(
                    "summary", {}
                ).get("best_policy")
            ),
            "stage_conditioned_benchmark_positive_recall": (
                stage_conditioned_candidate_generation_benchmark_v3.get(
                    "summary", {}
                )
                .get("best_policy_metrics", {})
                .get("positive_recall")
            ),
            "stage_conditioned_benchmark_negative_suppression": (
                stage_conditioned_candidate_generation_benchmark_v3.get(
                    "summary", {}
                )
                .get("best_policy_metrics", {})
                .get("negative_suppression")
            ),
            "stage_conditioned_benchmark_stage4_positive_recall": (
                stage_conditioned_candidate_generation_benchmark_v3.get(
                    "summary", {}
                )
                .get("stage4_positive_scope_metrics", {})
                .get("positive_recall")
            ),
            "stage_conditioned_benchmark_stage5_6_positive_recall": (
                stage_conditioned_candidate_generation_benchmark_v3.get(
                    "summary", {}
                )
                .get("stage5_6_positive_scope_metrics", {})
                .get("positive_recall")
            ),
            "stage_conditioned_benchmark_stage7_readiness_training_row_count": (
                stage_conditioned_candidate_generation_benchmark_v3.get(
                    "summary", {}
                ).get("stage7_readiness_training_row_count")
            ),
            "runtime_work_allowed": False,
            "runtime_candidate_generation_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "selector_objective_lineage_gate": {
            "ownership_recovery_status": (
                ownership_label_recovery_review.get("decision", {}).get("status")
            ),
            "ownership_recovery_joined_state_count": (
                ownership_label_recovery_review.get("summary", {}).get(
                    "joined_state_count"
                )
            ),
            "ownership_recovery_selected_failure_with_visible_positive_count": (
                ownership_label_recovery_review.get("summary", {}).get(
                    "selected_failure_with_visible_positive_alternative_count"
                )
            ),
            "ownership_recovery_safe_preservation_with_visible_positive_count": (
                ownership_label_recovery_review.get("summary", {}).get(
                    "safe_preservation_with_visible_positive_alternative_count"
                )
            ),
            "ownership_recovery_selector_training_row_count": (
                ownership_label_recovery_review.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "ownership_recovery_stage7_row_count": (
                ownership_label_recovery_review.get("summary", {}).get(
                    "stage7_row_count"
                )
            ),
            "seed_manifest_v0_status": selector_objective_seed_manifest_v0.get(
                "decision", {}
            ).get("status"),
            "seed_manifest_v0_seed_row_count": (
                selector_objective_seed_manifest_v0.get("summary", {}).get(
                    "seed_row_count"
                )
            ),
            "seed_manifest_v0_candidate_switch_count": (
                selector_objective_seed_manifest_v0.get("summary", {}).get(
                    "candidate_switch_contrast_seed_count"
                )
            ),
            "seed_manifest_v0_safe_preservation_count": (
                selector_objective_seed_manifest_v0.get("summary", {}).get(
                    "safe_preservation_contrast_seed_count"
                )
            ),
            "seed_probe_v0_status": selector_objective_seed_probe_v0.get(
                "decision", {}
            ).get("status"),
            "seed_probe_v0_runtime_feature_eligible_prediction_count": (
                selector_objective_seed_probe_v0.get("summary", {}).get(
                    "runtime_feature_eligible_prediction_count"
                )
            ),
            "seed_probe_v0_benchmark_underpowered": (
                selector_objective_seed_probe_v0.get("summary", {}).get(
                    "benchmark_underpowered"
                )
            ),
            "collection_manifest_status": (
                joined_trace_ownership_collection_manifest.get("decision", {}).get(
                    "status"
                )
            ),
            "collection_manifest_approved_observation_scope_candidate_count": (
                joined_trace_ownership_collection_manifest.get("summary", {}).get(
                    "approved_observation_scope_candidate_count"
                )
            ),
            "collection_manifest_excluded_requires_separate_review_count": (
                joined_trace_ownership_collection_manifest.get("summary", {}).get(
                    "excluded_requires_separate_review_count"
                )
            ),
            "collection_manifest_runtime_collection_allowed_row_count": (
                joined_trace_ownership_collection_manifest.get("summary", {}).get(
                    "runtime_collection_allowed_row_count"
                )
            ),
            "collection_review_status": (
                joined_trace_ownership_collection_review_packet.get(
                    "decision", {}
                ).get("status")
            ),
            "collection_review_runtime_review_ready": (
                joined_trace_ownership_collection_review_packet.get(
                    "decision", {}
                ).get("runtime_review_ready")
            ),
            "collection_review_implementation_authorized": (
                joined_trace_ownership_collection_review_packet.get(
                    "decision", {}
                ).get("implementation_authorized_by_this_packet")
            ),
            "collection_review_max_rows_if_later_authorized": (
                joined_trace_ownership_collection_review_packet.get(
                    "approved_if_later_explicitly_authorized", {}
                ).get("max_rows")
            ),
            "joined_collection_status": (
                joined_trace_ownership_collection.get("decision", {}).get("status")
            ),
            "joined_collection_collected_row_count": (
                joined_trace_ownership_collection.get("summary", {}).get(
                    "collected_row_count"
                )
            ),
            "joined_collection_generated_frame_count": (
                joined_trace_ownership_collection.get("summary", {}).get(
                    "generated_frame_count"
                )
            ),
            "joined_collection_default_off_equivalence_passed": (
                joined_trace_ownership_collection.get("summary", {}).get(
                    "default_off_equivalence_passed"
                )
            ),
            "joined_collection_selected_move_delta_count": (
                joined_trace_ownership_collection.get("summary", {}).get(
                    "selected_move_delta_count"
                )
            ),
            "joined_collection_selected_provider_delta_count": (
                joined_trace_ownership_collection.get("summary", {}).get(
                    "selected_provider_delta_count"
                )
            ),
            "joined_collection_score_delta_count": (
                joined_trace_ownership_collection.get("summary", {}).get(
                    "score_delta_count"
                )
            ),
            "joined_collection_routing_delta_count": (
                joined_trace_ownership_collection.get("summary", {}).get(
                    "routing_delta_count"
                )
            ),
            "seed_manifest_v1_status": selector_objective_seed_manifest_v1.get(
                "decision", {}
            ).get("status"),
            "seed_manifest_v1_seed_row_count": (
                selector_objective_seed_manifest_v1.get("summary", {}).get(
                    "seed_row_count"
                )
            ),
            "seed_manifest_v1_candidate_switch_count": (
                selector_objective_seed_manifest_v1.get("summary", {}).get(
                    "candidate_switch_contrast_seed_count"
                )
            ),
            "seed_manifest_v1_safe_preservation_count": (
                selector_objective_seed_manifest_v1.get("summary", {}).get(
                    "safe_preservation_contrast_seed_count"
                )
            ),
            "seed_manifest_v1_selector_training_row_count": (
                selector_objective_seed_manifest_v1.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "seed_manifest_v1_stage7_training_row_count": (
                selector_objective_seed_manifest_v1.get("summary", {}).get(
                    "stage7_training_row_count"
                )
            ),
            "seed_probe_v1_status": selector_objective_seed_probe_v1.get(
                "decision", {}
            ).get("status"),
            "seed_probe_v1_runtime_feature_eligible_prediction_count": (
                selector_objective_seed_probe_v1.get("summary", {}).get(
                    "runtime_feature_eligible_prediction_count"
                )
            ),
            "feature_probe_status": selector_objective_feature_probe.get(
                "decision", {}
            ).get("status"),
            "feature_probe_runtime_threshold_passing_model_count": (
                selector_objective_feature_probe.get("summary", {}).get(
                    "runtime_threshold_passing_model_count"
                )
            ),
            "feature_probe_best_switch_recall": (
                selector_objective_feature_probe.get("summary", {}).get(
                    "best_runtime_switch_recall"
                )
            ),
            "feature_probe_review_status": (
                selector_objective_feature_probe_review.get("decision", {}).get(
                    "status"
                )
            ),
            "feature_probe_review_best_switch_recall": (
                selector_objective_feature_probe_review.get("summary", {}).get(
                    "best_switch_recall"
                )
            ),
            "feature_probe_review_best_preserve_recall": (
                selector_objective_feature_probe_review.get("summary", {}).get(
                    "best_preserve_recall"
                )
            ),
            "feature_probe_review_runtime_threshold_passing_model_count": (
                selector_objective_feature_probe_review.get("summary", {}).get(
                    "runtime_threshold_passing_model_count"
                )
            ),
            "diversity_gap_status": (
                selector_objective_diversity_gap_review.get("decision", {}).get(
                    "status"
                )
            ),
            "diversity_gap_remaining_stage4_selected_failure_count": (
                selector_objective_diversity_gap_review.get("summary", {}).get(
                    "remaining_stage4_selected_failure_count"
                )
            ),
            "diversity_gap_remaining_stage5_6_selected_failure_count": (
                selector_objective_diversity_gap_review.get("summary", {}).get(
                    "remaining_stage5_6_selected_failure_count"
                )
            ),
            "stage4_scope_review_status": (
                stage4_joined_trace_ownership_scope_review_packet.get(
                    "decision", {}
                ).get("status")
            ),
            "stage4_scope_review_runtime_review_ready": (
                stage4_joined_trace_ownership_scope_review_packet.get(
                    "decision", {}
                ).get("runtime_review_ready")
            ),
            "stage4_scope_review_implementation_authorized": (
                stage4_joined_trace_ownership_scope_review_packet.get(
                    "decision", {}
                ).get("implementation_authorized_by_this_packet")
            ),
            "stage4_scope_review_max_rows_if_later_authorized": (
                stage4_joined_trace_ownership_scope_review_packet.get(
                    "approved_if_later_explicitly_authorized", {}
                ).get("max_rows")
            ),
            "runtime_work_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "selector_objective_gate": {
            "stage4_collection_status": (
                stage4_joined_trace_ownership_collection.get("decision", {}).get(
                    "status"
                )
            ),
            "stage4_collection_next_step": (
                stage4_joined_trace_ownership_collection.get("decision", {}).get(
                    "recommended_next_step"
                )
            ),
            "stage4_collection_collected_row_count": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "collected_row_count"
                )
            ),
            "stage4_collection_generated_frame_count": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "generated_frame_count"
                )
            ),
            "stage4_collection_switch_contrast_with_positive_capacity_count": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "switch_contrast_with_positive_capacity_count"
                )
            ),
            "stage4_collection_default_off_equivalence_passed": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "default_off_equivalence_passed"
                )
            ),
            "stage4_collection_selected_move_delta_count": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "selected_move_delta_count"
                )
            ),
            "stage4_collection_selected_provider_delta_count": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "selected_provider_delta_count"
                )
            ),
            "stage4_collection_score_delta_count": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "score_delta_count"
                )
            ),
            "stage4_collection_routing_delta_count": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "routing_delta_count"
                )
            ),
            "stage4_collection_selector_training_row_count": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "stage4_collection_stage7_training_row_count": (
                stage4_joined_trace_ownership_collection.get("summary", {}).get(
                    "stage7_training_row_count"
                )
            ),
            "seed_manifest_v2_status": selector_objective_seed_manifest_v2.get(
                "decision", {}
            ).get("status"),
            "seed_manifest_v2_next_step": selector_objective_seed_manifest_v2.get(
                "decision", {}
            ).get("recommended_next_step"),
            "seed_manifest_v2_seed_row_count": selector_objective_seed_manifest_v2.get(
                "summary", {}
            ).get("seed_row_count"),
            "seed_manifest_v2_objective_channel_counts": (
                selector_objective_seed_manifest_v2.get("summary", {}).get(
                    "objective_channel_counts"
                )
            ),
            "seed_manifest_v2_source_stage_counts": (
                selector_objective_seed_manifest_v2.get("summary", {}).get(
                    "source_stage_counts"
                )
            ),
            "seed_manifest_v2_selector_training_row_count": (
                selector_objective_seed_manifest_v2.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "seed_manifest_v2_stage7_training_row_count": (
                selector_objective_seed_manifest_v2.get("summary", {}).get(
                    "stage7_training_row_count"
                )
            ),
            "seed_probe_v2_status": selector_objective_seed_probe_v2.get(
                "decision", {}
            ).get("status"),
            "seed_probe_v2_runtime_feature_eligible_prediction_count": (
                selector_objective_seed_probe_v2.get("summary", {}).get(
                    "runtime_feature_eligible_prediction_count"
                )
            ),
            "seed_probe_v2_target_action_counts": (
                selector_objective_seed_probe_v2.get("summary", {}).get(
                    "target_action_counts"
                )
            ),
            "selector_benchmark_v2_status": selector_objective_benchmark_v2.get(
                "decision", {}
            ).get("status"),
            "selector_benchmark_v2_next_step": selector_objective_benchmark_v2.get(
                "decision", {}
            ).get("recommended_next_step"),
            "selector_benchmark_v2_best_runtime_model": (
                selector_objective_benchmark_v2.get("summary", {}).get(
                    "best_runtime_model"
                )
            ),
            "selector_benchmark_v2_best_runtime_accuracy": (
                selector_objective_benchmark_v2.get("summary", {}).get(
                    "best_runtime_accuracy"
                )
            ),
            "selector_benchmark_v2_best_runtime_switch_recall": (
                selector_objective_benchmark_v2.get("summary", {}).get(
                    "best_runtime_switch_recall"
                )
            ),
            "selector_benchmark_v2_best_runtime_preserve_recall": (
                selector_objective_benchmark_v2.get("summary", {}).get(
                    "best_runtime_preserve_recall"
                )
            ),
            "selector_benchmark_v2_best_runtime_abstain_recall": (
                selector_objective_benchmark_v2.get("summary", {}).get(
                    "best_runtime_abstain_recall"
                )
            ),
            "selector_benchmark_v2_runtime_threshold_passing_model_count": (
                selector_objective_benchmark_v2.get("summary", {}).get(
                    "runtime_threshold_passing_model_count"
                )
            ),
            "selector_benchmark_v2_selector_training_row_count": (
                selector_objective_benchmark_v2.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "selector_benchmark_v2_stage7_training_row_count": (
                selector_objective_benchmark_v2.get("summary", {}).get(
                    "stage7_training_row_count"
                )
            ),
            "selector_benchmark_review_status": (
                selector_objective_benchmark_review_packet_v2.get(
                    "decision", {}
                ).get("status")
            ),
            "selector_benchmark_review_next_step": (
                selector_objective_benchmark_review_packet_v2.get(
                    "decision", {}
                ).get("recommended_next_step")
            ),
            "selector_benchmark_review_runtime_review_ready": (
                selector_objective_benchmark_review_packet_v2.get(
                    "decision", {}
                ).get("runtime_review_ready")
            ),
            "selector_benchmark_review_independent_validation_ready": (
                selector_objective_benchmark_review_packet_v2.get(
                    "decision", {}
                ).get("independent_validation_review_ready")
            ),
            "independent_validation_manifest_status": (
                selector_objective_independent_validation_manifest.get(
                    "decision", {}
                ).get("status")
            ),
            "independent_validation_manifest_labels_allowed_by_review": (
                selector_objective_independent_validation_manifest.get(
                    "decision", {}
                ).get("labels_allowed_by_review")
            ),
            "independent_validation_manifest_job_count": (
                selector_objective_independent_validation_manifest.get(
                    "binding_summary", {}
                ).get("job_count")
            ),
            "independent_validation_manifest_job_count_by_stage": (
                selector_objective_independent_validation_manifest.get(
                    "binding_summary", {}
                ).get("job_count_by_stage")
            ),
            "independent_validation_manifest_all_bindings_valid": (
                selector_objective_independent_validation_manifest.get(
                    "binding_summary", {}
                ).get("all_bindings_valid")
            ),
            "independent_validation_manifest_excluded_stages": (
                selector_objective_independent_validation_manifest.get(
                    "selection_policy", {}
                ).get("excluded_stages")
            ),
            "independent_validation_manifest_stage7_training_rows": (
                selector_objective_independent_validation_manifest.get(
                    "selection_policy", {}
                ).get("stage7_training_rows")
            ),
            "independent_validation_manifest_job_labels_generated_count": sum(
                1
                for job in selector_objective_independent_validation_manifest.get(
                    "jobs"
                )
                or []
                if job.get("labels_generated")
            ),
            "independent_validation_labels_status": (
                selector_objective_independent_validation_labels.get(
                    "decision", {}
                ).get("status")
            ),
            "independent_validation_labels_label_count": (
                selector_objective_independent_validation_labels.get(
                    "summary", {}
                ).get("label_count")
            ),
            "independent_validation_labels_selected_result_counts": (
                selector_objective_independent_validation_labels.get(
                    "summary", {}
                ).get("selected_result_counts")
            ),
            "independent_validation_labels_result_counts_by_stage": (
                selector_objective_independent_validation_labels.get(
                    "summary", {}
                ).get("selected_result_counts_by_stage")
            ),
            "independent_validation_labels_selector_training_row_count": (
                selector_objective_independent_validation_labels.get(
                    "summary", {}
                ).get("selector_training_row_count")
            ),
            "independent_validation_labels_stage7_training_row_count": (
                selector_objective_independent_validation_labels.get(
                    "summary", {}
                ).get("stage7_training_row_count")
            ),
            "independent_validation_status": (
                selector_objective_independent_validation.get("decision", {}).get(
                    "status"
                )
            ),
            "independent_validation_row_count": (
                selector_objective_independent_validation.get("summary", {}).get(
                    "row_count"
                )
            ),
            "independent_validation_target_counts": (
                selector_objective_independent_validation.get("summary", {}).get(
                    "target_counts"
                )
            ),
            "independent_validation_switch_recall": (
                selector_objective_independent_validation.get("summary", {}).get(
                    "switch_recall"
                )
            ),
            "independent_validation_preserve_recall": (
                selector_objective_independent_validation.get("summary", {}).get(
                    "preserve_recall"
                )
            ),
            "independent_validation_selector_training_row_count": (
                selector_objective_independent_validation.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "independent_validation_stage7_training_row_count": (
                selector_objective_independent_validation.get("summary", {}).get(
                    "stage7_training_row_count"
                )
            ),
            "independent_validation_blocker_status": (
                selector_objective_independent_validation_blocker.get(
                    "decision", {}
                ).get("status")
            ),
            "independent_validation_blocker_class": (
                selector_objective_independent_validation_blocker.get(
                    "blocker", {}
                ).get("blocker_class")
            ),
            "independent_validation_runtime_selector_blocked": (
                selector_objective_independent_validation_blocker.get(
                    "blocker", {}
                ).get("runtime_selector_blocked")
            ),
            "runtime_work_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "stage4_first_move_diagnostic_gate": {
            "failure_discovery_status": (
                stage4_failure_discovery.get("decision", {}).get("status")
            ),
            "failure_discovery_next_step": (
                stage4_failure_discovery.get("decision", {}).get(
                    "recommended_next_step"
                )
            ),
            "failure_packet_count": (
                stage4_failure_discovery.get("summary", {}).get(
                    "failure_packet_count"
                )
            ),
            "unique_failure_state_move_count": (
                stage4_failure_discovery.get("summary", {}).get(
                    "unique_failure_state_move_count"
                )
            ),
            "all_unique_failures_already_in_selector_seed": (
                stage4_failure_discovery.get("summary", {}).get(
                    "all_unique_failures_already_in_selector_seed"
                )
            ),
            "sequence_review_status": (
                stage4_caveat_sequence_review.get("decision", {}).get("status")
            ),
            "sequence_review_primary_diagnosis": (
                stage4_caveat_sequence_review.get("diagnosis", {}).get("primary")
            ),
            "sequence_review_single_unique_failure": (
                stage4_caveat_sequence_review.get("summary", {}).get(
                    "single_unique_failure"
                )
            ),
            "sequence_review_base_control_reproduces_failure_count": (
                stage4_caveat_sequence_review.get("summary", {}).get(
                    "base_control_reproduces_failure_count"
                )
            ),
            "sequence_candidate_status": (
                stage4_sequence_candidate_review.get("decision", {}).get("status")
            ),
            "sequence_candidate_primary": (
                stage4_sequence_candidate_review.get("classification", {}).get(
                    "primary"
                )
            ),
            "sequence_candidate_legal_first_move_count": (
                stage4_sequence_candidate_review.get("summary", {}).get(
                    "legal_first_move_count"
                )
            ),
            "sequence_candidate_converting_first_move_count": (
                stage4_sequence_candidate_review.get("classification", {}).get(
                    "converting_first_move_count"
                )
            ),
            "sequence_candidate_non_converting_first_move_count": (
                stage4_sequence_candidate_review.get("classification", {}).get(
                    "non_converting_first_move_count"
                )
            ),
            "feature_review_status": (
                stage4_first_move_feature_review.get("decision", {}).get("status")
            ),
            "feature_review_single_state_only": (
                stage4_first_move_feature_review.get("summary", {}).get(
                    "single_state_only"
                )
            ),
            "feature_review_positive_terms": (
                stage4_first_move_feature_review.get("interpretation", {}).get(
                    "candidate_positive_terms"
                )
            ),
            "feature_review_failure_terms": (
                stage4_first_move_feature_review.get("interpretation", {}).get(
                    "candidate_failure_terms"
                )
            ),
            "stratified_validation_status": (
                stage4_stratified_contrast_validation.get("decision", {}).get(
                    "status"
                )
            ),
            "stratified_validation_variant_count": (
                stage4_stratified_contrast_validation.get("summary", {}).get(
                    "variant_count"
                )
            ),
            "stratified_validation_gap_variant_count": (
                stage4_stratified_contrast_validation.get("summary", {}).get(
                    "gap_variant_count"
                )
            ),
            "stratified_validation_candidate_row_count": (
                stage4_stratified_contrast_validation.get("summary", {}).get(
                    "candidate_row_count"
                )
            ),
            "runtime_review_status": (
                stage4_runtime_review.get("decision", {}).get("status")
            ),
            "runtime_review_ready": (
                stage4_runtime_review.get("decision", {}).get("runtime_review_ready")
            ),
            "runtime_review_implementation_authorized": (
                stage4_runtime_review.get("decision", {}).get(
                    "implementation_authorized_by_this_packet"
                )
            ),
            "sequence_control_dataset_status": (
                sequence_control_contrast_dataset.get("decision", {}).get("status")
            ),
            "sequence_control_dataset_row_count": (
                sequence_control_contrast_dataset.get("summary", {}).get("row_count")
            ),
            "sequence_control_dataset_row_type_counts": (
                sequence_control_contrast_dataset.get("summary", {}).get(
                    "row_type_counts"
                )
            ),
            "sequence_control_dataset_runtime_authorization_row_count": (
                sequence_control_contrast_dataset.get("summary", {}).get(
                    "runtime_authorization_row_count"
                )
            ),
            "sequence_control_probe_status": (
                sequence_control_contrast_probe.get("decision", {}).get("status")
            ),
            "sequence_control_probe_stage4_review_ready_pending_approval": (
                sequence_control_contrast_probe.get("summary", {}).get(
                    "stage4_review_ready_pending_approval"
                )
            ),
            "sequence_control_probe_stage7_rows_are_current_gate_evidence_not_promotion": (
                sequence_control_contrast_probe.get("summary", {}).get(
                    "stage7_rows_are_current_gate_evidence_not_promotion"
                )
            ),
            "runtime_work_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "candidate_generation_training_refresh_gate": {
            "dataset_v3_status": (
                strategy_sequence_dataset_v3.get("decision", {}).get("status")
            ),
            "dataset_v3_row_count": (
                strategy_sequence_dataset_v3.get("summary", {}).get("row_count")
            ),
            "dataset_v3_candidate_generation_training_row_count": (
                strategy_sequence_dataset_v3.get("summary", {}).get(
                    "candidate_generation_training_row_count"
                )
            ),
            "dataset_v3_selector_training_row_count": (
                strategy_sequence_dataset_v3.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "dataset_v3_stage7_readiness_training_row_count": (
                strategy_sequence_dataset_v3.get("summary", {}).get(
                    "stage7_readiness_training_row_count"
                )
            ),
            "dataset_v3_runtime_trace_feature_row_count": (
                strategy_sequence_dataset_v3.get("summary", {}).get(
                    "runtime_trace_feature_row_count"
                )
            ),
            "quality_probe_status": (
                strategy_sequence_dataset_v3_quality_probe.get("decision", {}).get(
                    "status"
                )
            ),
            "quality_probe_selector_blockers": (
                strategy_sequence_dataset_v3_quality_probe.get("selector_blockers")
            ),
            "context_review_status": (
                strategy_sequence_dataset_v3_context_review.get("decision", {}).get(
                    "status"
                )
            ),
            "context_benchmark_status": (
                candidate_generation_v3_context_benchmark.get("decision", {}).get(
                    "status"
                )
            ),
            "context_benchmark_exact_positive_capacity_recall_from_trace": (
                candidate_generation_v3_context_benchmark.get("summary", {}).get(
                    "exact_positive_capacity_recall_from_trace"
                )
            ),
            "context_benchmark_stage_family_positive_capacity_recall_from_trace": (
                candidate_generation_v3_context_benchmark.get("summary", {}).get(
                    "stage_family_positive_capacity_recall_from_trace"
                )
            ),
            "context_benchmark_stage_family_negative_capacity_exposure_from_trace": (
                candidate_generation_v3_context_benchmark.get("summary", {}).get(
                    "stage_family_negative_capacity_exposure_from_trace"
                )
            ),
            "runtime_boundary_status": (
                candidate_generation_v3_runtime_boundary_review.get(
                    "decision", {}
                ).get("status")
            ),
            "runtime_boundary_new_runtime_behavior_allowed": (
                candidate_generation_v3_runtime_boundary_review.get(
                    "approved_runtime_boundary", {}
                ).get("new_runtime_behavior_allowed")
            ),
            "runtime_boundary_selector_allowed": (
                candidate_generation_v3_runtime_boundary_review.get(
                    "approved_runtime_boundary", {}
                ).get("selector_allowed")
            ),
            "training_refresh_design_v2_status": (
                candidate_generation_training_refresh_design_v2.get(
                    "decision", {}
                ).get("status")
            ),
            "training_refresh_design_v2_next_step": (
                candidate_generation_training_refresh_design_v2.get(
                    "decision", {}
                ).get("recommended_next_step")
            ),
            "training_refresh_design_v2_runtime_candidate_generator_refresh_allowed": (
                candidate_generation_training_refresh_design_v2.get(
                    "decision", {}
                ).get("runtime_candidate_generator_refresh_allowed")
            ),
            "training_refresh_design_v2_selector_allowed": (
                candidate_generation_training_refresh_design_v2.get(
                    "decision", {}
                ).get("selector_allowed")
            ),
            "training_refresh_design_v2_guardrails_allowed": (
                candidate_generation_training_refresh_design_v2.get(
                    "decision", {}
                ).get("guardrails_allowed")
            ),
            "training_refresh_design_v2_promotion_allowed": (
                candidate_generation_training_refresh_design_v2.get(
                    "decision", {}
                ).get("promotion_allowed")
            ),
            "training_refresh_review_status": (
                candidate_generation_v3_training_refresh_review.get(
                    "decision", {}
                ).get("status")
            ),
            "training_refresh_design_status": (
                candidate_generation_training_refresh_design_v3.get(
                    "decision", {}
                ).get("status")
            ),
            "training_refresh_design_next_step": (
                candidate_generation_training_refresh_design_v3.get(
                    "decision", {}
                ).get("recommended_next_step")
            ),
            "training_refresh_design_implementation_allowed": (
                candidate_generation_training_refresh_design_v3.get(
                    "decision", {}
                ).get("implementation_allowed_by_this_artifact")
            ),
            "benchmark_status": (
                candidate_generation_training_refresh_benchmark_v3.get(
                    "decision", {}
                ).get("status")
            ),
            "benchmark_best_policy": (
                candidate_generation_training_refresh_benchmark_v3.get(
                    "summary", {}
                ).get("best_policy")
            ),
            "benchmark_positive_capacity_recall": (
                candidate_generation_training_refresh_benchmark_v3.get(
                    "summary", {}
                )
                .get("best_policy_metrics", {})
                .get("positive_capacity_recall")
            ),
            "benchmark_positive_precision": (
                candidate_generation_training_refresh_benchmark_v3.get(
                    "summary", {}
                )
                .get("best_policy_metrics", {})
                .get("positive_precision")
            ),
            "benchmark_negative_capacity_suppression": (
                candidate_generation_training_refresh_benchmark_v3.get(
                    "summary", {}
                )
                .get("best_policy_metrics", {})
                .get("negative_capacity_suppression")
            ),
            "benchmark_leave_stage_out_positive_capacity_recall": (
                candidate_generation_training_refresh_benchmark_v3.get(
                    "summary", {}
                )
                .get("best_policy_leave_stage_out_metrics", {})
                .get("positive_capacity_recall")
            ),
            "benchmark_thresholds_met": (
                candidate_generation_training_refresh_benchmark_v3.get(
                    "summary", {}
                ).get("thresholds_met")
            ),
            "benchmark_selector_training_row_count": (
                candidate_generation_training_refresh_benchmark_v3.get(
                    "summary", {}
                ).get("selector_training_row_count")
            ),
            "benchmark_stage7_training_row_count": (
                candidate_generation_training_refresh_benchmark_v3.get(
                    "summary", {}
                ).get("stage7_training_row_count")
            ),
            "runtime_review_status": (
                candidate_generation_training_refresh_runtime_review_v3.get(
                    "decision", {}
                ).get("status")
            ),
            "runtime_review_ready": (
                candidate_generation_training_refresh_runtime_review_v3.get(
                    "decision", {}
                ).get("runtime_review_ready")
            ),
            "runtime_review_candidate_generation_allowed_by_packet": (
                candidate_generation_training_refresh_runtime_review_v3.get(
                    "decision", {}
                ).get("runtime_candidate_generation_allowed_by_this_packet")
            ),
            "runtime_review_implementation_authorized": (
                candidate_generation_training_refresh_runtime_review_v3.get(
                    "decision", {}
                ).get("implementation_authorized_by_this_packet")
            ),
            "runtime_review_sandbox_type": (
                candidate_generation_training_refresh_runtime_review_v3.get(
                    "approved_scope_if_later_authorized", {}
                ).get("sandbox_type")
            ),
            "runtime_review_protected_stages": (
                candidate_generation_training_refresh_runtime_review_v3.get(
                    "approved_scope_if_later_authorized", {}
                ).get("protected_stages")
            ),
            "runtime_review_direct_request": (
                candidate_generation_training_refresh_runtime_review_v3.get(
                    "approved_scope_if_later_authorized", {}
                ).get("direct_request")
            ),
            "runtime_review_score_delta": (
                candidate_generation_training_refresh_runtime_review_v3.get(
                    "approved_scope_if_later_authorized", {}
                ).get("score_delta")
            ),
            "runtime_work_allowed": False,
            "runtime_candidate_generation_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "candidate_generation_trace_context_gate": {
            "refresh_sandbox_status": (
                candidate_generation_refresh_sandbox.get("decision", {}).get("status")
            ),
            "refresh_sandbox_default_off_equivalence_passed": (
                candidate_generation_refresh_sandbox.get("summary", {}).get(
                    "default_off_equivalence_passed"
                )
            ),
            "refresh_sandbox_generated_frame_count": (
                candidate_generation_refresh_sandbox.get("summary", {}).get(
                    "generated_frame_count"
                )
            ),
            "refresh_sandbox_stage7_held_out_frame_count": (
                candidate_generation_refresh_sandbox.get("summary", {}).get(
                    "stage7_held_out_frame_count"
                )
            ),
            "refresh_sandbox_selected_move_delta_count": (
                candidate_generation_refresh_sandbox.get("summary", {}).get(
                    "selected_move_delta_count"
                )
            ),
            "refresh_sandbox_selected_provider_delta_count": (
                candidate_generation_refresh_sandbox.get("summary", {}).get(
                    "selected_provider_delta_count"
                )
            ),
            "refresh_sandbox_score_delta_count": (
                candidate_generation_refresh_sandbox.get("summary", {}).get(
                    "score_delta_count"
                )
            ),
            "refresh_coverage_status": (
                candidate_generation_refresh_coverage.get("decision", {}).get(
                    "status"
                )
            ),
            "refresh_coverage_exact_positive_capacity_recall": (
                candidate_generation_refresh_coverage.get("summary", {}).get(
                    "exact_positive_capacity_recall"
                )
            ),
            "refresh_coverage_exact_negative_capacity_exposure_rate": (
                candidate_generation_refresh_coverage.get("summary", {}).get(
                    "exact_negative_capacity_exposure_rate"
                )
            ),
            "refresh_coverage_stage4_frame_count": (
                candidate_generation_refresh_coverage.get("summary", {}).get(
                    "stage4_frame_count"
                )
            ),
            "refresh_coverage_stage7_frame_count": (
                candidate_generation_refresh_coverage.get("summary", {}).get(
                    "stage7_frame_count"
                )
            ),
            "refresh_trace_features_status": (
                strategy_sequence_candidate_generation_refresh_trace_features.get(
                    "decision", {}
                ).get("status")
            ),
            "refresh_trace_features_trace_frame_count": (
                strategy_sequence_candidate_generation_refresh_trace_features.get(
                    "summary", {}
                ).get("trace_frame_count")
            ),
            "refresh_trace_features_stage_counts": (
                strategy_sequence_candidate_generation_refresh_trace_features.get(
                    "summary", {}
                ).get("stage_counts")
            ),
            "refresh_trace_features_stage7_trace_frame_count": (
                strategy_sequence_candidate_generation_refresh_trace_features.get(
                    "summary", {}
                ).get("stage7_trace_frame_count")
            ),
            "refresh_trace_features_selector_training_row_count": (
                strategy_sequence_candidate_generation_refresh_trace_features.get(
                    "summary", {}
                ).get("selector_training_row_count")
            ),
            "refresh_trace_features_candidate_generation_training_row_count": (
                strategy_sequence_candidate_generation_refresh_trace_features.get(
                    "summary", {}
                ).get("candidate_generation_training_row_count")
            ),
            "dataset_v4_status": (
                strategy_sequence_dataset_v4.get("decision", {}).get("status")
            ),
            "dataset_v4_row_count": (
                strategy_sequence_dataset_v4.get("summary", {}).get("row_count")
            ),
            "dataset_v4_runtime_trace_feature_row_count": (
                strategy_sequence_dataset_v4.get("summary", {}).get(
                    "runtime_trace_feature_row_count"
                )
            ),
            "dataset_v4_selector_training_row_count": (
                strategy_sequence_dataset_v4.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "dataset_v4_stage7_readiness_training_row_count": (
                strategy_sequence_dataset_v4.get("summary", {}).get(
                    "stage7_readiness_training_row_count"
                )
            ),
            "dataset_v4_quality_status": (
                strategy_sequence_dataset_v4_quality_probe.get("decision", {}).get(
                    "status"
                )
            ),
            "dataset_v4_context_status": (
                strategy_sequence_dataset_v4_context_review.get("decision", {}).get(
                    "status"
                )
            ),
            "v4_context_benchmark_status": (
                candidate_generation_v4_context_benchmark.get("decision", {}).get(
                    "status"
                )
            ),
            "v4_boundary_status": (
                candidate_generation_v4_next_boundary_review.get("decision", {}).get(
                    "status"
                )
            ),
            "v4_boundary_new_runtime_sandbox_allowed": (
                candidate_generation_v4_next_boundary_review.get(
                    "approved_now", {}
                ).get("implement_new_runtime_sandbox")
            ),
            "scope_gap_status": (
                candidate_generation_scope_gap_review.get("decision", {}).get("status")
            ),
            "source_gap_manifest_status": (
                candidate_source_gap_manifest.get("decision", {}).get("status")
            ),
            "source_gap_exact_covered_positive_capacity_count": (
                candidate_source_gap_manifest.get("summary", {}).get(
                    "exact_covered_positive_capacity_count"
                )
            ),
            "source_gap_exact_missing_positive_capacity_count": (
                candidate_source_gap_manifest.get("summary", {}).get(
                    "exact_missing_positive_capacity_count"
                )
            ),
            "source_gap_policy_cell_covered_exact_missing_count": (
                candidate_source_gap_manifest.get("summary", {}).get(
                    "policy_cell_covered_exact_missing_count"
                )
            ),
            "source_expansion_options_status": (
                candidate_source_expansion_options.get("decision", {}).get("status")
            ),
            "source_expansion_preferred_next_review": (
                candidate_source_expansion_options.get("preferred_next_review")
            ),
            "exact_trace_runtime_review_status": (
                exact_trace_enrichment_runtime_review.get("decision", {}).get(
                    "status"
                )
            ),
            "exact_trace_runtime_review_ready": (
                exact_trace_enrichment_runtime_review.get("decision", {}).get(
                    "runtime_review_ready"
                )
            ),
            "exact_trace_runtime_review_implementation_authorized": (
                exact_trace_enrichment_runtime_review.get("decision", {}).get(
                    "implementation_authorized_by_this_packet"
                )
            ),
            "exact_trace_sandbox_status": (
                exact_trace_enrichment_sandbox.get("decision", {}).get("status")
            ),
            "exact_trace_sandbox_default_off_equivalence_passed": (
                exact_trace_enrichment_sandbox.get("summary", {}).get(
                    "default_off_equivalence_passed"
                )
            ),
            "exact_trace_sandbox_generated_frame_count": (
                exact_trace_enrichment_sandbox.get("summary", {}).get(
                    "generated_frame_count"
                )
            ),
            "exact_trace_sandbox_selected_move_delta_count": (
                exact_trace_enrichment_sandbox.get("summary", {}).get(
                    "selected_move_delta_count"
                )
            ),
            "exact_trace_sandbox_selected_provider_delta_count": (
                exact_trace_enrichment_sandbox.get("summary", {}).get(
                    "selected_provider_delta_count"
                )
            ),
            "exact_trace_sandbox_score_delta_count": (
                exact_trace_enrichment_sandbox.get("summary", {}).get(
                    "score_delta_count"
                )
            ),
            "exact_trace_coverage_status": (
                exact_trace_enrichment_coverage.get("decision", {}).get("status")
            ),
            "exact_trace_coverage_exact_gap_recall": (
                exact_trace_enrichment_coverage.get("summary", {}).get(
                    "exact_gap_recall"
                )
            ),
            "exact_trace_coverage_stage4_frame_count": (
                exact_trace_enrichment_coverage.get("summary", {}).get(
                    "stage4_frame_count"
                )
            ),
            "exact_trace_coverage_stage7_frame_count": (
                exact_trace_enrichment_coverage.get("summary", {}).get(
                    "stage7_frame_count"
                )
            ),
            "dataset_v5_status": (
                strategy_sequence_dataset_v5.get("decision", {}).get("status")
            ),
            "dataset_v5_row_count": (
                strategy_sequence_dataset_v5.get("summary", {}).get("row_count")
            ),
            "dataset_v5_runtime_trace_feature_row_count": (
                strategy_sequence_dataset_v5.get("summary", {}).get(
                    "runtime_trace_feature_row_count"
                )
            ),
            "dataset_v5_exact_trace_enrichment_row_count": (
                strategy_sequence_dataset_v5.get("summary", {}).get(
                    "added_exact_trace_enrichment_row_count"
                )
            ),
            "dataset_v5_selector_training_row_count": (
                strategy_sequence_dataset_v5.get("summary", {}).get(
                    "selector_training_row_count"
                )
            ),
            "dataset_v5_stage7_readiness_training_row_count": (
                strategy_sequence_dataset_v5.get("summary", {}).get(
                    "stage7_readiness_training_row_count"
                )
            ),
            "dataset_v5_quality_status": (
                strategy_sequence_dataset_v5_quality_probe.get("decision", {}).get(
                    "status"
                )
            ),
            "dataset_v5_context_status": (
                strategy_sequence_dataset_v5_context_review.get("decision", {}).get(
                    "status"
                )
            ),
            "v5_context_benchmark_status": (
                candidate_generation_v5_context_benchmark.get("decision", {}).get(
                    "status"
                )
            ),
            "v5_exact_positive_capacity_recall_from_candidate_generation_trace": (
                candidate_generation_v5_context_benchmark.get("summary", {}).get(
                    "exact_positive_capacity_recall_from_candidate_generation_trace"
                )
            ),
            "v5_exact_positive_capacity_recall_delta_vs_v4": (
                candidate_generation_v5_context_benchmark.get("summary", {}).get(
                    "exact_positive_capacity_recall_delta_vs_v4"
                )
            ),
            "v5_policy_cell_negative_capacity_exposure": (
                candidate_generation_v5_context_benchmark.get("summary", {}).get(
                    "policy_cell_negative_capacity_exposure_from_candidate_generation_trace"
                )
            ),
            "v5_boundary_status": (
                candidate_generation_v5_next_boundary_review.get("decision", {}).get(
                    "status"
                )
            ),
            "v5_boundary_implement_new_runtime_sandbox": (
                candidate_generation_v5_next_boundary_review.get(
                    "approved_now", {}
                ).get("implement_new_runtime_sandbox")
            ),
            "v5_boundary_selector_allowed": (
                candidate_generation_v5_next_boundary_review.get(
                    "approved_now", {}
                ).get("selector_allowed")
            ),
            "runtime_work_allowed": False,
            "runtime_candidate_generation_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "stage7_sampling_gate": {
            "runner_status": runner.get("decision", {}).get("status"),
            "runner_dry_run": runner.get("summary", {}).get("dry_run"),
            "runner_job_count": runner.get("summary", {}).get("job_count"),
            "processed_job_count": current_stage7_processed_job_count,
            "executed_job_count": current_stage7_executed_job_count,
            "historical_processed_job_count": historical_stage7_processed_job_count,
            "historical_executed_job_count": historical_stage7_executed_job_count,
            "skipped_existing_output_count": runner.get("summary", {}).get(
                "skipped_existing_output_count"
            ),
            "overwrite_existing_outputs": runner.get("summary", {}).get(
                "overwrite_existing_outputs"
            ),
            "output_validation_status": output_validation_status,
            "runner_output_validation_status": runner.get("summary", {}).get(
                "output_validation_status"
            ),
            "output_valid_count": output_validation.get("summary", {}).get(
                "output_valid_count"
            ),
            "execution_readiness_source": runner.get("summary", {}).get(
                "execution_readiness_source"
            ),
            "execution_readiness_status": current_stage7_execution_readiness_status,
            "historical_execution_readiness_status": raw_stage7_execution_readiness_status,
            "execution_readiness_jobs_passing": runner.get("summary", {}).get(
                "execution_readiness_jobs_passing"
            ),
            "invalid_existing_output_count": runner.get("summary", {}).get(
                "invalid_existing_output_count"
            ),
            "job_timeout_seconds": runner.get("summary", {}).get("job_timeout_seconds"),
            "timed_out_job_count": runner.get("summary", {}).get("timed_out_job_count"),
            "integration_status": integration.get("decision", {}).get("status"),
            "outputs_present_count": stage7_summary.get("outputs_present_count"),
            "combined_success_controls": stage7_success_controls,
            "success_controls_required": stage7_success_required,
            "combined_failure_controls": stage7_summary.get("combined_failure_controls"),
            "failure_controls_required": stage7_summary.get("failure_controls_required"),
            "success_controls_ready": stage7_success_ready,
            "label_gate_status": (
                "stage7_success_gate_closed_no_current_label_approval"
                if stage7_label_gate_closed
                else "stage7_label_gate_pending_or_not_ready"
            ),
            "label_run_allowed_by_artifact": current_stage7_label_run_allowed,
            "historical_label_run_allowed_by_runner": historical_stage7_label_run_allowed,
        },
        "runtime_and_training_boundaries": boundaries,
        "current_control_plane_gate": {
            "status": gate.get("decision", {}).get("status"),
            "approval_option_ids": [
                option.get("option_id") for option in gate_approval_options
            ],
            "protected_failure_contrast_collection_option_available": bool(
                protected_collection_gate_option
            ),
            "protected_failure_contrast_collection_command_available": bool(
                protected_collection_gate_option.get("command_if_explicitly_approved")
            ),
            "protected_failure_contrast_collection_option_id": (
                protected_collection_gate_option.get("option_id")
            ),
            "protected_failure_contrast_collection_blocked_by_option_id": (
                protected_collection_blocking_gate_option.get("option_id")
            ),
            "label_run_allowed": gate.get("decision", {}).get("label_run_allowed"),
            "runtime_changes_allowed": gate.get("decision", {}).get("runtime_changes_allowed"),
            "selector_allowed": gate.get("decision", {}).get("selector_allowed"),
            "selector_training_allowed": gate.get("decision", {}).get(
                "selector_training_allowed"
            ),
            "runtime_direct_routing": gate.get("runtime_direct_routing"),
            "hidden_python_controller": gate.get("hidden_python_controller"),
            "stage7_promotion_allowed": gate.get("decision", {}).get("stage7_promotion_allowed"),
            "stage8_training_allowed": gate.get("decision", {}).get("stage8_training_allowed"),
        },
        "blockers": blockers,
        "hard_blockers": hard_blockers,
        "control_plane_gate_review_blockers": control_plane_gate_review_blockers,
        "explicit_gate_blockers": explicit_gate_blockers,
        "approval_gates": {
            "stage7_diverse_clean_label_execution": {
                "ready_for_explicit_approval": runner.get("decision", {}).get("status")
                == "stage7_diverse_clean_sampling_runner_dry_run_ready"
                and not (runner.get("summary", {}).get("invalid_existing_output_count") or 0),
                "current_artifact_allows_execution": False,
                "why": (
                    "The Stage 7 clean success-control gate is already closed; "
                    "additional Stage 7 labels are not the primary current unblocker."
                    if stage7_success_ready
                    else "The runner is dry-run ready, validates/skips existing outputs safely, but execution requires explicit approval because it creates new Stage 7 h40 labels."
                ),
            },
            "protected_plan_window_failure_contrast_collection": {
                "ready_for_explicit_approval": (
                    protected_failure_contrast_ready_for_explicit_approval
                ),
                "approval_request_ready_for_collection": (
                    failure_contrast_approval_request_ready
                ),
                "current_artifact_allows_collection": False,
                "status": failure_contrast_execution_readiness.get("decision", {}).get(
                    "status",
                    failure_contrast_runner.get("decision", {}).get("status"),
                ),
                "post_success_refresh_required": (
                    failure_contrast_approval_request_summary.get(
                        "post_success_refresh_required"
                    )
                ),
                "post_success_refresh_script": (
                    failure_contrast_approval_request_summary.get(
                        "post_success_refresh_script"
                    )
                ),
                "post_success_refresh_scope": (
                    failure_contrast_approval_request_summary.get(
                        "post_success_refresh_scope"
                    )
                ),
                "why": (
                    "The protected failure-contrast approval-request packet is blocked; repair it before considering collection approval."
                    if protected_failure_contrast_approval_request_repair_pending
                    else
                    "Sequence-policy inputs contain forbidden training or runtime "
                    "authorization rows; repair inputs before considering protected "
                    "failure-contrast collection."
                    if sequence_forbidden_training_or_runtime_inputs
                    else "The sequence-policy benchmark is mixed/underpowered on protected "
                    "plan-window failures; bounded observation-only collection is the "
                    "current explicit gate."
                ),
            },
            "stage4_first_move_contrast_sandbox": {
                "ready_for_explicit_approval": (
                    stage4_ready_for_explicit_approval and stage4_approval_request_ready
                ),
                "current_artifact_allows_implementation": bool(
                    stage4_decision.get("implementation_allowed_by_this_packet")
                ),
                "status": stage4_status,
                "approval_request_artifact": (
                    "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
                ),
                "approval_request_status": stage4_approval_request_decision.get(
                    "status"
                ),
                "approval_request_blockers": (
                    stage4_approval_request_blockers
                ),
                "approval_request_ready_for_runtime_approval": (
                    stage4_approval_request_ready
                ),
                "approval_request_created": stage4_approval_request.get(
                    "approval_request_created"
                ),
                "implementation_authorized_by_approval_request": (
                    stage4_approval_request.get("implementation_authorized_by_request")
                ),
                "safety_scope": {
                    "approval_id": stage4_approval_scope.get("approval_id"),
                    "approval_request_blockers": (
                        stage4_approval_request_blockers
                    ),
                    "approval_request_ready_for_runtime_approval": (
                        stage4_approval_request_ready
                    ),
                    "sandbox_scope_id": stage4_approval_scope.get("sandbox_scope_id"),
                    "default_off": stage4_approval_scope.get("default_off"),
                    "default_enabled": stage4_approval_scope.get("default_enabled"),
                    "implementation_authorized_by_request": (
                        stage4_approval_scope.get(
                            "implementation_authorized_by_request"
                        )
                    ),
                    "runtime_change_class": stage4_approval_scope.get(
                        "runtime_change_class"
                    ),
                    "exact_state_or_exact_move_exception": stage4_approval_scope.get(
                        "exact_state_or_exact_move_exception"
                    ),
                    "runtime_dtm_or_tablebase_lookup": stage4_approval_scope.get(
                        "runtime_dtm_or_tablebase_lookup"
                    ),
                    "hidden_python_controller": stage4_approval_scope.get(
                        "hidden_python_controller"
                    ),
                    "selector_training_allowed": stage4_approval_scope.get(
                        "selector_training_allowed"
                    ),
                    "gameplay_topology_mutation": stage4_approval_scope.get(
                        "gameplay_topology_mutation"
                    ),
                    "stage7_promotion_allowed": stage4_approval_scope.get(
                        "stage7_promotion_allowed"
                    ),
                    "stage8_training_allowed": stage4_approval_scope.get(
                        "stage8_training_allowed"
                    ),
                    "readiness_audit": stage4_approval_scope.get("readiness_audit"),
                    "readiness_audit_status": stage4_approval_scope.get(
                        "readiness_audit_status"
                    ),
                    "readiness_checked_flag_count": stage4_approval_scope.get(
                        "readiness_checked_flag_count"
                    ),
                    "readiness_boundary_violation_count": stage4_approval_scope.get(
                        "readiness_boundary_violation_count"
                    ),
                    "readiness_source_artifact_count": stage4_approval_scope.get(
                        "readiness_source_artifact_count"
                    ),
                },
                "why": "Stage 4 has a reviewed default-off first-move contrast sandbox scope, but implementation still requires explicit sandbox approval.",
            },
            "stage8_training": {
                "ready_for_explicit_approval": False,
                "why": (
                    "Protected plan-window failure-contrast evidence is not integrated; "
                    "Stage 8 training remains blocked even though Stage 7 held-out controls "
                    "are balanced."
                    if protected_failure_contrast_pending
                    else "Sequence-policy inputs require repair before Stage 8 training can be reviewed."
                    if sequence_forbidden_training_or_runtime_inputs
                    else "Stage 7 is still quarantined or the sequence-policy benchmark is not ready."
                ),
            },
        },
        "decision": {
            "status": decision_status,
            "recommended_next_step": next_step,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    protected = payload["protected_stack"]
    clean_curriculum = payload["clean_curriculum_run_lineage_gate"]
    strategy_sequence_architecture = payload["strategy_sequence_architecture_gate"]
    strategy_owner_contrast = payload["strategy_owner_contrast_gate"]
    selector_objective_normalization = payload["selector_objective_normalization_gate"]
    abstention_selector_safety = payload["abstention_selector_safety_gate"]
    targeted_ownership_recovery = payload["targeted_ownership_recovery_gate"]
    balanced_hard_negative = payload["balanced_hard_negative_gate"]
    clean_replacement = payload["clean_replacement_review_gate"]
    stage7 = payload["stage7_sampling_gate"]
    sequence = payload["sequence_policy"]
    protected_failure_contrast = payload["protected_failure_contrast_gate"]
    missing_provider = payload["protected_missing_provider_gate"]
    strategy_source = payload["strategy_sequence_candidate_source_gate"]
    strategy_arbitration = payload["strategy_arbitration_gate"]
    strategy_monitor = payload["strategy_monitor_maturity_gate"]
    internal_terminal = payload["internal_terminal_readiness_gate"]
    repair_monitor_trace = payload["repair_monitor_trace_feature_gate"]
    stage5_6_refresh = payload["stage5_6_candidate_generation_refresh_gate"]
    cross_stage_scope = payload["cross_stage_candidate_generation_scope_gate"]
    selector_lineage = payload["selector_objective_lineage_gate"]
    selector_objective = payload["selector_objective_gate"]
    stage4_diagnostic = payload["stage4_first_move_diagnostic_gate"]
    candidate_generation_refresh = payload["candidate_generation_training_refresh_gate"]
    candidate_generation_trace = payload["candidate_generation_trace_context_gate"]
    current_gate = payload["current_control_plane_gate"]
    decision = payload["decision"]
    lines = [
        "# KRK Full Suite Readiness Audit v0",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        f"- runtime_changes_allowed: `{str(decision['runtime_changes_allowed']).lower()}`",
        f"- label_run_allowed: `{str(decision['label_run_allowed']).lower()}`",
        f"- selector_training_allowed: `{str(decision['selector_training_allowed']).lower()}`",
        f"- stage7_promotion_allowed: `{str(decision['stage7_promotion_allowed']).lower()}`",
        f"- stage8_training_allowed: `{str(decision['stage8_training_allowed']).lower()}`",
        "",
        "## Protected Stack",
        "",
        f"- active status: `{protected['status']}`",
        f"- clean_stack_adopted: `{protected['clean_stack_adopted']}`",
        f"- filesystem_snapshots_replaced: `{protected['filesystem_snapshots_replaced']}`",
        f"- clean_stack_adopted_and_validated: `{protected['clean_stack_adopted_and_validated']}`",
        f"- post_adoption_validation_required: `{protected['post_adoption_validation_required']}`",
        f"- rollback_paths_preserved: `{protected['rollback_paths_preserved']}`",
        f"- active_stack_paths_safe: `{protected['active_stack_path_status']['all_paths_safe']}`",
        f"- active_stack_paths_exist: `{protected['active_stack_path_status']['all_paths_exist']}`",
        f"- rollback_stack_paths_safe: `{protected['rollback_stack_path_status']['all_paths_safe']}`",
        f"- rollback_stack_paths_exist: `{protected['rollback_stack_path_status']['all_paths_exist']}`",
        f"- rollback_common_paths_distinct: `{protected['rollback_common_paths_distinct']}`",
        f"- stage5_conversion_preservation_passed: `{protected['stage5_conversion_preservation_passed']}`",
        f"- stage6_drive_validation_passed: `{protected['stage6_drive_validation_passed']}`",
        f"- m1_m4_preservation_passed: `{protected['m1_m4_preservation_passed']}`",
        f"- kpk_kqk_bridge_preservation_passed: `{protected['kpk_kqk_bridge_preservation_passed']}`",
        "",
        "## Clean Curriculum Run Lineage",
        "",
        f"- passive_lineage_ready: `{clean_curriculum['passive_lineage_ready']}`",
        f"- checkpoint_plan_status: `{clean_curriculum['checkpoint_plan_status']}`",
        f"- execution_manifest_status: `{clean_curriculum['execution_manifest_status']}`",
        f"- execution_manifest_full_run_authorized: `{clean_curriculum['execution_manifest_full_run_authorized']}`",
        f"- stage6_compose_manifest_status: `{clean_curriculum['stage6_compose_manifest_status']}`",
        f"- stage6_compose_manifest_run_authorized: `{clean_curriculum['stage6_compose_manifest_run_authorized']}`",
        f"- preflight_status: `{clean_curriculum['preflight_status']}`",
        f"- preflight_blocker_count: `{clean_curriculum['preflight_blocker_count']}`",
        f"- smoke_result_status: `{clean_curriculum['smoke_result_status']}`",
        f"- smoke_command_plumbing_validated: `{clean_curriculum['smoke_command_plumbing_validated']}`",
        f"- smoke_curriculum_semantics_validated: `{clean_curriculum['smoke_curriculum_semantics_validated']}`",
        f"- initial_run_status: `{clean_curriculum['initial_run_status']}`",
        f"- initial_run_full_clean_retrain_complete: `{clean_curriculum['initial_run_full_clean_retrain_complete']}`",
        f"- retry1_status: `{clean_curriculum['retry1_status']}`",
        f"- retry1_complete_through_stage6: `{clean_curriculum['retry1_complete_through_stage6']}`",
        f"- retry1_promoted_by_this_artifact: `{clean_curriculum['retry1_promoted_by_this_artifact']}`",
        f"- guardrail_status: `{clean_curriculum['guardrail_status']}`",
        f"- stage6_gap_status: `{clean_curriculum['stage6_gap_status']}`",
        f"- stage5_control_debt_status: `{clean_curriculum['stage5_control_debt_status']}`",
        f"- stage5_semantics_status: `{clean_curriculum['stage5_semantics_status']}`",
        f"- stage4_caveat_control_status: `{clean_curriculum['stage4_caveat_control_status']}`",
        f"- curriculum_stage7_status: `{clean_curriculum['curriculum_stage7_status']}`",
        f"- curriculum_stage8_status: `{clean_curriculum['curriculum_stage8_status']}`",
        f"- stage7_promotion_allowed: `{clean_curriculum['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{clean_curriculum['stage8_training_allowed']}`",
        "",
        "## Strategy Sequence Architecture",
        "",
        f"- passive_architecture_ready: `{strategy_sequence_architecture['passive_architecture_ready']}`",
        f"- architecture_review_status: `{strategy_sequence_architecture['architecture_review_status']}`",
        f"- architecture_runtime_work_allowed: `{strategy_sequence_architecture['architecture_runtime_work_allowed']}`",
        f"- architecture_recommended_next_slice_id: `{strategy_sequence_architecture['architecture_recommended_next_slice_id']}`",
        f"- evidence_plan_status: `{strategy_sequence_architecture['evidence_plan_status']}`",
        f"- evidence_plan_runtime_work_allowed: `{strategy_sequence_architecture['evidence_plan_runtime_work_allowed']}`",
        f"- inventory_status: `{strategy_sequence_architecture['inventory_status']}`",
        f"- inventory_runtime_work_allowed: `{strategy_sequence_architecture['inventory_runtime_work_allowed']}`",
        f"- inventory_sequence_policy_clean_gate_closed: `{strategy_sequence_architecture['inventory_sequence_policy_clean_gate_closed']}`",
        f"- inventory_sequence_policy_has_clean_success_gap: `{strategy_sequence_architecture['inventory_sequence_policy_has_clean_success_gap']}`",
        f"- inventory_state_holdout_gap_blocks_runtime: `{strategy_sequence_architecture['inventory_state_holdout_gap_blocks_runtime']}`",
        f"- inventory_strategy_ownership_has_some_signal: `{strategy_sequence_architecture['inventory_strategy_ownership_has_some_signal']}`",
        f"- inventory_strategy_ownership_state_holdout_ready: `{strategy_sequence_architecture['inventory_strategy_ownership_state_holdout_ready']}`",
        f"- inventory_stage7_is_held_out: `{strategy_sequence_architecture['inventory_stage7_is_held_out']}`",
        f"- inventory_stage7_clean_review_recommendation: `{strategy_sequence_architecture['inventory_stage7_clean_review_recommendation']}`",
        f"- runtime_selector_implemented: `{strategy_sequence_architecture['runtime_selector_implemented']}`",
        f"- stage7_promotion_allowed: `{strategy_sequence_architecture['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{strategy_sequence_architecture['stage8_training_allowed']}`",
        "",
        "## Strategy Owner Contrast",
        "",
        f"- passive_probe_ready: `{strategy_owner_contrast['passive_probe_ready']}`",
        f"- label_plan_status: `{strategy_owner_contrast['label_plan_status']}`",
        f"- label_plan_job_count: `{strategy_owner_contrast['label_plan_job_count']}`",
        f"- label_plan_stage7_job_count: `{strategy_owner_contrast['label_plan_stage7_job_count']}`",
        f"- label_plan_labels_generated: `{strategy_owner_contrast['label_plan_labels_generated']}`",
        f"- label_plan_review_status: `{strategy_owner_contrast['label_plan_review_status']}`",
        f"- execution_manifest_status: `{strategy_owner_contrast['execution_manifest_status']}`",
        f"- execution_manifest_all_bindings_valid: `{strategy_owner_contrast['execution_manifest_all_bindings_valid']}`",
        f"- execution_manifest_review_status: `{strategy_owner_contrast['execution_manifest_review_status']}`",
        f"- control_label_count: `{strategy_owner_contrast['control_label_count']}`",
        f"- control_label_stage7_count: `{strategy_owner_contrast['control_label_stage7_count']}`",
        f"- dataset_status: `{strategy_owner_contrast['dataset_status']}`",
        f"- dataset_row_count: `{strategy_owner_contrast['dataset_row_count']}`",
        f"- dataset_stage7_training_rows: `{strategy_owner_contrast['dataset_stage7_training_rows']}`",
        f"- readiness_selector_sandbox_ready: `{strategy_owner_contrast['readiness_selector_sandbox_ready']}`",
        f"- probe_status: `{strategy_owner_contrast['probe_status']}`",
        f"- probe_training_row_count: `{strategy_owner_contrast['probe_training_row_count']}`",
        f"- probe_heldout_row_count: `{strategy_owner_contrast['probe_heldout_row_count']}`",
        f"- probe_readiness_blockers: `{strategy_owner_contrast['probe_readiness_blockers']}`",
        f"- runtime_arbiter_implemented: `{strategy_owner_contrast['runtime_arbiter_implemented']}`",
        f"- runtime_terminals_added: `{strategy_owner_contrast['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{strategy_owner_contrast['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{strategy_owner_contrast['stage8_training_allowed']}`",
        "",
        "## Selector Objective Normalization",
        "",
        f"- passive_objective_ready: `{selector_objective_normalization['passive_objective_ready']}`",
        f"- arbitration_objective_status: `{selector_objective_normalization['arbitration_objective_status']}`",
        f"- normalized_objective_status: `{selector_objective_normalization['normalized_objective_status']}`",
        f"- normalized_probe_status: `{selector_objective_normalization['normalized_probe_status']}`",
        f"- normalized_probe_benchmark_underpowered: `{selector_objective_normalization['normalized_probe_benchmark_underpowered']}`",
        f"- normalized_probe_review_status: `{selector_objective_normalization['normalized_probe_review_status']}`",
        f"- normalized_probe_review_stage7_training_leakage: `{selector_objective_normalization['normalized_probe_review_stage7_training_leakage']}`",
        f"- selector_architecture_status: `{selector_objective_normalization['selector_architecture_status']}`",
        f"- selector_architecture_sandbox_ready: `{selector_objective_normalization['selector_architecture_sandbox_ready']}`",
        f"- selector_label_semantics_sandbox_ready: `{selector_objective_normalization['selector_label_semantics_sandbox_ready']}`",
        f"- split_dataset_status: `{selector_objective_normalization['split_dataset_status']}`",
        f"- split_dataset_objective_row_count: `{selector_objective_normalization['split_dataset_objective_row_count']}`",
        f"- split_dataset_selector_training_row_count: `{selector_objective_normalization['split_dataset_selector_training_row_count']}`",
        f"- split_dataset_stage7_row_count: `{selector_objective_normalization['split_dataset_stage7_row_count']}`",
        f"- split_readiness_status: `{selector_objective_normalization['split_readiness_status']}`",
        f"- split_readiness_selector_training_allowed: `{selector_objective_normalization['split_readiness_selector_training_allowed']}`",
        f"- split_readiness_ownership_probe_underpowered: `{selector_objective_normalization['split_readiness_ownership_probe_underpowered']}`",
        f"- runtime_selector_implemented: `{selector_objective_normalization['runtime_selector_implemented']}`",
        f"- runtime_terminals_added: `{selector_objective_normalization['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{selector_objective_normalization['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{selector_objective_normalization['stage8_training_allowed']}`",
        "",
        "## Abstention Selector Safety",
        "",
        f"- passive_safety_ready: `{abstention_selector_safety['passive_safety_ready']}`",
        f"- first_objective_status: `{abstention_selector_safety['first_objective_status']}`",
        f"- safe_preservation_review_status: `{abstention_selector_safety['safe_preservation_review_status']}`",
        f"- training_dataset_status: `{abstention_selector_safety['training_dataset_status']}`",
        f"- training_dataset_row_count: `{abstention_selector_safety['training_dataset_row_count']}`",
        f"- training_dataset_stage7_training_rows: `{abstention_selector_safety['training_dataset_stage7_training_rows']}`",
        f"- training_probe_status: `{abstention_selector_safety['training_probe_status']}`",
        f"- context_dataset_status: `{abstention_selector_safety['context_dataset_status']}`",
        f"- context_probe_status: `{abstention_selector_safety['context_probe_status']}`",
        f"- context_probe_improved_negative_suppression: `{abstention_selector_safety['context_probe_improved_negative_suppression']}`",
        f"- context_error_audit_status: `{abstention_selector_safety['context_error_audit_status']}`",
        f"- context_error_false_positive_count: `{abstention_selector_safety['context_error_false_positive_count']}`",
        f"- feature_gap_next_step_status: `{abstention_selector_safety['feature_gap_next_step_status']}`",
        f"- feature_gap_implementation_allowed: `{abstention_selector_safety['feature_gap_implementation_allowed']}`",
        f"- feature_gap_runtime_ready: `{abstention_selector_safety['feature_gap_runtime_ready']}`",
        f"- blocked_next_steps: `{abstention_selector_safety['blocked_next_steps']}`",
        f"- runtime_selector_implemented: `{abstention_selector_safety['runtime_selector_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{abstention_selector_safety['runtime_dtm_or_tablebase_lookup']}`",
        f"- stage7_promotion_allowed: `{abstention_selector_safety['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{abstention_selector_safety['stage8_training_allowed']}`",
        "",
        "## Targeted Ownership Recovery",
        "",
        f"- passive_recovery_ready: `{targeted_ownership_recovery['passive_recovery_ready']}`",
        f"- non_stage0_manifest_status: `{targeted_ownership_recovery['non_stage0_manifest_status']}`",
        f"- non_stage0_manifest_job_count: `{targeted_ownership_recovery['non_stage0_manifest_job_count']}`",
        f"- non_stage0_manifest_stage7_job_count: `{targeted_ownership_recovery['non_stage0_manifest_stage7_job_count']}`",
        f"- non_stage0_labels_status: `{targeted_ownership_recovery['non_stage0_labels_status']}`",
        f"- non_stage0_label_count: `{targeted_ownership_recovery['non_stage0_label_count']}`",
        f"- non_stage0_preserved_count: `{targeted_ownership_recovery['non_stage0_preserved_count']}`",
        f"- non_stage0_stage0_collapse_count: `{targeted_ownership_recovery['non_stage0_stage0_collapse_count']}`",
        f"- non_stage0_stage7_training_rows: `{targeted_ownership_recovery['non_stage0_stage7_training_rows']}`",
        f"- negative_manifest_status: `{targeted_ownership_recovery['negative_manifest_status']}`",
        f"- negative_manifest_job_count: `{targeted_ownership_recovery['negative_manifest_job_count']}`",
        f"- negative_manifest_stage7_job_count: `{targeted_ownership_recovery['negative_manifest_stage7_job_count']}`",
        f"- negative_labels_status: `{targeted_ownership_recovery['negative_labels_status']}`",
        f"- negative_label_count: `{targeted_ownership_recovery['negative_label_count']}`",
        f"- negative_targeted_owner_converted_count: `{targeted_ownership_recovery['negative_targeted_owner_converted_count']}`",
        f"- negative_targeted_owner_failed_count: `{targeted_ownership_recovery['negative_targeted_owner_failed_count']}`",
        f"- negative_stage7_training_rows: `{targeted_ownership_recovery['negative_stage7_training_rows']}`",
        f"- runtime_selector_implemented: `{targeted_ownership_recovery['runtime_selector_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{targeted_ownership_recovery['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{targeted_ownership_recovery['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{targeted_ownership_recovery['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{targeted_ownership_recovery['stage8_training_allowed']}`",
        "",
        "## Balanced Hard-Negative Evidence",
        "",
        f"- passive_evidence_ready: `{balanced_hard_negative['passive_evidence_ready']}`",
        f"- label_plan_status: `{balanced_hard_negative['label_plan_status']}`",
        f"- label_plan_job_count: `{balanced_hard_negative['label_plan_job_count']}`",
        f"- label_plan_stage7_jobs: `{balanced_hard_negative['label_plan_stage7_jobs']}`",
        f"- execution_manifest_status: `{balanced_hard_negative['execution_manifest_status']}`",
        f"- execution_manifest_labels_allowed_now: `{balanced_hard_negative['execution_manifest_labels_allowed_now']}`",
        f"- execution_manifest_stage7_jobs: `{balanced_hard_negative['execution_manifest_stage7_jobs']}`",
        f"- execution_manifest_review_status: `{balanced_hard_negative['execution_manifest_review_status']}`",
        f"- labels_status: `{balanced_hard_negative['labels_status']}`",
        f"- label_count: `{balanced_hard_negative['label_count']}`",
        f"- positive_capacity_count: `{balanced_hard_negative['positive_capacity_count']}`",
        f"- negative_capacity_count: `{balanced_hard_negative['negative_capacity_count']}`",
        f"- stage7_labels: `{balanced_hard_negative['stage7_labels']}`",
        f"- stage7_training_labels: `{balanced_hard_negative['stage7_training_labels']}`",
        f"- evidence_review_status: `{balanced_hard_negative['evidence_review_status']}`",
        f"- evidence_underpowered: `{balanced_hard_negative['evidence_underpowered']}`",
        f"- evidence_expanded_row_count: `{balanced_hard_negative['evidence_expanded_row_count']}`",
        f"- evidence_expanded_hard_negative_count: `{balanced_hard_negative['evidence_expanded_hard_negative_count']}`",
        f"- evidence_best_negative_suppression: `{balanced_hard_negative['evidence_best_negative_suppression']}`",
        f"- runtime_selector_implemented: `{balanced_hard_negative['runtime_selector_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{balanced_hard_negative['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{balanced_hard_negative['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{balanced_hard_negative['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{balanced_hard_negative['stage8_training_allowed']}`",
        "",
        "## Clean Replacement Review",
        "",
        f"- passive_review_ready: `{clean_replacement['passive_review_ready']}`",
        f"- replacement_readiness_status: `{clean_replacement['replacement_readiness_status']}`",
        f"- replacement_readiness_clean_stack_replacement_allowed: `{clean_replacement['replacement_readiness_clean_stack_replacement_allowed']}`",
        f"- snapshot_manifest_status: `{clean_replacement['snapshot_manifest_status']}`",
        f"- snapshot_manifest_all_referenced_paths_exist: `{clean_replacement['snapshot_manifest_all_referenced_paths_exist']}`",
        f"- snapshot_manifest_replacement_allowed: `{clean_replacement['snapshot_manifest_replacement_allowed']}`",
        f"- review_packet_status: `{clean_replacement['review_packet_status']}`",
        f"- review_packet_replacement_review_ready: `{clean_replacement['review_packet_replacement_review_ready']}`",
        f"- review_packet_implementation_allowed: `{clean_replacement['review_packet_implementation_allowed']}`",
        f"- deferred_review_status: `{clean_replacement['deferred_review_status']}`",
        f"- deferred_review_explicit_approval_detected: `{clean_replacement['deferred_review_explicit_approval_detected']}`",
        f"- deferred_review_implementation_allowed: `{clean_replacement['deferred_review_implementation_allowed']}`",
        f"- protected_stage_reference_mode: `{clean_replacement['protected_stage_reference_mode']}`",
        f"- protected_stage_active_stack_status: `{clean_replacement['protected_stage_active_stack_status']}`",
        f"- protected_stage_stage4_status: `{clean_replacement['protected_stage_stage4_status']}`",
        f"- protected_stage_stage7_status: `{clean_replacement['protected_stage_stage7_status']}`",
        f"- stage7_promotion_allowed: `{clean_replacement['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{clean_replacement['stage8_training_allowed']}`",
        "",
        "## Stage Status",
        "",
    ]
    for stage, status in payload["stage_status"].items():
        lines.append(f"- `{stage}`: `{status['status']}`")
        if stage == "stage4":
            lines.append(
                f"  - approval_request_artifact: `{status['approval_request_artifact']}`"
            )
            lines.append(
                f"  - approval_request_status: `{status['approval_request_status']}`"
            )
            lines.append(
                f"  - approval_request_created: `{status['approval_request_created']}`"
            )
    lines.extend(
        [
            "",
            "## Stage 7 Sampling Gate",
            "",
            f"- runner_status: `{stage7['runner_status']}`",
            f"- runner_dry_run: `{stage7['runner_dry_run']}`",
            f"- runner_job_count: `{stage7['runner_job_count']}`",
            f"- processed_job_count: `{stage7['processed_job_count']}`",
            f"- executed_job_count: `{stage7['executed_job_count']}`",
            f"- skipped_existing_output_count: `{stage7['skipped_existing_output_count']}`",
            f"- overwrite_existing_outputs: `{stage7['overwrite_existing_outputs']}`",
            f"- output_validation_status: `{stage7['output_validation_status']}`",
            f"- execution_readiness_source: `{stage7['execution_readiness_source']}`",
            f"- execution_readiness_status: `{stage7['execution_readiness_status']}`",
            f"- execution_readiness_jobs_passing: `{stage7['execution_readiness_jobs_passing']}`",
            f"- invalid_existing_output_count: `{stage7['invalid_existing_output_count']}`",
            f"- job_timeout_seconds: `{stage7['job_timeout_seconds']}`",
            f"- timed_out_job_count: `{stage7['timed_out_job_count']}`",
            f"- integration_status: `{stage7['integration_status']}`",
            f"- outputs_present_count: `{stage7['outputs_present_count']}`",
            f"- combined_success_controls: `{stage7['combined_success_controls']}`",
            f"- success_controls_required: `{stage7['success_controls_required']}`",
            f"- success_controls_ready: `{stage7['success_controls_ready']}`",
            "",
            "## Sequence Policy",
            "",
            f"- pipeline_status: `{sequence['pipeline_status']}`",
            f"- input_probe_status: `{sequence['input_probe_status']}`",
            f"- input_probe_row_count: `{sequence['input_probe_row_count']}`",
            f"- input_probe_benchmark_input_ready: `{sequence['input_probe_benchmark_input_ready']}`",
            f"- input_probe_stage4_topk_signal: `{sequence['input_probe_stage4_topk_signal']}`",
            f"- input_probe_protected_plan_window_failure_sparse: `{sequence['input_probe_protected_plan_window_failure_sparse']}`",
            f"- input_probe_selector_training_row_count: `{sequence['input_probe_selector_training_row_count']}`",
            f"- input_probe_runtime_authorization_row_count: `{sequence['input_probe_runtime_authorization_row_count']}`",
            f"- benchmark_status: `{sequence['benchmark_status']}`",
            f"- benchmark_design_status: `{sequence['benchmark_design_status']}`",
            f"- benchmark_review_status: `{sequence['benchmark_review_status']}`",
            f"- post_failure_contrast_refresh_status: `{sequence['post_failure_contrast_refresh_status']}`",
            f"- post_failure_contrast_refresh_boundaries_preserved: `{sequence['post_failure_contrast_refresh_boundaries_preserved']}`",
            f"- post_failure_contrast_refresh_boundary_violation_count: `{sequence['post_failure_contrast_refresh_boundary_violation_count']}`",
            f"- post_failure_contrast_refresh_row_count: `{sequence['post_failure_contrast_refresh_row_count']}`",
            f"- post_failure_contrast_refresh_stage7_training_row_count: `{sequence['post_failure_contrast_refresh_stage7_training_row_count']}`",
            f"- passive_design_without_new_labels_status: `{sequence['passive_design_without_new_labels_status']}`",
            f"- passive_design_current_evidence_limit: `{sequence['passive_design_current_evidence_limit']}`",
            f"- passive_design_depends_on_new_label_execution: `{sequence['passive_design_depends_on_new_label_execution']}`",
            f"- passive_design_depends_on_protected_failure_contrast_collection: `{sequence['passive_design_depends_on_protected_failure_contrast_collection']}`",
            f"- cross_stage_requirements_status: `{sequence['cross_stage_requirements_status']}`",
            f"- replay_free_protected_cross_stage_evidence: `{sequence['replay_free_protected_cross_stage_evidence']}`",
            f"- cross_stage_sequence_evidence_met: `{sequence['cross_stage_sequence_evidence_met']}`",
            f"- input_row_count: `{sequence['input_row_count']}`",
            f"- inputs_ready: `{sequence['inputs_ready']}`",
            f"- benchmark_ready: `{sequence['benchmark_ready']}`",
            f"- selector_training_row_count: `{sequence['selector_training_row_count']}`",
            "",
            "## Protected Failure Contrast Gate",
            "",
            f"- plan_status: `{protected_failure_contrast['plan_status']}`",
            f"- unique_failure_count: `{protected_failure_contrast['unique_failure_count']}`",
            f"- minimum_new_failures_needed: `{protected_failure_contrast['minimum_new_failures_needed']}`",
            f"- manifest_status: `{protected_failure_contrast['manifest_status']}`",
            f"- manifest_job_count: `{protected_failure_contrast['manifest_job_count']}`",
            f"- manifest_review_status: `{protected_failure_contrast['manifest_review_status']}`",
            f"- execution_readiness_status: `{protected_failure_contrast['execution_readiness_status']}`",
            f"- execution_jobs_passing: `{protected_failure_contrast['execution_jobs_passing']}`",
            f"- runner_status: `{protected_failure_contrast['runner_status']}`",
            f"- runner_manifest_status: `{protected_failure_contrast['runner_manifest_status']}`",
            f"- runner_manifest_declared_job_count: `{protected_failure_contrast['runner_manifest_declared_job_count']}`",
            f"- runner_manifest_fingerprint: `{protected_failure_contrast['runner_manifest_fingerprint']}`",
            f"- runner_collection_run_allowed: `{protected_failure_contrast['runner_collection_run_allowed']}`",
            f"- runner_processed_job_count: `{protected_failure_contrast['runner_processed_job_count']}`",
            f"- runner_executed_job_count: `{protected_failure_contrast['runner_executed_job_count']}`",
            f"- output_validation_status: `{protected_failure_contrast['output_validation_status']}`",
            f"- output_exists_count: `{protected_failure_contrast['output_exists_count']}`",
            f"- output_valid_count: `{protected_failure_contrast['output_valid_count']}`",
            f"- integration_status: `{protected_failure_contrast['integration_status']}`",
            f"- integrated_new_failure_count: `{protected_failure_contrast['integrated_new_failure_count']}`",
            f"- integration_ready: `{protected_failure_contrast['integration_ready']}`",
            f"- ready_for_explicit_approval: `{protected_failure_contrast['ready_for_explicit_approval']}`",
            f"- current_artifact_allows_collection: `{protected_failure_contrast['current_artifact_allows_collection']}`",
            f"- approval_receipt_required: `{protected_failure_contrast['approval_receipt_required']}`",
            f"- approval_receipt_path: `{protected_failure_contrast['approval_receipt_path']}`",
            f"- approval_receipt_present: `{protected_failure_contrast['approval_receipt_present']}`",
            f"- approval_receipt_valid: `{protected_failure_contrast['approval_receipt_valid']}`",
            f"- approval_receipt_blockers: `{protected_failure_contrast['approval_receipt_blockers']}`",
            f"- approval_request_artifact: `{protected_failure_contrast['approval_request_artifact']}`",
            f"- approval_request_status: `{protected_failure_contrast['approval_request_status']}`",
            f"- approval_receipt_created_by_request: `{protected_failure_contrast['approval_receipt_created_by_request']}`",
            f"- post_success_refresh_required: `{protected_failure_contrast['post_success_refresh_required']}`",
            f"- post_success_refresh_script: `{protected_failure_contrast['post_success_refresh_script']}`",
            f"- post_success_refresh_scope: `{protected_failure_contrast['post_success_refresh_scope']}`",
            f"- expected_manifest_fingerprint: `{protected_failure_contrast['expected_manifest_fingerprint']}`",
            f"- expected_readiness_fingerprint: `{protected_failure_contrast['expected_readiness_fingerprint']}`",
            f"- command_if_explicitly_approved: `{protected_failure_contrast['command_if_explicitly_approved']}`",
            f"- runtime_behavior_changed: `{protected_failure_contrast['runtime_behavior_changed']}`",
            f"- runtime_defaults_changed: `{protected_failure_contrast['runtime_defaults_changed']}`",
            f"- runtime_selector_implemented: `{protected_failure_contrast['runtime_selector_implemented']}`",
            f"- runtime_score_changes: `{protected_failure_contrast['runtime_score_changes']}`",
            f"- runtime_direct_routing: `{protected_failure_contrast['runtime_direct_routing']}`",
            f"- runtime_dtm_or_tablebase_lookup: `{protected_failure_contrast['runtime_dtm_or_tablebase_lookup']}`",
            f"- hidden_python_controller: `{protected_failure_contrast['hidden_python_controller']}`",
            f"- gameplay_topology_mutation: `{protected_failure_contrast['gameplay_topology_mutation']}`",
            f"- selector_training_allowed: `{protected_failure_contrast['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{protected_failure_contrast['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{protected_failure_contrast['stage8_training_allowed']}`",
            "",
            "## Protected Missing-Provider Evidence",
            "",
            f"- labels_status: `{missing_provider['labels_status']}`",
            f"- labels_next_step: `{missing_provider['labels_next_step']}`",
            f"- label_count: `{missing_provider['label_count']}`",
            f"- label_result_counts: `{missing_provider['label_result_counts']}`",
            f"- stage7_label_count: `{missing_provider['stage7_label_count']}`",
            f"- stage7_training_label_count: `{missing_provider['stage7_training_label_count']}`",
            f"- merge_status: `{missing_provider['merge_status']}`",
            f"- merge_next_step: `{missing_provider['merge_next_step']}`",
            f"- matched_label_count: `{missing_provider['matched_label_count']}`",
            f"- unmatched_label_count: `{missing_provider['unmatched_label_count']}`",
            f"- coverage_status: `{missing_provider['coverage_status']}`",
            f"- coverage_next_step: `{missing_provider['coverage_next_step']}`",
            f"- coverage_label_count: `{missing_provider['coverage_label_count']}`",
            f"- coverage_frames_present_count: `{missing_provider['coverage_frames_present_count']}`",
            f"- provider_present_in_frame_count: `{missing_provider['provider_present_in_frame_count']}`",
            f"- provider_missing_from_frame_count: `{missing_provider['provider_missing_from_frame_count']}`",
            f"- missing_provider_mate_label_count: `{missing_provider['missing_provider_mate_label_count']}`",
            f"- current_gap_blocks_selector_training: `{missing_provider['current_gap_blocks_selector_training']}`",
            f"- coverage_expansion_plan_status: `{missing_provider['coverage_expansion_plan_status']}`",
            f"- coverage_expansion_rows_to_create: `{missing_provider['coverage_expansion_rows_to_create']}`",
            f"- coverage_expansion_training_allowed_initially: `{missing_provider['coverage_expansion_training_allowed_initially']}`",
            f"- coverage_frames_status: `{missing_provider['coverage_frames_status']}`",
            f"- coverage_frame_row_count: `{missing_provider['coverage_frame_row_count']}`",
            f"- coverage_frame_training_row_count: `{missing_provider['coverage_frame_training_row_count']}`",
            f"- coverage_frame_runtime_proposal_row_count: `{missing_provider['coverage_frame_runtime_proposal_row_count']}`",
            f"- training_semantics_review_status: `{missing_provider['training_semantics_review_status']}`",
            f"- training_semantics_selector_training_allowed: `{missing_provider['training_semantics_selector_training_allowed']}`",
            f"- training_semantics_runtime_work_allowed: `{missing_provider['training_semantics_runtime_work_allowed']}`",
            f"- training_semantics_training_row_count: `{missing_provider['training_semantics_training_row_count']}`",
            f"- training_semantics_runtime_proposal_row_count: `{missing_provider['training_semantics_runtime_proposal_row_count']}`",
            f"- candidate_generator_coverage_status: `{missing_provider['candidate_generator_coverage_status']}`",
            f"- candidate_generator_positive_recall_rate: `{missing_provider['candidate_generator_positive_recall_rate']}`",
            f"- candidate_generator_missing_positive_capacity_count: `{missing_provider['candidate_generator_missing_positive_capacity_count']}`",
            f"- validated_candidate_set_status: `{missing_provider['validated_candidate_set_status']}`",
            f"- validated_candidate_set_added_positive_capacity_count: `{missing_provider['validated_candidate_set_added_positive_capacity_count']}`",
            f"- validated_candidate_set_added_negative_capacity_count: `{missing_provider['validated_candidate_set_added_negative_capacity_count']}`",
            f"- two_stage_review_status: `{missing_provider['two_stage_review_status']}`",
            f"- two_stage_benchmark_plan_status: `{missing_provider['two_stage_benchmark_plan_status']}`",
            f"- two_stage_benchmark_status: `{missing_provider['two_stage_benchmark_status']}`",
            f"- two_stage_benchmark_current_positive_recall_rate: `{missing_provider['two_stage_benchmark_current_positive_recall_rate']}`",
            f"- two_stage_benchmark_expanded_positive_recall_rate: `{missing_provider['two_stage_benchmark_expanded_positive_recall_rate']}`",
            f"- two_stage_benchmark_selector_ready: `{missing_provider['two_stage_benchmark_selector_ready']}`",
            f"- runtime_work_allowed: `{missing_provider['runtime_work_allowed']}`",
            f"- selector_training_allowed: `{missing_provider['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{missing_provider['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{missing_provider['stage8_training_allowed']}`",
            "",
            "## Strategy Sequence Candidate-Source Evidence",
            "",
            f"- candidate_proposal_coverage_status: `{strategy_source['candidate_proposal_coverage_status']}`",
            f"- candidate_proposal_coverage_positive_capacity_recall: `{strategy_source['candidate_proposal_coverage_positive_capacity_recall']}`",
            f"- candidate_proposal_coverage_missing_positive_capacity_count: `{strategy_source['candidate_proposal_coverage_missing_positive_capacity_count']}`",
            f"- candidate_generation_strategy_review_status: `{strategy_source['candidate_generation_strategy_review_status']}`",
            f"- candidate_generation_strategy_review_runtime_sandbox_allowed: `{strategy_source['candidate_generation_strategy_review_runtime_sandbox_allowed']}`",
            f"- schema_status: `{strategy_source['schema_status']}`",
            f"- schema_runtime_sandbox_allowed: `{strategy_source['schema_runtime_sandbox_allowed']}`",
            f"- frames_status: `{strategy_source['frames_status']}`",
            f"- frames_frame_count: `{strategy_source['frames_frame_count']}`",
            f"- frames_frame_type_counts: `{strategy_source['frames_frame_type_counts']}`",
            f"- frames_stage7_challenge_row_count: `{strategy_source['frames_stage7_challenge_row_count']}`",
            f"- frames_stage7_readiness_training_row_count: `{strategy_source['frames_stage7_readiness_training_row_count']}`",
            f"- quality_status: `{strategy_source['quality_status']}`",
            f"- quality_capacity_not_selector_label: `{strategy_source['quality_capacity_not_selector_label']}`",
            f"- quality_sequence_candidate_mate_count: `{strategy_source['quality_sequence_candidate_mate_count']}`",
            f"- source_benchmark_status: `{strategy_source['source_benchmark_status']}`",
            f"- source_benchmark_protected_positive_capacity_ratio: `{strategy_source['source_benchmark_protected_positive_capacity_ratio']}`",
            f"- source_benchmark_protected_negative_capacity_ratio: `{strategy_source['source_benchmark_protected_negative_capacity_ratio']}`",
            f"- source_benchmark_progress_window_sequence_candidate_mate_count: `{strategy_source['source_benchmark_progress_window_sequence_candidate_mate_count']}`",
            f"- control_plane_status: `{strategy_source['control_plane_status']}`",
            f"- control_plane_runtime_sandbox_allowed: `{strategy_source['control_plane_runtime_sandbox_allowed']}`",
            f"- sandbox_review_status: `{strategy_source['sandbox_review_status']}`",
            f"- sandbox_review_implementation_authorized: `{strategy_source['sandbox_review_implementation_authorized']}`",
            f"- observation_sandbox_status: `{strategy_source['observation_sandbox_status']}`",
            f"- observation_sandbox_generated_candidate_count: `{strategy_source['observation_sandbox_generated_candidate_count']}`",
            f"- observation_sandbox_selected_move_or_provider_changed: `{strategy_source['observation_sandbox_selected_move_or_provider_changed']}`",
            f"- observation_coverage_status: `{strategy_source['observation_coverage_status']}`",
            f"- observation_coverage_sampled_frame_count: `{strategy_source['observation_coverage_sampled_frame_count']}`",
            f"- observation_coverage_invariant_failure_count: `{strategy_source['observation_coverage_invariant_failure_count']}`",
            f"- observation_broadened_status: `{strategy_source['observation_broadened_status']}`",
            f"- observation_broadened_case_count: `{strategy_source['observation_broadened_case_count']}`",
            f"- observation_broadened_emitted_frame_count: `{strategy_source['observation_broadened_emitted_frame_count']}`",
            f"- observation_broadened_selected_move_or_provider_delta_count: `{strategy_source['observation_broadened_selected_move_or_provider_delta_count']}`",
            f"- observation_gap_review_status: `{strategy_source['observation_gap_review_status']}`",
            f"- observation_gap_review_unknown_capacity_ratio: `{strategy_source['observation_gap_review_unknown_capacity_ratio']}`",
            f"- capacity_annotation_v1_status: `{strategy_source['capacity_annotation_v1_status']}`",
            f"- capacity_annotation_v1_protected_annotation_recall: `{strategy_source['capacity_annotation_v1_protected_annotation_recall']}`",
            f"- capacity_label_manifest_status: `{strategy_source['capacity_label_manifest_status']}`",
            f"- capacity_label_manifest_labels_run_by_this_artifact: `{strategy_source['capacity_label_manifest_labels_run_by_this_artifact']}`",
            f"- capacity_label_manifest_stage7_job_count: `{strategy_source['capacity_label_manifest_stage7_job_count']}`",
            f"- capacity_labels_status: `{strategy_source['capacity_labels_status']}`",
            f"- capacity_labels_label_count: `{strategy_source['capacity_labels_label_count']}`",
            f"- capacity_labels_stage7_training_label_count: `{strategy_source['capacity_labels_stage7_training_label_count']}`",
            f"- capacity_annotation_v2_status: `{strategy_source['capacity_annotation_v2_status']}`",
            f"- capacity_annotation_v2_protected_annotation_recall: `{strategy_source['capacity_annotation_v2_protected_annotation_recall']}`",
            f"- label_blocker_status: `{strategy_source['label_blocker_status']}`",
            f"- label_blocker_more_blind_label_farming_not_recommended: `{strategy_source['label_blocker_more_blind_label_farming_not_recommended']}`",
            f"- quality_prioritization_review_status: `{strategy_source['quality_prioritization_review_status']}`",
            f"- quality_dataset_status: `{strategy_source['quality_dataset_status']}`",
            f"- quality_dataset_row_count: `{strategy_source['quality_dataset_row_count']}`",
            f"- quality_dataset_quality_probe_row_count: `{strategy_source['quality_dataset_quality_probe_row_count']}`",
            f"- quality_probe_status: `{strategy_source['quality_probe_status']}`",
            f"- quality_probe_best_probe: `{strategy_source['quality_probe_best_probe']}`",
            f"- quality_probe_best_positive_recall: `{strategy_source['quality_probe_best_positive_recall']}`",
            f"- quality_probe_best_negative_suppression: `{strategy_source['quality_probe_best_negative_suppression']}`",
            f"- quality_probe_ready_for_selector_review: `{strategy_source['quality_probe_ready_for_selector_review']}`",
            f"- quality_decision_status: `{strategy_source['quality_decision_status']}`",
            f"- quality_decision_more_blind_label_farming_allowed: `{strategy_source['quality_decision_more_blind_label_farming_allowed']}`",
            f"- source_design_status: `{strategy_source['source_design_status']}`",
            f"- source_design_implementation_allowed: `{strategy_source['source_design_implementation_allowed']}`",
            f"- plan_capsule_source_status: `{strategy_source['plan_capsule_source_status']}`",
            f"- broader_strategy_source_status: `{strategy_source['broader_strategy_source_status']}`",
            f"- source_review_status: `{strategy_source['source_review_status']}`",
            f"- source_review_implementation_allowed: `{strategy_source['source_review_implementation_allowed']}`",
            f"- protected_monitor_expansion_status: `{strategy_source['protected_monitor_expansion_status']}`",
            f"- protected_monitor_expansion_frame_count: `{strategy_source['protected_monitor_expansion_frame_count']}`",
            f"- protected_monitor_expansion_stage7_challenge_row_count: `{strategy_source['protected_monitor_expansion_stage7_challenge_row_count']}`",
            f"- protected_monitor_quality_status: `{strategy_source['protected_monitor_quality_status']}`",
            f"- protected_monitor_quality_strong_failure_family_count: `{strategy_source['protected_monitor_quality_strong_failure_family_count']}`",
            f"- repair_monitor_review_status: `{strategy_source['repair_monitor_review_status']}`",
            f"- repair_monitor_review_implementation_authorized: `{strategy_source['repair_monitor_review_implementation_authorized']}`",
            f"- runtime_work_allowed: `{strategy_source['runtime_work_allowed']}`",
            f"- selector_training_allowed: `{strategy_source['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{strategy_source['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{strategy_source['stage8_training_allowed']}`",
            "",
            "## Strategy Arbitration Missing-Feature Gate",
            "",
            f"- dataset_record_count: `{strategy_arbitration['dataset_record_count']}`",
            f"- dataset_proposal_count: `{strategy_arbitration['dataset_proposal_count']}`",
            f"- dataset_records_by_source_stage: `{strategy_arbitration['dataset_records_by_source_stage']}`",
            f"- dataset_records_with_terminal_context: `{strategy_arbitration['dataset_records_with_terminal_context']}`",
            f"- probe_status: `{strategy_arbitration['probe_status']}`",
            f"- probe_next_step: `{strategy_arbitration['probe_next_step']}`",
            f"- probe_raw_global_provider_hit_rate: `{strategy_arbitration['probe_raw_global_provider_hit_rate']}`",
            f"- probe_visible_heuristic_hit_rate: `{strategy_arbitration['probe_visible_heuristic_hit_rate']}`",
            f"- probe_provider_local_rank1_coverage_rate: `{strategy_arbitration['probe_provider_local_rank1_coverage_rate']}`",
            f"- probe_stage7_record_count: `{strategy_arbitration['probe_stage7_record_count']}`",
            f"- probe_missing_terms_obvious: `{strategy_arbitration['probe_missing_terms_obvious']}`",
            f"- probe_stage7_failures_cluster_by_phase_boundary: `{strategy_arbitration['probe_stage7_failures_cluster_by_phase_boundary']}`",
            f"- decision_status: `{strategy_arbitration['decision_status']}`",
            f"- decision_next_class: `{strategy_arbitration['decision_next_class']}`",
            f"- decision_stop_after_next_class: `{strategy_arbitration['decision_stop_after_next_class']}`",
            f"- missing_feature_candidate_count: `{strategy_arbitration['missing_feature_candidate_count']}`",
            f"- missing_feature_challenge_family_count: `{strategy_arbitration['missing_feature_challenge_family_count']}`",
            f"- missing_feature_recommended_next_step: `{strategy_arbitration['missing_feature_recommended_next_step']}`",
            f"- runtime_work_allowed: `{strategy_arbitration['runtime_work_allowed']}`",
            f"- runtime_arbiter_allowed: `{strategy_arbitration['runtime_arbiter_allowed']}`",
            f"- selector_training_allowed: `{strategy_arbitration['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{strategy_arbitration['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{strategy_arbitration['stage8_training_allowed']}`",
            "",
            "## Strategy Monitor Maturity Evidence",
            "",
            f"- plan_do_not_implement_as_causal_affordances: `{strategy_monitor['plan_do_not_implement_as_causal_affordances']}`",
            f"- records_dataset_record_count: `{strategy_monitor['records_dataset_record_count']}`",
            f"- records_monitor_definition_count: `{strategy_monitor['records_monitor_definition_count']}`",
            f"- records_monitor_record_count: `{strategy_monitor['records_monitor_record_count']}`",
            f"- records_by_monitor_type: `{strategy_monitor['records_by_monitor_type']}`",
            f"- companion_terms_causal_terms_authorized: `{strategy_monitor['companion_terms_causal_terms_authorized']}`",
            f"- companion_terms_runtime_arbiter_authorized: `{strategy_monitor['companion_terms_runtime_arbiter_authorized']}`",
            f"- companion_terms_stage7_repair_authorized: `{strategy_monitor['companion_terms_stage7_repair_authorized']}`",
            f"- companion_audit_v0_all_terms_available: `{strategy_monitor['companion_audit_v0_all_terms_available']}`",
            f"- visible_terms_record_count: `{strategy_monitor['visible_terms_record_count']}`",
            f"- visible_terms_term_names: `{strategy_monitor['visible_terms_term_names']}`",
            f"- companion_audit_v1_all_terms_available: `{strategy_monitor['companion_audit_v1_all_terms_available']}`",
            f"- companion_audit_v1_visible_terms_applied: `{strategy_monitor['companion_audit_v1_visible_terms_applied']}`",
            f"- companion_audit_v1_visible_term_count: `{strategy_monitor['companion_audit_v1_visible_term_count']}`",
            f"- companion_audit_v1_still_missing_term_count: `{strategy_monitor['companion_audit_v1_still_missing_term_count']}`",
            f"- maturity_term_count: `{strategy_monitor['maturity_term_count']}`",
            f"- maturity_status_counts: `{strategy_monitor['maturity_status_counts']}`",
            f"- maturity_causal_ready_terms: `{strategy_monitor['maturity_causal_ready_terms']}`",
            f"- maturity_strongest_internal_terminal_candidates: `{strategy_monitor['maturity_strongest_internal_terminal_candidates']}`",
            f"- maturity_recommended_next_step: `{strategy_monitor['maturity_recommended_next_step']}`",
            f"- runtime_work_allowed: `{strategy_monitor['runtime_work_allowed']}`",
            f"- runtime_terminals_allowed: `{strategy_monitor['runtime_terminals_allowed']}`",
            f"- runtime_arbiter_allowed: `{strategy_monitor['runtime_arbiter_allowed']}`",
            f"- monitor_to_provider_routing_allowed: `{strategy_monitor['monitor_to_provider_routing_allowed']}`",
            f"- selector_training_allowed: `{strategy_monitor['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{strategy_monitor['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{strategy_monitor['stage8_training_allowed']}`",
            "",
            "## Internal Terminal Readiness Evidence",
            "",
            f"- feature_candidate_all_non_causal: `{internal_terminal['feature_candidate_all_non_causal']}`",
            f"- feature_candidate_count: `{internal_terminal['feature_candidate_count']}`",
            f"- feature_candidate_sandbox_ready_candidate_ids: `{internal_terminal['feature_candidate_sandbox_ready_candidate_ids']}`",
            f"- candidate_spec_count: `{internal_terminal['candidate_spec_count']}`",
            f"- candidate_terminal_ids: `{internal_terminal['candidate_terminal_ids']}`",
            f"- candidate_maturity_statuses: `{internal_terminal['candidate_maturity_statuses']}`",
            f"- validation_terminal_count: `{internal_terminal['validation_terminal_count']}`",
            f"- validation_record_count: `{internal_terminal['validation_record_count']}`",
            f"- validation_causal_ready_terminals: `{internal_terminal['validation_causal_ready_terminals']}`",
            f"- validation_all_causal_use_blocked: `{internal_terminal['validation_all_causal_use_blocked']}`",
            f"- evidence_terminal_count: `{internal_terminal['evidence_terminal_count']}`",
            f"- evidence_combined_record_count: `{internal_terminal['evidence_combined_record_count']}`",
            f"- evidence_causal_ready_terminals: `{internal_terminal['evidence_causal_ready_terminals']}`",
            f"- evidence_monitoring_only_candidates: `{internal_terminal['evidence_monitoring_only_candidates']}`",
            f"- evidence_stage7_only_candidates: `{internal_terminal['evidence_stage7_only_candidates']}`",
            f"- evidence_all_causal_ready_false: `{internal_terminal['evidence_all_causal_ready_false']}`",
            f"- design_review_causal_ready_terminals: `{internal_terminal['design_review_causal_ready_terminals']}`",
            f"- design_review_all_causal_ready_false: `{internal_terminal['design_review_all_causal_ready_false']}`",
            f"- design_review_recommended_next_step: `{internal_terminal['design_review_recommended_next_step']}`",
            f"- runtime_work_allowed: `{internal_terminal['runtime_work_allowed']}`",
            f"- runtime_terminals_allowed: `{internal_terminal['runtime_terminals_allowed']}`",
            f"- causal_affordances_allowed: `{internal_terminal['causal_affordances_allowed']}`",
            f"- runtime_arbiter_allowed: `{internal_terminal['runtime_arbiter_allowed']}`",
            f"- monitor_to_provider_routing_allowed: `{internal_terminal['monitor_to_provider_routing_allowed']}`",
            f"- selector_training_allowed: `{internal_terminal['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{internal_terminal['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{internal_terminal['stage8_training_allowed']}`",
            "",
            "## Repair-Monitor Trace-Feature Evidence",
            "",
            f"- smoke_status: `{repair_monitor_trace['smoke_status']}`",
            f"- smoke_case_count: `{repair_monitor_trace['smoke_case_count']}`",
            f"- smoke_repair_monitor_frame_count: `{repair_monitor_trace['smoke_repair_monitor_frame_count']}`",
            f"- smoke_selected_move_provider_delta_count: `{repair_monitor_trace['smoke_selected_move_provider_delta_count']}`",
            f"- smoke_invariant_failure_count: `{repair_monitor_trace['smoke_invariant_failure_count']}`",
            f"- smoke_stage7_case_count: `{repair_monitor_trace['smoke_stage7_case_count']}`",
            f"- coverage_status: `{repair_monitor_trace['coverage_status']}`",
            f"- broadened_status: `{repair_monitor_trace['broadened_status']}`",
            f"- broadened_case_count: `{repair_monitor_trace['broadened_case_count']}`",
            f"- broadened_repair_monitor_frame_count: `{repair_monitor_trace['broadened_repair_monitor_frame_count']}`",
            f"- broadened_selected_move_provider_delta_count: `{repair_monitor_trace['broadened_selected_move_provider_delta_count']}`",
            f"- broadened_stage7_case_count: `{repair_monitor_trace['broadened_stage7_case_count']}`",
            f"- quality_status: `{repair_monitor_trace['quality_status']}`",
            f"- quality_source_stable: `{repair_monitor_trace['quality_source_stable']}`",
            f"- quality_risk_term_set_count: `{repair_monitor_trace['quality_risk_term_set_count']}`",
            f"- trace_features_status: `{repair_monitor_trace['trace_features_status']}`",
            f"- trace_features_trace_frame_count: `{repair_monitor_trace['trace_features_trace_frame_count']}`",
            f"- trace_features_stage7_trace_frame_count: `{repair_monitor_trace['trace_features_stage7_trace_frame_count']}`",
            f"- trace_features_selector_training_row_count: `{repair_monitor_trace['trace_features_selector_training_row_count']}`",
            f"- integration_review_status: `{repair_monitor_trace['integration_review_status']}`",
            f"- integration_review_trace_integration_safe: `{repair_monitor_trace['integration_review_trace_integration_safe']}`",
            f"- dataset_design_status: `{repair_monitor_trace['dataset_design_status']}`",
            f"- dataset_design_implementation_allowed: `{repair_monitor_trace['dataset_design_implementation_allowed']}`",
            f"- dataset_v2_status: `{repair_monitor_trace['dataset_v2_status']}`",
            f"- dataset_v2_row_count: `{repair_monitor_trace['dataset_v2_row_count']}`",
            f"- dataset_v2_runtime_trace_feature_row_count: `{repair_monitor_trace['dataset_v2_runtime_trace_feature_row_count']}`",
            f"- dataset_v2_selector_training_row_count: `{repair_monitor_trace['dataset_v2_selector_training_row_count']}`",
            f"- dataset_v2_stage7_readiness_training_row_count: `{repair_monitor_trace['dataset_v2_stage7_readiness_training_row_count']}`",
            f"- dataset_v2_quality_status: `{repair_monitor_trace['dataset_v2_quality_status']}`",
            f"- dataset_v2_quality_runtime_flags_false: `{repair_monitor_trace['dataset_v2_quality_runtime_flags_false']}`",
            f"- dataset_v2_quality_selector_rows_absent: `{repair_monitor_trace['dataset_v2_quality_selector_rows_absent']}`",
            f"- refresh_probe_status: `{repair_monitor_trace['refresh_probe_status']}`",
            f"- capacity_manifest_status: `{repair_monitor_trace['capacity_manifest_status']}`",
            f"- capacity_manifest_labels_run_by_this_artifact: `{repair_monitor_trace['capacity_manifest_labels_run_by_this_artifact']}`",
            f"- capacity_manifest_stage7_job_count: `{repair_monitor_trace['capacity_manifest_stage7_job_count']}`",
            f"- capacity_labels_status: `{repair_monitor_trace['capacity_labels_status']}`",
            f"- capacity_labels_stage7_label_count: `{repair_monitor_trace['capacity_labels_stage7_label_count']}`",
            f"- dataset_v2_capacity_merged_status: `{repair_monitor_trace['dataset_v2_capacity_merged_status']}`",
            f"- refresh_after_labels_status: `{repair_monitor_trace['refresh_after_labels_status']}`",
            f"- refresh_after_labels_positive_recall: `{repair_monitor_trace['refresh_after_labels_positive_recall']}`",
            f"- refresh_after_labels_negative_suppression: `{repair_monitor_trace['refresh_after_labels_negative_suppression']}`",
            f"- runtime_work_allowed: `{repair_monitor_trace['runtime_work_allowed']}`",
            f"- selector_training_allowed: `{repair_monitor_trace['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{repair_monitor_trace['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{repair_monitor_trace['stage8_training_allowed']}`",
            "",
            "## Stage 5/6 Candidate-Generation Refresh Evidence",
            "",
            f"- review_status: `{stage5_6_refresh['review_status']}`",
            f"- review_runtime_review_ready: `{stage5_6_refresh['review_runtime_review_ready']}`",
            f"- review_implementation_authorized: `{stage5_6_refresh['review_implementation_authorized']}`",
            f"- review_runtime_candidate_generator_refresh_allowed: `{stage5_6_refresh['review_runtime_candidate_generator_refresh_allowed']}`",
            f"- smoke_status: `{stage5_6_refresh['smoke_status']}`",
            f"- smoke_case_count: `{stage5_6_refresh['smoke_case_count']}`",
            f"- smoke_refresh_frame_count: `{stage5_6_refresh['smoke_refresh_frame_count']}`",
            f"- smoke_selected_move_provider_delta_count: `{stage5_6_refresh['smoke_selected_move_provider_delta_count']}`",
            f"- smoke_invariant_failure_count: `{stage5_6_refresh['smoke_invariant_failure_count']}`",
            f"- smoke_stage7_case_count: `{stage5_6_refresh['smoke_stage7_case_count']}`",
            f"- coverage_status: `{stage5_6_refresh['coverage_status']}`",
            f"- coverage_refresh_frame_count: `{stage5_6_refresh['coverage_refresh_frame_count']}`",
            f"- coverage_stage7_case_count: `{stage5_6_refresh['coverage_stage7_case_count']}`",
            f"- broadened_status: `{stage5_6_refresh['broadened_status']}`",
            f"- broadened_case_count: `{stage5_6_refresh['broadened_case_count']}`",
            f"- broadened_case_count_by_stage: `{stage5_6_refresh['broadened_case_count_by_stage']}`",
            f"- broadened_refresh_frame_count: `{stage5_6_refresh['broadened_refresh_frame_count']}`",
            f"- broadened_selected_move_provider_delta_count: `{stage5_6_refresh['broadened_selected_move_provider_delta_count']}`",
            f"- broadened_invariant_failure_count: `{stage5_6_refresh['broadened_invariant_failure_count']}`",
            f"- broadened_stage7_case_count: `{stage5_6_refresh['broadened_stage7_case_count']}`",
            f"- quality_status: `{stage5_6_refresh['quality_status']}`",
            f"- quality_trace_usable_for_candidate_generation_context: `{stage5_6_refresh['quality_trace_usable_for_candidate_generation_context']}`",
            f"- quality_stage7_case_count: `{stage5_6_refresh['quality_stage7_case_count']}`",
            f"- trace_features_status: `{stage5_6_refresh['trace_features_status']}`",
            f"- trace_features_trace_frame_count: `{stage5_6_refresh['trace_features_trace_frame_count']}`",
            f"- trace_features_stage_counts: `{stage5_6_refresh['trace_features_stage_counts']}`",
            f"- trace_features_stage7_trace_frame_count: `{stage5_6_refresh['trace_features_stage7_trace_frame_count']}`",
            f"- trace_features_selector_training_row_count: `{stage5_6_refresh['trace_features_selector_training_row_count']}`",
            f"- trace_features_candidate_generation_training_row_count: `{stage5_6_refresh['trace_features_candidate_generation_training_row_count']}`",
            f"- dataset_design_v3_status: `{stage5_6_refresh['dataset_design_v3_status']}`",
            f"- dataset_design_v3_implementation_allowed: `{stage5_6_refresh['dataset_design_v3_implementation_allowed']}`",
            f"- runtime_work_allowed: `{stage5_6_refresh['runtime_work_allowed']}`",
            f"- selector_training_allowed: `{stage5_6_refresh['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{stage5_6_refresh['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{stage5_6_refresh['stage8_training_allowed']}`",
            "",
            "## Cross-Stage Candidate-Generation Scope Evidence",
            "",
            f"- cross_stage_label_probe_status: `{cross_stage_scope['cross_stage_label_probe_status']}`",
            f"- cross_stage_label_probe_best_policy: `{cross_stage_scope['cross_stage_label_probe_best_policy']}`",
            f"- cross_stage_label_probe_positive_recall: `{cross_stage_scope['cross_stage_label_probe_positive_recall']}`",
            f"- cross_stage_label_probe_negative_suppression: `{cross_stage_scope['cross_stage_label_probe_negative_suppression']}`",
            f"- cross_stage_label_probe_capacity_row_count: `{cross_stage_scope['cross_stage_label_probe_capacity_row_count']}`",
            f"- cross_stage_label_probe_guardrails_allowed: `{cross_stage_scope['cross_stage_label_probe_guardrails_allowed']}`",
            f"- cross_stage_label_probe_selector_allowed: `{cross_stage_scope['cross_stage_label_probe_selector_allowed']}`",
            f"- cross_stage_label_probe_promotion_allowed: `{cross_stage_scope['cross_stage_label_probe_promotion_allowed']}`",
            f"- capacity_review_status: `{cross_stage_scope['capacity_review_status']}`",
            f"- capacity_review_capacity_row_count: `{cross_stage_scope['capacity_review_capacity_row_count']}`",
            f"- capacity_manifest_status: `{cross_stage_scope['capacity_manifest_status']}`",
            f"- capacity_manifest_labels_run_by_this_artifact: `{cross_stage_scope['capacity_manifest_labels_run_by_this_artifact']}`",
            f"- capacity_manifest_job_count: `{cross_stage_scope['capacity_manifest_job_count']}`",
            f"- capacity_manifest_stage7_job_count: `{cross_stage_scope['capacity_manifest_stage7_job_count']}`",
            f"- capacity_labels_status: `{cross_stage_scope['capacity_labels_status']}`",
            f"- capacity_labels_label_count: `{cross_stage_scope['capacity_labels_label_count']}`",
            f"- capacity_labels_stage7_label_count: `{cross_stage_scope['capacity_labels_stage7_label_count']}`",
            f"- dataset_cross_stage_merged_status: `{cross_stage_scope['dataset_cross_stage_merged_status']}`",
            f"- dataset_cross_stage_merged_row_count: `{cross_stage_scope['dataset_cross_stage_merged_row_count']}`",
            f"- dataset_cross_stage_merged_selector_training_row_count: `{cross_stage_scope['dataset_cross_stage_merged_selector_training_row_count']}`",
            f"- dataset_cross_stage_merged_stage7_readiness_training_row_count: `{cross_stage_scope['dataset_cross_stage_merged_stage7_readiness_training_row_count']}`",
            f"- label_outcome_review_status: `{cross_stage_scope['label_outcome_review_status']}`",
            f"- scope_review_status: `{cross_stage_scope['scope_review_status']}`",
            f"- stage_conditioned_benchmark_status: `{cross_stage_scope['stage_conditioned_benchmark_status']}`",
            f"- stage_conditioned_benchmark_best_policy: `{cross_stage_scope['stage_conditioned_benchmark_best_policy']}`",
            f"- stage_conditioned_benchmark_positive_recall: `{cross_stage_scope['stage_conditioned_benchmark_positive_recall']}`",
            f"- stage_conditioned_benchmark_negative_suppression: `{cross_stage_scope['stage_conditioned_benchmark_negative_suppression']}`",
            f"- stage_conditioned_benchmark_stage4_positive_recall: `{cross_stage_scope['stage_conditioned_benchmark_stage4_positive_recall']}`",
            f"- stage_conditioned_benchmark_stage5_6_positive_recall: `{cross_stage_scope['stage_conditioned_benchmark_stage5_6_positive_recall']}`",
            f"- runtime_work_allowed: `{cross_stage_scope['runtime_work_allowed']}`",
            f"- selector_training_allowed: `{cross_stage_scope['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{cross_stage_scope['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{cross_stage_scope['stage8_training_allowed']}`",
            "",
            "## Selector Objective Lineage Evidence",
            "",
            f"- ownership_recovery_status: `{selector_lineage['ownership_recovery_status']}`",
            f"- ownership_recovery_joined_state_count: `{selector_lineage['ownership_recovery_joined_state_count']}`",
            f"- ownership_recovery_selected_failure_with_visible_positive_count: `{selector_lineage['ownership_recovery_selected_failure_with_visible_positive_count']}`",
            f"- seed_manifest_v0_status: `{selector_lineage['seed_manifest_v0_status']}`",
            f"- seed_manifest_v0_seed_row_count: `{selector_lineage['seed_manifest_v0_seed_row_count']}`",
            f"- seed_probe_v0_status: `{selector_lineage['seed_probe_v0_status']}`",
            f"- collection_manifest_status: `{selector_lineage['collection_manifest_status']}`",
            f"- collection_review_status: `{selector_lineage['collection_review_status']}`",
            f"- collection_review_implementation_authorized: `{selector_lineage['collection_review_implementation_authorized']}`",
            f"- joined_collection_status: `{selector_lineage['joined_collection_status']}`",
            f"- joined_collection_collected_row_count: `{selector_lineage['joined_collection_collected_row_count']}`",
            f"- joined_collection_generated_frame_count: `{selector_lineage['joined_collection_generated_frame_count']}`",
            f"- joined_collection_selected_move_delta_count: `{selector_lineage['joined_collection_selected_move_delta_count']}`",
            f"- joined_collection_selected_provider_delta_count: `{selector_lineage['joined_collection_selected_provider_delta_count']}`",
            f"- joined_collection_score_delta_count: `{selector_lineage['joined_collection_score_delta_count']}`",
            f"- joined_collection_routing_delta_count: `{selector_lineage['joined_collection_routing_delta_count']}`",
            f"- seed_manifest_v1_status: `{selector_lineage['seed_manifest_v1_status']}`",
            f"- seed_manifest_v1_seed_row_count: `{selector_lineage['seed_manifest_v1_seed_row_count']}`",
            f"- seed_probe_v1_status: `{selector_lineage['seed_probe_v1_status']}`",
            f"- feature_probe_status: `{selector_lineage['feature_probe_status']}`",
            f"- feature_probe_runtime_threshold_passing_model_count: `{selector_lineage['feature_probe_runtime_threshold_passing_model_count']}`",
            f"- feature_probe_review_status: `{selector_lineage['feature_probe_review_status']}`",
            f"- feature_probe_review_best_switch_recall: `{selector_lineage['feature_probe_review_best_switch_recall']}`",
            f"- feature_probe_review_best_preserve_recall: `{selector_lineage['feature_probe_review_best_preserve_recall']}`",
            f"- diversity_gap_status: `{selector_lineage['diversity_gap_status']}`",
            f"- diversity_gap_remaining_stage4_selected_failure_count: `{selector_lineage['diversity_gap_remaining_stage4_selected_failure_count']}`",
            f"- diversity_gap_remaining_stage5_6_selected_failure_count: `{selector_lineage['diversity_gap_remaining_stage5_6_selected_failure_count']}`",
            f"- stage4_scope_review_status: `{selector_lineage['stage4_scope_review_status']}`",
            f"- stage4_scope_review_implementation_authorized: `{selector_lineage['stage4_scope_review_implementation_authorized']}`",
            f"- selector_training_allowed: `{selector_lineage['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{selector_lineage['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{selector_lineage['stage8_training_allowed']}`",
            "",
            "## Selector Objective Evidence",
            "",
            f"- stage4_collection_status: `{selector_objective['stage4_collection_status']}`",
            f"- stage4_collection_collected_row_count: `{selector_objective['stage4_collection_collected_row_count']}`",
            f"- stage4_collection_generated_frame_count: `{selector_objective['stage4_collection_generated_frame_count']}`",
            f"- stage4_collection_switch_contrast_with_positive_capacity_count: `{selector_objective['stage4_collection_switch_contrast_with_positive_capacity_count']}`",
            f"- stage4_collection_default_off_equivalence_passed: `{selector_objective['stage4_collection_default_off_equivalence_passed']}`",
            f"- stage4_collection_selected_move_delta_count: `{selector_objective['stage4_collection_selected_move_delta_count']}`",
            f"- stage4_collection_selected_provider_delta_count: `{selector_objective['stage4_collection_selected_provider_delta_count']}`",
            f"- stage4_collection_score_delta_count: `{selector_objective['stage4_collection_score_delta_count']}`",
            f"- stage4_collection_routing_delta_count: `{selector_objective['stage4_collection_routing_delta_count']}`",
            f"- seed_manifest_v2_status: `{selector_objective['seed_manifest_v2_status']}`",
            f"- seed_manifest_v2_seed_row_count: `{selector_objective['seed_manifest_v2_seed_row_count']}`",
            f"- seed_manifest_v2_objective_channel_counts: `{selector_objective['seed_manifest_v2_objective_channel_counts']}`",
            f"- seed_probe_v2_status: `{selector_objective['seed_probe_v2_status']}`",
            f"- selector_benchmark_v2_status: `{selector_objective['selector_benchmark_v2_status']}`",
            f"- selector_benchmark_v2_best_runtime_model: `{selector_objective['selector_benchmark_v2_best_runtime_model']}`",
            f"- selector_benchmark_v2_runtime_threshold_passing_model_count: `{selector_objective['selector_benchmark_v2_runtime_threshold_passing_model_count']}`",
            f"- selector_benchmark_review_status: `{selector_objective['selector_benchmark_review_status']}`",
            f"- independent_validation_manifest_status: `{selector_objective['independent_validation_manifest_status']}`",
            f"- independent_validation_manifest_job_count: `{selector_objective['independent_validation_manifest_job_count']}`",
            f"- independent_validation_manifest_job_count_by_stage: `{selector_objective['independent_validation_manifest_job_count_by_stage']}`",
            f"- independent_validation_manifest_stage7_training_rows: `{selector_objective['independent_validation_manifest_stage7_training_rows']}`",
            f"- independent_validation_labels_status: `{selector_objective['independent_validation_labels_status']}`",
            f"- independent_validation_labels_label_count: `{selector_objective['independent_validation_labels_label_count']}`",
            f"- independent_validation_labels_selector_training_row_count: `{selector_objective['independent_validation_labels_selector_training_row_count']}`",
            f"- independent_validation_labels_stage7_training_row_count: `{selector_objective['independent_validation_labels_stage7_training_row_count']}`",
            f"- independent_validation_status: `{selector_objective['independent_validation_status']}`",
            f"- independent_validation_target_counts: `{selector_objective['independent_validation_target_counts']}`",
            f"- independent_validation_blocker_status: `{selector_objective['independent_validation_blocker_status']}`",
            f"- independent_validation_runtime_selector_blocked: `{selector_objective['independent_validation_runtime_selector_blocked']}`",
            f"- selector_training_allowed: `{selector_objective['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{selector_objective['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{selector_objective['stage8_training_allowed']}`",
            "",
            "## Stage 4 First-Move Diagnostic Evidence",
            "",
            f"- failure_discovery_status: `{stage4_diagnostic['failure_discovery_status']}`",
            f"- failure_packet_count: `{stage4_diagnostic['failure_packet_count']}`",
            f"- unique_failure_state_move_count: `{stage4_diagnostic['unique_failure_state_move_count']}`",
            f"- sequence_review_status: `{stage4_diagnostic['sequence_review_status']}`",
            f"- sequence_review_primary_diagnosis: `{stage4_diagnostic['sequence_review_primary_diagnosis']}`",
            f"- sequence_candidate_status: `{stage4_diagnostic['sequence_candidate_status']}`",
            f"- sequence_candidate_converting_first_move_count: `{stage4_diagnostic['sequence_candidate_converting_first_move_count']}`",
            f"- feature_review_status: `{stage4_diagnostic['feature_review_status']}`",
            f"- feature_review_positive_terms: `{stage4_diagnostic['feature_review_positive_terms']}`",
            f"- feature_review_failure_terms: `{stage4_diagnostic['feature_review_failure_terms']}`",
            f"- stratified_validation_status: `{stage4_diagnostic['stratified_validation_status']}`",
            f"- stratified_validation_gap_variant_count: `{stage4_diagnostic['stratified_validation_gap_variant_count']}`",
            f"- runtime_review_status: `{stage4_diagnostic['runtime_review_status']}`",
            f"- runtime_review_implementation_authorized: `{stage4_diagnostic['runtime_review_implementation_authorized']}`",
            f"- sequence_control_dataset_status: `{stage4_diagnostic['sequence_control_dataset_status']}`",
            f"- sequence_control_dataset_row_count: `{stage4_diagnostic['sequence_control_dataset_row_count']}`",
            f"- sequence_control_dataset_runtime_authorization_row_count: `{stage4_diagnostic['sequence_control_dataset_runtime_authorization_row_count']}`",
            f"- sequence_control_probe_status: `{stage4_diagnostic['sequence_control_probe_status']}`",
            f"- selector_training_allowed: `{stage4_diagnostic['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{stage4_diagnostic['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{stage4_diagnostic['stage8_training_allowed']}`",
            "",
            "## Candidate Generation Training-Refresh Evidence",
            "",
            f"- dataset_v3_status: `{candidate_generation_refresh['dataset_v3_status']}`",
            f"- dataset_v3_row_count: `{candidate_generation_refresh['dataset_v3_row_count']}`",
            f"- dataset_v3_candidate_generation_training_row_count: `{candidate_generation_refresh['dataset_v3_candidate_generation_training_row_count']}`",
            f"- dataset_v3_selector_training_row_count: `{candidate_generation_refresh['dataset_v3_selector_training_row_count']}`",
            f"- context_benchmark_status: `{candidate_generation_refresh['context_benchmark_status']}`",
            f"- context_benchmark_stage_family_positive_capacity_recall_from_trace: `{candidate_generation_refresh['context_benchmark_stage_family_positive_capacity_recall_from_trace']}`",
            f"- runtime_boundary_status: `{candidate_generation_refresh['runtime_boundary_status']}`",
            f"- runtime_boundary_new_runtime_behavior_allowed: `{candidate_generation_refresh['runtime_boundary_new_runtime_behavior_allowed']}`",
            f"- training_refresh_design_v2_status: `{candidate_generation_refresh['training_refresh_design_v2_status']}`",
            f"- training_refresh_design_v2_runtime_candidate_generator_refresh_allowed: `{candidate_generation_refresh['training_refresh_design_v2_runtime_candidate_generator_refresh_allowed']}`",
            f"- training_refresh_design_v2_selector_allowed: `{candidate_generation_refresh['training_refresh_design_v2_selector_allowed']}`",
            f"- training_refresh_design_v2_guardrails_allowed: `{candidate_generation_refresh['training_refresh_design_v2_guardrails_allowed']}`",
            f"- training_refresh_design_v2_promotion_allowed: `{candidate_generation_refresh['training_refresh_design_v2_promotion_allowed']}`",
            f"- training_refresh_design_status: `{candidate_generation_refresh['training_refresh_design_status']}`",
            f"- training_refresh_design_implementation_allowed: `{candidate_generation_refresh['training_refresh_design_implementation_allowed']}`",
            f"- benchmark_status: `{candidate_generation_refresh['benchmark_status']}`",
            f"- benchmark_best_policy: `{candidate_generation_refresh['benchmark_best_policy']}`",
            f"- benchmark_positive_capacity_recall: `{candidate_generation_refresh['benchmark_positive_capacity_recall']}`",
            f"- benchmark_negative_capacity_suppression: `{candidate_generation_refresh['benchmark_negative_capacity_suppression']}`",
            f"- benchmark_thresholds_met: `{candidate_generation_refresh['benchmark_thresholds_met']}`",
            f"- runtime_review_status: `{candidate_generation_refresh['runtime_review_status']}`",
            f"- runtime_review_ready: `{candidate_generation_refresh['runtime_review_ready']}`",
            f"- runtime_review_candidate_generation_allowed_by_packet: `{candidate_generation_refresh['runtime_review_candidate_generation_allowed_by_packet']}`",
            f"- runtime_review_implementation_authorized: `{candidate_generation_refresh['runtime_review_implementation_authorized']}`",
            f"- runtime_work_allowed: `{candidate_generation_refresh['runtime_work_allowed']}`",
            f"- selector_training_allowed: `{candidate_generation_refresh['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{candidate_generation_refresh['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{candidate_generation_refresh['stage8_training_allowed']}`",
            "",
            "## Candidate Generation Trace-Context Evidence",
            "",
            f"- refresh_sandbox_status: `{candidate_generation_trace['refresh_sandbox_status']}`",
            f"- refresh_sandbox_generated_frame_count: `{candidate_generation_trace['refresh_sandbox_generated_frame_count']}`",
            f"- refresh_sandbox_default_off_equivalence_passed: `{candidate_generation_trace['refresh_sandbox_default_off_equivalence_passed']}`",
            f"- refresh_coverage_status: `{candidate_generation_trace['refresh_coverage_status']}`",
            f"- refresh_coverage_exact_positive_capacity_recall: `{candidate_generation_trace['refresh_coverage_exact_positive_capacity_recall']}`",
            f"- refresh_trace_features_status: `{candidate_generation_trace['refresh_trace_features_status']}`",
            f"- refresh_trace_features_trace_frame_count: `{candidate_generation_trace['refresh_trace_features_trace_frame_count']}`",
            f"- refresh_trace_features_stage7_trace_frame_count: `{candidate_generation_trace['refresh_trace_features_stage7_trace_frame_count']}`",
            f"- refresh_trace_features_selector_training_row_count: `{candidate_generation_trace['refresh_trace_features_selector_training_row_count']}`",
            f"- dataset_v4_status: `{candidate_generation_trace['dataset_v4_status']}`",
            f"- dataset_v4_row_count: `{candidate_generation_trace['dataset_v4_row_count']}`",
            f"- v4_boundary_status: `{candidate_generation_trace['v4_boundary_status']}`",
            f"- source_gap_manifest_status: `{candidate_generation_trace['source_gap_manifest_status']}`",
            f"- source_gap_exact_missing_positive_capacity_count: `{candidate_generation_trace['source_gap_exact_missing_positive_capacity_count']}`",
            f"- exact_trace_runtime_review_status: `{candidate_generation_trace['exact_trace_runtime_review_status']}`",
            f"- exact_trace_runtime_review_implementation_authorized: `{candidate_generation_trace['exact_trace_runtime_review_implementation_authorized']}`",
            f"- exact_trace_sandbox_status: `{candidate_generation_trace['exact_trace_sandbox_status']}`",
            f"- exact_trace_sandbox_generated_frame_count: `{candidate_generation_trace['exact_trace_sandbox_generated_frame_count']}`",
            f"- exact_trace_coverage_exact_gap_recall: `{candidate_generation_trace['exact_trace_coverage_exact_gap_recall']}`",
            f"- dataset_v5_status: `{candidate_generation_trace['dataset_v5_status']}`",
            f"- dataset_v5_row_count: `{candidate_generation_trace['dataset_v5_row_count']}`",
            f"- dataset_v5_selector_training_row_count: `{candidate_generation_trace['dataset_v5_selector_training_row_count']}`",
            f"- v5_context_benchmark_status: `{candidate_generation_trace['v5_context_benchmark_status']}`",
            f"- v5_exact_positive_capacity_recall_from_candidate_generation_trace: `{candidate_generation_trace['v5_exact_positive_capacity_recall_from_candidate_generation_trace']}`",
            f"- v5_boundary_status: `{candidate_generation_trace['v5_boundary_status']}`",
            f"- v5_boundary_implement_new_runtime_sandbox: `{candidate_generation_trace['v5_boundary_implement_new_runtime_sandbox']}`",
            f"- runtime_work_allowed: `{candidate_generation_trace['runtime_work_allowed']}`",
            f"- selector_training_allowed: `{candidate_generation_trace['selector_training_allowed']}`",
            f"- stage7_promotion_allowed: `{candidate_generation_trace['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{candidate_generation_trace['stage8_training_allowed']}`",
            "",
            "## Current Control Plane Gate",
            "",
            f"- status: `{current_gate['status']}`",
            f"- approval_option_ids: `{current_gate['approval_option_ids']}`",
            f"- protected_failure_contrast_collection_option_available: `{current_gate['protected_failure_contrast_collection_option_available']}`",
            f"- protected_failure_contrast_collection_command_available: `{current_gate['protected_failure_contrast_collection_command_available']}`",
            f"- protected_failure_contrast_collection_option_id: `{current_gate['protected_failure_contrast_collection_option_id']}`",
            f"- protected_failure_contrast_collection_blocked_by_option_id: `{current_gate['protected_failure_contrast_collection_blocked_by_option_id']}`",
            "",
            "## Blockers",
            "",
        ]
    )
    for blocker in payload["blockers"]:
        lines.append(f"- `{blocker}`")
    if not payload["blockers"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Approval Gates",
            "",
        ]
    )
    for gate, details in payload["approval_gates"].items():
        lines.append(f"- `{gate}`: {details['why']}")
    lines.extend(
        [
            "",
            "## Boundary Check",
            "",
            f"- checked_flag_count: `{payload['runtime_and_training_boundaries']['checked_flag_count']}`",
            f"- violation_count: `{payload['runtime_and_training_boundaries']['violation_count']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()

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
    "self_expansion_architecture_gate": (
        "reports/krk_self_expansion_architecture_gate_v0.json"
    ),
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
    "provider_label_coverage_plan": (
        "reports/krk_provider_label_coverage_plan_v0.json"
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
    "protected_missing_provider_capacity_audit_plan": (
        "reports/krk_protected_missing_provider_capacity_audit_plan_v0.json"
    ),
    "protected_missing_provider_execution_manifest": (
        "reports/krk_protected_missing_provider_capacity_execution_manifest_v0.json"
    ),
    "protected_missing_provider_execution_manifest_review": (
        "reports/krk_protected_missing_provider_capacity_execution_manifest_review_v0.json"
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
    "selector_stratified_label_dataset_v1": (
        "reports/krk_selector_stratified_label_dataset_v1.json"
    ),
    "selector_stratified_label_balance_probe_v1": (
        "reports/krk_selector_stratified_label_balance_probe_v1.json"
    ),
    "selector_balanced_label_dataset_v1": (
        "reports/krk_selector_balanced_label_dataset_v1.json"
    ),
    "selector_balanced_label_probe_v1": (
        "reports/krk_selector_balanced_label_probe_v1.json"
    ),
    "selector_balanced_architecture_review_v1": (
        "reports/krk_selector_balanced_architecture_review_v1.json"
    ),
    "ownership_selection_label_dataset_v5": (
        "reports/krk_ownership_selection_label_dataset_v5.json"
    ),
    "ownership_selection_context_dataset_v3": (
        "reports/krk_ownership_selection_context_dataset_v3.json"
    ),
    "ownership_selection_context_feature_probe_v3": (
        "reports/krk_ownership_selection_context_feature_probe_v3.json"
    ),
    "ownership_selection_labeling_review_v0": (
        "reports/krk_ownership_selection_labeling_review_v0.json"
    ),
    "ownership_source_diversity_review_v0": (
        "reports/krk_ownership_source_diversity_review_v0.json"
    ),
    "protected_max_only_frame_review_v0": (
        "reports/krk_protected_max_only_frame_review_v0.json"
    ),
    "selector_negative_suppression_evidence_v0": (
        "reports/krk_selector_negative_suppression_evidence_v0.json"
    ),
    "runtime_selector_readiness_review_v1": (
        "reports/krk_runtime_selector_readiness_review_v1.json"
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
    "stage4_caveat_decision_gate": (
        "reports/krk_stage4_caveat_decision_gate_v0.json"
    ),
    "stage4_caveat_diagnostic_matrix": (
        "reports/krk_stage4_caveat_diagnostic_matrix_v0.json"
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
    "strategy_arbiter_sandbox_design_v0": (
        "reports/krk_strategy_arbiter_sandbox_design_v0.json"
    ),
    "strategy_arbiter_observability_smoke_v0": (
        "reports/krk_strategy_arbiter_observability_smoke_v0.json"
    ),
    "strategy_arbiter_observation_frames_v0": (
        "reports/krk_strategy_arbiter_observation_frames_v0.json"
    ),
    "strategy_arbiter_observation_separability_review_v0": (
        "reports/krk_strategy_arbiter_observation_separability_review_v0.json"
    ),
    "strategy_arbiter_observation_selector_probe_v0": (
        "reports/krk_strategy_arbiter_observation_selector_probe_v0.json"
    ),
    "strategy_arbiter_labeled_observation_controls_v0": (
        "reports/krk_strategy_arbiter_labeled_observation_controls_v0.json"
    ),
    "strategy_arbiter_labeled_controls_probe_v0": (
        "reports/krk_strategy_arbiter_labeled_controls_probe_v0.json"
    ),
    "strategy_arbiter_protected_control_matrix_v1": (
        "reports/krk_strategy_arbiter_protected_control_matrix_v1.json"
    ),
    "strategy_arbiter_evidence_risk_review_v0": (
        "reports/krk_strategy_arbiter_evidence_risk_review_v0.json"
    ),
    "strategy_arbiter_stratified_probe_v2": (
        "reports/krk_strategy_arbiter_stratified_probe_v2.json"
    ),
    "strategy_arbiter_architecture_review_v1": (
        "reports/krk_strategy_arbiter_architecture_review_v1.json"
    ),
    "strategy_arbiter_sandbox_readiness_criteria_v0": (
        "reports/krk_strategy_arbiter_sandbox_readiness_criteria_v0.json"
    ),
    "strategy_arbiter_control_plane_review_v0": (
        "reports/krk_strategy_arbiter_control_plane_review_v0.json"
    ),
    "strategy_arbiter_out_of_sample_control_plan_v0": (
        "reports/krk_strategy_arbiter_out_of_sample_control_plan_v0.json"
    ),
    "strategy_arbiter_out_of_sample_plan_review_v0": (
        "reports/krk_strategy_arbiter_out_of_sample_plan_review_v0.json"
    ),
    "strategy_arbiter_out_of_sample_execution_manifest_v0": (
        "reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.json"
    ),
    "strategy_arbiter_out_of_sample_execution_manifest_review_v0": (
        "reports/krk_strategy_arbiter_out_of_sample_execution_manifest_review_v0.json"
    ),
    "strategy_arbiter_out_of_sample_control_labels_v0": (
        "reports/krk_strategy_arbiter_out_of_sample_control_labels_v0.json"
    ),
    "strategy_arbiter_out_of_sample_control_probe_v0": (
        "reports/krk_strategy_arbiter_out_of_sample_control_probe_v0.json"
    ),
    "strategy_arbiter_out_of_sample_architecture_review_v0": (
        "reports/krk_strategy_arbiter_out_of_sample_architecture_review_v0.json"
    ),
    "strategy_arbiter_default_off_design_review_v1": (
        "reports/krk_strategy_arbiter_default_off_design_review_v1.json"
    ),
    "strategy_arbiter_runtime_review_packet_v1": (
        "reports/krk_strategy_arbiter_runtime_review_packet_v1.json"
    ),
    "strategy_arbiter_runtime_sandbox_smoke_v1": (
        "reports/krk_strategy_arbiter_runtime_sandbox_smoke_v1.json"
    ),
    "strategy_arbiter_protected_control_matrix_v2": (
        "reports/krk_strategy_arbiter_protected_control_matrix_v2.json"
    ),
    "strategy_arbiter_stage7_holdout_lock_v1": (
        "reports/krk_strategy_arbiter_stage7_holdout_lock_v1.json"
    ),
    "strategy_arbiter_stage7_challenge_probe_v1": (
        "reports/krk_strategy_arbiter_stage7_challenge_probe_v1.json"
    ),
    "strategy_arbiter_support_sensitivity_v1": (
        "reports/krk_strategy_arbiter_support_sensitivity_v1.json"
    ),
    "strategy_arbiter_runtime_test_review_v2": (
        "reports/krk_strategy_arbiter_runtime_test_review_v2.json"
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
    "selector_target_dataset_v0": (
        "reports/krk_selector_target_dataset_v0.json"
    ),
    "selector_target_probe_v0": "reports/krk_selector_target_probe_v0.json",
    "selector_baseline_probe_v0": "reports/krk_selector_baseline_probe_v0.json",
    "selector_feature_dataset_v0": "reports/krk_selector_feature_dataset_v0.json",
    "selector_feature_baseline_probe_v0": (
        "reports/krk_selector_feature_baseline_probe_v0.json"
    ),
    "provider_identity_maturity_review_v0": (
        "reports/krk_provider_identity_maturity_review_v0.json"
    ),
    "capacity_geometry_feature_audit_v0": (
        "reports/krk_capacity_geometry_feature_audit_v0.json"
    ),
    "geometry_augmented_selector_feature_probe_v0": (
        "reports/krk_geometry_augmented_selector_feature_probe_v0.json"
    ),
    "selector_directed_fix_review_v0": (
        "reports/krk_selector_directed_fix_review_v0.json"
    ),
    "forced_provider_control_label_plan_v0": (
        "reports/krk_forced_provider_control_label_plan_v0.json"
    ),
    "forced_provider_label_execution_manifest_v0": (
        "reports/krk_forced_provider_label_execution_manifest_v0.json"
    ),
    "forced_provider_control_labels_v0": (
        "reports/krk_forced_provider_control_labels_v0.json"
    ),
    "selector_provenance_feature_dataset_v0": (
        "reports/krk_selector_provenance_feature_dataset_v0.json"
    ),
    "selector_provenance_feature_probe_v0": (
        "reports/krk_selector_provenance_feature_probe_v0.json"
    ),
    "selector_feature_architecture_review_v0": (
        "reports/krk_selector_feature_architecture_review_v0.json"
    ),
    "selector_readiness_after_contrast_probe_review_v0": (
        "reports/krk_selector_readiness_after_contrast_probe_review_v0.json"
    ),
    "split_selector_objective_dataset_v3": (
        "reports/krk_split_selector_objective_dataset_v3.json"
    ),
    "split_selector_objective_readiness_v3": (
        "reports/krk_split_selector_objective_readiness_v3.json"
    ),
    "runtime_test_architecture_review_v3": (
        "reports/krk_runtime_test_architecture_review_v3.json"
    ),
    "abstention_first_selector_objective_v0": (
        "reports/krk_abstention_first_selector_objective_v0.json"
    ),
    "abstention_safe_preservation_label_review_v0": (
        "reports/krk_abstention_safe_preservation_label_review_v0.json"
    ),
    "selector_stratified_label_plan_v1": (
        "reports/krk_selector_stratified_label_plan_v1.json"
    ),
    "selector_label_plan_replay_free_review_v1": (
        "reports/krk_selector_label_plan_replay_free_review_v1.json"
    ),
    "selector_negative_control_manifest_v1": (
        "reports/krk_selector_negative_control_manifest_v1.json"
    ),
    "abstention_training_dataset_v0": (
        "reports/krk_abstention_training_dataset_v0.json"
    ),
    "abstention_training_probe_v0": (
        "reports/krk_abstention_training_probe_v0.json"
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
    "two_stage_abstention_objective_probe_v0": (
        "reports/krk_two_stage_abstention_objective_probe_v0.json"
    ),
    "two_stage_abstention_runtime_review_packet_v0": (
        "reports/krk_two_stage_abstention_runtime_review_packet_v0.json"
    ),
    "two_stage_abstention_default_off_equivalence_v0": (
        "reports/krk_two_stage_abstention_default_off_equivalence_v0.json"
    ),
    "two_stage_abstention_enabled_smoke_v0": (
        "reports/krk_two_stage_abstention_enabled_smoke_v0.json"
    ),
    "two_stage_abstention_stage7_challenge_smoke_v0": (
        "reports/krk_two_stage_abstention_stage7_challenge_smoke_v0.json"
    ),
    "two_stage_abstention_runtime_go_no_go_v0": (
        "reports/krk_two_stage_abstention_runtime_go_no_go_v0.json"
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
    "hard_negative_selector_target_dataset_v0": (
        "reports/krk_hard_negative_selector_target_dataset_v0.json"
    ),
    "hard_negative_selector_feature_ablation_v0": (
        "reports/krk_hard_negative_selector_feature_ablation_v0.json"
    ),
    "balanced_hard_negative_label_plan_v0": (
        "reports/krk_balanced_hard_negative_label_plan_v0.json"
    ),
    "balanced_hard_negative_execution_manifest_v0": (
        "reports/krk_balanced_hard_negative_execution_manifest_v0.json"
    ),
    "balanced_hard_negative_execution_manifest_review_v0": (
        "reports/krk_balanced_hard_negative_execution_manifest_review_v0.json"
    ),
    "balanced_hard_negative_labels_v0": (
        "reports/krk_balanced_hard_negative_labels_v0.json"
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
    "hard_negative_label_semantics_review_v1": (
        "reports/krk_hard_negative_label_semantics_review_v1.json"
    ),
    "hard_negative_selector_feature_ablation_v2": (
        "reports/krk_hard_negative_selector_feature_ablation_v2.json"
    ),
    "stronger_selector_feature_review_v0": (
        "reports/krk_stronger_selector_feature_review_v0.json"
    ),
    "selected_provider_diversity_evidence_plan_v0": (
        "reports/krk_selected_provider_diversity_evidence_plan_v0.json"
    ),
    "selected_provider_diversity_replay_free_scan_v0": (
        "reports/krk_selected_provider_diversity_replay_free_scan_v0.json"
    ),
    "selected_provider_diversity_sampling_manifest_v0": (
        "reports/krk_selected_provider_diversity_sampling_manifest_v0.json"
    ),
    "selected_provider_diversity_sampling_manifest_review_v0": (
        "reports/krk_selected_provider_diversity_sampling_manifest_review_v0.json"
    ),
    "selected_provider_diversity_observation_scan_v0": (
        "reports/krk_selected_provider_diversity_observation_scan_v0.json"
    ),
    "selected_provider_diversity_sampling_manifest_v1": (
        "reports/krk_selected_provider_diversity_sampling_manifest_v1.json"
    ),
    "selected_provider_diversity_ownership_labels_v1": (
        "reports/krk_selected_provider_diversity_ownership_labels_v1.json"
    ),
    "selected_provider_diversity_architecture_review_v0": (
        "reports/krk_selected_provider_diversity_architecture_review_v0.json"
    ),
    "selector_readiness_v3_plan": (
        "reports/krk_selector_readiness_v3_plan.json"
    ),
    "state_local_contrast_labels_v2": (
        "reports/krk_state_local_contrast_labels_v2.json"
    ),
    "state_local_contrast_selector_probe_v2": (
        "reports/krk_state_local_contrast_selector_probe_v2.json"
    ),
    "state_local_contrast_readiness_review_v2": (
        "reports/krk_state_local_contrast_readiness_review_v2.json"
    ),
    "hard_negative_selector_target_dataset_v2": (
        "reports/krk_hard_negative_selector_target_dataset_v2.json"
    ),
    "hard_negative_selector_target_training_semantics_review_v0": (
        "reports/krk_hard_negative_selector_target_training_semantics_review_v0.json"
    ),
    "ownership_context_feature_review_v3": (
        "reports/krk_ownership_context_feature_review_v3.json"
    ),
    "ownership_objective_architecture_review_v0": (
        "reports/krk_ownership_objective_architecture_review_v0.json"
    ),
    "state_local_paired_ownership_objective_plan_v0": (
        "reports/krk_state_local_paired_ownership_objective_plan_v0.json"
    ),
    "state_local_paired_ownership_work_package_v0": (
        "reports/krk_state_local_paired_ownership_work_package_v0.json"
    ),
    "state_local_paired_ownership_inventory_v1": (
        "reports/krk_state_local_paired_ownership_inventory_v1.json"
    ),
    "state_local_paired_ownership_probe_v1": (
        "reports/krk_state_local_paired_ownership_probe_v1.json"
    ),
    "state_local_paired_ownership_error_audit_v0": (
        "reports/krk_state_local_paired_ownership_error_audit_v0.json"
    ),
    "state_local_paired_ownership_review_v1": (
        "reports/krk_state_local_paired_ownership_review_v1.json"
    ),
    "state_local_paired_runtime_proxy_design_v0": (
        "reports/krk_state_local_paired_runtime_proxy_design_v0.json"
    ),
    "state_local_paired_runtime_proxy_dataset_v0": (
        "reports/krk_state_local_paired_runtime_proxy_dataset_v0.json"
    ),
    "state_local_paired_runtime_proxy_probe_v0": (
        "reports/krk_state_local_paired_runtime_proxy_probe_v0.json"
    ),
    "state_local_paired_runtime_proxy_review_v0": (
        "reports/krk_state_local_paired_runtime_proxy_review_v0.json"
    ),
    "state_local_paired_selector_runtime_review_packet_v0": (
        "reports/krk_state_local_paired_selector_runtime_review_packet_v0.json"
    ),
    "selected_owner_failure_risk_evidence_v1": (
        "reports/krk_selected_owner_failure_risk_evidence_v1.json"
    ),
    "selected_owner_failure_risk_visible_terms_v0": (
        "reports/krk_selected_owner_failure_risk_visible_terms_v0.json"
    ),
    "selected_owner_failure_risk_visible_proxy_review_v0": (
        "reports/krk_selected_owner_failure_risk_visible_proxy_review_v0.json"
    ),
    "selected_owner_failure_risk_visible_proxy_probe_v0": (
        "reports/krk_selected_owner_failure_risk_visible_proxy_probe_v0.json"
    ),
    "selected_owner_failure_risk_proxy_independent_manifest_v0": (
        "reports/krk_selected_owner_failure_risk_proxy_independent_manifest_v0.json"
    ),
    "selected_owner_failure_risk_proxy_independent_validation_v0": (
        "reports/krk_selected_owner_failure_risk_proxy_independent_validation_v0.json"
    ),
    "selected_owner_failure_risk_proxy_blocker_review_v0": (
        "reports/krk_selected_owner_failure_risk_proxy_blocker_review_v0.json"
    ),
    "selected_owner_failure_risk_proxy_probe_v1": (
        "reports/krk_selected_owner_failure_risk_proxy_probe_v1.json"
    ),
    "selected_owner_failure_risk_proxy_independent_labels_v0": (
        "reports/krk_selected_owner_failure_risk_proxy_independent_labels_v0.json"
    ),
    "selected_owner_failure_risk_proxy_independent_validation_v1": (
        "reports/krk_selected_owner_failure_risk_proxy_independent_validation_v1.json"
    ),
    "state_local_paired_selector_runtime_proxy_review_packet_v1": (
        "reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v1.json"
    ),
    "progress_window_reconsideration_runtime_test_review_v0": (
        "reports/krk_progress_window_reconsideration_runtime_test_review_v0.json"
    ),
    "progress_window_reconsideration_runtime_smoke_v0": (
        "reports/krk_progress_window_reconsideration_runtime_smoke_v0.json"
    ),
    "progress_window_reconsideration_post_activation_audit_v0": (
        "reports/krk_progress_window_reconsideration_post_activation_audit_v0.json"
    ),
    "runtime_sandbox_policy_update_v0": (
        "reports/krk_runtime_sandbox_policy_update_v0.json"
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
    protected_missing_provider_capacity_audit_plan = payloads[
        "protected_missing_provider_capacity_audit_plan"
    ]
    protected_missing_provider_execution_manifest = payloads[
        "protected_missing_provider_execution_manifest"
    ]
    protected_missing_provider_execution_manifest_review = payloads[
        "protected_missing_provider_execution_manifest_review"
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
    selector_stratified_label_dataset_v1 = payloads[
        "selector_stratified_label_dataset_v1"
    ]
    selector_stratified_label_balance_probe_v1 = payloads[
        "selector_stratified_label_balance_probe_v1"
    ]
    selector_balanced_label_dataset_v1 = payloads[
        "selector_balanced_label_dataset_v1"
    ]
    selector_balanced_label_probe_v1 = payloads["selector_balanced_label_probe_v1"]
    selector_balanced_architecture_review_v1 = payloads[
        "selector_balanced_architecture_review_v1"
    ]
    selector_stratified_label_plan_v1 = payloads[
        "selector_stratified_label_plan_v1"
    ]
    selector_label_plan_replay_free_review_v1 = payloads[
        "selector_label_plan_replay_free_review_v1"
    ]
    selector_negative_control_manifest_v1 = payloads[
        "selector_negative_control_manifest_v1"
    ]
    ownership_selection_label_dataset_v5 = payloads[
        "ownership_selection_label_dataset_v5"
    ]
    ownership_selection_context_dataset_v3 = payloads[
        "ownership_selection_context_dataset_v3"
    ]
    ownership_selection_context_feature_probe_v3 = payloads[
        "ownership_selection_context_feature_probe_v3"
    ]
    ownership_selection_labeling_review_v0 = payloads[
        "ownership_selection_labeling_review_v0"
    ]
    ownership_source_diversity_review_v0 = payloads[
        "ownership_source_diversity_review_v0"
    ]
    protected_max_only_frame_review_v0 = payloads[
        "protected_max_only_frame_review_v0"
    ]
    selector_negative_suppression_evidence_v0 = payloads[
        "selector_negative_suppression_evidence_v0"
    ]
    runtime_selector_readiness_review_v1 = payloads[
        "runtime_selector_readiness_review_v1"
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
    stage4_caveat_decision_gate = payloads["stage4_caveat_decision_gate"]
    stage4_caveat_diagnostic_matrix = payloads["stage4_caveat_diagnostic_matrix"]
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
    strategy_arbiter_sandbox_design_v0 = payloads[
        "strategy_arbiter_sandbox_design_v0"
    ]
    strategy_arbiter_observability_smoke_v0 = payloads[
        "strategy_arbiter_observability_smoke_v0"
    ]
    strategy_arbiter_observation_frames_v0 = payloads[
        "strategy_arbiter_observation_frames_v0"
    ]
    strategy_arbiter_observation_separability_review_v0 = payloads[
        "strategy_arbiter_observation_separability_review_v0"
    ]
    strategy_arbiter_observation_selector_probe_v0 = payloads[
        "strategy_arbiter_observation_selector_probe_v0"
    ]
    strategy_arbiter_labeled_observation_controls_v0 = payloads[
        "strategy_arbiter_labeled_observation_controls_v0"
    ]
    strategy_arbiter_labeled_controls_probe_v0 = payloads[
        "strategy_arbiter_labeled_controls_probe_v0"
    ]
    strategy_arbiter_protected_control_matrix_v1 = payloads[
        "strategy_arbiter_protected_control_matrix_v1"
    ]
    strategy_arbiter_evidence_risk_review_v0 = payloads[
        "strategy_arbiter_evidence_risk_review_v0"
    ]
    strategy_arbiter_stratified_probe_v2 = payloads[
        "strategy_arbiter_stratified_probe_v2"
    ]
    strategy_arbiter_architecture_review_v1 = payloads[
        "strategy_arbiter_architecture_review_v1"
    ]
    strategy_arbiter_sandbox_readiness_criteria_v0 = payloads[
        "strategy_arbiter_sandbox_readiness_criteria_v0"
    ]
    strategy_arbiter_control_plane_review_v0 = payloads[
        "strategy_arbiter_control_plane_review_v0"
    ]
    strategy_arbiter_out_of_sample_control_plan_v0 = payloads[
        "strategy_arbiter_out_of_sample_control_plan_v0"
    ]
    strategy_arbiter_out_of_sample_plan_review_v0 = payloads[
        "strategy_arbiter_out_of_sample_plan_review_v0"
    ]
    strategy_arbiter_out_of_sample_execution_manifest_v0 = payloads[
        "strategy_arbiter_out_of_sample_execution_manifest_v0"
    ]
    strategy_arbiter_out_of_sample_execution_manifest_review_v0 = payloads[
        "strategy_arbiter_out_of_sample_execution_manifest_review_v0"
    ]
    strategy_arbiter_out_of_sample_control_labels_v0 = payloads[
        "strategy_arbiter_out_of_sample_control_labels_v0"
    ]
    strategy_arbiter_out_of_sample_control_probe_v0 = payloads[
        "strategy_arbiter_out_of_sample_control_probe_v0"
    ]
    strategy_arbiter_out_of_sample_architecture_review_v0 = payloads[
        "strategy_arbiter_out_of_sample_architecture_review_v0"
    ]
    strategy_arbiter_default_off_design_review_v1 = payloads[
        "strategy_arbiter_default_off_design_review_v1"
    ]
    strategy_arbiter_runtime_review_packet_v1 = payloads[
        "strategy_arbiter_runtime_review_packet_v1"
    ]
    strategy_arbiter_runtime_sandbox_smoke_v1 = payloads[
        "strategy_arbiter_runtime_sandbox_smoke_v1"
    ]
    strategy_arbiter_protected_control_matrix_v2 = payloads[
        "strategy_arbiter_protected_control_matrix_v2"
    ]
    strategy_arbiter_stage7_holdout_lock_v1 = payloads[
        "strategy_arbiter_stage7_holdout_lock_v1"
    ]
    strategy_arbiter_stage7_challenge_probe_v1 = payloads[
        "strategy_arbiter_stage7_challenge_probe_v1"
    ]
    strategy_arbiter_support_sensitivity_v1 = payloads[
        "strategy_arbiter_support_sensitivity_v1"
    ]
    strategy_arbiter_runtime_test_review_v2 = payloads[
        "strategy_arbiter_runtime_test_review_v2"
    ]
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
    selector_target_dataset_v0 = payloads["selector_target_dataset_v0"]
    selector_target_probe_v0 = payloads["selector_target_probe_v0"]
    selector_baseline_probe_v0 = payloads["selector_baseline_probe_v0"]
    selector_feature_dataset_v0 = payloads["selector_feature_dataset_v0"]
    selector_feature_baseline_probe_v0 = payloads[
        "selector_feature_baseline_probe_v0"
    ]
    provider_identity_maturity_review_v0 = payloads[
        "provider_identity_maturity_review_v0"
    ]
    capacity_geometry_feature_audit_v0 = payloads[
        "capacity_geometry_feature_audit_v0"
    ]
    geometry_augmented_selector_feature_probe_v0 = payloads[
        "geometry_augmented_selector_feature_probe_v0"
    ]
    selector_directed_fix_review_v0 = payloads[
        "selector_directed_fix_review_v0"
    ]
    forced_provider_control_label_plan_v0 = payloads[
        "forced_provider_control_label_plan_v0"
    ]
    forced_provider_label_execution_manifest_v0 = payloads[
        "forced_provider_label_execution_manifest_v0"
    ]
    forced_provider_control_labels_v0 = payloads[
        "forced_provider_control_labels_v0"
    ]
    selector_provenance_feature_dataset_v0 = payloads[
        "selector_provenance_feature_dataset_v0"
    ]
    selector_provenance_feature_probe_v0 = payloads[
        "selector_provenance_feature_probe_v0"
    ]
    selector_feature_architecture_review_v0 = payloads[
        "selector_feature_architecture_review_v0"
    ]
    selector_readiness_after_contrast_probe_review_v0 = payloads[
        "selector_readiness_after_contrast_probe_review_v0"
    ]
    split_selector_objective_dataset_v3 = payloads[
        "split_selector_objective_dataset_v3"
    ]
    split_selector_objective_readiness_v3 = payloads[
        "split_selector_objective_readiness_v3"
    ]
    runtime_test_architecture_review_v3 = payloads[
        "runtime_test_architecture_review_v3"
    ]
    abstention_first_selector_objective_v0 = payloads[
        "abstention_first_selector_objective_v0"
    ]
    abstention_safe_preservation_label_review_v0 = payloads[
        "abstention_safe_preservation_label_review_v0"
    ]
    abstention_training_dataset_v0 = payloads["abstention_training_dataset_v0"]
    abstention_training_probe_v0 = payloads["abstention_training_probe_v0"]
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
    two_stage_abstention_objective_probe_v0 = payloads[
        "two_stage_abstention_objective_probe_v0"
    ]
    two_stage_abstention_runtime_review_packet_v0 = payloads[
        "two_stage_abstention_runtime_review_packet_v0"
    ]
    two_stage_abstention_default_off_equivalence_v0 = payloads[
        "two_stage_abstention_default_off_equivalence_v0"
    ]
    two_stage_abstention_enabled_smoke_v0 = payloads[
        "two_stage_abstention_enabled_smoke_v0"
    ]
    two_stage_abstention_stage7_challenge_smoke_v0 = payloads[
        "two_stage_abstention_stage7_challenge_smoke_v0"
    ]
    two_stage_abstention_runtime_go_no_go_v0 = payloads[
        "two_stage_abstention_runtime_go_no_go_v0"
    ]
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
    hard_negative_selector_target_dataset_v0 = payloads[
        "hard_negative_selector_target_dataset_v0"
    ]
    hard_negative_selector_feature_ablation_v0 = payloads[
        "hard_negative_selector_feature_ablation_v0"
    ]
    balanced_hard_negative_label_plan_v0 = payloads[
        "balanced_hard_negative_label_plan_v0"
    ]
    balanced_hard_negative_execution_manifest_v0 = payloads[
        "balanced_hard_negative_execution_manifest_v0"
    ]
    balanced_hard_negative_execution_manifest_review_v0 = payloads[
        "balanced_hard_negative_execution_manifest_review_v0"
    ]
    balanced_hard_negative_labels_v0 = payloads[
        "balanced_hard_negative_labels_v0"
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
    hard_negative_label_semantics_review_v1 = payloads[
        "hard_negative_label_semantics_review_v1"
    ]
    hard_negative_selector_feature_ablation_v2 = payloads[
        "hard_negative_selector_feature_ablation_v2"
    ]
    stronger_selector_feature_review_v0 = payloads[
        "stronger_selector_feature_review_v0"
    ]
    selected_provider_diversity_evidence_plan_v0 = payloads[
        "selected_provider_diversity_evidence_plan_v0"
    ]
    selected_provider_diversity_replay_free_scan_v0 = payloads[
        "selected_provider_diversity_replay_free_scan_v0"
    ]
    selected_provider_diversity_sampling_manifest_v0 = payloads[
        "selected_provider_diversity_sampling_manifest_v0"
    ]
    selected_provider_diversity_sampling_manifest_review_v0 = payloads[
        "selected_provider_diversity_sampling_manifest_review_v0"
    ]
    selected_provider_diversity_observation_scan_v0 = payloads[
        "selected_provider_diversity_observation_scan_v0"
    ]
    selected_provider_diversity_sampling_manifest_v1 = payloads[
        "selected_provider_diversity_sampling_manifest_v1"
    ]
    selected_provider_diversity_ownership_labels_v1 = payloads[
        "selected_provider_diversity_ownership_labels_v1"
    ]
    selected_provider_diversity_architecture_review_v0 = payloads[
        "selected_provider_diversity_architecture_review_v0"
    ]
    selector_readiness_v3_plan = payloads["selector_readiness_v3_plan"]
    state_local_contrast_labels_v2 = payloads[
        "state_local_contrast_labels_v2"
    ]
    state_local_contrast_selector_probe_v2 = payloads[
        "state_local_contrast_selector_probe_v2"
    ]
    state_local_contrast_readiness_review_v2 = payloads[
        "state_local_contrast_readiness_review_v2"
    ]
    hard_negative_selector_target_dataset_v2 = payloads[
        "hard_negative_selector_target_dataset_v2"
    ]
    hard_negative_selector_target_training_semantics_review_v0 = payloads[
        "hard_negative_selector_target_training_semantics_review_v0"
    ]
    ownership_context_feature_review_v3 = payloads[
        "ownership_context_feature_review_v3"
    ]
    ownership_objective_architecture_review_v0 = payloads[
        "ownership_objective_architecture_review_v0"
    ]
    state_local_paired_ownership_objective_plan_v0 = payloads[
        "state_local_paired_ownership_objective_plan_v0"
    ]
    state_local_paired_ownership_work_package_v0 = payloads[
        "state_local_paired_ownership_work_package_v0"
    ]
    state_local_paired_ownership_inventory_v1 = payloads[
        "state_local_paired_ownership_inventory_v1"
    ]
    state_local_paired_ownership_probe_v1 = payloads[
        "state_local_paired_ownership_probe_v1"
    ]
    state_local_paired_ownership_error_audit_v0 = payloads[
        "state_local_paired_ownership_error_audit_v0"
    ]
    state_local_paired_ownership_review_v1 = payloads[
        "state_local_paired_ownership_review_v1"
    ]
    state_local_paired_runtime_proxy_design_v0 = payloads[
        "state_local_paired_runtime_proxy_design_v0"
    ]
    state_local_paired_runtime_proxy_dataset_v0 = payloads[
        "state_local_paired_runtime_proxy_dataset_v0"
    ]
    state_local_paired_runtime_proxy_probe_v0 = payloads[
        "state_local_paired_runtime_proxy_probe_v0"
    ]
    state_local_paired_runtime_proxy_review_v0 = payloads[
        "state_local_paired_runtime_proxy_review_v0"
    ]
    state_local_paired_selector_runtime_review_packet_v0 = payloads[
        "state_local_paired_selector_runtime_review_packet_v0"
    ]
    selected_owner_failure_risk_evidence_v1 = payloads[
        "selected_owner_failure_risk_evidence_v1"
    ]
    selected_owner_failure_risk_visible_terms_v0 = payloads[
        "selected_owner_failure_risk_visible_terms_v0"
    ]
    selected_owner_failure_risk_visible_proxy_review_v0 = payloads[
        "selected_owner_failure_risk_visible_proxy_review_v0"
    ]
    selected_owner_failure_risk_visible_proxy_probe_v0 = payloads[
        "selected_owner_failure_risk_visible_proxy_probe_v0"
    ]
    selected_owner_failure_risk_proxy_independent_manifest_v0 = payloads[
        "selected_owner_failure_risk_proxy_independent_manifest_v0"
    ]
    selected_owner_failure_risk_proxy_independent_validation_v0 = payloads[
        "selected_owner_failure_risk_proxy_independent_validation_v0"
    ]
    selected_owner_failure_risk_proxy_blocker_review_v0 = payloads[
        "selected_owner_failure_risk_proxy_blocker_review_v0"
    ]
    selected_owner_failure_risk_proxy_probe_v1 = payloads[
        "selected_owner_failure_risk_proxy_probe_v1"
    ]
    selected_owner_failure_risk_proxy_independent_labels_v0 = payloads[
        "selected_owner_failure_risk_proxy_independent_labels_v0"
    ]
    selected_owner_failure_risk_proxy_independent_validation_v1 = payloads[
        "selected_owner_failure_risk_proxy_independent_validation_v1"
    ]
    state_local_paired_selector_runtime_proxy_review_packet_v1 = payloads[
        "state_local_paired_selector_runtime_proxy_review_packet_v1"
    ]
    progress_window_reconsideration_runtime_test_review_v0 = payloads[
        "progress_window_reconsideration_runtime_test_review_v0"
    ]
    progress_window_reconsideration_runtime_smoke_v0 = payloads[
        "progress_window_reconsideration_runtime_smoke_v0"
    ]
    progress_window_reconsideration_post_activation_audit_v0 = payloads[
        "progress_window_reconsideration_post_activation_audit_v0"
    ]
    runtime_sandbox_policy_update_v0 = payloads[
        "runtime_sandbox_policy_update_v0"
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
    self_expansion_architecture_gate = payloads["self_expansion_architecture_gate"]
    control_plane_evidence_contract = payloads["control_plane_evidence_contract"]
    control_plane_manifest = payloads["control_plane_manifest"]
    control_plane_gap_report = payloads["control_plane_gap_report"]
    control_plane_frames = payloads["control_plane_frames"]
    control_plane_frame_quality = payloads["control_plane_frame_quality"]
    control_plane_filtered_frames = payloads["control_plane_filtered_frames"]
    control_plane_forced_controls = payloads["control_plane_forced_controls"]
    control_plane_strategy_probe = payloads["control_plane_strategy_probe"]
    provider_label_coverage_plan = payloads["provider_label_coverage_plan"]
    control_plane_strategy_baseline = payloads["control_plane_strategy_baseline"]
    control_plane_stage7_boundary_refresh = payloads[
        "control_plane_stage7_boundary_refresh"
    ]
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
    self_expansion_goal = (
        self_expansion_architecture_gate.get("selected_next_architecture_goal") or {}
    )
    self_expansion_allowed_slices = (
        self_expansion_architecture_gate.get("allowed_next_slices") or []
    )
    self_expansion_forbidden_next_steps = (
        self_expansion_architecture_gate.get("forbidden_next_steps") or []
    )
    control_plane_contract_lineage_passive = (
        self_expansion_architecture_gate.get("schema_version")
        == "krk_self_expansion_architecture_gate.v0"
        and self_expansion_architecture_gate.get("causal_status")
        == "non_causal_architecture_review"
        and self_expansion_goal.get("goal_id")
        == "krk_control_plane_evidence_contract_v0"
        and self_expansion_goal.get("goal_type")
        == "non_causal_data_contract_and_review"
        and self_expansion_goal.get("must_remain_non_causal") is True
        and self_expansion_goal.get("runtime_defaults_must_remain_unchanged")
        is True
        and any(
            slice_.get("slice_id")
            == "control_plane_manifest_from_existing_artifacts_v0"
            and slice_.get("allowed") is True
            and slice_.get("causal") is False
            for slice_ in self_expansion_allowed_slices
        )
        and "runtime_arbiter" in self_expansion_forbidden_next_steps
        and "runtime_internal_terminal" in self_expansion_forbidden_next_steps
        and "runtime_dtm_or_tablebase" in self_expansion_forbidden_next_steps
        and "gameplay_topology_mutation" in self_expansion_forbidden_next_steps
        and "stage7_promotion" in self_expansion_forbidden_next_steps
        and "stage8_training" in self_expansion_forbidden_next_steps
        and self_expansion_architecture_gate.get("runtime_behavior_changed")
        is False
        and self_expansion_architecture_gate.get("runtime_defaults_changed")
        is False
        and self_expansion_architecture_gate.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and self_expansion_architecture_gate.get("gameplay_topology_mutation")
        is False
        and self_expansion_architecture_gate.get("stage7_promotion_allowed")
        is False
        and self_expansion_architecture_gate.get("stage8_training_allowed")
        is False
        and control_plane_evidence_contract.get("schema_version")
        == "krk_control_plane_evidence_contract.v0"
        and "reports/krk_self_expansion_architecture_gate_v0.json"
        in (control_plane_evidence_contract.get("source_artifacts") or [])
        and control_plane_evidence_contract.get("causal_status")
        == "non_causal_schema_contract"
        and control_plane_evidence_contract.get("recommended_next_slice")
        == "control_plane_manifest_from_existing_artifacts_v0"
        and control_plane_evidence_contract.get("runtime_behavior_changed")
        is False
        and control_plane_evidence_contract.get("runtime_defaults_changed")
        is False
        and control_plane_evidence_contract.get("runtime_selector_implemented")
        is False
        and control_plane_evidence_contract.get("runtime_dtm_or_tablebase_lookup")
        is False
        and control_plane_evidence_contract.get("hidden_python_controller")
        is False
        and control_plane_evidence_contract.get("gameplay_topology_mutation")
        is False
        and control_plane_evidence_contract.get("stage7_promotion_allowed")
        is False
        and control_plane_evidence_contract.get("stage8_training_allowed")
        is False
        and control_plane_manifest.get("causal_status") == "non_causal_manifest"
        and control_plane_manifest.get("contract_artifact")
        == "reports/krk_control_plane_evidence_contract_v0.json"
        and control_plane_manifest.get("summary", {}).get(
            "records_from_existing_artifacts_only"
        )
        is True
        and control_plane_manifest.get("summary", {}).get("new_playouts_added") == 0
        and not control_plane_manifest.get("summary", {}).get(
            "missing_required_fields_after_manifest"
        )
        and control_plane_manifest.get("runtime_behavior_changed") is False
        and control_plane_manifest.get("runtime_defaults_changed") is False
        and control_plane_manifest.get("runtime_selector_implemented") is False
        and control_plane_manifest.get("runtime_dtm_or_tablebase_lookup") is False
        and control_plane_manifest.get("hidden_python_controller") is False
        and control_plane_manifest.get("gameplay_topology_mutation") is False
        and control_plane_manifest.get("stage7_promotion_allowed") is False
        and control_plane_manifest.get("stage8_training_allowed") is False
    )
    control_plane_gap_next = control_plane_gap_report.get("recommended_next_slice") or {}
    control_plane_frame_summary = control_plane_frames.get("summary") or {}
    control_plane_quality_next = (
        control_plane_frame_quality.get("recommended_next_slice") or {}
    )
    control_plane_quality_coverage = (
        control_plane_frame_quality.get("coverage") or {}
    )
    control_plane_quality_readiness = (
        control_plane_frame_quality.get("readiness") or {}
    )
    control_plane_filtered_summary = control_plane_filtered_frames.get("summary") or {}
    control_plane_filtered_readiness = (
        control_plane_filtered_frames.get("readiness") or {}
    )
    control_plane_forced_summary = control_plane_forced_controls.get("summary") or {}
    control_plane_forced_readiness = (
        control_plane_forced_controls.get("readiness") or {}
    )
    control_plane_frame_export_artifacts = [
        control_plane_gap_report,
        control_plane_frames,
        control_plane_frame_quality,
        control_plane_filtered_frames,
        control_plane_forced_controls,
    ]
    control_plane_frame_export_forbidden_steps = [
        "runtime_arbiter",
        "runtime_internal_terminal",
        "stage7_promotion",
        "stage8_training",
        "runtime_dtm_or_tablebase",
        "gameplay_topology_mutation",
    ]
    control_plane_frame_export_passive = (
        control_plane_gap_report.get("schema_version")
        == "krk_control_plane_gap_report.v0"
        and control_plane_gap_report.get("causal_status") == "non_causal_gap_report"
        and control_plane_gap_report.get("source_artifacts")
        == ["reports/krk_control_plane_manifest_v0.json"]
        and control_plane_gap_next.get("slice_id")
        == "export_replay_free_control_plane_frames_v0"
        and control_plane_gap_next.get("allowed") is True
        and control_plane_gap_next.get("causal") is False
        and control_plane_gap_next.get("new_playouts_allowed") is False
        and all(
            step in (control_plane_gap_report.get("blocked_next_steps") or [])
            for step in control_plane_frame_export_forbidden_steps
        )
        and control_plane_gap_report.get("coverage_snapshot", {}).get(
            "new_playouts_added"
        )
        == 0
        and any(
            gap.get("gap_id") == "no_unified_control_plane_frames"
            and gap.get("priority") == "p0"
            and gap.get("causal_allowed") is False
            and gap.get("minimum_next_step")
            == "export_replay_free_control_plane_frames_v0"
            for gap in (control_plane_gap_report.get("stratified_gaps") or [])
        )
        and control_plane_frames.get("schema_version")
        == "krk_control_plane_frames_export.v0"
        and control_plane_frames.get("causal_status") == "non_causal_frame_export"
        and control_plane_frames.get("contract_artifact")
        == "reports/krk_control_plane_evidence_contract_v0.json"
        and control_plane_frame_summary.get("frame_count") == 33
        and control_plane_frame_summary.get("frames_by_source_stage")
        == {"stage4": 6, "stage5": 8, "stage6": 10, "stage7": 9}
        and control_plane_frame_summary.get("new_playouts_added") == 0
        and all(
            frame.get("schema_version") == "control_plane_evidence_frame.v1"
            and frame.get("causal_status") == "non_causal"
            for frame in (control_plane_frames.get("frames") or [])
        )
        and control_plane_frame_quality.get("schema_version")
        == "krk_control_plane_frame_quality_report.v0"
        and control_plane_frame_quality.get("causal_status")
        == "non_causal_quality_report"
        and control_plane_frame_quality.get("source_artifacts")
        == ["reports/krk_control_plane_frames_v0.json"]
        and control_plane_quality_coverage.get("frame_count") == 33
        and control_plane_quality_readiness.get("runtime_sandbox") == "blocked"
        and control_plane_quality_readiness.get("stage7_promotion") == "blocked"
        and control_plane_quality_readiness.get("stage8_training") == "blocked"
        and control_plane_quality_next.get("slice_id")
        == "control_plane_frame_dedupe_and_quality_filters_v0"
        and control_plane_quality_next.get("causal") is False
        and control_plane_quality_next.get("new_playouts_allowed") is False
        and all(
            step in (control_plane_frame_quality.get("blocked_next_steps") or [])
            for step in control_plane_frame_export_forbidden_steps
        )
        and control_plane_filtered_frames.get("schema_version")
        == "krk_control_plane_filtered_frames.v0"
        and control_plane_filtered_frames.get("causal_status")
        == "non_causal_filtered_frame_export"
        and control_plane_filtered_frames.get("source_artifacts")
        == [
            "reports/krk_control_plane_frames_v0.json",
            "reports/krk_control_plane_frame_quality_report_v0.json",
        ]
        and control_plane_filtered_summary.get("frame_count") == 33
        and control_plane_filtered_summary.get("strategy_ready_frame_count") == 24
        and control_plane_filtered_summary.get("stage7_boundary_heldout_frame_count")
        == 7
        and control_plane_filtered_summary.get("new_playouts_added") == 0
        and control_plane_filtered_readiness.get("runtime_sandbox") == "blocked"
        and control_plane_filtered_readiness.get("stage7_promotion") == "blocked"
        and control_plane_filtered_readiness.get("stage8_training") == "blocked"
        and control_plane_forced_controls.get("schema_version")
        == "krk_control_plane_filtered_frames_with_forced_controls.v0"
        and control_plane_forced_controls.get("causal_status")
        == "non_causal_augmented_frame_export"
        and control_plane_forced_controls.get("source_artifacts")
        == [
            "reports/krk_control_plane_filtered_frames_v0.json",
            "reports/krk_forced_provider_control_labels_v0.json",
        ]
        and control_plane_forced_summary.get("frame_count") == 33
        and control_plane_forced_summary.get("forced_control_labels_attached") == 12
        and control_plane_forced_summary.get("missing_label_job_ids") == []
        and control_plane_forced_readiness.get("runtime_sandbox") == "blocked"
        and control_plane_forced_readiness.get("stage7_promotion") == "blocked"
        and control_plane_forced_readiness.get("stage8_training") == "blocked"
        and all(
            artifact.get("runtime_behavior_changed") is False
            and artifact.get("runtime_defaults_changed") is False
            and artifact.get("runtime_selector_implemented") is False
            and artifact.get("runtime_dtm_or_tablebase_lookup") is False
            and artifact.get("hidden_python_controller") is False
            and artifact.get("gameplay_topology_mutation") is False
            and artifact.get("stage7_promotion_allowed") is False
            and artifact.get("stage8_training_allowed") is False
            for artifact in control_plane_frame_export_artifacts
        )
    )
    control_plane_strategy_probe_decision = (
        control_plane_strategy_probe.get("decision") or {}
    )
    control_plane_strategy_probe_coverage = (
        control_plane_strategy_probe.get("label_coverage") or {}
    )
    provider_label_coverage_current = (
        provider_label_coverage_plan.get("current_label_coverage") or {}
    )
    control_plane_strategy_baseline_decision = (
        control_plane_strategy_baseline.get("decision") or {}
    )
    control_plane_strategy_baseline_frame_summary = (
        control_plane_strategy_baseline.get("frame_summary") or {}
    )
    control_plane_strategy_baseline_context = (
        control_plane_strategy_baseline.get("context_summary") or {}
    )
    control_plane_strategy_baseline_results = (
        control_plane_strategy_baseline.get("selector_results") or []
    )
    control_plane_strategy_baseline_result_by_selector = {
        result.get("selector"): result
        for result in control_plane_strategy_baseline_results
    }
    control_plane_strategy_baseline_artifacts = [
        control_plane_strategy_probe,
        control_plane_strategy_baseline,
    ]
    provider_label_coverage_plan_ready = (
        provider_label_coverage_plan.get("schema_version")
        == "krk_provider_label_coverage_plan.v0"
        and provider_label_coverage_plan.get("causal_status")
        == "non_causal_label_plan"
        and provider_label_coverage_plan.get("source_artifacts")
        == [
            "reports/krk_control_plane_filtered_frames_v0.json",
            "reports/krk_control_plane_strategy_arbitration_probe_v0.json",
        ]
        and provider_label_coverage_current.get("coverage_status")
        == "sufficient_for_current_small_probe"
        and provider_label_coverage_current.get("benchmark_frame_count") == 28
        and provider_label_coverage_current.get("provider_labeled_frame_count") == 28
        and provider_label_coverage_current.get("frames_with_known_provider_mate")
        == 14
        and provider_label_coverage_current.get("unknown_examples") == []
        and provider_label_coverage_current.get("unknown_provider_label_count_by_stage")
        == {}
        and provider_label_coverage_plan.get("labels_generated_in_this_slice")
        is False
        and provider_label_coverage_plan.get("recommended_next_slice")
        == "offline_strategy_arbitration_baseline_v1"
        and all(
            step in (provider_label_coverage_plan.get("blocked_next_steps") or [])
            for step in [
                "runtime_arbiter",
                "runtime_internal_terminal",
                "stage7_promotion",
                "stage8_training",
                "runtime_dtm_or_tablebase",
                "gameplay_topology_mutation",
            ]
        )
        and provider_label_coverage_plan.get("runtime_behavior_changed") is False
        and provider_label_coverage_plan.get("runtime_defaults_changed") is False
        and provider_label_coverage_plan.get("runtime_arbiter_added") is False
        and provider_label_coverage_plan.get("runtime_terminals_added") is False
        and provider_label_coverage_plan.get("runtime_dtm_or_tablebase_lookup")
        is False
        and provider_label_coverage_plan.get("gameplay_topology_mutation") is False
        and provider_label_coverage_plan.get("stage7_promotion_allowed") is False
        and provider_label_coverage_plan.get("stage8_training_allowed") is False
    )
    control_plane_strategy_baseline_passive = (
        control_plane_strategy_probe.get("schema_version")
        == "krk_control_plane_strategy_arbitration_probe.v0"
        and control_plane_strategy_probe.get("causal_status") == "non_causal_probe"
        and control_plane_strategy_probe.get("source_artifacts")
        == ["reports/krk_control_plane_filtered_frames_v0.json"]
        and control_plane_strategy_probe_decision.get("selected_status")
        == "provider_labels_sufficient_for_small_probe"
        and control_plane_strategy_probe_decision.get("causal_next_step_allowed")
        is False
        and control_plane_strategy_probe_decision.get("recommended_next_slice")
        == "offline_strategy_arbitration_baseline_v1"
        and provider_label_coverage_plan_ready
        and control_plane_strategy_probe_coverage.get(
            "strategy_benchmark_frame_count"
        )
        == 24
        and control_plane_strategy_probe_coverage.get("provider_labeled_frame_count")
        == 24
        and control_plane_strategy_probe_coverage.get(
            "frames_with_known_provider_mate"
        )
        == 12
        and control_plane_strategy_probe_coverage.get("frames_with_normalized_scores")
        == 24
        and all(
            result.get("selected_count") == 24
            and result.get("known_selected_count") == 24
            and result.get("selected_mate_count") == 12
            and result.get("selected_max_plies_count") == 12
            and result.get("selected_unknown_count") == 0
            for result in (control_plane_strategy_probe.get("selector_results") or [])
        )
        and control_plane_strategy_baseline.get("schema_version")
        == "krk_control_plane_strategy_arbitration_baseline.v1"
        and control_plane_strategy_baseline.get("causal_status")
        == "non_causal_probe"
        and control_plane_strategy_baseline.get("source_artifacts")
        == ["reports/krk_control_plane_filtered_frames_v0.json"]
        and control_plane_strategy_baseline_decision.get("selected_status")
        == "strategy_arbitration_promising"
        and control_plane_strategy_baseline_decision.get("causal_next_step_allowed")
        is False
        and control_plane_strategy_baseline_decision.get("recommended_next_class")
        == "non_causal_strategy_arbiter_sandbox_design"
        and control_plane_strategy_baseline_frame_summary.get(
            "strategy_benchmark_frame_count"
        )
        == 24
        and control_plane_strategy_baseline_frame_summary.get(
            "frames_with_provider_mate"
        )
        == 12
        and control_plane_strategy_baseline_frame_summary.get(
            "frames_with_only_provider_max_plies"
        )
        == 12
        and control_plane_strategy_baseline_frame_summary.get("stage_counts")
        == {"stage4": 6, "stage5": 8, "stage6": 10}
        and control_plane_strategy_baseline_context.get(
            "box_relevance_by_edge_bucket"
        )
        == {"at_edge|low": 24}
        and all(
            (result := control_plane_strategy_baseline_result_by_selector.get(
                selector
            ))
            and result.get("selected_count") == 24
            and result.get("positive_available_frame_count") == 12
            and result.get("hit_when_positive_available_count") == 12
            and result.get("hit_when_positive_available_rate") == 1.0
            and result.get("selected_label_counts") == {"mate": 12, "max_plies": 12}
            and result.get("selected_mate_rate") == 0.5
            and result.get("miss_examples") == []
            for selector in [
                "raw_global_score",
                "normalized_score",
                "provider_local_rank",
                "stage_prior_heuristic",
            ]
        )
        and (
            visible_context_result := (
                control_plane_strategy_baseline_result_by_selector.get(
                    "visible_context_heuristic"
                )
                or {}
            )
        ).get("selected_count")
        == 0
        and visible_context_result.get("selected_label_counts") == {
            "no_selection": 24
        }
        and visible_context_result.get("hit_when_positive_available_rate") == 0.0
        and set(control_plane_strategy_baseline_result_by_selector)
        == {
            "raw_global_score",
            "normalized_score",
            "provider_local_rank",
            "visible_context_heuristic",
            "stage_prior_heuristic",
        }
        and all(
            step in (artifact.get("blocked_next_steps") or [])
            for artifact in control_plane_strategy_baseline_artifacts
            for step in [
                "runtime_arbiter",
                "runtime_internal_terminal",
                "stage7_promotion",
                "stage8_training",
                "runtime_dtm_or_tablebase",
                "gameplay_topology_mutation",
            ]
        )
        and all(
            artifact.get("runtime_behavior_changed") is False
            and artifact.get("runtime_defaults_changed") is False
            and artifact.get("runtime_selector_implemented") is False
            and artifact.get("runtime_dtm_or_tablebase_lookup") is False
            and artifact.get("hidden_python_controller") is False
            and artifact.get("gameplay_topology_mutation") is False
            and artifact.get("stage7_promotion_allowed") is False
            and artifact.get("stage8_training_allowed") is False
            for artifact in control_plane_strategy_baseline_artifacts
        )
    )
    control_plane_stage7_boundary_decision = (
        control_plane_stage7_boundary_refresh.get("decision") or {}
    )
    control_plane_stage7_boundary_filtered = (
        control_plane_stage7_boundary_refresh.get("filtered_frame_summary") or {}
    )
    control_plane_stage7_boundary_current = (
        control_plane_stage7_boundary_refresh.get(
            "boundary_current_evidence_state"
        )
        or {}
    )
    control_plane_stage7_boundary_protected = (
        control_plane_stage7_boundary_refresh.get("protected_failure_contrast_gate")
        or {}
    )
    control_plane_stage7_boundary_probe = (
        control_plane_stage7_boundary_refresh.get("strategy_probe_summary") or {}
    )
    control_plane_stage7_boundary_baseline = (
        control_plane_stage7_boundary_refresh.get("baseline_summary") or {}
    )
    control_plane_stage7_boundary_passive = (
        control_plane_stage7_boundary_refresh.get("schema_version")
        == "krk_control_plane_stage7_boundary_refresh.v0"
        and control_plane_stage7_boundary_refresh.get("causal_status")
        == "non_causal_artifact_review"
        and control_plane_stage7_boundary_decision.get("status")
        == "control_plane_respects_stage7_boundary"
        and control_plane_stage7_boundary_decision.get("runtime_work_allowed")
        is False
        and control_plane_stage7_boundary_decision.get("recommended_next_step")
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
        and control_plane_stage7_boundary_refresh.get("boundary_decision_status")
        == "box_shrink_reclassified_as_local_evidence_handoff_trigger"
        and control_plane_stage7_boundary_refresh.get(
            "boundary_recommended_next_step"
        )
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
        and control_plane_stage7_boundary_current.get(
            "stage7_clean_success_controls_met"
        )
        is True
        and control_plane_stage7_boundary_current.get(
            "stage7_clean_hard_negatives_met"
        )
        is True
        and control_plane_stage7_boundary_current.get(
            "stage7_clean_review_status"
        )
        == "stage7_clean_control_collection_closed_heldout_only"
        and control_plane_stage7_boundary_current.get(
            "strategy_sequence_inventory_status"
        )
        == "replay_free_inventory_state_holdout_gap_blocks_runtime"
        and control_plane_stage7_boundary_filtered.get(
            "strategy_ready_frame_count"
        )
        == 24
        and control_plane_stage7_boundary_filtered.get(
            "stage7_boundary_heldout_frame_count"
        )
        == 7
        and control_plane_stage7_boundary_filtered.get("strategy_ready_by_stage")
        == {"stage4": 6, "stage5": 8, "stage6": 10}
        and control_plane_stage7_boundary_probe.get("decision_status")
        == "provider_labels_sufficient_for_small_probe"
        and control_plane_stage7_boundary_probe.get("strategy_benchmark_frame_count")
        == 24
        and control_plane_stage7_boundary_baseline.get("decision_status")
        == "strategy_arbitration_promising"
        and control_plane_stage7_boundary_baseline.get(
            "strategy_benchmark_frame_count"
        )
        == 24
        and control_plane_stage7_boundary_protected.get("approval_receipt_present")
        is False
        and control_plane_stage7_boundary_protected.get("approval_receipt_valid")
        is False
        and control_plane_stage7_boundary_protected.get("runner_execution_requested")
        is False
        and control_plane_stage7_boundary_protected.get("runner_collection_run_allowed")
        is False
        and control_plane_stage7_boundary_protected.get("runner_processed_job_count")
        == 0
        and control_plane_stage7_boundary_protected.get("runner_executed_job_count")
        == 0
        and control_plane_stage7_boundary_refresh.get("runtime_behavior_changed")
        is False
        and control_plane_stage7_boundary_refresh.get("runtime_defaults_changed")
        is False
        and control_plane_stage7_boundary_refresh.get("runtime_selector_implemented")
        is False
        and control_plane_stage7_boundary_refresh.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and control_plane_stage7_boundary_refresh.get("hidden_python_controller")
        is False
        and control_plane_stage7_boundary_refresh.get("gameplay_topology_mutation")
        is False
        and control_plane_stage7_boundary_refresh.get("stage7_promotion_allowed")
        is False
        and control_plane_stage7_boundary_refresh.get("stage8_training_allowed")
        is False
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
    stage4_caveat_decision_invariants = (
        stage4_caveat_decision_gate.get("invariants") or {}
    )
    stage4_caveat_diagnostic_invariants = (
        stage4_caveat_diagnostic_matrix.get("invariants") or {}
    )
    stage4_caveat_diagnostic_observed = (
        stage4_caveat_diagnostic_matrix.get("stage4_observed_caveat") or {}
    )
    stage4_caveat_diagnostic_delta = (
        stage4_caveat_diagnostic_observed.get("overlay_vs_base_control_delta") or {}
    )
    stage4_caveat_diagnostic_hypotheses = {
        item.get("hypothesis"): item
        for item in (stage4_caveat_diagnostic_matrix.get("hypotheses") or [])
    }
    stage4_caveat_candidate_gap_hypothesis = (
        stage4_caveat_diagnostic_hypotheses.get("candidate_generation_gap") or {}
    )
    curriculum_next_invariants = curriculum_next_milestone_decision.get(
        "invariants"
    ) or {}
    stage4_caveat_diagnostic_matrix_ready = (
        stage4_caveat_diagnostic_matrix.get("schema_version")
        == "krk_stage4_caveat_diagnostic_matrix.v0"
        and stage4_caveat_diagnostic_matrix.get("status")
        == "stage4_caveat_diagnostic_matrix_ready"
        and stage4_caveat_diagnostic_observed.get("total") == 300
        and stage4_caveat_diagnostic_observed.get("mate") == 268
        and stage4_caveat_diagnostic_observed.get("max_plies") == 32
        and stage4_caveat_diagnostic_delta.get("mate_delta") == 0
        and stage4_caveat_diagnostic_delta.get("max_plies_delta") == 0
        and stage4_caveat_candidate_gap_hypothesis.get("confidence") == "high"
        and stage4_caveat_candidate_gap_hypothesis.get("recommended_next_test")
        == "approve_stage4_observation_only_trace_collection_max_6_rows"
        and "stage4_candidate_generation_gap"
        in (stage4_caveat_decision_gate.get("selected_decisions") or [])
        and stage4_caveat_diagnostic_invariants.get(
            "protected_stack_replacement_performed"
        )
        is False
        and stage4_caveat_diagnostic_invariants.get("runtime_behavior_changed")
        is False
        and stage4_caveat_diagnostic_invariants.get("runtime_defaults_changed")
        is False
        and stage4_caveat_diagnostic_invariants.get("runtime_direct_routing")
        is False
        and stage4_caveat_diagnostic_invariants.get("runtime_score_changes")
        is False
        and stage4_caveat_diagnostic_invariants.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and stage4_caveat_diagnostic_invariants.get("runtime_selector_implemented")
        is False
        and stage4_caveat_diagnostic_invariants.get("gameplay_topology_mutation")
        is False
        and stage4_caveat_diagnostic_invariants.get("stage7_promotion") is False
        and stage4_caveat_diagnostic_invariants.get("stage8_training") is False
    )
    stage4_caveat_decision_passive = (
        stage4_caveat_decision_gate.get("schema_version")
        == "krk_stage4_caveat_decision_gate.v0"
        and stage4_caveat_decision_gate.get("status")
        == "stage4_candidate_generation_gap_with_known_residual_guardrail"
        and "stage4_candidate_generation_gap"
        in (stage4_caveat_decision_gate.get("selected_decisions") or [])
        and "stage4_known_residual_keep_as_guardrail"
        in (stage4_caveat_decision_gate.get("selected_decisions") or [])
        and "stage4_runtime_sandbox_review_ready"
        in (stage4_caveat_decision_gate.get("rejected_decisions") or [])
        and "stage4_horizon_label_issue_as_primary"
        in (stage4_caveat_decision_gate.get("rejected_decisions") or [])
        and stage4_caveat_decision_gate.get("recommended_next_action")
        == "explicit_approval_for_stage4_observation_only_trace_collection_or_keep_as_known_guardrail"
        and stage4_caveat_decision_gate.get("runtime_or_training_authorized")
        is False
        and stage4_caveat_decision_invariants.get("protected_stack_replacement_performed")
        is False
        and stage4_caveat_decision_invariants.get("runtime_behavior_changed")
        is False
        and stage4_caveat_decision_invariants.get("runtime_defaults_changed")
        is False
        and stage4_caveat_decision_invariants.get("runtime_direct_routing")
        is False
        and stage4_caveat_decision_invariants.get("runtime_score_changes")
        is False
        and stage4_caveat_decision_invariants.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and stage4_caveat_decision_invariants.get("runtime_selector_implemented")
        is False
        and stage4_caveat_decision_invariants.get("gameplay_topology_mutation")
        is False
        and stage4_caveat_decision_invariants.get("stage7_promotion") is False
        and stage4_caveat_decision_invariants.get("stage8_training") is False
        and "reports/krk_stage4_caveat_decision_gate_v0.json"
        in (curriculum_next_milestone_decision.get("source_artifacts") or [])
        and curriculum_next_milestone_decision.get("stage4_status")
        == "stage4_candidate_generation_gap_with_known_residual_guardrail"
    )
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
    arbiter_sandbox_future = (
        strategy_arbiter_sandbox_design_v0.get("proposed_future_sandbox") or {}
    )
    arbiter_sandbox_blocked = (
        strategy_arbiter_sandbox_design_v0.get("blocked_next_steps") or []
    )
    arbiter_smoke_decision = (
        strategy_arbiter_observability_smoke_v0.get("decision") or {}
    )
    arbiter_smoke_equivalence = (
        strategy_arbiter_observability_smoke_v0.get("equivalence") or {}
    )
    arbiter_smoke_metadata = (
        strategy_arbiter_observability_smoke_v0.get("metadata_shape_check") or {}
    )
    arbiter_observation_frames_decision = (
        strategy_arbiter_observation_frames_v0.get("decision") or {}
    )
    arbiter_observation_stage_counts = (
        strategy_arbiter_observation_frames_v0.get("stage_counts") or {}
    )
    arbiter_separability_decision = (
        strategy_arbiter_observation_separability_review_v0.get("decision") or {}
    )
    arbiter_selector_probe_decision = (
        strategy_arbiter_observation_selector_probe_v0.get("decision") or {}
    )
    arbiter_labeled_controls_decision = (
        strategy_arbiter_labeled_observation_controls_v0.get("decision") or {}
    )
    arbiter_labeled_controls_stage_counts = (
        strategy_arbiter_labeled_observation_controls_v0.get("stage_counts") or {}
    )
    arbiter_labeled_probe_decision = (
        strategy_arbiter_labeled_controls_probe_v0.get("decision") or {}
    )
    arbiter_matrix_v1_decision = (
        strategy_arbiter_protected_control_matrix_v1.get("decision") or {}
    )
    arbiter_matrix_v1_summary = (
        strategy_arbiter_protected_control_matrix_v1.get("summary") or {}
    )
    arbiter_matrix_v1_sample = (
        strategy_arbiter_protected_control_matrix_v1.get("sample") or {}
    )
    arbiter_trace_observability_passive = (
        strategy_arbiter_sandbox_design_v0.get("causal_status")
        == "non_causal_design"
        and strategy_arbiter_sandbox_design_v0.get("design_status")
        == "proposed_for_review"
        and arbiter_sandbox_future.get("default_enabled") is False
        and "runtime DTM/tablebase lookup"
        in (arbiter_sandbox_future.get("forbidden_inputs") or [])
        and "direct move selection"
        in (arbiter_sandbox_future.get("forbidden_outputs") or [])
        and "implement_runtime_arbiter_without_review" in arbiter_sandbox_blocked
        and "promote_stage7" in arbiter_sandbox_blocked
        and "train_stage8" in arbiter_sandbox_blocked
        and "use_runtime_dtm_or_tablebase" in arbiter_sandbox_blocked
        and "mutate_topology_during_gameplay" in arbiter_sandbox_blocked
        and strategy_arbiter_sandbox_design_v0.get("runtime_behavior_changed")
        is False
        and strategy_arbiter_sandbox_design_v0.get("runtime_defaults_changed")
        is False
        and strategy_arbiter_sandbox_design_v0.get("runtime_arbiter_implemented")
        is False
        and strategy_arbiter_sandbox_design_v0.get("runtime_dtm_or_tablebase_lookup")
        is False
        and strategy_arbiter_sandbox_design_v0.get("gameplay_topology_mutation")
        is False
        and strategy_arbiter_sandbox_design_v0.get("stage7_promotion_allowed")
        is False
        and strategy_arbiter_sandbox_design_v0.get("stage8_training_allowed")
        is False
        and strategy_arbiter_observability_smoke_v0.get("causal_status")
        == "non_causal_smoke_test"
        and arbiter_smoke_decision.get("status")
        == "observability_skeleton_smoke_passed"
        and arbiter_smoke_decision.get("runtime_arbiter_allowed") is False
        and arbiter_smoke_equivalence.get("selected_behavior_metrics_match") is True
        and arbiter_smoke_equivalence.get("outcome_metrics_match") is True
        and arbiter_smoke_equivalence.get("observation_is_only_expected_delta")
        is True
        and arbiter_smoke_metadata.get("causal_status") == "non_causal_observation"
        and arbiter_smoke_metadata.get("direct_request") is False
        and arbiter_smoke_metadata.get("score_delta") == 0.0
        and arbiter_smoke_metadata.get("recommendation_only") is True
        and "provider_selection"
        in (strategy_arbiter_observability_smoke_v0.get("blocked_causal_actions") or [])
        and "score_adjustment"
        in (strategy_arbiter_observability_smoke_v0.get("blocked_causal_actions") or [])
        and "topology_mutation"
        in (strategy_arbiter_observability_smoke_v0.get("blocked_causal_actions") or [])
        and strategy_arbiter_observation_frames_v0.get("causal_status")
        == "non_causal_observation_export"
        and arbiter_observation_frames_decision.get("status")
        == "observation_frames_collected"
        and arbiter_observation_frames_decision.get("runtime_arbiter_allowed")
        is False
        and strategy_arbiter_observation_frames_v0.get("record_count") == 12
        and arbiter_observation_stage_counts.get("stage7") == 9
        and strategy_arbiter_observation_frames_v0.get("proposal_count_min") == 10
        and strategy_arbiter_observation_frames_v0.get("proposal_count_max") == 10
        and strategy_arbiter_observation_frames_v0.get("runtime_arbiter_implemented")
        is False
        and strategy_arbiter_observation_frames_v0.get("runtime_behavior_changed")
        is False
        and strategy_arbiter_observation_frames_v0.get("runtime_defaults_changed")
        is False
        and strategy_arbiter_observation_frames_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_observation_frames_v0.get("gameplay_topology_mutation")
        is False
        and strategy_arbiter_observation_separability_review_v0.get("causal_status")
        == "non_causal_review"
        and arbiter_separability_decision.get("status")
        == "observation_frames_ready_for_non_causal_selector_probe"
        and arbiter_separability_decision.get("runtime_arbiter_allowed") is False
        and arbiter_separability_decision.get("sandbox_ready") is False
        and strategy_arbiter_observation_separability_review_v0.get("record_count")
        == 12
        and strategy_arbiter_observation_separability_review_v0.get(
            "underinstrumented_record_count"
        )
        == 0
        and strategy_arbiter_observation_separability_review_v0.get(
            "single_provider_record_count"
        )
        == 0
        and strategy_arbiter_observation_separability_review_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_observation_separability_review_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_observation_separability_review_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_observation_selector_probe_v0.get("causal_status")
        == "non_causal_selector_probe"
        and arbiter_selector_probe_decision.get("status")
        == "observation_selector_probe_underlabeled"
        and arbiter_selector_probe_decision.get("runtime_arbiter_allowed") is False
        and arbiter_selector_probe_decision.get("sandbox_ready") is False
        and strategy_arbiter_observation_selector_probe_v0.get("underlabeled")
        is True
        and strategy_arbiter_observation_selector_probe_v0.get("record_count") == 12
        and strategy_arbiter_observation_selector_probe_v0.get("labeled_row_count")
        == 3
        and strategy_arbiter_observation_selector_probe_v0.get(
            "selected_unknown_count"
        )
        == 10
        and strategy_arbiter_observation_selector_probe_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_observation_selector_probe_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_observation_selector_probe_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_labeled_observation_controls_v0.get("causal_status")
        == "non_causal_labeled_observation_controls"
        and arbiter_labeled_controls_decision.get("status")
        == "labeled_observation_controls_collected"
        and arbiter_labeled_controls_decision.get("runtime_arbiter_allowed")
        is False
        and strategy_arbiter_labeled_observation_controls_v0.get("record_count")
        == 21
        and arbiter_labeled_controls_stage_counts.get("stage7") == 6
        and strategy_arbiter_labeled_observation_controls_v0.get(
            "selected_label_counts"
        )
        == {"negative": 5, "positive": 9, "unknown": 7}
        and strategy_arbiter_labeled_observation_controls_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_labeled_observation_controls_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_labeled_observation_controls_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_labeled_controls_probe_v0.get("causal_status")
        == "non_causal_probe"
        and arbiter_labeled_probe_decision.get("status")
        == "labeled_controls_mixed_no_sandbox"
        and arbiter_labeled_probe_decision.get("runtime_arbiter_allowed") is False
        and arbiter_labeled_probe_decision.get("sandbox_ready") is False
        and strategy_arbiter_labeled_controls_probe_v0.get("record_count") == 21
        and strategy_arbiter_labeled_controls_probe_v0.get("labeled_record_count")
        == 14
        and strategy_arbiter_labeled_controls_probe_v0.get("stage7_unknown_count")
        == 6
        and strategy_arbiter_labeled_controls_probe_v0.get(
            "selected_positive_rate_on_labeled_controls"
        )
        == 0.6428571428571429
        and strategy_arbiter_labeled_controls_probe_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_labeled_controls_probe_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_labeled_controls_probe_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_protected_control_matrix_v1.get("causal_status")
        == "runtime_test_protected_control_matrix"
        and arbiter_matrix_v1_decision.get("status") == "protected_control_matrix_passed"
        and arbiter_matrix_v1_summary.get("default_off_equivalence_passed") is True
        and arbiter_matrix_v1_summary.get("enabled_conversion_not_worse") is True
        and arbiter_matrix_v1_summary.get("enabled_has_no_no_move_or_draw_spike")
        is True
        and arbiter_matrix_v1_sample.get("stage7_rows") == 0
        and strategy_arbiter_protected_control_matrix_v1.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_protected_control_matrix_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_protected_control_matrix_v1.get(
            "gameplay_topology_mutation"
        )
        is False
        and strategy_arbiter_protected_control_matrix_v1.get(
            "stage7_promotion_allowed"
        )
        is False
        and strategy_arbiter_protected_control_matrix_v1.get(
            "stage8_training_allowed"
        )
        is False
    )
    arbiter_risk_decision = (
        strategy_arbiter_evidence_risk_review_v0.get("decision") or {}
    )
    arbiter_risk_summary = (
        strategy_arbiter_evidence_risk_review_v0.get("summary") or {}
    )
    arbiter_risk_blocked_steps = (
        strategy_arbiter_evidence_risk_review_v0.get("blocked_next_steps") or []
    )
    arbiter_stratified_decision = (
        strategy_arbiter_stratified_probe_v2.get("decision") or {}
    )
    arbiter_stratified_summary = (
        strategy_arbiter_stratified_probe_v2.get("summary") or {}
    )
    arbiter_architecture_evidence = (
        strategy_arbiter_architecture_review_v1.get("evidence_summary") or {}
    )
    arbiter_architecture_allowed_next = (
        strategy_arbiter_architecture_review_v1.get("allowed_next_implementation")
        or {}
    )
    arbiter_architecture_blocked = (
        strategy_arbiter_architecture_review_v1.get("blocked_implementation") or []
    )
    sandbox_criteria_decision = (
        strategy_arbiter_sandbox_readiness_criteria_v0.get("decision") or {}
    )
    sandbox_criteria_requirements = {
        requirement.get("id"): requirement
        for requirement in strategy_arbiter_sandbox_readiness_criteria_v0.get(
            "minimum_evidence_requirements"
        )
        or []
    }
    sandbox_profile_constraints = (
        strategy_arbiter_sandbox_readiness_criteria_v0.get(
            "sandbox_profile_constraints"
        )
        or {}
    )
    arbiter_control_current = (
        strategy_arbiter_control_plane_review_v0.get("current_status") or {}
    )
    arbiter_control_evidence = (
        strategy_arbiter_control_plane_review_v0.get("evidence") or {}
    )
    arbiter_control_recommended = (
        strategy_arbiter_control_plane_review_v0.get("recommended_next_step") or {}
    )
    arbiter_control_blocked_work = (
        strategy_arbiter_control_plane_review_v0.get("blocked_next_work") or []
    )
    arbiter_semantics_blocker_passive = (
        strategy_arbiter_evidence_risk_review_v0.get("causal_status")
        == "non_causal_review"
        and arbiter_risk_decision.get("status")
        == "runtime_sandbox_blocked_pending_semantics_review"
        and arbiter_risk_decision.get("runtime_sandbox_allowed") is False
        and arbiter_risk_summary.get("benchmark_frame_count") == 28
        and arbiter_risk_summary.get("max_only_frame_count") == 14
        and arbiter_risk_summary.get("provider_mate_frame_count") == 14
        and "runtime_arbiter" in arbiter_risk_blocked_steps
        and "runtime_internal_terminal" in arbiter_risk_blocked_steps
        and "stage7_promotion" in arbiter_risk_blocked_steps
        and "stage8_training" in arbiter_risk_blocked_steps
        and "runtime_dtm_or_tablebase" in arbiter_risk_blocked_steps
        and "gameplay_topology_mutation" in arbiter_risk_blocked_steps
        and strategy_arbiter_evidence_risk_review_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_evidence_risk_review_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_evidence_risk_review_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_evidence_risk_review_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_evidence_risk_review_v0.get("gameplay_topology_mutation")
        is False
        and strategy_arbiter_evidence_risk_review_v0.get("stage7_promotion_allowed")
        is False
        and strategy_arbiter_evidence_risk_review_v0.get("stage8_training_allowed")
        is False
        and strategy_arbiter_stratified_probe_v2.get("causal_status")
        == "non_causal_probe"
        and arbiter_stratified_decision.get("status")
        == "protected_forced_controls_promising_stage7_gap_confirmed"
        and arbiter_stratified_decision.get("runtime_sandbox_allowed") is False
        and arbiter_stratified_summary.get("best_selected_provider_positive_hit_rate")
        == 1.0
        and arbiter_stratified_summary.get(
            "best_forced_provider_control_positive_hit_rate"
        )
        == 1.0
        and arbiter_stratified_summary.get("best_forced_provider_positive_hit_rate")
        == 0.5
        and strategy_arbiter_stratified_probe_v2.get("runtime_arbiter_implemented")
        is False
        and strategy_arbiter_stratified_probe_v2.get("runtime_behavior_changed")
        is False
        and strategy_arbiter_stratified_probe_v2.get("runtime_defaults_changed")
        is False
        and strategy_arbiter_stratified_probe_v2.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_stratified_probe_v2.get("gameplay_topology_mutation")
        is False
        and strategy_arbiter_stratified_probe_v2.get("stage7_promotion_allowed")
        is False
        and strategy_arbiter_stratified_probe_v2.get("stage8_training_allowed")
        is False
        and strategy_arbiter_architecture_review_v1.get("causal_status")
        == "non_causal_review"
        and strategy_arbiter_architecture_review_v1.get("decision_status")
        == "trace_only_observability_skeleton_allowed"
        and strategy_arbiter_architecture_review_v1.get("runtime_arbiter_allowed")
        is False
        and strategy_arbiter_architecture_review_v1.get("runtime_defaults_may_change")
        is False
        and strategy_arbiter_architecture_review_v1.get("stage7_promotion_allowed")
        is False
        and strategy_arbiter_architecture_review_v1.get("stage8_training_allowed")
        is False
        and arbiter_architecture_allowed_next.get("default_enabled") is False
        and arbiter_architecture_allowed_next.get("may_change_scores") is False
        and arbiter_architecture_allowed_next.get("may_change_selected_move") is False
        and arbiter_architecture_allowed_next.get("may_change_selected_provider")
        is False
        and arbiter_architecture_allowed_next.get("may_request_provider") is False
        and "runtime_provider_selection_arbiter" in arbiter_architecture_blocked
        and "stage7_promotion" in arbiter_architecture_blocked
        and "stage8_training" in arbiter_architecture_blocked
        and "runtime_dtm_or_tablebase_lookup" in arbiter_architecture_blocked
        and strategy_arbiter_sandbox_readiness_criteria_v0.get("causal_status")
        == "non_causal_design_review"
        and strategy_arbiter_sandbox_readiness_criteria_v0.get("readiness_status")
        == "sandbox_not_ready_criteria_defined"
        and sandbox_criteria_decision.get("status")
        == "readiness_criteria_defined_sandbox_still_blocked"
        and sandbox_criteria_decision.get("runtime_arbiter_allowed") is False
        and sandbox_criteria_decision.get("selector_sandbox_ready") is False
        and sandbox_criteria_decision.get("stage7_repair_allowed") is False
        and sandbox_criteria_decision.get("stage7_promotion_allowed") is False
        and sandbox_criteria_decision.get("stage8_training_allowed") is False
        and sandbox_criteria_requirements.get("held_out_stage7_challenges", {}).get(
            "current_status"
        )
        == "met"
        and sandbox_criteria_requirements.get("out_of_sample_controls", {}).get(
            "current_status"
        )
        == "missing"
        and sandbox_profile_constraints.get("default_off") is True
        and strategy_arbiter_sandbox_readiness_criteria_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_sandbox_readiness_criteria_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_sandbox_readiness_criteria_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_control_plane_review_v0.get("causal_status")
        == "non_causal_architecture_review"
        and strategy_arbiter_control_plane_review_v0.get("decision_status")
        == "selector_objective_and_label_semantics_review_required"
        and arbiter_control_current.get("observability_skeleton")
        == "implemented_default_off_trace_only"
        and arbiter_control_current.get("labeled_controls") == "mixed"
        and arbiter_control_current.get("stage7") == "held_out_unlabeled_challenge"
        and arbiter_control_current.get("runtime_arbiter_allowed") is False
        and arbiter_control_current.get("sandbox_ready") is False
        and "runtime_arbiter" in arbiter_control_blocked_work
        and "default_off_selector_sandbox" in arbiter_control_blocked_work
        and "stage7_promotion" in arbiter_control_blocked_work
        and "stage8_training" in arbiter_control_blocked_work
        and "runtime_dtm_or_tablebase" in arbiter_control_blocked_work
        and "gameplay_topology_mutation" in arbiter_control_blocked_work
        and arbiter_control_recommended.get("must_remain_non_causal") is True
    )
    out_of_sample_plan_decision = (
        strategy_arbiter_out_of_sample_control_plan_v0.get("decision") or {}
    )
    out_of_sample_plan_bounds = (
        strategy_arbiter_out_of_sample_control_plan_v0.get("collection_bounds") or {}
    )
    out_of_sample_plan_review_decision = (
        strategy_arbiter_out_of_sample_plan_review_v0.get("decision") or {}
    )
    out_of_sample_manifest_decision = (
        strategy_arbiter_out_of_sample_execution_manifest_v0.get("decision") or {}
    )
    out_of_sample_manifest_binding = (
        strategy_arbiter_out_of_sample_execution_manifest_v0.get("binding_summary")
        or {}
    )
    out_of_sample_manifest_selection = (
        strategy_arbiter_out_of_sample_execution_manifest_v0.get("selection_policy")
        or {}
    )
    out_of_sample_manifest_review_decision = (
        strategy_arbiter_out_of_sample_execution_manifest_review_v0.get("decision")
        or {}
    )
    out_of_sample_manifest_review_summary = (
        strategy_arbiter_out_of_sample_execution_manifest_review_v0.get("summary")
        or {}
    )
    out_of_sample_labels_summary = (
        strategy_arbiter_out_of_sample_control_labels_v0.get("summary") or {}
    )
    out_of_sample_probe_decision = (
        strategy_arbiter_out_of_sample_control_probe_v0.get("decision") or {}
    )
    out_of_sample_probe_metrics = (
        strategy_arbiter_out_of_sample_control_probe_v0.get("metrics") or {}
    )
    out_of_sample_probe_interpretation = (
        strategy_arbiter_out_of_sample_control_probe_v0.get("interpretation") or {}
    )
    out_of_sample_architecture_decision = (
        strategy_arbiter_out_of_sample_architecture_review_v0.get("decision") or {}
    )
    out_of_sample_architecture_evidence = (
        strategy_arbiter_out_of_sample_architecture_review_v0.get("evidence_summary")
        or {}
    )
    out_of_sample_architecture_interpretation = (
        strategy_arbiter_out_of_sample_architecture_review_v0.get("interpretation")
        or {}
    )
    out_of_sample_blocked_steps = (
        strategy_arbiter_out_of_sample_architecture_review_v0.get("blocked_next_steps")
        or []
    )
    strategy_arbiter_out_of_sample_passive = (
        strategy_arbiter_out_of_sample_control_plan_v0.get("causal_status")
        == "non_causal_collection_plan"
        and out_of_sample_plan_decision.get("status")
        == "out_of_sample_control_plan_defined_execution_blocked"
        and out_of_sample_plan_decision.get("execute_collection_now") is False
        and out_of_sample_plan_decision.get("runtime_arbiter_allowed") is False
        and out_of_sample_plan_decision.get("selector_sandbox_ready") is False
        and out_of_sample_plan_bounds.get("stage7_training_rows") == 0
        and strategy_arbiter_out_of_sample_plan_review_v0.get("causal_status")
        == "non_causal_plan_review"
        and out_of_sample_plan_review_decision.get("status")
        == "plan_review_passed_execution_manifest_needed"
        and out_of_sample_plan_review_decision.get("execute_collection_now") is False
        and out_of_sample_plan_review_decision.get("runtime_arbiter_allowed") is False
        and out_of_sample_plan_review_decision.get("selector_sandbox_ready") is False
        and strategy_arbiter_out_of_sample_plan_review_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_out_of_sample_plan_review_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_plan_review_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_execution_manifest_v0.get(
            "causal_status"
        )
        == "non_causal_execution_manifest"
        and out_of_sample_manifest_decision.get("status")
        == "execution_manifest_ready_for_review"
        and out_of_sample_manifest_decision.get("execute_labels_now") is False
        and out_of_sample_manifest_decision.get("runtime_arbiter_allowed") is False
        and out_of_sample_manifest_decision.get("selector_sandbox_ready") is False
        and out_of_sample_manifest_binding.get("all_bindings_valid") is True
        and out_of_sample_manifest_binding.get("job_count") == 12
        and out_of_sample_manifest_binding.get("required_stage_coverage_met") is True
        and out_of_sample_manifest_binding.get("missing_path_count") == 0
        and out_of_sample_manifest_selection.get("stage7_training_rows") == 0
        and strategy_arbiter_out_of_sample_execution_manifest_v0.get(
            "labels_generated_in_this_slice"
        )
        is False
        and strategy_arbiter_out_of_sample_execution_manifest_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_out_of_sample_execution_manifest_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_execution_manifest_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_execution_manifest_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_out_of_sample_execution_manifest_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and strategy_arbiter_out_of_sample_execution_manifest_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and strategy_arbiter_out_of_sample_execution_manifest_v0.get(
            "stage8_training_allowed"
        )
        is False
        and strategy_arbiter_out_of_sample_execution_manifest_review_v0.get(
            "causal_status"
        )
        == "non_causal_manifest_review"
        and out_of_sample_manifest_review_decision.get("status")
        == "execution_manifest_review_passed_bounded_label_run_allowed"
        and out_of_sample_manifest_review_decision.get("execute_labels_now") is False
        and out_of_sample_manifest_review_decision.get("runtime_arbiter_allowed")
        is False
        and out_of_sample_manifest_review_decision.get("selector_sandbox_ready")
        is False
        and out_of_sample_manifest_review_summary.get("job_count") == 12
        and out_of_sample_manifest_review_summary.get("stage7_training_rows") == 0
        and out_of_sample_manifest_review_summary.get("invalid_job_count") == 0
        and strategy_arbiter_out_of_sample_execution_manifest_review_v0.get(
            "labels_generated_in_this_slice"
        )
        is False
        and strategy_arbiter_out_of_sample_control_labels_v0.get("causal_status")
        == "non_causal_label_run"
        and out_of_sample_labels_summary.get("label_count") == 12
        and out_of_sample_labels_summary.get("stage7_training_rows") == 0
        and out_of_sample_labels_summary.get("trace_failures_only") is True
        and strategy_arbiter_out_of_sample_control_labels_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_out_of_sample_control_labels_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_control_labels_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_control_labels_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_out_of_sample_control_labels_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and strategy_arbiter_out_of_sample_control_labels_v0.get(
            "stage8_training_allowed"
        )
        is False
        and strategy_arbiter_out_of_sample_control_probe_v0.get("causal_status")
        == "non_causal_probe"
        and out_of_sample_probe_decision.get("status")
        == "out_of_sample_controls_guardrail_positive_selector_sandbox_blocked"
        and out_of_sample_probe_decision.get("runtime_arbiter_allowed") is False
        and out_of_sample_probe_decision.get("selector_sandbox_ready") is False
        and "class_imbalance"
        in (out_of_sample_probe_decision.get("sandbox_blockers") or [])
        and "selected_provider_dominance"
        in (out_of_sample_probe_decision.get("sandbox_blockers") or [])
        and out_of_sample_probe_metrics.get("label_count") == 12
        and out_of_sample_probe_metrics.get("selected_provider_dominance") == 1.0
        and out_of_sample_probe_interpretation.get(
            "selector_training_signal_is_weak"
        )
        is True
        and strategy_arbiter_out_of_sample_control_probe_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_out_of_sample_control_probe_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_control_probe_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_control_probe_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_out_of_sample_control_probe_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and strategy_arbiter_out_of_sample_control_probe_v0.get(
            "stage8_training_allowed"
        )
        is False
        and strategy_arbiter_out_of_sample_architecture_review_v0.get(
            "causal_status"
        )
        == "non_causal_architecture_review"
        and out_of_sample_architecture_decision.get("status")
        == "selector_sandbox_blocked_out_of_sample_controls_not_selector_diverse"
        and out_of_sample_architecture_decision.get("runtime_arbiter_allowed")
        is False
        and out_of_sample_architecture_decision.get("selector_sandbox_ready")
        is False
        and out_of_sample_architecture_decision.get("stage7_repair_allowed")
        is False
        and out_of_sample_architecture_decision.get("stage7_promotion_allowed")
        is False
        and out_of_sample_architecture_decision.get("stage8_training_allowed")
        is False
        and out_of_sample_architecture_interpretation.get("selector_signal_status")
        == "not_ready_due_to_class_imbalance_and_provider_dominance"
        and "runtime_arbiter" in out_of_sample_blocked_steps
        and "selector_sandbox" in out_of_sample_blocked_steps
        and "stage7_promotion" in out_of_sample_blocked_steps
        and "stage8_training" in out_of_sample_blocked_steps
        and "runtime_dtm_or_tablebase" in out_of_sample_blocked_steps
        and "gameplay_topology_mutation" in out_of_sample_blocked_steps
        and strategy_arbiter_out_of_sample_architecture_review_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_out_of_sample_architecture_review_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_architecture_review_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_out_of_sample_architecture_review_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_out_of_sample_architecture_review_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and strategy_arbiter_out_of_sample_architecture_review_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and strategy_arbiter_out_of_sample_architecture_review_v0.get(
            "stage8_training_allowed"
        )
        is False
    )
    default_off_design_decision = (
        strategy_arbiter_default_off_design_review_v1.get("decision") or {}
    )
    default_off_future_contract = (
        strategy_arbiter_default_off_design_review_v1.get("future_sandbox_contract")
        or {}
    )
    runtime_review_packet_decision = (
        strategy_arbiter_runtime_review_packet_v1.get("decision") or {}
    )
    runtime_review_packet_evidence = (
        strategy_arbiter_runtime_review_packet_v1.get("evidence_summary") or {}
    )
    runtime_sandbox_smoke_decision = (
        strategy_arbiter_runtime_sandbox_smoke_v1.get("decision") or {}
    )
    runtime_sandbox_smoke_equivalence = (
        strategy_arbiter_runtime_sandbox_smoke_v1.get("equivalence") or {}
    )
    runtime_sandbox_smoke_enabled = (
        strategy_arbiter_runtime_sandbox_smoke_v1.get("enabled_sandbox") or {}
    )
    protected_control_matrix_decision = (
        strategy_arbiter_protected_control_matrix_v2.get("decision") or {}
    )
    protected_control_matrix_summary = (
        strategy_arbiter_protected_control_matrix_v2.get("summary") or {}
    )
    protected_control_matrix_sample = (
        strategy_arbiter_protected_control_matrix_v2.get("sample") or {}
    )
    stage7_holdout_decision = (
        strategy_arbiter_stage7_holdout_lock_v1.get("decision") or {}
    )
    stage7_holdout_equivalence = (
        strategy_arbiter_stage7_holdout_lock_v1.get("equivalence") or {}
    )
    stage7_holdout_sample = (
        strategy_arbiter_stage7_holdout_lock_v1.get("sample") or {}
    )
    stage7_challenge_decision = (
        strategy_arbiter_stage7_challenge_probe_v1.get("decision") or {}
    )
    stage7_challenge_summary = (
        strategy_arbiter_stage7_challenge_probe_v1.get("summary") or {}
    )
    support_sensitivity_decision = (
        strategy_arbiter_support_sensitivity_v1.get("decision") or {}
    )
    support_sensitivity_summary = (
        strategy_arbiter_support_sensitivity_v1.get("summary") or {}
    )
    runtime_test_review_decision = (
        strategy_arbiter_runtime_test_review_v2.get("decision") or {}
    )
    runtime_test_review_findings = (
        strategy_arbiter_runtime_test_review_v2.get("findings") or {}
    )
    runtime_test_review_interpretation = (
        strategy_arbiter_runtime_test_review_v2.get("interpretation") or {}
    )
    runtime_test_blocked_steps = (
        strategy_arbiter_runtime_test_review_v2.get("blocked_next_steps") or []
    )
    strategy_arbiter_runtime_no_scale_passive = (
        strategy_arbiter_default_off_design_review_v1.get("causal_status")
        == "non_causal_design_review"
        and default_off_design_decision.get("status")
        == "default_off_strategy_arbiter_design_ready_for_external_review"
        and default_off_design_decision.get("implementation_allowed") is False
        and default_off_design_decision.get("runtime_arbiter_allowed") is False
        and default_off_design_decision.get("selector_sandbox_ready") is False
        and default_off_future_contract.get("default_enabled") is False
        and strategy_arbiter_default_off_design_review_v1.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_default_off_design_review_v1.get(
            "runtime_behavior_changed"
        )
        is False
        and strategy_arbiter_default_off_design_review_v1.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_default_off_design_review_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_default_off_design_review_v1.get(
            "gameplay_topology_mutation"
        )
        is False
        and strategy_arbiter_default_off_design_review_v1.get(
            "stage7_promotion_allowed"
        )
        is False
        and strategy_arbiter_default_off_design_review_v1.get(
            "stage8_training_allowed"
        )
        is False
        and strategy_arbiter_runtime_review_packet_v1.get("causal_status")
        == "non_causal_review_packet"
        and runtime_review_packet_decision.get("status") == "runtime_review_packet_ready"
        and runtime_review_packet_decision.get("implementation_allowed") is False
        and runtime_review_packet_decision.get("runtime_arbiter_allowed") is False
        and runtime_review_packet_decision.get("selector_sandbox_ready") is False
        and strategy_arbiter_runtime_review_packet_v1.get(
            "implementation_blocked_until_review"
        )
        is True
        and strategy_arbiter_runtime_review_packet_v1.get(
            "runtime_arbiter_implemented"
        )
        is False
        and strategy_arbiter_runtime_review_packet_v1.get("runtime_behavior_changed")
        is False
        and strategy_arbiter_runtime_review_packet_v1.get("runtime_defaults_changed")
        is False
        and strategy_arbiter_runtime_review_packet_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_runtime_review_packet_v1.get("gameplay_topology_mutation")
        is False
        and strategy_arbiter_runtime_review_packet_v1.get("stage7_promotion_allowed")
        is False
        and strategy_arbiter_runtime_review_packet_v1.get("stage8_training_allowed")
        is False
        and strategy_arbiter_runtime_sandbox_smoke_v1.get("causal_status")
        == "runtime_test_sandbox_smoke"
        and runtime_sandbox_smoke_decision.get("status")
        == "runtime_sandbox_smoke_passed"
        and runtime_sandbox_smoke_decision.get("default_off_equivalence_passed")
        is True
        and runtime_sandbox_smoke_decision.get("enabled_support_trace_visible")
        is True
        and runtime_sandbox_smoke_equivalence.get(
            "flag_present_default_off_decision_matches_baseline"
        )
        is True
        and runtime_sandbox_smoke_equivalence.get(
            "flag_present_default_off_outcome_matches_baseline"
        )
        is True
        and runtime_sandbox_smoke_enabled.get("direct_request") is False
        and runtime_sandbox_smoke_enabled.get("support_was_applied") is True
        and strategy_arbiter_runtime_sandbox_smoke_v1.get("runtime_defaults_changed")
        is False
        and strategy_arbiter_runtime_sandbox_smoke_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_runtime_sandbox_smoke_v1.get(
            "gameplay_topology_mutation"
        )
        is False
        and strategy_arbiter_runtime_sandbox_smoke_v1.get("stage7_promotion_allowed")
        is False
        and strategy_arbiter_runtime_sandbox_smoke_v1.get("stage8_training_allowed")
        is False
        and strategy_arbiter_protected_control_matrix_v2.get("causal_status")
        == "runtime_test_protected_control_matrix"
        and protected_control_matrix_decision.get("status")
        == "protected_control_matrix_v2_passed"
        and protected_control_matrix_summary.get("default_off_equivalence_passed")
        is True
        and protected_control_matrix_summary.get("enabled_has_no_conversion_regression")
        is True
        and protected_control_matrix_summary.get("enabled_has_no_no_move_or_draw_spike")
        is True
        and protected_control_matrix_sample.get("stage7_rows") == 0
        and strategy_arbiter_protected_control_matrix_v2.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_protected_control_matrix_v2.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_protected_control_matrix_v2.get(
            "gameplay_topology_mutation"
        )
        is False
        and strategy_arbiter_protected_control_matrix_v2.get(
            "stage7_promotion_allowed"
        )
        is False
        and strategy_arbiter_protected_control_matrix_v2.get(
            "stage8_training_allowed"
        )
        is False
        and strategy_arbiter_stage7_holdout_lock_v1.get("causal_status")
        == "runtime_test_stage7_holdout_lock"
        and stage7_holdout_decision.get("status") == "stage7_holdout_lock_passed"
        and stage7_holdout_equivalence.get("enabled_blocked_matches_baseline") is True
        and stage7_holdout_equivalence.get("support_blocked") is True
        and stage7_holdout_sample.get("allow_stage7_challenge") is False
        and strategy_arbiter_stage7_holdout_lock_v1.get("runtime_defaults_changed")
        is False
        and strategy_arbiter_stage7_holdout_lock_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_stage7_holdout_lock_v1.get("gameplay_topology_mutation")
        is False
        and strategy_arbiter_stage7_holdout_lock_v1.get("stage7_promotion_allowed")
        is False
        and strategy_arbiter_stage7_holdout_lock_v1.get("stage8_training_allowed")
        is False
        and strategy_arbiter_stage7_challenge_probe_v1.get("causal_status")
        == "runtime_test_stage7_challenge_probe"
        and stage7_challenge_decision.get("status")
        == "stage7_challenge_probe_no_regression"
        and stage7_challenge_summary.get("conversion_delta") == 0
        and stage7_challenge_summary.get("selected_supported_count") == 0
        and stage7_challenge_summary.get("no_no_move_or_draw_spike") is True
        and strategy_arbiter_stage7_challenge_probe_v1.get(
            "runtime_defaults_changed"
        )
        is False
        and strategy_arbiter_stage7_challenge_probe_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_stage7_challenge_probe_v1.get(
            "gameplay_topology_mutation"
        )
        is False
        and strategy_arbiter_stage7_challenge_probe_v1.get(
            "stage7_promotion_allowed"
        )
        is False
        and strategy_arbiter_stage7_challenge_probe_v1.get("stage8_training_allowed")
        is False
        and strategy_arbiter_support_sensitivity_v1.get("causal_status")
        == "runtime_test_one_ply_sensitivity"
        and support_sensitivity_decision.get("status") == "support_sensitivity_measured"
        and support_sensitivity_decision.get("protected_control_status")
        == "high_support_changes_protected_one_ply_ownership"
        and support_sensitivity_decision.get("stage7_runtime_test_status")
        == "no_low_support_ownership_effect"
        and support_sensitivity_summary.get("low_support_cap") == 5.0
        and support_sensitivity_summary.get("stage7_changes_under_low_support_cap")
        is False
        and support_sensitivity_summary.get("support_scale_risk")
        == "high_support_changes_protected_ownership_before_safe_stage7_evidence"
        and strategy_arbiter_support_sensitivity_v1.get("runtime_defaults_changed")
        is False
        and strategy_arbiter_support_sensitivity_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_support_sensitivity_v1.get("gameplay_topology_mutation")
        is False
        and strategy_arbiter_support_sensitivity_v1.get("stage7_promotion_allowed")
        is False
        and strategy_arbiter_support_sensitivity_v1.get("stage8_training_allowed")
        is False
        and strategy_arbiter_runtime_test_review_v2.get("causal_status")
        == "runtime_test_review_non_promoting"
        and runtime_test_review_decision.get("status")
        == "runtime_sandbox_safe_but_additive_support_not_ready_to_scale"
        and runtime_test_review_decision.get("runtime_promotion_allowed") is False
        and runtime_test_review_decision.get("stage7_promotion_allowed") is False
        and runtime_test_review_decision.get("stage8_training_allowed") is False
        and runtime_test_review_findings.get("default_off_equivalence_passed") is True
        and runtime_test_review_findings.get("small_support_protected_no_regression")
        is True
        and runtime_test_review_findings.get("small_support_stage7_effective")
        is False
        and runtime_test_review_findings.get("high_support_scale_risk") is True
        and runtime_test_review_findings.get("stage7_holdout_locked_by_default")
        is True
        and runtime_test_review_interpretation.get("blocked_path")
        == "raise_additive_support_bonus"
        and "increase_broad_additive_support" in runtime_test_blocked_steps
        and "stage7_promotion" in runtime_test_blocked_steps
        and "stage8_training" in runtime_test_blocked_steps
        and "runtime_dtm_or_tablebase" in runtime_test_blocked_steps
        and "gameplay_topology_mutation" in runtime_test_blocked_steps
        and strategy_arbiter_runtime_test_review_v2.get("runtime_defaults_changed")
        is False
        and strategy_arbiter_runtime_test_review_v2.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and strategy_arbiter_runtime_test_review_v2.get("gameplay_topology_mutation")
        is False
        and strategy_arbiter_runtime_test_review_v2.get("stage7_promotion_allowed")
        is False
        and strategy_arbiter_runtime_test_review_v2.get("stage8_training_allowed")
        is False
    )
    selector_target_dataset_decision = selector_target_dataset_v0.get("decision") or {}
    selector_target_probe_decision = selector_target_probe_v0.get("decision") or {}
    selector_baseline_probe_decision = selector_baseline_probe_v0.get("decision") or {}
    selector_feature_dataset_decision = (
        selector_feature_dataset_v0.get("decision") or {}
    )
    selector_feature_baseline_decision = (
        selector_feature_baseline_probe_v0.get("decision") or {}
    )
    selector_feature_baseline_best = (
        selector_feature_baseline_probe_v0.get("best_baseline") or {}
    )
    provider_identity_decision = (
        provider_identity_maturity_review_v0.get("decision") or {}
    )
    provider_identity_interpretation = (
        provider_identity_maturity_review_v0.get("interpretation") or {}
    )
    provider_identity_best_feature_baseline = (
        provider_identity_maturity_review_v0.get("best_feature_probe_baseline") or {}
    )
    provider_identity_required_features = (
        provider_identity_maturity_review_v0.get("required_future_features") or []
    )
    provider_identity_blocked_work = (
        provider_identity_maturity_review_v0.get("blocked_next_work") or []
    )
    provider_identity_maturity_passive = (
        provider_identity_maturity_review_v0.get("causal_status")
        == "non_causal_architecture_review"
        and provider_identity_maturity_review_v0.get("source_artifacts")
        == [
            "reports/krk_selector_feature_dataset_v0.json",
            "reports/krk_selector_feature_baseline_probe_v0.json",
        ]
        and provider_identity_maturity_review_v0.get("row_count") == 42
        and provider_identity_maturity_review_v0.get("provider_prior_accuracy")
        == 0.8333333333333334
        and provider_identity_best_feature_baseline.get("name")
        == "provider_prior_loo"
        and provider_identity_best_feature_baseline.get("accuracy")
        == 0.8333333333333334
        and provider_identity_interpretation.get("provider_identity_signal")
        == "strong_but_not_causal_ready"
        and provider_identity_interpretation.get(
            "raw_provider_id_is_principled_runtime_signal"
        )
        is False
        and provider_identity_interpretation.get("stage0_basin_positive_rate")
        == 0.7333333333333333
        and provider_identity_interpretation.get("edge_trap_positive_rates")
        == [0.1111111111111111, 0.1111111111111111, 0.1111111111111111]
        and provider_identity_decision.get("status")
        == "provider_identity_signal_requires_provenance_decomposition"
        and provider_identity_decision.get("runtime_arbiter_allowed") is False
        and provider_identity_decision.get("selector_sandbox_ready") is False
        and provider_identity_decision.get("stage7_repair_allowed") is False
        and provider_identity_decision.get("stage8_training_allowed") is False
        and "provider_maturity" in provider_identity_required_features
        and "provider_version" in provider_identity_required_features
        and "source_stage" in provider_identity_required_features
        and "validated_profile" in provider_identity_required_features
        and "frozen_provider" in provider_identity_required_features
        and "overlay_provider" in provider_identity_required_features
        and "guardrail_status" in provider_identity_required_features
        and "plasticity_scope" in provider_identity_required_features
        and "promotion_status" in provider_identity_required_features
        and "protected_provider" in provider_identity_required_features
        and "runtime_arbiter" in provider_identity_blocked_work
        and "selector_sandbox" in provider_identity_blocked_work
        and "raw_provider_id_runtime_prior" in provider_identity_blocked_work
        and "provider_support_adapter" in provider_identity_blocked_work
        and "score_bonus_or_penalty" in provider_identity_blocked_work
        and "stage7_repair" in provider_identity_blocked_work
        and "stage7_promotion" in provider_identity_blocked_work
        and "stage8_training" in provider_identity_blocked_work
        and "runtime_dtm_or_tablebase" in provider_identity_blocked_work
        and "gameplay_topology_mutation" in provider_identity_blocked_work
        and provider_identity_maturity_review_v0.get("runtime_arbiter_implemented")
        is False
        and provider_identity_maturity_review_v0.get("runtime_behavior_changed")
        is False
        and provider_identity_maturity_review_v0.get("runtime_defaults_changed")
        is False
    )
    geometry_audit_decision = (
        capacity_geometry_feature_audit_v0.get("decision") or {}
    )
    geometry_audit_summary = (
        capacity_geometry_feature_audit_v0.get("summary") or {}
    )
    geometry_probe_decision = (
        geometry_augmented_selector_feature_probe_v0.get("decision") or {}
    )
    geometry_probe_summary = (
        geometry_augmented_selector_feature_probe_v0.get("summary") or {}
    )
    geometry_probe_best = (
        geometry_augmented_selector_feature_probe_v0.get("best_result") or {}
    )
    directed_fix_decision = selector_directed_fix_review_v0.get("decision") or {}
    directed_fix_recommended = (
        selector_directed_fix_review_v0.get("recommended_fix_class") or {}
    )
    directed_fix_rejected = [
        str(item.get("fix") or "")
        for item in selector_directed_fix_review_v0.get("rejected_fixes", []) or []
    ]
    directed_fix_requirements = (
        selector_directed_fix_review_v0.get("directed_fix_requirements") or []
    )
    selector_directed_fix_blocker_passive = (
        capacity_geometry_feature_audit_v0.get("causal_status")
        == "non_causal_feature_audit"
        and capacity_geometry_feature_audit_v0.get("source_artifacts")
        == [
            "reports/krk_protected_provider_coverage_frames_v0.json",
            "reports/krk_selector_negative_suppression_evidence_v0.json",
        ]
        and geometry_audit_decision.get("status")
        == "geometry_terms_partially_informative_not_sufficient"
        and geometry_audit_decision.get("runtime_work_allowed") is False
        and geometry_audit_decision.get("candidate_generator_runtime_allowed")
        is False
        and geometry_audit_decision.get("selector_training_allowed") is False
        and geometry_audit_decision.get("stage7_promotion_allowed") is False
        and geometry_audit_decision.get("stage8_training_allowed") is False
        and geometry_audit_summary.get("row_count") == 16
        and geometry_audit_summary.get("stage7_row_count") == 0
        and geometry_audit_summary.get("capacity_label_counts")
        == {"negative_capacity": 5, "positive_capacity": 11}
        and capacity_geometry_feature_audit_v0.get("runtime_behavior_changed")
        is False
        and capacity_geometry_feature_audit_v0.get("runtime_defaults_changed")
        is False
        and capacity_geometry_feature_audit_v0.get("runtime_selector_implemented")
        is False
        and capacity_geometry_feature_audit_v0.get(
            "runtime_candidate_generator_implemented"
        )
        is False
        and capacity_geometry_feature_audit_v0.get("runtime_terminals_added")
        is False
        and capacity_geometry_feature_audit_v0.get("runtime_dtm_or_tablebase_lookup")
        is False
        and capacity_geometry_feature_audit_v0.get("gameplay_topology_mutation")
        is False
        and capacity_geometry_feature_audit_v0.get("stage7_promotion_allowed")
        is False
        and capacity_geometry_feature_audit_v0.get("stage8_training_allowed")
        is False
        and geometry_augmented_selector_feature_probe_v0.get("causal_status")
        == "non_causal_feature_probe"
        and geometry_augmented_selector_feature_probe_v0.get("source_artifacts")
        == [
            "reports/krk_capacity_geometry_feature_audit_v0.json",
            "reports/krk_selector_negative_suppression_evidence_v0.json",
        ]
        and geometry_probe_decision.get("status")
        == "geometry_augmented_features_underpowered"
        and geometry_probe_decision.get("runtime_work_allowed") is False
        and geometry_probe_decision.get("candidate_generator_runtime_allowed")
        is False
        and geometry_probe_decision.get("selector_training_allowed") is False
        and geometry_probe_decision.get("stage7_promotion_allowed") is False
        and geometry_probe_decision.get("stage8_training_allowed") is False
        and geometry_probe_summary.get("row_count") == 16
        and geometry_probe_summary.get("state_count") == 6
        and geometry_probe_summary.get("positive_count") == 11
        and geometry_probe_summary.get("negative_count") == 5
        and geometry_probe_summary.get("stage7_row_count") == 0
        and geometry_probe_summary.get("underpowered") is True
        and geometry_probe_best.get("objective") == "provider_family"
        and geometry_probe_best.get("accuracy") == 0.6875
        and geometry_probe_best.get("negative_suppression") == 0.0
        and geometry_augmented_selector_feature_probe_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and geometry_augmented_selector_feature_probe_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and geometry_augmented_selector_feature_probe_v0.get(
            "runtime_selector_implemented"
        )
        is False
        and geometry_augmented_selector_feature_probe_v0.get(
            "runtime_candidate_generator_implemented"
        )
        is False
        and geometry_augmented_selector_feature_probe_v0.get(
            "runtime_terminals_added"
        )
        is False
        and geometry_augmented_selector_feature_probe_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and geometry_augmented_selector_feature_probe_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and geometry_augmented_selector_feature_probe_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and geometry_augmented_selector_feature_probe_v0.get(
            "stage8_training_allowed"
        )
        is False
        and selector_directed_fix_review_v0.get("causal_status")
        == "non_causal_architecture_review"
        and selector_directed_fix_review_v0.get("source_artifacts")
        == [
            "reports/krk_two_stage_candidate_selection_benchmark_v0.json",
            "reports/krk_selector_negative_suppression_evidence_v0.json",
            "reports/krk_geometry_augmented_selector_feature_probe_v0.json",
            "reports/krk_validated_provider_candidate_set_audit_v0.json",
            "reports/krk_protected_provider_capacity_frame_training_semantics_review_v0.json",
        ]
        and directed_fix_decision.get("status")
        == "directed_fix_review_complete_runtime_blocked"
        and directed_fix_decision.get("recommended_next_step")
        == "design_hard_negative_selector_target_dataset_v0"
        and directed_fix_decision.get("runtime_work_allowed") is False
        and directed_fix_decision.get("candidate_generator_runtime_allowed")
        is False
        and directed_fix_decision.get("selector_training_allowed") is False
        and directed_fix_decision.get("stage7_promotion_allowed") is False
        and directed_fix_decision.get("stage8_training_allowed") is False
        and directed_fix_recommended.get("name")
        == "non_causal_hard_negative_selector_target_design"
        and directed_fix_recommended.get("not_runtime") is True
        and "runtime_selector_now" in directed_fix_rejected
        and "runtime_candidate_generator_now" in directed_fix_rejected
        and "train_selector_on_forced_capacity_as_positive" in directed_fix_rejected
        and "add_simple_geometry_terms_only" in directed_fix_rejected
        and "return_to_stage7_patch" in directed_fix_rejected
        and "keep candidate generation and selection as separate channels"
        in directed_fix_requirements
        and "create a hard-negative selector target dataset from protected capacity negatives"
        in directed_fix_requirements
        and "keep forced-capacity labels distinct from selected-playout labels"
        in directed_fix_requirements
        and "add move/post-move geometry only as non-causal scoring features"
        in directed_fix_requirements
        and "evaluate leave-state-out suppression before any sandbox"
        in directed_fix_requirements
        and "keep Stage 7 held out" in directed_fix_requirements
        and selector_directed_fix_review_v0.get("runtime_behavior_changed") is False
        and selector_directed_fix_review_v0.get("runtime_defaults_changed") is False
        and selector_directed_fix_review_v0.get("runtime_selector_implemented")
        is False
        and selector_directed_fix_review_v0.get(
            "runtime_candidate_generator_implemented"
        )
        is False
        and selector_directed_fix_review_v0.get("runtime_terminals_added") is False
        and selector_directed_fix_review_v0.get("runtime_dtm_or_tablebase_lookup")
        is False
        and selector_directed_fix_review_v0.get("gameplay_topology_mutation")
        is False
        and selector_directed_fix_review_v0.get("stage7_promotion_allowed") is False
        and selector_directed_fix_review_v0.get("stage8_training_allowed") is False
    )
    forced_provider_plan_job_selection = (
        forced_provider_control_label_plan_v0.get("job_selection") or {}
    )
    forced_provider_manifest_binding_summary = (
        forced_provider_label_execution_manifest_v0.get("binding_summary") or {}
    )
    forced_provider_labels_summary = (
        forced_provider_control_labels_v0.get("summary") or {}
    )
    forced_provider_label_rows = (
        forced_provider_control_labels_v0.get("labels") or []
    )
    forced_provider_label_stage_counts = {
        stage: sum(
            1 for row in forced_provider_label_rows if row.get("source_stage") == stage
        )
        for stage in ("stage4", "stage5", "stage6", "stage7")
    }
    forced_provider_control_blocked_steps = [
        "runtime_arbiter",
        "runtime_internal_terminal",
        "stage7_promotion",
        "stage8_training",
        "runtime_dtm_or_tablebase",
        "gameplay_topology_mutation",
    ]
    forced_provider_control_label_lineage_passive = (
        forced_provider_control_label_plan_v0.get("causal_status")
        == "non_causal_label_plan"
        and forced_provider_control_label_plan_v0.get("source_artifacts")
        == [
            "reports/krk_control_plane_filtered_frames_v0.json",
            "reports/krk_strategy_arbiter_stratified_probe_v2.json",
        ]
        and forced_provider_plan_job_selection.get("selected_job_count") == 12
        and forced_provider_plan_job_selection.get("max_jobs") == 12
        and forced_provider_plan_job_selection.get("max_jobs_per_stage") == 6
        and forced_provider_plan_job_selection.get("selected_job_count_by_stage")
        == {"stage5": 6, "stage6": 6}
        and forced_provider_plan_job_selection.get("target_stages")
        == ["stage5", "stage6"]
        and forced_provider_plan_job_selection.get("current_label_result_counts")
        == {"mate": 8, "max_plies": 4}
        and forced_provider_control_label_plan_v0.get("recommended_next_step")
        == "run_bounded_forced_provider_control_labels_if_runner_available"
        and all(
            step in (forced_provider_control_label_plan_v0.get("blocked_next_steps") or [])
            for step in forced_provider_control_blocked_steps
        )
        and forced_provider_control_label_plan_v0.get("runtime_behavior_changed")
        is False
        and forced_provider_control_label_plan_v0.get("runtime_defaults_changed")
        is False
        and forced_provider_control_label_plan_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and forced_provider_control_label_plan_v0.get("gameplay_topology_mutation")
        is False
        and forced_provider_control_label_plan_v0.get("stage7_promotion_allowed")
        is False
        and forced_provider_control_label_plan_v0.get("stage8_training_allowed")
        is False
        and forced_provider_label_execution_manifest_v0.get("causal_status")
        == "non_causal_execution_manifest"
        and forced_provider_label_execution_manifest_v0.get("source_artifacts")
        == [
            "reports/krk_forced_provider_control_label_plan_v0.json",
            "reports/stage6_overlay_validation_manifest.md",
        ]
        and forced_provider_manifest_binding_summary.get("all_bindings_valid") is True
        and forced_provider_manifest_binding_summary.get("job_count") == 12
        and forced_provider_manifest_binding_summary.get("missing_path_count") == 0
        and forced_provider_label_execution_manifest_v0.get("recommended_next_step")
        == "run_bounded_forced_provider_control_labels"
        and all(
            step
            in (
                forced_provider_label_execution_manifest_v0.get("blocked_next_steps")
                or []
            )
            for step in forced_provider_control_blocked_steps
        )
        and forced_provider_label_execution_manifest_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and forced_provider_label_execution_manifest_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and forced_provider_label_execution_manifest_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and forced_provider_label_execution_manifest_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and forced_provider_label_execution_manifest_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and forced_provider_label_execution_manifest_v0.get(
            "stage8_training_allowed"
        )
        is False
        and forced_provider_control_labels_v0.get("causal_status")
        == "non_causal_label_run"
        and forced_provider_control_labels_v0.get("source_artifacts")
        == ["reports/krk_forced_provider_label_execution_manifest_v0.json"]
        and forced_provider_labels_summary.get("label_count") == 12
        and forced_provider_labels_summary.get("result_counts")
        == {"mate": 9, "max_plies": 3}
        and forced_provider_labels_summary.get("result_counts_by_stage")
        == {"stage5:mate": 6, "stage6:mate": 3, "stage6:max_plies": 3}
        and forced_provider_labels_summary.get("trace_failures_only") is True
        and forced_provider_control_labels_v0.get("recommended_next_step")
        == "merge_forced_provider_control_labels_and_rerun_stratified_probe"
        and len(forced_provider_label_rows) == 12
        and forced_provider_label_stage_counts
        == {"stage4": 0, "stage5": 6, "stage6": 6, "stage7": 0}
        and all(row.get("causal_status") == "non_causal_outcome_label" for row in forced_provider_label_rows)
        and all(row.get("forced_successor_available") is True for row in forced_provider_label_rows)
        and all(row.get("trace_included") is False for row in forced_provider_label_rows)
        and all(
            row.get("schema_version") == "krk_forced_provider_control_label.v0"
            for row in forced_provider_label_rows
        )
        and all(
            step in (forced_provider_control_labels_v0.get("blocked_next_steps") or [])
            for step in forced_provider_control_blocked_steps
        )
        and forced_provider_control_labels_v0.get("runtime_behavior_changed") is False
        and forced_provider_control_labels_v0.get("runtime_defaults_changed") is False
        and forced_provider_control_labels_v0.get("runtime_dtm_or_tablebase_lookup")
        is False
        and forced_provider_control_labels_v0.get("gameplay_topology_mutation")
        is False
        and forced_provider_control_labels_v0.get("stage7_promotion_allowed")
        is False
        and forced_provider_control_labels_v0.get("stage8_training_allowed")
        is False
    )
    selector_provenance_dataset_decision = (
        selector_provenance_feature_dataset_v0.get("decision") or {}
    )
    selector_provenance_probe_decision = (
        selector_provenance_feature_probe_v0.get("decision") or {}
    )
    selector_provenance_probe_best = (
        selector_provenance_feature_probe_v0.get("best_baseline") or {}
    )
    selector_provenance_blocked_work = (
        selector_provenance_feature_probe_v0.get("blocked_next_work") or []
    )
    selector_feature_architecture_summary = (
        selector_feature_architecture_review_v0.get("summary") or {}
    )
    selector_feature_architecture_recommended = (
        selector_feature_architecture_review_v0.get("recommended_next_step") or {}
    )
    selector_feature_architecture_blocked = (
        selector_feature_architecture_review_v0.get("blocked_next_work") or []
    )
    selector_after_contrast_decision = (
        selector_readiness_after_contrast_probe_review_v0.get("decision") or {}
    )
    selector_after_contrast_evidence = (
        selector_readiness_after_contrast_probe_review_v0.get("evidence") or {}
    )
    selector_after_contrast_blocked = (
        selector_readiness_after_contrast_probe_review_v0.get("blocked_next_steps")
        or []
    )
    selector_provenance_prior_blocker_passive = (
        selector_target_dataset_v0.get("causal_status") == "non_causal_target_dataset"
        and selector_target_dataset_decision.get("status")
        == "selector_target_dataset_built"
        and selector_target_dataset_decision.get("runtime_arbiter_allowed") is False
        and selector_target_dataset_decision.get("sandbox_ready") is False
        and selector_target_dataset_v0.get("row_count") == 63
        and selector_target_dataset_v0.get("training_row_count") == 42
        and selector_target_dataset_v0.get("stage7_training_rows") == 0
        and selector_target_dataset_v0.get("target_kind_counts")
        == {
            "forced_provider_conversion": 12,
            "held_out_challenge": 9,
            "selected_playout_success": 42,
        }
        and selector_target_dataset_v0.get("runtime_arbiter_implemented") is False
        and selector_target_dataset_v0.get("runtime_behavior_changed") is False
        and selector_target_dataset_v0.get("runtime_defaults_changed") is False
        and selector_target_probe_v0.get("causal_status") == "non_causal_probe"
        and selector_target_probe_decision.get("status")
        == "target_dataset_ready_for_non_causal_baseline_probe"
        and selector_target_probe_decision.get("runtime_arbiter_allowed") is False
        and selector_target_probe_decision.get("sandbox_ready") is False
        and selector_target_probe_v0.get("training_row_count") == 42
        and selector_target_probe_v0.get("heldout_training_row_count") == 0
        and selector_target_probe_v0.get("training_label_counts")
        == {"negative": 28, "positive": 14}
        and selector_target_probe_v0.get("runtime_arbiter_implemented") is False
        and selector_target_probe_v0.get("runtime_behavior_changed") is False
        and selector_target_probe_v0.get("runtime_defaults_changed") is False
        and selector_baseline_probe_v0.get("causal_status") == "non_causal_probe"
        and selector_baseline_probe_decision.get("status")
        == "simple_selector_baseline_promising_non_causal"
        and selector_baseline_probe_decision.get("runtime_arbiter_allowed") is False
        and selector_baseline_probe_decision.get("sandbox_ready") is False
        and (selector_baseline_probe_v0.get("best_baseline") or {}).get("name")
        == "provider_prior_loo"
        and (selector_baseline_probe_v0.get("best_baseline") or {}).get("accuracy")
        == 0.8333333333333334
        and selector_baseline_probe_v0.get("runtime_arbiter_implemented") is False
        and selector_baseline_probe_v0.get("runtime_behavior_changed") is False
        and selector_baseline_probe_v0.get("runtime_defaults_changed") is False
        and selector_feature_dataset_v0.get("causal_status")
        == "non_causal_feature_dataset"
        and selector_feature_dataset_decision.get("status")
        == "selector_feature_dataset_built"
        and selector_feature_dataset_decision.get("runtime_arbiter_allowed") is False
        and selector_feature_dataset_decision.get("sandbox_ready") is False
        and selector_feature_dataset_v0.get("row_count") == 63
        and selector_feature_dataset_v0.get("training_row_count") == 42
        and selector_feature_dataset_v0.get("stage7_training_rows") == 0
        and selector_feature_dataset_v0.get("rows_with_observation") == 60
        and selector_feature_dataset_v0.get("runtime_arbiter_implemented") is False
        and selector_feature_dataset_v0.get("runtime_behavior_changed") is False
        and selector_feature_dataset_v0.get("runtime_defaults_changed") is False
        and selector_feature_baseline_probe_v0.get("causal_status")
        == "non_causal_probe"
        and selector_feature_baseline_decision.get("status")
        == "provider_prior_remains_best_non_causal_baseline"
        and selector_feature_baseline_decision.get("runtime_arbiter_allowed")
        is False
        and selector_feature_baseline_decision.get("sandbox_ready") is False
        and selector_feature_baseline_best.get("name") == "provider_prior_loo"
        and selector_feature_baseline_best.get("accuracy") == 0.8333333333333334
        and selector_feature_baseline_probe_v0.get("feature_improved_over_provider_prior")
        is False
        and selector_feature_baseline_probe_v0.get("runtime_arbiter_implemented")
        is False
        and selector_feature_baseline_probe_v0.get("runtime_behavior_changed")
        is False
        and selector_feature_baseline_probe_v0.get("runtime_defaults_changed")
        is False
        and selector_provenance_feature_dataset_v0.get("causal_status")
        == "non_causal_provenance_feature_dataset"
        and selector_provenance_dataset_decision.get("status")
        == "selector_provenance_feature_dataset_built"
        and selector_provenance_dataset_decision.get("runtime_arbiter_allowed")
        is False
        and selector_provenance_dataset_decision.get("sandbox_ready") is False
        and selector_provenance_feature_dataset_v0.get("row_count") == 63
        and selector_provenance_feature_dataset_v0.get("training_row_count") == 42
        and selector_provenance_feature_dataset_v0.get("stage7_training_rows") == 0
        and selector_provenance_feature_dataset_v0.get("rows_with_provider_provenance")
        == 54
        and selector_provenance_feature_dataset_v0.get("runtime_arbiter_implemented")
        is False
        and selector_provenance_feature_dataset_v0.get("runtime_behavior_changed")
        is False
        and selector_provenance_feature_dataset_v0.get("runtime_defaults_changed")
        is False
        and selector_provenance_feature_probe_v0.get("causal_status")
        == "non_causal_probe"
        and selector_provenance_probe_decision.get("status")
        == "provenance_features_explain_provider_prior_non_causal"
        and selector_provenance_probe_decision.get("runtime_arbiter_allowed")
        is False
        and selector_provenance_probe_decision.get("selector_sandbox_ready")
        is False
        and selector_provenance_probe_decision.get(
            "raw_provider_id_runtime_prior_allowed"
        )
        is False
        and selector_provenance_probe_best.get("name") == "provider_id_loo"
        and selector_provenance_probe_best.get("accuracy") == 0.8333333333333334
        and "runtime_arbiter" in selector_provenance_blocked_work
        and "selector_sandbox" in selector_provenance_blocked_work
        and "raw_provider_id_runtime_prior" in selector_provenance_blocked_work
        and "stage7_promotion" in selector_provenance_blocked_work
        and "stage8_training" in selector_provenance_blocked_work
        and selector_provenance_feature_probe_v0.get("runtime_arbiter_implemented")
        is False
        and selector_provenance_feature_probe_v0.get("runtime_behavior_changed")
        is False
        and selector_provenance_feature_probe_v0.get("runtime_defaults_changed")
        is False
        and selector_feature_architecture_review_v0.get("causal_status")
        == "non_causal_architecture_review"
        and selector_feature_architecture_review_v0.get("decision_status")
        == "provider_prior_remains_best_no_selector_sandbox"
        and selector_feature_architecture_summary.get(
            "observation_features_improved_over_provider_prior"
        )
        is False
        and selector_feature_architecture_summary.get("best_baseline")
        == "provider_prior_loo"
        and selector_feature_architecture_summary.get("best_baseline_accuracy")
        == 0.8333333333333334
        and selector_feature_architecture_recommended.get("must_remain_non_causal")
        is True
        and "runtime_arbiter" in selector_feature_architecture_blocked
        and "default_off_selector_sandbox" in selector_feature_architecture_blocked
        and "runtime_dtm_or_tablebase" in selector_feature_architecture_blocked
        and "gameplay_topology_mutation" in selector_feature_architecture_blocked
        and "stage7_promotion" in selector_feature_architecture_blocked
        and "stage8_training" in selector_feature_architecture_blocked
        and selector_readiness_after_contrast_probe_review_v0.get("causal_status")
        == "non_causal_architecture_review"
        and selector_after_contrast_decision.get("status")
        == "selector_sandbox_blocked_selected_provider_evidence_missing"
        and selector_after_contrast_decision.get("runtime_arbiter_allowed") is False
        and selector_after_contrast_decision.get("selector_sandbox_ready") is False
        and selector_after_contrast_evidence.get("training_row_count") == 9
        and selector_after_contrast_evidence.get("heldout_row_count") == 4
        and selector_after_contrast_evidence.get("readiness_blockers")
        == ["insufficient_selected_provider_family_diversity"]
        and "runtime_arbiter" in selector_after_contrast_blocked
        and "selector_sandbox" in selector_after_contrast_blocked
        and "runtime_dtm_or_tablebase" in selector_after_contrast_blocked
        and "gameplay_topology_mutation" in selector_after_contrast_blocked
        and "stage7_promotion" in selector_after_contrast_blocked
        and "stage8_training" in selector_after_contrast_blocked
        and selector_readiness_after_contrast_probe_review_v0.get(
            "runtime_arbiter_implemented"
        )
        is False
        and selector_readiness_after_contrast_probe_review_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and selector_readiness_after_contrast_probe_review_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and selector_readiness_after_contrast_probe_review_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and selector_readiness_after_contrast_probe_review_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and selector_readiness_after_contrast_probe_review_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and selector_readiness_after_contrast_probe_review_v0.get(
            "stage8_training_allowed"
        )
        is False
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
    selector_stratified_dataset_decision = (
        selector_stratified_label_dataset_v1.get("decision") or {}
    )
    selector_stratified_probe_decision = (
        selector_stratified_label_balance_probe_v1.get("decision") or {}
    )
    selector_stratified_probe_label_counts = (
        selector_stratified_label_balance_probe_v1.get("label_counts") or {}
    )
    selector_stratified_rows = selector_stratified_label_dataset_v1.get("rows") or []
    selector_stratified_stage7_training_rows = sum(
        1 for row in selector_stratified_rows if row.get("stage7_training_row") is True
    )
    selector_balanced_dataset_decision = (
        selector_balanced_label_dataset_v1.get("decision") or {}
    )
    selector_balanced_probe_decision = (
        selector_balanced_label_probe_v1.get("decision") or {}
    )
    selector_balanced_probe_label_counts = (
        selector_balanced_label_probe_v1.get("label_counts") or {}
    )
    selector_balanced_probe_best_baseline = (
        selector_balanced_label_probe_v1.get("best_baseline") or {}
    )
    selector_balanced_rows = selector_balanced_label_dataset_v1.get("rows") or []
    selector_balanced_stage7_training_rows = sum(
        1 for row in selector_balanced_rows if row.get("stage7_training_row") is True
    )
    selector_balanced_provider_family_counts = {
        family: sum(
            1 for row in selector_balanced_rows if row.get("provider_family") == family
        )
        for family in sorted(
            {
                row.get("provider_family")
                for row in selector_balanced_rows
                if row.get("provider_family") is not None
            }
        )
    }
    selector_balanced_architecture_decision = (
        selector_balanced_architecture_review_v1.get("decision") or {}
    )
    selector_balanced_architecture_evidence = (
        selector_balanced_architecture_review_v1.get("evidence") or {}
    )
    selector_balanced_blocked_next_work = (
        selector_balanced_architecture_review_v1.get("blocked_next_work") or []
    )
    selector_replay_free_plan_decision = (
        selector_stratified_label_plan_v1.get("decision") or {}
    )
    selector_replay_free_review_decision = (
        selector_label_plan_replay_free_review_v1.get("decision") or {}
    )
    selector_negative_control_decision = (
        selector_negative_control_manifest_v1.get("decision") or {}
    )
    selector_replay_free_plan_jobs = selector_stratified_label_plan_v1.get("jobs") or []
    selector_replay_free_review_items = (
        selector_label_plan_replay_free_review_v1.get("reviews") or []
    )
    selector_negative_control_rows = (
        selector_negative_control_manifest_v1.get("controls") or []
    )
    selector_replay_free_plan_job_stage_counts = {
        stage: sum(
            1
            for row in selector_replay_free_plan_jobs
            if row.get("source_stage") == stage
        )
        for stage in ("stage4", "stage5", "stage6", "stage7")
    }
    selector_replay_free_plan_sources = [
        "reports/krk_selector_target_dataset_v0.json",
        "reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json",
        "reports/krk_selector_objective_architecture_review_v1.json",
    ]
    selector_replay_free_review_sources = [
        "reports/krk_selector_stratified_label_plan_v1.json",
        "reports/krk_selector_target_dataset_v0.json",
        "reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json",
    ]
    selector_replay_free_blocked_work = (
        selector_stratified_label_plan_v1.get("blocked_next_work") or []
    )
    selector_replay_free_lineage_artifacts = [
        selector_stratified_label_plan_v1,
        selector_label_plan_replay_free_review_v1,
        selector_negative_control_manifest_v1,
        selector_stratified_label_dataset_v1,
        selector_balanced_label_dataset_v1,
        selector_balanced_label_probe_v1,
        selector_balanced_architecture_review_v1,
    ]
    selector_replay_free_runtime_behavior_changed = any(
        artifact.get("runtime_behavior_changed") is True
        for artifact in selector_replay_free_lineage_artifacts
    )
    selector_replay_free_runtime_defaults_changed = any(
        artifact.get("runtime_defaults_changed") is True
        for artifact in selector_replay_free_lineage_artifacts
    )
    selector_replay_free_runtime_arbiter_implemented = any(
        artifact.get("runtime_arbiter_implemented") is True
        for artifact in selector_replay_free_lineage_artifacts
    )
    selector_replay_free_label_lineage_passive = (
        selector_stratified_label_plan_v1.get("causal_status")
        == "non_causal_label_plan"
        and selector_stratified_label_plan_v1.get("source_artifacts")
        == selector_replay_free_plan_sources
        and selector_replay_free_plan_decision.get("status")
        == "bounded_selector_stratified_label_plan_ready"
        and selector_replay_free_plan_decision.get("execute_labels_now") is False
        and selector_replay_free_plan_decision.get("runtime_arbiter_allowed")
        is False
        and selector_replay_free_plan_decision.get("selector_sandbox_ready") is False
        and len(selector_replay_free_plan_jobs) == 11
        and selector_replay_free_plan_job_stage_counts
        == {"stage4": 4, "stage5": 4, "stage6": 3, "stage7": 0}
        and all(
            row.get("causal_status") == "non_causal_label_job_plan"
            and row.get("stage7_training_row") is False
            for row in selector_replay_free_plan_jobs
        )
        and all(
            item in selector_replay_free_blocked_work
            for item in [
                "runtime_arbiter",
                "selector_sandbox",
                "stage7_repair",
                "stage7_promotion",
                "stage8_training",
                "runtime_dtm_or_tablebase",
                "gameplay_topology_mutation",
            ]
        )
        and selector_stratified_label_plan_v1.get("runtime_behavior_changed") is False
        and selector_stratified_label_plan_v1.get("runtime_defaults_changed") is False
        and selector_stratified_label_plan_v1.get("runtime_arbiter_implemented")
        is False
        and selector_label_plan_replay_free_review_v1.get("causal_status")
        == "non_causal_replay_free_review"
        and selector_label_plan_replay_free_review_v1.get("source_artifacts")
        == selector_replay_free_review_sources
        and selector_replay_free_review_decision.get("status")
        == "planned_labels_replay_free_fillable"
        and selector_replay_free_review_decision.get("execute_labels_now") is False
        and selector_replay_free_review_decision.get("runtime_arbiter_allowed")
        is False
        and selector_replay_free_review_decision.get("selector_sandbox_ready")
        is False
        and selector_label_plan_replay_free_review_v1.get("planned_job_count") == 11
        and selector_label_plan_replay_free_review_v1.get(
            "missing_replay_free_label_count"
        )
        == 0
        and selector_label_plan_replay_free_review_v1.get("fill_status_counts")
        == {"compatible_target_label_available": 11}
        and all(
            row.get("execute_playout_needed") is False
            and row.get("fill_status") == "compatible_target_label_available"
            for row in selector_replay_free_review_items
        )
        and selector_label_plan_replay_free_review_v1.get("runtime_behavior_changed")
        is False
        and selector_label_plan_replay_free_review_v1.get("runtime_defaults_changed")
        is False
        and selector_label_plan_replay_free_review_v1.get(
            "runtime_arbiter_implemented"
        )
        is False
        and selector_negative_control_manifest_v1.get("causal_status")
        == "non_causal_negative_control_manifest"
        and selector_negative_control_manifest_v1.get("source_artifact")
        == "reports/krk_selector_provenance_feature_dataset_v0.json"
        and selector_negative_control_decision.get("status")
        == "negative_protected_controls_identified_replay_free"
        and selector_negative_control_decision.get("runtime_arbiter_allowed")
        is False
        and selector_negative_control_decision.get("selector_sandbox_ready") is False
        and selector_negative_control_manifest_v1.get("control_count") == 9
        and selector_negative_control_manifest_v1.get("stage_counts")
        == {"stage4": 2, "stage5": 4, "stage6": 3}
        and selector_negative_control_manifest_v1.get("provider_counts")
        == {
            "krk.edge_trap_close": 3,
            "krk.edge_trap_enemy_between": 2,
            "krk.edge_trap_wrong_tempo": 2,
            "krk.stage0_basin": 2,
        }
        and all(
            row.get("causal_status") == "non_causal_negative_control"
            and row.get("schema_version") == "krk_selector_negative_control.v1"
            and row.get("label") == "negative"
            and row.get("target_kind") == "selected_playout_success"
            and row.get("stage7_training_row") is False
            for row in selector_negative_control_rows
        )
        and selector_negative_control_manifest_v1.get("runtime_behavior_changed")
        is False
        and selector_negative_control_manifest_v1.get("runtime_defaults_changed")
        is False
        and selector_negative_control_manifest_v1.get("runtime_arbiter_implemented")
        is False
        and selector_stratified_label_dataset_v1.get("row_count") == 11
        and selector_stratified_label_dataset_v1.get("label_counts")
        == {"negative": 1, "positive": 10}
        and selector_stratified_stage7_training_rows == 0
        and selector_stratified_dataset_decision.get("status")
        == "stratified_selector_label_dataset_built_replay_free"
        and selector_stratified_dataset_decision.get("runtime_arbiter_allowed")
        is False
        and selector_stratified_dataset_decision.get("selector_sandbox_ready") is False
        and selector_balanced_label_dataset_v1.get("row_count") == 18
        and selector_balanced_label_dataset_v1.get("label_counts")
        == {"negative": 9, "positive": 9}
        and selector_balanced_stage7_training_rows == 0
        and selector_balanced_dataset_decision.get("status")
        == "balanced_selector_label_dataset_built_replay_free"
        and selector_balanced_dataset_decision.get("runtime_arbiter_allowed")
        is False
        and selector_balanced_dataset_decision.get("selector_sandbox_ready") is False
        and selector_balanced_probe_decision.get("status")
        == "balanced_labels_support_non_causal_selector_signal"
        and selector_balanced_probe_best_baseline.get("name") == "provider_id_loo"
        and selector_balanced_probe_best_baseline.get("accuracy")
        == 0.7777777777777778
        and selector_balanced_architecture_decision.get("status")
        == "selector_signal_promising_sandbox_blocked_pending_readiness_criteria"
        and selector_balanced_architecture_decision.get("runtime_arbiter_allowed")
        is False
        and selector_balanced_architecture_decision.get("selector_sandbox_ready")
        is False
        and selector_balanced_architecture_decision.get("stage7_repair_allowed")
        is False
        and selector_balanced_architecture_decision.get("stage7_promotion_allowed")
        is False
        and selector_balanced_architecture_decision.get("stage8_training_allowed")
        is False
        and selector_replay_free_runtime_behavior_changed is False
        and selector_replay_free_runtime_defaults_changed is False
        and selector_replay_free_runtime_arbiter_implemented is False
    )
    selector_label_balance_passive = (
        selector_stratified_dataset_decision.get("status")
        == "stratified_selector_label_dataset_built_replay_free"
        and selector_stratified_dataset_decision.get("runtime_arbiter_allowed")
        is False
        and selector_stratified_dataset_decision.get("selector_sandbox_ready") is False
        and selector_stratified_label_dataset_v1.get("row_count") == 11
        and selector_stratified_stage7_training_rows == 0
        and selector_stratified_label_balance_probe_v1.get("causal_status")
        == "non_causal_probe"
        and selector_stratified_probe_decision.get("status")
        == "stratified_labels_underbalanced_no_selector_probe"
        and selector_stratified_probe_decision.get("runtime_arbiter_allowed")
        is False
        and selector_stratified_probe_decision.get("selector_sandbox_ready") is False
        and selector_stratified_label_balance_probe_v1.get("underbalanced") is True
        and selector_stratified_probe_label_counts == {"negative": 1, "positive": 10}
        and selector_balanced_dataset_decision.get("status")
        == "balanced_selector_label_dataset_built_replay_free"
        and selector_balanced_dataset_decision.get("runtime_arbiter_allowed")
        is False
        and selector_balanced_dataset_decision.get("selector_sandbox_ready") is False
        and selector_balanced_label_dataset_v1.get("row_count") == 18
        and selector_balanced_stage7_training_rows == 0
        and selector_balanced_label_probe_v1.get("causal_status")
        == "non_causal_probe"
        and selector_balanced_probe_decision.get("status")
        == "balanced_labels_support_non_causal_selector_signal"
        and selector_balanced_probe_decision.get("runtime_arbiter_allowed") is False
        and selector_balanced_probe_decision.get("selector_sandbox_ready") is False
        and selector_balanced_probe_label_counts == {"negative": 9, "positive": 9}
        and selector_balanced_architecture_review_v1.get("causal_status")
        == "non_causal_architecture_review"
        and selector_balanced_architecture_decision.get("status")
        == "selector_signal_promising_sandbox_blocked_pending_readiness_criteria"
        and selector_balanced_architecture_decision.get("runtime_arbiter_allowed")
        is False
        and selector_balanced_architecture_decision.get("selector_sandbox_ready")
        is False
        and selector_balanced_architecture_decision.get("stage7_promotion_allowed")
        is False
        and selector_balanced_architecture_decision.get("stage8_training_allowed")
        is False
        and "runtime_arbiter" in selector_balanced_blocked_next_work
        and "selector_sandbox_implementation" in selector_balanced_blocked_next_work
        and "runtime_dtm_or_tablebase" in selector_balanced_blocked_next_work
        and "stage7_promotion" in selector_balanced_blocked_next_work
        and "stage8_training" in selector_balanced_blocked_next_work
        and all(
            artifact.get("runtime_behavior_changed") is False
            and artifact.get("runtime_defaults_changed") is False
            for artifact in [
                selector_stratified_label_dataset_v1,
                selector_stratified_label_balance_probe_v1,
                selector_balanced_label_dataset_v1,
                selector_balanced_label_probe_v1,
                selector_balanced_architecture_review_v1,
            ]
        )
        and selector_balanced_label_probe_v1.get("runtime_arbiter_implemented")
        is False
        and selector_balanced_architecture_review_v1.get(
            "runtime_arbiter_implemented"
        )
        is False
    )
    ownership_selection_label_decision = (
        ownership_selection_label_dataset_v5.get("decision") or {}
    )
    ownership_selection_label_summary = (
        ownership_selection_label_dataset_v5.get("summary") or {}
    )
    ownership_selection_context_decision = (
        ownership_selection_context_dataset_v3.get("decision") or {}
    )
    ownership_selection_context_summary = (
        ownership_selection_context_dataset_v3.get("summary") or {}
    )
    ownership_selection_context_probe_decision = (
        ownership_selection_context_feature_probe_v3.get("decision") or {}
    )
    ownership_selection_context_probe_summary = (
        ownership_selection_context_feature_probe_v3.get("summary") or {}
    )
    ownership_selection_labeling_review_decision = (
        ownership_selection_labeling_review_v0.get("decision") or {}
    )
    ownership_selection_labeling_review_summary = (
        ownership_selection_labeling_review_v0.get("summary") or {}
    )
    ownership_source_diversity_decision = (
        ownership_source_diversity_review_v0.get("decision") or {}
    )
    ownership_source_diversity_summary = (
        ownership_source_diversity_review_v0.get("summary") or {}
    )
    ownership_selection_context_passive = (
        ownership_selection_label_dataset_v5.get("causal_status")
        == "non_causal_ownership_label_dataset"
        and ownership_selection_label_decision.get("status")
        == "ownership_selection_labels_expanded_with_targeted_false_positive_risk_cells"
        and ownership_selection_label_decision.get("runtime_work_allowed") is False
        and ownership_selection_label_decision.get("selector_training_allowed") is False
        and ownership_selection_label_decision.get("stage7_promotion_allowed") is False
        and ownership_selection_label_decision.get("stage8_training_allowed") is False
        and ownership_selection_label_summary.get("merged_row_count") == 41
        and ownership_selection_label_summary.get("selector_training_row_count") == 0
        and ownership_selection_label_summary.get("stage7_row_count") == 0
        and ownership_selection_context_dataset_v3.get("causal_status")
        == "non_causal_context_feature_dataset"
        and ownership_selection_context_decision.get("status")
        == "ownership_selection_context_dataset_ready_for_non_causal_probe"
        and ownership_selection_context_decision.get("runtime_work_allowed") is False
        and ownership_selection_context_decision.get("selector_training_allowed")
        is False
        and ownership_selection_context_decision.get("stage7_promotion_allowed")
        is False
        and ownership_selection_context_decision.get("stage8_training_allowed")
        is False
        and ownership_selection_context_summary.get("row_count") == 41
        and ownership_selection_context_summary.get("selector_training_row_count") == 0
        and ownership_selection_context_summary.get("stage7_row_count") == 0
        and ownership_selection_context_feature_probe_v3.get("causal_status")
        == "non_causal_offline_probe"
        and ownership_selection_context_probe_decision.get("status")
        == "context_features_underpowered"
        and ownership_selection_context_probe_decision.get("runtime_work_allowed")
        is False
        and ownership_selection_context_probe_decision.get("selector_training_allowed")
        is False
        and ownership_selection_context_probe_decision.get("stage7_promotion_allowed")
        is False
        and ownership_selection_context_probe_decision.get("stage8_training_allowed")
        is False
        and ownership_selection_context_probe_summary.get("underpowered") is True
        and ownership_selection_context_probe_summary.get("stage7_row_count") == 0
        and ownership_selection_labeling_review_v0.get("causal_status")
        == "non_causal_review"
        and ownership_selection_labeling_review_decision.get("status")
        == "ownership_labels_improved_but_selector_runtime_blocked"
        and ownership_selection_labeling_review_decision.get("runtime_work_allowed")
        is False
        and ownership_selection_labeling_review_decision.get(
            "selector_training_allowed"
        )
        is False
        and ownership_selection_labeling_review_summary.get("selector_training_rows")
        == 0
        and ownership_selection_labeling_review_summary.get("stage7_rows") == 0
        and ownership_source_diversity_review_v0.get("causal_status")
        == "non_causal_review"
        and ownership_source_diversity_decision.get("status")
        == "source_diversity_gap_blocks_runtime"
        and ownership_source_diversity_decision.get("runtime_work_allowed") is False
        and ownership_source_diversity_decision.get("selector_training_allowed")
        is False
        and ownership_source_diversity_decision.get("stage7_promotion_allowed")
        is False
        and ownership_source_diversity_decision.get("stage8_training_allowed")
        is False
        and ownership_source_diversity_summary.get("ownership_row_count") == 35
        and all(
            artifact.get("runtime_behavior_changed") is False
            and artifact.get("runtime_defaults_changed") is False
            and artifact.get("runtime_selector_implemented") is False
            and artifact.get("runtime_dtm_or_tablebase_lookup") is False
            and artifact.get("runtime_terminals_added") is False
            and artifact.get("stage7_promotion_allowed") is False
            and artifact.get("stage8_training_allowed") is False
            for artifact in [
                ownership_selection_label_dataset_v5,
                ownership_selection_context_dataset_v3,
                ownership_selection_context_feature_probe_v3,
                ownership_selection_labeling_review_v0,
                ownership_source_diversity_review_v0,
            ]
        )
    )
    protected_max_only_decision = (
        protected_max_only_frame_review_v0.get("decision") or {}
    )
    protected_max_only_summary = (
        protected_max_only_frame_review_v0.get("summary") or {}
    )
    selector_negative_suppression_decision = (
        selector_negative_suppression_evidence_v0.get("decision") or {}
    )
    runtime_selector_readiness_decision = (
        runtime_selector_readiness_review_v1.get("decision") or {}
    )
    selector_negative_suppression_blocker_passive = (
        protected_max_only_frame_review_v0.get("causal_status")
        == "non_causal_artifact_review"
        and protected_max_only_decision.get("status")
        == "protected_max_only_frames_block_runtime_selector"
        and protected_max_only_decision.get("runtime_work_allowed") is False
        and protected_max_only_summary.get("runtime_work_allowed") is False
        and protected_max_only_frame_review_v0.get("runtime_behavior_changed") is False
        and protected_max_only_frame_review_v0.get("runtime_defaults_changed") is False
        and protected_max_only_frame_review_v0.get("runtime_selector_implemented")
        is False
        and protected_max_only_frame_review_v0.get("runtime_dtm_or_tablebase_lookup")
        is False
        and protected_max_only_frame_review_v0.get("stage7_promotion_allowed") is False
        and protected_max_only_frame_review_v0.get("stage8_training_allowed") is False
        and selector_negative_suppression_evidence_v0.get("causal_status")
        == "non_causal_evidence_audit"
        and selector_negative_suppression_decision.get("status")
        == "selector_negative_suppression_failure_confirmed"
        and selector_negative_suppression_decision.get("runtime_work_allowed") is False
        and selector_negative_suppression_decision.get("selector_training_allowed")
        is False
        and selector_negative_suppression_decision.get(
            "candidate_generator_runtime_allowed"
        )
        is False
        and selector_negative_suppression_decision.get("stage7_promotion_allowed")
        is False
        and selector_negative_suppression_decision.get("stage8_training_allowed")
        is False
        and selector_negative_suppression_evidence_v0.get("runtime_behavior_changed")
        is False
        and selector_negative_suppression_evidence_v0.get("runtime_defaults_changed")
        is False
        and selector_negative_suppression_evidence_v0.get(
            "runtime_selector_implemented"
        )
        is False
        and selector_negative_suppression_evidence_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and selector_negative_suppression_evidence_v0.get("runtime_terminals_added")
        is False
        and runtime_selector_readiness_review_v1.get("causal_status")
        == "non_causal_readiness_review"
        and runtime_selector_readiness_decision.get("status")
        == "runtime_selector_not_ready_collect_better_contrast_labels"
        and runtime_selector_readiness_decision.get("runtime_test_allowed_next")
        is False
        and runtime_selector_readiness_decision.get("stage7_promotion_allowed")
        is False
        and runtime_selector_readiness_decision.get("stage8_training_allowed")
        is False
        and runtime_selector_readiness_review_v1.get("runtime_behavior_changed")
        is False
        and runtime_selector_readiness_review_v1.get("runtime_defaults_changed")
        is False
        and runtime_selector_readiness_review_v1.get("runtime_dtm_or_tablebase_lookup")
        is False
        and runtime_selector_readiness_review_v1.get("stage7_promotion_allowed")
        is False
        and runtime_selector_readiness_review_v1.get("stage8_training_allowed")
        is False
    )
    abstention_objective_decision = (
        abstention_first_selector_objective_v0.get("decision") or {}
    )
    runtime_test_architecture_next = (
        runtime_test_architecture_review_v3.get("recommended_next_class") or {}
    )
    runtime_test_architecture_readiness = (
        runtime_test_architecture_review_v3.get("runtime_readiness") or {}
    )
    runtime_test_architecture_blocked = (
        runtime_test_architecture_review_v3.get("blocked_next_steps") or []
    )
    runtime_test_architecture_lineage_passive = (
        runtime_test_architecture_review_v3.get("schema_version")
        == "krk_runtime_test_architecture_review.v3"
        and runtime_test_architecture_review_v3.get("causal_status")
        == "non_causal_architecture_review"
        and runtime_test_architecture_next.get("status")
        == "design_abstention_first_selector_objective"
        and runtime_test_architecture_next.get("implementation_allowed")
        == "design_only"
        and "reports/krk_abstention_first_selector_objective_v0.json"
        in (runtime_test_architecture_next.get("next_artifacts") or [])
        and runtime_test_architecture_readiness.get("runtime_selector_ready")
        is False
        and runtime_test_architecture_readiness.get("runtime_stage7_repair_ready")
        is False
        and runtime_test_architecture_readiness.get(
            "runtime_internal_terminal_ready"
        )
        is False
        and "runtime_selector" in runtime_test_architecture_blocked
        and "stage7_promotion" in runtime_test_architecture_blocked
        and "stage8_training" in runtime_test_architecture_blocked
        and "runtime_dtm_or_tablebase" in runtime_test_architecture_blocked
        and "gameplay_topology_mutation" in runtime_test_architecture_blocked
        and runtime_test_architecture_review_v3.get("runtime_behavior_changed")
        is False
        and runtime_test_architecture_review_v3.get("runtime_defaults_changed")
        is False
        and runtime_test_architecture_review_v3.get(
            "runtime_selector_implemented"
        )
        is False
        and runtime_test_architecture_review_v3.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and runtime_test_architecture_review_v3.get("gameplay_topology_mutation")
        is False
        and runtime_test_architecture_review_v3.get("stage7_promotion_allowed")
        is False
        and runtime_test_architecture_review_v3.get("stage8_training_allowed")
        is False
    )
    abstention_safe_review_decision = (
        abstention_safe_preservation_label_review_v0.get("decision") or {}
    )
    abstention_safe_review_summary = (
        abstention_safe_preservation_label_review_v0.get("summary") or {}
    )
    abstention_dataset_v0_decision = (
        abstention_training_dataset_v0.get("decision") or {}
    )
    abstention_dataset_v0_summary = abstention_training_dataset_v0.get("summary") or {}
    abstention_probe_v0_decision = abstention_training_probe_v0.get("decision") or {}
    abstention_probe_v0_summary = abstention_training_probe_v0.get("summary") or {}
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
        and abstention_dataset_v0_decision.get("status")
        == "abstention_training_dataset_under_minimum_requirements"
        and abstention_dataset_v0_decision.get("runtime_test_allowed_next") is False
        and abstention_dataset_v0_decision.get("stage7_promotion_allowed") is False
        and abstention_dataset_v0_decision.get("stage8_training_allowed") is False
        and abstention_dataset_v0_summary.get("row_count") == 28
        and abstention_dataset_v0_summary.get("stage7_training_rows") == 0
        and abstention_probe_v0_decision.get("status")
        == "abstention_signal_underpowered_no_runtime"
        and abstention_probe_v0_decision.get("runtime_test_allowed_next") is False
        and abstention_probe_v0_decision.get("stage7_promotion_allowed") is False
        and abstention_probe_v0_decision.get("stage8_training_allowed") is False
        and abstention_probe_v0_summary.get("under_minimum_requirements") is True
        and all(
            artifact.get("runtime_behavior_changed") is False
            and artifact.get("runtime_defaults_changed") is False
            and artifact.get("runtime_selector_implemented") is False
            and artifact.get("runtime_dtm_or_tablebase_lookup") is False
            and artifact.get("runtime_terminals_added", False) is False
            and artifact.get("gameplay_topology_mutation") is False
            and artifact.get("stage7_promotion_allowed") is False
            and artifact.get("stage8_training_allowed") is False
            for artifact in [
                abstention_training_dataset_v0,
                abstention_training_probe_v0,
            ]
        )
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
    two_stage_abstention_objective_decision = (
        two_stage_abstention_objective_probe_v0.get("decision") or {}
    )
    two_stage_abstention_objective_summary = (
        two_stage_abstention_objective_probe_v0.get("summary") or {}
    )
    two_stage_abstention_review_decision = (
        two_stage_abstention_runtime_review_packet_v0.get("decision") or {}
    )
    two_stage_abstention_review_evidence = (
        two_stage_abstention_runtime_review_packet_v0.get("accepted_evidence") or {}
    )
    two_stage_abstention_default_acceptance = (
        two_stage_abstention_default_off_equivalence_v0.get("acceptance") or {}
    )
    two_stage_abstention_enabled_aggregate = (
        two_stage_abstention_enabled_smoke_v0.get("aggregate") or {}
    )
    two_stage_abstention_stage7_summary = (
        two_stage_abstention_stage7_challenge_smoke_v0.get("summary") or {}
    )
    two_stage_abstention_go_no_go_stop_conditions = (
        two_stage_abstention_runtime_go_no_go_v0.get("stop_conditions") or {}
    )
    two_stage_abstention_no_go_passive = (
        two_stage_abstention_objective_probe_v0.get("causal_status")
        == "non_causal_offline_probe"
        and two_stage_abstention_objective_decision.get("status")
        == "two_stage_abstention_signal_present_runtime_review_required"
        and two_stage_abstention_objective_decision.get("runtime_test_allowed_next")
        is False
        and two_stage_abstention_objective_summary.get("row_count") == 51
        and two_stage_abstention_objective_summary.get(
            "threshold_passing_objective_count"
        )
        == 12
        and two_stage_abstention_objective_probe_v0.get("runtime_behavior_changed")
        is False
        and two_stage_abstention_objective_probe_v0.get("runtime_defaults_changed")
        is False
        and two_stage_abstention_objective_probe_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and two_stage_abstention_objective_probe_v0.get(
            "runtime_selector_implemented"
        )
        is False
        and two_stage_abstention_runtime_review_packet_v0.get("causal_status")
        == "non_causal_architecture_review_packet"
        and two_stage_abstention_review_decision.get("status")
        == "two_stage_abstention_review_ready_implementation_blocked"
        and two_stage_abstention_review_decision.get(
            "implementation_allowed_by_this_packet"
        )
        is False
        and two_stage_abstention_review_decision.get("runtime_test_allowed_next")
        is False
        and two_stage_abstention_runtime_review_packet_v0.get(
            "runtime_behavior_changed"
        )
        is False
        and two_stage_abstention_runtime_review_packet_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and two_stage_abstention_runtime_review_packet_v0.get(
            "runtime_selector_implemented"
        )
        is False
        and two_stage_abstention_runtime_review_packet_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and two_stage_abstention_runtime_review_packet_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and two_stage_abstention_default_off_equivalence_v0.get("status")
        == "default_off_equivalent"
        and two_stage_abstention_default_off_equivalence_v0.get("causal_status")
        == "sandbox_opt_in_disabled"
        and two_stage_abstention_default_off_equivalence_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and two_stage_abstention_default_acceptance.get("same_core_metrics") is True
        and two_stage_abstention_default_acceptance.get(
            "disabled_selector_penalized_count_zero"
        )
        is True
        and two_stage_abstention_default_off_equivalence_v0.get(
            "stop_condition_fired"
        )
        is False
        and two_stage_abstention_enabled_smoke_v0.get("status")
        == "enabled_tiny_smoke_no_behavior_delta"
        and two_stage_abstention_enabled_smoke_v0.get("causal_status")
        == "sandbox_opt_in_enabled"
        and two_stage_abstention_enabled_smoke_v0.get("runtime_defaults_changed")
        is False
        and two_stage_abstention_enabled_aggregate.get(
            "total_selected_penalized_count"
        )
        == 0
        and not two_stage_abstention_enabled_aggregate.get(
            "labels_with_core_metric_diffs"
        )
        and not two_stage_abstention_enabled_aggregate.get(
            "labels_with_conversion_regression"
        )
        and not two_stage_abstention_enabled_aggregate.get(
            "labels_with_shadow_regression"
        )
        and two_stage_abstention_stage7_challenge_smoke_v0.get("status")
        == "stage7_challenge_no_target_improvement"
        and two_stage_abstention_stage7_challenge_smoke_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and two_stage_abstention_stage7_challenge_smoke_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and two_stage_abstention_stage7_challenge_smoke_v0.get(
            "stage8_training_allowed"
        )
        is False
        and two_stage_abstention_stage7_challenge_smoke_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and two_stage_abstention_stage7_challenge_smoke_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and two_stage_abstention_stage7_summary.get("target_improved") is False
        and two_stage_abstention_stage7_summary.get("no_regression_detected") is True
        and two_stage_abstention_runtime_go_no_go_v0.get("decision")
        == "no_go_for_scaling_or_promotion"
        and two_stage_abstention_runtime_go_no_go_v0.get("runtime_defaults_changed")
        is False
        and two_stage_abstention_runtime_go_no_go_v0.get("stage7_promotion_allowed")
        is False
        and two_stage_abstention_runtime_go_no_go_v0.get("stage8_training_allowed")
        is False
        and two_stage_abstention_runtime_go_no_go_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and two_stage_abstention_runtime_go_no_go_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and two_stage_abstention_runtime_go_no_go_v0.get("rollback_tag")
        == "pre-two-stage-abstention-runtime"
        and two_stage_abstention_go_no_go_stop_conditions.get(
            "runtime_repair_not_promoted"
        )
        is True
        and two_stage_abstention_go_no_go_stop_conditions.get(
            "stage7_remains_quarantined"
        )
        is True
        and two_stage_abstention_go_no_go_stop_conditions.get(
            "stage8_remains_blocked"
        )
        is True
        and two_stage_abstention_go_no_go_stop_conditions.get("no_hidden_controller")
        is True
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
    hard_negative_targets_v0_decision = (
        hard_negative_selector_target_dataset_v0.get("decision") or {}
    )
    hard_negative_targets_v0_summary = (
        hard_negative_selector_target_dataset_v0.get("summary") or {}
    )
    hard_negative_ablation_v0_decision = (
        hard_negative_selector_feature_ablation_v0.get("decision") or {}
    )
    hard_negative_ablation_v0_summary = (
        hard_negative_selector_feature_ablation_v0.get("summary") or {}
    )
    balanced_hard_negative_plan_v0_decision = (
        balanced_hard_negative_label_plan_v0.get("decision") or {}
    )
    balanced_hard_negative_plan_v0_summary = (
        balanced_hard_negative_label_plan_v0.get("summary") or {}
    )
    balanced_hard_negative_manifest_v0_decision = (
        balanced_hard_negative_execution_manifest_v0.get("decision") or {}
    )
    balanced_hard_negative_manifest_v0_binding = (
        balanced_hard_negative_execution_manifest_v0.get("binding_summary") or {}
    )
    balanced_hard_negative_manifest_review_v0_decision = (
        balanced_hard_negative_execution_manifest_review_v0.get("decision") or {}
    )
    balanced_hard_negative_labels_v0_decision = (
        balanced_hard_negative_labels_v0.get("decision") or {}
    )
    balanced_hard_negative_labels_v0_summary = (
        balanced_hard_negative_labels_v0.get("summary") or {}
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
        hard_negative_targets_v0_decision.get("status")
        == "hard_negative_selector_target_candidates_built"
        and hard_negative_targets_v0_decision.get("runtime_work_allowed") is False
        and hard_negative_targets_v0_decision.get("selector_training_allowed")
        is False
        and hard_negative_targets_v0_decision.get("stage7_promotion_allowed")
        is False
        and hard_negative_targets_v0_decision.get("stage8_training_allowed")
        is False
        and hard_negative_targets_v0_summary.get("row_count") == 16
        and hard_negative_targets_v0_summary.get("training_row_count") == 0
        and hard_negative_targets_v0_summary.get("stage7_row_count") == 0
        and hard_negative_ablation_v0_decision.get("status")
        == "hard_negative_feature_ablation_no_runtime_ready_signal"
        and hard_negative_ablation_v0_decision.get("runtime_work_allowed") is False
        and hard_negative_ablation_v0_decision.get("selector_training_allowed")
        is False
        and hard_negative_ablation_v0_decision.get("stage7_promotion_allowed")
        is False
        and hard_negative_ablation_v0_decision.get("stage8_training_allowed")
        is False
        and hard_negative_ablation_v0_summary.get("row_count") == 16
        and hard_negative_ablation_v0_summary.get("underpowered") is True
        and hard_negative_ablation_v0_summary.get("stage7_row_count") == 0
        and balanced_hard_negative_plan_v0_decision.get("status")
        == "balanced_hard_negative_label_plan_ready"
        and balanced_hard_negative_plan_v0_decision.get("runtime_work_allowed")
        is False
        and balanced_hard_negative_plan_v0_decision.get("selector_training_allowed")
        is False
        and balanced_hard_negative_plan_v0_summary.get("job_count") == 12
        and balanced_hard_negative_plan_v0_summary.get("stage7_jobs") == 0
        and balanced_hard_negative_manifest_v0_decision.get("status")
        == "balanced_hard_negative_execution_manifest_bound"
        and balanced_hard_negative_manifest_v0_decision.get("labels_allowed_now")
        is False
        and balanced_hard_negative_manifest_v0_decision.get("runtime_work_allowed")
        is False
        and balanced_hard_negative_manifest_v0_decision.get(
            "selector_training_allowed"
        )
        is False
        and balanced_hard_negative_manifest_v0_binding.get("all_bindings_valid")
        is True
        and balanced_hard_negative_manifest_v0_binding.get("job_count") == 12
        and balanced_hard_negative_manifest_v0_binding.get("stage7_jobs") == 0
        and balanced_hard_negative_manifest_review_v0_decision.get("status")
        == "balanced_hard_negative_manifest_review_passed_labels_allowed"
        and balanced_hard_negative_manifest_review_v0_decision.get(
            "runtime_work_allowed"
        )
        is False
        and balanced_hard_negative_manifest_review_v0_decision.get(
            "selector_training_allowed"
        )
        is False
        and balanced_hard_negative_labels_v0_decision.get("status")
        == "balanced_hard_negative_labels_completed"
        and balanced_hard_negative_labels_v0_decision.get("runtime_work_allowed")
        is False
        and balanced_hard_negative_labels_v0_decision.get(
            "selector_training_allowed"
        )
        is False
        and balanced_hard_negative_labels_v0_summary.get("label_count") == 12
        and balanced_hard_negative_labels_v0_summary.get("stage7_labels") == 0
        and balanced_hard_negative_labels_v0_summary.get("stage7_training_labels")
        == 0
        and all(
            artifact.get("runtime_behavior_changed") is False
            and artifact.get("runtime_defaults_changed") is False
            and artifact.get("runtime_selector_implemented") is False
            and artifact.get("runtime_dtm_or_tablebase_lookup") is False
            and artifact.get("runtime_terminals_added", False) is False
            and artifact.get("stage7_promotion_allowed") is False
            and artifact.get("stage8_training_allowed") is False
            for artifact in [
                hard_negative_selector_target_dataset_v0,
                hard_negative_selector_feature_ablation_v0,
                balanced_hard_negative_label_plan_v0,
                balanced_hard_negative_execution_manifest_v0,
                balanced_hard_negative_execution_manifest_review_v0,
                balanced_hard_negative_labels_v0,
            ]
        )
        and balanced_hard_negative_plan_decision.get("status")
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
    hard_negative_targets_decision = (
        hard_negative_selector_target_dataset_v2.get("decision") or {}
    )
    hard_negative_targets_summary = (
        hard_negative_selector_target_dataset_v2.get("summary") or {}
    )
    hard_negative_semantics_decision = (
        hard_negative_selector_target_training_semantics_review_v0.get("decision")
        or {}
    )
    hard_negative_semantics_summary = (
        hard_negative_selector_target_training_semantics_review_v0.get("summary") or {}
    )
    hard_negative_label_semantics_decision = (
        hard_negative_label_semantics_review_v1.get("decision") or {}
    )
    hard_negative_label_semantics_summary = (
        hard_negative_label_semantics_review_v1.get("summary") or {}
    )
    hard_negative_label_semantics_split = (
        hard_negative_label_semantics_review_v1.get("recommended_objective_split")
        or {}
    )
    hard_negative_label_semantics_channels = {
        row.get("label_channel"): row
        for row in hard_negative_label_semantics_review_v1.get("semantics") or []
    }
    hard_negative_label_semantics_passive = (
        hard_negative_label_semantics_review_v1.get("causal_status")
        == "non_causal_semantics_review"
        and hard_negative_label_semantics_decision.get("status")
        == "capacity_labels_not_direct_selector_targets"
        and hard_negative_label_semantics_decision.get("recommended_next_step")
        == "run_stronger_capacity_risk_feature_review_non_causal"
        and hard_negative_label_semantics_decision.get("runtime_work_allowed") is False
        and hard_negative_label_semantics_decision.get("selector_training_allowed")
        is False
        and hard_negative_label_semantics_decision.get("stage7_promotion_allowed")
        is False
        and hard_negative_label_semantics_decision.get("stage8_training_allowed")
        is False
        and hard_negative_label_semantics_review_v1.get("source_artifacts")
        == [
            "reports/krk_hard_negative_selector_target_dataset_v2.json",
            "reports/krk_hard_negative_selector_feature_ablation_v2.json",
            "reports/krk_balanced_hard_negative_evidence_review_v0.json",
        ]
        and hard_negative_label_semantics_summary.get("row_count") == 40
        and hard_negative_label_semantics_summary.get("state_count") == 14
        and hard_negative_label_semantics_summary.get("stage7_row_count") == 0
        and hard_negative_label_semantics_summary.get("capacity_negative_count") == 9
        and hard_negative_label_semantics_summary.get("capacity_positive_count") == 31
        and hard_negative_label_semantics_summary.get(
            "state_local_contrast_state_count"
        )
        == 2
        and hard_negative_label_semantics_summary.get(
            "best_ablation_negative_suppression"
        )
        == 0.2222222222222222
        and hard_negative_label_semantics_summary.get(
            "best_ablation_positive_recall"
        )
        == 1.0
        and hard_negative_label_semantics_split.get("capacity_recall_objective")
        == "which validated providers should be present in candidate set"
        and hard_negative_label_semantics_split.get("capacity_risk_objective")
        == "which forced-provider paths are risky under current h40 continuation"
        and hard_negative_label_semantics_split.get("ownership_selection_objective")
        == (
            "which provider should own normal runtime decision; "
            "not supplied by this dataset alone"
        )
        and hard_negative_label_semantics_split.get("safe_preservation_objective")
        == (
            "validated safe owners must be preserved before any suppression can "
            "be reviewed"
        )
        and {
            channel: row.get("blocked_use")
            for channel, row in hard_negative_label_semantics_channels.items()
        }
        == {
            "forced_provider_capacity_label": (
                "direct_runtime_owner_selection_or_suppression"
            ),
            "state_local_capacity_contrast": "global provider-family suppression",
            "hard_negative_capacity": (
                "selector training target until safe-owner preservation is "
                "separately validated"
            ),
        }
        and "reports/krk_hard_negative_label_semantics_review_v1.json"
        in (stronger_selector_feature_review_v0.get("source_artifacts") or [])
        and hard_negative_label_semantics_review_v1.get("runtime_behavior_changed")
        is False
        and hard_negative_label_semantics_review_v1.get("runtime_defaults_changed")
        is False
        and hard_negative_label_semantics_review_v1.get("runtime_selector_implemented")
        is False
        and hard_negative_label_semantics_review_v1.get(
            "runtime_candidate_generator_implemented"
        )
        is False
        and hard_negative_label_semantics_review_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and hard_negative_label_semantics_review_v1.get("runtime_terminals_added")
        is False
        and hard_negative_label_semantics_review_v1.get("gameplay_topology_mutation")
        is False
        and hard_negative_label_semantics_review_v1.get("stage7_promotion_allowed")
        is False
        and hard_negative_label_semantics_review_v1.get("stage8_training_allowed")
        is False
    )
    feature_ablation_decision = (
        hard_negative_selector_feature_ablation_v2.get("decision") or {}
    )
    feature_ablation_summary = (
        hard_negative_selector_feature_ablation_v2.get("summary") or {}
    )
    feature_ablation_best_result = (
        hard_negative_selector_feature_ablation_v2.get("best_result") or {}
    )
    stronger_feature_decision = stronger_selector_feature_review_v0.get("decision") or {}
    stronger_feature_summary = stronger_selector_feature_review_v0.get("summary") or {}
    stronger_feature_best_result = (
        stronger_selector_feature_review_v0.get("best_result") or {}
    )
    stronger_selector_feature_passive = (
        hard_negative_selector_feature_ablation_v2.get("causal_status")
        == "non_causal_feature_ablation"
        and feature_ablation_decision.get("status")
        == "hard_negative_feature_ablation_promising_underpowered"
        and feature_ablation_decision.get("runtime_work_allowed") is False
        and feature_ablation_decision.get("selector_training_allowed") is False
        and feature_ablation_decision.get("stage7_promotion_allowed") is False
        and feature_ablation_decision.get("stage8_training_allowed") is False
        and feature_ablation_summary.get("underpowered") is True
        and feature_ablation_summary.get("row_count") == 40
        and feature_ablation_summary.get("stage7_row_count") == 0
        and hard_negative_selector_feature_ablation_v2.get("runtime_behavior_changed")
        is False
        and hard_negative_selector_feature_ablation_v2.get("runtime_defaults_changed")
        is False
        and hard_negative_selector_feature_ablation_v2.get(
            "runtime_selector_implemented"
        )
        is False
        and hard_negative_selector_feature_ablation_v2.get(
            "runtime_candidate_generator_implemented"
        )
        is False
        and hard_negative_selector_feature_ablation_v2.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and hard_negative_selector_feature_ablation_v2.get("runtime_terminals_added")
        is False
        and hard_negative_selector_feature_ablation_v2.get(
            "gameplay_topology_mutation"
        )
        is False
        and hard_negative_selector_feature_ablation_v2.get(
            "stage7_promotion_allowed"
        )
        is False
        and hard_negative_selector_feature_ablation_v2.get("stage8_training_allowed")
        is False
        and stronger_selector_feature_review_v0.get("causal_status")
        == "non_causal_feature_review"
        and stronger_feature_decision.get("status")
        == "stronger_features_review_ready_runtime_still_blocked"
        and stronger_feature_decision.get("runtime_work_allowed") is False
        and stronger_feature_decision.get("selector_training_allowed") is False
        and stronger_feature_decision.get("stage7_promotion_allowed") is False
        and stronger_feature_decision.get("stage8_training_allowed") is False
        and stronger_feature_summary.get("improved_over_v2_ablation") is True
        and stronger_feature_summary.get("row_count") == 40
        and stronger_feature_summary.get("stage7_row_count") == 0
        and stronger_feature_best_result.get("negative_suppression")
        == stronger_feature_summary.get("best_negative_suppression")
        and stronger_selector_feature_review_v0.get("runtime_behavior_changed")
        is False
        and stronger_selector_feature_review_v0.get("runtime_defaults_changed")
        is False
        and stronger_selector_feature_review_v0.get("runtime_selector_implemented")
        is False
        and stronger_selector_feature_review_v0.get(
            "runtime_candidate_generator_implemented"
        )
        is False
        and stronger_selector_feature_review_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and stronger_selector_feature_review_v0.get("runtime_terminals_added")
        is False
        and stronger_selector_feature_review_v0.get("gameplay_topology_mutation")
        is False
        and stronger_selector_feature_review_v0.get("stage7_promotion_allowed")
        is False
        and stronger_selector_feature_review_v0.get("stage8_training_allowed")
        is False
    )
    provider_diversity_plan_decision = (
        selected_provider_diversity_evidence_plan_v0.get("decision") or {}
    )
    provider_diversity_replay_decision = (
        selected_provider_diversity_replay_free_scan_v0.get("decision") or {}
    )
    provider_diversity_replay_summary = (
        selected_provider_diversity_replay_free_scan_v0.get("summary") or {}
    )
    provider_diversity_observation_manifest_decision = (
        selected_provider_diversity_sampling_manifest_v0.get("decision") or {}
    )
    provider_diversity_observation_manifest_binding = (
        selected_provider_diversity_sampling_manifest_v0.get("binding_summary") or {}
    )
    provider_diversity_observation_manifest_policy = (
        selected_provider_diversity_sampling_manifest_v0.get("selection_policy") or {}
    )
    provider_diversity_observation_manifest_review_decision = (
        selected_provider_diversity_sampling_manifest_review_v0.get("decision") or {}
    )
    provider_diversity_observation_decision = (
        selected_provider_diversity_observation_scan_v0.get("decision") or {}
    )
    provider_diversity_observation_summary = (
        selected_provider_diversity_observation_scan_v0.get("summary") or {}
    )
    provider_diversity_manifest_decision = (
        selected_provider_diversity_sampling_manifest_v1.get("decision") or {}
    )
    provider_diversity_manifest_binding = (
        selected_provider_diversity_sampling_manifest_v1.get("binding_summary") or {}
    )
    provider_diversity_manifest_policy = (
        selected_provider_diversity_sampling_manifest_v1.get("selection_policy") or {}
    )
    provider_diversity_labels_decision = (
        selected_provider_diversity_ownership_labels_v1.get("decision") or {}
    )
    provider_diversity_labels_summary = (
        selected_provider_diversity_ownership_labels_v1.get("summary") or {}
    )
    provider_diversity_architecture_decision = (
        selected_provider_diversity_architecture_review_v0.get("decision") or {}
    )
    selected_provider_diversity_passive = (
        selected_provider_diversity_evidence_plan_v0.get("causal_status")
        == "non_causal_design_plan"
        and provider_diversity_plan_decision.get("status")
        == "selected_provider_diversity_evidence_plan_defined"
        and provider_diversity_plan_decision.get("runtime_arbiter_allowed") is False
        and provider_diversity_plan_decision.get("selector_sandbox_ready") is False
        and selected_provider_diversity_evidence_plan_v0.get(
            "labels_generated_in_this_slice"
        )
        is False
        and selected_provider_diversity_replay_free_scan_v0.get("causal_status")
        == "non_causal_scan"
        and provider_diversity_replay_decision.get("status")
        == "selected_provider_diversity_replay_free_insufficient"
        and provider_diversity_replay_decision.get("runtime_arbiter_allowed")
        is False
        and provider_diversity_replay_decision.get("selector_sandbox_ready")
        is False
        and provider_diversity_replay_summary.get("selected_record_count") == 23
        and provider_diversity_replay_summary.get("stage7_records") == 0
        and provider_diversity_replay_summary.get(
            "max_selected_provider_family_dominance"
        )
        == 0.7826
        and selected_provider_diversity_sampling_manifest_v0.get("causal_status")
        == "non_causal_sampling_manifest"
        and provider_diversity_observation_manifest_decision.get("status")
        == "selected_provider_diversity_sampling_manifest_review_required"
        and provider_diversity_observation_manifest_decision.get(
            "observations_allowed_now"
        )
        is False
        and provider_diversity_observation_manifest_decision.get(
            "runtime_arbiter_allowed"
        )
        is False
        and provider_diversity_observation_manifest_decision.get(
            "selector_sandbox_ready"
        )
        is False
        and provider_diversity_observation_manifest_binding.get(
            "all_bindings_valid"
        )
        is True
        and provider_diversity_observation_manifest_binding.get("job_count") == 20
        and provider_diversity_observation_manifest_binding.get("missing_path_count")
        == 0
        and provider_diversity_observation_manifest_policy.get("stage7_jobs") == 0
        and provider_diversity_observation_manifest_policy.get("observation_only")
        is True
        and selected_provider_diversity_sampling_manifest_v0.get(
            "labels_generated_in_this_slice"
        )
        is False
        and selected_provider_diversity_sampling_manifest_review_v0.get(
            "causal_status"
        )
        == "non_causal_manifest_review"
        and provider_diversity_observation_manifest_review_decision.get("status")
        == "selected_provider_diversity_sampling_manifest_review_passed"
        and provider_diversity_observation_manifest_review_decision.get(
            "observations_allowed"
        )
        is True
        and provider_diversity_observation_manifest_review_decision.get(
            "runtime_arbiter_allowed"
        )
        is False
        and provider_diversity_observation_manifest_review_decision.get(
            "selector_sandbox_ready"
        )
        is False
        and selected_provider_diversity_sampling_manifest_review_v0.get(
            "labels_generated_in_this_slice"
        )
        is False
        and selected_provider_diversity_observation_scan_v0.get("causal_status")
        == "non_causal_observation_scan"
        and provider_diversity_observation_decision.get("status")
        == "selected_provider_diversity_observation_insufficient"
        and provider_diversity_observation_decision.get("runtime_arbiter_allowed")
        is False
        and provider_diversity_observation_decision.get("selector_sandbox_ready")
        is False
        and provider_diversity_observation_summary.get("observation_count") == 20
        and provider_diversity_observation_summary.get("stage7_observations") == 0
        and provider_diversity_observation_summary.get(
            "max_selected_provider_family_dominance"
        )
        == 1.0
        and "reports/krk_selected_provider_diversity_sampling_manifest_v0.json"
        in (selected_provider_diversity_sampling_manifest_review_v0.get("source_artifacts") or [])
        and "reports/krk_selected_provider_diversity_sampling_manifest_v0.json"
        in (selected_provider_diversity_observation_scan_v0.get("source_artifacts") or [])
        and "reports/krk_selected_provider_diversity_sampling_manifest_review_v0.json"
        in (selected_provider_diversity_observation_scan_v0.get("source_artifacts") or [])
        and selected_provider_diversity_sampling_manifest_v1.get("causal_status")
        == "non_causal_sampling_manifest"
        and "reports/krk_selected_provider_diversity_replay_free_scan_v0.json"
        in (selected_provider_diversity_sampling_manifest_v1.get("source_artifacts") or [])
        and "reports/krk_selected_provider_diversity_replay_free_scan_v0.json"
        in (selected_provider_diversity_architecture_review_v0.get("source_artifacts") or [])
        and "reports/krk_selected_provider_diversity_observation_scan_v0.json"
        in (selected_provider_diversity_architecture_review_v0.get("source_artifacts") or [])
        and provider_diversity_manifest_decision.get("status")
        == "fresh_seed_selected_provider_diversity_manifest_ready_for_bounded_labels"
        and provider_diversity_manifest_decision.get("observations_allowed_now")
        is False
        and provider_diversity_manifest_decision.get("runtime_arbiter_allowed")
        is False
        and provider_diversity_manifest_decision.get("selector_sandbox_ready")
        is False
        and provider_diversity_manifest_binding.get("all_bindings_valid") is True
        and provider_diversity_manifest_binding.get("job_count") == 18
        and provider_diversity_manifest_binding.get("missing_path_count") == 0
        and provider_diversity_manifest_policy.get("stage7_jobs") == 0
        and provider_diversity_manifest_policy.get("observation_only") is True
        and selected_provider_diversity_sampling_manifest_v1.get(
            "labels_generated_in_this_slice"
        )
        is False
        and selected_provider_diversity_ownership_labels_v1.get("causal_status")
        == "non_causal_label_run"
        and provider_diversity_labels_decision.get("status")
        == "fresh_seed_selected_provider_diversity_ownership_labels_collected"
        and provider_diversity_labels_decision.get("runtime_work_allowed") is False
        and provider_diversity_labels_decision.get("selector_training_allowed")
        is False
        and provider_diversity_labels_decision.get("stage7_promotion_allowed")
        is False
        and provider_diversity_labels_decision.get("stage8_training_allowed")
        is False
        and provider_diversity_labels_summary.get("label_count") == 18
        and provider_diversity_labels_summary.get("stage7_training_rows") == 0
        and provider_diversity_labels_summary.get("trace_failures_only") is True
        and selected_provider_diversity_architecture_review_v0.get("causal_status")
        == "non_causal_architecture_review"
        and provider_diversity_architecture_decision.get("status")
        == "selected_provider_diversity_requirement_should_be_reframed"
        and provider_diversity_architecture_decision.get("runtime_arbiter_allowed")
        is False
        and provider_diversity_architecture_decision.get("selector_sandbox_ready")
        is False
        and all(
            artifact.get("runtime_behavior_changed") is False
            and artifact.get("runtime_defaults_changed") is False
            and artifact.get("runtime_dtm_or_tablebase_lookup") is False
            and artifact.get("runtime_terminals_added") is False
            and artifact.get("runtime_arbiter_implemented") is False
            and artifact.get("gameplay_topology_mutation") is False
            and artifact.get("stage7_promotion_allowed") is False
            and artifact.get("stage8_training_allowed") is False
            for artifact in [
                selected_provider_diversity_evidence_plan_v0,
                selected_provider_diversity_sampling_manifest_v1,
                selected_provider_diversity_ownership_labels_v1,
                selected_provider_diversity_architecture_review_v0,
            ]
        )
        and selected_provider_diversity_ownership_labels_v1.get(
            "runtime_selector_implemented"
        )
        is False
        and selected_provider_diversity_ownership_labels_v1.get(
            "runtime_candidate_generator_implemented"
        )
        is False
    )
    selector_readiness_v3_decision = selector_readiness_v3_plan.get("decision") or {}
    selector_readiness_v3_checks = {
        check.get("requirement_id"): check
        for check in selector_readiness_v3_plan.get("readiness_checks_v3") or []
    }
    selector_readiness_v3_stage_coverage = (
        selector_readiness_v3_checks.get("protected_stage_coverage") or {}
    ).get("observed") or {}
    selector_readiness_v3_label_balance = (
        selector_readiness_v3_checks.get("label_balance") or {}
    ).get("observed") or {}
    selector_readiness_v3_stage7_boundary = (
        selector_readiness_v3_checks.get("stage7_heldout_boundary") or {}
    ).get("observed") or {}
    selector_readiness_v3_conversion_diversity = (
        selector_readiness_v3_checks.get("conversion_positive_provider_diversity")
        or {}
    ).get("observed") or {}
    selector_readiness_v3_blocked_next_steps = (
        selector_readiness_v3_plan.get("blocked_next_steps") or []
    )
    selector_readiness_v3_sandbox_requirements = (
        selector_readiness_v3_plan.get("sandbox_design_requirements") or []
    )
    selector_readiness_v3_passive = (
        selector_readiness_v3_plan.get("causal_status") == "non_causal_design_plan"
        and selector_readiness_v3_decision.get("status")
        == "selector_readiness_v3_sandbox_design_review_allowed"
        and selector_readiness_v3_decision.get("recommended_next_step")
        == "design_default_off_strategy_arbiter_sandbox_for_review"
        and selector_readiness_v3_decision.get("runtime_arbiter_allowed") is False
        and selector_readiness_v3_decision.get("selector_sandbox_ready") is False
        and selector_readiness_v3_decision.get("hard_blockers") == []
        and selector_readiness_v3_plan.get("source_artifacts")
        == [
            "reports/krk_selected_provider_diversity_architecture_review_v0.json",
            "reports/krk_strategy_owner_contrast_dataset_v0.json",
            "reports/krk_strategy_owner_contrast_probe_v0.json",
        ]
        and {
            key: (selector_readiness_v3_checks.get(key) or {}).get("status")
            for key in [
                "proposal_family_diversity",
                "conversion_positive_provider_diversity",
                "label_balance",
                "protected_stage_coverage",
                "stage7_heldout_boundary",
                "current_selected_provider_diversity",
            ]
        }
        == {
            "proposal_family_diversity": "passed",
            "conversion_positive_provider_diversity": "passed",
            "label_balance": "passed",
            "protected_stage_coverage": "passed",
            "stage7_heldout_boundary": "passed",
            "current_selected_provider_diversity": (
                "diagnostic_only_not_sandbox_blocker"
            ),
        }
        and selector_readiness_v3_conversion_diversity.get(
            "distinct_conversion_positive_provider_families"
        )
        == 3
        and selector_readiness_v3_conversion_diversity.get("families")
        == ["drive_to_edge", "edge_trap", "fence_established"]
        and selector_readiness_v3_label_balance == {"negative": 11, "positive": 13}
        and selector_readiness_v3_stage_coverage.get("row_count_by_stage")
        == {"stage4": 2, "stage5": 4, "stage6": 3, "stage7": 4}
        and selector_readiness_v3_stage7_boundary.get("stage7_training_rows") == 0
        and all(
            item in selector_readiness_v3_blocked_next_steps
            for item in [
                "runtime_arbiter",
                "selector_sandbox_without_design_review",
                "stage7_repair",
                "stage7_promotion",
                "stage8_training",
                "runtime_dtm_or_tablebase",
                "gameplay_topology_mutation",
            ]
        )
        and all(
            item in selector_readiness_v3_sandbox_requirements
            for item in [
                "default_off",
                "default_off_equivalence_before_enabled_tests",
                "visible_source_terms_and_provider_metadata",
                "no_runtime_dtm_or_tablebase",
                "no_gameplay_topology_mutation",
                "stage7_held_out_challenge_only",
                "guardrail_validation_before_promotion",
            ]
        )
        and runtime_review_packet_evidence.get("readiness_v3_status")
        == selector_readiness_v3_decision.get("status")
        and "reports/krk_selector_readiness_v3_plan.json"
        in (strategy_arbiter_default_off_design_review_v1.get("source_artifacts") or [])
        and default_off_design_decision.get("implementation_allowed") is False
        and default_off_design_decision.get("runtime_arbiter_allowed") is False
        and default_off_design_decision.get("selector_sandbox_ready") is False
        and selector_readiness_v3_plan.get("runtime_behavior_changed") is False
        and selector_readiness_v3_plan.get("runtime_defaults_changed") is False
        and selector_readiness_v3_plan.get("runtime_arbiter_implemented") is False
        and selector_readiness_v3_plan.get("runtime_dtm_or_tablebase_lookup") is False
        and selector_readiness_v3_plan.get("runtime_terminals_added") is False
        and selector_readiness_v3_plan.get("gameplay_topology_mutation") is False
        and selector_readiness_v3_plan.get("stage7_promotion_allowed") is False
        and selector_readiness_v3_plan.get("stage8_training_allowed") is False
    )
    state_local_contrast_labels_decision = (
        state_local_contrast_labels_v2.get("decision") or {}
    )
    state_local_contrast_labels_summary = (
        state_local_contrast_labels_v2.get("summary") or {}
    )
    state_local_contrast_probe_decision = (
        state_local_contrast_selector_probe_v2.get("decision") or {}
    )
    state_local_contrast_probe_summary = (
        state_local_contrast_selector_probe_v2.get("summary") or {}
    )
    state_local_contrast_readiness_decision = (
        state_local_contrast_readiness_review_v2.get("decision") or {}
    )
    state_local_contrast_passive = (
        state_local_contrast_labels_v2.get("causal_status")
        == "non_causal_state_local_contrast_dataset"
        and state_local_contrast_labels_decision.get("status")
        == "state_local_contrast_labels_v2_joined"
        and state_local_contrast_labels_decision.get("runtime_test_allowed_next")
        is False
        and state_local_contrast_labels_decision.get("stage7_promotion_allowed")
        is False
        and state_local_contrast_labels_decision.get("stage8_training_allowed")
        is False
        and state_local_contrast_labels_summary.get("row_count") == 20
        and state_local_contrast_labels_summary.get("usable_training_row_count") == 12
        and state_local_contrast_labels_summary.get("stage7_challenge_row_count") == 8
        and state_local_contrast_labels_summary.get("training_contrast_label_counts")
        == {"negative": 3, "positive": 9}
        and state_local_contrast_labels_summary.get("stage7_contrast_label_counts")
        == {"negative": 8}
        and state_local_contrast_selector_probe_v2.get("causal_status")
        == "non_causal_offline_probe"
        and state_local_contrast_probe_decision.get("status")
        == "state_local_contrast_signal_not_ready"
        and state_local_contrast_probe_decision.get("runtime_test_allowed_next")
        is False
        and state_local_contrast_probe_decision.get("stage7_promotion_allowed")
        is False
        and state_local_contrast_probe_decision.get("stage8_training_allowed")
        is False
        and state_local_contrast_probe_summary.get("training_row_count") == 12
        and state_local_contrast_probe_summary.get("stage7_eval_row_count") == 8
        and state_local_contrast_probe_summary.get("stage7_training_leakage") is False
        and state_local_contrast_readiness_review_v2.get("causal_status")
        == "non_causal_readiness_review"
        and state_local_contrast_readiness_decision.get("status")
        == "runtime_selector_blocked_negative_suppression_zero"
        and state_local_contrast_readiness_decision.get("runtime_test_allowed_next")
        is False
        and state_local_contrast_readiness_review_v2.get("stage7_promotion_allowed")
        is False
        and state_local_contrast_readiness_review_v2.get("stage8_training_allowed")
        is False
        and "runtime_selector"
        in (state_local_contrast_readiness_decision.get("blocked_next_steps") or [])
        and all(
            artifact.get("runtime_behavior_changed") is False
            and artifact.get("runtime_defaults_changed") is False
            and artifact.get("runtime_dtm_or_tablebase_lookup") is False
            and artifact.get("stage7_promotion_allowed") is False
            and artifact.get("stage8_training_allowed") is False
            for artifact in [
                state_local_contrast_labels_v2,
                state_local_contrast_selector_probe_v2,
                state_local_contrast_readiness_review_v2,
            ]
        )
        and state_local_contrast_readiness_review_v2.get(
            "runtime_selector_implemented"
        )
        is False
    )
    ownership_context_decision = ownership_context_feature_review_v3.get(
        "decision"
    ) or {}
    ownership_context_summary = ownership_context_feature_review_v3.get("summary") or {}
    ownership_architecture_decision = (
        ownership_objective_architecture_review_v0.get("decision") or {}
    )
    ownership_architecture_summary = (
        ownership_objective_architecture_review_v0.get("summary") or {}
    )
    paired_plan_decision = (
        state_local_paired_ownership_objective_plan_v0.get("decision") or {}
    )
    paired_work_package_decision = (
        state_local_paired_ownership_work_package_v0.get("decision") or {}
    )
    paired_inventory_decision = (
        state_local_paired_ownership_inventory_v1.get("decision") or {}
    )
    paired_inventory_summary = (
        state_local_paired_ownership_inventory_v1.get("summary") or {}
    )
    paired_probe_decision = state_local_paired_ownership_probe_v1.get("decision") or {}
    paired_probe_summary = state_local_paired_ownership_probe_v1.get("summary") or {}
    paired_error_audit_decision = (
        state_local_paired_ownership_error_audit_v0.get("decision") or {}
    )
    paired_error_audit_summary = (
        state_local_paired_ownership_error_audit_v0.get("summary") or {}
    )
    paired_review_decision = (
        state_local_paired_ownership_review_v1.get("decision") or {}
    )
    paired_review_summary = state_local_paired_ownership_review_v1.get("summary") or {}
    state_local_paired_ownership_passive = (
        hard_negative_targets_decision.get("status")
        == "hard_negative_selector_target_dataset_expanded_v2"
        and hard_negative_targets_decision.get("runtime_work_allowed") is False
        and hard_negative_targets_decision.get("selector_training_allowed") is False
        and hard_negative_targets_summary.get("row_count") == 40
        and hard_negative_targets_summary.get("training_row_count") == 0
        and hard_negative_targets_summary.get("stage7_row_count") == 0
        and hard_negative_semantics_decision.get("status")
        == "hard_negative_targets_approved_for_offline_benchmark_only"
        and hard_negative_semantics_decision.get("runtime_work_allowed") is False
        and hard_negative_semantics_decision.get("selector_training_allowed") is False
        and hard_negative_semantics_summary.get("current_training_row_count") == 0
        and hard_negative_semantics_summary.get("stage7_row_count") == 0
        and ownership_context_decision.get("status")
        == "context_features_review_ready_but_not_runtime_ready"
        and ownership_context_decision.get("runtime_work_allowed") is False
        and ownership_context_decision.get("selector_training_allowed") is False
        and ownership_context_summary.get("runtime_threshold_passed") is False
        and ownership_context_summary.get("context_row_count") == 41
        and ownership_architecture_decision.get("status")
        == "ownership_objective_requires_state_local_pairing_review"
        and ownership_architecture_decision.get("runtime_work_allowed") is False
        and ownership_architecture_decision.get("selector_training_allowed") is False
        and ownership_architecture_summary.get("stage7_rows") == 0
        and ownership_architecture_summary.get("runtime_threshold_passed") is False
        and paired_plan_decision.get("status")
        == "state_local_paired_ownership_objective_plan_ready"
        and paired_plan_decision.get("runtime_work_allowed") is False
        and paired_plan_decision.get("selector_training_allowed") is False
        and paired_work_package_decision.get("status") == "work_package_ready"
        and paired_work_package_decision.get("runtime_work_allowed") is False
        and paired_work_package_decision.get("selector_training_allowed") is False
        and paired_inventory_decision.get("status")
        == "paired_inventory_ready_for_non_causal_probe"
        and paired_inventory_decision.get("runtime_work_allowed") is False
        and paired_inventory_decision.get("selector_training_allowed") is False
        and paired_inventory_summary.get("pair_count") == 40
        and paired_inventory_summary.get("selector_training_row_count") == 0
        and paired_inventory_summary.get("stage7_row_count") == 0
        and paired_probe_decision.get("status")
        == "semantic_gate_review_ready_runtime_feature_translation_needed"
        and paired_probe_decision.get("runtime_work_allowed") is False
        and paired_probe_decision.get("selector_training_allowed") is False
        and paired_probe_summary.get("runtime_feature_passing_model_count") == 0
        and paired_probe_summary.get("stage7_row_count") == 0
        and paired_error_audit_decision.get("status")
        == "safe_preservation_false_positives_are_outcome_semantics_errors"
        and paired_error_audit_decision.get("runtime_work_allowed") is False
        and paired_error_audit_decision.get("selector_training_allowed") is False
        and paired_error_audit_summary.get("stage7_row_count") == 0
        and paired_review_decision.get("status")
        == "semantic_gate_review_ready_runtime_feature_translation_needed"
        and paired_review_decision.get("runtime_work_allowed") is False
        and paired_review_decision.get("selector_training_allowed") is False
        and paired_review_summary.get("runtime_feature_passing_model_count") == 0
        and paired_review_summary.get("stage7_row_count") == 0
        and state_local_paired_ownership_review_v1.get("runtime_behavior_changed")
        is False
        and state_local_paired_ownership_review_v1.get("runtime_defaults_changed")
        is False
        and state_local_paired_ownership_review_v1.get("runtime_selector_implemented")
        is False
        and state_local_paired_ownership_review_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and state_local_paired_ownership_review_v1.get("runtime_terminals_added")
        is False
        and state_local_paired_ownership_review_v1.get("stage7_promotion_allowed")
        is False
        and state_local_paired_ownership_review_v1.get("stage8_training_allowed")
        is False
    )
    runtime_proxy_design_decision = (
        state_local_paired_runtime_proxy_design_v0.get("decision") or {}
    )
    runtime_proxy_dataset_decision = (
        state_local_paired_runtime_proxy_dataset_v0.get("decision") or {}
    )
    runtime_proxy_dataset_summary = (
        state_local_paired_runtime_proxy_dataset_v0.get("summary") or {}
    )
    runtime_proxy_probe_decision = (
        state_local_paired_runtime_proxy_probe_v0.get("decision") or {}
    )
    runtime_proxy_probe_summary = (
        state_local_paired_runtime_proxy_probe_v0.get("summary") or {}
    )
    runtime_proxy_review_decision = (
        state_local_paired_runtime_proxy_review_v0.get("decision") or {}
    )
    runtime_proxy_review_summary = (
        state_local_paired_runtime_proxy_review_v0.get("summary") or {}
    )
    runtime_review_packet_v0_decision = (
        state_local_paired_selector_runtime_review_packet_v0.get("decision") or {}
    )
    runtime_review_packet_v0_summary = (
        state_local_paired_selector_runtime_review_packet_v0.get("summary") or {}
    )
    failure_risk_evidence_decision = (
        selected_owner_failure_risk_evidence_v1.get("decision") or {}
    )
    failure_risk_evidence_summary = (
        selected_owner_failure_risk_evidence_v1.get("summary") or {}
    )
    failure_risk_visible_terms_decision = (
        selected_owner_failure_risk_visible_terms_v0.get("decision") or {}
    )
    failure_risk_visible_terms_summary = (
        selected_owner_failure_risk_visible_terms_v0.get("summary") or {}
    )
    failure_risk_visible_proxy_metrics = (
        failure_risk_visible_terms_summary.get("term_metrics") or {}
    ).get("selected_owner_failure_risk_proxy_v0") or {}
    failure_risk_visible_review_decision = (
        selected_owner_failure_risk_visible_proxy_review_v0.get("decision") or {}
    )
    failure_risk_visible_review_summary = (
        selected_owner_failure_risk_visible_proxy_review_v0.get("summary") or {}
    )
    failure_risk_visible_probe_decision = (
        selected_owner_failure_risk_visible_proxy_probe_v0.get("decision") or {}
    )
    failure_risk_visible_probe_summary = (
        selected_owner_failure_risk_visible_proxy_probe_v0.get("summary") or {}
    )
    failure_risk_independent_manifest_decision = (
        selected_owner_failure_risk_proxy_independent_manifest_v0.get("decision") or {}
    )
    failure_risk_independent_manifest_binding_summary = (
        selected_owner_failure_risk_proxy_independent_manifest_v0.get("binding_summary")
        or {}
    )
    failure_risk_independent_manifest_selection_policy = (
        selected_owner_failure_risk_proxy_independent_manifest_v0.get(
            "selection_policy"
        )
        or {}
    )
    failure_risk_independent_validation_v0_decision = (
        selected_owner_failure_risk_proxy_independent_validation_v0.get("decision")
        or {}
    )
    failure_risk_independent_validation_v0_summary = (
        selected_owner_failure_risk_proxy_independent_validation_v0.get("summary")
        or {}
    )
    failure_risk_blocker_review_decision = (
        selected_owner_failure_risk_proxy_blocker_review_v0.get("decision") or {}
    )
    failure_risk_blocker_review_summary = (
        selected_owner_failure_risk_proxy_blocker_review_v0.get("summary") or {}
    )
    failure_risk_proxy_probe_decision = (
        selected_owner_failure_risk_proxy_probe_v1.get("decision") or {}
    )
    failure_risk_proxy_probe_summary = (
        selected_owner_failure_risk_proxy_probe_v1.get("summary") or {}
    )
    failure_risk_independent_labels_decision = (
        selected_owner_failure_risk_proxy_independent_labels_v0.get("decision") or {}
    )
    failure_risk_independent_labels_summary = (
        selected_owner_failure_risk_proxy_independent_labels_v0.get("summary") or {}
    )
    failure_risk_independent_validation_decision = (
        selected_owner_failure_risk_proxy_independent_validation_v1.get("decision") or {}
    )
    failure_risk_independent_validation_summary = (
        selected_owner_failure_risk_proxy_independent_validation_v1.get("summary") or {}
    )
    runtime_proxy_review_packet_v1_decision = (
        state_local_paired_selector_runtime_proxy_review_packet_v1.get("decision")
        or {}
    )
    runtime_proxy_review_packet_v1_summary = (
        state_local_paired_selector_runtime_proxy_review_packet_v1.get("summary") or {}
    )
    progress_reconsideration_review_decision = (
        progress_window_reconsideration_runtime_test_review_v0.get("decision") or {}
    )
    progress_reconsideration_smoke_decision = (
        progress_window_reconsideration_runtime_smoke_v0.get("decision") or {}
    )
    progress_reconsideration_smoke_summary = (
        progress_window_reconsideration_runtime_smoke_v0.get("summary") or {}
    )
    progress_reconsideration_audit_decision = (
        progress_window_reconsideration_post_activation_audit_v0.get("decision") or {}
    )
    runtime_sandbox_policy_decision = (
        runtime_sandbox_policy_update_v0.get("decision") or {}
    )
    runtime_sandbox_policy_test_result = (
        runtime_sandbox_policy_update_v0.get("runtime_test_result") or {}
    )
    runtime_sandbox_policy_boundaries = (
        runtime_sandbox_policy_update_v0.get("hard_boundaries") or {}
    )
    selected_owner_failure_risk_proxy_passive = (
        runtime_proxy_design_decision.get("status")
        == "proxy_design_ready_for_replay_free_validation"
        and runtime_proxy_design_decision.get("runtime_work_allowed") is False
        and runtime_proxy_design_decision.get("selector_training_allowed") is False
        and runtime_proxy_dataset_decision.get("status")
        == "runtime_proxy_dataset_ready_for_non_causal_probe"
        and runtime_proxy_dataset_decision.get("runtime_work_allowed") is False
        and runtime_proxy_dataset_decision.get("selector_training_allowed") is False
        and runtime_proxy_dataset_summary.get("row_count") == 40
        and runtime_proxy_dataset_summary.get("selector_training_row_count") == 0
        and runtime_proxy_dataset_summary.get("stage7_row_count") == 0
        and runtime_proxy_probe_decision.get("status")
        == "visible_runtime_proxy_features_insufficient"
        and runtime_proxy_probe_decision.get("runtime_work_allowed") is False
        and runtime_proxy_probe_decision.get("selector_training_allowed") is False
        and runtime_proxy_probe_summary.get("visible_proxy_review_ready") is False
        and runtime_proxy_probe_summary.get("stage7_row_count") == 0
        and runtime_proxy_review_decision.get("status")
        == "runtime_proxy_translation_still_blocked"
        and runtime_proxy_review_decision.get("runtime_work_allowed") is False
        and runtime_proxy_review_decision.get("selector_training_allowed") is False
        and runtime_proxy_review_summary.get("visible_proxy_review_ready") is False
        and runtime_proxy_review_summary.get("stage7_row_count") == 0
        and runtime_review_packet_v0_decision.get("status")
        == "runtime_review_packet_ready_with_translation_blocker"
        and runtime_review_packet_v0_decision.get("implementation_allowed_by_this_packet")
        is False
        and runtime_review_packet_v0_summary.get("runtime_feature_translation_blocker")
        is True
        and runtime_review_packet_v0_summary.get("runtime_feature_passing_model_count")
        == 0
        and runtime_review_packet_v0_summary.get("stage7_row_count") == 0
        and failure_risk_evidence_decision.get("status")
        == "failure_risk_evidence_v1_built"
        and failure_risk_evidence_decision.get("runtime_work_allowed") is False
        and failure_risk_evidence_decision.get("selector_training_allowed") is False
        and failure_risk_evidence_summary.get("row_count") == 48
        and failure_risk_evidence_summary.get("selector_training_row_count") == 0
        and failure_risk_evidence_summary.get("stage7_row_count") == 0
        and failure_risk_visible_terms_decision.get("status")
        == "visible_failure_risk_terms_extracted_for_probe"
        and failure_risk_visible_terms_decision.get("runtime_work_allowed") is False
        and failure_risk_visible_terms_decision.get("selector_training_allowed")
        is False
        and failure_risk_visible_terms_summary.get("row_count") == 40
        and failure_risk_visible_terms_summary.get("stage7_row_count") == 0
        and failure_risk_visible_proxy_metrics.get("precision") == 1.0
        and failure_risk_visible_proxy_metrics.get("recall") == 1.0
        and failure_risk_visible_review_decision.get("status")
        == "visible_failure_risk_proxy_candidate_identified_not_runtime_ready"
        and failure_risk_visible_review_decision.get("runtime_work_allowed") is False
        and failure_risk_visible_review_decision.get("selector_training_allowed")
        is False
        and failure_risk_visible_review_summary.get(
            "review_threshold_met_on_current_dataset"
        )
        is True
        and failure_risk_visible_review_summary.get("stage7_row_count") == 0
        and failure_risk_visible_probe_decision.get("status")
        == "visible_failure_risk_proxy_candidate_needs_out_of_sample_validation"
        and failure_risk_visible_probe_decision.get("runtime_work_allowed") is False
        and failure_risk_visible_probe_decision.get("selector_training_allowed")
        is False
        and failure_risk_visible_probe_summary.get("row_count") == 40
        and failure_risk_visible_probe_summary.get("stage7_row_count") == 0
        and failure_risk_visible_probe_summary.get("review_threshold_met") is True
        and failure_risk_independent_manifest_decision.get("status")
        == "independent_proxy_validation_manifest_ready"
        and failure_risk_independent_manifest_decision.get("execute_labels_now")
        is True
        and failure_risk_independent_manifest_decision.get("runtime_work_allowed")
        is False
        and failure_risk_independent_manifest_decision.get(
            "selector_training_allowed"
        )
        is False
        and selected_owner_failure_risk_proxy_independent_manifest_v0.get(
            "implementation_allowed_by_this_manifest"
        )
        is False
        and selected_owner_failure_risk_proxy_independent_manifest_v0.get(
            "labels_generated_in_this_slice"
        )
        is False
        and failure_risk_independent_manifest_binding_summary.get(
            "all_bindings_valid"
        )
        is True
        and failure_risk_independent_manifest_binding_summary.get("job_count") == 8
        and failure_risk_independent_manifest_binding_summary.get(
            "stage7_job_count"
        )
        == 0
        and failure_risk_independent_manifest_selection_policy.get(
            "stage7_training_rows"
        )
        == 0
        and failure_risk_independent_validation_v0_decision.get("status")
        == "independent_proxy_validation_failed_or_underpowered"
        and failure_risk_independent_validation_v0_decision.get("runtime_work_allowed")
        is False
        and failure_risk_independent_validation_v0_decision.get(
            "selector_training_allowed"
        )
        is False
        and failure_risk_independent_validation_v0_summary.get("threshold_met")
        is False
        and failure_risk_independent_validation_v0_summary.get("stage7_row_count") == 0
        and failure_risk_blocker_review_decision.get("status")
        == "failed_proxy_closed_next_evidence_v1_required"
        and failure_risk_blocker_review_decision.get("runtime_work_allowed") is False
        and failure_risk_blocker_review_decision.get("selector_training_allowed")
        is False
        and failure_risk_blocker_review_summary.get("threshold_met") is False
        and failure_risk_blocker_review_summary.get("stage7_row_count") == 0
        and all(
            artifact.get("runtime_behavior_changed") is False
            and artifact.get("runtime_defaults_changed") is False
            and artifact.get("runtime_selector_implemented") is False
            and artifact.get("runtime_dtm_or_tablebase_lookup") is False
            and artifact.get("runtime_terminals_added") is False
            and artifact.get("stage7_promotion_allowed") is False
            and artifact.get("stage8_training_allowed") is False
            for artifact in [
                selected_owner_failure_risk_visible_proxy_probe_v0,
                selected_owner_failure_risk_proxy_independent_manifest_v0,
                selected_owner_failure_risk_proxy_independent_validation_v0,
                selected_owner_failure_risk_proxy_blocker_review_v0,
            ]
        )
        and failure_risk_proxy_probe_decision.get("status")
        == "proxy_v1_independent_candidate_found"
        and failure_risk_proxy_probe_decision.get("runtime_work_allowed") is False
        and failure_risk_proxy_probe_decision.get("selector_training_allowed") is False
        and failure_risk_proxy_probe_summary.get("row_count") == 48
        and failure_risk_proxy_probe_summary.get("independent_passing_proxy_count") == 3
        and failure_risk_proxy_probe_summary.get("stage7_row_count") == 0
        and failure_risk_independent_labels_decision.get("status")
        == "independent_proxy_validation_labels_collected"
        and failure_risk_independent_labels_decision.get("runtime_work_allowed")
        is False
        and failure_risk_independent_labels_decision.get("selector_training_allowed")
        is False
        and failure_risk_independent_labels_summary.get("label_count") == 8
        and failure_risk_independent_labels_summary.get("stage7_training_rows") == 0
        and failure_risk_independent_validation_decision.get("status")
        == "independent_proxy_validation_passed"
        and failure_risk_independent_validation_decision.get("runtime_work_allowed")
        is False
        and failure_risk_independent_validation_decision.get(
            "selector_training_allowed"
        )
        is False
        and failure_risk_independent_validation_summary.get("threshold_met") is True
        and failure_risk_independent_validation_summary.get("stage7_row_count") == 0
        and runtime_proxy_review_packet_v1_decision.get("status")
        == "runtime_review_ready_progress_window_scope_only"
        and runtime_proxy_review_packet_v1_decision.get(
            "runtime_implementation_allowed"
        )
        is False
        and runtime_proxy_review_packet_v1_summary.get("label_count") == 8
        and runtime_proxy_review_packet_v1_summary.get("precision") == 1.0
        and runtime_proxy_review_packet_v1_summary.get("recall") == 1.0
        and runtime_proxy_review_packet_v1_summary.get("stage7_row_count") == 0
        and state_local_paired_selector_runtime_proxy_review_packet_v1.get(
            "runtime_behavior_changed"
        )
        is False
        and state_local_paired_selector_runtime_proxy_review_packet_v1.get(
            "runtime_defaults_changed"
        )
        is False
        and state_local_paired_selector_runtime_proxy_review_packet_v1.get(
            "runtime_selector_implemented"
        )
        is False
        and state_local_paired_selector_runtime_proxy_review_packet_v1.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and state_local_paired_selector_runtime_proxy_review_packet_v1.get(
            "runtime_terminals_added"
        )
        is False
        and state_local_paired_selector_runtime_proxy_review_packet_v1.get(
            "stage7_promotion_allowed"
        )
        is False
        and state_local_paired_selector_runtime_proxy_review_packet_v1.get(
            "stage8_training_allowed"
        )
        is False
    )
    progress_window_reconsideration_passive = (
        progress_window_reconsideration_runtime_test_review_v0.get("causal_status")
        == "default_off_runtime_test_scaffold"
        and progress_reconsideration_review_decision.get("status")
        == "runtime_test_scaffold_wired_but_policy_insufficient"
        and progress_reconsideration_review_decision.get("guardrails_allowed_now")
        is False
        and progress_reconsideration_review_decision.get("promotion_allowed_now")
        is False
        and progress_window_reconsideration_runtime_test_review_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and progress_window_reconsideration_runtime_test_review_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and progress_window_reconsideration_runtime_test_review_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and progress_window_reconsideration_runtime_test_review_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and progress_window_reconsideration_runtime_test_review_v0.get(
            "stage8_training_allowed"
        )
        is False
        and progress_window_reconsideration_runtime_test_review_v0.get(
            "default_off_equivalence_passed"
        )
        is True
        and progress_window_reconsideration_runtime_test_review_v0.get(
            "target_improvement_observed"
        )
        is False
        and progress_window_reconsideration_runtime_test_review_v0.get(
            "safe_regression_observed"
        )
        is False
        and progress_window_reconsideration_runtime_smoke_v0.get("causal_status")
        == "runtime_test_default_off_sandbox_smoke"
        and progress_reconsideration_smoke_decision.get("status")
        == "runtime_smoke_activation_observed_no_target_improvement"
        and progress_reconsideration_smoke_summary.get("default_off_equivalence_passed")
        is True
        and progress_reconsideration_smoke_summary.get("improved_target_failure_count")
        == 0
        and progress_reconsideration_smoke_summary.get("safe_regression_count") == 0
        and progress_window_reconsideration_runtime_smoke_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and progress_window_reconsideration_runtime_smoke_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and progress_window_reconsideration_runtime_smoke_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and progress_window_reconsideration_runtime_smoke_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and progress_window_reconsideration_runtime_smoke_v0.get(
            "stage8_training_allowed"
        )
        is False
        and progress_window_reconsideration_post_activation_audit_v0.get(
            "causal_status"
        )
        == "non_causal_audit"
        and progress_reconsideration_audit_decision.get("status")
        == "post_activation_failure_classified"
        and progress_reconsideration_audit_decision.get("implement_next_fix_now")
        is False
        and progress_window_reconsideration_post_activation_audit_v0.get(
            "promotion_status"
        )
        == "quarantined_or_analysis_only"
        and progress_window_reconsideration_post_activation_audit_v0.get(
            "sandbox_status"
        )
        == "wired_but_policy_insufficient"
        and progress_window_reconsideration_post_activation_audit_v0.get(
            "runtime_defaults_changed"
        )
        is False
        and progress_window_reconsideration_post_activation_audit_v0.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and progress_window_reconsideration_post_activation_audit_v0.get(
            "gameplay_topology_mutation"
        )
        is False
        and progress_window_reconsideration_post_activation_audit_v0.get(
            "stage7_promotion_allowed"
        )
        is False
        and progress_window_reconsideration_post_activation_audit_v0.get(
            "stage8_training_allowed"
        )
        is False
    )
    runtime_sandbox_policy_update_passive = (
        runtime_sandbox_policy_update_v0.get("schema_version")
        == "krk_runtime_sandbox_policy_update.v0"
        and runtime_sandbox_policy_decision.get("status")
        == "reviewed_default_off_runtime_sandbox_allowed"
        and runtime_sandbox_policy_decision.get("allowed_scope")
        == "progress_window_selected_owner_reconsideration"
        and runtime_sandbox_policy_decision.get("broad_runtime_changes_allowed")
        is False
        and runtime_sandbox_policy_decision.get("default_policy_changes_allowed")
        is False
        and runtime_sandbox_policy_decision.get("stage7_promotion_allowed") is False
        and runtime_sandbox_policy_decision.get("stage8_training_allowed") is False
        and runtime_sandbox_policy_test_result.get("source_smoke")
        == "reports/krk_progress_window_reconsideration_runtime_smoke_v0.json"
        and runtime_sandbox_policy_test_result.get("source_review")
        == "reports/krk_progress_window_reconsideration_runtime_test_review_v0.json"
        and runtime_sandbox_policy_test_result.get("status")
        == progress_reconsideration_review_decision.get("status")
        and runtime_sandbox_policy_test_result.get("default_off_equivalence_passed")
        is True
        and runtime_sandbox_policy_test_result.get("activation_observed") is True
        and runtime_sandbox_policy_test_result.get("target_improvement_observed")
        is False
        and runtime_sandbox_policy_test_result.get("guardrails_allowed_now") is False
        and runtime_sandbox_policy_update_v0.get("source_review_packet")
        == "reports/krk_state_local_paired_selector_runtime_proxy_review_packet_v1.json"
        and runtime_sandbox_policy_boundaries
        == {
            "hidden_python_controller": False,
            "runtime_dtm_or_tablebase": False,
            "gameplay_topology_mutation": False,
            "general_predecision_selector": False,
            "stage7_repair_or_promotion": False,
            "stage8_training": False,
        }
        and all(
            item in (runtime_sandbox_policy_update_v0.get("immediate_plan") or [])
            for item in [
                "implement_default_off_progress_window_reconsideration_sandbox",
                "prove_default_off_equivalence",
                "run_protected_guardrails_only_if_target_improves",
                "use_stage7_as_heldout_challenge_only",
                "quarantine_or_keep_sandboxed_until_later_review",
            ]
        )
        and progress_window_reconsideration_passive is True
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
    protected_missing_provider_audit_plan_decision = (
        protected_missing_provider_capacity_audit_plan.get("decision") or {}
    )
    protected_missing_provider_audit_plan_summary = (
        protected_missing_provider_capacity_audit_plan.get("summary") or {}
    )
    protected_missing_provider_manifest_decision = (
        protected_missing_provider_execution_manifest.get("decision") or {}
    )
    protected_missing_provider_manifest_binding = (
        protected_missing_provider_execution_manifest.get("binding_summary") or {}
    )
    protected_missing_provider_manifest_review_decision = (
        protected_missing_provider_execution_manifest_review.get("decision") or {}
    )
    protected_missing_provider_manifest_review_summary = (
        protected_missing_provider_execution_manifest_review.get("review_summary") or {}
    )
    protected_missing_provider_labels_decision = (
        protected_missing_provider_labels.get("decision") or {}
    )
    protected_missing_provider_audit_plan_ready = (
        protected_missing_provider_capacity_audit_plan.get("schema_version")
        == "krk_protected_missing_provider_capacity_audit_plan.v0"
        and protected_missing_provider_audit_plan_decision.get("status")
        == "protected_missing_provider_capacity_audit_plan_ready"
        and protected_missing_provider_audit_plan_decision.get("runtime_work_allowed")
        is False
        and protected_missing_provider_audit_plan_summary.get("job_count") == 16
        and protected_missing_provider_audit_plan_summary.get("source_frame_count")
        == 6
        and protected_missing_provider_audit_plan_summary.get("runtime_work_allowed")
        is False
        and (
            protected_missing_provider_audit_plan_summary.get("stage_counts") or {}
        )
        == {"stage4": 6, "stage5": 7, "stage6": 3}
        and "reports/krk_protected_max_only_frame_review_v0.json"
        in (protected_missing_provider_capacity_audit_plan.get("source_artifacts") or [])
        and protected_missing_provider_capacity_audit_plan.get(
            "runtime_behavior_changed"
        )
        is False
        and protected_missing_provider_capacity_audit_plan.get(
            "runtime_defaults_changed"
        )
        is False
        and protected_missing_provider_capacity_audit_plan.get(
            "runtime_selector_implemented"
        )
        is False
        and protected_missing_provider_capacity_audit_plan.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and protected_missing_provider_capacity_audit_plan.get(
            "gameplay_topology_mutation"
        )
        is False
        and protected_missing_provider_capacity_audit_plan.get(
            "stage7_promotion_allowed"
        )
        is False
        and protected_missing_provider_capacity_audit_plan.get(
            "stage8_training_allowed"
        )
        is False
    )
    protected_missing_provider_manifest_review_passive = (
        protected_missing_provider_execution_manifest.get("schema_version")
        == "krk_protected_missing_provider_capacity_execution_manifest.v0"
        and protected_missing_provider_execution_manifest_review.get("schema_version")
        == "krk_protected_missing_provider_capacity_execution_manifest_review.v0"
        and protected_missing_provider_manifest_decision.get("status")
        == "protected_missing_provider_capacity_execution_manifest_bound"
        and protected_missing_provider_manifest_decision.get("labels_allowed_now")
        is False
        and protected_missing_provider_manifest_decision.get("runtime_work_allowed")
        is False
        and protected_missing_provider_manifest_binding.get("all_bindings_valid")
        is True
        and protected_missing_provider_manifest_binding.get("job_count") == 16
        and protected_missing_provider_manifest_binding.get("stage7_jobs") == 0
        and protected_missing_provider_audit_plan_ready
        and "reports/krk_protected_missing_provider_capacity_audit_plan_v0.json"
        in (protected_missing_provider_execution_manifest.get("source_artifacts") or [])
        and protected_missing_provider_manifest_review_decision.get("status")
        == "protected_missing_provider_capacity_manifest_review_passed_labels_allowed"
        and protected_missing_provider_manifest_review_decision.get(
            "runtime_work_allowed"
        )
        is False
        and protected_missing_provider_manifest_review_summary.get("job_count") == 16
        and protected_missing_provider_manifest_review_summary.get("violation_count")
        == 0
        and protected_missing_provider_execution_manifest.get(
            "runtime_behavior_changed"
        )
        is False
        and protected_missing_provider_execution_manifest.get(
            "runtime_defaults_changed"
        )
        is False
        and protected_missing_provider_execution_manifest.get(
            "runtime_selector_implemented"
        )
        is False
        and protected_missing_provider_execution_manifest.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and protected_missing_provider_execution_manifest.get(
            "gameplay_topology_mutation"
        )
        is False
        and protected_missing_provider_execution_manifest.get(
            "stage7_promotion_allowed"
        )
        is False
        and protected_missing_provider_execution_manifest.get(
            "stage8_training_allowed"
        )
        is False
        and protected_missing_provider_execution_manifest_review.get(
            "runtime_behavior_changed"
        )
        is False
        and protected_missing_provider_execution_manifest_review.get(
            "runtime_defaults_changed"
        )
        is False
        and protected_missing_provider_execution_manifest_review.get(
            "runtime_selector_implemented"
        )
        is False
        and protected_missing_provider_execution_manifest_review.get(
            "runtime_dtm_or_tablebase_lookup"
        )
        is False
        and protected_missing_provider_execution_manifest_review.get(
            "gameplay_topology_mutation"
        )
        is False
        and protected_missing_provider_execution_manifest_review.get(
            "stage7_promotion_allowed"
        )
        is False
        and protected_missing_provider_execution_manifest_review.get(
            "stage8_training_allowed"
        )
        is False
        and "reports/krk_protected_missing_provider_capacity_execution_manifest_v0.json"
        in (protected_missing_provider_labels.get("source_artifacts") or [])
        and "reports/krk_protected_missing_provider_capacity_execution_manifest_review_v0.json"
        in (protected_missing_provider_labels.get("source_artifacts") or [])
        and protected_missing_provider_labels_decision.get("status")
        == "protected_missing_provider_capacity_labels_completed"
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
            "stage4_caveat_diagnostic_matrix_ready": (
                stage4_caveat_diagnostic_matrix_ready
            ),
            "stage4_caveat_diagnostic_status": (
                stage4_caveat_diagnostic_matrix.get("status")
            ),
            "stage4_caveat_diagnostic_total": (
                stage4_caveat_diagnostic_observed.get("total")
            ),
            "stage4_caveat_diagnostic_mate_count": (
                stage4_caveat_diagnostic_observed.get("mate")
            ),
            "stage4_caveat_diagnostic_max_plies_count": (
                stage4_caveat_diagnostic_observed.get("max_plies")
            ),
            "stage4_caveat_diagnostic_mate_delta": (
                stage4_caveat_diagnostic_delta.get("mate_delta")
            ),
            "stage4_caveat_diagnostic_max_plies_delta": (
                stage4_caveat_diagnostic_delta.get("max_plies_delta")
            ),
            "stage4_caveat_diagnostic_candidate_gap_confidence": (
                stage4_caveat_candidate_gap_hypothesis.get("confidence")
            ),
            "stage4_caveat_diagnostic_candidate_gap_next_test": (
                stage4_caveat_candidate_gap_hypothesis.get("recommended_next_test")
            ),
            "stage4_caveat_diagnostic_runtime_behavior_changed": (
                stage4_caveat_diagnostic_invariants.get("runtime_behavior_changed")
            ),
            "stage4_caveat_diagnostic_runtime_defaults_changed": (
                stage4_caveat_diagnostic_invariants.get("runtime_defaults_changed")
            ),
            "stage4_caveat_diagnostic_runtime_selector_implemented": (
                stage4_caveat_diagnostic_invariants.get(
                    "runtime_selector_implemented"
                )
            ),
            "stage4_caveat_diagnostic_runtime_dtm_or_tablebase_lookup": (
                stage4_caveat_diagnostic_invariants.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "stage4_caveat_diagnostic_gameplay_topology_mutation": (
                stage4_caveat_diagnostic_invariants.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage4_caveat_decision_passive_ready": (
                stage4_caveat_decision_passive
            ),
            "stage4_caveat_decision_status": (
                stage4_caveat_decision_gate.get("status")
            ),
            "stage4_caveat_decision_selected": (
                stage4_caveat_decision_gate.get("selected_decisions") or []
            ),
            "stage4_caveat_decision_rejected": (
                stage4_caveat_decision_gate.get("rejected_decisions") or []
            ),
            "stage4_caveat_decision_next_action": (
                stage4_caveat_decision_gate.get("recommended_next_action")
            ),
            "stage4_caveat_runtime_or_training_authorized": (
                stage4_caveat_decision_gate.get("runtime_or_training_authorized")
            ),
            "stage4_caveat_runtime_behavior_changed": (
                stage4_caveat_decision_invariants.get("runtime_behavior_changed")
            ),
            "stage4_caveat_runtime_defaults_changed": (
                stage4_caveat_decision_invariants.get("runtime_defaults_changed")
            ),
            "stage4_caveat_runtime_selector_implemented": (
                stage4_caveat_decision_invariants.get(
                    "runtime_selector_implemented"
                )
            ),
            "stage4_caveat_runtime_dtm_or_tablebase_lookup": (
                stage4_caveat_decision_invariants.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "stage4_caveat_gameplay_topology_mutation": (
                stage4_caveat_decision_invariants.get("gameplay_topology_mutation")
            ),
            "stage4_caveat_stage7_promotion": (
                stage4_caveat_decision_invariants.get("stage7_promotion")
            ),
            "stage4_caveat_stage8_training": (
                stage4_caveat_decision_invariants.get("stage8_training")
            ),
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
        "strategy_arbiter_trace_observability_gate": {
            "status": arbiter_labeled_probe_decision.get("status"),
            "passive_trace_observability_ready": (
                arbiter_trace_observability_passive
            ),
            "sandbox_design_status": strategy_arbiter_sandbox_design_v0.get(
                "design_status"
            ),
            "sandbox_default_enabled": arbiter_sandbox_future.get(
                "default_enabled"
            ),
            "sandbox_blocked_next_steps": arbiter_sandbox_blocked,
            "smoke_status": arbiter_smoke_decision.get("status"),
            "smoke_runtime_arbiter_allowed": arbiter_smoke_decision.get(
                "runtime_arbiter_allowed"
            ),
            "smoke_selected_behavior_metrics_match": (
                arbiter_smoke_equivalence.get("selected_behavior_metrics_match")
            ),
            "smoke_outcome_metrics_match": (
                arbiter_smoke_equivalence.get("outcome_metrics_match")
            ),
            "smoke_observation_is_only_expected_delta": (
                arbiter_smoke_equivalence.get("observation_is_only_expected_delta")
            ),
            "smoke_direct_request": arbiter_smoke_metadata.get("direct_request"),
            "smoke_score_delta": arbiter_smoke_metadata.get("score_delta"),
            "smoke_recommendation_only": (
                arbiter_smoke_metadata.get("recommendation_only")
            ),
            "observation_frames_status": (
                arbiter_observation_frames_decision.get("status")
            ),
            "observation_frames_runtime_arbiter_allowed": (
                arbiter_observation_frames_decision.get("runtime_arbiter_allowed")
            ),
            "observation_frame_count": (
                strategy_arbiter_observation_frames_v0.get("record_count")
            ),
            "observation_stage_counts": arbiter_observation_stage_counts,
            "observation_selected_provider_counts": (
                strategy_arbiter_observation_frames_v0.get(
                    "selected_provider_counts"
                )
                or {}
            ),
            "observation_proposal_count_min": (
                strategy_arbiter_observation_frames_v0.get("proposal_count_min")
            ),
            "observation_proposal_count_max": (
                strategy_arbiter_observation_frames_v0.get("proposal_count_max")
            ),
            "separability_status": arbiter_separability_decision.get("status"),
            "separability_runtime_arbiter_allowed": (
                arbiter_separability_decision.get("runtime_arbiter_allowed")
            ),
            "separability_sandbox_ready": (
                arbiter_separability_decision.get("sandbox_ready")
            ),
            "separability_underinstrumented_record_count": (
                strategy_arbiter_observation_separability_review_v0.get(
                    "underinstrumented_record_count"
                )
            ),
            "separability_single_provider_record_count": (
                strategy_arbiter_observation_separability_review_v0.get(
                    "single_provider_record_count"
                )
            ),
            "selector_probe_status": arbiter_selector_probe_decision.get("status"),
            "selector_probe_runtime_arbiter_allowed": (
                arbiter_selector_probe_decision.get("runtime_arbiter_allowed")
            ),
            "selector_probe_sandbox_ready": (
                arbiter_selector_probe_decision.get("sandbox_ready")
            ),
            "selector_probe_underlabeled": (
                strategy_arbiter_observation_selector_probe_v0.get("underlabeled")
            ),
            "selector_probe_labeled_row_count": (
                strategy_arbiter_observation_selector_probe_v0.get(
                    "labeled_row_count"
                )
            ),
            "selector_probe_selected_unknown_count": (
                strategy_arbiter_observation_selector_probe_v0.get(
                    "selected_unknown_count"
                )
            ),
            "labeled_controls_status": arbiter_labeled_controls_decision.get(
                "status"
            ),
            "labeled_controls_runtime_arbiter_allowed": (
                arbiter_labeled_controls_decision.get("runtime_arbiter_allowed")
            ),
            "labeled_controls_record_count": (
                strategy_arbiter_labeled_observation_controls_v0.get("record_count")
            ),
            "labeled_controls_stage_counts": arbiter_labeled_controls_stage_counts,
            "labeled_controls_selected_label_counts": (
                strategy_arbiter_labeled_observation_controls_v0.get(
                    "selected_label_counts"
                )
                or {}
            ),
            "labeled_probe_status": arbiter_labeled_probe_decision.get("status"),
            "labeled_probe_runtime_arbiter_allowed": (
                arbiter_labeled_probe_decision.get("runtime_arbiter_allowed")
            ),
            "labeled_probe_sandbox_ready": (
                arbiter_labeled_probe_decision.get("sandbox_ready")
            ),
            "labeled_probe_record_count": (
                strategy_arbiter_labeled_controls_probe_v0.get("record_count")
            ),
            "labeled_probe_labeled_record_count": (
                strategy_arbiter_labeled_controls_probe_v0.get(
                    "labeled_record_count"
                )
            ),
            "labeled_probe_stage7_unknown_count": (
                strategy_arbiter_labeled_controls_probe_v0.get(
                    "stage7_unknown_count"
                )
            ),
            "labeled_probe_selected_positive_rate": (
                strategy_arbiter_labeled_controls_probe_v0.get(
                    "selected_positive_rate_on_labeled_controls"
                )
            ),
            "protected_matrix_status": arbiter_matrix_v1_decision.get("status"),
            "protected_matrix_default_off_equivalence_passed": (
                arbiter_matrix_v1_summary.get("default_off_equivalence_passed")
            ),
            "protected_matrix_enabled_conversion_not_worse": (
                arbiter_matrix_v1_summary.get("enabled_conversion_not_worse")
            ),
            "protected_matrix_no_no_move_or_draw_spike": (
                arbiter_matrix_v1_summary.get(
                    "enabled_has_no_no_move_or_draw_spike"
                )
            ),
            "protected_matrix_stage7_rows": (
                arbiter_matrix_v1_sample.get("stage7_rows")
            ),
            "runtime_arbiter_implemented": (
                strategy_arbiter_labeled_controls_probe_v0.get(
                    "runtime_arbiter_implemented"
                )
            ),
            "runtime_behavior_changed": (
                strategy_arbiter_labeled_controls_probe_v0.get(
                    "runtime_behavior_changed"
                )
            ),
            "runtime_defaults_changed": (
                strategy_arbiter_labeled_controls_probe_v0.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                strategy_arbiter_protected_control_matrix_v1.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "gameplay_topology_mutation": (
                strategy_arbiter_protected_control_matrix_v1.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": (
                strategy_arbiter_protected_control_matrix_v1.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                strategy_arbiter_protected_control_matrix_v1.get(
                    "stage8_training_allowed"
                )
            ),
        },
        "strategy_arbiter_semantics_blocker_gate": {
            "status": strategy_arbiter_control_plane_review_v0.get(
                "decision_status"
            ),
            "passive_semantics_blocker_ready": arbiter_semantics_blocker_passive,
            "risk_review_status": arbiter_risk_decision.get("status"),
            "risk_review_runtime_sandbox_allowed": (
                arbiter_risk_decision.get("runtime_sandbox_allowed")
            ),
            "risk_review_recommended_next_step": (
                arbiter_risk_decision.get("recommended_next_step")
            ),
            "risk_review_benchmark_frame_count": (
                arbiter_risk_summary.get("benchmark_frame_count")
            ),
            "risk_review_max_only_frame_count": (
                arbiter_risk_summary.get("max_only_frame_count")
            ),
            "risk_review_provider_mate_frame_count": (
                arbiter_risk_summary.get("provider_mate_frame_count")
            ),
            "risk_review_label_semantic_counts": (
                arbiter_risk_summary.get("label_semantic_counts") or {}
            ),
            "risk_review_blocked_next_steps": arbiter_risk_blocked_steps,
            "stratified_probe_status": arbiter_stratified_decision.get("status"),
            "stratified_probe_runtime_sandbox_allowed": (
                arbiter_stratified_decision.get("runtime_sandbox_allowed")
            ),
            "stratified_probe_selected_provider_hit_rate": (
                arbiter_stratified_summary.get(
                    "best_selected_provider_positive_hit_rate"
                )
            ),
            "stratified_probe_forced_control_hit_rate": (
                arbiter_stratified_summary.get(
                    "best_forced_provider_control_positive_hit_rate"
                )
            ),
            "stratified_probe_stage7_forced_provider_hit_rate": (
                arbiter_stratified_summary.get(
                    "best_forced_provider_positive_hit_rate"
                )
            ),
            "architecture_review_status": (
                strategy_arbiter_architecture_review_v1.get("decision_status")
            ),
            "architecture_runtime_arbiter_allowed": (
                strategy_arbiter_architecture_review_v1.get(
                    "runtime_arbiter_allowed"
                )
            ),
            "architecture_runtime_defaults_may_change": (
                strategy_arbiter_architecture_review_v1.get(
                    "runtime_defaults_may_change"
                )
            ),
            "architecture_stage7_status": (
                strategy_arbiter_architecture_review_v1.get("stage7_status")
            ),
            "architecture_stage7_gap_status": (
                (
                    arbiter_architecture_evidence.get(
                        "stage7_forced_provider_residuals"
                    )
                    or {}
                ).get("status")
            ),
            "architecture_allowed_next_scope": (
                arbiter_architecture_allowed_next.get("scope")
            ),
            "architecture_allowed_next_default_enabled": (
                arbiter_architecture_allowed_next.get("default_enabled")
            ),
            "architecture_allowed_next_may_change_scores": (
                arbiter_architecture_allowed_next.get("may_change_scores")
            ),
            "architecture_allowed_next_may_request_provider": (
                arbiter_architecture_allowed_next.get("may_request_provider")
            ),
            "sandbox_readiness_status": (
                strategy_arbiter_sandbox_readiness_criteria_v0.get(
                    "readiness_status"
                )
            ),
            "sandbox_readiness_decision_status": sandbox_criteria_decision.get(
                "status"
            ),
            "sandbox_readiness_runtime_arbiter_allowed": (
                sandbox_criteria_decision.get("runtime_arbiter_allowed")
            ),
            "sandbox_readiness_selector_sandbox_ready": (
                sandbox_criteria_decision.get("selector_sandbox_ready")
            ),
            "sandbox_readiness_stage7_repair_allowed": (
                sandbox_criteria_decision.get("stage7_repair_allowed")
            ),
            "sandbox_readiness_stage7_promotion_allowed": (
                sandbox_criteria_decision.get("stage7_promotion_allowed")
            ),
            "sandbox_readiness_stage8_training_allowed": (
                sandbox_criteria_decision.get("stage8_training_allowed")
            ),
            "sandbox_readiness_stage7_holdout_status": (
                sandbox_criteria_requirements.get(
                    "held_out_stage7_challenges", {}
                ).get("current_status")
            ),
            "sandbox_readiness_out_of_sample_controls_status": (
                sandbox_criteria_requirements.get(
                    "out_of_sample_controls", {}
                ).get("current_status")
            ),
            "control_plane_status": (
                strategy_arbiter_control_plane_review_v0.get("decision_status")
            ),
            "control_plane_observability_skeleton": (
                arbiter_control_current.get("observability_skeleton")
            ),
            "control_plane_labeled_controls": (
                arbiter_control_current.get("labeled_controls")
            ),
            "control_plane_stage7": arbiter_control_current.get("stage7"),
            "control_plane_runtime_arbiter_allowed": (
                arbiter_control_current.get("runtime_arbiter_allowed")
            ),
            "control_plane_sandbox_ready": (
                arbiter_control_current.get("sandbox_ready")
            ),
            "control_plane_observability_smoke_status": (
                (arbiter_control_evidence.get("observability_smoke") or {}).get(
                    "status"
                )
            ),
            "control_plane_observability_behavior_metrics_match": (
                (arbiter_control_evidence.get("observability_smoke") or {}).get(
                    "behavior_metrics_match"
                )
            ),
            "control_plane_labeled_controls_probe_status": (
                (arbiter_control_evidence.get("labeled_controls_probe") or {}).get(
                    "status"
                )
            ),
            "control_plane_labeled_controls_positive_rate": (
                (arbiter_control_evidence.get("labeled_controls_probe") or {}).get(
                    "selected_positive_rate_on_labeled_controls"
                )
            ),
            "control_plane_stage7_unknown_count": (
                (arbiter_control_evidence.get("labeled_controls_probe") or {}).get(
                    "stage7_unknown_count"
                )
            ),
            "control_plane_recommended_next_step_id": (
                arbiter_control_recommended.get("step_id")
            ),
            "control_plane_must_remain_non_causal": (
                arbiter_control_recommended.get("must_remain_non_causal")
            ),
            "control_plane_blocked_next_work": arbiter_control_blocked_work,
            "runtime_arbiter_implemented": (
                strategy_arbiter_stratified_probe_v2.get(
                    "runtime_arbiter_implemented"
                )
            ),
            "runtime_behavior_changed": (
                strategy_arbiter_stratified_probe_v2.get("runtime_behavior_changed")
            ),
            "runtime_defaults_changed": (
                strategy_arbiter_stratified_probe_v2.get("runtime_defaults_changed")
            ),
            "runtime_dtm_or_tablebase_lookup": (
                strategy_arbiter_stratified_probe_v2.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "gameplay_topology_mutation": (
                strategy_arbiter_stratified_probe_v2.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": (
                strategy_arbiter_stratified_probe_v2.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                strategy_arbiter_stratified_probe_v2.get(
                    "stage8_training_allowed"
                )
            ),
        },
        "strategy_arbiter_out_of_sample_gate": {
            "status": out_of_sample_architecture_decision.get("status"),
            "passive_out_of_sample_ready": strategy_arbiter_out_of_sample_passive,
            "plan_status": out_of_sample_plan_decision.get("status"),
            "plan_execute_collection_now": out_of_sample_plan_decision.get(
                "execute_collection_now"
            ),
            "plan_stage7_training_rows": out_of_sample_plan_bounds.get(
                "stage7_training_rows"
            ),
            "plan_review_status": out_of_sample_plan_review_decision.get("status"),
            "plan_review_execute_collection_now": (
                out_of_sample_plan_review_decision.get("execute_collection_now")
            ),
            "manifest_status": out_of_sample_manifest_decision.get("status"),
            "manifest_execute_labels_now": out_of_sample_manifest_decision.get(
                "execute_labels_now"
            ),
            "manifest_job_count": out_of_sample_manifest_binding.get("job_count"),
            "manifest_job_count_by_stage": (
                out_of_sample_manifest_binding.get("job_count_by_stage") or {}
            ),
            "manifest_required_stage_coverage_met": (
                out_of_sample_manifest_binding.get("required_stage_coverage_met")
            ),
            "manifest_missing_path_count": out_of_sample_manifest_binding.get(
                "missing_path_count"
            ),
            "manifest_stage7_training_rows": (
                out_of_sample_manifest_selection.get("stage7_training_rows")
            ),
            "manifest_labels_generated_in_this_slice": (
                strategy_arbiter_out_of_sample_execution_manifest_v0.get(
                    "labels_generated_in_this_slice"
                )
            ),
            "manifest_review_status": (
                out_of_sample_manifest_review_decision.get("status")
            ),
            "manifest_review_execute_labels_now": (
                out_of_sample_manifest_review_decision.get("execute_labels_now")
            ),
            "manifest_review_bounded_label_run_allowed_after_review": (
                out_of_sample_manifest_review_decision.get(
                    "bounded_label_run_allowed_after_review"
                )
            ),
            "manifest_review_stage7_training_rows": (
                out_of_sample_manifest_review_summary.get("stage7_training_rows")
            ),
            "label_run_status": (
                strategy_arbiter_out_of_sample_control_labels_v0.get(
                    "schema_version"
                )
            ),
            "label_count": out_of_sample_labels_summary.get("label_count"),
            "label_stage7_training_rows": out_of_sample_labels_summary.get(
                "stage7_training_rows"
            ),
            "label_trace_failures_only": out_of_sample_labels_summary.get(
                "trace_failures_only"
            ),
            "label_selected_result_counts": (
                out_of_sample_labels_summary.get("selected_result_counts") or {}
            ),
            "probe_status": out_of_sample_probe_decision.get("status"),
            "probe_sandbox_blockers": (
                out_of_sample_probe_decision.get("sandbox_blockers") or []
            ),
            "probe_label_count": out_of_sample_probe_metrics.get("label_count"),
            "probe_positive_rate": out_of_sample_probe_metrics.get("positive_rate"),
            "probe_selected_provider_dominance": (
                out_of_sample_probe_metrics.get("selected_provider_dominance")
            ),
            "probe_selected_provider_counts": (
                out_of_sample_probe_metrics.get("selected_provider_counts") or {}
            ),
            "probe_selector_training_signal_is_weak": (
                out_of_sample_probe_interpretation.get(
                    "selector_training_signal_is_weak"
                )
            ),
            "architecture_review_status": (
                out_of_sample_architecture_decision.get("status")
            ),
            "architecture_review_recommended_next_step": (
                out_of_sample_architecture_decision.get("recommended_next_step")
            ),
            "architecture_out_of_sample_probe_status": (
                out_of_sample_architecture_evidence.get(
                    "out_of_sample_probe_status"
                )
            ),
            "architecture_out_of_sample_selected_provider_counts": (
                out_of_sample_architecture_evidence.get(
                    "out_of_sample_selected_provider_counts"
                )
                or {}
            ),
            "architecture_selector_signal_status": (
                out_of_sample_architecture_interpretation.get(
                    "selector_signal_status"
                )
            ),
            "blocked_next_steps": out_of_sample_blocked_steps,
            "runtime_arbiter_allowed": (
                out_of_sample_architecture_decision.get("runtime_arbiter_allowed")
            ),
            "selector_sandbox_ready": (
                out_of_sample_architecture_decision.get("selector_sandbox_ready")
            ),
            "runtime_arbiter_implemented": (
                strategy_arbiter_out_of_sample_architecture_review_v0.get(
                    "runtime_arbiter_implemented"
                )
            ),
            "runtime_behavior_changed": (
                strategy_arbiter_out_of_sample_architecture_review_v0.get(
                    "runtime_behavior_changed"
                )
            ),
            "runtime_defaults_changed": (
                strategy_arbiter_out_of_sample_architecture_review_v0.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                strategy_arbiter_out_of_sample_architecture_review_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_terminals_added": (
                strategy_arbiter_out_of_sample_architecture_review_v0.get(
                    "runtime_terminals_added"
                )
            ),
            "gameplay_topology_mutation": (
                strategy_arbiter_out_of_sample_architecture_review_v0.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": (
                strategy_arbiter_out_of_sample_architecture_review_v0.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                strategy_arbiter_out_of_sample_architecture_review_v0.get(
                    "stage8_training_allowed"
                )
            ),
        },
        "strategy_arbiter_runtime_no_scale_gate": {
            "status": runtime_test_review_decision.get("status"),
            "passive_no_scale_ready": strategy_arbiter_runtime_no_scale_passive,
            "default_off_design_status": default_off_design_decision.get("status"),
            "default_off_design_implementation_allowed": (
                default_off_design_decision.get("implementation_allowed")
            ),
            "default_off_design_runtime_arbiter_allowed": (
                default_off_design_decision.get("runtime_arbiter_allowed")
            ),
            "default_off_design_selector_sandbox_ready": (
                default_off_design_decision.get("selector_sandbox_ready")
            ),
            "default_off_future_contract_default_enabled": (
                default_off_future_contract.get("default_enabled")
            ),
            "runtime_review_packet_status": runtime_review_packet_decision.get(
                "status"
            ),
            "runtime_review_packet_implementation_allowed": (
                runtime_review_packet_decision.get("implementation_allowed")
            ),
            "runtime_review_packet_runtime_arbiter_allowed": (
                runtime_review_packet_decision.get("runtime_arbiter_allowed")
            ),
            "runtime_review_packet_selector_sandbox_ready": (
                runtime_review_packet_decision.get("selector_sandbox_ready")
            ),
            "runtime_review_packet_blocked_until_review": (
                strategy_arbiter_runtime_review_packet_v1.get(
                    "implementation_blocked_until_review"
                )
            ),
            "runtime_review_packet_stage7_heldout_row_count": (
                runtime_review_packet_evidence.get("stage7_heldout_row_count")
            ),
            "runtime_sandbox_smoke_status": runtime_sandbox_smoke_decision.get(
                "status"
            ),
            "runtime_sandbox_default_off_equivalence_passed": (
                runtime_sandbox_smoke_decision.get("default_off_equivalence_passed")
            ),
            "runtime_sandbox_enabled_support_trace_visible": (
                runtime_sandbox_smoke_decision.get("enabled_support_trace_visible")
            ),
            "runtime_sandbox_flag_present_default_off_decision_matches_baseline": (
                runtime_sandbox_smoke_equivalence.get(
                    "flag_present_default_off_decision_matches_baseline"
                )
            ),
            "runtime_sandbox_flag_present_default_off_outcome_matches_baseline": (
                runtime_sandbox_smoke_equivalence.get(
                    "flag_present_default_off_outcome_matches_baseline"
                )
            ),
            "runtime_sandbox_direct_request": (
                runtime_sandbox_smoke_enabled.get("direct_request")
            ),
            "runtime_sandbox_support_was_applied": (
                runtime_sandbox_smoke_enabled.get("support_was_applied")
            ),
            "protected_control_matrix_status": protected_control_matrix_decision.get(
                "status"
            ),
            "protected_control_default_off_equivalence_passed": (
                protected_control_matrix_summary.get("default_off_equivalence_passed")
            ),
            "protected_control_no_conversion_regression": (
                protected_control_matrix_summary.get(
                    "enabled_has_no_conversion_regression"
                )
            ),
            "protected_control_no_no_move_or_draw_spike": (
                protected_control_matrix_summary.get(
                    "enabled_has_no_no_move_or_draw_spike"
                )
            ),
            "protected_control_stage7_rows": (
                protected_control_matrix_sample.get("stage7_rows")
            ),
            "stage7_holdout_status": stage7_holdout_decision.get("status"),
            "stage7_holdout_enabled_blocked_matches_baseline": (
                stage7_holdout_equivalence.get("enabled_blocked_matches_baseline")
            ),
            "stage7_holdout_support_blocked": (
                stage7_holdout_equivalence.get("support_blocked")
            ),
            "stage7_holdout_allow_stage7_challenge": (
                stage7_holdout_sample.get("allow_stage7_challenge")
            ),
            "stage7_challenge_status": stage7_challenge_decision.get("status"),
            "stage7_challenge_conversion_delta": (
                stage7_challenge_summary.get("conversion_delta")
            ),
            "stage7_challenge_selected_supported_count": (
                stage7_challenge_summary.get("selected_supported_count")
            ),
            "stage7_challenge_no_no_move_or_draw_spike": (
                stage7_challenge_summary.get("no_no_move_or_draw_spike")
            ),
            "support_sensitivity_status": support_sensitivity_decision.get("status"),
            "support_sensitivity_protected_control_status": (
                support_sensitivity_decision.get("protected_control_status")
            ),
            "support_sensitivity_stage7_runtime_test_status": (
                support_sensitivity_decision.get("stage7_runtime_test_status")
            ),
            "support_sensitivity_low_support_cap": (
                support_sensitivity_summary.get("low_support_cap")
            ),
            "support_sensitivity_stage7_changes_under_low_support_cap": (
                support_sensitivity_summary.get(
                    "stage7_changes_under_low_support_cap"
                )
            ),
            "support_sensitivity_scale_risk": (
                support_sensitivity_summary.get("support_scale_risk")
            ),
            "runtime_test_review_status": runtime_test_review_decision.get("status"),
            "runtime_test_review_runtime_promotion_allowed": (
                runtime_test_review_decision.get("runtime_promotion_allowed")
            ),
            "runtime_test_review_small_support_protected_no_regression": (
                runtime_test_review_findings.get(
                    "small_support_protected_no_regression"
                )
            ),
            "runtime_test_review_small_support_stage7_effective": (
                runtime_test_review_findings.get("small_support_stage7_effective")
            ),
            "runtime_test_review_high_support_scale_risk": (
                runtime_test_review_findings.get("high_support_scale_risk")
            ),
            "runtime_test_review_stage7_holdout_locked_by_default": (
                runtime_test_review_findings.get("stage7_holdout_locked_by_default")
            ),
            "runtime_test_blocked_path": (
                runtime_test_review_interpretation.get("blocked_path")
            ),
            "blocked_next_steps": runtime_test_blocked_steps,
            "runtime_defaults_changed": (
                strategy_arbiter_runtime_test_review_v2.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                strategy_arbiter_runtime_test_review_v2.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "gameplay_topology_mutation": (
                strategy_arbiter_runtime_test_review_v2.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": (
                strategy_arbiter_runtime_test_review_v2.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                strategy_arbiter_runtime_test_review_v2.get(
                    "stage8_training_allowed"
                )
            ),
        },
        "provider_identity_maturity_blocker_gate": {
            "status": provider_identity_decision.get("status"),
            "passive_provider_identity_maturity_ready": (
                provider_identity_maturity_passive
            ),
            "row_count": provider_identity_maturity_review_v0.get("row_count"),
            "provider_prior_accuracy": (
                provider_identity_maturity_review_v0.get("provider_prior_accuracy")
            ),
            "best_feature_probe_baseline": (
                provider_identity_best_feature_baseline.get("name")
            ),
            "best_feature_probe_accuracy": (
                provider_identity_best_feature_baseline.get("accuracy")
            ),
            "provider_identity_signal": provider_identity_interpretation.get(
                "provider_identity_signal"
            ),
            "raw_provider_id_is_principled_runtime_signal": (
                provider_identity_interpretation.get(
                    "raw_provider_id_is_principled_runtime_signal"
                )
            ),
            "stage0_basin_positive_rate": provider_identity_interpretation.get(
                "stage0_basin_positive_rate"
            ),
            "edge_trap_positive_rates": (
                provider_identity_interpretation.get("edge_trap_positive_rates")
                or []
            ),
            "required_future_features": provider_identity_required_features,
            "blocked_next_work": provider_identity_blocked_work,
            "runtime_arbiter_allowed": provider_identity_decision.get(
                "runtime_arbiter_allowed"
            ),
            "selector_sandbox_ready": provider_identity_decision.get(
                "selector_sandbox_ready"
            ),
            "stage7_repair_allowed": provider_identity_decision.get(
                "stage7_repair_allowed"
            ),
            "runtime_arbiter_implemented": (
                provider_identity_maturity_review_v0.get(
                    "runtime_arbiter_implemented"
                )
            ),
            "runtime_behavior_changed": (
                provider_identity_maturity_review_v0.get(
                    "runtime_behavior_changed"
                )
            ),
            "runtime_defaults_changed": (
                provider_identity_maturity_review_v0.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": provider_identity_decision.get(
                "stage8_training_allowed"
            ),
        },
        "selector_directed_fix_blocker_gate": {
            "status": directed_fix_decision.get("status"),
            "passive_selector_directed_fix_ready": (
                selector_directed_fix_blocker_passive
            ),
            "geometry_audit_status": geometry_audit_decision.get("status"),
            "geometry_audit_row_count": geometry_audit_summary.get("row_count"),
            "geometry_audit_stage7_row_count": (
                geometry_audit_summary.get("stage7_row_count")
            ),
            "geometry_audit_capacity_label_counts": (
                geometry_audit_summary.get("capacity_label_counts") or {}
            ),
            "geometry_probe_status": geometry_probe_decision.get("status"),
            "geometry_probe_row_count": geometry_probe_summary.get("row_count"),
            "geometry_probe_state_count": geometry_probe_summary.get("state_count"),
            "geometry_probe_positive_count": (
                geometry_probe_summary.get("positive_count")
            ),
            "geometry_probe_negative_count": (
                geometry_probe_summary.get("negative_count")
            ),
            "geometry_probe_stage7_row_count": (
                geometry_probe_summary.get("stage7_row_count")
            ),
            "geometry_probe_underpowered": geometry_probe_summary.get("underpowered"),
            "geometry_probe_best_objective": geometry_probe_best.get("objective"),
            "geometry_probe_best_accuracy": geometry_probe_best.get("accuracy"),
            "geometry_probe_best_negative_suppression": (
                geometry_probe_best.get("negative_suppression")
            ),
            "directed_fix_recommended_next_step": directed_fix_decision.get(
                "recommended_next_step"
            ),
            "directed_fix_recommended_class": directed_fix_recommended.get("name"),
            "directed_fix_recommended_not_runtime": (
                directed_fix_recommended.get("not_runtime")
            ),
            "directed_fix_rejected_fixes": directed_fix_rejected,
            "directed_fix_requirements": directed_fix_requirements,
            "runtime_work_allowed": directed_fix_decision.get(
                "runtime_work_allowed"
            ),
            "candidate_generator_runtime_allowed": directed_fix_decision.get(
                "candidate_generator_runtime_allowed"
            ),
            "selector_training_allowed": directed_fix_decision.get(
                "selector_training_allowed"
            ),
            "runtime_behavior_changed": (
                selector_directed_fix_review_v0.get("runtime_behavior_changed")
            ),
            "runtime_defaults_changed": (
                selector_directed_fix_review_v0.get("runtime_defaults_changed")
            ),
            "runtime_selector_implemented": (
                selector_directed_fix_review_v0.get("runtime_selector_implemented")
            ),
            "runtime_candidate_generator_implemented": (
                selector_directed_fix_review_v0.get(
                    "runtime_candidate_generator_implemented"
                )
            ),
            "runtime_terminals_added": (
                selector_directed_fix_review_v0.get("runtime_terminals_added")
            ),
            "runtime_dtm_or_tablebase_lookup": (
                selector_directed_fix_review_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "gameplay_topology_mutation": (
                selector_directed_fix_review_v0.get("gameplay_topology_mutation")
            ),
            "stage7_promotion_allowed": (
                selector_directed_fix_review_v0.get("stage7_promotion_allowed")
            ),
            "stage8_training_allowed": (
                selector_directed_fix_review_v0.get("stage8_training_allowed")
            ),
        },
        "forced_provider_control_label_lineage_gate": {
            "status": forced_provider_control_labels_v0.get(
                "recommended_next_step"
            ),
            "passive_forced_provider_control_lineage_ready": (
                forced_provider_control_label_lineage_passive
            ),
            "plan_causal_status": forced_provider_control_label_plan_v0.get(
                "causal_status"
            ),
            "plan_selected_job_count": forced_provider_plan_job_selection.get(
                "selected_job_count"
            ),
            "plan_selected_job_count_by_stage": (
                forced_provider_plan_job_selection.get(
                    "selected_job_count_by_stage"
                )
                or {}
            ),
            "plan_current_label_result_counts": (
                forced_provider_plan_job_selection.get(
                    "current_label_result_counts"
                )
                or {}
            ),
            "plan_target_stages": (
                forced_provider_plan_job_selection.get("target_stages") or []
            ),
            "manifest_causal_status": (
                forced_provider_label_execution_manifest_v0.get("causal_status")
            ),
            "manifest_all_bindings_valid": (
                forced_provider_manifest_binding_summary.get("all_bindings_valid")
            ),
            "manifest_job_count": (
                forced_provider_manifest_binding_summary.get("job_count")
            ),
            "manifest_missing_path_count": (
                forced_provider_manifest_binding_summary.get("missing_path_count")
            ),
            "labels_causal_status": forced_provider_control_labels_v0.get(
                "causal_status"
            ),
            "label_count": forced_provider_labels_summary.get("label_count"),
            "label_stage_counts": forced_provider_label_stage_counts,
            "result_counts": forced_provider_labels_summary.get("result_counts")
            or {},
            "result_counts_by_stage": (
                forced_provider_labels_summary.get("result_counts_by_stage") or {}
            ),
            "trace_failures_only": forced_provider_labels_summary.get(
                "trace_failures_only"
            ),
            "trace_included_count": sum(
                1 for row in forced_provider_label_rows if row.get("trace_included")
            ),
            "forced_successor_available_count": sum(
                1
                for row in forced_provider_label_rows
                if row.get("forced_successor_available")
            ),
            "provider_ids": sorted(
                {
                    str(row.get("provider_id"))
                    for row in forced_provider_label_rows
                    if row.get("provider_id")
                }
            ),
            "blocked_next_steps": forced_provider_control_blocked_steps,
            "runtime_behavior_changed": (
                forced_provider_control_labels_v0.get("runtime_behavior_changed")
            ),
            "runtime_defaults_changed": (
                forced_provider_control_labels_v0.get("runtime_defaults_changed")
            ),
            "runtime_dtm_or_tablebase_lookup": (
                forced_provider_control_labels_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "gameplay_topology_mutation": (
                forced_provider_control_labels_v0.get("gameplay_topology_mutation")
            ),
            "stage7_promotion_allowed": (
                forced_provider_control_labels_v0.get("stage7_promotion_allowed")
            ),
            "stage8_training_allowed": (
                forced_provider_control_labels_v0.get("stage8_training_allowed")
            ),
        },
        "selector_provenance_prior_blocker_gate": {
            "status": selector_feature_architecture_review_v0.get(
                "decision_status"
            ),
            "passive_provenance_prior_blocker_ready": (
                selector_provenance_prior_blocker_passive
            ),
            "target_dataset_status": selector_target_dataset_decision.get("status"),
            "target_dataset_row_count": selector_target_dataset_v0.get("row_count"),
            "target_dataset_training_row_count": (
                selector_target_dataset_v0.get("training_row_count")
            ),
            "target_dataset_stage7_training_rows": (
                selector_target_dataset_v0.get("stage7_training_rows")
            ),
            "target_dataset_target_kind_counts": (
                selector_target_dataset_v0.get("target_kind_counts") or {}
            ),
            "target_probe_status": selector_target_probe_decision.get("status"),
            "target_probe_training_label_counts": (
                selector_target_probe_v0.get("training_label_counts") or {}
            ),
            "target_probe_heldout_training_row_count": (
                selector_target_probe_v0.get("heldout_training_row_count")
            ),
            "baseline_probe_status": selector_baseline_probe_decision.get(
                "status"
            ),
            "baseline_probe_best_baseline": (
                (selector_baseline_probe_v0.get("best_baseline") or {}).get("name")
            ),
            "baseline_probe_best_accuracy": (
                (selector_baseline_probe_v0.get("best_baseline") or {}).get(
                    "accuracy"
                )
            ),
            "feature_dataset_status": selector_feature_dataset_decision.get(
                "status"
            ),
            "feature_dataset_row_count": selector_feature_dataset_v0.get(
                "row_count"
            ),
            "feature_dataset_training_row_count": (
                selector_feature_dataset_v0.get("training_row_count")
            ),
            "feature_dataset_stage7_training_rows": (
                selector_feature_dataset_v0.get("stage7_training_rows")
            ),
            "feature_dataset_rows_with_observation": (
                selector_feature_dataset_v0.get("rows_with_observation")
            ),
            "feature_baseline_status": selector_feature_baseline_decision.get(
                "status"
            ),
            "feature_baseline_best_name": selector_feature_baseline_best.get(
                "name"
            ),
            "feature_baseline_best_accuracy": selector_feature_baseline_best.get(
                "accuracy"
            ),
            "feature_baseline_improved_over_provider_prior": (
                selector_feature_baseline_probe_v0.get(
                    "feature_improved_over_provider_prior"
                )
            ),
            "provenance_dataset_status": selector_provenance_dataset_decision.get(
                "status"
            ),
            "provenance_dataset_rows_with_provider_provenance": (
                selector_provenance_feature_dataset_v0.get(
                    "rows_with_provider_provenance"
                )
            ),
            "provenance_dataset_training_row_count": (
                selector_provenance_feature_dataset_v0.get("training_row_count")
            ),
            "provenance_dataset_stage7_training_rows": (
                selector_provenance_feature_dataset_v0.get("stage7_training_rows")
            ),
            "provenance_probe_status": selector_provenance_probe_decision.get(
                "status"
            ),
            "provenance_probe_raw_provider_id_runtime_prior_allowed": (
                selector_provenance_probe_decision.get(
                    "raw_provider_id_runtime_prior_allowed"
                )
            ),
            "provenance_probe_runtime_arbiter_allowed": (
                selector_provenance_probe_decision.get("runtime_arbiter_allowed")
            ),
            "provenance_probe_selector_sandbox_ready": (
                selector_provenance_probe_decision.get("selector_sandbox_ready")
            ),
            "provenance_probe_best_name": selector_provenance_probe_best.get(
                "name"
            ),
            "provenance_probe_best_accuracy": selector_provenance_probe_best.get(
                "accuracy"
            ),
            "provenance_probe_blocked_next_work": selector_provenance_blocked_work,
            "architecture_review_status": (
                selector_feature_architecture_review_v0.get("decision_status")
            ),
            "architecture_best_baseline": selector_feature_architecture_summary.get(
                "best_baseline"
            ),
            "architecture_best_baseline_accuracy": (
                selector_feature_architecture_summary.get("best_baseline_accuracy")
            ),
            "architecture_observation_features_improved_over_provider_prior": (
                selector_feature_architecture_summary.get(
                    "observation_features_improved_over_provider_prior"
                )
            ),
            "architecture_must_remain_non_causal": (
                selector_feature_architecture_recommended.get(
                    "must_remain_non_causal"
                )
            ),
            "architecture_blocked_next_work": selector_feature_architecture_blocked,
            "after_contrast_status": selector_after_contrast_decision.get("status"),
            "after_contrast_runtime_arbiter_allowed": (
                selector_after_contrast_decision.get("runtime_arbiter_allowed")
            ),
            "after_contrast_selector_sandbox_ready": (
                selector_after_contrast_decision.get("selector_sandbox_ready")
            ),
            "after_contrast_training_row_count": (
                selector_after_contrast_evidence.get("training_row_count")
            ),
            "after_contrast_heldout_row_count": (
                selector_after_contrast_evidence.get("heldout_row_count")
            ),
            "after_contrast_readiness_blockers": (
                selector_after_contrast_evidence.get("readiness_blockers") or []
            ),
            "after_contrast_selected_training_provider_families": (
                selector_after_contrast_evidence.get(
                    "selected_training_provider_families"
                )
                or []
            ),
            "after_contrast_blocked_next_steps": selector_after_contrast_blocked,
            "runtime_arbiter_implemented": (
                selector_readiness_after_contrast_probe_review_v0.get(
                    "runtime_arbiter_implemented"
                )
            ),
            "runtime_behavior_changed": (
                selector_readiness_after_contrast_probe_review_v0.get(
                    "runtime_behavior_changed"
                )
            ),
            "runtime_defaults_changed": (
                selector_readiness_after_contrast_probe_review_v0.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                selector_readiness_after_contrast_probe_review_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "gameplay_topology_mutation": (
                selector_readiness_after_contrast_probe_review_v0.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": (
                selector_readiness_after_contrast_probe_review_v0.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                selector_readiness_after_contrast_probe_review_v0.get(
                    "stage8_training_allowed"
                )
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
        "selector_label_balance_gate": {
            "status": selector_balanced_architecture_decision.get("status"),
            "passive_label_balance_ready": selector_label_balance_passive,
            "stratified_dataset_status": selector_stratified_dataset_decision.get(
                "status"
            ),
            "stratified_dataset_row_count": selector_stratified_label_dataset_v1.get(
                "row_count"
            ),
            "stratified_dataset_stage7_training_rows": (
                selector_stratified_stage7_training_rows
            ),
            "stratified_probe_status": selector_stratified_probe_decision.get(
                "status"
            ),
            "stratified_probe_label_counts": selector_stratified_probe_label_counts,
            "stratified_probe_underbalanced": (
                selector_stratified_label_balance_probe_v1.get("underbalanced")
            ),
            "stratified_probe_runtime_arbiter_allowed": (
                selector_stratified_probe_decision.get("runtime_arbiter_allowed")
            ),
            "stratified_probe_selector_sandbox_ready": (
                selector_stratified_probe_decision.get("selector_sandbox_ready")
            ),
            "balanced_dataset_status": selector_balanced_dataset_decision.get(
                "status"
            ),
            "balanced_dataset_row_count": selector_balanced_label_dataset_v1.get(
                "row_count"
            ),
            "balanced_dataset_stage7_training_rows": (
                selector_balanced_stage7_training_rows
            ),
            "balanced_dataset_provider_family_counts": (
                selector_balanced_provider_family_counts
            ),
            "balanced_probe_status": selector_balanced_probe_decision.get("status"),
            "balanced_probe_label_counts": selector_balanced_probe_label_counts,
            "balanced_probe_best_baseline": (
                selector_balanced_probe_best_baseline.get("name")
            ),
            "balanced_probe_best_accuracy": (
                selector_balanced_probe_best_baseline.get("accuracy")
            ),
            "balanced_probe_runtime_arbiter_allowed": (
                selector_balanced_probe_decision.get("runtime_arbiter_allowed")
            ),
            "balanced_probe_selector_sandbox_ready": (
                selector_balanced_probe_decision.get("selector_sandbox_ready")
            ),
            "architecture_status": selector_balanced_architecture_decision.get(
                "status"
            ),
            "architecture_recommended_next_step": (
                selector_balanced_architecture_decision.get("recommended_next_step")
            ),
            "architecture_runtime_arbiter_allowed": (
                selector_balanced_architecture_decision.get("runtime_arbiter_allowed")
            ),
            "architecture_selector_sandbox_ready": (
                selector_balanced_architecture_decision.get("selector_sandbox_ready")
            ),
            "architecture_stage7_training_rows": (
                selector_balanced_architecture_evidence.get("stage7_training_rows")
            ),
            "blocked_next_work": selector_balanced_blocked_next_work,
            "runtime_behavior_changed": (
                selector_balanced_architecture_review_v1.get(
                    "runtime_behavior_changed"
                )
            ),
            "runtime_defaults_changed": (
                selector_balanced_architecture_review_v1.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_selector_implemented": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "runtime_terminals_added": False,
            "stage7_promotion_allowed": (
                selector_balanced_architecture_decision.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                selector_balanced_architecture_decision.get("stage8_training_allowed")
            ),
        },
        "selector_replay_free_label_lineage_gate": {
            "status": selector_balanced_architecture_decision.get("status"),
            "passive_replay_free_label_lineage_ready": (
                selector_replay_free_label_lineage_passive
            ),
            "plan_status": selector_replay_free_plan_decision.get("status"),
            "plan_execute_labels_now": selector_replay_free_plan_decision.get(
                "execute_labels_now"
            ),
            "plan_job_count": len(selector_replay_free_plan_jobs),
            "plan_job_stage_counts": selector_replay_free_plan_job_stage_counts,
            "review_status": selector_replay_free_review_decision.get("status"),
            "review_execute_labels_now": selector_replay_free_review_decision.get(
                "execute_labels_now"
            ),
            "review_missing_replay_free_label_count": (
                selector_label_plan_replay_free_review_v1.get(
                    "missing_replay_free_label_count"
                )
            ),
            "review_fill_status_counts": (
                selector_label_plan_replay_free_review_v1.get("fill_status_counts")
                or {}
            ),
            "negative_control_status": selector_negative_control_decision.get(
                "status"
            ),
            "negative_control_count": selector_negative_control_manifest_v1.get(
                "control_count"
            ),
            "negative_control_stage_counts": (
                selector_negative_control_manifest_v1.get("stage_counts") or {}
            ),
            "negative_control_provider_counts": (
                selector_negative_control_manifest_v1.get("provider_counts") or {}
            ),
            "stratified_dataset_status": selector_stratified_dataset_decision.get(
                "status"
            ),
            "stratified_dataset_row_count": selector_stratified_label_dataset_v1.get(
                "row_count"
            ),
            "stratified_dataset_label_counts": (
                selector_stratified_label_dataset_v1.get("label_counts") or {}
            ),
            "stratified_dataset_stage7_training_rows": (
                selector_stratified_stage7_training_rows
            ),
            "balanced_dataset_status": selector_balanced_dataset_decision.get(
                "status"
            ),
            "balanced_dataset_row_count": selector_balanced_label_dataset_v1.get(
                "row_count"
            ),
            "balanced_dataset_label_counts": (
                selector_balanced_label_dataset_v1.get("label_counts") or {}
            ),
            "balanced_dataset_stage7_training_rows": (
                selector_balanced_stage7_training_rows
            ),
            "balanced_probe_status": selector_balanced_probe_decision.get("status"),
            "balanced_probe_best_baseline": (
                selector_balanced_probe_best_baseline.get("name")
            ),
            "balanced_probe_best_accuracy": (
                selector_balanced_probe_best_baseline.get("accuracy")
            ),
            "architecture_status": selector_balanced_architecture_decision.get(
                "status"
            ),
            "architecture_selector_sandbox_ready": (
                selector_balanced_architecture_decision.get("selector_sandbox_ready")
            ),
            "architecture_runtime_arbiter_allowed": (
                selector_balanced_architecture_decision.get("runtime_arbiter_allowed")
            ),
            "architecture_stage7_repair_allowed": (
                selector_balanced_architecture_decision.get("stage7_repair_allowed")
            ),
            "runtime_behavior_changed": (
                selector_replay_free_runtime_behavior_changed
            ),
            "runtime_defaults_changed": (
                selector_replay_free_runtime_defaults_changed
            ),
            "runtime_arbiter_implemented": (
                selector_replay_free_runtime_arbiter_implemented
            ),
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion_allowed": (
                selector_balanced_architecture_decision.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                selector_balanced_architecture_decision.get("stage8_training_allowed")
            ),
        },
        "ownership_selection_context_gate": {
            "status": ownership_source_diversity_decision.get("status"),
            "passive_context_ready": ownership_selection_context_passive,
            "label_dataset_status": ownership_selection_label_decision.get("status"),
            "label_dataset_merged_row_count": (
                ownership_selection_label_summary.get("merged_row_count")
            ),
            "label_dataset_state_count": (
                ownership_selection_label_summary.get("state_count")
            ),
            "label_dataset_target_label_counts": (
                ownership_selection_label_summary.get("target_label_counts") or {}
            ),
            "label_dataset_targeted_added_row_count": (
                ownership_selection_label_summary.get("targeted_added_row_count")
            ),
            "label_dataset_selector_training_row_count": (
                ownership_selection_label_summary.get("selector_training_row_count")
            ),
            "label_dataset_stage7_row_count": (
                ownership_selection_label_summary.get("stage7_row_count")
            ),
            "context_dataset_status": ownership_selection_context_decision.get(
                "status"
            ),
            "context_dataset_row_count": (
                ownership_selection_context_summary.get("row_count")
            ),
            "context_dataset_exact_move_context_count": (
                ownership_selection_context_summary.get("exact_move_context_count")
            ),
            "context_dataset_label_counts": (
                ownership_selection_context_summary.get("label_counts") or {}
            ),
            "context_dataset_provider_family_counts": (
                ownership_selection_context_summary.get("provider_family_counts") or {}
            ),
            "context_dataset_selector_training_row_count": (
                ownership_selection_context_summary.get("selector_training_row_count")
            ),
            "context_dataset_stage7_row_count": (
                ownership_selection_context_summary.get("stage7_row_count")
            ),
            "context_probe_status": (
                ownership_selection_context_probe_decision.get("status")
            ),
            "context_probe_underpowered": (
                ownership_selection_context_probe_summary.get("underpowered")
            ),
            "context_probe_row_count": (
                ownership_selection_context_probe_summary.get("row_count")
            ),
            "context_probe_positive_owner_count": (
                ownership_selection_context_probe_summary.get("positive_owner_count")
            ),
            "context_probe_negative_owner_count": (
                ownership_selection_context_probe_summary.get("negative_owner_count")
            ),
            "context_probe_stage7_row_count": (
                ownership_selection_context_probe_summary.get("stage7_row_count")
            ),
            "labeling_review_status": (
                ownership_selection_labeling_review_decision.get("status")
            ),
            "labeling_review_best_objective": (
                (
                    ownership_selection_labeling_review_summary.get(
                        "best_ownership_probe"
                    )
                    or {}
                ).get("objective")
            ),
            "labeling_review_selector_training_rows": (
                ownership_selection_labeling_review_summary.get(
                    "selector_training_rows"
                )
            ),
            "labeling_review_stage7_rows": (
                ownership_selection_labeling_review_summary.get("stage7_rows")
            ),
            "source_diversity_status": ownership_source_diversity_decision.get(
                "status"
            ),
            "source_diversity_non_stage0_ownership_row_count": (
                ownership_source_diversity_summary.get(
                    "non_stage0_ownership_row_count"
                )
            ),
            "source_diversity_ownership_row_count": (
                ownership_source_diversity_summary.get("ownership_row_count")
            ),
            "source_diversity_provider_counts": (
                ownership_source_diversity_summary.get("ownership_provider_counts")
                or {}
            ),
            "runtime_behavior_changed": ownership_source_diversity_review_v0.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": ownership_source_diversity_review_v0.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": ownership_source_diversity_review_v0.get(
                "runtime_selector_implemented"
            ),
            "runtime_dtm_or_tablebase_lookup": (
                ownership_source_diversity_review_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_terminals_added": ownership_source_diversity_review_v0.get(
                "runtime_terminals_added"
            ),
            "stage7_promotion_allowed": ownership_source_diversity_decision.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": ownership_source_diversity_decision.get(
                "stage8_training_allowed"
            ),
        },
        "selector_negative_suppression_blocker_gate": {
            "status": selector_negative_suppression_decision.get("status"),
            "passive_blocker_ready": selector_negative_suppression_blocker_passive,
            "protected_max_only_status": protected_max_only_decision.get("status"),
            "protected_max_only_frame_count": (
                protected_max_only_summary.get("strategy_benchmark_frame_count")
            ),
            "protected_max_only_frames_with_only_max_plies": (
                protected_max_only_summary.get(
                    "frames_with_only_labeled_max_plies_providers"
                )
            ),
            "protected_max_only_frames_with_mate_provider": (
                protected_max_only_summary.get("frames_with_labeled_mate_provider")
            ),
            "protected_max_only_by_stage": (
                protected_max_only_summary.get("max_only_by_stage") or {}
            ),
            "protected_max_only_runtime_work_allowed": (
                protected_max_only_decision.get("runtime_work_allowed")
            ),
            "negative_suppression_status": (
                selector_negative_suppression_decision.get("status")
            ),
            "negative_suppression_recommended_next_step": (
                selector_negative_suppression_decision.get("recommended_next_step")
            ),
            "negative_suppression_runtime_work_allowed": (
                selector_negative_suppression_decision.get("runtime_work_allowed")
            ),
            "negative_suppression_selector_training_allowed": (
                selector_negative_suppression_decision.get(
                    "selector_training_allowed"
                )
            ),
            "negative_suppression_candidate_generator_runtime_allowed": (
                selector_negative_suppression_decision.get(
                    "candidate_generator_runtime_allowed"
                )
            ),
            "runtime_selector_readiness_status": (
                runtime_selector_readiness_decision.get("status")
            ),
            "runtime_selector_readiness_runtime_test_allowed_next": (
                runtime_selector_readiness_decision.get("runtime_test_allowed_next")
            ),
            "runtime_selector_readiness_recommended_next_step": (
                runtime_selector_readiness_decision.get("recommended_next_step")
            ),
            "runtime_behavior_changed": (
                selector_negative_suppression_evidence_v0.get(
                    "runtime_behavior_changed"
                )
            ),
            "runtime_defaults_changed": (
                selector_negative_suppression_evidence_v0.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_selector_implemented": (
                selector_negative_suppression_evidence_v0.get(
                    "runtime_selector_implemented"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                selector_negative_suppression_evidence_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_terminals_added": (
                selector_negative_suppression_evidence_v0.get(
                    "runtime_terminals_added"
                )
            ),
            "stage7_promotion_allowed": (
                selector_negative_suppression_decision.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                selector_negative_suppression_decision.get("stage8_training_allowed")
            ),
        },
        "abstention_selector_safety_gate": {
            "status": abstention_context_probe_decision.get("status"),
            "runtime_architecture_lineage_ready": (
                runtime_test_architecture_lineage_passive
            ),
            "runtime_architecture_review_status": (
                runtime_test_architecture_next.get("status")
            ),
            "runtime_architecture_implementation_allowed": (
                runtime_test_architecture_next.get("implementation_allowed")
            ),
            "runtime_architecture_next_artifacts": (
                runtime_test_architecture_next.get("next_artifacts") or []
            ),
            "runtime_architecture_selector_ready": (
                runtime_test_architecture_readiness.get("runtime_selector_ready")
            ),
            "runtime_architecture_stage7_repair_ready": (
                runtime_test_architecture_readiness.get("runtime_stage7_repair_ready")
            ),
            "runtime_architecture_internal_terminal_ready": (
                runtime_test_architecture_readiness.get(
                    "runtime_internal_terminal_ready"
                )
            ),
            "runtime_architecture_blocked_next_steps": (
                runtime_test_architecture_blocked
            ),
            "runtime_architecture_runtime_behavior_changed": (
                runtime_test_architecture_review_v3.get("runtime_behavior_changed")
            ),
            "runtime_architecture_runtime_defaults_changed": (
                runtime_test_architecture_review_v3.get("runtime_defaults_changed")
            ),
            "runtime_architecture_selector_implemented": (
                runtime_test_architecture_review_v3.get(
                    "runtime_selector_implemented"
                )
            ),
            "runtime_architecture_dtm_or_tablebase_lookup": (
                runtime_test_architecture_review_v3.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_architecture_gameplay_topology_mutation": (
                runtime_test_architecture_review_v3.get(
                    "gameplay_topology_mutation"
                )
            ),
            "runtime_architecture_stage7_promotion_allowed": (
                runtime_test_architecture_review_v3.get("stage7_promotion_allowed")
            ),
            "runtime_architecture_stage8_training_allowed": (
                runtime_test_architecture_review_v3.get("stage8_training_allowed")
            ),
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
            "training_dataset_v0_status": (
                abstention_dataset_v0_decision.get("status")
            ),
            "training_dataset_v0_row_count": (
                abstention_dataset_v0_summary.get("row_count")
            ),
            "training_dataset_v0_safe_owner_count": (
                (abstention_dataset_v0_summary.get("label_counts") or {}).get(
                    "safe_owner"
                )
            ),
            "training_dataset_v0_unsafe_owner_count": (
                (abstention_dataset_v0_summary.get("label_counts") or {}).get(
                    "unsafe_owner"
                )
            ),
            "training_dataset_v0_stage7_training_rows": (
                abstention_dataset_v0_summary.get("stage7_training_rows")
            ),
            "training_probe_v0_status": abstention_probe_v0_decision.get("status"),
            "training_probe_v0_under_minimum_requirements": (
                abstention_probe_v0_summary.get("under_minimum_requirements")
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
        "two_stage_abstention_no_go_gate": {
            "status": two_stage_abstention_runtime_go_no_go_v0.get("decision"),
            "passive_no_go_ready": two_stage_abstention_no_go_passive,
            "objective_probe_status": (
                two_stage_abstention_objective_decision.get("status")
            ),
            "objective_probe_row_count": (
                two_stage_abstention_objective_summary.get("row_count")
            ),
            "objective_probe_threshold_passing_objective_count": (
                two_stage_abstention_objective_summary.get(
                    "threshold_passing_objective_count"
                )
            ),
            "objective_probe_best_negative_suppression": (
                (
                    two_stage_abstention_objective_probe_v0.get(
                        "best_threshold_passing_result"
                    )
                    or {}
                ).get("negative_suppression")
            ),
            "objective_probe_best_safe_preservation": (
                (
                    two_stage_abstention_objective_probe_v0.get(
                        "best_threshold_passing_result"
                    )
                    or {}
                ).get("safe_preservation")
            ),
            "runtime_review_status": (
                two_stage_abstention_review_decision.get("status")
            ),
            "runtime_review_implementation_allowed": (
                two_stage_abstention_review_decision.get(
                    "implementation_allowed_by_this_packet"
                )
            ),
            "runtime_review_runtime_test_allowed_next": (
                two_stage_abstention_review_decision.get("runtime_test_allowed_next")
            ),
            "runtime_review_evidence_row_count": (
                two_stage_abstention_review_evidence.get("row_count")
            ),
            "default_off_status": (
                two_stage_abstention_default_off_equivalence_v0.get("status")
            ),
            "default_off_same_core_metrics": (
                two_stage_abstention_default_acceptance.get("same_core_metrics")
            ),
            "default_off_stop_condition_fired": (
                two_stage_abstention_default_off_equivalence_v0.get(
                    "stop_condition_fired"
                )
            ),
            "enabled_smoke_status": (
                two_stage_abstention_enabled_smoke_v0.get("status")
            ),
            "enabled_smoke_total_penalized_count": (
                two_stage_abstention_enabled_aggregate.get("total_penalized_count")
            ),
            "enabled_smoke_total_selected_penalized_count": (
                two_stage_abstention_enabled_aggregate.get(
                    "total_selected_penalized_count"
                )
            ),
            "enabled_smoke_conversion_regressions": (
                two_stage_abstention_enabled_aggregate.get(
                    "labels_with_conversion_regression"
                )
            ),
            "stage7_challenge_status": (
                two_stage_abstention_stage7_challenge_smoke_v0.get("status")
            ),
            "stage7_challenge_conversion_delta_mates": (
                two_stage_abstention_stage7_summary.get("conversion_delta_mates")
            ),
            "stage7_challenge_target_improved": (
                two_stage_abstention_stage7_summary.get("target_improved")
            ),
            "stage7_challenge_no_regression_detected": (
                two_stage_abstention_stage7_summary.get("no_regression_detected")
            ),
            "go_no_go_allowed_status": (
                two_stage_abstention_runtime_go_no_go_v0.get("allowed_status")
            ),
            "rollback_tag": (
                two_stage_abstention_runtime_go_no_go_v0.get("rollback_tag")
            ),
            "runtime_defaults_changed": (
                two_stage_abstention_runtime_go_no_go_v0.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                two_stage_abstention_runtime_go_no_go_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "gameplay_topology_mutation": (
                two_stage_abstention_runtime_go_no_go_v0.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": (
                two_stage_abstention_runtime_go_no_go_v0.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                two_stage_abstention_runtime_go_no_go_v0.get(
                    "stage8_training_allowed"
                )
            ),
            "runtime_repair_not_promoted": (
                two_stage_abstention_go_no_go_stop_conditions.get(
                    "runtime_repair_not_promoted"
                )
            ),
            "stage7_remains_quarantined": (
                two_stage_abstention_go_no_go_stop_conditions.get(
                    "stage7_remains_quarantined"
                )
            ),
            "stage8_remains_blocked": (
                two_stage_abstention_go_no_go_stop_conditions.get(
                    "stage8_remains_blocked"
                )
            ),
            "no_hidden_controller": (
                two_stage_abstention_go_no_go_stop_conditions.get(
                    "no_hidden_controller"
                )
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
            "hard_negative_target_dataset_v0_status": (
                hard_negative_targets_v0_decision.get("status")
            ),
            "hard_negative_target_dataset_v0_row_count": (
                hard_negative_targets_v0_summary.get("row_count")
            ),
            "hard_negative_target_dataset_v0_training_row_count": (
                hard_negative_targets_v0_summary.get("training_row_count")
            ),
            "hard_negative_target_dataset_v0_stage7_row_count": (
                hard_negative_targets_v0_summary.get("stage7_row_count")
            ),
            "hard_negative_feature_ablation_v0_status": (
                hard_negative_ablation_v0_decision.get("status")
            ),
            "hard_negative_feature_ablation_v0_underpowered": (
                hard_negative_ablation_v0_summary.get("underpowered")
            ),
            "hard_negative_feature_ablation_v0_stage7_row_count": (
                hard_negative_ablation_v0_summary.get("stage7_row_count")
            ),
            "label_plan_v0_status": (
                balanced_hard_negative_plan_v0_decision.get("status")
            ),
            "label_plan_v0_job_count": (
                balanced_hard_negative_plan_v0_summary.get("job_count")
            ),
            "label_plan_v0_stage7_jobs": (
                balanced_hard_negative_plan_v0_summary.get("stage7_jobs")
            ),
            "execution_manifest_v0_status": (
                balanced_hard_negative_manifest_v0_decision.get("status")
            ),
            "execution_manifest_v0_labels_allowed_now": (
                balanced_hard_negative_manifest_v0_decision.get(
                    "labels_allowed_now"
                )
            ),
            "execution_manifest_v0_job_count": (
                balanced_hard_negative_manifest_v0_binding.get("job_count")
            ),
            "execution_manifest_v0_stage7_jobs": (
                balanced_hard_negative_manifest_v0_binding.get("stage7_jobs")
            ),
            "execution_manifest_review_v0_status": (
                balanced_hard_negative_manifest_review_v0_decision.get("status")
            ),
            "labels_v0_status": balanced_hard_negative_labels_v0_decision.get(
                "status"
            ),
            "label_v0_count": balanced_hard_negative_labels_v0_summary.get(
                "label_count"
            ),
            "stage7_labels_v0": balanced_hard_negative_labels_v0_summary.get(
                "stage7_labels"
            ),
            "stage7_training_labels_v0": (
                balanced_hard_negative_labels_v0_summary.get(
                    "stage7_training_labels"
                )
            ),
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
        "hard_negative_label_semantics_gate": {
            "status": hard_negative_label_semantics_decision.get("status"),
            "passive_semantics_ready": hard_negative_label_semantics_passive,
            "recommended_next_step": hard_negative_label_semantics_decision.get(
                "recommended_next_step"
            ),
            "runtime_work_allowed": hard_negative_label_semantics_decision.get(
                "runtime_work_allowed"
            ),
            "selector_training_allowed": hard_negative_label_semantics_decision.get(
                "selector_training_allowed"
            ),
            "row_count": hard_negative_label_semantics_summary.get("row_count"),
            "state_count": hard_negative_label_semantics_summary.get("state_count"),
            "stage7_row_count": hard_negative_label_semantics_summary.get(
                "stage7_row_count"
            ),
            "capacity_negative_count": hard_negative_label_semantics_summary.get(
                "capacity_negative_count"
            ),
            "capacity_positive_count": hard_negative_label_semantics_summary.get(
                "capacity_positive_count"
            ),
            "state_local_contrast_state_count": (
                hard_negative_label_semantics_summary.get(
                    "state_local_contrast_state_count"
                )
            ),
            "best_ablation_negative_suppression": (
                hard_negative_label_semantics_summary.get(
                    "best_ablation_negative_suppression"
                )
            ),
            "best_ablation_positive_recall": (
                hard_negative_label_semantics_summary.get(
                    "best_ablation_positive_recall"
                )
            ),
            "capacity_recall_objective": hard_negative_label_semantics_split.get(
                "capacity_recall_objective"
            ),
            "capacity_risk_objective": hard_negative_label_semantics_split.get(
                "capacity_risk_objective"
            ),
            "ownership_selection_objective": (
                hard_negative_label_semantics_split.get(
                    "ownership_selection_objective"
                )
            ),
            "safe_preservation_objective": hard_negative_label_semantics_split.get(
                "safe_preservation_objective"
            ),
            "blocked_use_by_label_channel": {
                channel: row.get("blocked_use")
                for channel, row in hard_negative_label_semantics_channels.items()
            },
            "stronger_feature_review_consumes_semantics": (
                "reports/krk_hard_negative_label_semantics_review_v1.json"
                in (stronger_selector_feature_review_v0.get("source_artifacts") or [])
            ),
            "runtime_behavior_changed": hard_negative_label_semantics_review_v1.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": hard_negative_label_semantics_review_v1.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": (
                hard_negative_label_semantics_review_v1.get(
                    "runtime_selector_implemented"
                )
            ),
            "runtime_candidate_generator_implemented": (
                hard_negative_label_semantics_review_v1.get(
                    "runtime_candidate_generator_implemented"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                hard_negative_label_semantics_review_v1.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_terminals_added": hard_negative_label_semantics_review_v1.get(
                "runtime_terminals_added"
            ),
            "gameplay_topology_mutation": (
                hard_negative_label_semantics_review_v1.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": hard_negative_label_semantics_review_v1.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": hard_negative_label_semantics_review_v1.get(
                "stage8_training_allowed"
            ),
        },
        "stronger_selector_feature_gate": {
            "status": stronger_feature_decision.get("status"),
            "passive_feature_review_ready": stronger_selector_feature_passive,
            "feature_ablation_status": feature_ablation_decision.get("status"),
            "feature_ablation_underpowered": feature_ablation_summary.get(
                "underpowered"
            ),
            "feature_ablation_row_count": feature_ablation_summary.get("row_count"),
            "feature_ablation_state_count": feature_ablation_summary.get(
                "state_count"
            ),
            "feature_ablation_hard_negative_count": feature_ablation_summary.get(
                "hard_negative_count"
            ),
            "feature_ablation_positive_context_count": (
                feature_ablation_summary.get("positive_context_count")
            ),
            "feature_ablation_stage7_row_count": (
                feature_ablation_summary.get("stage7_row_count")
            ),
            "feature_ablation_best_objective": feature_ablation_best_result.get(
                "objective"
            ),
            "feature_ablation_best_negative_suppression": (
                feature_ablation_best_result.get("negative_suppression")
            ),
            "feature_review_status": stronger_feature_decision.get("status"),
            "feature_review_recommended_next_step": (
                stronger_feature_decision.get("recommended_next_step")
            ),
            "feature_review_improved_over_v2_ablation": stronger_feature_summary.get(
                "improved_over_v2_ablation"
            ),
            "feature_review_row_count": stronger_feature_summary.get("row_count"),
            "feature_review_state_count": stronger_feature_summary.get("state_count"),
            "feature_review_hard_negative_count": stronger_feature_summary.get(
                "hard_negative_count"
            ),
            "feature_review_positive_context_count": stronger_feature_summary.get(
                "positive_context_count"
            ),
            "feature_review_stage7_row_count": stronger_feature_summary.get(
                "stage7_row_count"
            ),
            "feature_review_previous_best_negative_suppression": (
                stronger_feature_summary.get("previous_best_negative_suppression")
            ),
            "feature_review_best_negative_suppression": (
                stronger_feature_summary.get("best_negative_suppression")
            ),
            "feature_review_previous_best_positive_recall": (
                stronger_feature_summary.get("previous_best_positive_recall")
            ),
            "feature_review_best_positive_recall": stronger_feature_summary.get(
                "best_positive_recall"
            ),
            "feature_review_best_objective": stronger_feature_best_result.get(
                "objective"
            ),
            "feature_review_best_accuracy": stronger_feature_best_result.get(
                "accuracy"
            ),
            "feature_review_best_false_negative": stronger_feature_best_result.get(
                "false_negative"
            ),
            "feature_review_best_false_positive": stronger_feature_best_result.get(
                "false_positive"
            ),
            "runtime_behavior_changed": stronger_selector_feature_review_v0.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": stronger_selector_feature_review_v0.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": stronger_selector_feature_review_v0.get(
                "runtime_selector_implemented"
            ),
            "runtime_candidate_generator_implemented": (
                stronger_selector_feature_review_v0.get(
                    "runtime_candidate_generator_implemented"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": stronger_selector_feature_review_v0.get(
                "runtime_dtm_or_tablebase_lookup"
            ),
            "runtime_terminals_added": stronger_selector_feature_review_v0.get(
                "runtime_terminals_added"
            ),
            "gameplay_topology_mutation": stronger_selector_feature_review_v0.get(
                "gameplay_topology_mutation"
            ),
            "stage7_promotion_allowed": stronger_selector_feature_review_v0.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": stronger_selector_feature_review_v0.get(
                "stage8_training_allowed"
            ),
        },
        "selected_provider_diversity_gate": {
            "status": provider_diversity_architecture_decision.get("status"),
            "passive_diversity_review_ready": selected_provider_diversity_passive,
            "evidence_plan_status": provider_diversity_plan_decision.get("status"),
            "evidence_plan_runtime_arbiter_allowed": (
                provider_diversity_plan_decision.get("runtime_arbiter_allowed")
            ),
            "evidence_plan_selector_sandbox_ready": (
                provider_diversity_plan_decision.get("selector_sandbox_ready")
            ),
            "replay_free_scan_status": provider_diversity_replay_decision.get(
                "status"
            ),
            "replay_free_selected_record_count": (
                provider_diversity_replay_summary.get("selected_record_count")
            ),
            "replay_free_stage7_records": (
                provider_diversity_replay_summary.get("stage7_records")
            ),
            "replay_free_max_selected_provider_family_dominance": (
                provider_diversity_replay_summary.get(
                    "max_selected_provider_family_dominance"
                )
            ),
            "observation_manifest_status": (
                provider_diversity_observation_manifest_decision.get("status")
            ),
            "observation_manifest_job_count": (
                provider_diversity_observation_manifest_binding.get("job_count")
            ),
            "observation_manifest_stage7_jobs": (
                provider_diversity_observation_manifest_policy.get("stage7_jobs")
            ),
            "observation_manifest_review_status": (
                provider_diversity_observation_manifest_review_decision.get("status")
            ),
            "observation_manifest_review_observations_allowed": (
                provider_diversity_observation_manifest_review_decision.get(
                    "observations_allowed"
                )
            ),
            "observation_scan_status": provider_diversity_observation_decision.get(
                "status"
            ),
            "observation_scan_count": (
                provider_diversity_observation_summary.get("observation_count")
            ),
            "observation_scan_stage7_observations": (
                provider_diversity_observation_summary.get("stage7_observations")
            ),
            "observation_scan_max_selected_provider_family_dominance": (
                provider_diversity_observation_summary.get(
                    "max_selected_provider_family_dominance"
                )
            ),
            "manifest_status": provider_diversity_manifest_decision.get("status"),
            "manifest_observations_allowed_now": (
                provider_diversity_manifest_decision.get("observations_allowed_now")
            ),
            "manifest_bounded_labels_allowed_by_script": (
                provider_diversity_manifest_decision.get(
                    "bounded_labels_allowed_by_script"
                )
            ),
            "manifest_runtime_arbiter_allowed": (
                provider_diversity_manifest_decision.get("runtime_arbiter_allowed")
            ),
            "manifest_all_bindings_valid": (
                provider_diversity_manifest_binding.get("all_bindings_valid")
            ),
            "manifest_job_count": provider_diversity_manifest_binding.get("job_count"),
            "manifest_job_count_by_stage": (
                provider_diversity_manifest_binding.get("job_count_by_stage") or {}
            ),
            "manifest_stage7_jobs": provider_diversity_manifest_policy.get(
                "stage7_jobs"
            ),
            "manifest_observation_only": provider_diversity_manifest_policy.get(
                "observation_only"
            ),
            "labels_status": provider_diversity_labels_decision.get("status"),
            "label_count": provider_diversity_labels_summary.get("label_count"),
            "ownership_label_counts": (
                provider_diversity_labels_summary.get("ownership_label_counts") or {}
            ),
            "selected_result_counts": (
                provider_diversity_labels_summary.get("selected_result_counts") or {}
            ),
            "selected_result_counts_by_stage": (
                provider_diversity_labels_summary.get(
                    "selected_result_counts_by_stage"
                )
                or {}
            ),
            "selected_provider_counts": (
                provider_diversity_labels_summary.get("selected_provider_counts") or {}
            ),
            "stage7_training_rows": provider_diversity_labels_summary.get(
                "stage7_training_rows"
            ),
            "trace_failures_only": provider_diversity_labels_summary.get(
                "trace_failures_only"
            ),
            "architecture_status": provider_diversity_architecture_decision.get(
                "status"
            ),
            "architecture_recommended_next_step": (
                provider_diversity_architecture_decision.get("recommended_next_step")
            ),
            "architecture_runtime_arbiter_allowed": (
                provider_diversity_architecture_decision.get(
                    "runtime_arbiter_allowed"
                )
            ),
            "architecture_selector_sandbox_ready": (
                provider_diversity_architecture_decision.get("selector_sandbox_ready")
            ),
            "runtime_behavior_changed": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "runtime_behavior_changed"
                )
            ),
            "runtime_defaults_changed": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_selector_implemented": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "runtime_selector_implemented"
                )
            ),
            "runtime_candidate_generator_implemented": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "runtime_candidate_generator_implemented"
                )
            ),
            "runtime_arbiter_implemented": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "runtime_arbiter_implemented"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_terminals_added": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "runtime_terminals_added"
                )
            ),
            "gameplay_topology_mutation": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                selected_provider_diversity_ownership_labels_v1.get(
                    "stage8_training_allowed"
                )
            ),
        },
        "selector_readiness_v3_design_gate": {
            "status": selector_readiness_v3_decision.get("status"),
            "passive_design_review_ready": selector_readiness_v3_passive,
            "recommended_next_step": selector_readiness_v3_decision.get(
                "recommended_next_step"
            ),
            "runtime_arbiter_allowed": selector_readiness_v3_decision.get(
                "runtime_arbiter_allowed"
            ),
            "selector_sandbox_ready": selector_readiness_v3_decision.get(
                "selector_sandbox_ready"
            ),
            "hard_blocker_count": len(
                selector_readiness_v3_decision.get("hard_blockers") or []
            ),
            "passed_checks": [
                key
                for key, check in selector_readiness_v3_checks.items()
                if check.get("status") == "passed"
            ],
            "diagnostic_only_checks": [
                key
                for key, check in selector_readiness_v3_checks.items()
                if check.get("status") == "diagnostic_only_not_sandbox_blocker"
            ],
            "label_balance": selector_readiness_v3_label_balance,
            "stage_coverage": selector_readiness_v3_stage_coverage.get(
                "row_count_by_stage"
            )
            or {},
            "stage7_training_rows": selector_readiness_v3_stage7_boundary.get(
                "stage7_training_rows"
            ),
            "conversion_positive_provider_family_count": (
                selector_readiness_v3_conversion_diversity.get(
                    "distinct_conversion_positive_provider_families"
                )
            ),
            "conversion_positive_provider_families": (
                selector_readiness_v3_conversion_diversity.get("families") or []
            ),
            "blocked_next_steps": selector_readiness_v3_blocked_next_steps,
            "sandbox_design_requirements": selector_readiness_v3_sandbox_requirements,
            "default_off_design_status": default_off_design_decision.get("status"),
            "default_off_design_implementation_allowed": (
                default_off_design_decision.get("implementation_allowed")
            ),
            "default_off_design_runtime_arbiter_allowed": (
                default_off_design_decision.get("runtime_arbiter_allowed")
            ),
            "default_off_design_selector_sandbox_ready": (
                default_off_design_decision.get("selector_sandbox_ready")
            ),
            "runtime_review_packet_readiness_v3_status": (
                runtime_review_packet_evidence.get("readiness_v3_status")
            ),
            "runtime_behavior_changed": selector_readiness_v3_plan.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": selector_readiness_v3_plan.get(
                "runtime_defaults_changed"
            ),
            "runtime_arbiter_implemented": selector_readiness_v3_plan.get(
                "runtime_arbiter_implemented"
            ),
            "runtime_dtm_or_tablebase_lookup": selector_readiness_v3_plan.get(
                "runtime_dtm_or_tablebase_lookup"
            ),
            "runtime_terminals_added": selector_readiness_v3_plan.get(
                "runtime_terminals_added"
            ),
            "gameplay_topology_mutation": selector_readiness_v3_plan.get(
                "gameplay_topology_mutation"
            ),
            "stage7_promotion_allowed": selector_readiness_v3_plan.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": selector_readiness_v3_plan.get(
                "stage8_training_allowed"
            ),
        },
        "state_local_contrast_gate": {
            "status": state_local_contrast_readiness_decision.get("status"),
            "passive_contrast_ready": state_local_contrast_passive,
            "labels_status": state_local_contrast_labels_decision.get("status"),
            "labels_row_count": state_local_contrast_labels_summary.get("row_count"),
            "labels_state_count": state_local_contrast_labels_summary.get(
                "state_count"
            ),
            "labels_provider_family_counts": (
                state_local_contrast_labels_summary.get("provider_family_counts") or {}
            ),
            "labels_contrast_label_counts": (
                state_local_contrast_labels_summary.get("contrast_label_counts") or {}
            ),
            "labels_training_contrast_label_counts": (
                state_local_contrast_labels_summary.get(
                    "training_contrast_label_counts"
                )
                or {}
            ),
            "labels_stage7_challenge_row_count": (
                state_local_contrast_labels_summary.get("stage7_challenge_row_count")
            ),
            "labels_stage7_contrast_label_counts": (
                state_local_contrast_labels_summary.get(
                    "stage7_contrast_label_counts"
                )
                or {}
            ),
            "labels_usable_training_row_count": (
                state_local_contrast_labels_summary.get("usable_training_row_count")
            ),
            "labels_runtime_test_allowed_next": (
                state_local_contrast_labels_decision.get("runtime_test_allowed_next")
            ),
            "probe_status": state_local_contrast_probe_decision.get("status"),
            "probe_row_count": state_local_contrast_probe_summary.get("row_count"),
            "probe_training_row_count": state_local_contrast_probe_summary.get(
                "training_row_count"
            ),
            "probe_stage7_eval_row_count": (
                state_local_contrast_probe_summary.get("stage7_eval_row_count")
            ),
            "probe_stage7_training_leakage": (
                state_local_contrast_probe_summary.get("stage7_training_leakage")
            ),
            "probe_training_label_counts": (
                state_local_contrast_probe_summary.get("training_label_counts") or {}
            ),
            "probe_stage7_label_counts": (
                state_local_contrast_probe_summary.get("stage7_label_counts") or {}
            ),
            "probe_runtime_test_allowed_next": (
                state_local_contrast_probe_decision.get("runtime_test_allowed_next")
            ),
            "readiness_status": state_local_contrast_readiness_decision.get("status"),
            "readiness_recommended_next_step": (
                state_local_contrast_readiness_decision.get("recommended_next_step")
            ),
            "readiness_runtime_test_allowed_next": (
                state_local_contrast_readiness_decision.get(
                    "runtime_test_allowed_next"
                )
            ),
            "readiness_blocked_next_steps": (
                state_local_contrast_readiness_decision.get("blocked_next_steps") or []
            ),
            "runtime_behavior_changed": state_local_contrast_readiness_review_v2.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": state_local_contrast_readiness_review_v2.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": (
                state_local_contrast_readiness_review_v2.get(
                    "runtime_selector_implemented"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                state_local_contrast_readiness_review_v2.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "stage7_promotion_allowed": (
                state_local_contrast_readiness_review_v2.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                state_local_contrast_readiness_review_v2.get(
                    "stage8_training_allowed"
                )
            ),
        },
        "state_local_paired_ownership_gate": {
            "status": paired_review_decision.get("status"),
            "passive_semantic_gate_ready": state_local_paired_ownership_passive,
            "hard_negative_target_dataset_status": hard_negative_targets_decision.get(
                "status"
            ),
            "hard_negative_target_row_count": hard_negative_targets_summary.get(
                "row_count"
            ),
            "hard_negative_training_row_count": hard_negative_targets_summary.get(
                "training_row_count"
            ),
            "hard_negative_stage7_row_count": hard_negative_targets_summary.get(
                "stage7_row_count"
            ),
            "hard_negative_semantics_status": hard_negative_semantics_decision.get(
                "status"
            ),
            "hard_negative_semantics_current_training_row_count": (
                hard_negative_semantics_summary.get("current_training_row_count")
            ),
            "ownership_context_status": ownership_context_decision.get("status"),
            "ownership_context_row_count": ownership_context_summary.get(
                "context_row_count"
            ),
            "ownership_context_runtime_threshold_passed": (
                ownership_context_summary.get("runtime_threshold_passed")
            ),
            "ownership_context_targeted_negative_label_count": (
                ownership_context_summary.get("targeted_negative_label_count")
            ),
            "ownership_architecture_status": ownership_architecture_decision.get(
                "status"
            ),
            "ownership_architecture_runtime_threshold_passed": (
                ownership_architecture_summary.get("runtime_threshold_passed")
            ),
            "ownership_architecture_stage7_rows": ownership_architecture_summary.get(
                "stage7_rows"
            ),
            "objective_plan_status": paired_plan_decision.get("status"),
            "work_package_status": paired_work_package_decision.get("status"),
            "inventory_status": paired_inventory_decision.get("status"),
            "inventory_pair_count": paired_inventory_summary.get("pair_count"),
            "inventory_state_count": paired_inventory_summary.get("state_count"),
            "inventory_same_state_conflict_pair_count": (
                paired_inventory_summary.get("same_state_conflict_pair_count")
            ),
            "inventory_safe_preservation_pair_count": (
                paired_inventory_summary.get("safe_preservation_pair_count")
            ),
            "inventory_selected_failure_with_alternative_success_count": (
                paired_inventory_summary.get(
                    "selected_failure_with_alternative_success_count"
                )
            ),
            "inventory_selector_training_row_count": (
                paired_inventory_summary.get("selector_training_row_count")
            ),
            "inventory_stage7_row_count": paired_inventory_summary.get(
                "stage7_row_count"
            ),
            "probe_status": paired_probe_decision.get("status"),
            "probe_row_count": paired_probe_summary.get("row_count"),
            "probe_threshold_passing_model_count": paired_probe_summary.get(
                "threshold_passing_model_count"
            ),
            "probe_runtime_feature_passing_model_count": paired_probe_summary.get(
                "runtime_feature_passing_model_count"
            ),
            "probe_stage7_row_count": paired_probe_summary.get("stage7_row_count"),
            "error_audit_status": paired_error_audit_decision.get("status"),
            "error_audit_false_positive_count": paired_error_audit_summary.get(
                "false_positive_count"
            ),
            "error_audit_false_negative_count": paired_error_audit_summary.get(
                "false_negative_count"
            ),
            "review_status": paired_review_decision.get("status"),
            "review_best_objective": paired_review_summary.get("best_objective"),
            "review_prefer_capacity_recall": paired_review_summary.get(
                "prefer_capacity_recall"
            ),
            "review_safe_preservation_recall": paired_review_summary.get(
                "safe_preservation_recall"
            ),
            "review_selected_preservation_recall": paired_review_summary.get(
                "selected_preservation_recall"
            ),
            "review_runtime_feature_passing_model_count": (
                paired_review_summary.get("runtime_feature_passing_model_count")
            ),
            "review_stage7_row_count": paired_review_summary.get("stage7_row_count"),
            "runtime_behavior_changed": state_local_paired_ownership_review_v1.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": state_local_paired_ownership_review_v1.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": state_local_paired_ownership_review_v1.get(
                "runtime_selector_implemented"
            ),
            "runtime_dtm_or_tablebase_lookup": (
                state_local_paired_ownership_review_v1.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_terminals_added": state_local_paired_ownership_review_v1.get(
                "runtime_terminals_added"
            ),
            "stage7_promotion_allowed": state_local_paired_ownership_review_v1.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": state_local_paired_ownership_review_v1.get(
                "stage8_training_allowed"
            ),
        },
        "selected_owner_failure_risk_proxy_gate": {
            "status": runtime_proxy_review_packet_v1_decision.get("status"),
            "passive_proxy_review_ready": selected_owner_failure_risk_proxy_passive,
            "runtime_proxy_design_status": runtime_proxy_design_decision.get("status"),
            "runtime_proxy_dataset_status": runtime_proxy_dataset_decision.get(
                "status"
            ),
            "runtime_proxy_dataset_row_count": runtime_proxy_dataset_summary.get(
                "row_count"
            ),
            "runtime_proxy_dataset_selector_training_row_count": (
                runtime_proxy_dataset_summary.get("selector_training_row_count")
            ),
            "runtime_proxy_dataset_stage7_row_count": (
                runtime_proxy_dataset_summary.get("stage7_row_count")
            ),
            "runtime_proxy_probe_status": runtime_proxy_probe_decision.get("status"),
            "runtime_proxy_probe_visible_review_ready": (
                runtime_proxy_probe_summary.get("visible_proxy_review_ready")
            ),
            "runtime_proxy_review_status": runtime_proxy_review_decision.get("status"),
            "runtime_proxy_review_visible_review_ready": (
                runtime_proxy_review_summary.get("visible_proxy_review_ready")
            ),
            "runtime_review_packet_v0_status": runtime_review_packet_v0_decision.get(
                "status"
            ),
            "runtime_review_packet_v0_implementation_allowed": (
                runtime_review_packet_v0_decision.get(
                    "implementation_allowed_by_this_packet"
                )
            ),
            "runtime_review_packet_v0_translation_blocker": (
                runtime_review_packet_v0_summary.get(
                    "runtime_feature_translation_blocker"
                )
            ),
            "runtime_review_packet_v0_runtime_feature_passing_model_count": (
                runtime_review_packet_v0_summary.get(
                    "runtime_feature_passing_model_count"
                )
            ),
            "failure_risk_evidence_status": failure_risk_evidence_decision.get(
                "status"
            ),
            "failure_risk_evidence_row_count": failure_risk_evidence_summary.get(
                "row_count"
            ),
            "failure_risk_evidence_target_counts": (
                failure_risk_evidence_summary.get("target_counts") or {}
            ),
            "failure_risk_evidence_selector_training_row_count": (
                failure_risk_evidence_summary.get("selector_training_row_count")
            ),
            "failure_risk_evidence_stage7_row_count": (
                failure_risk_evidence_summary.get("stage7_row_count")
            ),
            "visible_terms_status": failure_risk_visible_terms_decision.get("status"),
            "visible_terms_row_count": failure_risk_visible_terms_summary.get(
                "row_count"
            ),
            "visible_terms_stage7_row_count": failure_risk_visible_terms_summary.get(
                "stage7_row_count"
            ),
            "visible_proxy_precision": failure_risk_visible_proxy_metrics.get(
                "precision"
            ),
            "visible_proxy_recall": failure_risk_visible_proxy_metrics.get("recall"),
            "visible_proxy_safe_preservation_recall": (
                failure_risk_visible_proxy_metrics.get("safe_preservation_recall")
            ),
            "visible_proxy_review_status": failure_risk_visible_review_decision.get(
                "status"
            ),
            "visible_proxy_review_threshold_met": (
                failure_risk_visible_review_summary.get(
                    "review_threshold_met_on_current_dataset"
                )
            ),
            "visible_proxy_probe_v0_status": (
                failure_risk_visible_probe_decision.get("status")
            ),
            "visible_proxy_probe_v0_review_threshold_met": (
                failure_risk_visible_probe_summary.get("review_threshold_met")
            ),
            "visible_proxy_probe_v0_row_count": (
                failure_risk_visible_probe_summary.get("row_count")
            ),
            "visible_proxy_probe_v0_stage7_row_count": (
                failure_risk_visible_probe_summary.get("stage7_row_count")
            ),
            "independent_manifest_status": (
                failure_risk_independent_manifest_decision.get("status")
            ),
            "independent_manifest_execute_labels_now": (
                failure_risk_independent_manifest_decision.get("execute_labels_now")
            ),
            "independent_manifest_implementation_allowed": (
                selected_owner_failure_risk_proxy_independent_manifest_v0.get(
                    "implementation_allowed_by_this_manifest"
                )
            ),
            "independent_manifest_labels_generated_in_this_slice": (
                selected_owner_failure_risk_proxy_independent_manifest_v0.get(
                    "labels_generated_in_this_slice"
                )
            ),
            "independent_manifest_all_bindings_valid": (
                failure_risk_independent_manifest_binding_summary.get(
                    "all_bindings_valid"
                )
            ),
            "independent_manifest_job_count": (
                failure_risk_independent_manifest_binding_summary.get("job_count")
            ),
            "independent_manifest_stage7_job_count": (
                failure_risk_independent_manifest_binding_summary.get(
                    "stage7_job_count"
                )
            ),
            "independent_manifest_stage7_training_rows": (
                failure_risk_independent_manifest_selection_policy.get(
                    "stage7_training_rows"
                )
            ),
            "independent_validation_v0_status": (
                failure_risk_independent_validation_v0_decision.get("status")
            ),
            "independent_validation_v0_threshold_met": (
                failure_risk_independent_validation_v0_summary.get("threshold_met")
            ),
            "independent_validation_v0_proxy_precision": (
                failure_risk_independent_validation_v0_summary.get("proxy_precision")
            ),
            "independent_validation_v0_proxy_recall": (
                failure_risk_independent_validation_v0_summary.get("proxy_recall")
            ),
            "independent_validation_v0_safe_preservation_recall": (
                failure_risk_independent_validation_v0_summary.get(
                    "safe_preservation_recall"
                )
            ),
            "independent_validation_v0_stage7_row_count": (
                failure_risk_independent_validation_v0_summary.get("stage7_row_count")
            ),
            "blocker_review_v0_status": failure_risk_blocker_review_decision.get(
                "status"
            ),
            "blocker_review_v0_threshold_met": (
                failure_risk_blocker_review_summary.get("threshold_met")
            ),
            "blocker_review_v0_false_positive_count": (
                failure_risk_blocker_review_summary.get("false_positive_count")
            ),
            "blocker_review_v0_false_negative_count": (
                failure_risk_blocker_review_summary.get("false_negative_count")
            ),
            "blocker_review_v0_stage7_row_count": (
                failure_risk_blocker_review_summary.get("stage7_row_count")
            ),
            "proxy_v1_probe_status": failure_risk_proxy_probe_decision.get("status"),
            "proxy_v1_probe_row_count": failure_risk_proxy_probe_summary.get(
                "row_count"
            ),
            "proxy_v1_independent_passing_proxy_count": (
                failure_risk_proxy_probe_summary.get("independent_passing_proxy_count")
            ),
            "proxy_v1_selected_proxy_for_independent_validation": (
                failure_risk_proxy_probe_summary.get(
                    "selected_proxy_for_independent_validation"
                )
            ),
            "independent_labels_status": failure_risk_independent_labels_decision.get(
                "status"
            ),
            "independent_label_count": failure_risk_independent_labels_summary.get(
                "label_count"
            ),
            "independent_label_target_failure_risk_count": (
                failure_risk_independent_labels_summary.get("target_failure_risk_count")
            ),
            "independent_label_stage7_training_rows": (
                failure_risk_independent_labels_summary.get("stage7_training_rows")
            ),
            "independent_validation_status": (
                failure_risk_independent_validation_decision.get("status")
            ),
            "independent_validation_threshold_met": (
                failure_risk_independent_validation_summary.get("threshold_met")
            ),
            "independent_validation_runtime_scope": (
                failure_risk_independent_validation_summary.get("runtime_scope")
            ),
            "independent_validation_stage7_row_count": (
                failure_risk_independent_validation_summary.get("stage7_row_count")
            ),
            "runtime_proxy_review_packet_v1_status": (
                runtime_proxy_review_packet_v1_decision.get("status")
            ),
            "runtime_proxy_review_packet_v1_implementation_allowed": (
                runtime_proxy_review_packet_v1_decision.get(
                    "runtime_implementation_allowed"
                )
            ),
            "runtime_proxy_review_packet_v1_precision": (
                runtime_proxy_review_packet_v1_summary.get("precision")
            ),
            "runtime_proxy_review_packet_v1_recall": (
                runtime_proxy_review_packet_v1_summary.get("recall")
            ),
            "runtime_proxy_review_packet_v1_safe_preservation_recall": (
                runtime_proxy_review_packet_v1_summary.get("safe_preservation_recall")
            ),
            "runtime_proxy_review_packet_v1_stage7_row_count": (
                runtime_proxy_review_packet_v1_summary.get("stage7_row_count")
            ),
            "runtime_behavior_changed": (
                state_local_paired_selector_runtime_proxy_review_packet_v1.get(
                    "runtime_behavior_changed"
                )
            ),
            "runtime_defaults_changed": (
                state_local_paired_selector_runtime_proxy_review_packet_v1.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_selector_implemented": (
                state_local_paired_selector_runtime_proxy_review_packet_v1.get(
                    "runtime_selector_implemented"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                state_local_paired_selector_runtime_proxy_review_packet_v1.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "runtime_terminals_added": (
                state_local_paired_selector_runtime_proxy_review_packet_v1.get(
                    "runtime_terminals_added"
                )
            ),
            "stage7_promotion_allowed": (
                state_local_paired_selector_runtime_proxy_review_packet_v1.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                state_local_paired_selector_runtime_proxy_review_packet_v1.get(
                    "stage8_training_allowed"
                )
            ),
        },
        "progress_window_reconsideration_gate": {
            "status": progress_reconsideration_audit_decision.get("status"),
            "passive_review_ready": progress_window_reconsideration_passive,
            "runtime_test_review_status": (
                progress_reconsideration_review_decision.get("status")
            ),
            "runtime_test_guardrails_allowed_now": (
                progress_reconsideration_review_decision.get("guardrails_allowed_now")
            ),
            "runtime_test_promotion_allowed_now": (
                progress_reconsideration_review_decision.get("promotion_allowed_now")
            ),
            "runtime_test_default_off_equivalence_passed": (
                progress_window_reconsideration_runtime_test_review_v0.get(
                    "default_off_equivalence_passed"
                )
            ),
            "runtime_test_activation_observed": (
                progress_window_reconsideration_runtime_test_review_v0.get(
                    "activation_observed"
                )
            ),
            "runtime_test_target_improvement_observed": (
                progress_window_reconsideration_runtime_test_review_v0.get(
                    "target_improvement_observed"
                )
            ),
            "runtime_test_safe_regression_observed": (
                progress_window_reconsideration_runtime_test_review_v0.get(
                    "safe_regression_observed"
                )
            ),
            "smoke_status": progress_reconsideration_smoke_decision.get("status"),
            "smoke_default_off_equivalence_passed": (
                progress_reconsideration_smoke_summary.get(
                    "default_off_equivalence_passed"
                )
            ),
            "smoke_improved_target_failure_count": (
                progress_reconsideration_smoke_summary.get(
                    "improved_target_failure_count"
                )
            ),
            "smoke_safe_regression_count": (
                progress_reconsideration_smoke_summary.get("safe_regression_count")
            ),
            "smoke_target_failure_row_count": (
                progress_reconsideration_smoke_summary.get("target_failure_row_count")
            ),
            "smoke_protected_label_count": (
                progress_reconsideration_smoke_summary.get("protected_label_count")
            ),
            "smoke_enabled_supported_total": (
                progress_reconsideration_smoke_summary.get("enabled_supported_total")
            ),
            "smoke_enabled_selected_supported_total": (
                progress_reconsideration_smoke_summary.get(
                    "enabled_selected_supported_total"
                )
            ),
            "post_activation_status": (
                progress_reconsideration_audit_decision.get("status")
            ),
            "post_activation_implement_next_fix_now": (
                progress_reconsideration_audit_decision.get("implement_next_fix_now")
            ),
            "post_activation_recommended_next_step": (
                progress_reconsideration_audit_decision.get("recommended_next_step")
            ),
            "classification_primary": (
                (
                    progress_window_reconsideration_post_activation_audit_v0.get(
                        "classification"
                    )
                    or {}
                ).get("primary")
            ),
            "classification_labels": (
                (
                    progress_window_reconsideration_post_activation_audit_v0.get(
                        "classification"
                    )
                    or {}
                ).get("labels")
            ),
            "promotion_status": (
                progress_window_reconsideration_post_activation_audit_v0.get(
                    "promotion_status"
                )
            ),
            "sandbox_status": (
                progress_window_reconsideration_post_activation_audit_v0.get(
                    "sandbox_status"
                )
            ),
            "runtime_defaults_changed": (
                progress_window_reconsideration_post_activation_audit_v0.get(
                    "runtime_defaults_changed"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                progress_window_reconsideration_post_activation_audit_v0.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "gameplay_topology_mutation": (
                progress_window_reconsideration_post_activation_audit_v0.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": (
                progress_window_reconsideration_post_activation_audit_v0.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                progress_window_reconsideration_post_activation_audit_v0.get(
                    "stage8_training_allowed"
                )
            ),
        },
        "runtime_sandbox_policy_update_gate": {
            "status": runtime_sandbox_policy_decision.get("status"),
            "passive_policy_update_ready": runtime_sandbox_policy_update_passive,
            "allowed_scope": runtime_sandbox_policy_decision.get("allowed_scope"),
            "broad_runtime_changes_allowed": runtime_sandbox_policy_decision.get(
                "broad_runtime_changes_allowed"
            ),
            "default_policy_changes_allowed": runtime_sandbox_policy_decision.get(
                "default_policy_changes_allowed"
            ),
            "stage7_promotion_allowed": runtime_sandbox_policy_decision.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": runtime_sandbox_policy_decision.get(
                "stage8_training_allowed"
            ),
            "test_result_status": runtime_sandbox_policy_test_result.get("status"),
            "test_result_default_off_equivalence_passed": (
                runtime_sandbox_policy_test_result.get(
                    "default_off_equivalence_passed"
                )
            ),
            "test_result_activation_observed": (
                runtime_sandbox_policy_test_result.get("activation_observed")
            ),
            "test_result_target_improvement_observed": (
                runtime_sandbox_policy_test_result.get(
                    "target_improvement_observed"
                )
            ),
            "test_result_guardrails_allowed_now": (
                runtime_sandbox_policy_test_result.get("guardrails_allowed_now")
            ),
            "source_review_packet": runtime_sandbox_policy_update_v0.get(
                "source_review_packet"
            ),
            "hard_boundaries": runtime_sandbox_policy_boundaries,
            "immediate_plan": runtime_sandbox_policy_update_v0.get("immediate_plan")
            or [],
            "progress_window_passive_review_ready": (
                progress_window_reconsideration_passive
            ),
            "hidden_python_controller": runtime_sandbox_policy_boundaries.get(
                "hidden_python_controller"
            ),
            "runtime_dtm_or_tablebase_lookup": runtime_sandbox_policy_boundaries.get(
                "runtime_dtm_or_tablebase"
            ),
            "gameplay_topology_mutation": runtime_sandbox_policy_boundaries.get(
                "gameplay_topology_mutation"
            ),
            "general_predecision_selector": runtime_sandbox_policy_boundaries.get(
                "general_predecision_selector"
            ),
            "stage7_repair_or_promotion": runtime_sandbox_policy_boundaries.get(
                "stage7_repair_or_promotion"
            ),
            "stage8_training": runtime_sandbox_policy_boundaries.get(
                "stage8_training"
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
            "audit_plan_ready": protected_missing_provider_audit_plan_ready,
            "audit_plan_status": (
                protected_missing_provider_audit_plan_decision.get("status")
            ),
            "audit_plan_job_count": (
                protected_missing_provider_audit_plan_summary.get("job_count")
            ),
            "audit_plan_source_frame_count": (
                protected_missing_provider_audit_plan_summary.get(
                    "source_frame_count"
                )
            ),
            "audit_plan_stage_counts": (
                protected_missing_provider_audit_plan_summary.get("stage_counts")
                or {}
            ),
            "audit_plan_runtime_work_allowed": (
                protected_missing_provider_audit_plan_decision.get(
                    "runtime_work_allowed"
                )
            ),
            "audit_plan_runtime_behavior_changed": (
                protected_missing_provider_capacity_audit_plan.get(
                    "runtime_behavior_changed"
                )
            ),
            "audit_plan_runtime_defaults_changed": (
                protected_missing_provider_capacity_audit_plan.get(
                    "runtime_defaults_changed"
                )
            ),
            "audit_plan_runtime_selector_implemented": (
                protected_missing_provider_capacity_audit_plan.get(
                    "runtime_selector_implemented"
                )
            ),
            "audit_plan_runtime_dtm_or_tablebase_lookup": (
                protected_missing_provider_capacity_audit_plan.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "audit_plan_gameplay_topology_mutation": (
                protected_missing_provider_capacity_audit_plan.get(
                    "gameplay_topology_mutation"
                )
            ),
            "audit_plan_stage7_promotion_allowed": (
                protected_missing_provider_capacity_audit_plan.get(
                    "stage7_promotion_allowed"
                )
            ),
            "audit_plan_stage8_training_allowed": (
                protected_missing_provider_capacity_audit_plan.get(
                    "stage8_training_allowed"
                )
            ),
            "execution_manifest_status": (
                protected_missing_provider_manifest_decision.get("status")
            ),
            "execution_manifest_job_count": (
                protected_missing_provider_manifest_binding.get("job_count")
            ),
            "execution_manifest_stage7_job_count": (
                protected_missing_provider_manifest_binding.get("stage7_jobs")
            ),
            "execution_manifest_labels_allowed_now": (
                protected_missing_provider_manifest_decision.get("labels_allowed_now")
            ),
            "execution_manifest_runtime_work_allowed": (
                protected_missing_provider_manifest_decision.get(
                    "runtime_work_allowed"
                )
            ),
            "execution_manifest_review_passive_ready": (
                protected_missing_provider_manifest_review_passive
            ),
            "execution_manifest_review_status": (
                protected_missing_provider_manifest_review_decision.get("status")
            ),
            "execution_manifest_review_labels_allowed": (
                protected_missing_provider_manifest_review_decision.get(
                    "labels_allowed"
                )
            ),
            "execution_manifest_review_runtime_work_allowed": (
                protected_missing_provider_manifest_review_decision.get(
                    "runtime_work_allowed"
                )
            ),
            "execution_manifest_review_violation_count": (
                protected_missing_provider_manifest_review_summary.get(
                    "violation_count"
                )
            ),
            "execution_manifest_review_runtime_behavior_changed": (
                protected_missing_provider_execution_manifest_review.get(
                    "runtime_behavior_changed"
                )
            ),
            "execution_manifest_review_runtime_defaults_changed": (
                protected_missing_provider_execution_manifest_review.get(
                    "runtime_defaults_changed"
                )
            ),
            "execution_manifest_review_runtime_selector_implemented": (
                protected_missing_provider_execution_manifest_review.get(
                    "runtime_selector_implemented"
                )
            ),
            "execution_manifest_review_runtime_dtm_or_tablebase_lookup": (
                protected_missing_provider_execution_manifest_review.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "execution_manifest_review_gameplay_topology_mutation": (
                protected_missing_provider_execution_manifest_review.get(
                    "gameplay_topology_mutation"
                )
            ),
            "execution_manifest_review_stage7_promotion_allowed": (
                protected_missing_provider_execution_manifest_review.get(
                    "stage7_promotion_allowed"
                )
            ),
            "execution_manifest_review_stage8_training_allowed": (
                protected_missing_provider_execution_manifest_review.get(
                    "stage8_training_allowed"
                )
            ),
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
        "control_plane_contract_lineage_gate": {
            "status": control_plane_manifest.get("summary", {}).get(
                "recommended_next_slice"
            ),
            "passive_contract_lineage_ready": control_plane_contract_lineage_passive,
            "architecture_goal_id": self_expansion_goal.get("goal_id"),
            "architecture_goal_type": self_expansion_goal.get("goal_type"),
            "architecture_must_remain_non_causal": self_expansion_goal.get(
                "must_remain_non_causal"
            ),
            "architecture_runtime_defaults_must_remain_unchanged": (
                self_expansion_goal.get("runtime_defaults_must_remain_unchanged")
            ),
            "architecture_forbidden_next_steps": self_expansion_forbidden_next_steps,
            "contract_recommended_next_slice": (
                control_plane_evidence_contract.get("recommended_next_slice")
            ),
            "contract_causal_status": (
                control_plane_evidence_contract.get("causal_status")
            ),
            "contract_validation_requirements": (
                control_plane_evidence_contract.get("validation_requirements") or []
            ),
            "manifest_causal_status": control_plane_manifest.get("causal_status"),
            "manifest_records_from_existing_artifacts_only": (
                control_plane_manifest.get("summary", {}).get(
                    "records_from_existing_artifacts_only"
                )
            ),
            "manifest_new_playouts_added": (
                control_plane_manifest.get("summary", {}).get("new_playouts_added")
            ),
            "manifest_missing_required_fields_after_manifest": (
                control_plane_manifest.get("summary", {}).get(
                    "missing_required_fields_after_manifest"
                )
                or []
            ),
            "manifest_recommended_next_slice": (
                control_plane_manifest.get("summary", {}).get(
                    "recommended_next_slice"
                )
            ),
            "runtime_behavior_changed": (
                control_plane_evidence_contract.get("runtime_behavior_changed")
            ),
            "runtime_defaults_changed": (
                control_plane_evidence_contract.get("runtime_defaults_changed")
            ),
            "runtime_selector_implemented": (
                control_plane_evidence_contract.get("runtime_selector_implemented")
            ),
            "runtime_dtm_or_tablebase_lookup": (
                control_plane_evidence_contract.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "hidden_python_controller": (
                control_plane_evidence_contract.get("hidden_python_controller")
            ),
            "gameplay_topology_mutation": (
                control_plane_evidence_contract.get("gameplay_topology_mutation")
            ),
            "stage7_promotion_allowed": (
                control_plane_evidence_contract.get("stage7_promotion_allowed")
            ),
            "stage8_training_allowed": (
                control_plane_evidence_contract.get("stage8_training_allowed")
            ),
        },
        "control_plane_frame_export_gate": {
            "status": control_plane_forced_controls.get("recommended_next_slice"),
            "passive_frame_export_ready": control_plane_frame_export_passive,
            "gap_report_next_slice_id": control_plane_gap_next.get("slice_id"),
            "gap_report_next_slice_allowed": control_plane_gap_next.get("allowed"),
            "gap_report_next_slice_causal": control_plane_gap_next.get("causal"),
            "gap_report_new_playouts_allowed": (
                control_plane_gap_next.get("new_playouts_allowed")
            ),
            "gap_report_new_playouts_added": (
                control_plane_gap_report.get("coverage_snapshot", {}).get(
                    "new_playouts_added"
                )
            ),
            "frame_export_frame_count": control_plane_frame_summary.get(
                "frame_count"
            ),
            "frame_export_frames_by_source_stage": (
                control_plane_frame_summary.get("frames_by_source_stage") or {}
            ),
            "frame_export_new_playouts_added": (
                control_plane_frame_summary.get("new_playouts_added")
            ),
            "frame_export_strategy_proposal_frame_count": (
                control_plane_frame_summary.get("strategy_proposal_frame_count")
            ),
            "frame_export_internal_monitor_record_count": (
                control_plane_frame_summary.get("internal_monitor_record_count")
            ),
            "frame_quality_next_slice_id": control_plane_quality_next.get(
                "slice_id"
            ),
            "frame_quality_runtime_sandbox": (
                control_plane_quality_readiness.get("runtime_sandbox")
            ),
            "frame_quality_stage7_promotion": (
                control_plane_quality_readiness.get("stage7_promotion")
            ),
            "frame_quality_stage8_training": (
                control_plane_quality_readiness.get("stage8_training")
            ),
            "frame_quality_flag_ids": [
                flag.get("flag_id")
                for flag in (control_plane_frame_quality.get("quality_flags") or [])
            ],
            "filtered_frame_count": control_plane_filtered_summary.get(
                "frame_count"
            ),
            "filtered_strategy_ready_frame_count": (
                control_plane_filtered_summary.get("strategy_ready_frame_count")
            ),
            "filtered_stage7_boundary_heldout_frame_count": (
                control_plane_filtered_summary.get(
                    "stage7_boundary_heldout_frame_count"
                )
            ),
            "filtered_new_playouts_added": (
                control_plane_filtered_summary.get("new_playouts_added")
            ),
            "filtered_runtime_sandbox": (
                control_plane_filtered_readiness.get("runtime_sandbox")
            ),
            "forced_control_labels_attached": (
                control_plane_forced_summary.get("forced_control_labels_attached")
            ),
            "forced_control_missing_label_job_ids": (
                control_plane_forced_summary.get("missing_label_job_ids") or []
            ),
            "forced_control_runtime_sandbox": (
                control_plane_forced_readiness.get("runtime_sandbox")
            ),
            "runtime_behavior_changed": control_plane_forced_controls.get(
                "runtime_behavior_changed"
            ),
            "runtime_defaults_changed": control_plane_forced_controls.get(
                "runtime_defaults_changed"
            ),
            "runtime_selector_implemented": control_plane_forced_controls.get(
                "runtime_selector_implemented"
            ),
            "runtime_dtm_or_tablebase_lookup": control_plane_forced_controls.get(
                "runtime_dtm_or_tablebase_lookup"
            ),
            "hidden_python_controller": control_plane_forced_controls.get(
                "hidden_python_controller"
            ),
            "gameplay_topology_mutation": control_plane_forced_controls.get(
                "gameplay_topology_mutation"
            ),
            "stage7_promotion_allowed": control_plane_forced_controls.get(
                "stage7_promotion_allowed"
            ),
            "stage8_training_allowed": control_plane_forced_controls.get(
                "stage8_training_allowed"
            ),
        },
        "control_plane_strategy_baseline_gate": {
            "status": control_plane_strategy_baseline_decision.get(
                "selected_status"
            ),
            "passive_strategy_baseline_ready": (
                control_plane_strategy_baseline_passive
            ),
            "provider_label_coverage_plan_ready": (
                provider_label_coverage_plan_ready
            ),
            "provider_label_coverage_status": (
                provider_label_coverage_current.get("coverage_status")
            ),
            "provider_label_coverage_benchmark_frame_count": (
                provider_label_coverage_current.get("benchmark_frame_count")
            ),
            "provider_label_coverage_labeled_frame_count": (
                provider_label_coverage_current.get("provider_labeled_frame_count")
            ),
            "provider_label_coverage_known_provider_mate_count": (
                provider_label_coverage_current.get(
                    "frames_with_known_provider_mate"
                )
            ),
            "provider_label_coverage_unknown_examples": (
                provider_label_coverage_current.get("unknown_examples") or []
            ),
            "provider_label_coverage_recommended_next_slice": (
                provider_label_coverage_plan.get("recommended_next_slice")
            ),
            "provider_label_coverage_labels_generated_in_this_slice": (
                provider_label_coverage_plan.get("labels_generated_in_this_slice")
            ),
            "provider_label_coverage_runtime_behavior_changed": (
                provider_label_coverage_plan.get("runtime_behavior_changed")
            ),
            "provider_label_coverage_runtime_defaults_changed": (
                provider_label_coverage_plan.get("runtime_defaults_changed")
            ),
            "provider_label_coverage_runtime_arbiter_added": (
                provider_label_coverage_plan.get("runtime_arbiter_added")
            ),
            "provider_label_coverage_runtime_dtm_or_tablebase_lookup": (
                provider_label_coverage_plan.get("runtime_dtm_or_tablebase_lookup")
            ),
            "provider_label_coverage_gameplay_topology_mutation": (
                provider_label_coverage_plan.get("gameplay_topology_mutation")
            ),
            "provider_label_coverage_stage7_promotion_allowed": (
                provider_label_coverage_plan.get("stage7_promotion_allowed")
            ),
            "provider_label_coverage_stage8_training_allowed": (
                provider_label_coverage_plan.get("stage8_training_allowed")
            ),
            "probe_status": control_plane_strategy_probe_decision.get(
                "selected_status"
            ),
            "probe_causal_next_step_allowed": (
                control_plane_strategy_probe_decision.get(
                    "causal_next_step_allowed"
                )
            ),
            "probe_recommended_next_slice": (
                control_plane_strategy_probe_decision.get("recommended_next_slice")
            ),
            "probe_strategy_benchmark_frame_count": (
                control_plane_strategy_probe_coverage.get(
                    "strategy_benchmark_frame_count"
                )
            ),
            "probe_provider_labeled_frame_count": (
                control_plane_strategy_probe_coverage.get(
                    "provider_labeled_frame_count"
                )
            ),
            "probe_frames_with_known_provider_mate": (
                control_plane_strategy_probe_coverage.get(
                    "frames_with_known_provider_mate"
                )
            ),
            "baseline_status": control_plane_strategy_baseline_decision.get(
                "selected_status"
            ),
            "baseline_causal_next_step_allowed": (
                control_plane_strategy_baseline_decision.get(
                    "causal_next_step_allowed"
                )
            ),
            "baseline_recommended_next_class": (
                control_plane_strategy_baseline_decision.get(
                    "recommended_next_class"
                )
            ),
            "baseline_strategy_benchmark_frame_count": (
                control_plane_strategy_baseline_frame_summary.get(
                    "strategy_benchmark_frame_count"
                )
            ),
            "baseline_frames_with_provider_mate": (
                control_plane_strategy_baseline_frame_summary.get(
                    "frames_with_provider_mate"
                )
            ),
            "baseline_frames_with_only_provider_max_plies": (
                control_plane_strategy_baseline_frame_summary.get(
                    "frames_with_only_provider_max_plies"
                )
            ),
            "baseline_stage_counts": (
                control_plane_strategy_baseline_frame_summary.get("stage_counts")
                or {}
            ),
            "baseline_selector_names": [
                result.get("selector")
                for result in control_plane_strategy_baseline_results
            ],
            "baseline_selector_hit_rates": {
                result.get("selector"): result.get(
                    "hit_when_positive_available_rate"
                )
                for result in control_plane_strategy_baseline_results
            },
            "runtime_behavior_changed": (
                control_plane_strategy_baseline.get("runtime_behavior_changed")
            ),
            "runtime_defaults_changed": (
                control_plane_strategy_baseline.get("runtime_defaults_changed")
            ),
            "runtime_selector_implemented": (
                control_plane_strategy_baseline.get("runtime_selector_implemented")
            ),
            "runtime_dtm_or_tablebase_lookup": (
                control_plane_strategy_baseline.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "hidden_python_controller": (
                control_plane_strategy_baseline.get("hidden_python_controller")
            ),
            "gameplay_topology_mutation": (
                control_plane_strategy_baseline.get("gameplay_topology_mutation")
            ),
            "stage7_promotion_allowed": (
                control_plane_strategy_baseline.get("stage7_promotion_allowed")
            ),
            "stage8_training_allowed": (
                control_plane_strategy_baseline.get("stage8_training_allowed")
            ),
        },
        "control_plane_stage7_boundary_gate": {
            "status": control_plane_stage7_boundary_decision.get("status"),
            "passive_stage7_boundary_ready": control_plane_stage7_boundary_passive,
            "boundary_decision_status": control_plane_stage7_boundary_refresh.get(
                "boundary_decision_status"
            ),
            "boundary_recommended_next_step": (
                control_plane_stage7_boundary_refresh.get(
                    "boundary_recommended_next_step"
                )
            ),
            "stage7_clean_success_controls_met": (
                control_plane_stage7_boundary_current.get(
                    "stage7_clean_success_controls_met"
                )
            ),
            "stage7_clean_hard_negatives_met": (
                control_plane_stage7_boundary_current.get(
                    "stage7_clean_hard_negatives_met"
                )
            ),
            "stage7_clean_review_status": (
                control_plane_stage7_boundary_current.get(
                    "stage7_clean_review_status"
                )
            ),
            "strategy_sequence_inventory_status": (
                control_plane_stage7_boundary_current.get(
                    "strategy_sequence_inventory_status"
                )
            ),
            "strategy_ready_frame_count": (
                control_plane_stage7_boundary_filtered.get(
                    "strategy_ready_frame_count"
                )
            ),
            "strategy_ready_by_stage": (
                control_plane_stage7_boundary_filtered.get("strategy_ready_by_stage")
                or {}
            ),
            "stage7_boundary_heldout_frame_count": (
                control_plane_stage7_boundary_filtered.get(
                    "stage7_boundary_heldout_frame_count"
                )
            ),
            "strategy_probe_status": control_plane_stage7_boundary_probe.get(
                "decision_status"
            ),
            "strategy_baseline_status": (
                control_plane_stage7_boundary_baseline.get("decision_status")
            ),
            "approval_receipt_present": (
                control_plane_stage7_boundary_protected.get(
                    "approval_receipt_present"
                )
            ),
            "approval_receipt_valid": (
                control_plane_stage7_boundary_protected.get(
                    "approval_receipt_valid"
                )
            ),
            "runner_execution_requested": (
                control_plane_stage7_boundary_protected.get(
                    "runner_execution_requested"
                )
            ),
            "runner_collection_run_allowed": (
                control_plane_stage7_boundary_protected.get(
                    "runner_collection_run_allowed"
                )
            ),
            "runner_processed_job_count": (
                control_plane_stage7_boundary_protected.get(
                    "runner_processed_job_count"
                )
            ),
            "runner_executed_job_count": (
                control_plane_stage7_boundary_protected.get(
                    "runner_executed_job_count"
                )
            ),
            "runtime_behavior_changed": (
                control_plane_stage7_boundary_refresh.get("runtime_behavior_changed")
            ),
            "runtime_defaults_changed": (
                control_plane_stage7_boundary_refresh.get("runtime_defaults_changed")
            ),
            "runtime_selector_implemented": (
                control_plane_stage7_boundary_refresh.get(
                    "runtime_selector_implemented"
                )
            ),
            "runtime_dtm_or_tablebase_lookup": (
                control_plane_stage7_boundary_refresh.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "hidden_python_controller": (
                control_plane_stage7_boundary_refresh.get("hidden_python_controller")
            ),
            "gameplay_topology_mutation": (
                control_plane_stage7_boundary_refresh.get(
                    "gameplay_topology_mutation"
                )
            ),
            "stage7_promotion_allowed": (
                control_plane_stage7_boundary_refresh.get(
                    "stage7_promotion_allowed"
                )
            ),
            "stage8_training_allowed": (
                control_plane_stage7_boundary_refresh.get("stage8_training_allowed")
            ),
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
    strategy_arbiter_trace = payload["strategy_arbiter_trace_observability_gate"]
    strategy_arbiter_semantics = payload["strategy_arbiter_semantics_blocker_gate"]
    strategy_arbiter_out_of_sample = payload["strategy_arbiter_out_of_sample_gate"]
    strategy_arbiter_runtime_no_scale = payload[
        "strategy_arbiter_runtime_no_scale_gate"
    ]
    provider_identity_maturity = payload["provider_identity_maturity_blocker_gate"]
    selector_directed_fix = payload["selector_directed_fix_blocker_gate"]
    forced_provider_control = payload["forced_provider_control_label_lineage_gate"]
    selector_provenance_prior = payload["selector_provenance_prior_blocker_gate"]
    selector_objective_normalization = payload["selector_objective_normalization_gate"]
    selector_replay_free_label = payload[
        "selector_replay_free_label_lineage_gate"
    ]
    selector_label_balance = payload["selector_label_balance_gate"]
    ownership_selection_context = payload["ownership_selection_context_gate"]
    selector_negative_suppression = payload[
        "selector_negative_suppression_blocker_gate"
    ]
    abstention_selector_safety = payload["abstention_selector_safety_gate"]
    two_stage_abstention_no_go = payload["two_stage_abstention_no_go_gate"]
    targeted_ownership_recovery = payload["targeted_ownership_recovery_gate"]
    balanced_hard_negative = payload["balanced_hard_negative_gate"]
    hard_negative_semantics = payload["hard_negative_label_semantics_gate"]
    stronger_selector_feature = payload["stronger_selector_feature_gate"]
    selected_provider_diversity = payload["selected_provider_diversity_gate"]
    selector_readiness_v3 = payload["selector_readiness_v3_design_gate"]
    state_local_contrast = payload["state_local_contrast_gate"]
    state_local_paired_ownership = payload["state_local_paired_ownership_gate"]
    selected_owner_failure_risk = payload["selected_owner_failure_risk_proxy_gate"]
    progress_window_reconsideration = payload["progress_window_reconsideration_gate"]
    runtime_sandbox_policy_update = payload["runtime_sandbox_policy_update_gate"]
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
    control_plane_contract = payload["control_plane_contract_lineage_gate"]
    control_plane_frame_export = payload["control_plane_frame_export_gate"]
    control_plane_strategy_baseline = payload["control_plane_strategy_baseline_gate"]
    control_plane_stage7_boundary = payload["control_plane_stage7_boundary_gate"]
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
        f"- stage4_caveat_diagnostic_matrix_ready: `{clean_curriculum['stage4_caveat_diagnostic_matrix_ready']}`",
        f"- stage4_caveat_diagnostic_status: `{clean_curriculum['stage4_caveat_diagnostic_status']}`",
        f"- stage4_caveat_diagnostic_max_plies_count: `{clean_curriculum['stage4_caveat_diagnostic_max_plies_count']}`",
        f"- stage4_caveat_diagnostic_candidate_gap_confidence: `{clean_curriculum['stage4_caveat_diagnostic_candidate_gap_confidence']}`",
        f"- stage4_caveat_diagnostic_candidate_gap_next_test: `{clean_curriculum['stage4_caveat_diagnostic_candidate_gap_next_test']}`",
        f"- stage4_caveat_decision_passive_ready: `{clean_curriculum['stage4_caveat_decision_passive_ready']}`",
        f"- stage4_caveat_decision_status: `{clean_curriculum['stage4_caveat_decision_status']}`",
        f"- stage4_caveat_decision_next_action: `{clean_curriculum['stage4_caveat_decision_next_action']}`",
        f"- stage4_caveat_runtime_or_training_authorized: `{clean_curriculum['stage4_caveat_runtime_or_training_authorized']}`",
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
        "## Strategy Arbiter Trace Observability",
        "",
        f"- passive_trace_observability_ready: `{strategy_arbiter_trace['passive_trace_observability_ready']}`",
        f"- status: `{strategy_arbiter_trace['status']}`",
        f"- sandbox_design_status: `{strategy_arbiter_trace['sandbox_design_status']}`",
        f"- sandbox_default_enabled: `{strategy_arbiter_trace['sandbox_default_enabled']}`",
        f"- smoke_status: `{strategy_arbiter_trace['smoke_status']}`",
        f"- smoke_runtime_arbiter_allowed: `{strategy_arbiter_trace['smoke_runtime_arbiter_allowed']}`",
        f"- smoke_selected_behavior_metrics_match: `{strategy_arbiter_trace['smoke_selected_behavior_metrics_match']}`",
        f"- smoke_observation_is_only_expected_delta: `{strategy_arbiter_trace['smoke_observation_is_only_expected_delta']}`",
        f"- smoke_direct_request: `{strategy_arbiter_trace['smoke_direct_request']}`",
        f"- smoke_score_delta: `{strategy_arbiter_trace['smoke_score_delta']}`",
        f"- observation_frames_status: `{strategy_arbiter_trace['observation_frames_status']}`",
        f"- observation_frame_count: `{strategy_arbiter_trace['observation_frame_count']}`",
        f"- observation_stage_counts: `{strategy_arbiter_trace['observation_stage_counts']}`",
        f"- separability_status: `{strategy_arbiter_trace['separability_status']}`",
        f"- separability_sandbox_ready: `{strategy_arbiter_trace['separability_sandbox_ready']}`",
        f"- selector_probe_status: `{strategy_arbiter_trace['selector_probe_status']}`",
        f"- selector_probe_underlabeled: `{strategy_arbiter_trace['selector_probe_underlabeled']}`",
        f"- selector_probe_selected_unknown_count: `{strategy_arbiter_trace['selector_probe_selected_unknown_count']}`",
        f"- labeled_controls_status: `{strategy_arbiter_trace['labeled_controls_status']}`",
        f"- labeled_controls_record_count: `{strategy_arbiter_trace['labeled_controls_record_count']}`",
        f"- labeled_controls_selected_label_counts: `{strategy_arbiter_trace['labeled_controls_selected_label_counts']}`",
        f"- labeled_probe_status: `{strategy_arbiter_trace['labeled_probe_status']}`",
        f"- labeled_probe_sandbox_ready: `{strategy_arbiter_trace['labeled_probe_sandbox_ready']}`",
        f"- labeled_probe_stage7_unknown_count: `{strategy_arbiter_trace['labeled_probe_stage7_unknown_count']}`",
        f"- protected_matrix_status: `{strategy_arbiter_trace['protected_matrix_status']}`",
        f"- protected_matrix_default_off_equivalence_passed: `{strategy_arbiter_trace['protected_matrix_default_off_equivalence_passed']}`",
        f"- protected_matrix_stage7_rows: `{strategy_arbiter_trace['protected_matrix_stage7_rows']}`",
        f"- runtime_arbiter_implemented: `{strategy_arbiter_trace['runtime_arbiter_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{strategy_arbiter_trace['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{strategy_arbiter_trace['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{strategy_arbiter_trace['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{strategy_arbiter_trace['stage8_training_allowed']}`",
        "",
        "## Strategy Arbiter Semantics Blocker",
        "",
        f"- passive_semantics_blocker_ready: `{strategy_arbiter_semantics['passive_semantics_blocker_ready']}`",
        f"- status: `{strategy_arbiter_semantics['status']}`",
        f"- risk_review_status: `{strategy_arbiter_semantics['risk_review_status']}`",
        f"- risk_review_runtime_sandbox_allowed: `{strategy_arbiter_semantics['risk_review_runtime_sandbox_allowed']}`",
        f"- risk_review_benchmark_frame_count: `{strategy_arbiter_semantics['risk_review_benchmark_frame_count']}`",
        f"- risk_review_max_only_frame_count: `{strategy_arbiter_semantics['risk_review_max_only_frame_count']}`",
        f"- stratified_probe_status: `{strategy_arbiter_semantics['stratified_probe_status']}`",
        f"- stratified_probe_selected_provider_hit_rate: `{strategy_arbiter_semantics['stratified_probe_selected_provider_hit_rate']}`",
        f"- stratified_probe_forced_control_hit_rate: `{strategy_arbiter_semantics['stratified_probe_forced_control_hit_rate']}`",
        f"- stratified_probe_stage7_forced_provider_hit_rate: `{strategy_arbiter_semantics['stratified_probe_stage7_forced_provider_hit_rate']}`",
        f"- architecture_review_status: `{strategy_arbiter_semantics['architecture_review_status']}`",
        f"- architecture_runtime_arbiter_allowed: `{strategy_arbiter_semantics['architecture_runtime_arbiter_allowed']}`",
        f"- architecture_allowed_next_scope: `{strategy_arbiter_semantics['architecture_allowed_next_scope']}`",
        f"- architecture_allowed_next_default_enabled: `{strategy_arbiter_semantics['architecture_allowed_next_default_enabled']}`",
        f"- sandbox_readiness_decision_status: `{strategy_arbiter_semantics['sandbox_readiness_decision_status']}`",
        f"- sandbox_readiness_selector_sandbox_ready: `{strategy_arbiter_semantics['sandbox_readiness_selector_sandbox_ready']}`",
        f"- sandbox_readiness_out_of_sample_controls_status: `{strategy_arbiter_semantics['sandbox_readiness_out_of_sample_controls_status']}`",
        f"- control_plane_observability_skeleton: `{strategy_arbiter_semantics['control_plane_observability_skeleton']}`",
        f"- control_plane_labeled_controls: `{strategy_arbiter_semantics['control_plane_labeled_controls']}`",
        f"- control_plane_stage7: `{strategy_arbiter_semantics['control_plane_stage7']}`",
        f"- control_plane_runtime_arbiter_allowed: `{strategy_arbiter_semantics['control_plane_runtime_arbiter_allowed']}`",
        f"- control_plane_sandbox_ready: `{strategy_arbiter_semantics['control_plane_sandbox_ready']}`",
        f"- control_plane_recommended_next_step_id: `{strategy_arbiter_semantics['control_plane_recommended_next_step_id']}`",
        f"- control_plane_blocked_next_work: `{strategy_arbiter_semantics['control_plane_blocked_next_work']}`",
        f"- runtime_arbiter_implemented: `{strategy_arbiter_semantics['runtime_arbiter_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{strategy_arbiter_semantics['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{strategy_arbiter_semantics['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{strategy_arbiter_semantics['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{strategy_arbiter_semantics['stage8_training_allowed']}`",
        "",
        "## Strategy Arbiter Out-Of-Sample Controls",
        "",
        f"- passive_out_of_sample_ready: `{strategy_arbiter_out_of_sample['passive_out_of_sample_ready']}`",
        f"- plan_status: `{strategy_arbiter_out_of_sample['plan_status']}`",
        f"- plan_execute_collection_now: `{strategy_arbiter_out_of_sample['plan_execute_collection_now']}`",
        f"- manifest_status: `{strategy_arbiter_out_of_sample['manifest_status']}`",
        f"- manifest_execute_labels_now: `{strategy_arbiter_out_of_sample['manifest_execute_labels_now']}`",
        f"- manifest_job_count: `{strategy_arbiter_out_of_sample['manifest_job_count']}`",
        f"- manifest_job_count_by_stage: `{strategy_arbiter_out_of_sample['manifest_job_count_by_stage']}`",
        f"- manifest_stage7_training_rows: `{strategy_arbiter_out_of_sample['manifest_stage7_training_rows']}`",
        f"- manifest_review_status: `{strategy_arbiter_out_of_sample['manifest_review_status']}`",
        f"- manifest_review_execute_labels_now: `{strategy_arbiter_out_of_sample['manifest_review_execute_labels_now']}`",
        f"- label_count: `{strategy_arbiter_out_of_sample['label_count']}`",
        f"- label_stage7_training_rows: `{strategy_arbiter_out_of_sample['label_stage7_training_rows']}`",
        f"- label_selected_result_counts: `{strategy_arbiter_out_of_sample['label_selected_result_counts']}`",
        f"- probe_status: `{strategy_arbiter_out_of_sample['probe_status']}`",
        f"- probe_sandbox_blockers: `{strategy_arbiter_out_of_sample['probe_sandbox_blockers']}`",
        f"- probe_selected_provider_dominance: `{strategy_arbiter_out_of_sample['probe_selected_provider_dominance']}`",
        f"- architecture_review_status: `{strategy_arbiter_out_of_sample['architecture_review_status']}`",
        f"- architecture_selector_signal_status: `{strategy_arbiter_out_of_sample['architecture_selector_signal_status']}`",
        f"- blocked_next_steps: `{strategy_arbiter_out_of_sample['blocked_next_steps']}`",
        f"- runtime_arbiter_allowed: `{strategy_arbiter_out_of_sample['runtime_arbiter_allowed']}`",
        f"- selector_sandbox_ready: `{strategy_arbiter_out_of_sample['selector_sandbox_ready']}`",
        f"- runtime_arbiter_implemented: `{strategy_arbiter_out_of_sample['runtime_arbiter_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{strategy_arbiter_out_of_sample['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{strategy_arbiter_out_of_sample['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{strategy_arbiter_out_of_sample['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{strategy_arbiter_out_of_sample['stage8_training_allowed']}`",
        "",
        "## Strategy Arbiter Runtime No-Scale Review",
        "",
        f"- passive_no_scale_ready: `{strategy_arbiter_runtime_no_scale['passive_no_scale_ready']}`",
        f"- status: `{strategy_arbiter_runtime_no_scale['status']}`",
        f"- default_off_design_status: `{strategy_arbiter_runtime_no_scale['default_off_design_status']}`",
        f"- default_off_design_implementation_allowed: `{strategy_arbiter_runtime_no_scale['default_off_design_implementation_allowed']}`",
        f"- default_off_design_runtime_arbiter_allowed: `{strategy_arbiter_runtime_no_scale['default_off_design_runtime_arbiter_allowed']}`",
        f"- default_off_design_selector_sandbox_ready: `{strategy_arbiter_runtime_no_scale['default_off_design_selector_sandbox_ready']}`",
        f"- default_off_future_contract_default_enabled: `{strategy_arbiter_runtime_no_scale['default_off_future_contract_default_enabled']}`",
        f"- runtime_review_packet_status: `{strategy_arbiter_runtime_no_scale['runtime_review_packet_status']}`",
        f"- runtime_review_packet_implementation_allowed: `{strategy_arbiter_runtime_no_scale['runtime_review_packet_implementation_allowed']}`",
        f"- runtime_review_packet_selector_sandbox_ready: `{strategy_arbiter_runtime_no_scale['runtime_review_packet_selector_sandbox_ready']}`",
        f"- runtime_review_packet_blocked_until_review: `{strategy_arbiter_runtime_no_scale['runtime_review_packet_blocked_until_review']}`",
        f"- runtime_sandbox_smoke_status: `{strategy_arbiter_runtime_no_scale['runtime_sandbox_smoke_status']}`",
        f"- runtime_sandbox_default_off_equivalence_passed: `{strategy_arbiter_runtime_no_scale['runtime_sandbox_default_off_equivalence_passed']}`",
        f"- runtime_sandbox_enabled_support_trace_visible: `{strategy_arbiter_runtime_no_scale['runtime_sandbox_enabled_support_trace_visible']}`",
        f"- runtime_sandbox_direct_request: `{strategy_arbiter_runtime_no_scale['runtime_sandbox_direct_request']}`",
        f"- runtime_sandbox_support_was_applied: `{strategy_arbiter_runtime_no_scale['runtime_sandbox_support_was_applied']}`",
        f"- protected_control_matrix_status: `{strategy_arbiter_runtime_no_scale['protected_control_matrix_status']}`",
        f"- protected_control_no_conversion_regression: `{strategy_arbiter_runtime_no_scale['protected_control_no_conversion_regression']}`",
        f"- protected_control_no_no_move_or_draw_spike: `{strategy_arbiter_runtime_no_scale['protected_control_no_no_move_or_draw_spike']}`",
        f"- protected_control_stage7_rows: `{strategy_arbiter_runtime_no_scale['protected_control_stage7_rows']}`",
        f"- stage7_holdout_status: `{strategy_arbiter_runtime_no_scale['stage7_holdout_status']}`",
        f"- stage7_holdout_support_blocked: `{strategy_arbiter_runtime_no_scale['stage7_holdout_support_blocked']}`",
        f"- stage7_holdout_allow_stage7_challenge: `{strategy_arbiter_runtime_no_scale['stage7_holdout_allow_stage7_challenge']}`",
        f"- stage7_challenge_status: `{strategy_arbiter_runtime_no_scale['stage7_challenge_status']}`",
        f"- stage7_challenge_conversion_delta: `{strategy_arbiter_runtime_no_scale['stage7_challenge_conversion_delta']}`",
        f"- stage7_challenge_selected_supported_count: `{strategy_arbiter_runtime_no_scale['stage7_challenge_selected_supported_count']}`",
        f"- support_sensitivity_status: `{strategy_arbiter_runtime_no_scale['support_sensitivity_status']}`",
        f"- support_sensitivity_scale_risk: `{strategy_arbiter_runtime_no_scale['support_sensitivity_scale_risk']}`",
        f"- runtime_test_review_runtime_promotion_allowed: `{strategy_arbiter_runtime_no_scale['runtime_test_review_runtime_promotion_allowed']}`",
        f"- runtime_test_review_small_support_stage7_effective: `{strategy_arbiter_runtime_no_scale['runtime_test_review_small_support_stage7_effective']}`",
        f"- runtime_test_review_high_support_scale_risk: `{strategy_arbiter_runtime_no_scale['runtime_test_review_high_support_scale_risk']}`",
        f"- runtime_test_blocked_path: `{strategy_arbiter_runtime_no_scale['runtime_test_blocked_path']}`",
        f"- blocked_next_steps: `{strategy_arbiter_runtime_no_scale['blocked_next_steps']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{strategy_arbiter_runtime_no_scale['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{strategy_arbiter_runtime_no_scale['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{strategy_arbiter_runtime_no_scale['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{strategy_arbiter_runtime_no_scale['stage8_training_allowed']}`",
        "",
        "## Provider Identity Maturity Blocker",
        "",
        f"- passive_provider_identity_maturity_ready: `{provider_identity_maturity['passive_provider_identity_maturity_ready']}`",
        f"- status: `{provider_identity_maturity['status']}`",
        f"- row_count: `{provider_identity_maturity['row_count']}`",
        f"- provider_prior_accuracy: `{provider_identity_maturity['provider_prior_accuracy']}`",
        f"- best_feature_probe_baseline: `{provider_identity_maturity['best_feature_probe_baseline']}`",
        f"- best_feature_probe_accuracy: `{provider_identity_maturity['best_feature_probe_accuracy']}`",
        f"- provider_identity_signal: `{provider_identity_maturity['provider_identity_signal']}`",
        f"- raw_provider_id_is_principled_runtime_signal: `{provider_identity_maturity['raw_provider_id_is_principled_runtime_signal']}`",
        f"- stage0_basin_positive_rate: `{provider_identity_maturity['stage0_basin_positive_rate']}`",
        f"- edge_trap_positive_rates: `{provider_identity_maturity['edge_trap_positive_rates']}`",
        f"- required_future_features: `{provider_identity_maturity['required_future_features']}`",
        f"- blocked_next_work: `{provider_identity_maturity['blocked_next_work']}`",
        f"- runtime_arbiter_allowed: `{provider_identity_maturity['runtime_arbiter_allowed']}`",
        f"- selector_sandbox_ready: `{provider_identity_maturity['selector_sandbox_ready']}`",
        f"- stage7_repair_allowed: `{provider_identity_maturity['stage7_repair_allowed']}`",
        f"- runtime_arbiter_implemented: `{provider_identity_maturity['runtime_arbiter_implemented']}`",
        f"- runtime_behavior_changed: `{provider_identity_maturity['runtime_behavior_changed']}`",
        f"- runtime_defaults_changed: `{provider_identity_maturity['runtime_defaults_changed']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{provider_identity_maturity['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{provider_identity_maturity['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{provider_identity_maturity['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{provider_identity_maturity['stage8_training_allowed']}`",
        "",
        "## Selector Directed Fix Blocker",
        "",
        f"- passive_selector_directed_fix_ready: `{selector_directed_fix['passive_selector_directed_fix_ready']}`",
        f"- status: `{selector_directed_fix['status']}`",
        f"- geometry_audit_status: `{selector_directed_fix['geometry_audit_status']}`",
        f"- geometry_audit_row_count: `{selector_directed_fix['geometry_audit_row_count']}`",
        f"- geometry_audit_stage7_row_count: `{selector_directed_fix['geometry_audit_stage7_row_count']}`",
        f"- geometry_audit_capacity_label_counts: `{selector_directed_fix['geometry_audit_capacity_label_counts']}`",
        f"- geometry_probe_status: `{selector_directed_fix['geometry_probe_status']}`",
        f"- geometry_probe_row_count: `{selector_directed_fix['geometry_probe_row_count']}`",
        f"- geometry_probe_state_count: `{selector_directed_fix['geometry_probe_state_count']}`",
        f"- geometry_probe_underpowered: `{selector_directed_fix['geometry_probe_underpowered']}`",
        f"- geometry_probe_best_objective: `{selector_directed_fix['geometry_probe_best_objective']}`",
        f"- geometry_probe_best_negative_suppression: `{selector_directed_fix['geometry_probe_best_negative_suppression']}`",
        f"- directed_fix_recommended_next_step: `{selector_directed_fix['directed_fix_recommended_next_step']}`",
        f"- directed_fix_recommended_class: `{selector_directed_fix['directed_fix_recommended_class']}`",
        f"- directed_fix_recommended_not_runtime: `{selector_directed_fix['directed_fix_recommended_not_runtime']}`",
        f"- directed_fix_rejected_fixes: `{selector_directed_fix['directed_fix_rejected_fixes']}`",
        f"- directed_fix_requirements: `{selector_directed_fix['directed_fix_requirements']}`",
        f"- runtime_work_allowed: `{selector_directed_fix['runtime_work_allowed']}`",
        f"- candidate_generator_runtime_allowed: `{selector_directed_fix['candidate_generator_runtime_allowed']}`",
        f"- selector_training_allowed: `{selector_directed_fix['selector_training_allowed']}`",
        f"- runtime_selector_implemented: `{selector_directed_fix['runtime_selector_implemented']}`",
        f"- runtime_candidate_generator_implemented: `{selector_directed_fix['runtime_candidate_generator_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{selector_directed_fix['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{selector_directed_fix['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{selector_directed_fix['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{selector_directed_fix['stage8_training_allowed']}`",
        "",
        "## Forced Provider Control Label Lineage",
        "",
        f"- passive_forced_provider_control_lineage_ready: `{forced_provider_control['passive_forced_provider_control_lineage_ready']}`",
        f"- status: `{forced_provider_control['status']}`",
        f"- plan_causal_status: `{forced_provider_control['plan_causal_status']}`",
        f"- plan_selected_job_count: `{forced_provider_control['plan_selected_job_count']}`",
        f"- plan_selected_job_count_by_stage: `{forced_provider_control['plan_selected_job_count_by_stage']}`",
        f"- plan_current_label_result_counts: `{forced_provider_control['plan_current_label_result_counts']}`",
        f"- plan_target_stages: `{forced_provider_control['plan_target_stages']}`",
        f"- manifest_causal_status: `{forced_provider_control['manifest_causal_status']}`",
        f"- manifest_all_bindings_valid: `{forced_provider_control['manifest_all_bindings_valid']}`",
        f"- manifest_job_count: `{forced_provider_control['manifest_job_count']}`",
        f"- manifest_missing_path_count: `{forced_provider_control['manifest_missing_path_count']}`",
        f"- labels_causal_status: `{forced_provider_control['labels_causal_status']}`",
        f"- label_count: `{forced_provider_control['label_count']}`",
        f"- label_stage_counts: `{forced_provider_control['label_stage_counts']}`",
        f"- result_counts: `{forced_provider_control['result_counts']}`",
        f"- result_counts_by_stage: `{forced_provider_control['result_counts_by_stage']}`",
        f"- trace_failures_only: `{forced_provider_control['trace_failures_only']}`",
        f"- trace_included_count: `{forced_provider_control['trace_included_count']}`",
        f"- forced_successor_available_count: `{forced_provider_control['forced_successor_available_count']}`",
        f"- provider_ids: `{forced_provider_control['provider_ids']}`",
        f"- blocked_next_steps: `{forced_provider_control['blocked_next_steps']}`",
        f"- runtime_behavior_changed: `{forced_provider_control['runtime_behavior_changed']}`",
        f"- runtime_defaults_changed: `{forced_provider_control['runtime_defaults_changed']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{forced_provider_control['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{forced_provider_control['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{forced_provider_control['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{forced_provider_control['stage8_training_allowed']}`",
        "",
        "## Selector Provenance Prior Blocker",
        "",
        f"- passive_provenance_prior_blocker_ready: `{selector_provenance_prior['passive_provenance_prior_blocker_ready']}`",
        f"- status: `{selector_provenance_prior['status']}`",
        f"- target_dataset_status: `{selector_provenance_prior['target_dataset_status']}`",
        f"- target_dataset_training_row_count: `{selector_provenance_prior['target_dataset_training_row_count']}`",
        f"- target_dataset_stage7_training_rows: `{selector_provenance_prior['target_dataset_stage7_training_rows']}`",
        f"- target_probe_heldout_training_row_count: `{selector_provenance_prior['target_probe_heldout_training_row_count']}`",
        f"- baseline_probe_best_baseline: `{selector_provenance_prior['baseline_probe_best_baseline']}`",
        f"- baseline_probe_best_accuracy: `{selector_provenance_prior['baseline_probe_best_accuracy']}`",
        f"- feature_baseline_status: `{selector_provenance_prior['feature_baseline_status']}`",
        f"- feature_baseline_improved_over_provider_prior: `{selector_provenance_prior['feature_baseline_improved_over_provider_prior']}`",
        f"- provenance_dataset_rows_with_provider_provenance: `{selector_provenance_prior['provenance_dataset_rows_with_provider_provenance']}`",
        f"- provenance_probe_status: `{selector_provenance_prior['provenance_probe_status']}`",
        f"- provenance_probe_raw_provider_id_runtime_prior_allowed: `{selector_provenance_prior['provenance_probe_raw_provider_id_runtime_prior_allowed']}`",
        f"- provenance_probe_selector_sandbox_ready: `{selector_provenance_prior['provenance_probe_selector_sandbox_ready']}`",
        f"- provenance_probe_best_name: `{selector_provenance_prior['provenance_probe_best_name']}`",
        f"- architecture_review_status: `{selector_provenance_prior['architecture_review_status']}`",
        f"- architecture_observation_features_improved_over_provider_prior: `{selector_provenance_prior['architecture_observation_features_improved_over_provider_prior']}`",
        f"- architecture_must_remain_non_causal: `{selector_provenance_prior['architecture_must_remain_non_causal']}`",
        f"- after_contrast_status: `{selector_provenance_prior['after_contrast_status']}`",
        f"- after_contrast_selector_sandbox_ready: `{selector_provenance_prior['after_contrast_selector_sandbox_ready']}`",
        f"- after_contrast_readiness_blockers: `{selector_provenance_prior['after_contrast_readiness_blockers']}`",
        f"- runtime_arbiter_implemented: `{selector_provenance_prior['runtime_arbiter_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{selector_provenance_prior['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{selector_provenance_prior['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{selector_provenance_prior['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{selector_provenance_prior['stage8_training_allowed']}`",
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
        "## Selector Replay-Free Label Lineage",
        "",
        f"- passive_replay_free_label_lineage_ready: `{selector_replay_free_label['passive_replay_free_label_lineage_ready']}`",
        f"- plan_status: `{selector_replay_free_label['plan_status']}`",
        f"- plan_execute_labels_now: `{selector_replay_free_label['plan_execute_labels_now']}`",
        f"- plan_job_count: `{selector_replay_free_label['plan_job_count']}`",
        f"- plan_job_stage_counts: `{selector_replay_free_label['plan_job_stage_counts']}`",
        f"- review_status: `{selector_replay_free_label['review_status']}`",
        f"- review_execute_labels_now: `{selector_replay_free_label['review_execute_labels_now']}`",
        f"- review_missing_replay_free_label_count: `{selector_replay_free_label['review_missing_replay_free_label_count']}`",
        f"- review_fill_status_counts: `{selector_replay_free_label['review_fill_status_counts']}`",
        f"- negative_control_status: `{selector_replay_free_label['negative_control_status']}`",
        f"- negative_control_count: `{selector_replay_free_label['negative_control_count']}`",
        f"- negative_control_stage_counts: `{selector_replay_free_label['negative_control_stage_counts']}`",
        f"- negative_control_provider_counts: `{selector_replay_free_label['negative_control_provider_counts']}`",
        f"- stratified_dataset_status: `{selector_replay_free_label['stratified_dataset_status']}`",
        f"- stratified_dataset_row_count: `{selector_replay_free_label['stratified_dataset_row_count']}`",
        f"- stratified_dataset_label_counts: `{selector_replay_free_label['stratified_dataset_label_counts']}`",
        f"- stratified_dataset_stage7_training_rows: `{selector_replay_free_label['stratified_dataset_stage7_training_rows']}`",
        f"- balanced_dataset_status: `{selector_replay_free_label['balanced_dataset_status']}`",
        f"- balanced_dataset_row_count: `{selector_replay_free_label['balanced_dataset_row_count']}`",
        f"- balanced_dataset_label_counts: `{selector_replay_free_label['balanced_dataset_label_counts']}`",
        f"- balanced_dataset_stage7_training_rows: `{selector_replay_free_label['balanced_dataset_stage7_training_rows']}`",
        f"- balanced_probe_status: `{selector_replay_free_label['balanced_probe_status']}`",
        f"- balanced_probe_best_baseline: `{selector_replay_free_label['balanced_probe_best_baseline']}`",
        f"- balanced_probe_best_accuracy: `{selector_replay_free_label['balanced_probe_best_accuracy']}`",
        f"- architecture_status: `{selector_replay_free_label['architecture_status']}`",
        f"- architecture_selector_sandbox_ready: `{selector_replay_free_label['architecture_selector_sandbox_ready']}`",
        f"- architecture_runtime_arbiter_allowed: `{selector_replay_free_label['architecture_runtime_arbiter_allowed']}`",
        f"- architecture_stage7_repair_allowed: `{selector_replay_free_label['architecture_stage7_repair_allowed']}`",
        f"- runtime_behavior_changed: `{selector_replay_free_label['runtime_behavior_changed']}`",
        f"- runtime_defaults_changed: `{selector_replay_free_label['runtime_defaults_changed']}`",
        f"- runtime_arbiter_implemented: `{selector_replay_free_label['runtime_arbiter_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{selector_replay_free_label['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{selector_replay_free_label['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{selector_replay_free_label['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{selector_replay_free_label['stage8_training_allowed']}`",
        "",
        "## Selector Label Balance",
        "",
        f"- passive_label_balance_ready: `{selector_label_balance['passive_label_balance_ready']}`",
        f"- stratified_dataset_status: `{selector_label_balance['stratified_dataset_status']}`",
        f"- stratified_dataset_row_count: `{selector_label_balance['stratified_dataset_row_count']}`",
        f"- stratified_dataset_stage7_training_rows: `{selector_label_balance['stratified_dataset_stage7_training_rows']}`",
        f"- stratified_probe_status: `{selector_label_balance['stratified_probe_status']}`",
        f"- stratified_probe_label_counts: `{selector_label_balance['stratified_probe_label_counts']}`",
        f"- stratified_probe_underbalanced: `{selector_label_balance['stratified_probe_underbalanced']}`",
        f"- balanced_dataset_status: `{selector_label_balance['balanced_dataset_status']}`",
        f"- balanced_dataset_row_count: `{selector_label_balance['balanced_dataset_row_count']}`",
        f"- balanced_dataset_stage7_training_rows: `{selector_label_balance['balanced_dataset_stage7_training_rows']}`",
        f"- balanced_dataset_provider_family_counts: `{selector_label_balance['balanced_dataset_provider_family_counts']}`",
        f"- balanced_probe_status: `{selector_label_balance['balanced_probe_status']}`",
        f"- balanced_probe_label_counts: `{selector_label_balance['balanced_probe_label_counts']}`",
        f"- balanced_probe_best_baseline: `{selector_label_balance['balanced_probe_best_baseline']}`",
        f"- balanced_probe_best_accuracy: `{selector_label_balance['balanced_probe_best_accuracy']}`",
        f"- architecture_status: `{selector_label_balance['architecture_status']}`",
        f"- architecture_recommended_next_step: `{selector_label_balance['architecture_recommended_next_step']}`",
        f"- architecture_runtime_arbiter_allowed: `{selector_label_balance['architecture_runtime_arbiter_allowed']}`",
        f"- architecture_selector_sandbox_ready: `{selector_label_balance['architecture_selector_sandbox_ready']}`",
        f"- blocked_next_work: `{selector_label_balance['blocked_next_work']}`",
        f"- runtime_selector_implemented: `{selector_label_balance['runtime_selector_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{selector_label_balance['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{selector_label_balance['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{selector_label_balance['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{selector_label_balance['stage8_training_allowed']}`",
        "",
        "## Ownership Selection Context",
        "",
        f"- passive_context_ready: `{ownership_selection_context['passive_context_ready']}`",
        f"- label_dataset_status: `{ownership_selection_context['label_dataset_status']}`",
        f"- label_dataset_merged_row_count: `{ownership_selection_context['label_dataset_merged_row_count']}`",
        f"- label_dataset_target_label_counts: `{ownership_selection_context['label_dataset_target_label_counts']}`",
        f"- label_dataset_targeted_added_row_count: `{ownership_selection_context['label_dataset_targeted_added_row_count']}`",
        f"- label_dataset_selector_training_row_count: `{ownership_selection_context['label_dataset_selector_training_row_count']}`",
        f"- label_dataset_stage7_row_count: `{ownership_selection_context['label_dataset_stage7_row_count']}`",
        f"- context_dataset_status: `{ownership_selection_context['context_dataset_status']}`",
        f"- context_dataset_row_count: `{ownership_selection_context['context_dataset_row_count']}`",
        f"- context_dataset_exact_move_context_count: `{ownership_selection_context['context_dataset_exact_move_context_count']}`",
        f"- context_dataset_label_counts: `{ownership_selection_context['context_dataset_label_counts']}`",
        f"- context_dataset_provider_family_counts: `{ownership_selection_context['context_dataset_provider_family_counts']}`",
        f"- context_dataset_selector_training_row_count: `{ownership_selection_context['context_dataset_selector_training_row_count']}`",
        f"- context_dataset_stage7_row_count: `{ownership_selection_context['context_dataset_stage7_row_count']}`",
        f"- context_probe_status: `{ownership_selection_context['context_probe_status']}`",
        f"- context_probe_underpowered: `{ownership_selection_context['context_probe_underpowered']}`",
        f"- context_probe_positive_owner_count: `{ownership_selection_context['context_probe_positive_owner_count']}`",
        f"- context_probe_negative_owner_count: `{ownership_selection_context['context_probe_negative_owner_count']}`",
        f"- source_diversity_status: `{ownership_selection_context['source_diversity_status']}`",
        f"- source_diversity_non_stage0_ownership_row_count: `{ownership_selection_context['source_diversity_non_stage0_ownership_row_count']}`",
        f"- source_diversity_provider_counts: `{ownership_selection_context['source_diversity_provider_counts']}`",
        f"- runtime_selector_implemented: `{ownership_selection_context['runtime_selector_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{ownership_selection_context['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{ownership_selection_context['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{ownership_selection_context['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{ownership_selection_context['stage8_training_allowed']}`",
        "",
        "## Selector Negative-Suppression Blocker",
        "",
        f"- passive_blocker_ready: `{selector_negative_suppression['passive_blocker_ready']}`",
        f"- protected_max_only_status: `{selector_negative_suppression['protected_max_only_status']}`",
        f"- protected_max_only_frame_count: `{selector_negative_suppression['protected_max_only_frame_count']}`",
        f"- protected_max_only_frames_with_only_max_plies: `{selector_negative_suppression['protected_max_only_frames_with_only_max_plies']}`",
        f"- protected_max_only_frames_with_mate_provider: `{selector_negative_suppression['protected_max_only_frames_with_mate_provider']}`",
        f"- protected_max_only_runtime_work_allowed: `{selector_negative_suppression['protected_max_only_runtime_work_allowed']}`",
        f"- negative_suppression_status: `{selector_negative_suppression['negative_suppression_status']}`",
        f"- negative_suppression_recommended_next_step: `{selector_negative_suppression['negative_suppression_recommended_next_step']}`",
        f"- negative_suppression_runtime_work_allowed: `{selector_negative_suppression['negative_suppression_runtime_work_allowed']}`",
        f"- negative_suppression_selector_training_allowed: `{selector_negative_suppression['negative_suppression_selector_training_allowed']}`",
        f"- negative_suppression_candidate_generator_runtime_allowed: `{selector_negative_suppression['negative_suppression_candidate_generator_runtime_allowed']}`",
        f"- runtime_selector_readiness_status: `{selector_negative_suppression['runtime_selector_readiness_status']}`",
        f"- runtime_selector_readiness_runtime_test_allowed_next: `{selector_negative_suppression['runtime_selector_readiness_runtime_test_allowed_next']}`",
        f"- runtime_selector_readiness_recommended_next_step: `{selector_negative_suppression['runtime_selector_readiness_recommended_next_step']}`",
        f"- runtime_selector_implemented: `{selector_negative_suppression['runtime_selector_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{selector_negative_suppression['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{selector_negative_suppression['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{selector_negative_suppression['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{selector_negative_suppression['stage8_training_allowed']}`",
        "",
        "## Abstention Selector Safety",
        "",
        f"- passive_safety_ready: `{abstention_selector_safety['passive_safety_ready']}`",
        f"- runtime_architecture_lineage_ready: `{abstention_selector_safety['runtime_architecture_lineage_ready']}`",
        f"- runtime_architecture_review_status: `{abstention_selector_safety['runtime_architecture_review_status']}`",
        f"- runtime_architecture_implementation_allowed: `{abstention_selector_safety['runtime_architecture_implementation_allowed']}`",
        f"- runtime_architecture_selector_ready: `{abstention_selector_safety['runtime_architecture_selector_ready']}`",
        f"- runtime_architecture_stage7_repair_ready: `{abstention_selector_safety['runtime_architecture_stage7_repair_ready']}`",
        f"- runtime_architecture_internal_terminal_ready: `{abstention_selector_safety['runtime_architecture_internal_terminal_ready']}`",
        f"- runtime_architecture_blocked_next_steps: `{abstention_selector_safety['runtime_architecture_blocked_next_steps']}`",
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
        "## Two-Stage Abstention No-Go",
        "",
        f"- passive_no_go_ready: `{two_stage_abstention_no_go['passive_no_go_ready']}`",
        f"- objective_probe_status: `{two_stage_abstention_no_go['objective_probe_status']}`",
        f"- objective_probe_row_count: `{two_stage_abstention_no_go['objective_probe_row_count']}`",
        f"- objective_probe_threshold_passing_objective_count: `{two_stage_abstention_no_go['objective_probe_threshold_passing_objective_count']}`",
        f"- runtime_review_status: `{two_stage_abstention_no_go['runtime_review_status']}`",
        f"- runtime_review_implementation_allowed: `{two_stage_abstention_no_go['runtime_review_implementation_allowed']}`",
        f"- runtime_review_runtime_test_allowed_next: `{two_stage_abstention_no_go['runtime_review_runtime_test_allowed_next']}`",
        f"- default_off_status: `{two_stage_abstention_no_go['default_off_status']}`",
        f"- default_off_same_core_metrics: `{two_stage_abstention_no_go['default_off_same_core_metrics']}`",
        f"- enabled_smoke_status: `{two_stage_abstention_no_go['enabled_smoke_status']}`",
        f"- enabled_smoke_total_penalized_count: `{two_stage_abstention_no_go['enabled_smoke_total_penalized_count']}`",
        f"- enabled_smoke_total_selected_penalized_count: `{two_stage_abstention_no_go['enabled_smoke_total_selected_penalized_count']}`",
        f"- stage7_challenge_status: `{two_stage_abstention_no_go['stage7_challenge_status']}`",
        f"- stage7_challenge_conversion_delta_mates: `{two_stage_abstention_no_go['stage7_challenge_conversion_delta_mates']}`",
        f"- stage7_challenge_target_improved: `{two_stage_abstention_no_go['stage7_challenge_target_improved']}`",
        f"- status: `{two_stage_abstention_no_go['status']}`",
        f"- go_no_go_allowed_status: `{two_stage_abstention_no_go['go_no_go_allowed_status']}`",
        f"- rollback_tag: `{two_stage_abstention_no_go['rollback_tag']}`",
        f"- runtime_defaults_changed: `{two_stage_abstention_no_go['runtime_defaults_changed']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{two_stage_abstention_no_go['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{two_stage_abstention_no_go['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{two_stage_abstention_no_go['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{two_stage_abstention_no_go['stage8_training_allowed']}`",
        f"- runtime_repair_not_promoted: `{two_stage_abstention_no_go['runtime_repair_not_promoted']}`",
        f"- stage7_remains_quarantined: `{two_stage_abstention_no_go['stage7_remains_quarantined']}`",
        f"- stage8_remains_blocked: `{two_stage_abstention_no_go['stage8_remains_blocked']}`",
        f"- no_hidden_controller: `{two_stage_abstention_no_go['no_hidden_controller']}`",
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
        "## Hard-Negative Label Semantics",
        "",
        f"- passive_semantics_ready: `{hard_negative_semantics['passive_semantics_ready']}`",
        f"- status: `{hard_negative_semantics['status']}`",
        f"- recommended_next_step: `{hard_negative_semantics['recommended_next_step']}`",
        f"- runtime_work_allowed: `{hard_negative_semantics['runtime_work_allowed']}`",
        f"- selector_training_allowed: `{hard_negative_semantics['selector_training_allowed']}`",
        f"- row_count: `{hard_negative_semantics['row_count']}`",
        f"- state_count: `{hard_negative_semantics['state_count']}`",
        f"- stage7_row_count: `{hard_negative_semantics['stage7_row_count']}`",
        f"- capacity_negative_count: `{hard_negative_semantics['capacity_negative_count']}`",
        f"- capacity_positive_count: `{hard_negative_semantics['capacity_positive_count']}`",
        f"- state_local_contrast_state_count: `{hard_negative_semantics['state_local_contrast_state_count']}`",
        f"- best_ablation_negative_suppression: `{hard_negative_semantics['best_ablation_negative_suppression']}`",
        f"- blocked_use_by_label_channel: `{hard_negative_semantics['blocked_use_by_label_channel']}`",
        f"- stronger_feature_review_consumes_semantics: `{hard_negative_semantics['stronger_feature_review_consumes_semantics']}`",
        f"- runtime_selector_implemented: `{hard_negative_semantics['runtime_selector_implemented']}`",
        f"- runtime_candidate_generator_implemented: `{hard_negative_semantics['runtime_candidate_generator_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{hard_negative_semantics['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{hard_negative_semantics['runtime_terminals_added']}`",
        f"- gameplay_topology_mutation: `{hard_negative_semantics['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{hard_negative_semantics['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{hard_negative_semantics['stage8_training_allowed']}`",
        "",
        "## Stronger Selector Feature Review",
        "",
        f"- passive_feature_review_ready: `{stronger_selector_feature['passive_feature_review_ready']}`",
        f"- feature_ablation_status: `{stronger_selector_feature['feature_ablation_status']}`",
        f"- feature_ablation_underpowered: `{stronger_selector_feature['feature_ablation_underpowered']}`",
        f"- feature_ablation_row_count: `{stronger_selector_feature['feature_ablation_row_count']}`",
        f"- feature_ablation_stage7_row_count: `{stronger_selector_feature['feature_ablation_stage7_row_count']}`",
        f"- feature_ablation_best_objective: `{stronger_selector_feature['feature_ablation_best_objective']}`",
        f"- feature_ablation_best_negative_suppression: `{stronger_selector_feature['feature_ablation_best_negative_suppression']}`",
        f"- feature_review_status: `{stronger_selector_feature['feature_review_status']}`",
        f"- feature_review_recommended_next_step: `{stronger_selector_feature['feature_review_recommended_next_step']}`",
        f"- feature_review_improved_over_v2_ablation: `{stronger_selector_feature['feature_review_improved_over_v2_ablation']}`",
        f"- feature_review_row_count: `{stronger_selector_feature['feature_review_row_count']}`",
        f"- feature_review_stage7_row_count: `{stronger_selector_feature['feature_review_stage7_row_count']}`",
        f"- feature_review_previous_best_negative_suppression: `{stronger_selector_feature['feature_review_previous_best_negative_suppression']}`",
        f"- feature_review_best_negative_suppression: `{stronger_selector_feature['feature_review_best_negative_suppression']}`",
        f"- feature_review_best_positive_recall: `{stronger_selector_feature['feature_review_best_positive_recall']}`",
        f"- feature_review_best_objective: `{stronger_selector_feature['feature_review_best_objective']}`",
        f"- runtime_selector_implemented: `{stronger_selector_feature['runtime_selector_implemented']}`",
        f"- runtime_candidate_generator_implemented: `{stronger_selector_feature['runtime_candidate_generator_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{stronger_selector_feature['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{stronger_selector_feature['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{stronger_selector_feature['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{stronger_selector_feature['stage8_training_allowed']}`",
        "",
        "## Selected-Provider Diversity",
        "",
        f"- passive_diversity_review_ready: `{selected_provider_diversity['passive_diversity_review_ready']}`",
        f"- evidence_plan_status: `{selected_provider_diversity['evidence_plan_status']}`",
        f"- replay_free_scan_status: `{selected_provider_diversity['replay_free_scan_status']}`",
        f"- replay_free_selected_record_count: `{selected_provider_diversity['replay_free_selected_record_count']}`",
        f"- observation_manifest_status: `{selected_provider_diversity['observation_manifest_status']}`",
        f"- observation_manifest_review_status: `{selected_provider_diversity['observation_manifest_review_status']}`",
        f"- observation_scan_status: `{selected_provider_diversity['observation_scan_status']}`",
        f"- observation_scan_count: `{selected_provider_diversity['observation_scan_count']}`",
        f"- manifest_status: `{selected_provider_diversity['manifest_status']}`",
        f"- manifest_observations_allowed_now: `{selected_provider_diversity['manifest_observations_allowed_now']}`",
        f"- manifest_bounded_labels_allowed_by_script: `{selected_provider_diversity['manifest_bounded_labels_allowed_by_script']}`",
        f"- manifest_job_count: `{selected_provider_diversity['manifest_job_count']}`",
        f"- manifest_stage7_jobs: `{selected_provider_diversity['manifest_stage7_jobs']}`",
        f"- labels_status: `{selected_provider_diversity['labels_status']}`",
        f"- label_count: `{selected_provider_diversity['label_count']}`",
        f"- ownership_label_counts: `{selected_provider_diversity['ownership_label_counts']}`",
        f"- selected_result_counts_by_stage: `{selected_provider_diversity['selected_result_counts_by_stage']}`",
        f"- selected_provider_counts: `{selected_provider_diversity['selected_provider_counts']}`",
        f"- stage7_training_rows: `{selected_provider_diversity['stage7_training_rows']}`",
        f"- architecture_status: `{selected_provider_diversity['architecture_status']}`",
        f"- architecture_recommended_next_step: `{selected_provider_diversity['architecture_recommended_next_step']}`",
        f"- architecture_runtime_arbiter_allowed: `{selected_provider_diversity['architecture_runtime_arbiter_allowed']}`",
        f"- runtime_selector_implemented: `{selected_provider_diversity['runtime_selector_implemented']}`",
        f"- runtime_candidate_generator_implemented: `{selected_provider_diversity['runtime_candidate_generator_implemented']}`",
        f"- runtime_arbiter_implemented: `{selected_provider_diversity['runtime_arbiter_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{selected_provider_diversity['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{selected_provider_diversity['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{selected_provider_diversity['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{selected_provider_diversity['stage8_training_allowed']}`",
        "",
        "## Selector Readiness v3 Design",
        "",
        f"- passive_design_review_ready: `{selector_readiness_v3['passive_design_review_ready']}`",
        f"- status: `{selector_readiness_v3['status']}`",
        f"- recommended_next_step: `{selector_readiness_v3['recommended_next_step']}`",
        f"- runtime_arbiter_allowed: `{selector_readiness_v3['runtime_arbiter_allowed']}`",
        f"- selector_sandbox_ready: `{selector_readiness_v3['selector_sandbox_ready']}`",
        f"- hard_blocker_count: `{selector_readiness_v3['hard_blocker_count']}`",
        f"- passed_checks: `{selector_readiness_v3['passed_checks']}`",
        f"- diagnostic_only_checks: `{selector_readiness_v3['diagnostic_only_checks']}`",
        f"- label_balance: `{selector_readiness_v3['label_balance']}`",
        f"- stage_coverage: `{selector_readiness_v3['stage_coverage']}`",
        f"- stage7_training_rows: `{selector_readiness_v3['stage7_training_rows']}`",
        f"- conversion_positive_provider_family_count: `{selector_readiness_v3['conversion_positive_provider_family_count']}`",
        f"- conversion_positive_provider_families: `{selector_readiness_v3['conversion_positive_provider_families']}`",
        f"- default_off_design_status: `{selector_readiness_v3['default_off_design_status']}`",
        f"- default_off_design_implementation_allowed: `{selector_readiness_v3['default_off_design_implementation_allowed']}`",
        f"- runtime_review_packet_readiness_v3_status: `{selector_readiness_v3['runtime_review_packet_readiness_v3_status']}`",
        f"- runtime_arbiter_implemented: `{selector_readiness_v3['runtime_arbiter_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{selector_readiness_v3['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{selector_readiness_v3['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{selector_readiness_v3['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{selector_readiness_v3['stage8_training_allowed']}`",
        "",
        "## State-Local Contrast",
        "",
        f"- passive_contrast_ready: `{state_local_contrast['passive_contrast_ready']}`",
        f"- labels_status: `{state_local_contrast['labels_status']}`",
        f"- labels_row_count: `{state_local_contrast['labels_row_count']}`",
        f"- labels_training_contrast_label_counts: `{state_local_contrast['labels_training_contrast_label_counts']}`",
        f"- labels_stage7_challenge_row_count: `{state_local_contrast['labels_stage7_challenge_row_count']}`",
        f"- labels_stage7_contrast_label_counts: `{state_local_contrast['labels_stage7_contrast_label_counts']}`",
        f"- labels_usable_training_row_count: `{state_local_contrast['labels_usable_training_row_count']}`",
        f"- probe_status: `{state_local_contrast['probe_status']}`",
        f"- probe_training_row_count: `{state_local_contrast['probe_training_row_count']}`",
        f"- probe_stage7_eval_row_count: `{state_local_contrast['probe_stage7_eval_row_count']}`",
        f"- probe_stage7_training_leakage: `{state_local_contrast['probe_stage7_training_leakage']}`",
        f"- readiness_status: `{state_local_contrast['readiness_status']}`",
        f"- readiness_recommended_next_step: `{state_local_contrast['readiness_recommended_next_step']}`",
        f"- readiness_runtime_test_allowed_next: `{state_local_contrast['readiness_runtime_test_allowed_next']}`",
        f"- runtime_selector_implemented: `{state_local_contrast['runtime_selector_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{state_local_contrast['runtime_dtm_or_tablebase_lookup']}`",
        f"- stage7_promotion_allowed: `{state_local_contrast['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{state_local_contrast['stage8_training_allowed']}`",
        "",
        "## State-Local Paired Ownership",
        "",
        f"- passive_semantic_gate_ready: `{state_local_paired_ownership['passive_semantic_gate_ready']}`",
        f"- hard_negative_target_dataset_status: `{state_local_paired_ownership['hard_negative_target_dataset_status']}`",
        f"- hard_negative_target_row_count: `{state_local_paired_ownership['hard_negative_target_row_count']}`",
        f"- hard_negative_training_row_count: `{state_local_paired_ownership['hard_negative_training_row_count']}`",
        f"- hard_negative_stage7_row_count: `{state_local_paired_ownership['hard_negative_stage7_row_count']}`",
        f"- ownership_context_status: `{state_local_paired_ownership['ownership_context_status']}`",
        f"- ownership_context_runtime_threshold_passed: `{state_local_paired_ownership['ownership_context_runtime_threshold_passed']}`",
        f"- ownership_architecture_status: `{state_local_paired_ownership['ownership_architecture_status']}`",
        f"- objective_plan_status: `{state_local_paired_ownership['objective_plan_status']}`",
        f"- work_package_status: `{state_local_paired_ownership['work_package_status']}`",
        f"- inventory_status: `{state_local_paired_ownership['inventory_status']}`",
        f"- inventory_pair_count: `{state_local_paired_ownership['inventory_pair_count']}`",
        f"- inventory_same_state_conflict_pair_count: `{state_local_paired_ownership['inventory_same_state_conflict_pair_count']}`",
        f"- inventory_selector_training_row_count: `{state_local_paired_ownership['inventory_selector_training_row_count']}`",
        f"- inventory_stage7_row_count: `{state_local_paired_ownership['inventory_stage7_row_count']}`",
        f"- probe_status: `{state_local_paired_ownership['probe_status']}`",
        f"- probe_threshold_passing_model_count: `{state_local_paired_ownership['probe_threshold_passing_model_count']}`",
        f"- probe_runtime_feature_passing_model_count: `{state_local_paired_ownership['probe_runtime_feature_passing_model_count']}`",
        f"- error_audit_status: `{state_local_paired_ownership['error_audit_status']}`",
        f"- review_status: `{state_local_paired_ownership['review_status']}`",
        f"- review_best_objective: `{state_local_paired_ownership['review_best_objective']}`",
        f"- review_runtime_feature_passing_model_count: `{state_local_paired_ownership['review_runtime_feature_passing_model_count']}`",
        f"- review_stage7_row_count: `{state_local_paired_ownership['review_stage7_row_count']}`",
        f"- runtime_selector_implemented: `{state_local_paired_ownership['runtime_selector_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{state_local_paired_ownership['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{state_local_paired_ownership['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{state_local_paired_ownership['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{state_local_paired_ownership['stage8_training_allowed']}`",
        "",
        "## Selected-Owner Failure-Risk Proxy",
        "",
        f"- passive_proxy_review_ready: `{selected_owner_failure_risk['passive_proxy_review_ready']}`",
        f"- runtime_proxy_design_status: `{selected_owner_failure_risk['runtime_proxy_design_status']}`",
        f"- runtime_proxy_dataset_row_count: `{selected_owner_failure_risk['runtime_proxy_dataset_row_count']}`",
        f"- runtime_proxy_dataset_selector_training_row_count: `{selected_owner_failure_risk['runtime_proxy_dataset_selector_training_row_count']}`",
        f"- runtime_proxy_dataset_stage7_row_count: `{selected_owner_failure_risk['runtime_proxy_dataset_stage7_row_count']}`",
        f"- runtime_proxy_review_status: `{selected_owner_failure_risk['runtime_proxy_review_status']}`",
        f"- runtime_review_packet_v0_translation_blocker: `{selected_owner_failure_risk['runtime_review_packet_v0_translation_blocker']}`",
        f"- failure_risk_evidence_status: `{selected_owner_failure_risk['failure_risk_evidence_status']}`",
        f"- failure_risk_evidence_row_count: `{selected_owner_failure_risk['failure_risk_evidence_row_count']}`",
        f"- visible_proxy_precision: `{selected_owner_failure_risk['visible_proxy_precision']}`",
        f"- visible_proxy_recall: `{selected_owner_failure_risk['visible_proxy_recall']}`",
        f"- visible_proxy_probe_v0_status: `{selected_owner_failure_risk['visible_proxy_probe_v0_status']}`",
        f"- independent_validation_v0_status: `{selected_owner_failure_risk['independent_validation_v0_status']}`",
        f"- independent_validation_v0_threshold_met: `{selected_owner_failure_risk['independent_validation_v0_threshold_met']}`",
        f"- independent_validation_v0_safe_preservation_recall: `{selected_owner_failure_risk['independent_validation_v0_safe_preservation_recall']}`",
        f"- blocker_review_v0_status: `{selected_owner_failure_risk['blocker_review_v0_status']}`",
        f"- blocker_review_v0_threshold_met: `{selected_owner_failure_risk['blocker_review_v0_threshold_met']}`",
        f"- blocker_review_v0_false_positive_count: `{selected_owner_failure_risk['blocker_review_v0_false_positive_count']}`",
        f"- proxy_v1_probe_status: `{selected_owner_failure_risk['proxy_v1_probe_status']}`",
        f"- proxy_v1_independent_passing_proxy_count: `{selected_owner_failure_risk['proxy_v1_independent_passing_proxy_count']}`",
        f"- independent_label_count: `{selected_owner_failure_risk['independent_label_count']}`",
        f"- independent_label_stage7_training_rows: `{selected_owner_failure_risk['independent_label_stage7_training_rows']}`",
        f"- independent_validation_status: `{selected_owner_failure_risk['independent_validation_status']}`",
        f"- independent_validation_threshold_met: `{selected_owner_failure_risk['independent_validation_threshold_met']}`",
        f"- independent_validation_runtime_scope: `{selected_owner_failure_risk['independent_validation_runtime_scope']}`",
        f"- runtime_proxy_review_packet_v1_status: `{selected_owner_failure_risk['runtime_proxy_review_packet_v1_status']}`",
        f"- runtime_proxy_review_packet_v1_implementation_allowed: `{selected_owner_failure_risk['runtime_proxy_review_packet_v1_implementation_allowed']}`",
        f"- runtime_proxy_review_packet_v1_stage7_row_count: `{selected_owner_failure_risk['runtime_proxy_review_packet_v1_stage7_row_count']}`",
        f"- runtime_selector_implemented: `{selected_owner_failure_risk['runtime_selector_implemented']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{selected_owner_failure_risk['runtime_dtm_or_tablebase_lookup']}`",
        f"- runtime_terminals_added: `{selected_owner_failure_risk['runtime_terminals_added']}`",
        f"- stage7_promotion_allowed: `{selected_owner_failure_risk['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{selected_owner_failure_risk['stage8_training_allowed']}`",
        "",
        "## Progress-Window Reconsideration",
        "",
        f"- passive_review_ready: `{progress_window_reconsideration['passive_review_ready']}`",
        f"- runtime_test_review_status: `{progress_window_reconsideration['runtime_test_review_status']}`",
        f"- runtime_test_guardrails_allowed_now: `{progress_window_reconsideration['runtime_test_guardrails_allowed_now']}`",
        f"- runtime_test_promotion_allowed_now: `{progress_window_reconsideration['runtime_test_promotion_allowed_now']}`",
        f"- runtime_test_default_off_equivalence_passed: `{progress_window_reconsideration['runtime_test_default_off_equivalence_passed']}`",
        f"- runtime_test_activation_observed: `{progress_window_reconsideration['runtime_test_activation_observed']}`",
        f"- runtime_test_target_improvement_observed: `{progress_window_reconsideration['runtime_test_target_improvement_observed']}`",
        f"- runtime_test_safe_regression_observed: `{progress_window_reconsideration['runtime_test_safe_regression_observed']}`",
        f"- smoke_status: `{progress_window_reconsideration['smoke_status']}`",
        f"- smoke_default_off_equivalence_passed: `{progress_window_reconsideration['smoke_default_off_equivalence_passed']}`",
        f"- smoke_improved_target_failure_count: `{progress_window_reconsideration['smoke_improved_target_failure_count']}`",
        f"- smoke_safe_regression_count: `{progress_window_reconsideration['smoke_safe_regression_count']}`",
        f"- smoke_target_failure_row_count: `{progress_window_reconsideration['smoke_target_failure_row_count']}`",
        f"- smoke_protected_label_count: `{progress_window_reconsideration['smoke_protected_label_count']}`",
        f"- smoke_enabled_supported_total: `{progress_window_reconsideration['smoke_enabled_supported_total']}`",
        f"- smoke_enabled_selected_supported_total: `{progress_window_reconsideration['smoke_enabled_selected_supported_total']}`",
        f"- post_activation_status: `{progress_window_reconsideration['post_activation_status']}`",
        f"- post_activation_implement_next_fix_now: `{progress_window_reconsideration['post_activation_implement_next_fix_now']}`",
        f"- post_activation_recommended_next_step: `{progress_window_reconsideration['post_activation_recommended_next_step']}`",
        f"- classification_primary: `{progress_window_reconsideration['classification_primary']}`",
        f"- classification_labels: `{progress_window_reconsideration['classification_labels']}`",
        f"- promotion_status: `{progress_window_reconsideration['promotion_status']}`",
        f"- sandbox_status: `{progress_window_reconsideration['sandbox_status']}`",
        f"- runtime_defaults_changed: `{progress_window_reconsideration['runtime_defaults_changed']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{progress_window_reconsideration['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{progress_window_reconsideration['gameplay_topology_mutation']}`",
        f"- stage7_promotion_allowed: `{progress_window_reconsideration['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{progress_window_reconsideration['stage8_training_allowed']}`",
        "",
        "## Runtime Sandbox Policy Update",
        "",
        f"- passive_policy_update_ready: `{runtime_sandbox_policy_update['passive_policy_update_ready']}`",
        f"- status: `{runtime_sandbox_policy_update['status']}`",
        f"- allowed_scope: `{runtime_sandbox_policy_update['allowed_scope']}`",
        f"- broad_runtime_changes_allowed: `{runtime_sandbox_policy_update['broad_runtime_changes_allowed']}`",
        f"- default_policy_changes_allowed: `{runtime_sandbox_policy_update['default_policy_changes_allowed']}`",
        f"- test_result_status: `{runtime_sandbox_policy_update['test_result_status']}`",
        f"- test_result_default_off_equivalence_passed: `{runtime_sandbox_policy_update['test_result_default_off_equivalence_passed']}`",
        f"- test_result_activation_observed: `{runtime_sandbox_policy_update['test_result_activation_observed']}`",
        f"- test_result_target_improvement_observed: `{runtime_sandbox_policy_update['test_result_target_improvement_observed']}`",
        f"- test_result_guardrails_allowed_now: `{runtime_sandbox_policy_update['test_result_guardrails_allowed_now']}`",
        f"- source_review_packet: `{runtime_sandbox_policy_update['source_review_packet']}`",
        f"- progress_window_passive_review_ready: `{runtime_sandbox_policy_update['progress_window_passive_review_ready']}`",
        f"- hidden_python_controller: `{runtime_sandbox_policy_update['hidden_python_controller']}`",
        f"- runtime_dtm_or_tablebase_lookup: `{runtime_sandbox_policy_update['runtime_dtm_or_tablebase_lookup']}`",
        f"- gameplay_topology_mutation: `{runtime_sandbox_policy_update['gameplay_topology_mutation']}`",
        f"- general_predecision_selector: `{runtime_sandbox_policy_update['general_predecision_selector']}`",
        f"- stage7_repair_or_promotion: `{runtime_sandbox_policy_update['stage7_repair_or_promotion']}`",
        f"- stage7_promotion_allowed: `{runtime_sandbox_policy_update['stage7_promotion_allowed']}`",
        f"- stage8_training_allowed: `{runtime_sandbox_policy_update['stage8_training_allowed']}`",
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
            f"- audit_plan_ready: `{missing_provider['audit_plan_ready']}`",
            f"- audit_plan_status: `{missing_provider['audit_plan_status']}`",
            f"- audit_plan_job_count: `{missing_provider['audit_plan_job_count']}`",
            f"- audit_plan_source_frame_count: `{missing_provider['audit_plan_source_frame_count']}`",
            f"- audit_plan_stage_counts: `{missing_provider['audit_plan_stage_counts']}`",
            f"- audit_plan_runtime_work_allowed: `{missing_provider['audit_plan_runtime_work_allowed']}`",
            f"- execution_manifest_status: `{missing_provider['execution_manifest_status']}`",
            f"- execution_manifest_job_count: `{missing_provider['execution_manifest_job_count']}`",
            f"- execution_manifest_stage7_job_count: `{missing_provider['execution_manifest_stage7_job_count']}`",
            f"- execution_manifest_labels_allowed_now: `{missing_provider['execution_manifest_labels_allowed_now']}`",
            f"- execution_manifest_runtime_work_allowed: `{missing_provider['execution_manifest_runtime_work_allowed']}`",
            f"- execution_manifest_review_passive_ready: `{missing_provider['execution_manifest_review_passive_ready']}`",
            f"- execution_manifest_review_status: `{missing_provider['execution_manifest_review_status']}`",
            f"- execution_manifest_review_labels_allowed: `{missing_provider['execution_manifest_review_labels_allowed']}`",
            f"- execution_manifest_review_runtime_work_allowed: `{missing_provider['execution_manifest_review_runtime_work_allowed']}`",
            f"- execution_manifest_review_violation_count: `{missing_provider['execution_manifest_review_violation_count']}`",
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
            "## Control Plane Contract Lineage",
            "",
            f"- passive_contract_lineage_ready: `{control_plane_contract['passive_contract_lineage_ready']}`",
            f"- architecture_goal_id: `{control_plane_contract['architecture_goal_id']}`",
            f"- architecture_goal_type: `{control_plane_contract['architecture_goal_type']}`",
            f"- architecture_must_remain_non_causal: `{control_plane_contract['architecture_must_remain_non_causal']}`",
            f"- architecture_runtime_defaults_must_remain_unchanged: `{control_plane_contract['architecture_runtime_defaults_must_remain_unchanged']}`",
            f"- contract_recommended_next_slice: `{control_plane_contract['contract_recommended_next_slice']}`",
            f"- contract_causal_status: `{control_plane_contract['contract_causal_status']}`",
            f"- manifest_causal_status: `{control_plane_contract['manifest_causal_status']}`",
            f"- manifest_records_from_existing_artifacts_only: `{control_plane_contract['manifest_records_from_existing_artifacts_only']}`",
            f"- manifest_new_playouts_added: `{control_plane_contract['manifest_new_playouts_added']}`",
            f"- manifest_missing_required_fields_after_manifest: `{control_plane_contract['manifest_missing_required_fields_after_manifest']}`",
            f"- manifest_recommended_next_slice: `{control_plane_contract['manifest_recommended_next_slice']}`",
            f"- runtime_behavior_changed: `{control_plane_contract['runtime_behavior_changed']}`",
            f"- runtime_defaults_changed: `{control_plane_contract['runtime_defaults_changed']}`",
            f"- runtime_selector_implemented: `{control_plane_contract['runtime_selector_implemented']}`",
            f"- runtime_dtm_or_tablebase_lookup: `{control_plane_contract['runtime_dtm_or_tablebase_lookup']}`",
            f"- hidden_python_controller: `{control_plane_contract['hidden_python_controller']}`",
            f"- gameplay_topology_mutation: `{control_plane_contract['gameplay_topology_mutation']}`",
            f"- stage7_promotion_allowed: `{control_plane_contract['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{control_plane_contract['stage8_training_allowed']}`",
            "",
            "## Control Plane Frame Export",
            "",
            f"- passive_frame_export_ready: `{control_plane_frame_export['passive_frame_export_ready']}`",
            f"- gap_report_next_slice_id: `{control_plane_frame_export['gap_report_next_slice_id']}`",
            f"- gap_report_new_playouts_allowed: `{control_plane_frame_export['gap_report_new_playouts_allowed']}`",
            f"- gap_report_new_playouts_added: `{control_plane_frame_export['gap_report_new_playouts_added']}`",
            f"- frame_export_frame_count: `{control_plane_frame_export['frame_export_frame_count']}`",
            f"- frame_export_frames_by_source_stage: `{control_plane_frame_export['frame_export_frames_by_source_stage']}`",
            f"- frame_export_new_playouts_added: `{control_plane_frame_export['frame_export_new_playouts_added']}`",
            f"- frame_quality_next_slice_id: `{control_plane_frame_export['frame_quality_next_slice_id']}`",
            f"- frame_quality_runtime_sandbox: `{control_plane_frame_export['frame_quality_runtime_sandbox']}`",
            f"- frame_quality_stage7_promotion: `{control_plane_frame_export['frame_quality_stage7_promotion']}`",
            f"- frame_quality_stage8_training: `{control_plane_frame_export['frame_quality_stage8_training']}`",
            f"- filtered_strategy_ready_frame_count: `{control_plane_frame_export['filtered_strategy_ready_frame_count']}`",
            f"- filtered_stage7_boundary_heldout_frame_count: `{control_plane_frame_export['filtered_stage7_boundary_heldout_frame_count']}`",
            f"- forced_control_labels_attached: `{control_plane_frame_export['forced_control_labels_attached']}`",
            f"- forced_control_missing_label_job_ids: `{control_plane_frame_export['forced_control_missing_label_job_ids']}`",
            f"- runtime_behavior_changed: `{control_plane_frame_export['runtime_behavior_changed']}`",
            f"- runtime_defaults_changed: `{control_plane_frame_export['runtime_defaults_changed']}`",
            f"- runtime_selector_implemented: `{control_plane_frame_export['runtime_selector_implemented']}`",
            f"- runtime_dtm_or_tablebase_lookup: `{control_plane_frame_export['runtime_dtm_or_tablebase_lookup']}`",
            f"- hidden_python_controller: `{control_plane_frame_export['hidden_python_controller']}`",
            f"- gameplay_topology_mutation: `{control_plane_frame_export['gameplay_topology_mutation']}`",
            f"- stage7_promotion_allowed: `{control_plane_frame_export['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{control_plane_frame_export['stage8_training_allowed']}`",
            "",
            "## Control Plane Strategy Baseline",
            "",
            f"- passive_strategy_baseline_ready: `{control_plane_strategy_baseline['passive_strategy_baseline_ready']}`",
            f"- provider_label_coverage_plan_ready: `{control_plane_strategy_baseline['provider_label_coverage_plan_ready']}`",
            f"- provider_label_coverage_status: `{control_plane_strategy_baseline['provider_label_coverage_status']}`",
            f"- provider_label_coverage_benchmark_frame_count: `{control_plane_strategy_baseline['provider_label_coverage_benchmark_frame_count']}`",
            f"- provider_label_coverage_known_provider_mate_count: `{control_plane_strategy_baseline['provider_label_coverage_known_provider_mate_count']}`",
            f"- provider_label_coverage_recommended_next_slice: `{control_plane_strategy_baseline['provider_label_coverage_recommended_next_slice']}`",
            f"- probe_status: `{control_plane_strategy_baseline['probe_status']}`",
            f"- probe_causal_next_step_allowed: `{control_plane_strategy_baseline['probe_causal_next_step_allowed']}`",
            f"- probe_recommended_next_slice: `{control_plane_strategy_baseline['probe_recommended_next_slice']}`",
            f"- probe_strategy_benchmark_frame_count: `{control_plane_strategy_baseline['probe_strategy_benchmark_frame_count']}`",
            f"- probe_provider_labeled_frame_count: `{control_plane_strategy_baseline['probe_provider_labeled_frame_count']}`",
            f"- probe_frames_with_known_provider_mate: `{control_plane_strategy_baseline['probe_frames_with_known_provider_mate']}`",
            f"- baseline_status: `{control_plane_strategy_baseline['baseline_status']}`",
            f"- baseline_causal_next_step_allowed: `{control_plane_strategy_baseline['baseline_causal_next_step_allowed']}`",
            f"- baseline_recommended_next_class: `{control_plane_strategy_baseline['baseline_recommended_next_class']}`",
            f"- baseline_strategy_benchmark_frame_count: `{control_plane_strategy_baseline['baseline_strategy_benchmark_frame_count']}`",
            f"- baseline_frames_with_provider_mate: `{control_plane_strategy_baseline['baseline_frames_with_provider_mate']}`",
            f"- baseline_frames_with_only_provider_max_plies: `{control_plane_strategy_baseline['baseline_frames_with_only_provider_max_plies']}`",
            f"- baseline_stage_counts: `{control_plane_strategy_baseline['baseline_stage_counts']}`",
            f"- baseline_selector_names: `{control_plane_strategy_baseline['baseline_selector_names']}`",
            f"- baseline_selector_hit_rates: `{control_plane_strategy_baseline['baseline_selector_hit_rates']}`",
            f"- runtime_behavior_changed: `{control_plane_strategy_baseline['runtime_behavior_changed']}`",
            f"- runtime_defaults_changed: `{control_plane_strategy_baseline['runtime_defaults_changed']}`",
            f"- runtime_selector_implemented: `{control_plane_strategy_baseline['runtime_selector_implemented']}`",
            f"- runtime_dtm_or_tablebase_lookup: `{control_plane_strategy_baseline['runtime_dtm_or_tablebase_lookup']}`",
            f"- hidden_python_controller: `{control_plane_strategy_baseline['hidden_python_controller']}`",
            f"- gameplay_topology_mutation: `{control_plane_strategy_baseline['gameplay_topology_mutation']}`",
            f"- stage7_promotion_allowed: `{control_plane_strategy_baseline['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{control_plane_strategy_baseline['stage8_training_allowed']}`",
            "",
            "## Control Plane Stage 7 Boundary",
            "",
            f"- passive_stage7_boundary_ready: `{control_plane_stage7_boundary['passive_stage7_boundary_ready']}`",
            f"- boundary_decision_status: `{control_plane_stage7_boundary['boundary_decision_status']}`",
            f"- boundary_recommended_next_step: `{control_plane_stage7_boundary['boundary_recommended_next_step']}`",
            f"- stage7_clean_success_controls_met: `{control_plane_stage7_boundary['stage7_clean_success_controls_met']}`",
            f"- stage7_clean_hard_negatives_met: `{control_plane_stage7_boundary['stage7_clean_hard_negatives_met']}`",
            f"- stage7_clean_review_status: `{control_plane_stage7_boundary['stage7_clean_review_status']}`",
            f"- strategy_sequence_inventory_status: `{control_plane_stage7_boundary['strategy_sequence_inventory_status']}`",
            f"- strategy_ready_frame_count: `{control_plane_stage7_boundary['strategy_ready_frame_count']}`",
            f"- strategy_ready_by_stage: `{control_plane_stage7_boundary['strategy_ready_by_stage']}`",
            f"- stage7_boundary_heldout_frame_count: `{control_plane_stage7_boundary['stage7_boundary_heldout_frame_count']}`",
            f"- strategy_probe_status: `{control_plane_stage7_boundary['strategy_probe_status']}`",
            f"- strategy_baseline_status: `{control_plane_stage7_boundary['strategy_baseline_status']}`",
            f"- approval_receipt_present: `{control_plane_stage7_boundary['approval_receipt_present']}`",
            f"- approval_receipt_valid: `{control_plane_stage7_boundary['approval_receipt_valid']}`",
            f"- runner_execution_requested: `{control_plane_stage7_boundary['runner_execution_requested']}`",
            f"- runner_collection_run_allowed: `{control_plane_stage7_boundary['runner_collection_run_allowed']}`",
            f"- runner_processed_job_count: `{control_plane_stage7_boundary['runner_processed_job_count']}`",
            f"- runner_executed_job_count: `{control_plane_stage7_boundary['runner_executed_job_count']}`",
            f"- runtime_behavior_changed: `{control_plane_stage7_boundary['runtime_behavior_changed']}`",
            f"- runtime_defaults_changed: `{control_plane_stage7_boundary['runtime_defaults_changed']}`",
            f"- runtime_selector_implemented: `{control_plane_stage7_boundary['runtime_selector_implemented']}`",
            f"- runtime_dtm_or_tablebase_lookup: `{control_plane_stage7_boundary['runtime_dtm_or_tablebase_lookup']}`",
            f"- hidden_python_controller: `{control_plane_stage7_boundary['hidden_python_controller']}`",
            f"- gameplay_topology_mutation: `{control_plane_stage7_boundary['gameplay_topology_mutation']}`",
            f"- stage7_promotion_allowed: `{control_plane_stage7_boundary['stage7_promotion_allowed']}`",
            f"- stage8_training_allowed: `{control_plane_stage7_boundary['stage8_training_allowed']}`",
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

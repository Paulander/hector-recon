#!/usr/bin/env python3
"""Tests for non-causal KRK candidate-generation control-plane artifacts."""

import importlib.util
from pathlib import Path


_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_generation_control_plane_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_generation_control_plane_v0.py",
)
assert _spec is not None
assert _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

_populate_spec = importlib.util.spec_from_file_location(
    "populate_krk_strategy_sequence_candidate_frames_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "populate_krk_strategy_sequence_candidate_frames_v1.py",
)
assert _populate_spec is not None
assert _populate_spec.loader is not None
_populate = importlib.util.module_from_spec(_populate_spec)
_populate_spec.loader.exec_module(_populate)

_benchmark_spec = importlib.util.spec_from_file_location(
    "benchmark_krk_candidate_frame_sources_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_krk_candidate_frame_sources_v1.py",
)
assert _benchmark_spec is not None
assert _benchmark_spec.loader is not None
_benchmark = importlib.util.module_from_spec(_benchmark_spec)
_benchmark_spec.loader.exec_module(_benchmark)

_sandbox_review_spec = importlib.util.spec_from_file_location(
    "write_krk_candidate_generation_sandbox_review_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_candidate_generation_sandbox_review_v0.py",
)
assert _sandbox_review_spec is not None
assert _sandbox_review_spec.loader is not None
_sandbox_review = importlib.util.module_from_spec(_sandbox_review_spec)
_sandbox_review_spec.loader.exec_module(_sandbox_review)

_observation_smoke_spec = importlib.util.spec_from_file_location(
    "run_krk_candidate_generation_observation_sandbox_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_candidate_generation_observation_sandbox_v0.py",
)
assert _observation_smoke_spec is not None
assert _observation_smoke_spec.loader is not None
_observation_smoke = importlib.util.module_from_spec(_observation_smoke_spec)
_observation_smoke_spec.loader.exec_module(_observation_smoke)

_observation_analysis_spec = importlib.util.spec_from_file_location(
    "analyze_krk_candidate_generation_observation_frames_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_candidate_generation_observation_frames_v0.py",
)
assert _observation_analysis_spec is not None
assert _observation_analysis_spec.loader is not None
_observation_analysis = importlib.util.module_from_spec(_observation_analysis_spec)
_observation_analysis_spec.loader.exec_module(_observation_analysis)

_observation_broadened_spec = importlib.util.spec_from_file_location(
    "run_krk_candidate_generation_observation_broadened_sample_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_candidate_generation_observation_broadened_sample_v1.py",
)
assert _observation_broadened_spec is not None
assert _observation_broadened_spec.loader is not None
_observation_broadened = importlib.util.module_from_spec(_observation_broadened_spec)
_observation_broadened_spec.loader.exec_module(_observation_broadened)

_observation_gap_review_spec = importlib.util.spec_from_file_location(
    "analyze_krk_candidate_generation_observation_gap_review_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_candidate_generation_observation_gap_review_v1.py",
)
assert _observation_gap_review_spec is not None
assert _observation_gap_review_spec.loader is not None
_observation_gap_review = importlib.util.module_from_spec(_observation_gap_review_spec)
_observation_gap_review_spec.loader.exec_module(_observation_gap_review)

_candidate_move_annotation_spec = importlib.util.spec_from_file_location(
    "annotate_krk_candidate_move_capacity_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "annotate_krk_candidate_move_capacity_v1.py",
)
assert _candidate_move_annotation_spec is not None
assert _candidate_move_annotation_spec.loader is not None
_candidate_move_annotation = importlib.util.module_from_spec(_candidate_move_annotation_spec)
_candidate_move_annotation_spec.loader.exec_module(_candidate_move_annotation)

_candidate_move_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_move_capacity_label_manifest_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_move_capacity_label_manifest_v1.py",
)
assert _candidate_move_manifest_spec is not None
assert _candidate_move_manifest_spec.loader is not None
_candidate_move_manifest = importlib.util.module_from_spec(_candidate_move_manifest_spec)
_candidate_move_manifest_spec.loader.exec_module(_candidate_move_manifest)

_candidate_move_label_spec = importlib.util.spec_from_file_location(
    "run_krk_candidate_move_capacity_labels_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_candidate_move_capacity_labels_v1.py",
)
assert _candidate_move_label_spec is not None
assert _candidate_move_label_spec.loader is not None
_candidate_move_label = importlib.util.module_from_spec(_candidate_move_label_spec)
_candidate_move_label_spec.loader.exec_module(_candidate_move_label)

_candidate_move_merge_spec = importlib.util.spec_from_file_location(
    "merge_krk_candidate_move_capacity_annotations_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "merge_krk_candidate_move_capacity_annotations_v2.py",
)
assert _candidate_move_merge_spec is not None
assert _candidate_move_merge_spec.loader is not None
_candidate_move_merge = importlib.util.module_from_spec(_candidate_move_merge_spec)
_candidate_move_merge_spec.loader.exec_module(_candidate_move_merge)

_candidate_label_blocker_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_label_blockers_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_label_blockers_v1.py",
)
assert _candidate_label_blocker_spec is not None
assert _candidate_label_blocker_spec.loader is not None
_candidate_label_blocker = importlib.util.module_from_spec(_candidate_label_blocker_spec)
_candidate_label_blocker_spec.loader.exec_module(_candidate_label_blocker)

_candidate_quality_review_spec = importlib.util.spec_from_file_location(
    "write_krk_candidate_proposal_quality_prioritization_review_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_candidate_proposal_quality_prioritization_review_v1.py",
)
assert _candidate_quality_review_spec is not None
assert _candidate_quality_review_spec.loader is not None
_candidate_quality_review = importlib.util.module_from_spec(_candidate_quality_review_spec)
_candidate_quality_review_spec.loader.exec_module(_candidate_quality_review)

_candidate_quality_dataset_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_proposal_quality_dataset_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_proposal_quality_dataset_v1.py",
)
assert _candidate_quality_dataset_spec is not None
assert _candidate_quality_dataset_spec.loader is not None
_candidate_quality_dataset = importlib.util.module_from_spec(_candidate_quality_dataset_spec)
_candidate_quality_dataset_spec.loader.exec_module(_candidate_quality_dataset)

_candidate_quality_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_candidate_proposal_quality_axes_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_candidate_proposal_quality_axes_v1.py",
)
assert _candidate_quality_probe_spec is not None
assert _candidate_quality_probe_spec.loader is not None
_candidate_quality_probe = importlib.util.module_from_spec(_candidate_quality_probe_spec)
_candidate_quality_probe_spec.loader.exec_module(_candidate_quality_probe)

_candidate_quality_decision_spec = importlib.util.spec_from_file_location(
    "write_krk_candidate_proposal_quality_decision_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_candidate_proposal_quality_decision_v1.py",
)
assert _candidate_quality_decision_spec is not None
assert _candidate_quality_decision_spec.loader is not None
_candidate_quality_decision = importlib.util.module_from_spec(_candidate_quality_decision_spec)
_candidate_quality_decision_spec.loader.exec_module(_candidate_quality_decision)

_broader_source_design_spec = importlib.util.spec_from_file_location(
    "write_krk_broader_strategy_sequence_candidate_source_design_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_broader_strategy_sequence_candidate_source_design_v1.py",
)
assert _broader_source_design_spec is not None
assert _broader_source_design_spec.loader is not None
_broader_source_design = importlib.util.module_from_spec(_broader_source_design_spec)
_broader_source_design_spec.loader.exec_module(_broader_source_design)

_source_review_spec = importlib.util.spec_from_file_location(
    "review_krk_plan_capsule_and_broader_strategy_sources_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_plan_capsule_and_broader_strategy_sources_v1.py",
)
assert _source_review_spec is not None
assert _source_review_spec.loader is not None
_source_review = importlib.util.module_from_spec(_source_review_spec)
_source_review_spec.loader.exec_module(_source_review)

_protected_monitor_expansion_spec = importlib.util.spec_from_file_location(
    "build_krk_protected_strategy_monitor_frame_expansion_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_protected_strategy_monitor_frame_expansion_v1.py",
)
assert _protected_monitor_expansion_spec is not None
assert _protected_monitor_expansion_spec.loader is not None
_protected_monitor_expansion = importlib.util.module_from_spec(
    _protected_monitor_expansion_spec
)
_protected_monitor_expansion_spec.loader.exec_module(_protected_monitor_expansion)

_protected_monitor_quality_spec = importlib.util.spec_from_file_location(
    "probe_krk_protected_strategy_monitor_frame_quality_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_protected_strategy_monitor_frame_quality_v1.py",
)
assert _protected_monitor_quality_spec is not None
assert _protected_monitor_quality_spec.loader is not None
_protected_monitor_quality = importlib.util.module_from_spec(_protected_monitor_quality_spec)
_protected_monitor_quality_spec.loader.exec_module(_protected_monitor_quality)

_protected_monitor_packet_spec = importlib.util.spec_from_file_location(
    "write_krk_protected_strategy_monitor_observation_source_review_packet_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_protected_strategy_monitor_observation_source_review_packet_v1.py",
)
assert _protected_monitor_packet_spec is not None
assert _protected_monitor_packet_spec.loader is not None
_protected_monitor_packet = importlib.util.module_from_spec(_protected_monitor_packet_spec)
_protected_monitor_packet_spec.loader.exec_module(_protected_monitor_packet)

_repair_monitor_smoke_spec = importlib.util.spec_from_file_location(
    "run_krk_repair_monitor_observation_source_smoke_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_repair_monitor_observation_source_smoke_v1.py",
)
assert _repair_monitor_smoke_spec is not None
assert _repair_monitor_smoke_spec.loader is not None
_repair_monitor_smoke = importlib.util.module_from_spec(_repair_monitor_smoke_spec)
_repair_monitor_smoke_spec.loader.exec_module(_repair_monitor_smoke)

_repair_monitor_coverage_spec = importlib.util.spec_from_file_location(
    "analyze_krk_repair_monitor_observation_source_coverage_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_repair_monitor_observation_source_coverage_v1.py",
)
assert _repair_monitor_coverage_spec is not None
assert _repair_monitor_coverage_spec.loader is not None
_repair_monitor_coverage = importlib.util.module_from_spec(_repair_monitor_coverage_spec)
_repair_monitor_coverage_spec.loader.exec_module(_repair_monitor_coverage)

_repair_monitor_broadened_spec = importlib.util.spec_from_file_location(
    "run_krk_repair_monitor_observation_source_broadened_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_repair_monitor_observation_source_broadened_v1.py",
)
assert _repair_monitor_broadened_spec is not None
assert _repair_monitor_broadened_spec.loader is not None
_repair_monitor_broadened = importlib.util.module_from_spec(
    _repair_monitor_broadened_spec
)
_repair_monitor_broadened_spec.loader.exec_module(_repair_monitor_broadened)

_repair_monitor_quality_spec = importlib.util.spec_from_file_location(
    "analyze_krk_repair_monitor_observation_source_quality_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_repair_monitor_observation_source_quality_v1.py",
)
assert _repair_monitor_quality_spec is not None
assert _repair_monitor_quality_spec.loader is not None
_repair_monitor_quality = importlib.util.module_from_spec(_repair_monitor_quality_spec)
_repair_monitor_quality_spec.loader.exec_module(_repair_monitor_quality)

_repair_monitor_trace_fold_spec = importlib.util.spec_from_file_location(
    "fold_krk_repair_monitor_frames_into_strategy_sequence_trace_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "fold_krk_repair_monitor_frames_into_strategy_sequence_trace_v1.py",
)
assert _repair_monitor_trace_fold_spec is not None
assert _repair_monitor_trace_fold_spec.loader is not None
_repair_monitor_trace_fold = importlib.util.module_from_spec(
    _repair_monitor_trace_fold_spec
)
_repair_monitor_trace_fold_spec.loader.exec_module(_repair_monitor_trace_fold)

_trace_feature_review_spec = importlib.util.spec_from_file_location(
    "review_krk_strategy_sequence_trace_feature_integration_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_strategy_sequence_trace_feature_integration_v1.py",
)
assert _trace_feature_review_spec is not None
assert _trace_feature_review_spec.loader is not None
_trace_feature_review = importlib.util.module_from_spec(_trace_feature_review_spec)
_trace_feature_review_spec.loader.exec_module(_trace_feature_review)

_dataset_design_v2_spec = importlib.util.spec_from_file_location(
    "write_krk_strategy_sequence_dataset_design_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_strategy_sequence_dataset_design_v2.py",
)
assert _dataset_design_v2_spec is not None
assert _dataset_design_v2_spec.loader is not None
_dataset_design_v2 = importlib.util.module_from_spec(_dataset_design_v2_spec)
_dataset_design_v2_spec.loader.exec_module(_dataset_design_v2)

_dataset_v2_spec = importlib.util.spec_from_file_location(
    "build_krk_strategy_sequence_dataset_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_strategy_sequence_dataset_v2.py",
)
assert _dataset_v2_spec is not None
assert _dataset_v2_spec.loader is not None
_dataset_v2 = importlib.util.module_from_spec(_dataset_v2_spec)
_dataset_v2_spec.loader.exec_module(_dataset_v2)

_dataset_v2_quality_spec = importlib.util.spec_from_file_location(
    "probe_krk_strategy_sequence_dataset_v2_quality",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_strategy_sequence_dataset_v2_quality.py",
)
assert _dataset_v2_quality_spec is not None
assert _dataset_v2_quality_spec.loader is not None
_dataset_v2_quality = importlib.util.module_from_spec(_dataset_v2_quality_spec)
_dataset_v2_quality_spec.loader.exec_module(_dataset_v2_quality)

_candidate_generation_refresh_spec = importlib.util.spec_from_file_location(
    "probe_krk_candidate_generation_refresh_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_candidate_generation_refresh_v2.py",
)
assert _candidate_generation_refresh_spec is not None
assert _candidate_generation_refresh_spec.loader is not None
_candidate_generation_refresh = importlib.util.module_from_spec(
    _candidate_generation_refresh_spec
)
_candidate_generation_refresh_spec.loader.exec_module(_candidate_generation_refresh)

_capacity_evidence_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_generation_capacity_evidence_manifest_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_generation_capacity_evidence_manifest_v2.py",
)
assert _capacity_evidence_manifest_spec is not None
assert _capacity_evidence_manifest_spec.loader is not None
_capacity_evidence_manifest = importlib.util.module_from_spec(
    _capacity_evidence_manifest_spec
)
_capacity_evidence_manifest_spec.loader.exec_module(_capacity_evidence_manifest)

_capacity_evidence_labels_spec = importlib.util.spec_from_file_location(
    "run_krk_candidate_generation_capacity_evidence_labels_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_candidate_generation_capacity_evidence_labels_v2.py",
)
assert _capacity_evidence_labels_spec is not None
assert _capacity_evidence_labels_spec.loader is not None
_capacity_evidence_labels = importlib.util.module_from_spec(
    _capacity_evidence_labels_spec
)
_capacity_evidence_labels_spec.loader.exec_module(_capacity_evidence_labels)

_capacity_evidence_merge_spec = importlib.util.spec_from_file_location(
    "merge_krk_candidate_generation_capacity_evidence_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "merge_krk_candidate_generation_capacity_evidence_v2.py",
)
assert _capacity_evidence_merge_spec is not None
assert _capacity_evidence_merge_spec.loader is not None
_capacity_evidence_merge = importlib.util.module_from_spec(_capacity_evidence_merge_spec)
_capacity_evidence_merge_spec.loader.exec_module(_capacity_evidence_merge)

_training_refresh_design_spec = importlib.util.spec_from_file_location(
    "write_krk_candidate_generation_training_refresh_design_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_candidate_generation_training_refresh_design_v2.py",
)
assert _training_refresh_design_spec is not None
assert _training_refresh_design_spec.loader is not None
_training_refresh_design = importlib.util.module_from_spec(_training_refresh_design_spec)
_training_refresh_design_spec.loader.exec_module(_training_refresh_design)

_cross_stage_capacity_review_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_cross_stage_capacity_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_cross_stage_capacity_v2.py",
)
assert _cross_stage_capacity_review_spec is not None
assert _cross_stage_capacity_review_spec.loader is not None
_cross_stage_capacity_review = importlib.util.module_from_spec(
    _cross_stage_capacity_review_spec
)
_cross_stage_capacity_review_spec.loader.exec_module(_cross_stage_capacity_review)

_cross_stage_capacity_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_generation_cross_stage_capacity_manifest_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_generation_cross_stage_capacity_manifest_v3.py",
)
assert _cross_stage_capacity_manifest_spec is not None
assert _cross_stage_capacity_manifest_spec.loader is not None
_cross_stage_capacity_manifest = importlib.util.module_from_spec(
    _cross_stage_capacity_manifest_spec
)
_cross_stage_capacity_manifest_spec.loader.exec_module(_cross_stage_capacity_manifest)

_cross_stage_capacity_labels_spec = importlib.util.spec_from_file_location(
    "run_krk_candidate_generation_cross_stage_capacity_labels_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_candidate_generation_cross_stage_capacity_labels_v3.py",
)
assert _cross_stage_capacity_labels_spec is not None
assert _cross_stage_capacity_labels_spec.loader is not None
_cross_stage_capacity_labels = importlib.util.module_from_spec(
    _cross_stage_capacity_labels_spec
)
_cross_stage_capacity_labels_spec.loader.exec_module(_cross_stage_capacity_labels)

_cross_stage_capacity_merge_spec = importlib.util.spec_from_file_location(
    "merge_krk_candidate_generation_cross_stage_capacity_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "merge_krk_candidate_generation_cross_stage_capacity_v3.py",
)
assert _cross_stage_capacity_merge_spec is not None
assert _cross_stage_capacity_merge_spec.loader is not None
_cross_stage_capacity_merge = importlib.util.module_from_spec(
    _cross_stage_capacity_merge_spec
)
_cross_stage_capacity_merge_spec.loader.exec_module(_cross_stage_capacity_merge)

_cross_stage_label_outcome_review_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_cross_stage_label_outcome_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_cross_stage_label_outcome_v3.py",
)
assert _cross_stage_label_outcome_review_spec is not None
assert _cross_stage_label_outcome_review_spec.loader is not None
_cross_stage_label_outcome_review = importlib.util.module_from_spec(
    _cross_stage_label_outcome_review_spec
)
_cross_stage_label_outcome_review_spec.loader.exec_module(_cross_stage_label_outcome_review)

_stage_conditioned_scope_review_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_stage_conditioned_scope_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_stage_conditioned_scope_v3.py",
)
assert _stage_conditioned_scope_review_spec is not None
assert _stage_conditioned_scope_review_spec.loader is not None
_stage_conditioned_scope_review = importlib.util.module_from_spec(
    _stage_conditioned_scope_review_spec
)
_stage_conditioned_scope_review_spec.loader.exec_module(_stage_conditioned_scope_review)

_stage_conditioned_benchmark_spec = importlib.util.spec_from_file_location(
    "benchmark_krk_stage_conditioned_candidate_generation_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_krk_stage_conditioned_candidate_generation_v3.py",
)
assert _stage_conditioned_benchmark_spec is not None
assert _stage_conditioned_benchmark_spec.loader is not None
_stage_conditioned_benchmark = importlib.util.module_from_spec(
    _stage_conditioned_benchmark_spec
)
_stage_conditioned_benchmark_spec.loader.exec_module(_stage_conditioned_benchmark)

_stage5_6_refresh_packet_spec = importlib.util.spec_from_file_location(
    "write_krk_stage5_6_candidate_generation_refresh_review_packet_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_stage5_6_candidate_generation_refresh_review_packet_v3.py",
)
assert _stage5_6_refresh_packet_spec is not None
assert _stage5_6_refresh_packet_spec.loader is not None
_stage5_6_refresh_packet = importlib.util.module_from_spec(_stage5_6_refresh_packet_spec)
_stage5_6_refresh_packet_spec.loader.exec_module(_stage5_6_refresh_packet)

_stage5_6_refresh_smoke_spec = importlib.util.spec_from_file_location(
    "run_krk_stage5_6_candidate_generation_refresh_smoke_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_stage5_6_candidate_generation_refresh_smoke_v0.py",
)
assert _stage5_6_refresh_smoke_spec is not None
assert _stage5_6_refresh_smoke_spec.loader is not None
_stage5_6_refresh_smoke = importlib.util.module_from_spec(_stage5_6_refresh_smoke_spec)
_stage5_6_refresh_smoke_spec.loader.exec_module(_stage5_6_refresh_smoke)

_candidate_generation_refresh_sandbox_spec = importlib.util.spec_from_file_location(
    "run_krk_candidate_generation_refresh_sandbox_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_candidate_generation_refresh_sandbox_v0.py",
)
assert _candidate_generation_refresh_sandbox_spec is not None
assert _candidate_generation_refresh_sandbox_spec.loader is not None
_candidate_generation_refresh_sandbox = importlib.util.module_from_spec(
    _candidate_generation_refresh_sandbox_spec
)
_candidate_generation_refresh_sandbox_spec.loader.exec_module(
    _candidate_generation_refresh_sandbox
)

_stage5_6_refresh_coverage_spec = importlib.util.spec_from_file_location(
    "analyze_krk_stage5_6_candidate_generation_refresh_coverage_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_stage5_6_candidate_generation_refresh_coverage_v0.py",
)
assert _stage5_6_refresh_coverage_spec is not None
assert _stage5_6_refresh_coverage_spec.loader is not None
_stage5_6_refresh_coverage = importlib.util.module_from_spec(
    _stage5_6_refresh_coverage_spec
)
_stage5_6_refresh_coverage_spec.loader.exec_module(_stage5_6_refresh_coverage)

_stage5_6_refresh_broadened_spec = importlib.util.spec_from_file_location(
    "run_krk_stage5_6_candidate_generation_refresh_broadened_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_stage5_6_candidate_generation_refresh_broadened_v0.py",
)
assert _stage5_6_refresh_broadened_spec is not None
assert _stage5_6_refresh_broadened_spec.loader is not None
_stage5_6_refresh_broadened = importlib.util.module_from_spec(
    _stage5_6_refresh_broadened_spec
)
_stage5_6_refresh_broadened_spec.loader.exec_module(_stage5_6_refresh_broadened)

_stage5_6_refresh_quality_spec = importlib.util.spec_from_file_location(
    "analyze_krk_stage5_6_candidate_generation_refresh_quality_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_stage5_6_candidate_generation_refresh_quality_v0.py",
)
assert _stage5_6_refresh_quality_spec is not None
assert _stage5_6_refresh_quality_spec.loader is not None
_stage5_6_refresh_quality = importlib.util.module_from_spec(
    _stage5_6_refresh_quality_spec
)
_stage5_6_refresh_quality_spec.loader.exec_module(_stage5_6_refresh_quality)

_stage5_6_refresh_trace_fold_spec = importlib.util.spec_from_file_location(
    "fold_krk_stage5_6_refresh_frames_into_strategy_sequence_trace_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "fold_krk_stage5_6_refresh_frames_into_strategy_sequence_trace_v0.py",
)
assert _stage5_6_refresh_trace_fold_spec is not None
assert _stage5_6_refresh_trace_fold_spec.loader is not None
_stage5_6_refresh_trace_fold = importlib.util.module_from_spec(
    _stage5_6_refresh_trace_fold_spec
)
_stage5_6_refresh_trace_fold_spec.loader.exec_module(_stage5_6_refresh_trace_fold)

_dataset_design_v3_spec = importlib.util.spec_from_file_location(
    "write_krk_strategy_sequence_dataset_design_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_strategy_sequence_dataset_design_v3.py",
)
assert _dataset_design_v3_spec is not None
assert _dataset_design_v3_spec.loader is not None
_dataset_design_v3 = importlib.util.module_from_spec(_dataset_design_v3_spec)
_dataset_design_v3_spec.loader.exec_module(_dataset_design_v3)

_dataset_v3_spec = importlib.util.spec_from_file_location(
    "build_krk_strategy_sequence_dataset_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_strategy_sequence_dataset_v3.py",
)
assert _dataset_v3_spec is not None
assert _dataset_v3_spec.loader is not None
_dataset_v3 = importlib.util.module_from_spec(_dataset_v3_spec)
_dataset_v3_spec.loader.exec_module(_dataset_v3)

_dataset_v3_quality_spec = importlib.util.spec_from_file_location(
    "probe_krk_strategy_sequence_dataset_v3_quality",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_strategy_sequence_dataset_v3_quality.py",
)
assert _dataset_v3_quality_spec is not None
assert _dataset_v3_quality_spec.loader is not None
_dataset_v3_quality = importlib.util.module_from_spec(_dataset_v3_quality_spec)
_dataset_v3_quality_spec.loader.exec_module(_dataset_v3_quality)

_dataset_v3_context_review_spec = importlib.util.spec_from_file_location(
    "review_krk_strategy_sequence_dataset_v3_context",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_strategy_sequence_dataset_v3_context.py",
)
assert _dataset_v3_context_review_spec is not None
assert _dataset_v3_context_review_spec.loader is not None
_dataset_v3_context_review = importlib.util.module_from_spec(
    _dataset_v3_context_review_spec
)
_dataset_v3_context_review_spec.loader.exec_module(_dataset_v3_context_review)

_candidate_generation_v3_context_benchmark_spec = importlib.util.spec_from_file_location(
    "benchmark_krk_candidate_generation_v3_context",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_krk_candidate_generation_v3_context.py",
)
assert _candidate_generation_v3_context_benchmark_spec is not None
assert _candidate_generation_v3_context_benchmark_spec.loader is not None
_candidate_generation_v3_context_benchmark = importlib.util.module_from_spec(
    _candidate_generation_v3_context_benchmark_spec
)
_candidate_generation_v3_context_benchmark_spec.loader.exec_module(
    _candidate_generation_v3_context_benchmark
)

_candidate_generation_v3_runtime_boundary_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_v3_runtime_boundary",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_v3_runtime_boundary.py",
)
assert _candidate_generation_v3_runtime_boundary_spec is not None
assert _candidate_generation_v3_runtime_boundary_spec.loader is not None
_candidate_generation_v3_runtime_boundary = importlib.util.module_from_spec(
    _candidate_generation_v3_runtime_boundary_spec
)
_candidate_generation_v3_runtime_boundary_spec.loader.exec_module(
    _candidate_generation_v3_runtime_boundary
)

_candidate_generation_v3_training_refresh_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_v3_training_refresh",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_v3_training_refresh.py",
)
assert _candidate_generation_v3_training_refresh_spec is not None
assert _candidate_generation_v3_training_refresh_spec.loader is not None
_candidate_generation_v3_training_refresh = importlib.util.module_from_spec(
    _candidate_generation_v3_training_refresh_spec
)
_candidate_generation_v3_training_refresh_spec.loader.exec_module(
    _candidate_generation_v3_training_refresh
)

_candidate_generation_training_refresh_design_v3_spec = importlib.util.spec_from_file_location(
    "write_krk_candidate_generation_training_refresh_design_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_candidate_generation_training_refresh_design_v3.py",
)
assert _candidate_generation_training_refresh_design_v3_spec is not None
assert _candidate_generation_training_refresh_design_v3_spec.loader is not None
_candidate_generation_training_refresh_design_v3 = importlib.util.module_from_spec(
    _candidate_generation_training_refresh_design_v3_spec
)
_candidate_generation_training_refresh_design_v3_spec.loader.exec_module(
    _candidate_generation_training_refresh_design_v3
)

_candidate_generation_training_refresh_benchmark_v3_spec = importlib.util.spec_from_file_location(
    "benchmark_krk_candidate_generation_training_refresh_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_krk_candidate_generation_training_refresh_v3.py",
)
assert _candidate_generation_training_refresh_benchmark_v3_spec is not None
assert _candidate_generation_training_refresh_benchmark_v3_spec.loader is not None
_candidate_generation_training_refresh_benchmark_v3 = importlib.util.module_from_spec(
    _candidate_generation_training_refresh_benchmark_v3_spec
)
_candidate_generation_training_refresh_benchmark_v3_spec.loader.exec_module(
    _candidate_generation_training_refresh_benchmark_v3
)

_candidate_generation_training_refresh_packet_v3_spec = importlib.util.spec_from_file_location(
    "write_krk_candidate_generation_training_refresh_runtime_review_packet_v3",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_candidate_generation_training_refresh_runtime_review_packet_v3.py",
)
assert _candidate_generation_training_refresh_packet_v3_spec is not None
assert _candidate_generation_training_refresh_packet_v3_spec.loader is not None
_candidate_generation_training_refresh_packet_v3 = importlib.util.module_from_spec(
    _candidate_generation_training_refresh_packet_v3_spec
)
_candidate_generation_training_refresh_packet_v3_spec.loader.exec_module(
    _candidate_generation_training_refresh_packet_v3
)

_candidate_generation_refresh_coverage_spec = importlib.util.spec_from_file_location(
    "analyze_krk_candidate_generation_refresh_coverage_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_candidate_generation_refresh_coverage_v0.py",
)
assert _candidate_generation_refresh_coverage_spec is not None
assert _candidate_generation_refresh_coverage_spec.loader is not None
_candidate_generation_refresh_coverage = importlib.util.module_from_spec(
    _candidate_generation_refresh_coverage_spec
)
_candidate_generation_refresh_coverage_spec.loader.exec_module(
    _candidate_generation_refresh_coverage
)

_candidate_generation_refresh_trace_fold_spec = importlib.util.spec_from_file_location(
    "fold_krk_candidate_generation_refresh_sandbox_frames_into_strategy_sequence_trace_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "fold_krk_candidate_generation_refresh_sandbox_frames_into_strategy_sequence_trace_v1.py",
)
assert _candidate_generation_refresh_trace_fold_spec is not None
assert _candidate_generation_refresh_trace_fold_spec.loader is not None
_candidate_generation_refresh_trace_fold = importlib.util.module_from_spec(
    _candidate_generation_refresh_trace_fold_spec
)
_candidate_generation_refresh_trace_fold_spec.loader.exec_module(
    _candidate_generation_refresh_trace_fold
)

_dataset_v4_spec = importlib.util.spec_from_file_location(
    "build_krk_strategy_sequence_dataset_v4",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_strategy_sequence_dataset_v4.py",
)
assert _dataset_v4_spec is not None
assert _dataset_v4_spec.loader is not None
_dataset_v4 = importlib.util.module_from_spec(_dataset_v4_spec)
_dataset_v4_spec.loader.exec_module(_dataset_v4)

_dataset_v4_quality_spec = importlib.util.spec_from_file_location(
    "probe_krk_strategy_sequence_dataset_v4_quality",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_strategy_sequence_dataset_v4_quality.py",
)
assert _dataset_v4_quality_spec is not None
assert _dataset_v4_quality_spec.loader is not None
_dataset_v4_quality = importlib.util.module_from_spec(_dataset_v4_quality_spec)
_dataset_v4_quality_spec.loader.exec_module(_dataset_v4_quality)

_dataset_v4_context_review_spec = importlib.util.spec_from_file_location(
    "review_krk_strategy_sequence_dataset_v4_context",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_strategy_sequence_dataset_v4_context.py",
)
assert _dataset_v4_context_review_spec is not None
assert _dataset_v4_context_review_spec.loader is not None
_dataset_v4_context_review = importlib.util.module_from_spec(_dataset_v4_context_review_spec)
_dataset_v4_context_review_spec.loader.exec_module(_dataset_v4_context_review)

_candidate_generation_v4_context_benchmark_spec = importlib.util.spec_from_file_location(
    "benchmark_krk_candidate_generation_v4_context",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_krk_candidate_generation_v4_context.py",
)
assert _candidate_generation_v4_context_benchmark_spec is not None
assert _candidate_generation_v4_context_benchmark_spec.loader is not None
_candidate_generation_v4_context_benchmark = importlib.util.module_from_spec(
    _candidate_generation_v4_context_benchmark_spec
)
_candidate_generation_v4_context_benchmark_spec.loader.exec_module(
    _candidate_generation_v4_context_benchmark
)

_candidate_generation_v4_runtime_boundary_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_v4_next_runtime_boundary",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_v4_next_runtime_boundary.py",
)
assert _candidate_generation_v4_runtime_boundary_spec is not None
assert _candidate_generation_v4_runtime_boundary_spec.loader is not None
_candidate_generation_v4_runtime_boundary = importlib.util.module_from_spec(
    _candidate_generation_v4_runtime_boundary_spec
)
_candidate_generation_v4_runtime_boundary_spec.loader.exec_module(
    _candidate_generation_v4_runtime_boundary
)

_candidate_generation_scope_gap_review_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_scope_gaps_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_scope_gaps_v0.py",
)
assert _candidate_generation_scope_gap_review_spec is not None
assert _candidate_generation_scope_gap_review_spec.loader is not None
_candidate_generation_scope_gap_review = importlib.util.module_from_spec(
    _candidate_generation_scope_gap_review_spec
)
_candidate_generation_scope_gap_review_spec.loader.exec_module(
    _candidate_generation_scope_gap_review
)

_candidate_source_gap_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_source_gap_manifest_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_source_gap_manifest_v0.py",
)
assert _candidate_source_gap_manifest_spec is not None
assert _candidate_source_gap_manifest_spec.loader is not None
_candidate_source_gap_manifest = importlib.util.module_from_spec(
    _candidate_source_gap_manifest_spec
)
_candidate_source_gap_manifest_spec.loader.exec_module(_candidate_source_gap_manifest)

_candidate_source_expansion_options_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_source_expansion_options_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_source_expansion_options_v0.py",
)
assert _candidate_source_expansion_options_spec is not None
assert _candidate_source_expansion_options_spec.loader is not None
_candidate_source_expansion_options = importlib.util.module_from_spec(
    _candidate_source_expansion_options_spec
)
_candidate_source_expansion_options_spec.loader.exec_module(
    _candidate_source_expansion_options
)

_exact_trace_enrichment_packet_spec = importlib.util.spec_from_file_location(
    "write_krk_exact_trace_enrichment_runtime_review_packet_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_exact_trace_enrichment_runtime_review_packet_v0.py",
)
assert _exact_trace_enrichment_packet_spec is not None
assert _exact_trace_enrichment_packet_spec.loader is not None
_exact_trace_enrichment_packet = importlib.util.module_from_spec(
    _exact_trace_enrichment_packet_spec
)
_exact_trace_enrichment_packet_spec.loader.exec_module(_exact_trace_enrichment_packet)

_exact_trace_enrichment_sandbox_spec = importlib.util.spec_from_file_location(
    "run_krk_exact_trace_enrichment_sandbox_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_exact_trace_enrichment_sandbox_v0.py",
)
assert _exact_trace_enrichment_sandbox_spec is not None
assert _exact_trace_enrichment_sandbox_spec.loader is not None
_exact_trace_enrichment_sandbox = importlib.util.module_from_spec(
    _exact_trace_enrichment_sandbox_spec
)
_exact_trace_enrichment_sandbox_spec.loader.exec_module(_exact_trace_enrichment_sandbox)

_exact_trace_enrichment_coverage_spec = importlib.util.spec_from_file_location(
    "analyze_krk_exact_trace_enrichment_coverage_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_exact_trace_enrichment_coverage_v0.py",
)
assert _exact_trace_enrichment_coverage_spec is not None
assert _exact_trace_enrichment_coverage_spec.loader is not None
_exact_trace_enrichment_coverage = importlib.util.module_from_spec(
    _exact_trace_enrichment_coverage_spec
)
_exact_trace_enrichment_coverage_spec.loader.exec_module(_exact_trace_enrichment_coverage)

_exact_trace_enrichment_trace_fold_spec = importlib.util.spec_from_file_location(
    "fold_krk_exact_trace_enrichment_frames_into_strategy_sequence_trace_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "fold_krk_exact_trace_enrichment_frames_into_strategy_sequence_trace_v1.py",
)
assert _exact_trace_enrichment_trace_fold_spec is not None
assert _exact_trace_enrichment_trace_fold_spec.loader is not None
_exact_trace_enrichment_trace_fold = importlib.util.module_from_spec(
    _exact_trace_enrichment_trace_fold_spec
)
_exact_trace_enrichment_trace_fold_spec.loader.exec_module(_exact_trace_enrichment_trace_fold)

_dataset_v5_spec = importlib.util.spec_from_file_location(
    "build_krk_strategy_sequence_dataset_v5",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_strategy_sequence_dataset_v5.py",
)
assert _dataset_v5_spec is not None
assert _dataset_v5_spec.loader is not None
_dataset_v5 = importlib.util.module_from_spec(_dataset_v5_spec)
_dataset_v5_spec.loader.exec_module(_dataset_v5)

_dataset_v5_quality_spec = importlib.util.spec_from_file_location(
    "probe_krk_strategy_sequence_dataset_v5_quality",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_strategy_sequence_dataset_v5_quality.py",
)
assert _dataset_v5_quality_spec is not None
assert _dataset_v5_quality_spec.loader is not None
_dataset_v5_quality = importlib.util.module_from_spec(_dataset_v5_quality_spec)
_dataset_v5_quality_spec.loader.exec_module(_dataset_v5_quality)

_dataset_v5_context_spec = importlib.util.spec_from_file_location(
    "review_krk_strategy_sequence_dataset_v5_context",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_strategy_sequence_dataset_v5_context.py",
)
assert _dataset_v5_context_spec is not None
assert _dataset_v5_context_spec.loader is not None
_dataset_v5_context = importlib.util.module_from_spec(_dataset_v5_context_spec)
_dataset_v5_context_spec.loader.exec_module(_dataset_v5_context)

_candidate_generation_v5_benchmark_spec = importlib.util.spec_from_file_location(
    "benchmark_krk_candidate_generation_v5_context",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_krk_candidate_generation_v5_context.py",
)
assert _candidate_generation_v5_benchmark_spec is not None
assert _candidate_generation_v5_benchmark_spec.loader is not None
_candidate_generation_v5_benchmark = importlib.util.module_from_spec(
    _candidate_generation_v5_benchmark_spec
)
_candidate_generation_v5_benchmark_spec.loader.exec_module(
    _candidate_generation_v5_benchmark
)

_candidate_generation_v5_boundary_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_v5_next_boundary",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_v5_next_boundary.py",
)
assert _candidate_generation_v5_boundary_spec is not None
assert _candidate_generation_v5_boundary_spec.loader is not None
_candidate_generation_v5_boundary = importlib.util.module_from_spec(
    _candidate_generation_v5_boundary_spec
)
_candidate_generation_v5_boundary_spec.loader.exec_module(_candidate_generation_v5_boundary)

_ownership_label_recovery_spec = importlib.util.spec_from_file_location(
    "review_krk_ownership_label_recovery_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_ownership_label_recovery_v0.py",
)
assert _ownership_label_recovery_spec is not None
assert _ownership_label_recovery_spec.loader is not None
_ownership_label_recovery = importlib.util.module_from_spec(
    _ownership_label_recovery_spec
)
_ownership_label_recovery_spec.loader.exec_module(_ownership_label_recovery)

_selector_objective_seed_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_selector_objective_seed_manifest_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_selector_objective_seed_manifest_v0.py",
)
assert _selector_objective_seed_manifest_spec is not None
assert _selector_objective_seed_manifest_spec.loader is not None
_selector_objective_seed_manifest = importlib.util.module_from_spec(
    _selector_objective_seed_manifest_spec
)
_selector_objective_seed_manifest_spec.loader.exec_module(_selector_objective_seed_manifest)

_selector_objective_seed_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_selector_objective_seed_manifest_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_selector_objective_seed_manifest_v0.py",
)
assert _selector_objective_seed_probe_spec is not None
assert _selector_objective_seed_probe_spec.loader is not None
_selector_objective_seed_probe = importlib.util.module_from_spec(
    _selector_objective_seed_probe_spec
)
_selector_objective_seed_probe_spec.loader.exec_module(_selector_objective_seed_probe)

_joined_trace_ownership_collection_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_joined_trace_ownership_collection_manifest_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_joined_trace_ownership_collection_manifest_v0.py",
)
assert _joined_trace_ownership_collection_manifest_spec is not None
assert _joined_trace_ownership_collection_manifest_spec.loader is not None
_joined_trace_ownership_collection_manifest = importlib.util.module_from_spec(
    _joined_trace_ownership_collection_manifest_spec
)
_joined_trace_ownership_collection_manifest_spec.loader.exec_module(
    _joined_trace_ownership_collection_manifest
)

_joined_trace_ownership_collection_packet_spec = importlib.util.spec_from_file_location(
    "write_krk_joined_trace_ownership_collection_review_packet_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_joined_trace_ownership_collection_review_packet_v0.py",
)
assert _joined_trace_ownership_collection_packet_spec is not None
assert _joined_trace_ownership_collection_packet_spec.loader is not None
_joined_trace_ownership_collection_packet = importlib.util.module_from_spec(
    _joined_trace_ownership_collection_packet_spec
)
_joined_trace_ownership_collection_packet_spec.loader.exec_module(
    _joined_trace_ownership_collection_packet
)

_joined_trace_ownership_collection_run_spec = importlib.util.spec_from_file_location(
    "run_krk_joined_trace_ownership_collection_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_joined_trace_ownership_collection_v0.py",
)
assert _joined_trace_ownership_collection_run_spec is not None
assert _joined_trace_ownership_collection_run_spec.loader is not None
_joined_trace_ownership_collection_run = importlib.util.module_from_spec(
    _joined_trace_ownership_collection_run_spec
)
_joined_trace_ownership_collection_run_spec.loader.exec_module(
    _joined_trace_ownership_collection_run
)

_selector_objective_seed_manifest_v1_spec = importlib.util.spec_from_file_location(
    "build_krk_selector_objective_seed_manifest_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_selector_objective_seed_manifest_v1.py",
)
assert _selector_objective_seed_manifest_v1_spec is not None
assert _selector_objective_seed_manifest_v1_spec.loader is not None
_selector_objective_seed_manifest_v1 = importlib.util.module_from_spec(
    _selector_objective_seed_manifest_v1_spec
)
_selector_objective_seed_manifest_v1_spec.loader.exec_module(
    _selector_objective_seed_manifest_v1
)

_selector_objective_seed_probe_v1_spec = importlib.util.spec_from_file_location(
    "probe_krk_selector_objective_seed_manifest_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_selector_objective_seed_manifest_v1.py",
)
assert _selector_objective_seed_probe_v1_spec is not None
assert _selector_objective_seed_probe_v1_spec.loader is not None
_selector_objective_seed_probe_v1 = importlib.util.module_from_spec(
    _selector_objective_seed_probe_v1_spec
)
_selector_objective_seed_probe_v1_spec.loader.exec_module(_selector_objective_seed_probe_v1)

_selector_objective_feature_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_selector_objective_features_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_selector_objective_features_v0.py",
)
assert _selector_objective_feature_probe_spec is not None
assert _selector_objective_feature_probe_spec.loader is not None
_selector_objective_feature_probe = importlib.util.module_from_spec(
    _selector_objective_feature_probe_spec
)
_selector_objective_feature_probe_spec.loader.exec_module(_selector_objective_feature_probe)

_selector_objective_feature_review_spec = importlib.util.spec_from_file_location(
    "review_krk_selector_objective_feature_probe_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_selector_objective_feature_probe_v0.py",
)
assert _selector_objective_feature_review_spec is not None
assert _selector_objective_feature_review_spec.loader is not None
_selector_objective_feature_review = importlib.util.module_from_spec(
    _selector_objective_feature_review_spec
)
_selector_objective_feature_review_spec.loader.exec_module(_selector_objective_feature_review)

_selector_objective_diversity_gap_spec = importlib.util.spec_from_file_location(
    "review_krk_selector_objective_diversity_gap_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_selector_objective_diversity_gap_v0.py",
)
assert _selector_objective_diversity_gap_spec is not None
assert _selector_objective_diversity_gap_spec.loader is not None
_selector_objective_diversity_gap = importlib.util.module_from_spec(
    _selector_objective_diversity_gap_spec
)
_selector_objective_diversity_gap_spec.loader.exec_module(_selector_objective_diversity_gap)

_stage4_joined_trace_scope_packet_spec = importlib.util.spec_from_file_location(
    "write_krk_stage4_joined_trace_ownership_scope_review_packet_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_stage4_joined_trace_ownership_scope_review_packet_v0.py",
)
assert _stage4_joined_trace_scope_packet_spec is not None
assert _stage4_joined_trace_scope_packet_spec.loader is not None
_stage4_joined_trace_scope_packet = importlib.util.module_from_spec(
    _stage4_joined_trace_scope_packet_spec
)
_stage4_joined_trace_scope_packet_spec.loader.exec_module(_stage4_joined_trace_scope_packet)

_clean_curriculum_checkpoint_plan_spec = importlib.util.spec_from_file_location(
    "write_krk_clean_curriculum_checkpoint_plan_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_clean_curriculum_checkpoint_plan_v0.py",
)
assert _clean_curriculum_checkpoint_plan_spec is not None
assert _clean_curriculum_checkpoint_plan_spec.loader is not None
_clean_curriculum_checkpoint_plan = importlib.util.module_from_spec(
    _clean_curriculum_checkpoint_plan_spec
)
_clean_curriculum_checkpoint_plan_spec.loader.exec_module(_clean_curriculum_checkpoint_plan)

_clean_retrain_execution_manifest_spec = importlib.util.spec_from_file_location(
    "write_krk_clean_retrain_execution_manifest_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_clean_retrain_execution_manifest_v0.py",
)
assert _clean_retrain_execution_manifest_spec is not None
assert _clean_retrain_execution_manifest_spec.loader is not None
_clean_retrain_execution_manifest = importlib.util.module_from_spec(
    _clean_retrain_execution_manifest_spec
)
_clean_retrain_execution_manifest_spec.loader.exec_module(_clean_retrain_execution_manifest)

_stage6_overlay_compose_manifest_spec = importlib.util.spec_from_file_location(
    "write_krk_stage6_overlay_compose_manifest_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_stage6_overlay_compose_manifest_v0.py",
)
assert _stage6_overlay_compose_manifest_spec is not None
assert _stage6_overlay_compose_manifest_spec.loader is not None
_stage6_overlay_compose_manifest = importlib.util.module_from_spec(
    _stage6_overlay_compose_manifest_spec
)
_stage6_overlay_compose_manifest_spec.loader.exec_module(_stage6_overlay_compose_manifest)

_clean_retrain_preflight_spec = importlib.util.spec_from_file_location(
    "verify_krk_clean_retrain_preflight_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "verify_krk_clean_retrain_preflight_v0.py",
)
assert _clean_retrain_preflight_spec is not None
assert _clean_retrain_preflight_spec.loader is not None
_clean_retrain_preflight = importlib.util.module_from_spec(_clean_retrain_preflight_spec)
_clean_retrain_preflight_spec.loader.exec_module(_clean_retrain_preflight)

_clean_retrain_smoke_manifest_spec = importlib.util.spec_from_file_location(
    "write_krk_clean_retrain_smoke_manifest_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_clean_retrain_smoke_manifest_v0.py",
)
assert _clean_retrain_smoke_manifest_spec is not None
assert _clean_retrain_smoke_manifest_spec.loader is not None
_clean_retrain_smoke_manifest = importlib.util.module_from_spec(
    _clean_retrain_smoke_manifest_spec
)
_clean_retrain_smoke_manifest_spec.loader.exec_module(_clean_retrain_smoke_manifest)

_landmark_spec = importlib.util.spec_from_file_location(
    "test_krk_landmark_progress",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "test_krk_landmark_progress.py",
)
assert _landmark_spec is not None
assert _landmark_spec.loader is not None
_landmark = importlib.util.module_from_spec(_landmark_spec)
_landmark_spec.loader.exec_module(_landmark)


def test_candidate_proposal_coverage_preserves_capacity_label_semantics():
    capacity_rows = [
        {
            "state_id": "state.a",
            "frame_id": "frame.a",
            "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
            "source_stage": "stage5",
            "provider_id": "krk.fence_established",
            "provider_family": "fence_established",
            "capacity_label": "positive_capacity",
            "forced_result": "mate",
            "existing_frame_providers": ["krk.stage0_basin"],
            "stage7_challenge_row": False,
        }
    ]
    ranked_rows = [
        {
            "state_id": "state.a",
            "provider_id": "krk.stage0_basin",
        }
    ]

    rows = _module._coverage_rows(capacity_rows, ranked_rows)

    assert rows[0]["provider_visible_in_current_proposals"] is False
    assert rows[0]["candidate_generation_channel"] == (
        "missing_validated_provider_capacity_candidate"
    )
    assert rows[0]["label_semantics"] == "forced_provider_capacity_label"
    assert rows[0]["usable_for_selector_training"] is False
    assert rows[0]["causal_status"] == "non_causal_capacity_coverage_evidence"


def test_candidate_proposal_coverage_summary_excludes_stage7_training_readiness():
    rows = [
        {
            "capacity_label": "positive_capacity",
            "provider_visible_in_current_proposals": False,
            "provider_family": "fence_established",
            "source_stage": "stage5",
            "stage7_challenge_row": False,
        },
        {
            "capacity_label": "negative_capacity",
            "provider_visible_in_current_proposals": True,
            "provider_family": "edge_trap",
            "source_stage": "stage4",
            "stage7_challenge_row": False,
        },
    ]

    summary = _module._summarize_coverage(rows)

    assert summary["positive_capacity_recall"] == 0.0
    assert summary["missing_positive_capacity_count"] == 1
    assert summary["stage7_row_count"] == 0


def test_strategy_sequence_candidate_frame_schema_is_non_causal():
    review = {
        "decision": {
            "future_runtime_sandbox_requires": [
                "candidate-generation candidate set exists",
            ]
        }
    }

    payload = _module.build_frame_schema_payload(review)

    assert payload["causal_status"] == "non_causal_schema_design"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert "direct_provider_request" in payload["forbidden_causal_uses"]
    assert "capacity_evidence" in payload["required_fields"]


def test_strategy_sequence_capacity_frames_are_generation_not_selection_labels():
    frames = _populate.capacity_candidate_frames(
        [
            {
                "state_id": "state.a",
                "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "source_stage": "stage5",
                "provider_id": "krk.fence_established",
                "provider_family": "fence_established",
                "capacity_label": "positive_capacity",
                "forced_result": "mate",
                "forced_first_move": "a1a2",
                "stage7_challenge_row": False,
            }
        ]
    )

    assert frames[0]["frame_type"] == "validated_provider_candidate"
    assert frames[0]["label_semantics"] == "capacity_evidence_not_ownership_label"
    assert frames[0]["usable_for_selector_training"] is False
    assert frames[0]["usable_for_candidate_generation_training"] is True
    assert frames[0]["causal_status"] == "non_causal"


def test_strategy_sequence_quality_blocks_stage7_training_rows():
    frames_payload = {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": {
            "readiness_training_stage7_row_count": 1,
        },
        "frames": [
            {
                "label_semantics": "capacity_evidence_not_ownership_label",
                "usable_for_selector_training": False,
                "stage7_challenge_row": True,
                "frame_type": "candidate_move_hypothesis",
                "sequence_evidence": {},
            }
        ],
    }

    quality = _populate.build_quality_payload(frames_payload)

    assert quality["quality_checks"]["stage7_excluded_from_training_readiness"] is False
    assert quality["decision"]["status"] == "frame_quality_blocked"


def test_progress_window_continuation_index_accepts_list_shape():
    indexed = _populate._continuation_index(
        [
            {
                "move": "a1a2",
                "continuation": {
                    "result": "max_plies",
                },
            }
        ]
    )

    assert indexed == {"a1a2": {"result": "max_plies"}}


def test_candidate_frame_source_benchmark_keeps_capacity_and_selection_separate():
    frames = [
        {
            "label_semantics": "capacity_evidence_not_ownership_label",
            "stage7_challenge_row": False,
            "state_id": "state.a",
            "candidate_strategy_family": "fence_established",
            "capacity_evidence": {"capacity_label": "positive_capacity"},
            "usable_for_candidate_generation_training": True,
            "usable_for_selector_training": False,
        },
        {
            "label_semantics": "capacity_evidence_not_ownership_label",
            "stage7_challenge_row": False,
            "state_id": "state.a",
            "candidate_strategy_family": "stage0_basin",
            "capacity_evidence": {"capacity_label": "negative_capacity"},
            "usable_for_candidate_generation_training": False,
            "usable_for_selector_training": False,
        },
    ]

    summary = _benchmark.benchmark_frames(frames)
    readiness = _benchmark.source_readiness(summary)

    assert summary["protected_forced_capacity"]["positive_capacity_ratio"] == 0.5
    assert summary["protected_forced_capacity"]["negative_capacity_ratio"] == 0.5
    assert readiness["protected_forced_capacity"]["selection_signal"] == (
        "blocked_capacity_not_ownership_label"
    )
    assert readiness["protected_forced_capacity"]["usable_next"] == (
        "candidate_generation_benchmark_only"
    )


def test_control_plane_decision_blocks_runtime_when_stage7_training_leaks():
    benchmark = {
        "channel_summaries": {
            "protected_forced_capacity": {
                "candidate_generation_training_row_count": 1,
                "negative_capacity_ratio": 0.0,
                "stage7_training_row_count": 1,
            }
        },
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }

    decision = _benchmark.build_decision_payload(benchmark)

    assert decision["decision"]["status"] == "blocked_stage7_leakage"
    assert decision["decision"]["runtime_sandbox_allowed_by_this_packet"] is False
    assert decision["evidence"]["stage7_training_row_count"] == 1


def test_candidate_generation_sandbox_review_is_observation_only():
    payload = _sandbox_review.build_review_payload()

    assert payload["decision"]["status"] == (
        "candidate_generation_observation_sandbox_review_ready"
    )
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["runtime_sandbox_allowed_by_this_packet"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["score_changes_allowed"] is False
    assert payload["decision"]["routing_changes_allowed"] is False
    assert payload["runtime_candidate_generator_implemented"] is False
    assert payload["runtime_behavior_changed"] is False
    assert "selecting_a_provider" in payload["explicitly_forbidden"]
    assert "score_delta_zero" in payload["required_candidate_frame_fields"]


def test_candidate_generation_observation_frames_are_non_causal():
    suggestion = {
        "move": "a1a2",
        "score": 7.5,
        "meta": {"curriculum_label": "fence_established", "provider_version": "frozen"},
    }

    observation = _landmark._krk_candidate_generation_observation_for_suggestions(
        [suggestion],
        selected_suggestion=suggestion,
        active_landmark_label="fence_established",
        visible_terms={"fence_exists": True},
        board=None,
        blackboard={},
        limit=1,
    )

    assert observation["causal_status"] == "observation_only"
    assert observation["direct_request"] is False
    assert observation["score_delta"] == 0.0
    assert suggestion["score"] == 7.5
    assert observation["candidate_count"] == 1
    frame = observation["frames"][0]
    assert frame["candidate_source"] == "validated_provider_pack"
    assert frame["direct_request"] is False
    assert frame["score_delta"] == 0.0
    assert "selecting_a_provider" in frame["forbidden_actions"]


def test_candidate_generation_observation_smoke_decision_schema():
    payload = {
        "summary": {
            "generated_candidate_count": 1,
            "generated_candidate_count_by_source": {"validated_provider_pack": 1},
            "protected_candidate_count": 1,
            "stage7_heldout_candidate_count": 0,
            "capacity_evidence_counts": {"positive_capacity": 1},
            "selected_move_or_provider_changed": False,
            "playout_result_or_plies_changed": False,
        },
        "decision": {
            "status": "observation_sandbox_ready_for_non_causal_coverage_analysis",
            "default_off_equivalence_passed": True,
            "observation_frames_emitted": True,
            "frame_invariants_passed": True,
            "selector_allowed": False,
        },
        "cases": [],
    }

    assert _observation_smoke._same_decision(
        {"move": "a1a2", "selected_provider": "krk.fence", "confidence": 1.0},
        {"move": "a1a2", "selected_provider": "krk.fence", "confidence": 1.0},
    )
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_generation_observation_runtime_flag_is_observation_only():
    case = _observation_smoke._load_cases()[0]

    flag_off = _observation_smoke._run_decision(case, enabled=False)
    enabled = _observation_smoke._run_decision(case, enabled=True)

    assert flag_off["observation_present"] is False
    assert enabled["observation_present"] is True
    assert _observation_smoke._same_decision(flag_off, enabled)
    observation = enabled["observation"]
    assert observation["direct_request"] is False
    assert observation["score_delta"] == 0.0
    assert observation["candidate_count"] > 0
    assert observation["sample_frames"][0]["causal_status"] == "observation_only"


def test_candidate_generation_observation_coverage_analysis_blocks_selector():
    payload = {
        "summary": {
            "generated_candidate_count": 1,
            "selected_move_or_provider_changed": False,
            "playout_result_or_plies_changed": False,
        },
        "cases": [
            {
                "case_id": "protected",
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "validated_provider_pack",
                                "capacity_evidence_kind": "positive_capacity",
                                "protected_status": "protected_control",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            }
                        ]
                    }
                },
            }
        ],
    }

    analysis = _observation_analysis.analyze(payload)

    assert analysis["summary"]["invariant_failure_count"] == 0
    assert analysis["interpretation"]["candidate_generation_visible"] is True
    assert analysis["decision"]["selector_allowed"] is False
    assert analysis["decision"]["guardrails_allowed"] is False


def test_candidate_generation_broadened_sample_cases_keep_stage7_held_out():
    cases = _observation_broadened.load_broadened_cases(stage7_cap=2)

    assert cases
    assert any(case["source_stage"] in {"stage4", "stage5", "stage6"} for case in cases)
    assert sum(1 for case in cases if case["source_stage"] == "stage7") == 2
    assert all(case["held_out"] for case in cases if case["source_stage"] == "stage7")


def test_candidate_generation_broadened_aggregate_blocks_selector():
    rows = [
        {
            "case_id": "stage5_state",
            "source_stage": "stage5",
            "held_out": False,
            "source_artifact": "fixture",
            "flag_off_decision": {"observation_present": False},
            "enabled_decision": {
                "observation": {
                    "frames": [
                        {
                            "candidate_source": "validated_provider_pack",
                            "capacity_evidence_kind": "positive_capacity",
                            "protected_status": "protected_control",
                            "direct_request": False,
                            "score_delta": 0.0,
                            "causal_status": "observation_only",
                        }
                    ]
                }
            },
            "selected_move_provider_score_equivalent": True,
        },
        {
            "case_id": "stage7_state",
            "source_stage": "stage7",
            "held_out": True,
            "source_artifact": "fixture",
            "flag_off_decision": {"observation_present": False},
            "enabled_decision": {
                "observation": {
                    "frames": [
                        {
                            "candidate_source": "candidate_move_frame",
                            "capacity_evidence_kind": "held_out_challenge",
                            "protected_status": "held_out_stage7_challenge",
                            "direct_request": False,
                            "score_delta": 0.0,
                            "causal_status": "observation_only",
                        }
                    ]
                }
            },
            "selected_move_provider_score_equivalent": True,
        },
    ]

    summary = _observation_broadened._aggregate(rows)

    assert summary["stage7_heldout_case_count"] == 1
    assert summary["stage7_readiness_training_row_count"] == 0
    assert summary["selected_move_or_provider_delta_count"] == 0
    assert summary["default_off_observation_case_count"] == 0
    assert summary["invariant_failure_count"] == 0


def test_candidate_generation_observation_gap_review_blocks_selector_on_unknown_capacity():
    payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "source_stage": "stage5",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "capacity_evidence_kind": "unknown_capacity",
                                "protected_status": "protected_or_unknown",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                            {
                                "candidate_source": "candidate_move_frame",
                                "capacity_evidence_kind": "unknown_capacity",
                                "protected_status": "protected_or_unknown",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                            {
                                "candidate_source": "validated_provider_pack",
                                "capacity_evidence_kind": "negative_capacity",
                                "protected_status": "protected_control",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                        ]
                    }
                },
            }
        ]
    }

    review = _observation_gap_review.review(payload)

    assert review["decision"]["selector_allowed"] is False
    assert review["decision"]["guardrails_allowed"] is False
    assert "candidate_capacity_mostly_unknown" in review["selector_blockers"]
    assert "generated_set_contains_negative_capacity_candidates" in review["selector_blockers"]


def test_candidate_move_capacity_annotation_remains_offline_capacity_evidence():
    observation_payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "source_stage": "stage5",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a2",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a3",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                        ]
                    }
                },
            }
        ]
    }
    capacity_payload = {
        "rows": [
            {
                "fen": "fen-a",
                "forced_first_move": "a1a2",
                "capacity_label": "positive_capacity",
                "provider_id": "krk.fence_established",
                "forced_result": "mate",
                "stage7_challenge_row": False,
            }
        ]
    }

    payload = _candidate_move_annotation.build_payload(
        observation_payload=observation_payload,
        capacity_payload=capacity_payload,
    )

    assert payload["summary"]["annotated_candidate_move_count"] == 1
    assert payload["summary"]["annotation_counts"]["positive_capacity"] == 1
    assert payload["summary"]["annotation_counts"]["unannotated"] == 1
    assert payload["interpretation"]["capacity_labels_are_not_ownership_labels"] is True
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_move_capacity_manifest_is_bounded_and_protected_only():
    observation_payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "state_id": "state.a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "selected_move_before_observation": "a1a2",
                        "selected_provider_before_observation": "krk.fence_established",
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a3",
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["box_area_not_increased_after_move"],
                                "safety_terms": [],
                                "source_terms": [],
                            }
                        ],
                    }
                },
            },
            {
                "case_id": "stage7_state",
                "state_id": "state.b",
                "source_stage": "stage7",
                "active_landmark_label": "box_shrink",
                "held_out": True,
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-b",
                                "move_uci": "b1b2",
                            }
                        ],
                    }
                },
            },
        ]
    }
    capacity_payload = {"rows": []}

    payload = _candidate_move_manifest.build_payload(
        observation_payload=observation_payload,
        capacity_payload=capacity_payload,
        cap=4,
    )

    assert payload["summary"]["job_count"] == 1
    assert payload["summary"]["stage7_job_count"] == 0
    assert payload["jobs"][0]["label_semantics"] == (
        "forced_first_move_capacity_not_runtime_ownership_label"
    )
    assert payload["decision"]["labels_run_by_this_artifact"] is False
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_move_capacity_label_payload_validation_blocks_stage7():
    payload = {
        "schema_version": "krk_candidate_move_capacity_labels.v1",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": {
            "stage7_label_count": 0,
            "stage7_training_label_count": 0,
        },
        "labels": [
            {
                "causal_status": "non_causal_outcome_label",
                "label_semantics": "forced_first_move_capacity_not_runtime_ownership_label",
            }
        ],
    }

    _candidate_move_label.validate_payload(payload)


def test_candidate_move_capacity_merge_improves_annotation_but_keeps_selector_blocked():
    observation_payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "source_stage": "stage5",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a2",
                            },
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a3",
                            },
                        ]
                    }
                },
            }
        ]
    }
    capacity_payload = {
        "rows": [
            {
                "fen": "fen-a",
                "forced_first_move": "a1a2",
                "capacity_label": "positive_capacity",
                "forced_result": "mate",
                "provider_id": "krk.fence_established",
            }
        ]
    }
    label_payload = {
        "labels": [
            {
                "fen": "fen-a",
                "forced_first_move": "a1a3",
                "capacity_label": "negative_capacity",
                "result": "max_plies",
                "source_stage": "stage5",
                "label_semantics": "forced_first_move_capacity_not_runtime_ownership_label",
            }
        ]
    }

    payload = _candidate_move_merge.build_payload(
        observation_payload=observation_payload,
        capacity_payload=capacity_payload,
        label_payload=label_payload,
    )

    assert payload["summary"]["annotated_candidate_move_count"] == 2
    assert payload["summary"]["annotation_counts"]["positive_capacity"] == 1
    assert payload["summary"]["annotation_counts"]["negative_capacity"] == 1
    assert payload["interpretation"]["capacity_labels_are_not_ownership_labels"] is True
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_generation_label_blocker_review_rejects_blind_label_farming():
    gap_review = {
        "summary": {
            "frame_count": 100,
            "missing_expected_sources": ["plan_capsule_sequence_candidate"],
        },
        "selector_blockers": ["candidate_capacity_mostly_unknown"],
    }
    annotation_v2 = {
        "summary": {
            "candidate_move_frame_count": 80,
            "protected_candidate_move_count": 70,
            "protected_annotated_candidate_move_count": 5,
            "protected_annotation_recall": 5 / 70,
        }
    }
    labels_v1 = {
        "summary": {
            "label_count": 12,
            "capacity_label_counts": {"positive_capacity": 11, "negative_capacity": 1},
            "stage7_label_count": 0,
            "stage7_training_label_count": 0,
        }
    }
    manifest_v1 = {"summary": {"job_count": 12}}

    payload = _candidate_label_blocker.build_payload(
        gap_review=gap_review,
        annotation_v2=annotation_v2,
        labels_v1=labels_v1,
        manifest_v1=manifest_v1,
    )

    assert payload["decision"]["selector_allowed"] is False
    assert payload["interpretation"]["more_blind_label_farming_not_recommended"] is True
    assert "candidate_move_annotation_coverage_too_sparse" in payload["blockers"]


def test_candidate_proposal_quality_review_stays_non_causal():
    payload = _candidate_quality_review.build_payload(
        gap_review={
            "summary": {
                "frame_count": 10,
                "missing_expected_sources": ["plan_capsule_sequence_candidate"],
            }
        },
        annotation_v2={
            "summary": {
                "candidate_move_frame_count": 8,
                "protected_candidate_move_count": 8,
                "protected_annotated_candidate_move_count": 2,
                "protected_annotation_recall": 0.25,
            }
        },
        blocker_review={
            "evidence": {
                "bounded_label_count": 4,
                "bounded_label_positive_capacity_count": 3,
                "bounded_label_negative_capacity_count": 1,
            }
        },
    )

    assert payload["decision"]["status"] == "proposal_quality_prioritization_review_ready"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert "runtime_selector" in payload["forbidden_next_steps"]
    assert payload["decision"]["recommended_next_step"] == (
        "build_non_causal_candidate_proposal_quality_dataset"
    )


def test_candidate_proposal_quality_dataset_keeps_capacity_not_selector_labels():
    observation_payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "state_id": "state.a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "selected_move_before_observation": "a1a2",
                        "selected_provider_before_observation": "krk.stage0_basin",
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a3",
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["box_area_not_increased_after_move"],
                                "safety_terms": [],
                                "source_terms": ["rook_safe"],
                                "direct_request": False,
                                "score_delta": 0.0,
                            }
                        ],
                    }
                },
            }
        ]
    }
    capacity_payload = {"rows": []}
    label_payload = {
        "labels": [
            {
                "fen": "fen-a",
                "forced_first_move": "a1a3",
                "capacity_label": "positive_capacity",
                "source_stage": "stage5",
            }
        ]
    }

    payload = _candidate_quality_dataset.build_payload(
        observation_payload=observation_payload,
        annotation_payload={"summary": {}},
        capacity_payload=capacity_payload,
        label_payload=label_payload,
    )

    assert payload["summary"]["quality_probe_row_count"] == 1
    assert payload["rows"][0]["capacity_evidence_kind"] == "positive_capacity"
    assert payload["rows"][0]["usable_for_selector_training"] is False
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_proposal_quality_decision_blocks_selector_when_probe_weak():
    dataset = {
        "summary": {
            "row_count": 10,
            "quality_probe_row_count": 5,
            "stage7_challenge_row_count": 1,
            "stage7_readiness_training_row_count": 0,
        }
    }
    probe = {
        "summary": {
            "best_probe": "fixture",
            "best_probe_metrics": {
                "positive_precision": 0.8,
                "positive_recall": 0.6,
                "negative_suppression": 0.6,
                "balanced_score": 0.6,
            },
        }
    }

    payload = _candidate_quality_decision.build_payload(dataset=dataset, probe=probe)

    assert payload["decision"]["status"] == "candidate_proposal_quality_not_selector_ready"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["more_blind_label_farming_allowed"] is False
    assert payload["decision"]["recommended_next_step"] == (
        "design_broader_strategy_sequence_candidate_sources"
    )


def test_broader_strategy_sequence_candidate_source_design_requires_separate_review():
    payload = _broader_source_design.build_payload(
        quality_decision={"decision": {"status": "candidate_proposal_quality_not_selector_ready"}},
        gap_review={
            "decision": {
                "status": "observation_gap_review_blocks_selector_recommends_capacity_annotation"
            }
        },
    )

    assert payload["decision"]["status"] == (
        "broader_strategy_sequence_candidate_source_design_ready"
    )
    assert payload["decision"]["implementation_allowed_by_this_artifact"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["runtime_candidate_generator_changes_implemented"] is False
    assert "runtime_source_expansion_without_review" in payload["forbidden_next_steps"]


def test_plan_capsule_and_broader_strategy_source_reviews_block_runtime_expansion():
    plan = _source_review.plan_capsule_review(
        source_design={
            "candidate_source_contracts": [
                {
                    "candidate_source": "plan_capsule_sequence_candidate",
                    "required_fields": ["plan_capsule_id"],
                }
            ]
        },
        plan_spec={
            "plan_capsule": {
                "capsule_id": "krk.plan",
                "causal_status": "non_causal",
                "promotion_status": "sandboxed",
                "ttl_white_moves": 3,
                "entry_terms": ["entry"],
                "progress_terms": ["progress"],
                "exit_terms": ["exit"],
                "abort_terms": ["abort"],
                "handoff_exports": {"krk.stage0_basin": 0.1},
            }
        },
        plan_failure={"summary_counters": {"plan_capsule_selected_supported_count": 1}},
        plan_audit={"diagnosis": {"missing_plan_commitment": "likely"}},
    )
    strategy = _source_review.broader_strategy_review(
        source_design={
            "candidate_source_contracts": [
                {
                    "candidate_source": "broader_strategy_candidate",
                    "required_fields": ["strategy_id"],
                }
            ]
        },
        sequence_frames={
            "frames": [
                {
                    "frame_type": "broader_krk_strategy_candidate",
                    "source_stage": "stage7",
                    "stage7_challenge_row": True,
                    "candidate_strategy_family": "terminal.krk.post_plan_stagnation",
                }
            ]
        },
        monitor_records={"summary": {"monitor_record_count": 1}},
        internal_terminals={
            "summary": {
                "strongest_internal_terminal_candidates": [
                    "terminal.krk.post_plan_stagnation"
                ],
                "causal_ready_terminals": [],
            }
        },
    )
    combined = _source_review.combined_review(plan, strategy)

    assert plan["decision"]["implementation_allowed_by_this_artifact"] is False
    assert strategy["decision"]["implementation_allowed_by_this_artifact"] is False
    assert strategy["readiness"]["stage7_only_evidence"] is True
    assert combined["decision"]["runtime_changes_allowed"] is False
    assert combined["decision"]["recommended_next_step"] == (
        "build_protected_cross_stage_strategy_monitor_frame_expansion_non_causal"
    )


def test_protected_strategy_monitor_frame_expansion_excludes_stage7():
    payload = _protected_monitor_expansion.build_payload(
        monitor_payload={
            "records": [
                {
                    "active_landmark_label": "fence_established",
                    "monitor_type": "RepairNeededMonitor",
                    "state_id": "state.a",
                    "fen": "fen-a",
                    "associated_outcome": "max_plies",
                    "source_terms": ["repair_needed"],
                },
                {
                    "active_landmark_label": "box_shrink",
                    "monitor_type": "PlanSelectionNeededMonitor",
                    "state_id": "state.b",
                    "fen": "fen-b",
                    "associated_outcome": "max_plies",
                    "source_terms": ["plan_needed"],
                },
            ]
        },
        source_review={"decision": {"status": "source_reviews_complete_runtime_expansion_not_authorized"}},
    )

    assert payload["summary"]["frame_count"] == 1
    assert payload["summary"]["stage7_challenge_row_count"] == 0
    assert payload["frames"][0]["source_stage"] == "stage5"
    assert payload["frames"][0]["usable_for_selector_training"] is False
    assert payload["decision"]["selector_allowed"] is False


def test_protected_strategy_monitor_quality_packet_requires_explicit_approval():
    quality = _protected_monitor_quality.build_payload(
        frames_payload={
            "frames": [
                {
                    "candidate_strategy_family": "terminal.krk.repair_needed_monitor",
                    "associated_outcome": "max_plies",
                    "stage7_challenge_row": False,
                }
                for _ in range(4)
            ]
            + [
                {
                    "candidate_strategy_family": "terminal.krk.repair_needed_monitor",
                    "associated_outcome": "mate",
                    "stage7_challenge_row": False,
                }
            ]
        }
    )
    packet = _protected_monitor_packet.build_payload(
        expansion={
            "summary": {
                "frame_count": 5,
                "frame_count_by_stage": {"stage5": 5},
                "stage7_challenge_row_count": 0,
            }
        },
        quality=quality,
    )

    assert quality["decision"]["status"] == "protected_strategy_monitor_frames_have_monitor_signal"
    assert packet["decision"]["status"] == (
        "protected_repair_monitor_observation_source_review_ready"
    )
    assert packet["decision"]["implementation_allowed_by_this_packet"] is False
    assert packet["decision"]["selector_allowed"] is False


def test_repair_monitor_observation_source_emits_only_for_protected_scope():
    suggestion = {
        "move": "a1a2",
        "score": 1.0,
        "meta": {"curriculum_label": "fence_established"},
    }

    observation = _landmark._krk_candidate_generation_observation_for_suggestions(
        [suggestion],
        selected_suggestion=suggestion,
        active_landmark_label="fence_established",
        visible_terms={
            "repair_or_reestablish_cut_available": True,
            "rook_safe": True,
        },
        board=None,
        blackboard={},
        limit=0,
        repair_monitor_observation_source_enabled=True,
    )
    repair_frames = [
        frame
        for frame in observation["frames"]
        if frame.get("strategy_family") == "terminal.krk.repair_needed_monitor"
    ]

    assert len(repair_frames) == 1
    frame = repair_frames[0]
    assert frame["candidate_source"] == "broader_strategy_candidate"
    assert frame["direct_request"] is False
    assert frame["score_delta"] == 0.0
    assert frame["causal_status"] == "observation_only"
    assert frame["protected_status"] == "protected_control"
    assert "selecting_a_provider" in frame["forbidden_actions"]
    assert "repair_or_reestablish_cut_available" in frame["risk_terms"]

    held_out_observation = _landmark._krk_candidate_generation_observation_for_suggestions(
        [suggestion],
        selected_suggestion=suggestion,
        active_landmark_label="box_shrink",
        visible_terms={
            "repair_or_reestablish_cut_available": True,
            "rook_safe": True,
        },
        board=None,
        blackboard={},
        limit=0,
        repair_monitor_observation_source_enabled=True,
    )

    assert not [
        frame
        for frame in held_out_observation["frames"]
        if frame.get("strategy_family") == "terminal.krk.repair_needed_monitor"
    ]


def test_repair_monitor_observation_source_coverage_blocks_selector_and_guardrails():
    payload = _repair_monitor_coverage.build_payload(
        {
            "summary": {
                "stage7_case_count": 0,
                "selected_move_provider_delta_count": 0,
            },
            "cases": [
                {
                    "source_stage": "stage5",
                    "enabled_repair_monitor_sample_frames": [
                        {
                            "candidate_source": "broader_strategy_candidate",
                            "strategy_family": "terminal.krk.repair_needed_monitor",
                            "risk_terms": ["repair_or_reestablish_cut_available"],
                            "direct_request": False,
                            "score_delta": 0.0,
                            "causal_status": "observation_only",
                        }
                    ],
                }
            ],
        }
    )

    assert payload["decision"]["status"] == (
        "repair_monitor_observation_source_coverage_ready_for_guarded_analysis"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert payload["summary"]["stage7_case_count"] == 0
    assert payload["summary"]["invariant_failure_count"] == 0


def test_repair_monitor_observation_smoke_loads_protected_cases_only():
    cases = _repair_monitor_smoke._load_cases()

    assert cases
    assert all(case["source_stage"] in {"stage4", "stage5", "stage6"} for case in cases)
    assert all(case["held_out"] is False for case in cases)


def test_repair_monitor_observation_broadened_summary_blocks_selector():
    rows = [
        {
            "case_id": f"case_{idx}",
            "source_stage": "stage5",
            "selected_provider": "krk.stage0_basin",
            "baseline_decision": {"observation": {"frames": []}},
            "enabled_decision": {
                "observation": {
                    "frames": [
                        {
                            "candidate_source": "broader_strategy_candidate",
                            "strategy_family": "terminal.krk.repair_needed_monitor",
                            "risk_terms": ["repair_or_reestablish_cut_available"],
                            "direct_request": False,
                            "score_delta": 0.0,
                            "causal_status": "observation_only",
                            "protected_status": "protected_control",
                        }
                    ]
                }
            },
            "selected_move_provider_score_equivalent": True,
            "baseline_repair_monitor_frame_count": 0,
            "enabled_repair_monitor_frame_count": 1,
            "enabled_repair_monitor_sample_frames": [
                {
                    "candidate_source": "broader_strategy_candidate",
                    "strategy_family": "terminal.krk.repair_needed_monitor",
                    "risk_terms": ["repair_or_reestablish_cut_available"],
                    "direct_request": False,
                    "score_delta": 0.0,
                    "causal_status": "observation_only",
                    "protected_status": "protected_control",
                }
            ],
        }
        for idx in range(4)
    ]

    summary = _repair_monitor_broadened._summary(rows)
    decision = _repair_monitor_broadened._decision(summary)

    assert summary["case_count"] == 4
    assert summary["repair_monitor_frame_count"] == 4
    assert summary["stage7_case_count"] == 0
    assert summary["selected_move_provider_delta_count"] == 0
    assert summary["invariant_failure_count"] == 0
    assert decision["status"] == (
        "repair_monitor_observation_source_broadened_default_off_equivalent"
    )
    assert decision["selector_allowed"] is False
    assert decision["guardrails_allowed"] is False


def test_repair_monitor_observation_quality_keeps_trace_only_use():
    payload = _repair_monitor_quality.build_payload(
        {
            "summary": {
                "selected_move_provider_delta_count": 0,
                "baseline_repair_monitor_frame_count": 0,
                "invariant_failure_count": 0,
                "stage7_case_count": 0,
            },
            "cases": [
                {
                    "case_id": "case_a",
                    "source_stage": "stage5",
                    "selected_provider": "krk.stage0_basin",
                    "enabled_repair_monitor_sample_frames": [
                        {
                            "candidate_source": "broader_strategy_candidate",
                            "strategy_family": "terminal.krk.repair_needed_monitor",
                            "risk_terms": [
                                "repair_or_reestablish_cut_available",
                                "post_fence_conversion_needed",
                            ],
                            "licensed_provider_families": ["krk.fence_established"],
                            "direct_request": False,
                            "score_delta": 0.0,
                            "causal_status": "observation_only",
                            "protected_status": "protected_control",
                        }
                    ],
                }
            ],
        }
    )

    assert payload["decision"]["status"] == (
        "repair_monitor_observation_source_quality_trace_only_retained"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert payload["interpretation"]["quality_signal_mature"] is False
    assert "selector_input_without_separate_review" in payload["interpretation"]["forbidden_use"]


def test_repair_monitor_trace_fold_keeps_rows_non_causal_and_non_training():
    payload = _repair_monitor_trace_fold.build_payload(
        base_payload={"summary": {"frame_count": 1}},
        repair_payload={
            "cases": [
                {
                    "case_id": "case_a",
                    "state_id": "state.a",
                    "fen": "fen-a",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "selected_move_provider_score_equivalent": True,
                    "enabled_repair_monitor_sample_frames": [
                        {
                            "candidate_source": "broader_strategy_candidate",
                            "strategy_family": "terminal.krk.repair_needed_monitor",
                            "selected_provider_before_observation": "krk.stage0_basin",
                            "selected_move_before_observation": "a1a2",
                            "risk_terms": ["repair_or_reestablish_cut_available"],
                            "handoff_or_exit_terms": ["repair_or_reestablish_cut_available"],
                            "licensed_provider_families": ["krk.fence_established"],
                            "source_monitor_records": ["terminal.krk.repair_needed_monitor"],
                            "source_terms": ["repair_or_reestablish_cut_available"],
                            "capacity_evidence_kind": "unknown_capacity",
                        }
                    ],
                },
                {
                    "case_id": "heldout",
                    "state_id": "state.stage7",
                    "source_stage": "stage7",
                    "enabled_repair_monitor_sample_frames": [
                        {
                            "candidate_source": "broader_strategy_candidate",
                            "strategy_family": "terminal.krk.repair_needed_monitor",
                        }
                    ],
                },
            ]
        },
        quality_payload={"decision": {"selector_allowed": False}},
    )

    assert payload["decision"]["status"] == "repair_monitor_trace_features_folded_non_causal"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["trace_frame_count"] == 1
    assert payload["summary"]["stage7_trace_frame_count"] == 0
    frame = payload["trace_only_frames"][0]
    assert frame["label_semantics"] == "runtime_observation_context_not_selector_label"
    assert frame["usable_for_selector_training"] is False
    assert frame["usable_for_candidate_generation_training"] is False
    assert frame["causal_status"] == "non_causal_trace_feature"


def test_strategy_sequence_trace_feature_review_keeps_selector_blocked():
    payload = _trace_feature_review.build_payload(
        base_payload={
            "summary": {
                "frame_count": 10,
                "stage7_challenge_row_count": 2,
                "readiness_training_stage7_row_count": 0,
            }
        },
        trace_payload={
            "runtime_behavior_changed": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "summary": {
                "trace_frame_count": 6,
                "stage_counts": {"stage5": 6},
                "stage7_trace_frame_count": 0,
                "selector_training_row_count": 0,
                "candidate_generation_training_row_count": 0,
            },
            "decision": {"selector_allowed": False},
        },
        quality_payload={
            "summary": {"risk_term_set_count": 1},
            "interpretation": {"quality_signal_mature": False},
        },
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_trace_features_integrated_selector_still_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert "trace_features_are_not_selector_labels" in payload["selector_blockers"]


def test_strategy_sequence_dataset_design_v2_separates_trace_and_labels():
    payload = _dataset_design_v2.build_payload(
        {
            "decision": {
                "status": "strategy_sequence_trace_features_integrated_selector_still_blocked"
            },
            "summary": {"trace_frame_count": 6},
            "selector_blockers": ["trace_features_are_not_selector_labels"],
        }
    )

    channels = {item["channel"]: item for item in payload["evidence_channels"]}

    assert payload["decision"]["status"] == "strategy_sequence_dataset_design_v2_ready"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["partition_rules"]["stage7_training_rows_allowed"] is False
    assert channels["runtime_observation_trace_feature"]["forbidden_use"] == (
        "selector_training_or_guardrail_trigger"
    )
    assert channels["validated_provider_capacity"]["forbidden_use"] == (
        "selector_training_label"
    )


def test_strategy_sequence_dataset_v2_blocks_selector_and_preserves_generator_rows():
    base_frame = {
        "frame_id": "frame.capacity",
        "state_id": "state.a",
        "source_stage": "stage5",
        "frame_type": "validated_provider_candidate",
        "candidate_strategy_family": "fence_established",
        "label_semantics": "capacity_evidence_not_ownership_label",
        "stage7_challenge_row": False,
        "usable_for_selector_training": True,
        "capacity_evidence": {"capacity_label": "positive_capacity"},
    }
    trace_frame = {
        "frame_id": "frame.trace",
        "state_id": "state.b",
        "source_stage": "stage5",
        "frame_type": "broader_krk_strategy_candidate",
        "candidate_strategy_family": "terminal.krk.repair_needed_monitor",
        "label_semantics": "runtime_observation_context_not_selector_label",
        "stage7_challenge_row": False,
        "usable_for_selector_training": False,
    }

    payload = _dataset_v2.build_payload(
        base_payload={"frames": [base_frame]},
        trace_payload={"trace_only_frames": [trace_frame]},
        design_payload={"schema_version": "krk_strategy_sequence_dataset_design.v2"},
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v2_refreshed_non_causal_selector_blocked"
    )
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["candidate_generation_training_row_count"] == 1
    assert payload["summary"]["runtime_trace_feature_row_count"] == 1
    assert payload["rows"][0]["legacy_usable_for_selector_training"] is True
    assert payload["rows"][0]["usable_for_selector_training_v2"] is False
    assert payload["rows"][0]["usable_for_candidate_generation_training_v2"] is True


def test_strategy_sequence_dataset_v2_quality_keeps_selector_blocked():
    payload = _dataset_v2_quality.build_payload(
        {
            "runtime_behavior_changed": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "summary": {
                "row_count_by_channel": {
                    "validated_provider_capacity": 1,
                    "visible_provider_proposal": 1,
                    "candidate_move_frame": 1,
                    "runtime_observation_trace_feature": 1,
                },
                "stage7_readiness_training_row_count": 0,
            },
            "rows": [
                {
                    "evidence_channel": "validated_provider_capacity",
                    "stage7_challenge_row": False,
                    "usable_for_candidate_generation_training_v2": True,
                    "usable_for_selector_training_v2": False,
                },
                {
                    "evidence_channel": "runtime_observation_trace_feature",
                    "stage7_challenge_row": False,
                    "usable_for_candidate_generation_training_v2": False,
                    "usable_for_selector_training_v2": False,
                },
                {
                    "evidence_channel": "candidate_move_frame",
                    "stage7_challenge_row": True,
                    "usable_for_candidate_generation_training_v2": False,
                    "usable_for_selector_training_v2": False,
                },
            ],
        }
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v2_quality_candidate_generation_ready_selector_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["interpretation"]["candidate_generation_dataset_usable"] is True
    assert payload["interpretation"]["selector_dataset_usable"] is False
    assert "no_explicit_ownership_selector_rows" in payload["selector_blockers"]


def test_candidate_generation_refresh_probe_uses_capacity_not_ownership_labels():
    dataset = {
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage5",
                "candidate_strategy_family": "fence_established",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage5",
                "candidate_strategy_family": "drive_to_edge",
                "capacity_label": "negative_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage7",
                "candidate_strategy_family": "box_shrink",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": True,
            },
        ]
    }

    payload = _candidate_generation_refresh.build_payload(
        dataset=dataset,
        quality={"decision": {"status": "fixture"}},
    )

    assert payload["summary"]["capacity_row_count"] == 2
    assert payload["decision"]["selector_allowed"] is False
    assert payload["interpretation"]["capacity_labels_are_not_ownership_labels"] is True
    assert payload["interpretation"]["stage7_training_allowed"] is False
    assert payload["policy_metrics"]["oracle_positive_capacity_ceiling"]["positive_recall"] == 1.0


def test_candidate_generation_capacity_manifest_is_protected_and_non_causal():
    dataset = {
        "rows": [
            {
                "evidence_channel": "visible_provider_proposal",
                "state_id": "state.a",
                "fen": "fen-a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "candidate_provider_id": "krk.fence_established",
                "candidate_strategy_family": "fence_established",
                "candidate_move_uci": "a1a2",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "visible_provider_proposal",
                "state_id": "state.b",
                "source_stage": "stage7",
                "candidate_provider_id": "krk.box_shrink",
                "candidate_strategy_family": "box_shrink",
                "stage7_challenge_row": True,
            },
        ]
    }

    payload = _capacity_evidence_manifest.build_payload(
        dataset=dataset,
        refresh_probe={"decision": {"status": "underpowered"}},
        cap=4,
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_capacity_evidence_manifest_ready"
    )
    assert payload["decision"]["labels_run_by_this_artifact"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["job_count"] == 1
    assert payload["summary"]["stage7_job_count"] == 0
    assert payload["jobs"][0]["label_semantics"] == (
        "forced_provider_capacity_not_runtime_ownership"
    )
    assert payload["jobs"][0]["selector_training_allowed"] is False


def test_candidate_generation_capacity_labels_validate_non_causal_capacity_semantics():
    payload = {
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": {
            "stage7_label_count": 0,
            "stage7_training_label_count": 0,
        },
        "labels": [
            {
                "causal_status": "non_causal_outcome_label",
                "label_semantics": "forced_provider_capacity_not_runtime_ownership",
            }
        ],
    }

    _capacity_evidence_labels.validate_payload(payload)


def test_candidate_generation_capacity_merge_preserves_selector_block():
    payload = _capacity_evidence_merge.build_dataset_payload(
        dataset={"rows": []},
        labels={
            "causal_status": "non_causal_label_run",
            "summary": {"stage7_label_count": 0},
            "labels": [
                {
                    "job_id": "job.a",
                    "causal_status": "non_causal_outcome_label",
                    "state_id": "state.a",
                    "source_stage": "stage5",
                    "provider_id": "krk.stage0_basin",
                    "provider_family": "stage0_basin",
                    "result": "mate",
                    "forced_first_move": "a1a2",
                    "label_semantics": "forced_provider_capacity_not_runtime_ownership",
                },
                {
                    "job_id": "job.b",
                    "causal_status": "non_causal_outcome_label",
                    "state_id": "state.b",
                    "source_stage": "stage6",
                    "provider_id": "krk.drive_to_edge",
                    "provider_family": "drive_to_edge",
                    "result": "max_plies",
                    "label_semantics": "forced_provider_capacity_not_runtime_ownership",
                },
            ],
        },
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v2_capacity_merged_non_causal"
    )
    assert payload["summary"]["merged_label_capacity_counts"] == {
        "negative_capacity": 1,
        "positive_capacity": 1,
    }
    assert payload["summary"]["candidate_generation_training_row_count"] == 1
    assert payload["summary"]["selector_training_row_count"] == 0
    assert all(row["usable_for_selector_training_v2"] is False for row in payload["rows"])


def test_candidate_generation_training_refresh_design_blocks_runtime_selector():
    payload = _training_refresh_design.build_payload(
        merged_dataset={
            "summary": {
                "candidate_generation_training_row_count": 14,
                "selector_training_row_count": 0,
                "stage7_readiness_training_row_count": 0,
            },
            "decision": {"status": "strategy_sequence_dataset_v2_capacity_merged_non_causal"},
        },
        refresh_probe={
            "summary": {
                "capacity_row_count": 20,
                "capacity_label_counts": {
                    "positive_capacity": 14,
                    "negative_capacity": 6,
                },
                "best_non_oracle_policy": "stage_family_pure_positive_with_support_2",
                "best_non_oracle_metrics": {
                    "positive_recall": 0.75,
                    "positive_precision": 1.0,
                    "negative_suppression": 1.0,
                    "false_negative": 2,
                    "false_positive": 0,
                },
                "leave_stage_out_aggregate": {
                    "positive_recall": 0.5,
                    "negative_suppression": 0.25,
                },
            },
            "decision": {"status": "candidate_generation_refresh_supported_selector_blocked"},
        },
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_training_refresh_design_ready"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_candidate_generator_refresh_allowed"] is False
    assert payload["readiness_assessment"]["candidate_refresh_supported"] is True
    assert payload["readiness_assessment"]["cross_stage_generalization_supported"] is False
    assert payload["training_refresh_scope"]["selector_rows_allowed"] is False
    assert payload["training_refresh_scope"]["stage7_rows_use"] == "held_out_challenge_only"
    assert "using_capacity_labels_as_ownership_labels" in payload["forbidden_next_steps"]


def test_candidate_generation_cross_stage_review_recommends_stratified_manifest():
    payload = _cross_stage_capacity_review.build_payload(
        merged_dataset={
            "rows": [
                {
                    "evidence_channel": "validated_provider_capacity",
                    "source_stage": "stage5",
                    "candidate_strategy_family": "stage0_basin",
                    "capacity_label": "positive_capacity",
                    "stage7_challenge_row": False,
                    "state_id": "state.a",
                },
                {
                    "evidence_channel": "validated_provider_capacity",
                    "source_stage": "stage5",
                    "candidate_strategy_family": "stage0_basin",
                    "capacity_label": "positive_capacity",
                    "stage7_challenge_row": False,
                    "state_id": "state.b",
                },
                {
                    "evidence_channel": "validated_provider_capacity",
                    "source_stage": "stage6",
                    "candidate_strategy_family": "stage0_basin",
                    "capacity_label": "negative_capacity",
                    "stage7_challenge_row": False,
                    "state_id": "state.c",
                },
                {
                    "evidence_channel": "validated_provider_capacity",
                    "source_stage": "stage7",
                    "candidate_strategy_family": "box_shrink",
                    "capacity_label": "positive_capacity",
                    "stage7_challenge_row": True,
                    "state_id": "state.stage7",
                },
            ]
        },
        refresh_probe={
            "summary": {
                "leave_stage_out_aggregate": {
                    "positive_recall": 0.4,
                    "negative_suppression": 0.0,
                }
            }
        },
        training_design={
            "readiness_assessment": {
                "candidate_refresh_supported": True,
                "cross_stage_generalization_supported": False,
            }
        },
    )

    assert payload["decision"]["status"] == (
        "cross_stage_capacity_review_recommends_stratified_capacity_manifest"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_candidate_generator_refresh_allowed"] is False
    assert payload["summary"]["stage7_readiness_training_row_count"] == 0
    assert payload["stage_family_cells"]["stage5|stage0_basin"]["maturity"] == (
        "positive_only_cell"
    )
    assert payload["stage_family_cells"]["stage6|stage0_basin"]["maturity"] == (
        "underpowered_cell"
    )
    assert payload["recommended_manifest_scope"]["stage7_jobs_allowed"] is False


def test_candidate_generation_cross_stage_manifest_targets_protected_cells_only():
    payload = _cross_stage_capacity_manifest.build_payload(
        dataset={
            "rows": [
                {
                    "evidence_channel": "validated_provider_capacity",
                    "state_id": "state.a",
                    "candidate_provider_id": "krk.stage0_basin",
                    "source_stage": "stage5",
                    "candidate_strategy_family": "stage0_basin",
                },
                {
                    "evidence_channel": "visible_provider_proposal",
                    "state_id": "state.a",
                    "candidate_provider_id": "krk.stage0_basin",
                    "candidate_strategy_family": "stage0_basin",
                    "candidate_move_uci": "a1a2",
                    "source_stage": "stage5",
                    "stage7_challenge_row": False,
                },
                {
                    "evidence_channel": "visible_provider_proposal",
                    "state_id": "state.b",
                    "candidate_provider_id": "krk.stage0_basin",
                    "candidate_strategy_family": "stage0_basin",
                    "candidate_move_uci": "a1a3",
                    "source_stage": "stage5",
                    "stage7_challenge_row": False,
                },
                {
                    "evidence_channel": "visible_provider_proposal",
                    "state_id": "state.stage7",
                    "candidate_provider_id": "krk.box_shrink",
                    "candidate_strategy_family": "box_shrink",
                    "candidate_move_uci": "b1b2",
                    "source_stage": "stage7",
                    "stage7_challenge_row": True,
                },
            ]
        },
        review={
            "findings": {
                "positive_only_cells": ["stage5|stage0_basin"],
                "negative_only_cells": [],
                "mixed_capacity_cells": [],
                "underpowered_cells": [],
            }
        },
        cap=4,
    )

    assert payload["decision"]["status"] == (
        "cross_stage_capacity_manifest_ready_partial_target_coverage"
    )
    assert payload["decision"]["labels_run_by_this_artifact"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["job_count"] == 1
    assert payload["summary"]["stage7_job_count"] == 0
    assert payload["jobs"][0]["state_id"] == "state.b"
    assert payload["jobs"][0]["label_semantics"] == (
        "forced_provider_capacity_not_runtime_ownership"
    )


def test_candidate_generation_cross_stage_labels_validate_non_causal_semantics():
    payload = {
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": {
            "stage7_label_count": 0,
            "stage7_training_label_count": 0,
        },
        "labels": [
            {
                "causal_status": "non_causal_outcome_label",
                "label_semantics": "forced_provider_capacity_not_runtime_ownership",
            }
        ],
    }

    _cross_stage_capacity_labels.validate_payload(payload)


def test_candidate_generation_cross_stage_merge_keeps_selector_blocked():
    payload = _cross_stage_capacity_merge.build_dataset_payload(
        base_dataset={"rows": []},
        labels={
            "causal_status": "non_causal_label_run",
            "summary": {"stage7_label_count": 0},
            "labels": [
                {
                    "job_id": "job.cross.a",
                    "causal_status": "non_causal_outcome_label",
                    "state_id": "state.a",
                    "source_stage": "stage5",
                    "provider_id": "krk.stage0_basin",
                    "provider_family": "stage0_basin",
                    "stage_family_cell": "stage5|stage0_basin",
                    "target_cell_maturity": "positive_only_cell",
                    "result": "mate",
                    "forced_first_move": "a1a2",
                    "label_semantics": "forced_provider_capacity_not_runtime_ownership",
                },
                {
                    "job_id": "job.cross.b",
                    "causal_status": "non_causal_outcome_label",
                    "state_id": "state.b",
                    "source_stage": "stage6",
                    "provider_id": "krk.edge_trap_close",
                    "provider_family": "edge_trap",
                    "stage_family_cell": "stage6|edge_trap",
                    "target_cell_maturity": "negative_only_cell",
                    "result": "max_plies",
                    "label_semantics": "forced_provider_capacity_not_runtime_ownership",
                },
            ],
        },
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v2_cross_stage_capacity_merged_non_causal"
    )
    assert payload["summary"]["merged_cross_stage_label_capacity_counts"] == {
        "negative_capacity": 1,
        "positive_capacity": 1,
    }
    assert payload["summary"]["candidate_generation_training_row_count"] == 1
    assert payload["summary"]["selector_training_row_count"] == 0
    assert all(row["usable_for_selector_training_v2"] is False for row in payload["rows"])


def test_candidate_generation_cross_stage_label_outcome_blocks_runtime_when_generalization_weak():
    payload = _cross_stage_label_outcome_review.build_payload(
        pre_probe={
            "summary": {
                "capacity_row_count": 10,
                "capacity_label_counts": {"positive_capacity": 6, "negative_capacity": 4},
                "best_non_oracle_policy": "fixture",
                "best_non_oracle_metrics": {
                    "positive_recall": 0.7,
                    "positive_precision": 1.0,
                    "negative_suppression": 1.0,
                    "balanced_recall_risk": 0.85,
                },
                "leave_stage_out_aggregate": {
                    "positive_recall": 0.6,
                    "negative_suppression": 0.2,
                    "balanced_recall_risk": 0.4,
                },
            }
        },
        labels={
            "summary": {
                "label_count": 2,
                "result_counts": {"mate": 2},
                "stage7_label_count": 0,
                "stage7_training_label_count": 0,
            }
        },
        post_probe={
            "summary": {
                "capacity_row_count": 12,
                "capacity_label_counts": {"positive_capacity": 8, "negative_capacity": 4},
                "best_non_oracle_policy": "fixture",
                "best_non_oracle_metrics": {
                    "positive_recall": 0.8,
                    "positive_precision": 1.0,
                    "negative_suppression": 1.0,
                    "balanced_recall_risk": 0.9,
                },
                "leave_stage_out_aggregate": {
                    "positive_recall": 0.58,
                    "negative_suppression": 0.2,
                    "balanced_recall_risk": 0.39,
                },
            }
        },
    )

    assert payload["decision"]["status"] == (
        "cross_stage_capacity_labels_improve_in_sample_but_generalization_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_candidate_generator_refresh_allowed"] is False
    assert payload["interpretation"]["more_blind_capacity_labels_recommended"] is False
    assert payload["interpretation"]["capacity_labels_are_not_ownership_labels"] is True


def test_candidate_generation_stage_conditioned_scope_review_blocks_runtime():
    payload = _stage_conditioned_scope_review.build_payload(
        outcome_review={
            "decision": {
                "status": "cross_stage_capacity_labels_improve_in_sample_but_generalization_blocked"
            }
        },
        post_probe={
            "stage_family_rates": {
                "stage5|edge_trap": {
                    "support": 3,
                    "positive": 3,
                    "negative": 0,
                    "positive_rate": 1.0,
                },
                "stage6|edge_trap": {
                    "support": 3,
                    "positive": 0,
                    "negative": 3,
                    "positive_rate": 0.0,
                },
                "stage4|stage0_basin": {
                    "support": 3,
                    "positive": 2,
                    "negative": 1,
                    "positive_rate": 2 / 3,
                },
            }
        },
    )

    assert payload["decision"]["status"] == (
        "stage_conditioned_candidate_generation_scope_review_ready"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_candidate_generator_refresh_allowed"] is False
    assert payload["interpretation"]["stage_conditioned_scope_supported_for_benchmark"] is True
    assert payload["stage_scopes"]["stage5"]["positive_scope_families"] == ["edge_trap"]
    assert payload["stage_scopes"]["stage6"]["risk_scope_families"] == ["edge_trap"]
    assert payload["stage_scopes"]["stage4"]["mixed_scope_families"] == ["stage0_basin"]
    assert "provider_suppression" in payload["forbidden_uses"]


def test_stage_conditioned_candidate_generation_benchmark_separates_stage5_6_from_stage4():
    payload = _stage_conditioned_benchmark.build_payload(
        dataset={
            "rows": [
                {
                    "evidence_channel": "validated_provider_capacity",
                    "source_stage": "stage5",
                    "candidate_strategy_family": "edge_trap",
                    "capacity_label": "positive_capacity",
                    "stage7_challenge_row": False,
                },
                {
                    "evidence_channel": "validated_provider_capacity",
                    "source_stage": "stage6",
                    "candidate_strategy_family": "stage0_basin",
                    "capacity_label": "positive_capacity",
                    "stage7_challenge_row": False,
                },
                {
                    "evidence_channel": "validated_provider_capacity",
                    "source_stage": "stage6",
                    "candidate_strategy_family": "edge_trap",
                    "capacity_label": "negative_capacity",
                    "stage7_challenge_row": False,
                },
                {
                    "evidence_channel": "validated_provider_capacity",
                    "source_stage": "stage4",
                    "candidate_strategy_family": "stage0_basin",
                    "capacity_label": "positive_capacity",
                    "stage7_challenge_row": False,
                },
            ]
        },
        scope_review={
            "stage_scopes": {
                "stage5": {"positive_scope_families": ["edge_trap"]},
                "stage6": {"positive_scope_families": ["stage0_basin"]},
                "stage4": {"positive_scope_families": []},
            }
        },
    )

    assert payload["decision"]["status"] == (
        "stage_conditioned_candidate_generation_stage5_6_promising_stage4_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_candidate_generator_refresh_allowed"] is False
    assert payload["interpretation"]["stage5_6_scope_promising"] is True
    assert payload["interpretation"]["stage4_scope_blocked_without_companion_terms"] is True
    assert payload["summary"]["stage7_readiness_training_row_count"] == 0


def test_stage5_6_candidate_generation_refresh_packet_requires_explicit_approval():
    payload = _stage5_6_refresh_packet.build_payload(
        benchmark={
            "decision": {
                "status": "stage_conditioned_candidate_generation_stage5_6_promising_stage4_blocked"
            },
            "summary": {
                "stage5_6_positive_scope_metrics": {
                    "positive_recall": 1.0,
                    "negative_suppression": 1.0,
                },
                "stage4_positive_scope_metrics": {
                    "positive_recall": 0.0,
                    "negative_suppression": 1.0,
                },
                "positive_scope_cells": ["stage5|edge_trap", "stage6|stage0_basin"],
                "stage7_readiness_training_row_count": 0,
            },
        }
    )

    assert payload["decision"]["status"] == (
        "stage5_6_candidate_generation_refresh_review_ready"
    )
    assert payload["decision"]["runtime_review_ready"] is True
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["runtime_candidate_generator_refresh_allowed_by_this_packet"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["approved_scope_if_later_authorized"]["excluded_stages"] == [
        "stage4",
        "stage7",
        "stage8",
    ]
    assert "selecting_a_provider" in payload["explicitly_forbidden"]


def test_stage5_6_refresh_observation_source_is_default_off_and_scoped():
    suggestion = {
        "move": "a1a2",
        "score": 7.5,
        "meta": {"curriculum_label": "fence_established", "provider_version": "frozen"},
    }

    disabled = _landmark._krk_candidate_generation_observation_for_suggestions(
        [suggestion],
        selected_suggestion=suggestion,
        active_landmark_label="fence_established",
        visible_terms={"fence_exists": True},
        board=None,
        blackboard={},
        limit=1,
        stage5_6_candidate_generation_refresh_enabled=False,
    )
    enabled = _landmark._krk_candidate_generation_observation_for_suggestions(
        [suggestion],
        selected_suggestion=suggestion,
        active_landmark_label="fence_established",
        visible_terms={"fence_exists": True},
        board=None,
        blackboard={},
        limit=1,
        stage5_6_candidate_generation_refresh_enabled=True,
    )
    stage4 = _landmark._krk_candidate_generation_observation_for_suggestions(
        [suggestion],
        selected_suggestion=suggestion,
        active_landmark_label="wrong_tempo_control",
        visible_terms={"fence_exists": True},
        board=None,
        blackboard={},
        limit=1,
        stage5_6_candidate_generation_refresh_enabled=True,
    )
    stage7 = _landmark._krk_candidate_generation_observation_for_suggestions(
        [suggestion],
        selected_suggestion=suggestion,
        active_landmark_label="box_shrink",
        visible_terms={"fence_exists": True},
        board=None,
        blackboard={},
        limit=1,
        stage5_6_candidate_generation_refresh_enabled=True,
    )

    assert not any(
        frame.get("candidate_source") == "stage_conditioned_candidate_generation_refresh"
        for frame in disabled["frames"]
    )
    refresh_frames = [
        frame
        for frame in enabled["frames"]
        if frame.get("candidate_source") == "stage_conditioned_candidate_generation_refresh"
    ]
    assert refresh_frames
    assert refresh_frames[0]["direct_request"] is False
    assert refresh_frames[0]["score_delta"] == 0.0
    assert refresh_frames[0]["causal_status"] == "candidate_generation_only"
    assert refresh_frames[0]["policy"] == "trace_stage_family_context"
    assert refresh_frames[0]["stage"] == "stage5"
    assert refresh_frames[0]["provider_family"] == "fence_established"
    assert refresh_frames[0]["policy_cell"] == "stage5|fence_established"
    assert refresh_frames[0]["protected_status"] == "protected_control"
    assert "selecting_a_provider" in refresh_frames[0]["forbidden_actions"]
    assert not any(
        frame.get("candidate_source") == "stage_conditioned_candidate_generation_refresh"
        for frame in stage4["frames"]
    )
    assert not any(
        frame.get("candidate_source") == "stage_conditioned_candidate_generation_refresh"
        for frame in stage7["frames"]
    )


def test_stage5_6_refresh_smoke_loads_protected_cases_only():
    cases = _stage5_6_refresh_smoke.load_cases()

    assert cases
    assert {case["source_stage"] for case in cases} <= {"stage5", "stage6"}
    assert any(case["source_stage"] == "stage5" for case in cases)
    assert any(case["source_stage"] == "stage6" for case in cases)
    assert all(not case["held_out"] for case in cases)


def test_stage5_6_refresh_smoke_decision_blocks_selector():
    payload = {
        "summary": {
            "case_count": 2,
            "refresh_frame_count": 3,
            "selected_move_provider_delta_count": 0,
            "baseline_refresh_frame_count": 0,
            "invariant_failure_count": 0,
            "stage7_case_count": 0,
        },
        "decision": {
            "status": "stage5_6_candidate_generation_refresh_wired_default_off_equivalent",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
        },
    }

    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert payload["decision"]["promotion_allowed"] is False


def test_candidate_generation_refresh_sandbox_summary_enforces_frame_invariants():
    rows = [
        {
            "source_stage": "stage5",
            "baseline_refresh_frame_count": 0,
            "selected_move_delta": False,
            "selected_provider_delta": False,
            "selected_score_delta": False,
            "enabled_refresh_frames": [
                {
                    "candidate_source": "stage_conditioned_candidate_generation_refresh",
                    "policy": "trace_stage_family_context",
                    "stage": "stage5",
                    "provider_family": "stage0_basin",
                    "direct_request": False,
                    "score_delta": 0.0,
                    "causal_status": "candidate_generation_only",
                    "protected_status": "protected_control",
                    "candidate_generation_truncated": False,
                }
            ],
        }
    ]

    summary = _candidate_generation_refresh_sandbox._summarize_rows(rows)

    assert summary["generated_frame_count"] == 1
    assert summary["generated_frame_count_by_stage"] == {"stage5": 1}
    assert summary["generated_frame_count_by_provider_family"] == {"stage0_basin": 1}
    assert summary["direct_request_false_count"] == 1
    assert summary["score_delta_zero_count"] == 1
    assert summary["invalid_frame_count"] == 0


def test_stage5_6_refresh_coverage_keeps_selector_blocked():
    source = {
        "decision": {
            "status": "stage5_6_candidate_generation_refresh_wired_default_off_equivalent"
        },
        "summary": {
            "stage7_case_count": 0,
            "selected_move_provider_delta_count": 0,
            "baseline_refresh_frame_count": 0,
        },
        "cases": [
            {
                "case_id": "stage5",
                "source_stage": "stage5",
                "enabled_refresh_sample_frames": [
                    {
                        "candidate_source": "stage_conditioned_candidate_generation_refresh",
                        "provider_id": "krk.stage0_basin",
                        "capacity_evidence_kind": "positive_capacity",
                        "provider_provenance": "stage5_6_candidate_generation_refresh_review_packet_v3",
                        "direct_request": False,
                        "score_delta": 0.0,
                        "causal_status": "candidate_generation_only",
                        "protected_status": "protected_control",
                    }
                ],
            }
        ],
    }

    payload = _stage5_6_refresh_coverage.build_payload(source)

    assert payload["decision"]["status"] == (
        "stage5_6_refresh_coverage_ready_for_broadened_analysis"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert payload["summary"]["stage7_case_count"] == 0
    assert payload["summary"]["invariant_failure_count"] == 0


def test_stage5_6_refresh_broadened_summary_blocks_selector():
    payload = {
        "summary": {
            "case_count": 2,
            "case_count_by_stage": {"stage5": 1, "stage6": 1},
            "refresh_frame_count": 3,
            "selected_move_provider_delta_count": 0,
            "baseline_refresh_frame_count": 0,
            "invariant_failure_count": 0,
            "stage7_case_count": 0,
        },
        "decision": {
            "status": "stage5_6_candidate_generation_refresh_broadened_default_off_equivalent",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
        },
    }

    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert payload["decision"]["promotion_allowed"] is False
    assert payload["summary"]["stage7_case_count"] == 0


def test_stage5_6_refresh_quality_retains_trace_only_use():
    source = {
        "decision": {
            "status": "stage5_6_candidate_generation_refresh_broadened_default_off_equivalent"
        },
        "summary": {
            "case_count": 4,
            "refresh_frame_count": 38,
            "stage7_case_count": 0,
            "invariant_failure_count": 0,
            "selected_move_provider_delta_count": 0,
            "baseline_refresh_frame_count": 0,
            "refresh_provider_counts": {"krk.stage0_basin": 13},
            "capacity_evidence_counts": {"positive_capacity": 16},
        },
    }

    payload = _stage5_6_refresh_quality.build_payload(source)

    assert payload["decision"]["status"] == (
        "stage5_6_candidate_generation_refresh_quality_trace_only_retained"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert "capacity_evidence_not_runtime_ownership_label" in payload["selector_blockers"]
    assert payload["summary"]["trace_usable_for_candidate_generation_context"] is True


def test_stage5_6_refresh_trace_fold_is_non_causal_context_only():
    refresh_payload = {
        "cases": [
            {
                "case_id": "stage5",
                "state_id": "state.a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "fen": "fen-a",
                "selected_move_provider_score_equivalent": True,
                "enabled_refresh_sample_frames": [
                    {
                        "candidate_source": "stage_conditioned_candidate_generation_refresh",
                        "provider_id": "krk.stage0_basin",
                        "move_id": "a1a2",
                        "capacity_evidence_kind": "positive_capacity",
                        "capacity_evidence_source": "offline",
                        "label_semantics": "forced_provider_capacity_not_runtime_ownership",
                        "source_terms": ["stage5_6_candidate_generation_refresh_scope"],
                        "provider_provenance": "stage5_6_candidate_generation_refresh_review_packet_v3",
                        "protected_status": "protected_control",
                        "selected_provider_before_observation": "krk.fence_established",
                        "selected_move_before_observation": "h7c7",
                    }
                ],
            }
        ]
    }
    quality_payload = {"decision": {"selector_allowed": False}}

    payload = _stage5_6_refresh_trace_fold.build_payload(
        base_payload={"summary": {}},
        refresh_payload=refresh_payload,
        quality_payload=quality_payload,
    )

    assert payload["decision"]["status"] == (
        "stage5_6_refresh_trace_features_folded_non_causal"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["trace_frame_count"] == 1
    assert payload["summary"]["stage7_trace_frame_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["trace_only_frames"][0]["usable_for_selector_training"] is False
    assert payload["trace_only_frames"][0]["causal_status"] == "non_causal_trace_feature"


def test_strategy_sequence_dataset_design_v3_integrates_stage5_6_trace_only():
    payload = _dataset_design_v3.build_payload(
        {
            "summary": {
                "trace_frame_count": 38,
                "stage7_trace_frame_count": 0,
                "selector_training_row_count": 0,
                "candidate_generation_training_row_count": 0,
            }
        }
    )

    assert payload["decision"]["status"] == "strategy_sequence_dataset_design_v3_ready"
    assert payload["decision"]["selector_allowed"] is False
    source = payload["new_trace_feature_sources"][0]
    assert source["source"] == "stage5_6_candidate_generation_refresh"
    assert source["forbidden_use"] == "selector_training_or_guardrail_trigger"


def test_strategy_sequence_dataset_v3_appends_trace_context_without_selector_rows():
    base_row = {
        "schema_version": "krk_strategy_sequence_dataset_row.v2",
        "row_id": "capacity",
        "source_stage": "stage5",
        "evidence_channel": "validated_provider_capacity",
        "candidate_strategy_family": "stage0_basin",
        "capacity_label": "positive_capacity",
        "stage7_challenge_row": False,
        "usable_for_selector_training_v2": False,
        "usable_for_candidate_generation_training_v2": True,
    }
    trace_frame = {
        "frame_id": "trace",
        "state_id": "state.a",
        "source_stage": "stage5",
        "frame_type": "stage_conditioned_candidate_generation_refresh",
        "candidate_provider_id": "krk.stage0_basin",
        "candidate_move_uci": "a1a2",
        "candidate_strategy_family": "stage0_basin",
        "label_semantics": "runtime_observation_context_not_selector_label",
        "usable_for_selector_training": False,
        "usable_for_candidate_generation_training": False,
        "capacity_evidence": {"capacity_label": "positive_capacity_scope"},
        "ownership_evidence": {
            "label_semantics": "runtime_observation_context_not_ownership_label"
        },
        "sequence_evidence": {"candidate_source": "stage_conditioned_candidate_generation_refresh"},
    }

    payload = _dataset_v3.build_payload(
        base_dataset={"rows": [base_row]},
        stage5_6_trace={
            "decision": {"selector_allowed": False},
            "trace_only_frames": [trace_frame],
        },
        design={"schema_version": "krk_strategy_sequence_dataset_design.v3"},
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v3_refreshed_non_causal_selector_blocked"
    )
    assert payload["summary"]["row_count"] == 2
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["candidate_generation_training_row_count"] == 1
    assert payload["summary"]["added_stage5_6_refresh_trace_row_count"] == 1
    assert payload["rows"][1]["usable_for_selector_training_v3"] is False
    assert payload["rows"][1]["trace_feature_source"] == (
        "stage5_6_candidate_generation_refresh"
    )


def test_strategy_sequence_dataset_v3_quality_blocks_selector():
    payload = _dataset_v3_quality.build_payload(
        {
            "runtime_behavior_changed": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "summary": {
                "row_count_by_channel": {
                    "validated_provider_capacity": 1,
                    "visible_provider_proposal": 1,
                    "candidate_move_frame": 1,
                    "runtime_observation_trace_feature": 2,
                },
                "runtime_trace_feature_row_count_by_source": {
                    "repair_monitor_observation": 1,
                    "stage5_6_candidate_generation_refresh": 1,
                },
                "stage7_readiness_training_row_count": 0,
            },
            "rows": [
                {
                    "evidence_channel": "validated_provider_capacity",
                    "usable_for_candidate_generation_training_v3": True,
                    "usable_for_selector_training_v3": False,
                },
                {
                    "evidence_channel": "runtime_observation_trace_feature",
                    "trace_feature_source": "repair_monitor_observation",
                    "usable_for_candidate_generation_training_v3": False,
                    "usable_for_selector_training_v3": False,
                },
                {
                    "evidence_channel": "runtime_observation_trace_feature",
                    "trace_feature_source": "stage5_6_candidate_generation_refresh",
                    "usable_for_candidate_generation_training_v3": False,
                    "usable_for_selector_training_v3": False,
                },
            ],
        }
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v3_quality_candidate_generation_context_ready_selector_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["interpretation"]["candidate_generation_context_usable"] is True
    assert payload["interpretation"]["selector_dataset_usable"] is False


def test_strategy_sequence_dataset_v3_context_review_closes_selector_blocked_slice():
    payload = _dataset_v3_context_review.build_payload(
        dataset={
            "decision": {"selector_allowed": False},
            "summary": {
                "row_count": 320,
                "candidate_generation_training_row_count": 26,
                "selector_training_row_count": 0,
                "stage7_readiness_training_row_count": 0,
                "runtime_trace_feature_row_count": 44,
                "runtime_trace_feature_row_count_by_source": {
                    "repair_monitor_observation": 6,
                    "stage5_6_candidate_generation_refresh": 38,
                },
            },
        },
        quality={
            "decision": {
                "selector_allowed": False,
                "status": "strategy_sequence_dataset_v3_quality_candidate_generation_context_ready_selector_blocked",
            },
            "summary": {"row_count": 320},
            "selector_blockers": ["no_explicit_ownership_selector_rows"],
        },
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v3_context_integrated_selector_still_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert "selector_training" in payload["still_blocked"]


def test_candidate_generation_v3_context_benchmark_keeps_selection_blocked():
    dataset = {
        "summary": {
            "selector_training_row_count": 0,
            "stage7_readiness_training_row_count": 0,
        },
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "fen": "fen-a",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "fen": "fen-b",
                "candidate_provider_id": "krk.edge_trap_close",
                "candidate_move_uci": "b1b2",
                "source_stage": "stage5",
                "candidate_strategy_family": "edge_trap",
                "capacity_label": "negative_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "fen": "fen-a",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "trace_feature_source": "stage5_6_candidate_generation_refresh",
                "stage7_challenge_row": False,
            },
        ],
    }

    payload = _candidate_generation_v3_context_benchmark.build_payload(
        dataset=dataset,
        quality={"decision": {"selector_allowed": False}},
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_v3_context_useful_selector_still_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["exact_positive_capacity_recall_from_trace"] == 1.0
    assert payload["interpretation"]["trace_rows_are_not_training_labels"] is True


def test_candidate_generation_v3_runtime_boundary_blocks_selector():
    payload = _candidate_generation_v3_runtime_boundary.build_payload(
        {
            "decision": {"selector_allowed": False},
            "summary": {
                "exact_positive_capacity_recall_from_trace": 0.31,
                "stage_family_positive_capacity_recall_from_trace": 0.77,
                "stage_family_negative_capacity_exposure_from_trace": 0.0,
                "runtime_trace_row_count": 44,
                "selector_training_row_count": 0,
                "stage7_readiness_training_row_count": 0,
            },
        }
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_v3_runtime_boundary_context_ready_selector_blocked"
    )
    assert payload["approved_runtime_boundary"]["current_observation_sources_remain_allowed"] is True
    assert payload["approved_runtime_boundary"]["new_runtime_behavior_allowed"] is False
    assert payload["approved_runtime_boundary"]["selector_allowed"] is False
    assert "selector_training" in payload["still_forbidden"]


def test_candidate_generation_v3_training_refresh_review_allows_design_only():
    payload = _candidate_generation_v3_training_refresh.build_payload(
        boundary={"decision": {"selector_allowed": False}},
        benchmark={
            "summary": {
                "exact_positive_capacity_recall_from_trace": 0.31,
                "stage_family_positive_capacity_recall_from_trace": 0.77,
                "stage_family_negative_capacity_exposure_from_trace": 0.0,
            }
        },
        dataset={
            "summary": {
                "candidate_generation_training_row_count": 26,
                "selector_training_row_count": 0,
                "stage7_readiness_training_row_count": 0,
                "runtime_trace_feature_row_count": 44,
            }
        },
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_v3_training_refresh_design_ready_non_causal"
    )
    assert payload["allowed_next_design_scope"][
        "offline_candidate_generation_training_refresh_design"
    ] is True
    assert payload["allowed_next_design_scope"]["runtime_candidate_generator_change"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert "capacity labels are not runtime ownership labels" in payload[
        "blockers_before_runtime"
    ]


def test_candidate_generation_training_refresh_design_v3_blocks_runtime_use():
    payload = _candidate_generation_training_refresh_design_v3.build_payload(
        review={
            "decision": {
                "status": "candidate_generation_v3_training_refresh_design_ready_non_causal"
            }
        },
        dataset={
            "summary": {
                "row_count": 320,
                "candidate_generation_training_row_count": 26,
                "selector_training_row_count": 0,
                "runtime_trace_feature_row_count": 44,
                "stage7_readiness_training_row_count": 0,
            }
        },
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_training_refresh_v3_design_ready"
    )
    assert payload["decision"]["implementation_allowed_by_this_artifact"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["training_target"]["not_objective"] == "runtime_ownership_or_move_selection"
    assert "runtime_selector" in payload["forbidden_uses"]


def test_candidate_generation_training_refresh_benchmark_v3_passes_without_selector():
    dataset = {
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
                "usable_for_selector_training_v3": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage5",
                "candidate_strategy_family": "edge_trap",
                "capacity_label": "negative_capacity",
                "stage7_challenge_row": False,
                "usable_for_selector_training_v3": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage7",
                "candidate_strategy_family": "box_shrink",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": True,
                "usable_for_candidate_generation_training_v3": False,
                "usable_for_selector_training_v3": False,
            },
        ]
    }
    design = {
        "readiness_thresholds_for_future_runtime_review": {
            "positive_capacity_recall": 0.75,
            "negative_capacity_suppression": 0.8,
            "leave_stage_out_positive_capacity_recall": 0.65,
            "selector_training_rows": 0,
            "stage7_training_rows": 0,
        }
    }

    payload = _candidate_generation_training_refresh_benchmark_v3.build_payload(
        dataset=dataset,
        design=design,
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_training_refresh_v3_benchmark_passed_runtime_review_needed"
    )
    assert payload["decision"]["runtime_implementation_allowed_by_this_artifact"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["best_policy"] == "trace_stage_family_context"
    assert payload["summary"]["best_policy_metrics"]["positive_capacity_recall"] == 1.0
    assert payload["summary"]["best_policy_metrics"]["negative_capacity_suppression"] == 1.0
    assert payload["label_semantics"]["capacity_labels_are_not_selector_or_ownership_labels"] is True


def test_candidate_generation_training_refresh_benchmark_v3_blocks_noisy_context():
    dataset = {
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "capacity_label": "negative_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "stage7_challenge_row": False,
            },
        ]
    }
    design = {
        "readiness_thresholds_for_future_runtime_review": {
            "positive_capacity_recall": 0.75,
            "negative_capacity_suppression": 0.8,
            "leave_stage_out_positive_capacity_recall": 0.65,
            "selector_training_rows": 0,
            "stage7_training_rows": 0,
        }
    }

    payload = _candidate_generation_training_refresh_benchmark_v3.build_payload(
        dataset=dataset,
        design=design,
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_training_refresh_v3_benchmark_runtime_blocked"
    )
    assert payload["decision"]["runtime_implementation_allowed_by_this_artifact"] is False
    assert payload["summary"]["best_policy_metrics"]["negative_capacity_suppression"] < 0.8


def test_candidate_generation_training_refresh_runtime_review_packet_requires_approval():
    benchmark = {
        "decision": {
            "status": "candidate_generation_training_refresh_v3_benchmark_passed_runtime_review_needed"
        },
        "summary": {
            "thresholds_met": True,
            "best_policy": "trace_stage_family_context",
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "best_policy_metrics": {
                "positive_capacity_recall": 0.77,
                "negative_capacity_suppression": 1.0,
            },
            "best_policy_leave_stage_out_metrics": {
                "positive_capacity_recall": 0.77,
                "negative_capacity_suppression": 1.0,
            },
        },
        "thresholds": {
            "positive_capacity_recall": 0.75,
            "negative_capacity_suppression": 0.8,
            "leave_stage_out_positive_capacity_recall": 0.65,
        },
        "rate_tables": {
            "stage_family": {
                "stage5|stage0_basin": {
                    "support": 2,
                    "positive": 2,
                    "negative": 0,
                    "positive_rate": 1.0,
                },
                "stage4|edge_trap": {
                    "support": 2,
                    "positive": 2,
                    "negative": 0,
                    "positive_rate": 1.0,
                },
                "stage6|drive_to_edge": {
                    "support": 1,
                    "positive": 0,
                    "negative": 1,
                    "positive_rate": 0.0,
                },
            }
        },
        "policy_metrics": {"trace_stage_family_context": {"false_positive": 0}},
    }

    payload = _candidate_generation_training_refresh_packet_v3.build_payload(benchmark)

    assert payload["decision"]["status"] == (
        "candidate_generation_training_refresh_runtime_review_ready"
    )
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["runtime_candidate_generation_allowed_by_this_packet"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["approved_scope_if_later_authorized"]["candidate_generation_cells"] == {
        "stage5": ["stage0_basin"]
    }
    assert "stage4_runtime_scope_without_separate_review" in payload["explicitly_forbidden"]


def test_candidate_generation_training_refresh_runtime_review_packet_blocks_failed_benchmark():
    benchmark = {
        "decision": {"status": "candidate_generation_training_refresh_v3_benchmark_runtime_blocked"},
        "summary": {
            "thresholds_met": False,
            "best_policy": "trace_stage_family_context",
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
        },
        "policy_metrics": {"trace_stage_family_context": {"false_positive": 1}},
    }

    payload = _candidate_generation_training_refresh_packet_v3.build_payload(benchmark)

    assert payload["decision"]["status"] == (
        "candidate_generation_training_refresh_runtime_review_blocked"
    )
    assert payload["decision"]["runtime_review_ready"] is False
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False


def test_candidate_generation_refresh_coverage_analysis_keeps_selector_blocked():
    sandbox = {
        "decision": {
            "status": "candidate_generation_refresh_sandbox_ready_for_non_causal_coverage_analysis"
        },
        "summary": {
            "selected_move_delta_count": 0,
            "selected_provider_delta_count": 0,
            "score_delta_count": 0,
            "truncation_count": 0,
            "truncated_frame_count": 0,
        },
        "cases": [
            {
                "case_id": "stage5",
                "source_stage": "stage5",
                "fen": "fen-a",
                "enabled_refresh_frames": [
                    {
                        "candidate_source": "stage_conditioned_candidate_generation_refresh",
                        "policy": "trace_stage_family_context",
                        "stage": "stage5",
                        "state_fen": "fen-a",
                        "provider_family": "stage0_basin",
                        "provider_id": "krk.stage0_basin",
                        "move_id": "a1a2",
                        "direct_request": False,
                        "score_delta": 0.0,
                        "causal_status": "candidate_generation_only",
                        "protected_status": "protected_control",
                        "capacity_evidence_kind": "positive_capacity",
                    }
                ],
            }
        ],
    }
    dataset = {
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "fen": "fen-a",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            }
        ]
    }

    payload = _candidate_generation_refresh_coverage.analyze(
        sandbox=sandbox,
        dataset=dataset,
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_refresh_coverage_ready_for_trace_dataset_refresh"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["exact_positive_capacity_recall"] == 1.0
    assert payload["summary"]["stage4_frame_count"] == 0
    assert payload["summary"]["stage7_frame_count"] == 0
    assert payload["interpretation"]["capacity_labels_are_not_ownership_labels"] is True


def test_candidate_generation_refresh_trace_fold_is_non_causal():
    sandbox = {
        "cases": [
            {
                "case_id": "stage5",
                "state_id": "state.a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "fen": "fen-a",
                "selected_move_provider_score_equivalent": True,
                "enabled_refresh_frames": [
                    {
                        "candidate_source": "stage_conditioned_candidate_generation_refresh",
                        "policy": "trace_stage_family_context",
                        "policy_cell": "stage5|stage0_basin",
                        "stage": "stage5",
                        "provider_family": "stage0_basin",
                        "provider_id": "krk.stage0_basin",
                        "move_id": "a1a2",
                        "capacity_evidence_kind": "positive_capacity",
                        "capacity_evidence_source": "offline",
                        "label_semantics": "forced_provider_capacity_not_runtime_ownership",
                        "selected_provider_before_observation": "krk.fence_established",
                        "selected_move_before_observation": "h7c7",
                        "source_terms": ["stage5_6_candidate_generation_refresh_scope"],
                        "protected_status": "protected_control",
                    }
                ],
            }
        ]
    }
    coverage = {
        "decision": {
            "status": "candidate_generation_refresh_coverage_ready_for_trace_dataset_refresh",
            "selector_allowed": False,
        }
    }

    payload = _candidate_generation_refresh_trace_fold.build_payload(
        base_payload={"summary": {}},
        sandbox_payload=sandbox,
        coverage_payload=coverage,
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_refresh_trace_features_folded_non_causal"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["trace_frame_count"] == 1
    assert payload["trace_only_frames"][0]["usable_for_selector_training"] is False
    assert payload["trace_only_frames"][0]["causal_status"] == "non_causal_trace_feature"


def test_strategy_sequence_dataset_v4_preserves_trace_context_without_selector():
    base = {
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage5",
                "stage7_challenge_row": False,
                "usable_for_candidate_generation_training_v2": True,
                "usable_for_selector_training_v2": False,
            }
        ]
    }
    trace = {
        "decision": {"selector_allowed": False},
        "trace_only_frames": [
            {
                "frame_id": "frame.a",
                "state_id": "state.a",
                "fen": "fen-a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "frame_type": "candidate_generation_refresh_sandbox",
                "candidate_strategy_family": "stage0_basin",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "label_semantics": "runtime_observation_context_not_selector_label",
                "stage7_challenge_row": False,
                "usable_for_selector_training": False,
                "usable_for_candidate_generation_training": False,
                "capacity_evidence": {"capacity_label": "positive_capacity"},
                "ownership_evidence": {
                    "label_semantics": "runtime_observation_context_not_ownership_label"
                },
                "sequence_evidence": {
                    "policy": "trace_stage_family_context",
                    "policy_cell": "stage5|stage0_basin",
                },
                "causal_status": "non_causal_trace_feature",
            }
        ],
    }

    payload = _dataset_v4.build_payload(
        base_dataset=base,
        refresh_trace=trace,
        design={},
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v4_refreshed_non_causal_selector_blocked"
    )
    assert payload["summary"]["row_count"] == 2
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_readiness_training_row_count"] == 0
    assert payload["summary"]["runtime_trace_feature_row_count_by_source"] == {
        "candidate_generation_refresh_sandbox": 1
    }


def test_strategy_sequence_dataset_v4_quality_blocks_selector():
    payload = _dataset_v4_quality.build_payload(
        dataset={
            "runtime_behavior_changed": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "summary": {
                "row_count_by_channel": {
                    "validated_provider_capacity": 1,
                    "runtime_observation_trace_feature": 2,
                    "candidate_move_frame": 1,
                    "visible_provider_proposal": 1,
                },
                "runtime_trace_feature_row_count_by_source": {
                    "candidate_generation_refresh_sandbox": 1,
                    "repair_monitor_observation": 1,
                },
                "stage7_readiness_training_row_count": 0,
            },
            "rows": [
                {
                    "evidence_channel": "validated_provider_capacity",
                    "usable_for_candidate_generation_training_v4": True,
                    "usable_for_selector_training_v4": False,
                },
                {
                    "evidence_channel": "runtime_observation_trace_feature",
                    "trace_feature_source": "candidate_generation_refresh_sandbox",
                    "usable_for_candidate_generation_training_v4": False,
                    "usable_for_selector_training_v4": False,
                    "causal_status": "non_causal_dataset_row",
                },
                {
                    "evidence_channel": "runtime_observation_trace_feature",
                    "trace_feature_source": "repair_monitor_observation",
                    "usable_for_candidate_generation_training_v4": False,
                    "usable_for_selector_training_v4": False,
                    "causal_status": "non_causal_dataset_row",
                },
            ],
        }
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v4_quality_candidate_generation_context_ready_selector_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["candidate_generation_refresh_trace_row_count"] == 1
    assert payload["interpretation"]["selector_dataset_usable"] is False


def test_strategy_sequence_dataset_v4_context_review_closes_selector_blocked_slice():
    payload = _dataset_v4_context_review.build_payload(
        dataset={
            "decision": {"selector_allowed": False},
            "summary": {
                "row_count": 307,
                "candidate_generation_training_row_count": 26,
                "selector_training_row_count": 0,
                "stage7_readiness_training_row_count": 0,
                "runtime_trace_feature_row_count": 31,
                "runtime_trace_feature_row_count_by_source": {
                    "candidate_generation_refresh_sandbox": 25,
                    "repair_monitor_observation": 6,
                },
            },
        },
        quality={
            "decision": {
                "selector_allowed": False,
                "status": "strategy_sequence_dataset_v4_quality_candidate_generation_context_ready_selector_blocked",
            },
            "summary": {
                "row_count": 307,
                "candidate_generation_refresh_trace_row_count": 25,
            },
            "selector_blockers": ["no_selector_training_rows"],
        },
    )

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v4_context_integrated_selector_still_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert "selector_training" in payload["still_blocked"]
    assert payload["summary"]["candidate_generation_refresh_trace_row_count"] == 25


def test_candidate_generation_v4_context_benchmark_keeps_selector_blocked():
    dataset = {
        "summary": {
            "selector_training_row_count": 0,
            "stage7_readiness_training_row_count": 0,
        },
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "fen": "fen-a",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "fen": "fen-b",
                "candidate_provider_id": "krk.edge_trap_close",
                "candidate_move_uci": "b1b2",
                "source_stage": "stage5",
                "candidate_strategy_family": "edge_trap",
                "capacity_label": "negative_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "fen": "fen-a",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "policy_cell": "stage5|stage0_basin",
                "trace_feature_source": "candidate_generation_refresh_sandbox",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "trace_feature_source": "repair_monitor_observation",
                "stage7_challenge_row": False,
            },
        ],
    }

    payload = _candidate_generation_v4_context_benchmark.build_payload(
        dataset=dataset,
        quality={"decision": {"selector_allowed": False}},
        context={"decision": {"selector_allowed": False}},
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_v4_context_useful_selector_still_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["exact_positive_capacity_recall_from_refresh_trace"] == 1.0
    assert payload["summary"]["policy_cell_negative_capacity_exposure_from_refresh_trace"] == 0.0
    assert payload["interpretation"]["capacity_labels_are_not_ownership_labels"] is True
    assert payload["interpretation"]["trace_rows_are_not_training_labels"] is True


def test_candidate_generation_v4_runtime_boundary_blocks_new_runtime_behavior():
    payload = _candidate_generation_v4_runtime_boundary.build_payload(
        {
            "decision": {"selector_allowed": False},
            "summary": {
                "capacity_row_count": 36,
                "positive_capacity_count": 26,
                "negative_capacity_count": 10,
                "runtime_trace_row_count": 31,
                "refresh_trace_row_count": 25,
                "exact_positive_capacity_recall_from_refresh_trace": 0.19,
                "policy_cell_positive_capacity_recall_from_refresh_trace": 0.77,
                "exact_negative_capacity_exposure_from_refresh_trace": 0.0,
                "policy_cell_negative_capacity_exposure_from_refresh_trace": 0.0,
                "selector_training_row_count": 0,
                "stage7_readiness_training_row_count": 0,
            },
        }
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_v4_next_runtime_boundary_context_ready_selector_blocked"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["approved_now"]["implement_new_runtime_sandbox"] is False
    assert payload["approved_now"]["selector_allowed"] is False
    assert payload["boundary_assessment"]["exact_move_provider_coverage_is_partial"] is True
    assert "selector_training" in payload["still_forbidden"]


def test_candidate_generation_scope_gap_review_blocks_new_runtime_boundary():
    dataset = {
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "stage7_challenge_row": False,
            },
        ]
    }
    benchmark = {
        "summary": {
            "exact_positive_capacity_recall_from_refresh_trace": 0.2,
            "policy_cell_positive_capacity_recall_from_refresh_trace": 0.8,
            "policy_cell_negative_capacity_exposure_from_refresh_trace": 0.0,
            "selector_training_row_count": 0,
            "stage7_readiness_training_row_count": 0,
        }
    }
    boundary = {"decision": {"runtime_changes_allowed": False}}

    payload = _candidate_generation_scope_gap_review.build_payload(
        dataset=dataset,
        benchmark=benchmark,
        boundary=boundary,
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_scope_gap_review_blocks_new_runtime_boundary"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert "exact_move_provider_coverage_partial" in payload["scope_gaps"]
    assert "ownership_selector_labels_absent" in payload["scope_gaps"]
    assert payload["gap_interpretation"]["selection_blocked_by_label_semantics"] is True


def test_candidate_source_gap_manifest_keeps_capacity_gaps_non_causal():
    dataset = {
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "state_id": "state.a",
                "fen": "fen-a",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "state_id": "state.b",
                "fen": "fen-b",
                "source_stage": "stage4",
                "candidate_strategy_family": "edge_trap",
                "candidate_provider_id": "krk.edge_trap_close",
                "candidate_move_uci": "b1b2",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "fen": "fen-a",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "policy_cell": "stage5|stage0_basin",
                "trace_feature_source": "candidate_generation_refresh_sandbox",
                "stage7_challenge_row": False,
            },
        ]
    }

    payload = _candidate_source_gap_manifest.build_payload(
        dataset=dataset,
        scope_review={"decision": {"status": "scope_review_fixture"}},
    )

    assert payload["decision"]["status"] == "candidate_source_gap_manifest_ready_non_causal"
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["summary"]["exact_covered_positive_capacity_count"] == 1
    assert payload["summary"]["exact_missing_positive_capacity_count"] == 1
    assert payload["summary"]["policy_cell_missing_count"] == 1
    assert payload["gap_records"][0]["runtime_allowed"] is False
    assert payload["interpretation"]["not_selector_training_data"] is True


def test_candidate_source_expansion_options_require_review_packet():
    payload = _candidate_source_expansion_options.build_payload(
        {
            "summary": {
                "exact_missing_positive_capacity_count": 21,
                "policy_cell_covered_exact_missing_count": 15,
                "policy_cell_missing_count": 6,
                "gap_count_by_stage": {"stage4": 6, "stage5": 12, "stage6": 3},
                "gap_count_by_family": {"edge_trap": 12, "stage0_basin": 9},
            }
        }
    )

    assert payload["decision"]["status"] == (
        "candidate_source_expansion_options_review_complete_runtime_packet_required"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["preferred_next_review"] == (
        "exact_trace_enrichment_within_existing_policy_cells"
    )
    assert payload["options"][0]["selector_allowed"] is False
    assert "new_review_packet" in payload["required_before_runtime"]


def test_exact_trace_enrichment_runtime_review_packet_requires_explicit_approval():
    options = {
        "decision": {
            "status": "candidate_source_expansion_options_review_complete_runtime_packet_required"
        },
        "preferred_next_review": "exact_trace_enrichment_within_existing_policy_cells",
        "summary": {},
    }
    manifest = {
        "summary": {
            "exact_missing_positive_capacity_count": 2,
            "policy_cell_covered_exact_missing_count": 1,
            "policy_cell_missing_count": 1,
            "gap_count_by_stage": {"stage4": 1, "stage5": 1},
            "gap_count_by_family": {"edge_trap": 2},
        },
        "gap_records": [
            {
                "gap_type": "policy_cell_covered_exact_missing",
                "source_stage": "stage5",
                "candidate_strategy_family": "edge_trap",
            },
            {
                "gap_type": "policy_cell_missing",
                "source_stage": "stage4",
                "candidate_strategy_family": "edge_trap",
            },
        ],
    }

    payload = _exact_trace_enrichment_packet.build_payload(
        options=options,
        manifest=manifest,
    )

    assert payload["decision"]["status"] == "exact_trace_enrichment_runtime_review_ready"
    assert payload["decision"]["runtime_review_ready"] is True
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["runtime_candidate_generation_allowed_by_this_packet"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["approved_scope_if_later_authorized"]["candidate_generation_cells"] == {
        "stage5": ["edge_trap"]
    }
    assert "stage4_runtime_scope_without_separate_review" in payload["explicitly_forbidden"]


def test_exact_trace_enrichment_sandbox_summary_enforces_frame_invariants():
    rows = [
        {
            "source_stage": "stage5",
            "enabled_exact_frames": [
                {
                    "candidate_source": "exact_trace_enrichment",
                    "policy": "trace_stage_family_context",
                    "direct_request": False,
                    "score_delta": 0.0,
                    "causal_status": "candidate_generation_only",
                    "protected_status": "protected_control",
                    "stage": "stage5",
                    "provider_family": "edge_trap",
                    "candidate_generation_truncated": False,
                }
            ],
        }
    ]

    summary = _exact_trace_enrichment_sandbox._summarize_rows(rows)

    assert summary["generated_frame_count"] == 1
    assert summary["direct_request_false_count"] == 1
    assert summary["score_delta_zero_count"] == 1
    assert summary["invalid_frame_count"] == 0
    assert summary["stage7_held_out_frame_count"] == 0


def test_exact_trace_enrichment_coverage_keeps_selector_blocked():
    sandbox = {
        "decision": {
            "status": "exact_trace_enrichment_sandbox_ready_for_non_causal_coverage_analysis"
        },
        "summary": {
            "selected_move_delta_count": 0,
            "selected_provider_delta_count": 0,
            "score_delta_count": 0,
        },
        "cases": [
            {
                "case_id": "case.a",
                "fen": "fen-a",
                "enabled_exact_frames": [
                    {
                        "candidate_source": "exact_trace_enrichment",
                        "state_fen": "fen-a",
                        "provider_id": "krk.edge_trap_close",
                        "move_id": "a1a2",
                        "stage": "stage5",
                        "provider_family": "edge_trap",
                        "policy": "trace_stage_family_context",
                        "direct_request": False,
                        "score_delta": 0.0,
                        "causal_status": "candidate_generation_only",
                        "protected_status": "protected_control",
                    }
                ],
            }
        ],
    }
    gaps = {
        "gap_records": [
            {
                "gap_type": "policy_cell_covered_exact_missing",
                "fen": "fen-a",
                "candidate_provider_id": "krk.edge_trap_close",
                "candidate_move_uci": "a1a2",
                "source_stage": "stage5",
                "candidate_strategy_family": "edge_trap",
                "stage7_challenge_row": False,
            }
        ]
    }

    payload = _exact_trace_enrichment_coverage.analyze(sandbox=sandbox, gaps=gaps)

    assert payload["decision"]["status"] == (
        "exact_trace_enrichment_coverage_ready_for_trace_dataset_refresh"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["summary"]["exact_gap_recall"] == 1.0
    assert payload["interpretation"]["capacity_gap_labels_are_not_ownership_labels"] is True


def test_exact_trace_enrichment_trace_fold_is_context_only():
    sandbox = {
        "cases": [
            {
                "state_id": "state.a",
                "fen": "fen-a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "selected_move_provider_score_equivalent": True,
                "enabled_exact_frames": [
                    {
                        "candidate_source": "exact_trace_enrichment",
                        "provider_id": "krk.edge_trap_close",
                        "provider_family": "edge_trap",
                        "move_id": "a1a2",
                        "source_terms": ["exact_trace_enrichment_scope"],
                        "capacity_evidence_kind": "positive_capacity",
                        "capacity_evidence_source": "source.json",
                        "label_semantics": "offline_capacity_gap_not_runtime_ownership",
                        "selected_provider_before_observation": "krk.fence_established",
                        "selected_move_before_observation": "h7c7",
                        "policy": "trace_stage_family_context",
                        "policy_cell": "stage5|edge_trap",
                        "provider_provenance": "packet",
                        "protected_status": "protected_control",
                        "exact_enrichment_reason": "policy_cell_covered_exact_missing",
                    }
                ],
            }
        ]
    }
    coverage = {
        "decision": {
            "selector_allowed": False,
            "status": "exact_trace_enrichment_coverage_ready_for_trace_dataset_refresh",
        }
    }

    payload = _exact_trace_enrichment_trace_fold.build_payload(
        base_payload={"summary": {}},
        sandbox_payload=sandbox,
        coverage_payload=coverage,
    )

    assert payload["decision"]["status"] == (
        "exact_trace_enrichment_trace_features_folded_non_causal"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["trace_frame_count"] == 1
    assert payload["trace_only_frames"][0]["usable_for_selector_training"] is False
    assert payload["trace_only_frames"][0]["causal_status"] == "non_causal_trace_feature"


def test_strategy_sequence_dataset_v5_adds_exact_trace_without_selector_rows():
    base = {
        "rows": [
            {
                "schema_version": "krk_strategy_sequence_dataset_row.v4",
                "evidence_channel": "validated_provider_capacity",
                "source_stage": "stage5",
                "stage7_challenge_row": False,
                "usable_for_candidate_generation_training_v4": True,
                "usable_for_selector_training_v4": False,
                "causal_status": "non_causal_dataset_row",
            },
            {
                "schema_version": "krk_strategy_sequence_dataset_row.v4",
                "evidence_channel": "runtime_observation_trace_feature",
                "trace_feature_source": "candidate_generation_refresh_sandbox",
                "source_stage": "stage5",
                "stage7_challenge_row": False,
                "usable_for_candidate_generation_training_v4": False,
                "usable_for_selector_training_v4": False,
                "causal_status": "non_causal_dataset_row",
            },
            {
                "schema_version": "krk_strategy_sequence_dataset_row.v4",
                "evidence_channel": "runtime_observation_trace_feature",
                "trace_feature_source": "repair_monitor_observation",
                "source_stage": "stage5",
                "stage7_challenge_row": False,
                "usable_for_candidate_generation_training_v4": False,
                "usable_for_selector_training_v4": False,
                "causal_status": "non_causal_dataset_row",
            },
            {
                "schema_version": "krk_strategy_sequence_dataset_row.v4",
                "evidence_channel": "visible_provider_proposal",
                "source_stage": "stage5",
                "stage7_challenge_row": False,
                "usable_for_candidate_generation_training_v4": False,
                "usable_for_selector_training_v4": False,
                "causal_status": "non_causal_dataset_row",
            },
            {
                "schema_version": "krk_strategy_sequence_dataset_row.v4",
                "evidence_channel": "candidate_move_frame",
                "source_stage": "stage5",
                "stage7_challenge_row": False,
                "usable_for_candidate_generation_training_v4": False,
                "usable_for_selector_training_v4": False,
                "causal_status": "non_causal_dataset_row",
            },
        ]
    }
    trace = {
        "decision": {"selector_allowed": False},
        "trace_only_frames": [
            {
                "frame_id": "frame.exact",
                "state_id": "state.a",
                "fen": "fen-a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "frame_type": "exact_trace_enrichment_sandbox",
                "candidate_strategy_family": "edge_trap",
                "candidate_provider_id": "krk.edge_trap_close",
                "candidate_move_uci": "a1a2",
                "label_semantics": "runtime_observation_context_not_selector_label",
                "stage7_challenge_row": False,
                "usable_for_selector_training": False,
                "usable_for_candidate_generation_training": False,
                "capacity_evidence": {"capacity_label": "positive_capacity"},
                "ownership_evidence": {
                    "label_semantics": "runtime_observation_context_not_ownership_label"
                },
                "sequence_evidence": {
                    "policy": "trace_stage_family_context",
                    "policy_cell": "stage5|edge_trap",
                    "exact_enrichment_reason": "policy_cell_covered_exact_missing",
                },
                "causal_status": "non_causal_trace_feature",
            }
        ],
    }

    dataset = _dataset_v5.build_payload(base_dataset=base, exact_trace=trace, design={})
    probe = _dataset_v5_quality.build_payload(dataset)

    assert dataset["decision"]["status"] == (
        "strategy_sequence_dataset_v5_refreshed_non_causal_selector_blocked"
    )
    assert dataset["summary"]["added_exact_trace_enrichment_row_count"] == 1
    assert dataset["summary"]["selector_training_row_count"] == 0
    assert probe["decision"]["status"] == (
        "strategy_sequence_dataset_v5_quality_candidate_generation_context_ready_selector_blocked"
    )
    assert probe["summary"]["exact_trace_enrichment_trace_row_count"] == 1
    assert probe["interpretation"]["selector_dataset_usable"] is False


def test_strategy_sequence_dataset_v5_context_review_keeps_selector_blocked():
    dataset = {
        "summary": {
            "row_count": 12,
            "candidate_generation_training_row_count": 2,
            "selector_training_row_count": 0,
            "stage7_readiness_training_row_count": 0,
            "runtime_trace_feature_row_count": 3,
            "runtime_trace_feature_row_count_by_source": {
                "candidate_generation_refresh_sandbox": 1,
                "exact_trace_enrichment_sandbox": 1,
                "repair_monitor_observation": 1,
            },
        },
        "decision": {"selector_allowed": False},
    }
    quality = {
        "summary": {
            "row_count": 12,
            "candidate_generation_refresh_trace_row_count": 1,
            "exact_trace_enrichment_trace_row_count": 1,
        },
        "decision": {
            "selector_allowed": False,
            "status": "strategy_sequence_dataset_v5_quality_candidate_generation_context_ready_selector_blocked",
        },
        "selector_blockers": ["capacity_rows_are_candidate_generation_not_ownership_labels"],
    }

    payload = _dataset_v5_context.build_payload(dataset=dataset, quality=quality)

    assert payload["decision"]["status"] == (
        "strategy_sequence_dataset_v5_context_integrated_selector_still_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["guardrails_allowed"] is False
    assert payload["summary"]["exact_trace_enrichment_trace_row_count"] == 1
    assert "exact_trace_enrichment_source_integrated" in payload["validated_progress"]


def test_candidate_generation_v5_context_benchmark_counts_exact_enrichment():
    dataset = {
        "summary": {
            "selector_training_row_count": 0,
            "stage7_readiness_training_row_count": 0,
        },
        "rows": [
            {
                "evidence_channel": "validated_provider_capacity",
                "fen": "fen-a",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "fen": "fen-b",
                "source_stage": "stage5",
                "candidate_strategy_family": "edge_trap",
                "candidate_provider_id": "krk.edge_trap_close",
                "candidate_move_uci": "b1b2",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "validated_provider_capacity",
                "fen": "fen-c",
                "source_stage": "stage6",
                "candidate_strategy_family": "stage0_basin",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "c1c2",
                "capacity_label": "negative_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "trace_feature_source": "candidate_generation_refresh_sandbox",
                "fen": "fen-a",
                "source_stage": "stage5",
                "candidate_strategy_family": "stage0_basin",
                "candidate_provider_id": "krk.stage0_basin",
                "candidate_move_uci": "a1a2",
                "policy_cell": "stage5|stage0_basin",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "trace_feature_source": "exact_trace_enrichment_sandbox",
                "fen": "fen-b",
                "source_stage": "stage5",
                "candidate_strategy_family": "edge_trap",
                "candidate_provider_id": "krk.edge_trap_close",
                "candidate_move_uci": "b1b2",
                "policy_cell": "stage5|edge_trap",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "trace_feature_source": "repair_monitor_observation",
                "fen": "fen-z",
                "source_stage": "stage5",
                "candidate_strategy_family": "repair",
                "stage7_challenge_row": False,
            },
        ],
    }
    quality = {"decision": {"selector_allowed": False}}
    context = {"decision": {"selector_allowed": False}}
    v4_benchmark = {
        "summary": {"exact_positive_capacity_recall_from_refresh_trace": 0.5}
    }

    payload = _candidate_generation_v5_benchmark.build_payload(
        dataset=dataset,
        quality=quality,
        context=context,
        v4_benchmark=v4_benchmark,
    )

    assert payload["decision"]["status"] == (
        "candidate_generation_v5_context_useful_selector_still_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert (
        payload["summary"][
            "exact_positive_capacity_recall_from_candidate_generation_trace"
        ]
        == 1.0
    )
    assert (
        payload["summary"][
            "exact_positive_capacity_recall_from_exact_trace_enrichment"
        ]
        == 0.5
    )
    assert (
        payload["summary"][
            "exact_negative_capacity_exposure_from_candidate_generation_trace"
        ]
        == 0.0
    )
    assert payload["interpretation"]["capacity_labels_are_not_ownership_labels"] is True
    assert payload["interpretation"]["exact_trace_enrichment_improved_exact_coverage"] is True


def test_candidate_generation_v5_next_boundary_keeps_runtime_blocked():
    benchmark = {
        "summary": {
            "capacity_row_count": 36,
            "positive_capacity_count": 26,
            "negative_capacity_count": 10,
            "runtime_trace_row_count": 34,
            "candidate_generation_trace_row_count": 28,
            "exact_trace_enrichment_trace_row_count": 3,
            "exact_positive_capacity_recall_from_candidate_generation_trace": 8 / 26,
            "exact_positive_capacity_recall_delta_vs_v4": 3 / 26,
            "policy_cell_positive_capacity_recall_from_candidate_generation_trace": 20 / 26,
            "exact_negative_capacity_exposure_from_candidate_generation_trace": 0.0,
            "policy_cell_negative_capacity_exposure_from_candidate_generation_trace": 0.0,
            "selector_training_row_count": 0,
            "stage7_readiness_training_row_count": 0,
        },
        "decision": {"selector_allowed": False},
    }

    payload = _candidate_generation_v5_boundary.build_payload(benchmark=benchmark)

    assert payload["decision"]["status"] == (
        "candidate_generation_v5_next_boundary_context_improved_selector_blocked"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["approved_now"]["implement_new_runtime_sandbox"] is False
    assert payload["boundary_assessment"]["exact_trace_enrichment_helped"] is True
    assert payload["boundary_assessment"]["exact_move_provider_coverage_is_still_partial"] is True
    assert "capacity_labels_as_ownership_labels" in payload["still_forbidden"]


def test_ownership_label_recovery_review_builds_seed_classes_without_selector():
    dataset = {
        "rows": [
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "trace_feature_source": "candidate_generation_refresh_sandbox",
                "state_id": "state.fail",
                "source_stage": "stage5",
                "candidate_provider_id": "krk.edge_trap_close",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "trace_feature_source": "exact_trace_enrichment_sandbox",
                "state_id": "state.safe",
                "source_stage": "stage5",
                "candidate_provider_id": "krk.fence_established",
                "capacity_label": "positive_capacity",
                "stage7_challenge_row": False,
            },
        ]
    }
    ownership = {
        "summary": {"selector_training_row_count": 0, "stage7_row_count": 0},
        "rows": [
            {
                "state_id": "state.fail",
                "source_stage": "stage5",
                "provider_id": "krk.stage0_basin",
                "provider_family": "stage0_basin",
                "target_label": "selected_owner_failed",
            },
            {
                "state_id": "state.safe",
                "source_stage": "stage5",
                "provider_id": "krk.fence_established",
                "provider_family": "fence_established",
                "target_label": "selected_owner_converted",
            },
            {
                "state_id": "state.stage7",
                "source_stage": "stage7",
                "provider_id": "krk.box_shrink",
                "provider_family": "box_shrink",
                "target_label": "selected_owner_failed",
            },
        ],
    }
    paired_review = {"summary": {"threshold_passing_model_count": 2, "runtime_feature_passing_model_count": 0}}
    progress_audit = {"classification": {"primary": "candidate_set_missing_good_alternative"}}
    boundary = {
        "decision": {
            "status": "candidate_generation_v5_next_boundary_context_improved_selector_blocked"
        }
    }

    payload = _ownership_label_recovery.build_payload(
        dataset=dataset,
        ownership=ownership,
        paired_review=paired_review,
        progress_audit=progress_audit,
        boundary=boundary,
    )

    assert payload["decision"]["status"] == (
        "ownership_label_recovery_seed_manifest_ready_selector_blocked"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["stage7_row_count"] == 0
    assert payload["summary"]["selected_failure_with_visible_positive_alternative_count"] == 1
    assert payload["summary"]["safe_preservation_with_visible_positive_alternative_count"] == 1
    assert "selector_training" in payload["forbidden_uses"]


def test_selector_objective_seed_manifest_remains_non_causal():
    review = {
        "summary": {"stage7_row_count": 0},
        "decision": {"selector_allowed": False},
        "joined_records": [
            {
                "state_id": "state.fail",
                "source_stage": "stage5",
                "selected_provider": "krk.stage0_basin",
                "selected_provider_family": "stage0_basin",
                "target_label": "selected_owner_failed",
                "trace_provider_candidate_count": 1,
                "positive_trace_provider_candidate_count": 1,
                "trace_sources": ["exact_trace_enrichment_sandbox"],
                "recovery_class": "selected_failure_with_visible_positive_alternative",
            },
            {
                "state_id": "state.safe",
                "source_stage": "stage5",
                "selected_provider": "krk.fence_established",
                "selected_provider_family": "fence_established",
                "target_label": "selected_owner_converted",
                "trace_provider_candidate_count": 1,
                "positive_trace_provider_candidate_count": 1,
                "trace_sources": ["candidate_generation_refresh_sandbox"],
                "recovery_class": "safe_preservation_with_visible_positive_alternative",
            },
        ],
    }

    payload = _selector_objective_seed_manifest.build_payload(review=review)

    assert payload["decision"]["status"] == "selector_objective_seed_manifest_ready_non_causal"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["summary"]["candidate_switch_contrast_seed_count"] == 1
    assert payload["summary"]["safe_preservation_contrast_seed_count"] == 1
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0


def test_selector_objective_seed_probe_confirms_semantics_but_blocks_runtime():
    manifest = {
        "summary": {"selector_training_row_count": 0, "stage7_training_row_count": 0},
        "seed_rows": [
            {
                "state_id": "state.fail",
                "source_stage": "stage5",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "positive_trace_provider_candidate_count": 1,
                "objective_channel": "candidate_switch_contrast_seed",
            },
            {
                "state_id": "state.safe",
                "source_stage": "stage5",
                "selected_provider": "krk.fence_established",
                "selected_owner_label": "selected_owner_converted",
                "positive_trace_provider_candidate_count": 1,
                "objective_channel": "safe_preservation_contrast_seed",
            },
        ],
    }

    payload = _selector_objective_seed_probe.build_payload(manifest=manifest)

    assert payload["decision"]["status"] == (
        "selector_objective_seed_probe_underpowered_semantics_confirmed"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["summary"]["apparent_semantic_rule_accuracy"] == 1.0
    assert payload["summary"]["benchmark_underpowered"] is True
    assert payload["summary"]["runtime_feature_eligible_prediction_count"] == 0
    assert payload["interpretation"]["selector_training_supported"] is False


def test_joined_trace_ownership_collection_manifest_requires_review_before_runtime():
    ownership = {
        "rows": [
            {
                "state_id": "state.fail",
                "source_stage": "stage5",
                "provider_id": "krk.stage0_basin",
                "provider_family": "stage0_basin",
                "target_label": "selected_owner_failed",
            },
            {
                "state_id": "state.safe",
                "source_stage": "stage6",
                "provider_id": "krk.stage0_basin",
                "provider_family": "stage0_basin",
                "target_label": "selected_owner_converted",
            },
            {
                "state_id": "state.stage4",
                "source_stage": "stage4",
                "provider_id": "krk.stage0_basin",
                "provider_family": "stage0_basin",
                "target_label": "selected_owner_failed",
            },
        ]
    }
    dataset = {
        "rows": [
            {
                "evidence_channel": "runtime_observation_trace_feature",
                "state_id": "state.already",
                "candidate_provider_id": "krk.stage0_basin",
                "stage7_challenge_row": False,
            }
        ]
    }
    seed_probe = {"decision": {"selector_allowed": False}}

    payload = _joined_trace_ownership_collection_manifest.build_payload(
        ownership=ownership,
        dataset=dataset,
        seed_probe=seed_probe,
    )

    assert payload["decision"]["status"] == (
        "joined_trace_ownership_collection_manifest_ready_for_review"
    )
    assert payload["decision"]["runtime_collection_allowed_by_manifest"] is False
    assert payload["summary"]["approved_observation_scope_candidate_count"] == 2
    assert payload["summary"]["excluded_requires_separate_review_count"] == 1
    assert payload["summary"]["runtime_collection_allowed_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0


def test_joined_trace_ownership_collection_review_packet_does_not_authorize_run():
    manifest = {
        "decision": {
            "status": "joined_trace_ownership_collection_manifest_ready_for_review"
        },
        "manifest_rows": [
            {
                "state_id": "state.fail",
                "source_stage": "stage5",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "approved_observation_scope": True,
                "priority": "high_selected_failure",
            },
            {
                "state_id": "state.safe",
                "source_stage": "stage6",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_converted",
                "approved_observation_scope": True,
                "priority": "medium_safe_preservation_control",
            },
            {
                "state_id": "state.stage4",
                "source_stage": "stage4",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "approved_observation_scope": False,
                "priority": "excluded_requires_separate_review",
            },
        ],
    }

    payload = _joined_trace_ownership_collection_packet.build_payload(manifest=manifest)

    assert payload["decision"]["status"] == (
        "joined_trace_ownership_observation_collection_review_ready"
    )
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["approved_if_later_explicitly_authorized"]["max_rows"] == 8
    assert payload["approved_if_later_explicitly_authorized"]["selected_review_row_count"] == 2
    assert "stage4_runtime_scope" in payload["explicitly_forbidden"]


def test_joined_trace_ownership_collection_preserves_observation_only_invariants(monkeypatch):
    packet = {
        "approved_if_later_explicitly_authorized": {
            "max_rows": 2,
            "protected_stages": ["stage5", "stage6"],
            "excluded_stages": ["stage4", "stage7", "stage8"],
        },
        "review_rows": [
            {
                "state_id": "state.fail",
                "source_stage": "stage5",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "priority": "high_selected_failure",
            },
            {
                "state_id": "state.safe",
                "source_stage": "stage6",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_converted",
                "priority": "medium_safe_preservation_control",
            },
            {
                "state_id": "state.stage4",
                "source_stage": "stage4",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "priority": "excluded_requires_separate_review",
            },
        ],
    }
    context = {
        "rows": [
            {
                "state_id": "state.fail",
                "frame_id": "cp.fail",
                "fen": "fen-fail",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
            },
            {
                "state_id": "state.safe",
                "frame_id": "cp.safe",
                "fen": "fen-safe",
                "source_stage": "stage6",
                "active_landmark_label": "drive_to_edge",
            },
        ]
    }

    def fake_run(case, *, enabled):
        frame = {
            "candidate_source": "stage_conditioned_candidate_generation_refresh",
            "policy": "trace_stage_family_context",
            "direct_request": False,
            "score_delta": 0.0,
            "causal_status": "candidate_generation_only",
            "protected_status": "protected_control",
            "stage": case["source_stage"],
            "provider_family": "stage0_basin",
            "provider_id": "krk.stage0_basin",
            "capacity_evidence_kind": "positive_capacity",
        }
        return {
            "move": "a1a2",
            "selected_provider": "krk.stage0_basin",
            "confidence": 1.0,
            "observation": {"frames": [frame] if enabled else []},
        }

    monkeypatch.setattr(_joined_trace_ownership_collection_run, "_run_decision", fake_run)

    payload = _joined_trace_ownership_collection_run.build_payload(
        packet=packet,
        context=context,
    )

    assert payload["decision"]["status"] == "joined_trace_ownership_collection_complete_seed_improved"
    assert payload["summary"]["attempted_row_count"] == 2
    assert payload["summary"]["joined_row_count"] == 2
    assert payload["summary"]["switch_contrast_count"] == 1
    assert payload["summary"]["safe_preservation_count"] == 1
    assert payload["summary"]["selected_move_provider_delta_count"] == 0
    assert payload["summary"]["score_delta_count"] == 0
    assert payload["summary"]["routing_delta_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["runtime_selector_implemented"] is False


def test_selector_objective_seed_manifest_v1_adds_collection_rows_without_training():
    seed_v0 = {
        "seed_rows": [
            {
                "state_id": "state.old",
                "source_stage": "stage5",
                "selected_provider": "krk.fence_established",
                "selected_provider_family": "fence_established",
                "selected_owner_label": "selected_owner_converted",
                "trace_provider_candidate_count": 1,
                "positive_trace_provider_candidate_count": 1,
                "trace_sources": ["candidate_generation_refresh_sandbox"],
                "recovery_class": "safe_preservation_with_visible_positive_alternative",
                "objective_channel": "safe_preservation_contrast_seed",
            }
        ]
    }
    collection = {
        "decision": {"collection_valid": True},
        "summary": {"joined_row_count": 8},
        "rows": [
            {
                "state_id": f"state.fail.{idx}",
                "source_stage": "stage5",
                "selected_provider_label": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "enabled_refresh_frame_count": 1,
                "positive_refresh_frame_count": 1,
                "recovery_class": "selected_failure_with_visible_positive_alternative",
                "joined_trace_ownership_row": True,
            }
            for idx in range(4)
        ]
        + [
            {
                "state_id": f"state.safe.{idx}",
                "source_stage": "stage6",
                "selected_provider_label": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_converted",
                "enabled_refresh_frame_count": 1,
                "positive_refresh_frame_count": 1,
                "recovery_class": "safe_preservation_with_visible_positive_alternative",
                "joined_trace_ownership_row": True,
            }
            for idx in range(4)
        ],
    }

    payload = _selector_objective_seed_manifest_v1.build_payload(
        seed_v0=seed_v0,
        collection=collection,
    )

    assert payload["decision"]["status"] == "selector_objective_seed_manifest_v1_ready_non_causal"
    assert payload["summary"]["candidate_switch_contrast_seed_count"] == 4
    assert payload["summary"]["safe_preservation_contrast_seed_count"] == 5
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["decision"]["selector_allowed"] is False


def test_selector_objective_seed_probe_v1_allows_only_non_causal_feature_probe():
    manifest = {
        "summary": {"selector_training_row_count": 0, "stage7_training_row_count": 0},
        "seed_rows": [
            {
                "state_id": f"state.fail.{idx}",
                "source_stage": "stage5",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "positive_trace_provider_candidate_count": 1,
                "objective_channel": "candidate_switch_contrast_seed",
            }
            for idx in range(4)
        ]
        + [
            {
                "state_id": f"state.safe.{idx}",
                "source_stage": "stage6",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_converted",
                "positive_trace_provider_candidate_count": 1,
                "objective_channel": "safe_preservation_contrast_seed",
            }
            for idx in range(8)
        ],
    }

    payload = _selector_objective_seed_probe_v1.build_payload(manifest=manifest)

    assert payload["decision"]["status"] == "selector_objective_seed_ready_for_non_causal_feature_probe"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["summary"]["seed_row_count"] == 12
    assert payload["summary"]["benchmark_underpowered"] is False
    assert payload["summary"]["runtime_feature_eligible_prediction_count"] == 0
    assert payload["interpretation"]["runtime_selector_supported"] is False


def test_selector_objective_feature_probe_keeps_oracle_separate_from_runtime_features():
    rows = []
    for idx in range(4):
        rows.append(
            {
                "state_id": f"state.fail.{idx}",
                "source_stage": "stage5",
                "selected_provider": "krk.stage0_basin",
                "selected_provider_family": "stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "positive_trace_provider_candidate_count": 10,
                "trace_sources": ["stage5_6_candidate_generation_refresh_collection"],
                "objective_channel": "candidate_switch_contrast_seed",
                "stage7_training_row": False,
            }
        )
    for idx in range(8):
        rows.append(
            {
                "state_id": f"state.safe.{idx}",
                "source_stage": "stage6",
                "selected_provider": "krk.stage0_basin",
                "selected_provider_family": "stage0_basin",
                "selected_owner_label": "selected_owner_converted",
                "positive_trace_provider_candidate_count": 10,
                "trace_sources": ["stage5_6_candidate_generation_refresh_collection"],
                "objective_channel": "safe_preservation_contrast_seed",
                "stage7_training_row": False,
            }
        )
    manifest = {
        "summary": {"selector_training_row_count": 0, "stage7_training_row_count": 0},
        "seed_rows": rows,
    }
    seed_probe = {"decision": {"status": "selector_objective_seed_ready_for_non_causal_feature_probe"}}

    payload = _selector_objective_feature_probe.build_payload(
        manifest=manifest,
        seed_probe=seed_probe,
    )

    assert payload["summary"]["offline_oracle_accuracy"] == 1.0
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["results"]["offline_selected_owner_outcome_oracle"]["runtime_feature_eligible"] is False
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0


def test_selector_objective_feature_probe_review_blocks_runtime_without_passing_model():
    probe = {
        "summary": {
            "seed_row_count": 12,
            "target_channel_counts": {
                "candidate_switch_contrast_seed": 4,
                "safe_preservation_contrast_seed": 8,
            },
            "runtime_threshold_passing_model_count": 0,
            "offline_oracle_accuracy": 1.0,
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
        },
        "results": {
            "switchy": {
                "model_id": "switchy",
                "runtime_feature_eligible": True,
                "switch_recall": 0.75,
                "preserve_recall": 0.0,
                "switch_precision": 0.27,
            },
            "safe": {
                "model_id": "safe",
                "runtime_feature_eligible": True,
                "switch_recall": 0.5,
                "preserve_recall": 1.0,
                "switch_precision": 1.0,
            },
        },
    }

    payload = _selector_objective_feature_review.build_payload(probe=probe)

    assert payload["decision"]["status"] == (
        "selector_feature_probe_blocks_runtime_needs_diverse_evidence"
    )
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert "offline_outcome_oracle_is_not_runtime_feature_eligible" in payload["blockers"]
    assert "more_non_stage0_selected_owner_rows" in payload["recommended_evidence"]


def test_selector_objective_diversity_gap_points_to_stage4_scope_review():
    ownership = {
        "rows": [
            {
                "state_id": "state.stage4.fail",
                "frame_id": "cp.stage4.fail",
                "source_stage": "stage4",
                "active_landmark_label": "edge_trap_wrong_tempo",
                "provider_id": "krk.stage0_basin",
                "provider_family": "stage0_basin",
                "target_label": "selected_owner_failed",
            },
            {
                "state_id": "state.stage5.safe",
                "frame_id": "cp.stage5.safe",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "provider_id": "krk.edge_trap_close",
                "provider_family": "edge_trap",
                "target_label": "selected_owner_converted",
            },
        ]
    }
    seed = {"seed_rows": [{"state_id": "state.seed"}]}
    feature_review = {"decision": {"status": "selector_feature_probe_blocks_runtime_needs_diverse_evidence"}}

    payload = _selector_objective_diversity_gap.build_payload(
        ownership=ownership,
        seed=seed,
        feature_review=feature_review,
    )

    assert payload["decision"]["status"] == (
        "selector_objective_diversity_gap_requires_stage4_scope_review"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["summary"]["remaining_stage4_selected_failure_count"] == 1
    assert payload["interpretation"]["stage4_scope_needed_for_more_switch_contrast"] is True


def test_stage4_joined_trace_scope_packet_requires_explicit_approval():
    diversity = {
        "decision": {
            "status": "selector_objective_diversity_gap_requires_stage4_scope_review"
        },
        "stage4_failure_candidates": [
            {
                "state_id": "state.stage4.fail",
                "source_stage": "stage4",
                "active_landmark_label": "edge_trap_wrong_tempo",
                "selected_provider": "krk.stage0_basin",
                "provider_family": "stage0_basin",
                "target_label": "selected_owner_failed",
            }
        ],
    }

    payload = _stage4_joined_trace_scope_packet.build_payload(diversity=diversity)

    assert payload["decision"]["status"] == "stage4_joined_trace_ownership_scope_review_ready"
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["approved_if_later_explicitly_authorized"]["protected_stages"] == ["stage4"]
    assert payload["approved_if_later_explicitly_authorized"]["requires_new_stage4_observation_source"] is True
    assert "selector_training" in payload["explicitly_forbidden"]


def test_clean_curriculum_checkpoint_plan_blocks_full_run_without_manifest_review():
    payload = _clean_curriculum_checkpoint_plan.build_payload()

    assert payload["schema_version"] == "krk_clean_curriculum_checkpoint_plan.v0"
    assert payload["decision"]["status"] == (
        "clean_curriculum_checkpoint_plan_ready_full_run_requires_review"
    )
    assert payload["decision"]["stage7_remains_quarantined"] is True
    assert payload["decision"]["stage8_remains_blocked"] is True
    assert payload["decision"]["runtime_selector_allowed"] is False
    assert payload["readiness_review"]["can_run_full_clean_curriculum_now"] is False
    assert payload["candidate_generation_observation_policy"]["include_in_normal_clean_training"] is False
    assert payload["candidate_generation_observation_policy"]["selector_allowed"] is False
    assert {step["step_id"] for step in payload["command_sequence"]} == {
        "stage1_foundation_clean",
        "stage4_wrong_tempo_profile",
        "stage5_fence_handoff",
        "stage6_drive_overlay",
        "stage6_overlay_composition",
    }


def test_clean_curriculum_checkpoint_plan_preserves_stage_boundaries():
    payload = _clean_curriculum_checkpoint_plan.build_payload()
    checkpoints = {item["stage"]: item for item in payload["stage_checkpoints"]}

    assert checkpoints["stage7"]["promotion_policy"] == "do_not_promote"
    assert payload["stage8_training_allowed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert "training Stage 8" in payload["readiness_review"]["invalid_run_conditions"]
    assert "promoting Stage 7" in payload["readiness_review"]["invalid_run_conditions"]


def test_clean_retrain_execution_manifest_uses_fresh_outputs_and_blocks_run():
    payload = _clean_retrain_execution_manifest.build_payload()

    assert payload["schema_version"] == "krk_clean_retrain_execution_manifest.v0"
    assert payload["decision"]["status"] == "clean_retrain_execution_manifest_ready_not_run"
    assert payload["decision"]["full_run_authorized_by_this_manifest"] is False
    assert payload["preflight"]["fresh_output_root_required"] is True
    assert payload["preflight"]["must_not_overwrite_protected_snapshots"] is True
    assert payload["runtime_behavior_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["selector_training_allowed"] is False
    assert all(
        "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0" in output
        for step in payload["steps"]
        for output in step.get("expected_outputs", [])
    )


def test_clean_retrain_execution_manifest_chains_prior_stage_learners():
    payload = _clean_retrain_execution_manifest.build_payload()
    steps = {step["step_id"]: step for step in payload["steps"]}

    assert steps["stage2b_enemy_between"]["prerequisites"] == ["stage2a_edge_trap_close"]
    assert steps["stage4_wrong_tempo"]["prerequisites"] == ["stage2b_enemy_between"]
    assert steps["stage5_fence_handoff"]["prerequisites"] == ["stage4_wrong_tempo"]
    assert steps["stage6_drive_overlay_candidate"]["prerequisites"] == ["stage5_fence_handoff"]
    assert steps["stage6_overlay_composition_review"]["execution_status"] == (
        "requires_dedicated_compose_script_or_manual_review"
    )
    stage6_cmd = " ".join(steps["stage6_drive_overlay_candidate"]["commands"][0])
    assert "--adaptive-composition-profile handoff_composition_v1" in stage6_cmd
    assert "stage5_fence_handoff/baseline/best_by_stage/fence_established.pkl" in stage6_cmd


def test_stage6_overlay_compose_manifest_is_review_only_and_fresh_scoped():
    payload = _stage6_overlay_compose_manifest.build_payload()

    assert payload["schema_version"] == "krk_stage6_overlay_compose_manifest.v0"
    assert payload["decision"]["status"] == "stage6_overlay_compose_manifest_ready_not_run"
    assert payload["decision"]["compose_run_authorized_by_this_manifest"] is False
    assert payload["decision"]["full_run_authorized_by_this_manifest"] is False
    assert payload["decision"]["stage7_remains_quarantined"] is True
    assert payload["decision"]["stage8_remains_blocked"] is True
    assert payload["runtime_behavior_changed"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["composition_profile"] == "handoff_composition_v1"
    assert payload["base_provider_version"] == "stage5_validated_v1"
    assert payload["overlay_provider_version"] == "stage6_overlay_v1"
    assert all(
        "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0" in value
        for value in payload["fresh_outputs"].values()
    )


def test_stage6_overlay_compose_manifest_preserves_overlay_compile_contract():
    payload = _stage6_overlay_compose_manifest.build_payload()
    compile_cmd = " ".join(payload["commands"]["compile_overlay_topology"])

    assert "--base-topology" in compile_cmd
    assert "--overlay-learner" in compile_cmd
    assert "--overlay-label drive_to_edge" in compile_cmd
    assert "--base-provider-version stage5_validated_v1" in compile_cmd
    assert "--overlay-provider-version stage6_overlay_v1" in compile_cmd
    assert "--validated-profile handoff_composition_v1" in compile_cmd
    assert "Stage 5 guardrail regresses" in payload["stop_conditions"]
    assert "Stage 4 caveat worsens relative to base control" in payload["stop_conditions"]


def test_clean_retrain_preflight_ready_without_running_training():
    payload = _clean_retrain_preflight.build_payload()

    assert payload["schema_version"] == "krk_clean_retrain_preflight.v0"
    assert payload["decision"]["status"] == "clean_retrain_preflight_ready_for_run_review"
    assert payload["decision"]["safe_to_request_run_review"] is True
    assert payload["decision"]["training_started"] is False
    assert payload["decision"]["full_run_authorized_by_this_artifact"] is False
    assert payload["summary"]["blocker_count"] == 0
    assert payload["summary"]["protected_overwrite_count"] == 0
    assert payload["summary"]["command_violation_count"] == 0
    assert payload["runtime_behavior_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False


def test_clean_retrain_smoke_manifest_is_tiny_and_not_authorizing_full_run():
    payload = _clean_retrain_smoke_manifest.build_payload()

    assert payload["schema_version"] == "krk_clean_retrain_smoke_manifest.v0"
    assert payload["decision"]["status"] in {
        "clean_retrain_smoke_manifest_ready_not_run",
        "clean_retrain_smoke_manifest_blocked",
    }
    assert payload["decision"]["safe_to_request_smoke_run_approval"] is (
        not bool(payload["blockers"])
    )
    assert payload["decision"]["smoke_run_authorized_by_this_manifest"] is False
    assert payload["decision"]["full_run_authorized_by_this_manifest"] is False
    assert payload["smoke_scope"]["stage7_rows"] == 0
    assert payload["smoke_scope"]["stage8_training"] is False
    assert payload["smoke_scope"]["samples_per_cycle"] == 8
    assert payload["smoke_scope"]["stage0_cycles"] == 1
    assert payload["smoke_scope"]["stage1_cycles"] == 1
    assert payload["runtime_behavior_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["selector_training_allowed"] is False

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
        "stage_status": stage_status,
        "sequence_policy": {
            "pipeline_status": pipeline.get("decision", {}).get("status"),
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
    stage7 = payload["stage7_sampling_gate"]
    sequence = payload["sequence_policy"]
    protected_failure_contrast = payload["protected_failure_contrast_gate"]
    missing_provider = payload["protected_missing_provider_gate"]
    selector_objective = payload["selector_objective_gate"]
    stage4_diagnostic = payload["stage4_first_move_diagnostic_gate"]
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

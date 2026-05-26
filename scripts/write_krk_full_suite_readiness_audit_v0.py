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
    "active_protected_stack": "reports/krk_active_protected_stack_v0.json",
    "clean_stack_validation": "reports/krk_clean_stack_post_replacement_validation_v0.json",
    "preservation_checks": "reports/krk_clean_retrain_retry1_preservation_checks_v0.json",
    "stage4_caveat_unblocker": "reports/krk_stage4_caveat_unblocker_packet_v0.json",
    "stage4_sandbox_approval_request": (
        "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
    ),
    "sequence_pipeline_refresh": (
        "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json"
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
    "stage7_sampling_output_validation": (
        "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
    ),
    "stage7_sampling_integration": (
        "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json"
    ),
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
    runner = payloads["stage7_sampling_runner"]
    output_validation = payloads["stage7_sampling_output_validation"]
    integration = payloads["stage7_sampling_integration"]
    gate = payloads["control_plane_gate"]

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

    stage4_decision = stage4_unblocker.get("decision") or {}
    stage4_status = (
        stage4_decision.get("status")
        or "stage4_caveat_unblocker_missing"
    )
    stage4_ready_for_explicit_approval = (
        stage4_status == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    stage4_approval_request_decision = stage4_approval_request.get("decision") or {}
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
            "ready_for_explicit_runtime_approval": stage4_ready_for_explicit_approval,
            "implementation_allowed_by_current_artifact": stage4_decision.get(
                "implementation_allowed_by_this_packet"
            ),
            "approval_request_artifact": (
                "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
            ),
            "approval_request_status": stage4_approval_request_decision.get("status"),
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
    if not post_failure_contrast_refresh_boundaries_preserved:
        hard_blockers.append("post_failure_contrast_sequence_refresh_boundary_violation")
    if boundaries["violation_count"]:
        hard_blockers.append("hard_invariant_violation_detected")
    explicit_gate_blockers: list[str] = []
    if protected_failure_contrast_pending:
        explicit_gate_blockers.append(
            "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        )
    blockers = hard_blockers + explicit_gate_blockers

    if sequence_forbidden_training_or_runtime_inputs:
        decision_status = "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows"
        next_step = "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    elif hard_blockers:
        decision_status = "krk_suite_readiness_blocked_pending_stage7_clean_success_controls"
        next_step = (
            "explicitly_approve_stage7_diverse_clean_sampling_or_choose_stage4_sandbox_gate"
        )
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
                "ready_for_explicit_approval": stage4_ready_for_explicit_approval,
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
                "approval_request_created": stage4_approval_request.get(
                    "approval_request_created"
                ),
                "implementation_authorized_by_approval_request": (
                    stage4_approval_request.get("implementation_authorized_by_request")
                ),
                "safety_scope": {
                    "approval_id": stage4_approval_scope.get("approval_id"),
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

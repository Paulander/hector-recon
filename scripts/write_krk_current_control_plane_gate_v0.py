#!/usr/bin/env python3
"""Summarize the current KRK control-plane approval gates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE4_PACKET = ROOT / "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json"
STAGE4_APPROVAL_REQUEST = (
    ROOT / "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
)
STAGE7_MANIFEST = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
STAGE7_EXECUTION_READINESS = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_execution_readiness_v0.json"
STAGE7_INTEGRATION = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json"
STAGE7_RUNNER = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_runner_v0.json"
STAGE7_OUTPUT_VALIDATION = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
STAGE7_LABEL_DISTRIBUTION_REVIEW = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.json"
)
STAGE7_ADDITIONAL_MANIFEST = (
    ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
)
STAGE7_ADDITIONAL_RUNNER = (
    ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_runner_v0.json"
)
STAGE7_POST_LABEL_OUTCOME = ROOT / "reports/krk_stage7_post_label_outcome_review_v0.json"
SEQUENCE_PROBE = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json"
SEQUENCE_POLICY_DESIGN = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json"
SEQUENCE_POLICY_CROSS_STAGE_REQUIREMENTS = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_cross_stage_plan_capsule_evidence_requirements_v0.json"
)
SEQUENCE_POLICY_BENCHMARK_REVIEW = (
    ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
)
FAILURE_CONTRAST_PLAN = (
    ROOT / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json"
)
FAILURE_CONTRAST_MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
FAILURE_CONTRAST_MANIFEST_REVIEW = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_manifest_review_v0.json"
)
FAILURE_CONTRAST_EXECUTION_READINESS = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
)
FAILURE_CONTRAST_RUNNER = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_runner_v0.json"
)
FAILURE_CONTRAST_APPROVAL_REQUEST = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
)
FAILURE_CONTRAST_OUTPUT_VALIDATION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_output_validation_v0.json"
)
FAILURE_CONTRAST_INTEGRATION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_integration_v0.json"
)
POST_FAILURE_CONTRAST_SEQUENCE_REFRESH = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
)
PROTECTED_PLAN_WINDOWS = ROOT / "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json"
SEQUENCE_POLICY_INPUTS = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
FULL_SUITE_READINESS = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
OUTPUT_JSON = ROOT / "reports/krk_current_control_plane_gate_v0.json"
OUTPUT_MD = ROOT / "reports/krk_current_control_plane_gate_v0.md"

SCHEMA_VERSION = "krk_current_control_plane_gate.v0"

FORBIDDEN_INPUT_BLOCKERS = {
    "selector_training_rows_forbidden",
    "runtime_authorization_rows_forbidden",
}

FORBIDDEN_INPUT_STATUSES = {
    "sequence_policy_benchmark_inputs_blocked_forbidden_training_or_runtime_rows",
    "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows",
    "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows",
}


COMMON_FALSE_FLAGS = {
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


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load(path)


def build_payload(
    *,
    stage4_packet: dict[str, Any] | None = None,
    stage4_approval_request: dict[str, Any] | None = None,
    stage7_manifest: dict[str, Any] | None = None,
    stage7_execution_readiness: dict[str, Any] | None = None,
    stage7_integration: dict[str, Any] | None = None,
    stage7_runner: dict[str, Any] | None = None,
    stage7_output_validation: dict[str, Any] | None = None,
    stage7_label_distribution_review: dict[str, Any] | None = None,
    stage7_additional_manifest: dict[str, Any] | None = None,
    stage7_additional_runner: dict[str, Any] | None = None,
    stage7_post_label_outcome: dict[str, Any] | None = None,
    sequence_probe: dict[str, Any] | None = None,
    sequence_policy_design: dict[str, Any] | None = None,
    sequence_policy_cross_stage_requirements: dict[str, Any] | None = None,
    sequence_policy_benchmark_review: dict[str, Any] | None = None,
    failure_contrast_plan: dict[str, Any] | None = None,
    failure_contrast_manifest: dict[str, Any] | None = None,
    failure_contrast_manifest_review: dict[str, Any] | None = None,
    failure_contrast_execution_readiness: dict[str, Any] | None = None,
    failure_contrast_runner: dict[str, Any] | None = None,
    failure_contrast_approval_request: dict[str, Any] | None = None,
    failure_contrast_output_validation: dict[str, Any] | None = None,
    failure_contrast_integration: dict[str, Any] | None = None,
    post_failure_contrast_sequence_refresh: dict[str, Any] | None = None,
    protected_plan_windows: dict[str, Any] | None = None,
    sequence_policy_inputs: dict[str, Any] | None = None,
    full_suite_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stage4_packet = stage4_packet or _load(STAGE4_PACKET)
    stage4_approval_request = stage4_approval_request or _load_optional(
        STAGE4_APPROVAL_REQUEST
    )
    stage7_manifest = stage7_manifest or _load(STAGE7_MANIFEST)
    stage7_execution_readiness = stage7_execution_readiness or _load_optional(STAGE7_EXECUTION_READINESS)
    stage7_integration = stage7_integration or _load_optional(STAGE7_INTEGRATION)
    stage7_runner = stage7_runner or _load_optional(STAGE7_RUNNER)
    stage7_output_validation = stage7_output_validation or _load_optional(STAGE7_OUTPUT_VALIDATION)
    stage7_label_distribution_review = stage7_label_distribution_review or _load_optional(STAGE7_LABEL_DISTRIBUTION_REVIEW)
    stage7_additional_manifest = stage7_additional_manifest or _load_optional(STAGE7_ADDITIONAL_MANIFEST)
    stage7_additional_runner = stage7_additional_runner or _load_optional(STAGE7_ADDITIONAL_RUNNER)
    stage7_post_label_outcome = stage7_post_label_outcome or _load_optional(STAGE7_POST_LABEL_OUTCOME)
    sequence_probe = sequence_probe or _load(SEQUENCE_PROBE)
    sequence_policy_design = sequence_policy_design or _load(SEQUENCE_POLICY_DESIGN)
    sequence_policy_cross_stage_requirements = (
        sequence_policy_cross_stage_requirements
        or _load_optional(SEQUENCE_POLICY_CROSS_STAGE_REQUIREMENTS)
    )
    sequence_policy_benchmark_review = sequence_policy_benchmark_review or _load_optional(
        SEQUENCE_POLICY_BENCHMARK_REVIEW
    )
    failure_contrast_plan = failure_contrast_plan or _load_optional(FAILURE_CONTRAST_PLAN)
    failure_contrast_manifest = failure_contrast_manifest or _load_optional(FAILURE_CONTRAST_MANIFEST)
    failure_contrast_manifest_review = failure_contrast_manifest_review or _load_optional(
        FAILURE_CONTRAST_MANIFEST_REVIEW
    )
    failure_contrast_execution_readiness = failure_contrast_execution_readiness or _load_optional(
        FAILURE_CONTRAST_EXECUTION_READINESS
    )
    failure_contrast_runner = failure_contrast_runner or _load_optional(
        FAILURE_CONTRAST_RUNNER
    )
    failure_contrast_approval_request = (
        failure_contrast_approval_request
        or _load_optional(FAILURE_CONTRAST_APPROVAL_REQUEST)
    )
    failure_contrast_output_validation = failure_contrast_output_validation or _load_optional(
        FAILURE_CONTRAST_OUTPUT_VALIDATION
    )
    failure_contrast_integration = failure_contrast_integration or _load_optional(
        FAILURE_CONTRAST_INTEGRATION
    )
    post_failure_contrast_sequence_refresh = (
        post_failure_contrast_sequence_refresh
        or _load_optional(POST_FAILURE_CONTRAST_SEQUENCE_REFRESH)
    )
    protected_plan_windows = protected_plan_windows or _load_optional(PROTECTED_PLAN_WINDOWS)
    sequence_policy_inputs = sequence_policy_inputs or _load_optional(SEQUENCE_POLICY_INPUTS)
    full_suite_readiness = full_suite_readiness or _load_optional(FULL_SUITE_READINESS)
    readiness_boundaries = full_suite_readiness.get("runtime_and_training_boundaries") or {}
    protected_stack = full_suite_readiness.get("protected_stack") or {}
    active_stack_path_status = protected_stack.get("active_stack_path_status") or {}
    rollback_stack_path_status = protected_stack.get("rollback_stack_path_status") or {}
    protected_stack_ready = bool(protected_stack.get("ready", True))
    protected_stack_status = (
        "retry1_stage5_6_active_manifest_validated"
        if protected_stack_ready
        else "protected_stack_validation_blocked"
    )
    protected_stack_blockers = list(full_suite_readiness.get("hard_blockers") or [])
    protected_plan_window_met = bool(
        protected_plan_windows.get("summary", {}).get("protected_cross_stage_evidence_met", False)
    )
    stage7_success_ready = bool(
        stage7_integration.get("summary", {}).get("success_controls_met", False)
    )
    raw_stage7_execution_readiness_status = stage7_runner.get("summary", {}).get(
        "execution_readiness_status"
    )
    stage7_label_gate_closed = (
        stage7_success_ready
        and stage7_runner.get("decision", {}).get("status")
        == "stage7_diverse_clean_sampling_runner_executed_success"
    )
    current_stage7_execution_readiness_status = (
        "not_applicable_stage7_success_gate_closed"
        if stage7_label_gate_closed
        else raw_stage7_execution_readiness_status
    )
    sequence_inputs_ready = (
        sequence_policy_inputs.get("decision", {}).get("status")
        == "sequence_policy_benchmark_inputs_ready_non_causal"
    )
    sequence_policy_status = (
        sequence_policy_benchmark_review.get("decision", {}).get("status")
        or sequence_policy_design.get("decision", {}).get("status")
    )
    passive_sequence_design = (
        sequence_policy_design.get("passive_design_without_new_labels") or {}
    )
    cross_stage_requirements_readiness = (
        sequence_policy_cross_stage_requirements.get("current_readiness") or {}
    )
    sequence_policy_input_summary = sequence_policy_inputs.get("summary", {})
    sequence_policy_input_decision = sequence_policy_inputs.get("decision", {})
    sequence_policy_benchmark_review_blockers = set(
        sequence_policy_benchmark_review.get("blockers") or []
    )
    forbidden_input_blockers_set = FORBIDDEN_INPUT_BLOCKERS & (
        sequence_policy_benchmark_review_blockers
        | set(sequence_policy_input_summary.get("preflight_blockers") or [])
        | set(sequence_policy_inputs.get("preflight", {}).get("blockers") or [])
    )
    if int(sequence_policy_input_summary.get("selector_training_row_count") or 0) > 0:
        forbidden_input_blockers_set.add("selector_training_rows_forbidden")
    if int(sequence_policy_input_summary.get("runtime_authorization_row_count") or 0) > 0:
        forbidden_input_blockers_set.add("runtime_authorization_rows_forbidden")
    sequence_forbidden_input_blockers = sorted(forbidden_input_blockers_set)
    sequence_forbidden_training_or_runtime_inputs = (
        bool(sequence_forbidden_input_blockers)
        or sequence_policy_input_decision.get("status") in FORBIDDEN_INPUT_STATUSES
        or sequence_policy_status in FORBIDDEN_INPUT_STATUSES
    )
    failure_contrast_integration_ready = bool(
        failure_contrast_integration.get("summary", {}).get("integration_ready")
    )
    failure_contrast_manifest_summary = failure_contrast_manifest.get("summary", {})
    failure_contrast_constraints = failure_contrast_manifest.get(
        "collection_constraints", {}
    )
    failure_contrast_runner_summary = failure_contrast_runner.get("summary", {})
    failure_contrast_approval_request_summary = (
        failure_contrast_approval_request.get("summary") or {}
    )
    post_failure_contrast_sequence_refresh_summary = (
        post_failure_contrast_sequence_refresh.get("summary") or {}
    )
    failure_contrast_ready_for_collection = (
        failure_contrast_manifest_review.get("decision", {}).get("status")
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    )
    failure_contrast_command = (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection --refresh-after-run "
        "--approval-receipt "
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    stage4_approval_scope = (
        stage4_approval_request.get("required_scope_if_user_approves") or {}
    )
    approval_options = [
        {
            "option_id": "approve_stage4_first_move_contrast_sandbox",
            "artifact": "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.md",
            "approval_request_artifact": (
                "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.md"
            ),
            "approval_request_status": stage4_approval_request.get("decision", {}).get(
                "status"
            ),
            "approval_request_created": stage4_approval_request.get(
                "approval_request_created"
            ),
            "status": stage4_packet.get("decision", {}).get("status"),
            "what_it_allows": "default-off Stage 4 CandidateMoveFrame first-move contrast sandbox only",
            "safety_scope": {
                "approval_id": stage4_approval_scope.get("approval_id"),
                "sandbox_scope_id": stage4_approval_scope.get("sandbox_scope_id"),
                "default_off": stage4_approval_scope.get("default_off"),
                "default_enabled": stage4_approval_scope.get("default_enabled"),
                "approval_request_created": stage4_approval_scope.get(
                    "approval_request_created"
                ),
                "implementation_authorized_by_request": stage4_approval_scope.get(
                    "implementation_authorized_by_request"
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
                "provider_suppression_allowed": stage4_approval_scope.get(
                    "provider_suppression_allowed"
                ),
                "broad_stage0_penalty_allowed": stage4_approval_scope.get(
                    "broad_stage0_penalty_allowed"
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
            "what_it_does_not_allow": [
                "default enablement",
                "exact-state or exact-move runtime exception",
                "selector training",
                "broad stage0 penalty",
                "provider suppression",
                "Stage 7 promotion",
                "Stage 8 training",
            ],
            "recommended_if": "you want to reduce the known Stage 4 h40 caveat now",
        },
    ]
    if not stage7_success_ready:
        approval_options.append(
            {
                "option_id": "approve_stage7_additional_clean_label_run",
                "artifact": "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.md",
                "status": stage7_additional_runner.get("decision", {}).get(
                    "status",
                    stage7_additional_manifest.get("decision", {}).get("status"),
                ),
                "what_it_allows": "run 4 bounded h40 clean Stage 7 follow-up label jobs, 32 samples total",
                "safety_scope": {
                    "resume_safe": True,
                    "skip_existing_outputs_by_default": True,
                    "invalid_existing_outputs_block_without_overwrite": True,
                    "execution_readiness_recomputed_live": (
                        stage7_additional_runner.get("summary", {}).get(
                            "execution_readiness_source"
                        )
                        == "live_recomputed"
                    ),
                    "per_job_timeout_seconds": stage7_additional_runner.get("summary", {}).get(
                        "job_timeout_seconds"
                    ),
                    "timed_out_job_count": stage7_additional_runner.get("summary", {}).get(
                        "timed_out_job_count"
                    ),
                    "stage7_training_rows": 0,
                },
                "what_it_does_not_allow": [
                    "runtime behavior",
                    "selector training",
                    "Stage 7 promotion",
                    "Stage 8 training",
                    "Stage 7 repair flags",
                ],
                "recommended_if": "you want to fill the one remaining Stage 7 clean success-control gap before broader sequence-policy benchmarking",
            }
        )
    if not protected_stack_ready:
        approval_options.append(
            {
                "option_id": "repair_protected_stack_validation",
                "artifact": "reports/krk_full_suite_readiness_audit_v0.md",
                "status": full_suite_readiness.get("decision", {}).get("status"),
                "what_it_allows": "repair passive protected-stack validation evidence before any collection or runtime review",
                "command_if_explicitly_approved": None,
                "safety_scope": {
                    "protected_stack_ready": protected_stack_ready,
                    "protected_stack_readiness_status": protected_stack.get("status"),
                    "protected_stack_rollback_paths_preserved": protected_stack.get(
                        "rollback_paths_preserved"
                    ),
                    "protected_stack_active_paths_safe": active_stack_path_status.get(
                        "all_paths_safe"
                    ),
                    "protected_stack_active_paths_exist": active_stack_path_status.get(
                        "all_paths_exist"
                    ),
                    "protected_stack_rollback_paths_safe": rollback_stack_path_status.get(
                        "all_paths_safe"
                    ),
                    "protected_stack_rollback_paths_exist": rollback_stack_path_status.get(
                        "all_paths_exist"
                    ),
                    "protected_stack_rollback_common_paths_distinct": protected_stack.get(
                        "rollback_common_paths_distinct"
                    ),
                    "protected_stack_filesystem_snapshots_replaced": protected_stack.get(
                        "filesystem_snapshots_replaced"
                    ),
                    "hard_blockers": protected_stack_blockers,
                    "runtime_behavior_changed": False,
                    "stage7_promotion_allowed": False,
                    "stage8_training_allowed": False,
                },
                "what_it_does_not_allow": [
                    "protected failure-contrast collection",
                    "runtime selector",
                    "runtime default changes",
                    "runtime DTM or tablebase lookup",
                    "gameplay-time topology mutation",
                    "selector training",
                    "Stage 7 promotion",
                    "Stage 8 training",
                ],
                "recommended_if": "protected stack validation is missing, stale, or rollback evidence is unsafe",
            }
        )
    elif sequence_forbidden_training_or_runtime_inputs:
        approval_options.append(
            {
                "option_id": "repair_sequence_policy_inputs_remove_training_or_runtime_rows",
                "artifact": "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.md",
                "status": (
                    sequence_policy_input_decision.get("status") or sequence_policy_status
                ),
                "what_it_allows": "repair passive sequence-policy inputs by removing forbidden selector-training or runtime-authorization rows",
                "command_if_explicitly_approved": None,
                "safety_scope": {
                    "selector_training_row_count": sequence_policy_input_summary.get(
                        "selector_training_row_count"
                    ),
                    "runtime_authorization_row_count": sequence_policy_input_summary.get(
                        "runtime_authorization_row_count"
                    ),
                    "blockers": sequence_forbidden_input_blockers,
                    "runtime_behavior_changed": False,
                    "stage7_training_rows": 0,
                    "stage7_promotion_allowed": False,
                    "stage8_training_allowed": False,
                },
                "what_it_does_not_allow": [
                    "protected failure-contrast collection",
                    "runtime selector",
                    "runtime default changes",
                    "runtime DTM or tablebase lookup",
                    "gameplay-time topology mutation",
                    "selector training",
                    "Stage 7 promotion",
                    "Stage 8 training",
                ],
                "recommended_if": "sequence-policy inputs contain forbidden training or runtime-authorization rows",
            }
        )
    else:
        approval_options.append(
            {
                "option_id": "approve_protected_plan_window_failure_contrast_collection"
            if failure_contrast_manifest_review.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
            else "review_protected_plan_window_failure_contrast_manifest"
            if failure_contrast_manifest.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_manifest_ready_for_review"
            else "review_protected_plan_window_failure_contrast_plan"
            if failure_contrast_plan.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
            else "review_non_causal_sequence_policy_benchmark_results"
            if sequence_inputs_ready
            else "defer_runtime_and_labels_review_cross_stage_plan_capsule_evidence",
            "artifact": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_manifest_review_v0.md"
            )
            if failure_contrast_manifest_review.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
            else (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_manifest_v0.md"
            )
            if failure_contrast_manifest.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_manifest_ready_for_review"
            else (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_plan_v0.md"
            )
            if failure_contrast_plan.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
            else "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.md"
            if sequence_inputs_ready
            else "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.md",
            "status": failure_contrast_execution_readiness.get("decision", {}).get("status")
            or failure_contrast_runner.get("decision", {}).get("status")
            or failure_contrast_manifest_review.get("decision", {}).get("status")
            or failure_contrast_manifest.get("decision", {}).get("status")
            or failure_contrast_plan.get("decision", {}).get("status")
            or sequence_policy_status,
            "what_it_allows": "explicitly approved bounded observation-only protected plan-window failure-contrast collection"
            if failure_contrast_ready_for_collection
            else "non-causal protected plan-window failure-contrast manifest review only"
            if failure_contrast_manifest.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_manifest_ready_for_review"
            else "non-causal protected plan-window failure-contrast plan review only"
            if failure_contrast_plan.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
            else "non-causal sequence-policy benchmark evidence review only"
            if sequence_inputs_ready
            else "non-causal protected Stage 4/5/6 plan-window evidence review only",
            "command_if_explicitly_approved": (
                failure_contrast_command if failure_contrast_ready_for_collection else None
            ),
            "approval_request_artifact": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_approval_request_v0.md"
            )
            if failure_contrast_ready_for_collection
            else None,
            "safety_scope": (
                {
                    "manifest_job_count": failure_contrast_manifest_summary.get(
                        "job_count"
                    ),
                    "max_jobs": failure_contrast_manifest_summary.get("job_count"),
                    "runner_max_jobs_option": failure_contrast_runner_summary.get(
                        "max_jobs"
                    ),
                    "horizon": (
                        f"h{failure_contrast_constraints.get('horizon')}"
                        if failure_contrast_constraints.get("horizon")
                        else None
                    ),
                    "stage": "protected_plan_window_failure_contrast_evidence_only",
                    "protected_stack_readiness_status": protected_stack.get("status"),
                    "protected_stack_rollback_paths_preserved": protected_stack.get(
                        "rollback_paths_preserved"
                    ),
                    "protected_stack_active_paths_safe": active_stack_path_status.get(
                        "all_paths_safe"
                    ),
                    "protected_stack_active_paths_exist": active_stack_path_status.get(
                        "all_paths_exist"
                    ),
                    "protected_stack_rollback_paths_safe": rollback_stack_path_status.get(
                        "all_paths_safe"
                    ),
                    "protected_stack_rollback_paths_exist": rollback_stack_path_status.get(
                        "all_paths_exist"
                    ),
                    "protected_stack_rollback_common_paths_distinct": protected_stack.get(
                        "rollback_common_paths_distinct"
                    ),
                    "protected_stack_filesystem_snapshots_replaced": protected_stack.get(
                        "filesystem_snapshots_replaced"
                    ),
                    "source_stage_counts": failure_contrast_manifest_summary.get(
                        "source_stage_counts"
                    ),
                    "stop_after_unique_failures": failure_contrast_constraints.get(
                        "stop_after_unique_failures"
                    ),
                    "observation_only": bool(
                        failure_contrast_constraints.get("observation_only")
                    ),
                    "resume_safe": True,
                    "skip_existing_outputs_by_default": True,
                    "invalid_existing_outputs_block_without_overwrite": True,
                    "execution_readiness_recomputed_live": bool(
                        failure_contrast_runner_summary.get(
                            "execution_readiness_all_jobs_pass"
                        )
                    ),
                    "approval_receipt_required": True,
                    "approval_receipt_path": failure_contrast_runner.get(
                        "approval_receipt_path"
                    )
                    or (
                        "reports/strategy_arbitration/"
                        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
                    ),
                    "approval_receipt_present": failure_contrast_runner_summary.get(
                        "approval_receipt_present"
                    ),
                    "approval_receipt_valid": failure_contrast_runner_summary.get(
                        "approval_receipt_valid"
                    ),
                    "approval_receipt_blockers": failure_contrast_runner_summary.get(
                        "approval_receipt_blockers"
                    ),
                    "approval_request_status": failure_contrast_approval_request.get(
                        "decision", {}
                    ).get("status"),
                    "approval_request_blockers": (
                        failure_contrast_approval_request.get("blockers") or []
                    ),
                    "approval_receipt_created_by_request": (
                        failure_contrast_approval_request.get(
                            "approval_receipt_created"
                        )
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
                        failure_contrast_runner_summary.get(
                            "execution_readiness_fingerprint"
                        )
                        or failure_contrast_execution_readiness.get("summary", {}).get(
                            "readiness_fingerprint"
                        )
                    ),
                    "readiness_checked_flag_count": readiness_boundaries.get(
                        "checked_flag_count"
                    ),
                    "readiness_boundary_violation_count": readiness_boundaries.get(
                        "violation_count"
                    ),
                    "readiness_source_artifact_count": len(
                        full_suite_readiness.get("source_artifacts") or {}
                    ),
                    "per_job_timeout_seconds": failure_contrast_runner_summary.get(
                        "job_timeout_seconds"
                    ),
                    "refresh_after_run": failure_contrast_runner_summary.get(
                        "refresh_after_run_requested"
                    ),
                    "processed_job_count": failure_contrast_runner_summary.get(
                        "processed_job_count"
                    ),
                    "executed_job_count": failure_contrast_runner_summary.get(
                        "executed_job_count"
                    ),
                    "output_valid_count": failure_contrast_runner_summary.get(
                        "output_valid_count"
                    ),
                    "runtime_authorization_row_count": failure_contrast_runner_summary.get(
                        "runtime_authorization_row_count"
                    ),
                    "stage7_training_row_count": failure_contrast_runner_summary.get(
                        "stage7_training_row_count"
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
                }
                if failure_contrast_ready_for_collection
                else None
            ),
            "what_it_does_not_allow": [
                "runtime selector",
                "runtime direct routing",
                "hidden Python controller",
                "runtime default changes",
                "runtime DTM or tablebase lookup",
                "gameplay-time topology mutation",
                "unreviewed or unbounded label execution",
                "selector training",
                "Stage 7 promotion",
                "Stage 8 training",
            ],
            "recommended_if": "manifest review passed and you want to collect bounded observation-only failure contrasts"
            if failure_contrast_manifest_review.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
            else "benchmark review found sparse protected plan-window failure evidence"
            if failure_contrast_plan.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
            else "Stage 7 held-out controls are sufficient and the benchmark now needs review"
            if sequence_inputs_ready
            else "already executed replay-free; remaining sequence-policy gap is Stage 7 clean success controls",
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_current_gate_summary",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json",
            "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_execution_readiness_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_runner_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.json",
            "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json",
            "reports/structural_candidates/stage7_additional_clean_sampling_runner_v0.json",
            "reports/krk_stage7_post_label_outcome_review_v0.json",
            "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json",
            "reports/strategy_arbitration/krk_cross_stage_plan_capsule_evidence_requirements_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_review_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_execution_readiness_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_runner_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_approval_request_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_output_validation_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_integration_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json",
            "reports/krk_full_suite_readiness_audit_v0.json",
        ],
        "current_state": {
            "protected_stack": protected_stack_status,
            "protected_stack_readiness_status": protected_stack.get("status"),
            "protected_stack_ready": protected_stack_ready,
            "protected_stack_rollback_paths_preserved": protected_stack.get(
                "rollback_paths_preserved"
            ),
            "protected_stack_active_paths_safe": active_stack_path_status.get(
                "all_paths_safe"
            ),
            "protected_stack_active_paths_exist": active_stack_path_status.get(
                "all_paths_exist"
            ),
            "protected_stack_rollback_paths_safe": rollback_stack_path_status.get(
                "all_paths_safe"
            ),
            "protected_stack_rollback_paths_exist": rollback_stack_path_status.get(
                "all_paths_exist"
            ),
            "protected_stack_rollback_common_paths_distinct": protected_stack.get(
                "rollback_common_paths_distinct"
            ),
            "protected_stack_filesystem_snapshots_replaced": protected_stack.get(
                "filesystem_snapshots_replaced"
            ),
            "protected_stack_hard_blockers": protected_stack_blockers,
            "readiness_checked_flag_count": readiness_boundaries.get(
                "checked_flag_count"
            ),
            "readiness_boundary_violation_count": readiness_boundaries.get(
                "violation_count"
            ),
            "readiness_source_artifact_count": len(
                full_suite_readiness.get("source_artifacts") or {}
            ),
            "stage4": "first_move_contrast_runtime_review_ready_pending_explicit_approval",
            "stage7": "heldout_clean_success_controls_ready_sequence_benchmark_available"
            if stage7_success_ready
            else "heldout_clean_success_controls_insufficient_sampling_manifest_ready",
            "stage7_success_controls_ready": stage7_success_ready,
            "stage7_success_controls": stage7_integration.get("summary", {}).get(
                "combined_success_controls"
            ),
            "stage7_success_controls_required": stage7_integration.get("summary", {}).get(
                "success_controls_required"
            ),
            "stage7_label_execution_readiness": current_stage7_execution_readiness_status
            or stage7_execution_readiness.get("decision", {}).get("status", "not_checked"),
            "stage7_label_historical_execution_readiness": (
                stage7_execution_readiness.get("decision", {}).get("status", "not_checked")
            ),
            "stage7_label_output_integration": stage7_integration.get("decision", {}).get(
                "status",
                "not_checked",
            ),
            "stage7_label_runner": stage7_runner.get("decision", {}).get(
                "status",
                "not_checked",
            ),
            "stage7_label_runner_output_validation_status": stage7_runner.get("summary", {}).get(
                "output_validation_status",
                "not_checked",
            ),
            "stage7_label_output_validation_status": stage7_output_validation.get(
                "decision", {}
            ).get("status", "not_checked"),
            "stage7_label_distribution_review": stage7_label_distribution_review.get(
                "decision", {}
            ).get("status", "not_checked"),
            "stage7_additional_label_manifest": stage7_additional_manifest.get(
                "decision", {}
            ).get("status", "not_checked"),
            "stage7_additional_label_runner": stage7_additional_runner.get(
                "decision", {}
            ).get("status", "not_checked"),
            "stage7_additional_label_runner_job_count": stage7_additional_runner.get(
                "summary", {}
            ).get("job_count"),
            "stage7_label_runner_execution_readiness_source": stage7_runner.get(
                "summary", {}
            ).get("execution_readiness_source"),
            "stage7_label_runner_execution_readiness_status": (
                current_stage7_execution_readiness_status
            ),
            "stage7_label_runner_historical_execution_readiness_status": (
                raw_stage7_execution_readiness_status
            ),
            "stage7_label_runner_execution_readiness_jobs_passing": stage7_runner.get(
                "summary", {}
            ).get("execution_readiness_jobs_passing"),
            "stage7_label_runner_invalid_existing_output_count": stage7_runner.get(
                "summary", {}
            ).get("invalid_existing_output_count"),
            "stage7_label_runner_processed_job_count": stage7_runner.get("summary", {}).get(
                "processed_job_count"
            ),
            "stage7_label_runner_executed_job_count": stage7_runner.get("summary", {}).get(
                "executed_job_count"
            ),
            "stage7_label_runner_historical_processed_job_count": stage7_runner.get(
                "summary", {}
            ).get(
                "historical_processed_job_count",
                stage7_runner.get("summary", {}).get("processed_job_count"),
            ),
            "stage7_label_runner_historical_executed_job_count": stage7_runner.get(
                "summary", {}
            ).get(
                "historical_executed_job_count",
                stage7_runner.get("summary", {}).get("executed_job_count"),
            ),
            "stage7_label_runner_skipped_existing_output_count": stage7_runner.get(
                "summary", {}
            ).get("skipped_existing_output_count"),
            "stage7_label_runner_job_timeout_seconds": stage7_runner.get(
                "summary", {}
            ).get("job_timeout_seconds"),
            "stage7_label_runner_timed_out_job_count": stage7_runner.get(
                "summary", {}
            ).get("timed_out_job_count"),
            "stage7_post_label_outcome": stage7_post_label_outcome.get("decision", {}).get(
                "status",
                "not_checked",
            ),
            "protected_plan_window_evidence": "available_non_causal"
            if protected_plan_window_met
            else "missing_or_underpowered",
            "sequence_policy": sequence_policy_status,
            "sequence_policy_passive_design_without_new_labels": (
                passive_sequence_design.get("status")
            ),
            "sequence_policy_passive_design_current_evidence_limit": (
                passive_sequence_design.get("current_evidence_limit")
            ),
            "sequence_policy_passive_design_depends_on_new_label_execution": (
                passive_sequence_design.get("depends_on_new_label_execution")
            ),
            "sequence_policy_passive_design_depends_on_protected_failure_contrast_collection": (
                passive_sequence_design.get(
                    "depends_on_protected_failure_contrast_collection"
                )
            ),
            "sequence_policy_cross_stage_requirements": (
                sequence_policy_cross_stage_requirements.get("decision", {}).get("status")
            ),
            "sequence_policy_replay_free_protected_cross_stage_evidence": (
                cross_stage_requirements_readiness.get(
                    "replay_free_protected_cross_stage_evidence"
                )
            ),
            "sequence_policy_cross_stage_sequence_evidence_met": (
                cross_stage_requirements_readiness.get("cross_stage_sequence_evidence_met")
            ),
            "sequence_policy_forbidden_training_or_runtime_input_blocked": (
                sequence_forbidden_training_or_runtime_inputs
            ),
            "sequence_policy_forbidden_training_or_runtime_input_blockers": (
                sequence_forbidden_input_blockers
            ),
            "protected_plan_window_failure_contrast_plan": failure_contrast_plan.get(
                "decision", {}
            ).get("status", "not_written"),
            "protected_plan_window_unique_failure_count": failure_contrast_plan.get(
                "summary", {}
            ).get("unique_failure_count"),
            "protected_plan_window_minimum_new_failures_needed": failure_contrast_plan.get(
                "summary", {}
            ).get("minimum_new_unique_failures_needed"),
            "protected_plan_window_failure_contrast_manifest": failure_contrast_manifest.get(
                "decision", {}
            ).get("status", "not_written"),
            "protected_plan_window_failure_contrast_manifest_job_count": failure_contrast_manifest.get(
                "summary", {}
            ).get("job_count"),
            "protected_plan_window_failure_contrast_manifest_review": failure_contrast_manifest_review.get(
                "decision", {}
            ).get("status", "not_written"),
            "protected_plan_window_failure_contrast_execution_readiness": failure_contrast_execution_readiness.get(
                "decision", {}
            ).get("status", "not_written"),
            "protected_plan_window_failure_contrast_execution_jobs_passing": failure_contrast_execution_readiness.get(
                "summary", {}
            ).get("jobs_passing_readiness"),
            "protected_plan_window_failure_contrast_runner": failure_contrast_runner.get(
                "decision", {}
            ).get("status", "not_written"),
            "protected_plan_window_failure_contrast_runner_processed_job_count": failure_contrast_runner.get(
                "summary", {}
            ).get("processed_job_count"),
            "protected_plan_window_failure_contrast_runner_executed_job_count": failure_contrast_runner.get(
                "summary", {}
            ).get("executed_job_count"),
            "protected_plan_window_failure_contrast_approval_request": failure_contrast_approval_request.get(
                "decision", {}
            ).get("status", "not_written"),
            "protected_plan_window_failure_contrast_approval_request_blockers": (
                failure_contrast_approval_request.get("blockers") or []
            ),
            "protected_plan_window_failure_contrast_approval_receipt_created": failure_contrast_approval_request.get(
                "approval_receipt_created"
            ),
            "protected_plan_window_failure_contrast_approval_receipt_blockers": failure_contrast_approval_request.get(
                "approval_receipt_blockers"
            ),
            "protected_plan_window_failure_contrast_post_success_refresh_required": (
                failure_contrast_approval_request_summary.get(
                    "post_success_refresh_required"
                )
            ),
            "protected_plan_window_failure_contrast_post_success_refresh_script": (
                failure_contrast_approval_request_summary.get(
                    "post_success_refresh_script"
                )
            ),
            "protected_plan_window_failure_contrast_post_success_refresh_scope": (
                failure_contrast_approval_request_summary.get(
                    "post_success_refresh_scope"
                )
            ),
            "protected_plan_window_failure_contrast_output_validation": failure_contrast_output_validation.get(
                "decision", {}
            ).get("status", "not_written"),
            "protected_plan_window_failure_contrast_output_exists_count": failure_contrast_output_validation.get(
                "summary", {}
            ).get("output_exists_count"),
            "protected_plan_window_failure_contrast_output_valid_count": failure_contrast_output_validation.get(
                "summary", {}
            ).get("output_valid_count"),
            "protected_plan_window_failure_contrast_integration": failure_contrast_integration.get(
                "decision", {}
            ).get("status", "not_written"),
            "protected_plan_window_failure_contrast_integrated_new_failure_count": failure_contrast_integration.get(
                "summary", {}
            ).get("integrated_new_failure_count"),
            "protected_plan_window_failure_contrast_integration_ready": failure_contrast_integration.get(
                "summary", {}
            ).get("integration_ready"),
            "sequence_policy_after_protected_failure_contrast_refresh": post_failure_contrast_sequence_refresh.get(
                "decision", {}
            ).get("status", "not_written"),
            "sequence_policy_after_protected_failure_contrast_rows": post_failure_contrast_sequence_refresh.get(
                "summary", {}
            ).get("protected_failure_contrast_row_count"),
            "sequence_policy_after_protected_failure_contrast_boundaries_preserved": post_failure_contrast_sequence_refresh_summary.get(
                "all_boundaries_preserved"
            ),
            "sequence_policy_after_protected_failure_contrast_boundary_violation_count": post_failure_contrast_sequence_refresh_summary.get(
                "boundary_violation_count"
            ),
            "sequence_policy_after_protected_failure_contrast_stage7_training_row_count": post_failure_contrast_sequence_refresh_summary.get(
                "stage7_training_row_count"
            ),
            "sequence_policy_after_protected_failure_contrast_selector_training_row_count": post_failure_contrast_sequence_refresh_summary.get(
                "selector_training_row_count"
            ),
            "sequence_policy_after_protected_failure_contrast_runtime_authorization_row_count": post_failure_contrast_sequence_refresh_summary.get(
                "runtime_authorization_row_count"
            ),
            "sequence_policy_inputs": sequence_policy_inputs.get("decision", {}).get(
                "status",
                "not_assembled",
            ),
            "stage8": "blocked",
            "runtime_selector": "blocked",
        },
        "approval_options": approval_options,
        "recommendation": {
            "preferred_next_if_no_user_approval": (
                "repair_protected_stack_validation"
            )
            if not protected_stack_ready
            else (
                "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
            )
            if sequence_forbidden_training_or_runtime_inputs
            else (
                failure_contrast_integration.get("decision", {}).get("recommended_next_step")
                or "refresh_non_causal_sequence_policy_benchmark_inputs_with_integrated_failure_contrasts"
            )
            if failure_contrast_integration_ready
            else "wait_for_explicit_protected_plan_window_failure_contrast_collection_approval"
            if failure_contrast_manifest_review.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
            else "review_protected_plan_window_failure_contrast_manifest"
            if failure_contrast_manifest.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_manifest_ready_for_review"
            else "review_protected_plan_window_failure_contrast_plan"
            if failure_contrast_plan.get("decision", {}).get("status")
            == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
            else "review_non_causal_sequence_policy_benchmark_results"
            if sequence_inputs_ready
            else "stop_at_gate_or_design_non_causal_sequence_policy_only",
            "preferred_next_if_user_approves_runtime": "implement_stage4_default_off_first_move_contrast_sandbox",
            "preferred_next_if_user_approves_collection": (
                "not_applicable_pending_protected_stack_validation"
            if not protected_stack_ready
            else "not_applicable_pending_sequence_policy_input_repair"
            if sequence_forbidden_training_or_runtime_inputs
            else "create_matching_approval_receipt_then_execute_bounded_protected_plan_window_failure_contrast_collection_from_reviewed_manifest"
            if failure_contrast_ready_for_collection
                else "not_applicable_pending_protected_failure_contrast_manifest_review"
            ),
            "preferred_next_if_user_approves_labels": "not_applicable_stage7_success_gate_closed"
            if stage7_success_ready
            else "run_stage7_additional_clean_sampling_manifest_and_recover_controls",
            "preferred_next_if_user_defers_both": "non_causal_sequence_policy_design_without_new_labels",
            "reason": (
                "Protected-stack validation is blocked or stale; repair rollback/path "
                "evidence before protected collection, runtime work, promotion, or "
                "Stage 8 training."
                if not protected_stack_ready
                else
                "Sequence-policy inputs contain forbidden training or runtime-authorization rows; "
                "input repair takes precedence over protected collection, runtime work, promotion, "
                "or Stage 8 training."
                if sequence_forbidden_training_or_runtime_inputs
                else
                "Stage 7 held-out clean controls now satisfy the benchmark gate; "
                "the remaining work is non-causal benchmark review/protected "
                "plan-window contrast analysis, while Stage 4 runtime work still "
                "requires explicit sandbox approval."
                if stage7_success_ready
                else (
                    "Replay-free protected plan-window evidence now satisfies the "
                    "Stage 4/5/6 cross-stage side. The remaining empirical blocker for "
                    "the sequence-policy benchmark is clean Stage 7 success controls, "
                    "while Stage 4 runtime work still requires explicit sandbox approval."
                )
            ),
        },
        "decision": {
            "status": "krk_control_plane_waiting_on_explicit_gate_choice",
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Current Control-Plane Gate v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "## Current State",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in payload["current_state"].items())
    lines.extend(["", "## Approval Options", ""])
    for option in payload["approval_options"]:
        lines.extend([
            f"### {option['option_id']}",
            "",
            f"- artifact: `{option['artifact']}`",
            f"- status: `{option['status']}`",
            f"- allows: {option['what_it_allows']}",
            f"- recommended_if: {option['recommended_if']}",
        ])
        if option.get("command_if_explicitly_approved"):
            lines.append(
                "- command_if_explicitly_approved: "
                f"`{option['command_if_explicitly_approved']}`"
            )
        if option.get("approval_request_artifact"):
            lines.append(
                "- approval_request_artifact: "
                f"`{option['approval_request_artifact']}`"
            )
        if option.get("approval_request_status"):
            lines.append(
                "- approval_request_status: "
                f"`{option['approval_request_status']}`"
            )
        if option.get("safety_scope"):
            lines.append("- safety_scope:")
            lines.extend(
                f"  - {key}: `{value}`" for key, value in option["safety_scope"].items()
            )
        lines.extend([
            "- does_not_allow:",
        ])
        lines.extend(f"  - {item}" for item in option["what_it_does_not_allow"])
        lines.append("")
    lines.extend([
        "## Recommendation",
        "",
        f"- if_no_user_approval: `{payload['recommendation']['preferred_next_if_no_user_approval']}`",
        f"- if_runtime_approved: `{payload['recommendation']['preferred_next_if_user_approves_runtime']}`",
        f"- if_collection_approved: `{payload['recommendation']['preferred_next_if_user_approves_collection']}`",
        f"- if_labels_approved: `{payload['recommendation']['preferred_next_if_user_approves_labels']}`",
        f"- reason: {payload['recommendation']['reason']}",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "approval_options": [option["option_id"] for option in payload["approval_options"]],
    }, indent=2))


if __name__ == "__main__":
    main()

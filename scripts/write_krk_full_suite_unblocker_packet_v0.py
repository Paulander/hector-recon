#!/usr/bin/env python3
"""Write the next KRK-suite unblocker packet from the readiness audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
STAGE4_UNBLOCKER = ROOT / "reports/krk_stage4_caveat_unblocker_packet_v0.json"
LABEL_DISTRIBUTION_REVIEW = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.json"
)
ADDITIONAL_MANIFEST = (
    ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
)
ADDITIONAL_RUNNER = (
    ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_runner_v0.json"
)
BENCHMARK_REVIEW = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
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
OUT_JSON = ROOT / "reports/krk_full_suite_unblocker_packet_v0.json"
OUT_MD = ROOT / "reports/krk_full_suite_unblocker_packet_v0.md"

DEFAULT_FAILURE_CONTRAST_APPROVAL_RECEIPT = (
    "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
)


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _load_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load(path)


def build_payload() -> dict[str, Any]:
    readiness = _load(READINESS)
    stage4_unblocker = _load(STAGE4_UNBLOCKER)
    label_distribution_review = _load_optional(LABEL_DISTRIBUTION_REVIEW)
    additional_manifest = _load_optional(ADDITIONAL_MANIFEST)
    additional_runner = _load_optional(ADDITIONAL_RUNNER)
    benchmark_review = _load_optional(BENCHMARK_REVIEW)
    failure_contrast_plan = _load_optional(FAILURE_CONTRAST_PLAN)
    failure_contrast_manifest = _load_optional(FAILURE_CONTRAST_MANIFEST)
    failure_contrast_manifest_review = _load_optional(FAILURE_CONTRAST_MANIFEST_REVIEW)
    failure_contrast_execution_readiness = _load_optional(
        FAILURE_CONTRAST_EXECUTION_READINESS
    )
    failure_contrast_runner = _load_optional(FAILURE_CONTRAST_RUNNER)
    failure_contrast_output_validation = _load_optional(FAILURE_CONTRAST_OUTPUT_VALIDATION)
    failure_contrast_integration = _load_optional(FAILURE_CONTRAST_INTEGRATION)
    post_failure_contrast_sequence_refresh = _load_optional(
        POST_FAILURE_CONTRAST_SEQUENCE_REFRESH
    )
    stage7_gate = readiness["stage7_sampling_gate"]
    sequence = readiness["sequence_policy"]
    protected = readiness["protected_stack"]
    stage4_decision = stage4_unblocker.get("decision") or {}
    sequence_forbidden_training_or_runtime_inputs = bool(
        sequence.get("forbidden_training_or_runtime_input_blocked")
    ) or (
        "sequence_policy_forbidden_training_or_runtime_rows"
        in set(readiness.get("hard_blockers") or [])
    )
    failure_contrast_primary = bool(
        stage7_gate["success_controls_ready"]
        and sequence["benchmark_ready"]
        and not sequence_forbidden_training_or_runtime_inputs
    )
    failure_contrast_manifest_summary = failure_contrast_manifest.get("summary", {})
    failure_contrast_constraints = failure_contrast_manifest.get(
        "collection_constraints", {}
    )
    failure_contrast_runner_summary = failure_contrast_runner.get("summary", {})
    failure_contrast_integration_ready = bool(
        failure_contrast_integration.get("summary", {}).get("integration_ready")
    )

    primary_ready = (
        stage7_gate["runner_status"] == "stage7_diverse_clean_sampling_runner_dry_run_ready"
        and stage7_gate["executed_job_count"] == 0
        and stage7_gate["success_controls_ready"] is False
        and not (stage7_gate.get("invalid_existing_output_count") or 0)
    )
    consumed_with_gap = (
        stage7_gate["runner_status"] == "stage7_diverse_clean_sampling_runner_executed_success"
        and stage7_gate["success_controls_ready"] is False
        and stage7_gate.get("outputs_present_count", 0) > 0
    )
    additional_ready = (
        consumed_with_gap
        and additional_manifest.get("decision", {}).get("status")
        == "stage7_additional_clean_sampling_manifest_ready_pending_explicit_approval"
        and additional_runner.get("decision", {}).get("status")
        == "stage7_additional_clean_sampling_runner_dry_run_ready"
    )
    job_timeout_seconds = int(stage7_gate.get("job_timeout_seconds") or 900)
    approved_command = (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_stage7_diverse_clean_sampling_jobs_v0.py "
        "--execute-reviewed-label-run "
        f"--job-timeout-seconds {job_timeout_seconds} "
        "--refresh-after-run"
    )
    additional_command = (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_stage7_additional_clean_sampling_jobs_v0.py "
        "--execute-reviewed-label-run "
        f"--job-timeout-seconds {job_timeout_seconds} "
        "--refresh-after-run"
    )
    failure_contrast_command = (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection "
        "--refresh-after-run "
        "--approval-receipt "
        f"{failure_contrast_runner.get('approval_receipt_path') or DEFAULT_FAILURE_CONTRAST_APPROVAL_RECEIPT}"
    )
    if sequence_forbidden_training_or_runtime_inputs:
        decision_status = "krk_suite_unblocker_blocked_forbidden_training_or_runtime_rows"
        recommended_next_step = "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    elif primary_ready:
        decision_status = "krk_suite_primary_unblocker_ready_pending_explicit_label_approval"
        recommended_next_step = "explicitly_approve_stage7_diverse_clean_label_execution"
    elif additional_ready:
        decision_status = (
            "krk_suite_additional_stage7_label_unblocker_ready_pending_explicit_approval"
        )
        recommended_next_step = "explicitly_approve_stage7_additional_clean_label_execution"
    elif stage7_gate["success_controls_ready"] and sequence["benchmark_ready"]:
        decision_status = (
            "krk_suite_protected_failure_contrast_unblocker_ready_pending_explicit_collection_approval"
        )
        recommended_next_step = (
            failure_contrast_integration.get("decision", {}).get("recommended_next_step")
            if failure_contrast_integration_ready
            else None
        ) or (
            failure_contrast_manifest_review.get("decision", {}).get("recommended_next_step")
            or failure_contrast_plan.get("decision", {}).get("recommended_next_step")
            or benchmark_review.get("decision", {}).get("recommended_next_step")
            or "review_non_causal_sequence_policy_benchmark_results"
        )
    elif consumed_with_gap:
        decision_status = "krk_suite_label_unblocker_consumed_pending_new_stage7_sampling_plan"
        recommended_next_step = (
            label_distribution_review.get("decision", {}).get("recommended_next_step")
            or "design_additional_stage7_clean_sampling_plan_for_remaining_success_gap"
        )
    else:
        decision_status = "krk_suite_primary_unblocker_not_ready"
        recommended_next_step = "inspect_current_readiness_gate"

    return {
        "schema_version": "krk_full_suite_unblocker_packet.v0",
        "causal_status": "non_causal_approval_packet",
        "source_artifacts": {
            "readiness_audit": "reports/krk_full_suite_readiness_audit_v0.json",
            "stage7_runner": (
                "reports/structural_candidates/stage7_diverse_clean_sampling_runner_v0.json"
            ),
            "stage4_gate": "reports/krk_current_control_plane_gate_v0.json",
            "stage4_unblocker": "reports/krk_stage4_caveat_unblocker_packet_v0.json",
            "label_distribution_review": (
                "reports/structural_candidates/"
                "stage7_diverse_clean_label_distribution_review_v0.json"
            ),
            "additional_sampling_manifest": (
                "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
            ),
            "additional_sampling_runner": (
                "reports/structural_candidates/stage7_additional_clean_sampling_runner_v0.json"
            ),
            "sequence_policy_benchmark_review": (
                "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
            ),
            "protected_plan_window_failure_contrast_plan": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_plan_v0.json"
            ),
            "protected_plan_window_failure_contrast_manifest": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_manifest_v0.json"
            ),
            "protected_plan_window_failure_contrast_manifest_review": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_manifest_review_v0.json"
            ),
            "protected_plan_window_failure_contrast_execution_readiness": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
            ),
            "protected_plan_window_failure_contrast_runner": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_runner_v0.json"
            ),
            "protected_plan_window_failure_contrast_output_validation": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_output_validation_v0.json"
            ),
            "protected_plan_window_failure_contrast_integration": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_integration_v0.json"
            ),
            "sequence_policy_after_protected_failure_contrast_refresh": (
                "reports/strategy_arbitration/"
                "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
            ),
        },
        "current_state": {
            "protected_stack_ready": protected["ready"],
            "stage7_success_controls": stage7_gate["combined_success_controls"],
            "stage7_success_controls_required": stage7_gate["success_controls_required"],
            "sequence_policy_inputs_ready": sequence["inputs_ready"],
            "sequence_policy_benchmark_ready": sequence["benchmark_ready"],
            "sequence_policy_forbidden_training_or_runtime_input_blocked": (
                sequence_forbidden_training_or_runtime_inputs
            ),
            "sequence_policy_forbidden_training_or_runtime_input_blockers": (
                sequence.get("forbidden_training_or_runtime_input_blockers") or []
            ),
            "stage8_training_ready": False,
            "stage7_output_validation_status": stage7_gate.get("output_validation_status"),
            "stage7_execution_readiness_source": stage7_gate.get(
                "execution_readiness_source"
            ),
            "stage7_execution_readiness_status": stage7_gate.get(
                "execution_readiness_status"
            ),
            "stage7_historical_execution_readiness_status": stage7_gate.get(
                "historical_execution_readiness_status"
            ),
            "stage7_execution_readiness_jobs_passing": stage7_gate.get(
                "execution_readiness_jobs_passing"
            ),
            "stage7_invalid_existing_output_count": stage7_gate.get(
                "invalid_existing_output_count"
            ),
            "stage7_job_timeout_seconds": stage7_gate.get("job_timeout_seconds"),
            "stage7_timed_out_job_count": stage7_gate.get("timed_out_job_count"),
            "stage7_overwrite_existing_outputs": stage7_gate.get(
                "overwrite_existing_outputs"
            ),
            "stage7_processed_job_count": stage7_gate.get("processed_job_count"),
            "stage7_executed_job_count": stage7_gate.get("executed_job_count"),
            "stage7_historical_processed_job_count": stage7_gate.get(
                "historical_processed_job_count",
                stage7_gate.get("processed_job_count"),
            ),
            "stage7_historical_executed_job_count": stage7_gate.get(
                "historical_executed_job_count",
                stage7_gate.get("executed_job_count"),
            ),
            "stage7_skipped_existing_output_count": stage7_gate.get(
                "skipped_existing_output_count"
            ),
            "stage7_label_distribution_review_status": label_distribution_review.get(
                "decision", {}
            ).get("status"),
            "stage7_label_distribution_review_next_step": label_distribution_review.get(
                "decision", {}
            ).get("recommended_next_step"),
            "stage7_label_distribution_unique_new_success": label_distribution_review.get(
                "summary", {}
            ).get("unique_new_success_key_count_vs_pre_run"),
            "stage7_label_distribution_duplicate_playouts": label_distribution_review.get(
                "summary", {}
            ).get("duplicate_playout_count"),
            "stage7_additional_clean_sampling_manifest_status": additional_manifest.get(
                "decision", {}
            ).get("status"),
            "stage7_additional_clean_sampling_runner_status": additional_runner.get(
                "decision", {}
            ).get("status"),
            "stage7_additional_clean_sampling_job_count": additional_runner.get(
                "summary", {}
            ).get("job_count"),
            "stage7_additional_clean_sampling_max_samples": additional_manifest.get(
                "summary", {}
            ).get("max_total_samples"),
            "protected_plan_window_failure_contrast_plan_status": failure_contrast_plan.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_unique_failure_count": failure_contrast_plan.get(
                "summary", {}
            ).get("unique_failure_count"),
            "protected_plan_window_minimum_new_failures_needed": failure_contrast_plan.get(
                "summary", {}
            ).get("minimum_new_unique_failures_needed"),
            "protected_plan_window_failure_contrast_manifest_status": failure_contrast_manifest.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_manifest_job_count": failure_contrast_manifest.get(
                "summary", {}
            ).get("job_count"),
            "protected_plan_window_failure_contrast_manifest_review_status": failure_contrast_manifest_review.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_execution_readiness_status": failure_contrast_execution_readiness.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_execution_jobs_passing": failure_contrast_execution_readiness.get(
                "summary", {}
            ).get("jobs_passing_readiness"),
            "protected_plan_window_failure_contrast_runner_status": failure_contrast_runner.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_runner_processed_job_count": failure_contrast_runner.get(
                "summary", {}
            ).get("processed_job_count"),
            "protected_plan_window_failure_contrast_runner_executed_job_count": failure_contrast_runner.get(
                "summary", {}
            ).get("executed_job_count"),
            "protected_plan_window_failure_contrast_output_validation_status": failure_contrast_output_validation.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_output_exists_count": failure_contrast_output_validation.get(
                "summary", {}
            ).get("output_exists_count"),
            "protected_plan_window_failure_contrast_output_valid_count": failure_contrast_output_validation.get(
                "summary", {}
            ).get("output_valid_count"),
            "protected_plan_window_failure_contrast_integration_status": failure_contrast_integration.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_integrated_new_failure_count": failure_contrast_integration.get(
                "summary", {}
            ).get("integrated_new_failure_count"),
            "protected_plan_window_failure_contrast_integration_ready": failure_contrast_integration.get(
                "summary", {}
            ).get("integration_ready"),
            "sequence_policy_after_protected_failure_contrast_refresh_status": post_failure_contrast_sequence_refresh.get(
                "decision", {}
            ).get("status"),
            "sequence_policy_after_protected_failure_contrast_rows": post_failure_contrast_sequence_refresh.get(
                "summary", {}
            ).get("protected_failure_contrast_row_count"),
        },
        "why_agent_stops_here": [
            (
                "The Stage 7 held-out clean label gate is closed; the remaining "
                "non-causal benchmark review identifies protected plan-window "
                "failure-contrast sparsity."
                if stage7_gate["success_controls_ready"]
                else "The next highest-value action creates new Stage 7 h40 labels or implements a reviewed runtime sandbox."
            ),
            "Runtime changes, Stage 7 promotion, and Stage 8 training remain gated by repository reports and architecture policy.",
            "The current /goal does not by itself authorize runtime behavior, Stage 7 promotion, or Stage 8 training.",
        ],
        "primary_unblocker": {
            "id": (
                "sequence_policy_input_repair"
                if sequence_forbidden_training_or_runtime_inputs
                else
                "stage7_additional_clean_label_execution"
                if additional_ready
                else "protected_plan_window_failure_contrast_collection"
                if failure_contrast_primary
                else "stage7_diverse_clean_label_execution"
            ),
            "status": (
                "blocked_forbidden_training_or_runtime_rows"
                if sequence_forbidden_training_or_runtime_inputs
                else "ready_pending_explicit_approval"
                if primary_ready
                else "additional_manifest_ready_pending_explicit_approval"
                if additional_ready
                else failure_contrast_manifest_review.get("decision", {}).get(
                    "status",
                    failure_contrast_plan.get("decision", {}).get(
                        "status",
                        benchmark_review.get("decision", {}).get("status", "ready_for_review"),
                    ),
                )
                if failure_contrast_primary
                else "consumed_gap_still_open_pending_new_label_plan"
                if consumed_with_gap
                else "not_ready"
            ),
            "purpose": (
                "Remove forbidden selector-training or runtime-authorization rows from passive sequence-policy inputs before any protected collection review."
                if sequence_forbidden_training_or_runtime_inputs
                else
                "Review the bounded protected plan-window failure-contrast manifest before any explicitly approved collection run."
                if failure_contrast_primary
                else "Fill held-out Stage 7 clean success controls so the sequence-policy benchmark can run."
            ),
            "command_if_explicitly_approved": None
            if sequence_forbidden_training_or_runtime_inputs
            or failure_contrast_primary
            and failure_contrast_runner.get("decision", {}).get("status")
            != "protected_plan_window_failure_contrast_runner_dry_run_ready"
            else failure_contrast_command
            if failure_contrast_primary
            else additional_command
            if additional_ready
            else approved_command,
            "scope": {
                "max_jobs": (
                    0
                    if sequence_forbidden_training_or_runtime_inputs
                    else failure_contrast_manifest_summary.get("job_count")
                    if failure_contrast_primary
                    else additional_manifest.get("summary", {}).get("job_count")
                    if additional_ready
                    else 8
                ),
                "horizon": (
                    f"h{failure_contrast_constraints.get('horizon')}"
                    if failure_contrast_primary
                    and failure_contrast_constraints.get("horizon")
                    else "h40"
                ),
                "stage": (
                    "sequence_policy_input_repair_only"
                    if sequence_forbidden_training_or_runtime_inputs
                    else "protected_plan_window_failure_contrast_evidence_only"
                    if failure_contrast_primary
                    else "stage7_held_out_evidence_only"
                ),
                "source_stage_counts": (
                    failure_contrast_manifest_summary.get("source_stage_counts")
                    if failure_contrast_primary
                    else None
                ),
                "stop_after_unique_failures": (
                    failure_contrast_constraints.get("stop_after_unique_failures")
                    if failure_contrast_primary
                    else None
                ),
                "observation_only": (
                    bool(failure_contrast_constraints.get("observation_only"))
                    if failure_contrast_primary
                    else None
                ),
                "resume_safe": True,
                "skip_existing_outputs_by_default": True,
                "invalid_existing_outputs_block_without_overwrite": True,
                "execution_readiness_recomputed_live": (
                    failure_contrast_runner_summary.get(
                        "execution_readiness_all_jobs_pass"
                    )
                    if failure_contrast_primary
                    else stage7_gate.get("execution_readiness_source")
                    == "live_recomputed"
                ),
                "per_job_timeout_seconds": (
                    failure_contrast_runner_summary.get("job_timeout_seconds")
                    if failure_contrast_primary
                    else job_timeout_seconds
                ),
                "approval_receipt_required": (
                    True if failure_contrast_primary else None
                ),
                "approval_receipt_path": (
                    failure_contrast_runner.get("approval_receipt_path")
                    or DEFAULT_FAILURE_CONTRAST_APPROVAL_RECEIPT
                    if failure_contrast_primary
                    else None
                ),
                "approval_receipt_present": (
                    failure_contrast_runner_summary.get("approval_receipt_present")
                    if failure_contrast_primary
                    else None
                ),
                "approval_receipt_valid": (
                    failure_contrast_runner_summary.get("approval_receipt_valid")
                    if failure_contrast_primary
                    else None
                ),
                "expected_manifest_fingerprint": (
                    failure_contrast_runner_summary.get(
                        "execution_readiness_manifest_fingerprint"
                    )
                    or failure_contrast_execution_readiness.get("summary", {}).get(
                        "manifest_fingerprint"
                    )
                    if failure_contrast_primary
                    else None
                ),
                "expected_readiness_fingerprint": (
                    failure_contrast_runner_summary.get(
                        "execution_readiness_fingerprint"
                    )
                    or failure_contrast_execution_readiness.get("summary", {}).get(
                        "readiness_fingerprint"
                    )
                    if failure_contrast_primary
                    else None
                ),
                "timed_out_job_count": (
                    failure_contrast_runner_summary.get("timed_out_job_count", 0)
                    if failure_contrast_primary
                    else stage7_gate.get("timed_out_job_count")
                ),
                "post_success_refresh": "full_passive_krk_suite_gate_stack",
                "runtime_behavior_changed": False,
                "stage7_training_rows": 0,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "approval_required": (
                bool(
                    failure_contrast_plan.get("decision", {}).get(
                        "approval_required_before_label_execution"
                    )
                    or failure_contrast_manifest_review.get("decision", {}).get(
                        "approval_required_before_collection"
                    )
                )
                if stage7_gate["success_controls_ready"] and sequence["benchmark_ready"]
                and not sequence_forbidden_training_or_runtime_inputs
                else True
            ),
            "implementation_allowed_by_this_packet": False,
        },
        "secondary_unblocker": {
            "id": "stage4_first_move_contrast_sandbox",
            "status": stage4_decision.get("status"),
            "purpose": "Address the separate Stage 4 h40 caveat through a reviewed default-off sandbox path.",
            "why_secondary": (
                "This may reduce Stage 4 debt, but it does not directly fill the protected "
                "plan-window failure-contrast sparsity now blocking sequence-policy review."
            ),
            "approval_required": True,
            "implementation_allowed_by_this_packet": bool(
                stage4_decision.get("implementation_allowed_by_this_packet")
            ),
        },
        "low_value_safe_work_remaining": [
            (
                "Rerunning Stage 7 label commands without overwrite will skip existing outputs; "
                "the Stage 7 success-control gap is already closed."
                if stage7_gate["success_controls_ready"]
                else "Rerunning the original Stage 7 command without overwrite will skip existing outputs and will not fill the remaining unique success-control gap."
            ),
            (
                "More passive summaries can be written, but the next useful work is benchmark review or protected plan-window failure-contrast collection."
                if sequence["benchmark_ready"]
                else "More passive summaries can be written, but they will not unblock Stage 8 or the sequence-policy benchmark."
            ),
        ],
        "decision": {
            "status": decision_status,
            "recommended_next_step": recommended_next_step,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    primary = payload["primary_unblocker"]
    secondary = payload["secondary_unblocker"]
    state = payload["current_state"]
    lines = [
        "# KRK Full Suite Unblocker Packet v0",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        f"- implementation_allowed_by_this_packet: `{primary['implementation_allowed_by_this_packet']}`",
        f"- label_run_allowed: `{decision['label_run_allowed']}`",
        f"- runtime_changes_allowed: `{decision['runtime_changes_allowed']}`",
        "",
        "## Current State",
        "",
        f"- protected_stack_ready: `{state['protected_stack_ready']}`",
        f"- stage7_success_controls: `{state['stage7_success_controls']}`",
        f"- stage7_success_controls_required: `{state['stage7_success_controls_required']}`",
        f"- sequence_policy_inputs_ready: `{state['sequence_policy_inputs_ready']}`",
        f"- sequence_policy_benchmark_ready: `{state['sequence_policy_benchmark_ready']}`",
        f"- stage8_training_ready: `{state['stage8_training_ready']}`",
        f"- stage7_output_validation_status: `{state['stage7_output_validation_status']}`",
        f"- stage7_invalid_existing_output_count: `{state['stage7_invalid_existing_output_count']}`",
        f"- stage7_overwrite_existing_outputs: `{state['stage7_overwrite_existing_outputs']}`",
        f"- stage7_processed_job_count: `{state['stage7_processed_job_count']}`",
        f"- stage7_executed_job_count: `{state['stage7_executed_job_count']}`",
        f"- stage7_historical_processed_job_count: `{state['stage7_historical_processed_job_count']}`",
        f"- stage7_historical_executed_job_count: `{state['stage7_historical_executed_job_count']}`",
        f"- stage7_skipped_existing_output_count: `{state['stage7_skipped_existing_output_count']}`",
        f"- stage7_label_distribution_review_status: `{state['stage7_label_distribution_review_status']}`",
        f"- stage7_label_distribution_unique_new_success: `{state['stage7_label_distribution_unique_new_success']}`",
        f"- stage7_label_distribution_duplicate_playouts: `{state['stage7_label_distribution_duplicate_playouts']}`",
        f"- stage7_additional_clean_sampling_manifest_status: `{state['stage7_additional_clean_sampling_manifest_status']}`",
        f"- stage7_additional_clean_sampling_runner_status: `{state['stage7_additional_clean_sampling_runner_status']}`",
        f"- stage7_additional_clean_sampling_job_count: `{state['stage7_additional_clean_sampling_job_count']}`",
        f"- protected_plan_window_failure_contrast_plan_status: `{state['protected_plan_window_failure_contrast_plan_status']}`",
        f"- protected_plan_window_unique_failure_count: `{state['protected_plan_window_unique_failure_count']}`",
        f"- protected_plan_window_minimum_new_failures_needed: `{state['protected_plan_window_minimum_new_failures_needed']}`",
        f"- protected_plan_window_failure_contrast_manifest_status: `{state['protected_plan_window_failure_contrast_manifest_status']}`",
        f"- protected_plan_window_failure_contrast_manifest_job_count: `{state['protected_plan_window_failure_contrast_manifest_job_count']}`",
        f"- protected_plan_window_failure_contrast_manifest_review_status: `{state['protected_plan_window_failure_contrast_manifest_review_status']}`",
        f"- protected_plan_window_failure_contrast_execution_readiness_status: `{state['protected_plan_window_failure_contrast_execution_readiness_status']}`",
        f"- protected_plan_window_failure_contrast_execution_jobs_passing: `{state['protected_plan_window_failure_contrast_execution_jobs_passing']}`",
        f"- protected_plan_window_failure_contrast_runner_status: `{state['protected_plan_window_failure_contrast_runner_status']}`",
        f"- protected_plan_window_failure_contrast_runner_processed_job_count: `{state['protected_plan_window_failure_contrast_runner_processed_job_count']}`",
        f"- protected_plan_window_failure_contrast_runner_executed_job_count: `{state['protected_plan_window_failure_contrast_runner_executed_job_count']}`",
        f"- protected_plan_window_failure_contrast_output_validation_status: `{state['protected_plan_window_failure_contrast_output_validation_status']}`",
        f"- protected_plan_window_failure_contrast_output_exists_count: `{state['protected_plan_window_failure_contrast_output_exists_count']}`",
        f"- protected_plan_window_failure_contrast_output_valid_count: `{state['protected_plan_window_failure_contrast_output_valid_count']}`",
        f"- protected_plan_window_failure_contrast_integration_status: `{state['protected_plan_window_failure_contrast_integration_status']}`",
        f"- protected_plan_window_failure_contrast_integrated_new_failure_count: `{state['protected_plan_window_failure_contrast_integrated_new_failure_count']}`",
        f"- protected_plan_window_failure_contrast_integration_ready: `{state['protected_plan_window_failure_contrast_integration_ready']}`",
        f"- sequence_policy_after_protected_failure_contrast_refresh_status: `{state['sequence_policy_after_protected_failure_contrast_refresh_status']}`",
        f"- sequence_policy_after_protected_failure_contrast_rows: `{state['sequence_policy_after_protected_failure_contrast_rows']}`",
        "",
        "## Why Work Stops At This Gate",
        "",
    ]
    for reason in payload["why_agent_stops_here"]:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Primary Unblocker",
            "",
            f"- id: `{primary['id']}`",
            f"- status: `{primary['status']}`",
            f"- purpose: {primary['purpose']}",
            f"- command_if_explicitly_approved: `{primary['command_if_explicitly_approved']}`",
            f"- max_jobs: `{primary['scope']['max_jobs']}`",
            f"- horizon: `{primary['scope']['horizon']}`",
            f"- stage: `{primary['scope']['stage']}`",
            f"- stop_after_unique_failures: `{primary['scope']['stop_after_unique_failures']}`",
            f"- observation_only: `{primary['scope']['observation_only']}`",
            f"- resume_safe: `{primary['scope']['resume_safe']}`",
            f"- skip_existing_outputs_by_default: `{primary['scope']['skip_existing_outputs_by_default']}`",
            f"- invalid_existing_outputs_block_without_overwrite: `{primary['scope']['invalid_existing_outputs_block_without_overwrite']}`",
            f"- per_job_timeout_seconds: `{primary['scope']['per_job_timeout_seconds']}`",
            f"- approval_receipt_required: `{primary['scope']['approval_receipt_required']}`",
            f"- approval_receipt_path: `{primary['scope']['approval_receipt_path']}`",
            f"- approval_receipt_present: `{primary['scope']['approval_receipt_present']}`",
            f"- approval_receipt_valid: `{primary['scope']['approval_receipt_valid']}`",
            f"- expected_manifest_fingerprint: `{primary['scope']['expected_manifest_fingerprint']}`",
            f"- expected_readiness_fingerprint: `{primary['scope']['expected_readiness_fingerprint']}`",
            f"- post_success_refresh: `{primary['scope']['post_success_refresh']}`",
            f"- stage7_training_rows: `{primary['scope']['stage7_training_rows']}`",
            f"- approval_required: `{primary['approval_required']}`",
            f"- implementation_allowed_by_this_packet: `{primary['implementation_allowed_by_this_packet']}`",
            "",
            "## Secondary Unblocker",
            "",
            f"- id: `{secondary['id']}`",
            f"- status: `{secondary['status']}`",
            f"- purpose: {secondary['purpose']}",
            f"- why_secondary: {secondary['why_secondary']}",
            "",
            "## Low-Value Safe Work Remaining",
            "",
        ]
    )
    for item in payload["low_value_safe_work_remaining"]:
        lines.append(f"- {item}")
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

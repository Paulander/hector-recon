#!/usr/bin/env python3
"""Review the post-label outcome after Stage 7 diverse-clean sampling.

This is a passive decision router. It never executes labels, trains, changes
runtime behavior, promotes Stage 7, or trains Stage 8. Its purpose is to make
the next post-approval branch explicit once the approval-gated Stage 7 clean
label run has produced, partially produced, or failed to produce outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_VALIDATION = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
)
INTEGRATION = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json"
)
PIPELINE = ROOT / "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json"
BENCHMARK_REVIEW = (
    ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
)
READINESS = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
STAGE8_REVIEW = ROOT / "reports/krk_stage8_training_readiness_review_v0.json"
OUT_JSON = ROOT / "reports/krk_stage7_post_label_outcome_review_v0.json"
OUT_MD = ROOT / "reports/krk_stage7_post_label_outcome_review_v0.md"

SCHEMA_VERSION = "krk_stage7_post_label_outcome_review.v0"

FORBIDDEN_INPUT_BLOCKERS = {
    "selector_training_rows_forbidden",
    "runtime_authorization_rows_forbidden",
    "sequence_policy_forbidden_training_or_runtime_rows",
}

FORBIDDEN_INPUT_STATUSES = {
    "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows",
    "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows",
    "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows",
    "stage8_training_blocked_forbidden_training_or_runtime_rows",
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
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def build_payload(
    *,
    output_validation: dict[str, Any] | None = None,
    integration: dict[str, Any] | None = None,
    pipeline: dict[str, Any] | None = None,
    benchmark_review: dict[str, Any] | None = None,
    readiness: dict[str, Any] | None = None,
    stage8_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_validation = output_validation or _load(OUTPUT_VALIDATION)
    integration = integration or _load(INTEGRATION)
    pipeline = pipeline or _load(PIPELINE)
    benchmark_review = benchmark_review or _load(BENCHMARK_REVIEW)
    readiness = readiness or _load(READINESS)
    stage8_review = stage8_review or _load(STAGE8_REVIEW)

    validation_status = (output_validation.get("decision") or {}).get("status")
    integration_status = (integration.get("decision") or {}).get("status")
    pipeline_status = (pipeline.get("decision") or {}).get("status")
    benchmark_review_status = (benchmark_review.get("decision") or {}).get("status")
    readiness_status = (readiness.get("decision") or {}).get("status")
    stage8_status = (stage8_review.get("decision") or {}).get("status")
    protected_failure_contrast = readiness.get("protected_failure_contrast_gate") or {}
    readiness_boundaries = readiness.get("runtime_and_training_boundaries") or {}
    explicit_gate_blockers = set(readiness.get("explicit_gate_blockers") or [])
    hard_blockers = set(readiness.get("hard_blockers") or [])
    sequence_policy = readiness.get("sequence_policy") or {}
    post_failure_contrast_refresh_boundaries_preserved = sequence_policy.get(
        "post_failure_contrast_refresh_boundaries_preserved"
    )
    post_failure_contrast_refresh_boundary_violation_count = sequence_policy.get(
        "post_failure_contrast_refresh_boundary_violation_count"
    )
    benchmark_review_blockers = set(benchmark_review.get("blockers") or [])
    protected_failure_contrast_pending_approval = (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        in explicit_gate_blockers
    )

    validation_summary = output_validation.get("summary") or {}
    integration_summary = integration.get("summary") or {}
    readiness_stage7 = readiness.get("stage7_sampling_gate") or {}

    outputs_present = int(validation_summary.get("output_exists_count") or 0)
    outputs_valid = int(validation_summary.get("output_valid_count") or 0)
    invalid_outputs = max(outputs_present - outputs_valid, 0)
    success_controls = int(integration_summary.get("combined_success_controls") or 0)
    success_required = int(integration_summary.get("success_controls_required") or 5)
    failure_controls = int(integration_summary.get("combined_failure_controls") or 0)
    failure_required = int(integration_summary.get("failure_controls_required") or 5)
    success_controls_met = bool(integration_summary.get("success_controls_met"))
    failure_controls_met = bool(integration_summary.get("failure_controls_met"))
    benchmark_inputs_ready = bool((pipeline.get("summary") or {}).get("sequence_policy_inputs_ready"))
    stage8_training_ready = stage8_status == "stage8_training_review_ready_pending_explicit_approval"
    forbidden_input_blockers = sorted(
        FORBIDDEN_INPUT_BLOCKERS
        & (
            hard_blockers
            | benchmark_review_blockers
            | set(sequence_policy.get("benchmark_preflight_blockers") or [])
            | set(sequence_policy.get("benchmark_review_blockers") or [])
            | set(sequence_policy.get("forbidden_training_or_runtime_input_blockers") or [])
        )
    )
    sequence_forbidden_training_or_runtime_inputs = (
        bool(forbidden_input_blockers)
        or bool(sequence_policy.get("forbidden_training_or_runtime_input_blocked"))
        or readiness_status in FORBIDDEN_INPUT_STATUSES
        or benchmark_review_status in FORBIDDEN_INPUT_STATUSES
        or stage8_status in FORBIDDEN_INPUT_STATUSES
    )

    blockers: list[str] = []
    findings: list[str] = []

    if validation_status == "stage7_diverse_clean_sampling_outputs_validation_pending":
        blockers.append("stage7_diverse_clean_outputs_absent")
        status = "post_label_outcome_pending_explicit_label_outputs"
        next_step = "explicitly_approve_stage7_diverse_clean_label_execution"
    elif validation_status == "stage7_diverse_clean_sampling_outputs_invalid_block_integration":
        blockers.append("stage7_diverse_clean_outputs_invalid")
        status = "post_label_outcome_invalid_outputs_block_integration"
        next_step = "inspect_or_clean_invalid_stage7_outputs_then_rerun_validation"
    elif not success_controls_met:
        blockers.append("stage7_clean_success_controls_still_missing")
        findings.append("label_outputs_present_but_success_controls_underpowered")
        status = "post_label_outcome_success_controls_still_underpowered"
        next_step = "review_stage7_label_distribution_before_any_additional_label_manifest"
    elif not failure_controls_met:
        blockers.append("stage7_clean_failure_controls_missing")
        findings.append("success_controls_met_failure_controls_underpowered")
        status = "post_label_outcome_failure_controls_underpowered"
        next_step = "review_stage7_failure_control_gap_before_any_additional_labels"
    elif not benchmark_inputs_ready:
        blockers.append("sequence_policy_inputs_not_ready_after_controls")
        status = "post_label_outcome_controls_met_pipeline_not_ready"
        next_step = "inspect_sequence_policy_pipeline_refresh"
    elif sequence_forbidden_training_or_runtime_inputs:
        blockers.append("sequence_policy_forbidden_training_or_runtime_rows")
        status = "post_label_outcome_blocked_forbidden_training_or_runtime_rows"
        next_step = "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    elif benchmark_review_status == "sequence_policy_benchmark_supports_non_causal_sequence_policy_review":
        findings.append("sequence_policy_benchmark_supportive")
        if stage8_training_ready:
            status = "post_label_outcome_stage8_training_review_ready"
            next_step = "write_explicit_stage8_training_review_packet"
        else:
            status = "post_label_outcome_sequence_policy_review_ready_stage8_blocked"
            next_step = "inspect_stage8_training_readiness_review"
    elif benchmark_review_status == "sequence_policy_benchmark_mixed_plan_window_underpowered":
        if protected_failure_contrast_pending_approval:
            blockers.append(
                "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
            )
            findings.append("protected_plan_window_failure_contrast_gate_ready_for_approval")
            status = (
                "post_label_outcome_waiting_on_explicit_protected_failure_contrast_collection"
            )
        else:
            blockers.append("protected_plan_window_failure_evidence_sparse")
            status = "post_label_outcome_sequence_policy_mixed_plan_window_underpowered"
        next_step = "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    elif benchmark_review_status == "sequence_policy_benchmark_review_blocked_pending_ready_inputs":
        blockers.append("sequence_policy_benchmark_review_not_ready")
        status = "post_label_outcome_benchmark_review_still_blocked"
        next_step = "rerun_passive_gate_advancement_or_inspect_benchmark_preflight"
    else:
        blockers.append("post_label_outcome_needs_manual_architecture_review")
        status = "post_label_outcome_manual_review_required"
        next_step = "inspect_sequence_policy_and_stage8_reviews"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_post_label_outcome_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
            "reports/krk_full_suite_readiness_audit_v0.json",
            "reports/krk_stage8_training_readiness_review_v0.json",
        ],
        "summary": {
            "output_validation_status": validation_status,
            "integration_status": integration_status,
            "pipeline_status": pipeline_status,
            "benchmark_review_status": benchmark_review_status,
            "readiness_status": readiness_status,
            "readiness_checked_flag_count": readiness_boundaries.get(
                "checked_flag_count"
            ),
            "readiness_boundary_violation_count": readiness_boundaries.get(
                "violation_count"
            ),
            "readiness_source_artifact_count": len(
                readiness.get("source_artifacts") or {}
            ),
            "stage8_status": stage8_status,
            "outputs_present_count": outputs_present,
            "outputs_valid_count": outputs_valid,
            "invalid_output_count": invalid_outputs,
            "success_controls": success_controls,
            "success_controls_required": success_required,
            "success_controls_met": success_controls_met,
            "failure_controls": failure_controls,
            "failure_controls_required": failure_required,
            "failure_controls_met": failure_controls_met,
            "sequence_policy_inputs_ready": benchmark_inputs_ready,
            "sequence_policy_forbidden_training_or_runtime_input_blocked": (
                sequence_forbidden_training_or_runtime_inputs
            ),
            "sequence_policy_forbidden_training_or_runtime_input_blockers": (
                forbidden_input_blockers
            ),
            "sequence_policy_after_protected_failure_contrast_refresh_status": (
                sequence_policy.get("post_failure_contrast_refresh_status")
            ),
            "sequence_policy_after_protected_failure_contrast_boundaries_preserved": (
                post_failure_contrast_refresh_boundaries_preserved
            ),
            "sequence_policy_after_protected_failure_contrast_boundary_violation_count": (
                post_failure_contrast_refresh_boundary_violation_count
            ),
            "sequence_policy_after_protected_failure_contrast_rows": (
                sequence_policy.get("post_failure_contrast_refresh_row_count")
            ),
            "sequence_policy_after_protected_failure_contrast_stage7_training_row_count": (
                sequence_policy.get(
                    "post_failure_contrast_refresh_stage7_training_row_count"
                )
            ),
            "stage7_runner_invalid_existing_output_count": readiness_stage7.get(
                "invalid_existing_output_count"
            ),
            "protected_failure_contrast_ready_for_explicit_approval": (
                protected_failure_contrast.get("ready_for_explicit_approval")
            ),
            "protected_failure_contrast_integration_ready": (
                protected_failure_contrast.get("integration_ready")
            ),
            "protected_failure_contrast_runner_status": protected_failure_contrast.get(
                "runner_status"
            ),
            "protected_failure_contrast_runner_processed_job_count": (
                protected_failure_contrast.get("runner_processed_job_count")
            ),
            "protected_failure_contrast_runner_executed_job_count": (
                protected_failure_contrast.get("runner_executed_job_count")
            ),
            "protected_failure_contrast_command_if_explicitly_approved": (
                protected_failure_contrast.get("command_if_explicitly_approved")
            ),
            "protected_failure_contrast_approval_request_artifact": (
                protected_failure_contrast.get("approval_request_artifact")
            ),
            "protected_failure_contrast_approval_request_status": (
                protected_failure_contrast.get("approval_request_status")
            ),
            "protected_failure_contrast_approval_request_blockers": (
                protected_failure_contrast.get("approval_request_blockers") or []
            ),
            "protected_failure_contrast_approval_receipt_created_by_request": (
                protected_failure_contrast.get("approval_receipt_created_by_request")
            ),
            "protected_failure_contrast_approval_receipt_blockers": (
                protected_failure_contrast.get("approval_receipt_blockers") or []
            ),
            "protected_failure_contrast_post_success_refresh_required": (
                protected_failure_contrast.get("post_success_refresh_required")
            ),
            "protected_failure_contrast_post_success_refresh_script": (
                protected_failure_contrast.get("post_success_refresh_script")
            ),
            "protected_failure_contrast_post_success_refresh_scope": (
                protected_failure_contrast.get("post_success_refresh_scope")
            ),
            "protected_failure_contrast_runtime_behavior_changed": (
                protected_failure_contrast.get("runtime_behavior_changed", False)
            ),
            "protected_failure_contrast_runtime_defaults_changed": (
                protected_failure_contrast.get("runtime_defaults_changed", False)
            ),
            "protected_failure_contrast_runtime_selector_implemented": (
                protected_failure_contrast.get("runtime_selector_implemented", False)
            ),
            "protected_failure_contrast_runtime_score_changes": (
                protected_failure_contrast.get("runtime_score_changes", False)
            ),
            "protected_failure_contrast_runtime_direct_routing": (
                protected_failure_contrast.get("runtime_direct_routing", False)
            ),
            "protected_failure_contrast_runtime_dtm_or_tablebase_lookup": (
                protected_failure_contrast.get("runtime_dtm_or_tablebase_lookup", False)
            ),
            "protected_failure_contrast_hidden_python_controller": (
                protected_failure_contrast.get("hidden_python_controller", False)
            ),
            "protected_failure_contrast_gameplay_topology_mutation": (
                protected_failure_contrast.get("gameplay_topology_mutation", False)
            ),
            "protected_failure_contrast_selector_training_allowed": (
                protected_failure_contrast.get("selector_training_allowed", False)
            ),
            "protected_failure_contrast_stage7_promotion_allowed": (
                protected_failure_contrast.get("stage7_promotion_allowed", False)
            ),
            "protected_failure_contrast_stage8_training_allowed": (
                protected_failure_contrast.get("stage8_training_allowed", False)
            ),
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "findings": findings,
        "blockers": blockers,
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "implementation_allowed_by_this_review": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    lines = [
        "# KRK Stage 7 Post-Label Outcome Review v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This review is passive. It does not execute labels, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Findings", ""])
    if payload["findings"]:
        for finding in payload["findings"]:
            lines.append(f"- `{finding}`")
    else:
        lines.append("- none")
    lines.extend(["", "## Blockers", ""])
    if payload["blockers"]:
        for blocker in payload["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            f"- implementation_allowed_by_this_review: `{decision['implementation_allowed_by_this_review']}`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- stage7_promotion_allowed: `false`",
            "- stage8_training_allowed: `false`",
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

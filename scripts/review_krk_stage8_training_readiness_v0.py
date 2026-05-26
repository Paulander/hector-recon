#!/usr/bin/env python3
"""Review whether KRK Stage 8 training is ready for explicit approval.

This is a passive review gate. It never trains Stage 8 and never promotes
Stage 7. Its purpose is to make the downstream requirements explicit once the
Stage 7 held-out controls and sequence-policy benchmark are ready.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
BENCHMARK_REVIEW = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
OUTPUT_JSON = ROOT / "reports/krk_stage8_training_readiness_review_v0.json"
OUTPUT_MD = ROOT / "reports/krk_stage8_training_readiness_review_v0.md"

SCHEMA_VERSION = "krk_stage8_training_readiness_review.v0"

FORBIDDEN_INPUT_BLOCKERS = {
    "selector_training_rows_forbidden",
    "runtime_authorization_rows_forbidden",
    "sequence_policy_forbidden_training_or_runtime_rows",
}

FORBIDDEN_INPUT_STATUSES = {
    "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows",
    "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows",
    "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows",
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
    readiness: dict[str, Any] | None = None,
    benchmark_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    readiness = readiness or _load(READINESS)
    benchmark_review = benchmark_review or _load(BENCHMARK_REVIEW)

    protected = readiness.get("protected_stack") or {}
    stage_status = readiness.get("stage_status") or {}
    stage7 = stage_status.get("stage7") or {}
    stage4 = stage_status.get("stage4") or {}
    protected_failure_contrast = readiness.get("protected_failure_contrast_gate") or {}
    readiness_boundaries = readiness.get("runtime_and_training_boundaries") or {}
    explicit_gate_blockers = set(readiness.get("explicit_gate_blockers") or [])
    hard_blockers = set(readiness.get("hard_blockers") or [])
    sequence_policy = readiness.get("sequence_policy") or {}
    sequence_decision = benchmark_review.get("decision") or {}
    benchmark_review_blockers = set(benchmark_review.get("blockers") or [])

    protected_ready = bool(protected.get("ready"))
    stage7_controls_ready = bool(stage7.get("success_controls_ready"))
    stage7_promoted = bool(stage7.get("ready_for_promotion"))
    sequence_review_ready = sequence_decision.get("status") in {
        "sequence_policy_benchmark_supports_non_causal_sequence_policy_review",
        "sequence_policy_benchmark_mixed_plan_window_underpowered",
    }
    sequence_review_supportive = (
        sequence_decision.get("status")
        == "sequence_policy_benchmark_supports_non_causal_sequence_policy_review"
    )
    protected_failure_contrast_request_status = protected_failure_contrast.get(
        "approval_request_status"
    )
    protected_failure_contrast_request_blockers = (
        protected_failure_contrast.get("approval_request_blockers") or []
    )
    protected_failure_contrast_request_ready_value = protected_failure_contrast.get(
        "approval_request_ready_for_collection"
    )
    protected_failure_contrast_request_ready = (
        bool(protected_failure_contrast_request_ready_value)
        if protected_failure_contrast_request_ready_value is not None
        else (
            not protected_failure_contrast_request_blockers
            and protected_failure_contrast_request_status
            in (None, "protected_plan_window_failure_contrast_approval_request_ready")
        )
    )
    protected_failure_contrast_collection_blocker = (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        in explicit_gate_blockers
    )
    protected_failure_contrast_ready_value = protected_failure_contrast.get(
        "ready_for_explicit_approval"
    )
    protected_failure_contrast_gate_ready = (
        bool(protected_failure_contrast_ready_value)
        if protected_failure_contrast_ready_value is not None
        else (
            protected_failure_contrast.get("status")
            == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
            or protected_failure_contrast_collection_blocker
        )
    )
    protected_failure_contrast_collection_ready = (
        protected_failure_contrast_gate_ready
        and protected_failure_contrast_request_ready
    )
    protected_failure_contrast_integration_ready = bool(
        protected_failure_contrast.get("integration_ready")
    )
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
        or readiness.get("decision", {}).get("status") in FORBIDDEN_INPUT_STATUSES
        or sequence_decision.get("status") in FORBIDDEN_INPUT_STATUSES
    )
    stage4_ready = bool(stage4.get("ready_for_current_suite"))

    blockers: list[str] = []
    warnings: list[str] = []
    if not protected_ready:
        blockers.append("protected_stage5_6_stack_not_ready")
    if not stage7_controls_ready:
        blockers.append("stage7_clean_success_controls_missing")
    if not sequence_review_ready:
        blockers.append("sequence_policy_benchmark_review_not_ready")
    elif not sequence_review_supportive:
        if not protected_failure_contrast_request_ready:
            blockers.append(
                "protected_plan_window_failure_contrast_approval_request_blocked"
            )
        elif protected_failure_contrast_collection_blocker:
            blockers.append(
                "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
            )
        else:
            blockers.append("sequence_policy_benchmark_mixed_or_underpowered")
    if sequence_forbidden_training_or_runtime_inputs:
        blockers.append("sequence_policy_forbidden_training_or_runtime_rows")
    if not stage4_ready:
        warnings.append("stage4_h40_caveat_remains")
    if not stage7_promoted:
        warnings.append("stage7_not_promoted_and_must_remain_held_out_without_explicit_gate")

    if blockers:
        if "sequence_policy_forbidden_training_or_runtime_rows" in blockers:
            status = "stage8_training_blocked_forbidden_training_or_runtime_rows"
            next_step = "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
        elif "stage7_clean_success_controls_missing" in blockers:
            status = "stage8_training_blocked_pending_stage7_sequence_gate"
            next_step = "fill_stage7_success_controls_and_rerun_passive_gate_advancement"
        elif "protected_plan_window_failure_contrast_collection_pending_explicit_approval" in blockers:
            status = "stage8_training_blocked_pending_protected_failure_contrast_collection"
            next_step = "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
        elif "protected_plan_window_failure_contrast_approval_request_blocked" in blockers:
            status = (
                "stage8_training_blocked_pending_protected_failure_contrast_approval_request_repair"
            )
            next_step = "repair_protected_failure_contrast_approval_request_scope"
        elif "sequence_policy_benchmark_mixed_or_underpowered" in blockers:
            status = "stage8_training_blocked_pending_sequence_policy_benchmark_review"
            next_step = "inspect_sequence_policy_benchmark_review_before_stage8_training"
        else:
            status = "stage8_training_blocked_pending_sequence_policy_gate"
            next_step = "rerun_passive_gate_advancement_or_inspect_sequence_policy_benchmark_review"
    elif warnings:
        status = "stage8_training_review_blocked_pending_architecture_review"
        next_step = "write_explicit_stage8_training_review_packet_if_warnings_are_accepted"
    else:
        status = "stage8_training_review_ready_pending_explicit_approval"
        next_step = "write_explicit_stage8_training_review_packet"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_stage8_training_readiness_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_full_suite_readiness_audit_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
        ],
        "requirements": {
            "readiness_checked_flag_count": readiness_boundaries.get("checked_flag_count"),
            "readiness_boundary_violation_count": readiness_boundaries.get(
                "violation_count"
            ),
            "readiness_source_artifact_count": len(
                readiness.get("source_artifacts") or {}
            ),
            "protected_stage5_6_stack_ready": protected_ready,
            "m1_m4_preservation_passed": protected.get("m1_m4_preservation_passed"),
            "kpk_kqk_bridge_preservation_passed": protected.get(
                "kpk_kqk_bridge_preservation_passed"
            ),
            "stage7_clean_success_controls_ready": stage7_controls_ready,
            "stage7_success_controls": stage7.get("success_controls"),
            "stage7_success_controls_required": stage7.get("success_controls_required"),
            "stage7_promoted": stage7_promoted,
            "stage4_ready_for_current_suite": stage4_ready,
            "sequence_policy_benchmark_design_status": sequence_policy.get(
                "benchmark_design_status"
            ),
            "sequence_policy_benchmark_review_status": sequence_decision.get("status"),
            "sequence_policy_benchmark_review_ready": sequence_review_ready,
            "sequence_policy_benchmark_supportive": sequence_review_supportive,
            "sequence_policy_passive_design_without_new_labels_status": (
                sequence_policy.get("passive_design_without_new_labels_status")
            ),
            "sequence_policy_passive_design_current_evidence_limit": (
                sequence_policy.get("passive_design_current_evidence_limit")
            ),
            "sequence_policy_cross_stage_requirements_status": sequence_policy.get(
                "cross_stage_requirements_status"
            ),
            "sequence_policy_replay_free_protected_cross_stage_evidence": (
                sequence_policy.get("replay_free_protected_cross_stage_evidence")
            ),
            "sequence_policy_cross_stage_sequence_evidence_met": sequence_policy.get(
                "cross_stage_sequence_evidence_met"
            ),
            "sequence_policy_after_protected_failure_contrast_refresh_status": (
                sequence_policy.get("post_failure_contrast_refresh_status")
            ),
            "sequence_policy_after_protected_failure_contrast_boundaries_preserved": (
                sequence_policy.get("post_failure_contrast_refresh_boundaries_preserved")
            ),
            "sequence_policy_after_protected_failure_contrast_boundary_violation_count": (
                sequence_policy.get(
                    "post_failure_contrast_refresh_boundary_violation_count"
                )
            ),
            "sequence_policy_after_protected_failure_contrast_rows": (
                sequence_policy.get("post_failure_contrast_refresh_row_count")
            ),
            "sequence_policy_after_protected_failure_contrast_stage7_training_row_count": (
                sequence_policy.get(
                    "post_failure_contrast_refresh_stage7_training_row_count"
                )
            ),
            "sequence_policy_forbidden_training_or_runtime_input_blocked": (
                sequence_forbidden_training_or_runtime_inputs
            ),
            "sequence_policy_forbidden_training_or_runtime_input_blockers": (
                forbidden_input_blockers
            ),
            "protected_failure_contrast_collection_ready_for_explicit_approval": (
                protected_failure_contrast_collection_ready
            ),
            "protected_failure_contrast_integration_ready": (
                protected_failure_contrast_integration_ready
            ),
            "protected_failure_contrast_runner_status": protected_failure_contrast.get(
                "runner_status"
            ),
            "protected_failure_contrast_runner_manifest_status": (
                protected_failure_contrast.get("runner_manifest_status")
            ),
            "protected_failure_contrast_runner_manifest_declared_job_count": (
                protected_failure_contrast.get("runner_manifest_declared_job_count")
            ),
            "protected_failure_contrast_runner_manifest_fingerprint": (
                protected_failure_contrast.get("runner_manifest_fingerprint")
            ),
            "protected_failure_contrast_runner_collection_run_allowed": (
                protected_failure_contrast.get("runner_collection_run_allowed")
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
                protected_failure_contrast_request_status
            ),
            "protected_failure_contrast_approval_request_blockers": (
                protected_failure_contrast_request_blockers
            ),
            "protected_failure_contrast_approval_request_ready_for_collection": (
                protected_failure_contrast_request_ready
            ),
            "protected_failure_contrast_approval_receipt_created_by_request": (
                protected_failure_contrast.get("approval_receipt_created_by_request")
            ),
            "protected_failure_contrast_approval_receipt_present": (
                protected_failure_contrast.get("approval_receipt_present")
            ),
            "protected_failure_contrast_approval_receipt_valid": (
                protected_failure_contrast.get("approval_receipt_valid")
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
        },
        "blockers": blockers,
        "warnings": warnings,
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
        "# KRK Stage 8 Training Readiness Review v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This review is non-causal. It does not train Stage 8, promote Stage 7, change runtime behavior, or authorize implementation by itself.",
        "",
        "## Requirements",
        "",
    ]
    for key, value in payload["requirements"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Blockers", ""])
    for blocker in payload["blockers"]:
        lines.append(f"- `{blocker}`")
    if not payload["blockers"]:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    for warning in payload["warnings"]:
        lines.append(f"- `{warning}`")
    if not payload["warnings"]:
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
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()

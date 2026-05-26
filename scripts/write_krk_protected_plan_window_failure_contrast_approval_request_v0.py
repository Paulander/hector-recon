#!/usr/bin/env python3
"""Write the passive approval-request packet for protected failure contrasts.

This artifact is not an approval receipt and is never consumed by the runner as
authorization. It records the exact reviewed manifest/readiness scope that a
separate explicit approval receipt would have to match before collection could
execute.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
READINESS = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
)
RUNNER = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_runner_v0.json"
)
FULL_SUITE_READINESS = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
OUTPUT_JSON = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
)
OUTPUT_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_approval_request_v0.md"
)
POST_FAILURE_CONTRAST_SEQUENCE_REFRESH = (
    "reports/strategy_arbitration/"
    "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
)
POST_SUCCESS_REFRESH_SCRIPT = "scripts/advance_krk_suite_from_current_gates_v0.py"
POST_SUCCESS_REFRESH_SCOPE = "full_passive_krk_suite_gate_stack"

SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_approval_request.v0"
APPROVAL_SCHEMA_VERSION = (
    "krk_protected_plan_window_failure_contrast_collection_approval.v0"
)
APPROVAL_ID = "approve_protected_plan_window_failure_contrast_collection"
APPROVAL_STATUS = "approved_for_single_bounded_observation_collection"
DEFAULT_APPROVAL_RECEIPT = (
    "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
)

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
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
    manifest: dict[str, Any] | None = None,
    readiness: dict[str, Any] | None = None,
    runner: dict[str, Any] | None = None,
    full_suite_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    readiness = readiness or _load(READINESS)
    runner = runner or _load(RUNNER)
    full_suite_readiness = full_suite_readiness or _load(FULL_SUITE_READINESS)
    manifest_summary = manifest.get("summary") or {}
    readiness_summary = readiness.get("summary") or {}
    runner_summary = runner.get("summary") or {}
    protected_stack = full_suite_readiness.get("protected_stack") or {}
    sequence_policy = full_suite_readiness.get("sequence_policy") or {}
    active_stack_path_status = protected_stack.get("active_stack_path_status") or {}
    rollback_stack_path_status = protected_stack.get("rollback_stack_path_status") or {}
    protected_stack_safety = {
        "status": protected_stack.get("status"),
        "ready": protected_stack.get("ready"),
        "rollback_paths_preserved": protected_stack.get("rollback_paths_preserved"),
        "active_paths_safe": active_stack_path_status.get("all_paths_safe"),
        "active_paths_exist": active_stack_path_status.get("all_paths_exist"),
        "rollback_paths_safe": rollback_stack_path_status.get("all_paths_safe"),
        "rollback_paths_exist": rollback_stack_path_status.get("all_paths_exist"),
        "rollback_common_paths_distinct": protected_stack.get(
            "rollback_common_paths_distinct"
        ),
        "filesystem_snapshots_replaced": protected_stack.get(
            "filesystem_snapshots_replaced"
        ),
        "hard_blockers": full_suite_readiness.get("hard_blockers") or [],
    }
    job_count = int(
        runner_summary.get("job_count")
        if runner_summary.get("job_count") is not None
        else manifest_summary.get("job_count") or len(manifest.get("jobs") or [])
    )
    approval_receipt_path = runner.get("approval_receipt_path") or DEFAULT_APPROVAL_RECEIPT
    required_receipt = {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "approval_id": APPROVAL_ID,
        "receipt_path": approval_receipt_path,
        "approval_scope": {
            "manifest_fingerprint": readiness_summary.get("manifest_fingerprint"),
            "readiness_fingerprint": readiness_summary.get("readiness_fingerprint"),
            "job_count": job_count,
            "max_jobs": runner_summary.get("max_jobs"),
            "job_timeout_seconds": runner_summary.get("job_timeout_seconds"),
            "overwrite_existing_outputs": runner_summary.get(
                "overwrite_existing_outputs"
            ),
            "refresh_after_run": runner_summary.get("refresh_after_run_requested"),
            "post_success_refresh_required": True,
            "post_success_refresh_script": POST_SUCCESS_REFRESH_SCRIPT,
            "post_success_refresh_scope": POST_SUCCESS_REFRESH_SCOPE,
            "manifest_status": manifest.get("decision", {}).get("status"),
            "readiness_status": readiness.get("decision", {}).get("status"),
            "protected_stack_status": readiness_summary.get("protected_stack_status"),
            "protected_stack_ready": readiness_summary.get("protected_stack_ready"),
            "protected_stack_rollback_paths_preserved": readiness_summary.get(
                "protected_stack_rollback_paths_preserved"
            ),
            "protected_stack_active_paths_safe": readiness_summary.get(
                "protected_stack_active_paths_safe"
            ),
            "protected_stack_active_paths_exist": readiness_summary.get(
                "protected_stack_active_paths_exist"
            ),
            "protected_stack_rollback_paths_safe": readiness_summary.get(
                "protected_stack_rollback_paths_safe"
            ),
            "protected_stack_rollback_paths_exist": readiness_summary.get(
                "protected_stack_rollback_paths_exist"
            ),
            "protected_stack_rollback_common_paths_distinct": readiness_summary.get(
                "protected_stack_rollback_common_paths_distinct"
            ),
            "protected_stack_filesystem_snapshots_replaced": readiness_summary.get(
                "protected_stack_filesystem_snapshots_replaced"
            ),
            "protected_stack_hard_blockers": (
                readiness_summary.get("protected_stack_hard_blockers") or []
            ),
        },
        "decision": {
            "status": APPROVAL_STATUS,
            "single_execution_only": True,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_behavior_changed": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_approval_request_packet",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_execution_readiness_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_runner_v0.json",
            "reports/krk_full_suite_readiness_audit_v0.json",
            POST_FAILURE_CONTRAST_SEQUENCE_REFRESH,
        ],
        "approval_receipt_path": approval_receipt_path,
        "approval_receipt_created": False,
        "approval_receipt_present": runner_summary.get("approval_receipt_present"),
        "approval_receipt_valid": runner_summary.get("approval_receipt_valid"),
        "approval_receipt_blockers": runner_summary.get("approval_receipt_blockers") or [],
        "protected_stack_safety": protected_stack_safety,
        "required_receipt_if_user_approves": required_receipt,
        "summary": {
            "job_count": job_count,
            "manifest_status": manifest.get("decision", {}).get("status"),
            "readiness_status": readiness.get("decision", {}).get("status"),
            "runner_status": runner.get("decision", {}).get("status"),
            "runner_execution_requested": runner.get("execution_requested"),
            "runner_processed_job_count": runner_summary.get("processed_job_count"),
            "runner_executed_job_count": runner_summary.get("executed_job_count"),
            "runner_max_jobs_option": runner_summary.get("max_jobs"),
            "runner_job_timeout_seconds": runner_summary.get("job_timeout_seconds"),
            "runner_overwrite_existing_outputs": runner_summary.get(
                "overwrite_existing_outputs"
            ),
            "runner_refresh_after_run_requested": runner_summary.get(
                "refresh_after_run_requested"
            ),
            "post_success_refresh_required": True,
            "post_success_refresh_script": POST_SUCCESS_REFRESH_SCRIPT,
            "post_success_refresh_scope": POST_SUCCESS_REFRESH_SCOPE,
            "pre_collection_sequence_policy_after_protected_failure_contrast_refresh_status": (
                sequence_policy.get("post_failure_contrast_refresh_status")
            ),
            "pre_collection_sequence_policy_after_protected_failure_contrast_boundaries_preserved": (
                sequence_policy.get("post_failure_contrast_refresh_boundaries_preserved")
            ),
            "pre_collection_sequence_policy_after_protected_failure_contrast_boundary_violation_count": (
                sequence_policy.get(
                    "post_failure_contrast_refresh_boundary_violation_count"
                )
            ),
            "pre_collection_sequence_policy_after_protected_failure_contrast_rows": (
                sequence_policy.get("post_failure_contrast_refresh_row_count")
            ),
            "pre_collection_sequence_policy_after_protected_failure_contrast_stage7_training_row_count": (
                sequence_policy.get(
                    "post_failure_contrast_refresh_stage7_training_row_count"
                )
            ),
            "manifest_fingerprint": readiness_summary.get("manifest_fingerprint"),
            "readiness_fingerprint": readiness_summary.get("readiness_fingerprint"),
            "protected_stack_status": protected_stack_safety["status"],
            "protected_stack_ready": protected_stack_safety["ready"],
            "protected_stack_rollback_paths_preserved": protected_stack_safety[
                "rollback_paths_preserved"
            ],
            "protected_stack_filesystem_snapshots_replaced": protected_stack_safety[
                "filesystem_snapshots_replaced"
            ],
            "approval_receipt_required": True,
            "approval_receipt_missing": not bool(runner_summary.get("approval_receipt_present")),
        },
        "decision": {
            "status": "protected_plan_window_failure_contrast_approval_request_ready",
            "recommended_next_step": (
                "user_may_create_matching_approval_receipt_only_if_collection_is_explicitly_approved"
            ),
            "collection_run_allowed": False,
            "label_run_allowed": False,
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    summary = payload["summary"]
    required = payload["required_receipt_if_user_approves"]
    lines = [
        "# KRK Protected Plan-Window Failure Contrast Approval Request v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a passive request packet only. It does not create the approval receipt, execute collection, run labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Protected Stack Safety", ""])
    for key, value in payload["protected_stack_safety"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Approval Receipt Status",
            "",
            f"- approval_receipt_path: `{payload['approval_receipt_path']}`",
            f"- approval_receipt_present: `{payload['approval_receipt_present']}`",
            f"- approval_receipt_valid: `{payload['approval_receipt_valid']}`",
            f"- approval_receipt_blockers: `{payload['approval_receipt_blockers']}`",
            f"- approval_receipt_created: `{payload['approval_receipt_created']}`",
            "",
            "## Required Receipt If Explicitly Approved",
            "",
            "```json",
            json.dumps(required, indent=2, sort_keys=True),
            "```",
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            f"- collection_run_allowed: `{decision['collection_run_allowed']}`",
            f"- label_run_allowed: `{decision['label_run_allowed']}`",
            "- runtime_changes_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate protected plan-window failure-contrast collection readiness.

This is a preflight artifact only. It checks the reviewed manifest and output
bindings, but it does not execute collection, run labels, change runtime
behavior, train selectors, promote Stage 7, or authorize Stage 8.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
REVIEW = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_manifest_review_v0.json"
)
FULL_SUITE_READINESS = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
OUTPUT_JSON = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
)
OUTPUT_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_execution_readiness_v0.md"
)

SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_execution_readiness.v0"
MAX_COLLECTION_JOBS = 6
OUTPUT_ROOT = Path("reports/strategy_arbitration/protected_plan_window_failure_contrasts")

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

FORBIDDEN_JOB_TRUE_FLAGS = (
    "labels_generated",
    "usable_for_selector_training",
    "usable_for_runtime_authorization",
    "stage7_heldout_challenge",
    "runtime_behavior_changed",
    "runtime_defaults_changed",
    "runtime_selector_implemented",
    "runtime_score_changes",
    "runtime_direct_routing",
    "runtime_dtm_or_tablebase_lookup",
    "hidden_python_controller",
    "gameplay_topology_mutation",
    "runtime_changes_allowed",
    "label_run_allowed",
    "selector_allowed",
    "selector_training_allowed",
    "stage7_promotion_allowed",
    "stage8_training_allowed",
)


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _safe_relative(path_value: Any) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        return False
    return path.parts[: len(OUTPUT_ROOT.parts)] == OUTPUT_ROOT.parts


def _safe_topology(path_value: Any) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        return False
    return (ROOT / path).exists()


def _manifest_fingerprint(manifest: dict[str, Any]) -> str:
    summary = manifest.get("summary") or {}
    fingerprint_summary = {
        key: summary.get(key)
        for key in (
            "job_count",
            "max_collection_jobs",
            "minimum_new_unique_failures_needed",
            "target_failure_label_goal",
            "source_stage_counts",
            "source_family_counts",
            "missing_required_source_stages",
            "all_bindings_valid",
            "topology_path",
            "topology_path_safe",
            "topology_exists",
            "output_paths_valid",
            "forbidden_job_flag_count",
        )
    }
    canonical = {
        "schema_version": manifest.get("schema_version"),
        "causal_status": manifest.get("causal_status"),
        "collection_constraints": manifest.get("collection_constraints") or {},
        "summary": fingerprint_summary,
        "jobs": manifest.get("jobs") or [],
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_job(job: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if job.get("source_stage") not in {"stage4", "stage5", "stage6"}:
        blockers.append("invalid_source_stage")
    if int(job.get("horizon") or 0) != 40:
        blockers.append("horizon_must_be_40")
    if job.get("collection_mode") != "observation_only_trace_collection_pending_explicit_approval":
        blockers.append("invalid_collection_mode")
    for flag in FORBIDDEN_JOB_TRUE_FLAGS:
        if job.get(flag) is True:
            blockers.append(f"{flag}_forbidden")
    if not _safe_relative(job.get("expected_output_json")):
        blockers.append("unsafe_expected_output_json")
    if not _safe_topology((job.get("execution_binding") or {}).get("topology_path")):
        blockers.append("missing_or_invalid_topology_binding")
    return blockers


def _readiness_fingerprint(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    fingerprint_summary = {
        key: summary.get(key)
        for key in (
            "job_count",
            "jobs_passing_readiness",
            "all_jobs_pass_readiness",
            "job_readiness_blocker_count",
            "manifest_status",
            "manifest_review_status",
            "manifest_fingerprint",
            "recorded_manifest_fingerprint",
            "review_manifest_fingerprint",
            "manifest_fingerprints_match",
            "execution_readiness_blockers",
            "existing_output_count",
            "selector_training_row_count",
            "runtime_authorization_row_count",
            "stage7_training_row_count",
            "protected_stack_status",
            "protected_stack_ready",
            "protected_stack_rollback_paths_preserved",
            "protected_stack_active_paths_safe",
            "protected_stack_active_paths_exist",
            "protected_stack_rollback_paths_safe",
            "protected_stack_rollback_paths_exist",
            "protected_stack_rollback_common_paths_distinct",
            "protected_stack_filesystem_snapshots_replaced",
            "protected_stack_hard_blockers",
            "readiness_checked_flag_count",
            "readiness_boundary_violation_count",
            "readiness_source_artifact_count",
        )
    }
    canonical = {
        "schema_version": payload.get("schema_version"),
        "causal_status": payload.get("causal_status"),
        "source_artifacts": payload.get("source_artifacts") or [],
        "summary": fingerprint_summary,
        "job_checks": payload.get("job_checks") or [],
        "decision": payload.get("decision") or {},
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_payload(
    *,
    manifest: dict[str, Any] | None = None,
    review: dict[str, Any] | None = None,
    full_suite_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    review = review or _load(REVIEW)
    full_suite_readiness = full_suite_readiness or _load(FULL_SUITE_READINESS)
    jobs = manifest.get("jobs") or []
    manifest_status = manifest.get("decision", {}).get("status")
    review_status = review.get("decision", {}).get("status")
    protected_stack = full_suite_readiness.get("protected_stack") or {}
    readiness_boundaries = full_suite_readiness.get("runtime_and_training_boundaries") or {}
    active_stack_path_status = protected_stack.get("active_stack_path_status") or {}
    rollback_stack_path_status = protected_stack.get("rollback_stack_path_status") or {}
    protected_stack_hard_blockers = list(full_suite_readiness.get("hard_blockers") or [])
    manifest_fingerprint = _manifest_fingerprint(manifest)
    recorded_manifest_fingerprint = (manifest.get("summary") or {}).get(
        "manifest_fingerprint"
    )
    review_manifest_fingerprint = (review.get("review_summary") or {}).get(
        "manifest_fingerprint"
    )
    blockers: list[str] = []
    if manifest_status != "protected_plan_window_failure_contrast_manifest_ready_for_review":
        blockers.append("manifest_not_ready_for_review")
    if (
        review_status
        != "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    ):
        blockers.append("manifest_review_not_passed")
    if len(jobs) == 0:
        blockers.append("no_jobs_bound")
    if len(jobs) > MAX_COLLECTION_JOBS:
        blockers.append("job_count_exceeds_bound")
    if not (manifest.get("summary") or {}).get("all_bindings_valid"):
        blockers.append("manifest_bindings_not_valid")
    if recorded_manifest_fingerprint != manifest_fingerprint:
        blockers.append("manifest_fingerprint_missing_or_mismatch")
    if review_manifest_fingerprint != manifest_fingerprint:
        blockers.append("manifest_review_fingerprint_mismatch")
    if protected_stack.get("ready") is not True:
        blockers.append("protected_stack_not_ready")
    if protected_stack.get("rollback_paths_preserved") is not True:
        blockers.append("protected_stack_rollback_paths_not_preserved")
    if active_stack_path_status.get("all_paths_safe") is not True:
        blockers.append("protected_stack_active_paths_unsafe")
    if active_stack_path_status.get("all_paths_exist") is not True:
        blockers.append("protected_stack_active_paths_missing")
    if rollback_stack_path_status.get("all_paths_safe") is not True:
        blockers.append("protected_stack_rollback_paths_unsafe")
    if rollback_stack_path_status.get("all_paths_exist") is not True:
        blockers.append("protected_stack_rollback_paths_missing")
    if protected_stack.get("rollback_common_paths_distinct") is not True:
        blockers.append("protected_stack_rollback_common_paths_not_distinct")
    if protected_stack.get("filesystem_snapshots_replaced") is not False:
        blockers.append("protected_stack_filesystem_snapshot_replacement_detected")
    if protected_stack_hard_blockers:
        blockers.append("protected_stack_hard_blockers_present")
    boundary_violation_count = readiness_boundaries.get("violation_count")
    if boundary_violation_count not in (None, 0):
        blockers.append("readiness_boundary_violations_present")

    seen_job_ids: set[str] = set()
    seen_outputs: set[str] = set()
    job_checks = []
    for job in jobs:
        job_id = str(job.get("job_id"))
        output = str(job.get("expected_output_json") or "")
        job_blockers = _validate_job(job)
        if job_id in seen_job_ids:
            job_blockers.append("duplicate_job_id")
        seen_job_ids.add(job_id)
        if output in seen_outputs:
            job_blockers.append("duplicate_expected_output_json")
        seen_outputs.add(output)
        output_exists = _safe_relative(output) and (ROOT / output).exists()
        job_checks.append(
            {
                "job_id": job_id,
                "source_stage": job.get("source_stage"),
                "source_family": job.get("source_family"),
                "expected_output_json": output,
                "output_exists": output_exists,
                "readiness_blockers": job_blockers,
                "ready": not job_blockers,
            }
        )
    job_blocker_count = sum(len(row["readiness_blockers"]) for row in job_checks)
    if job_blocker_count:
        blockers.append("job_readiness_blockers_present")
    ready = not blockers
    payload = {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_collection_execution_readiness",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_review_v0.json",
            "reports/krk_full_suite_readiness_audit_v0.json",
        ],
        "summary": {
            "job_count": len(jobs),
            "jobs_passing_readiness": sum(1 for row in job_checks if row["ready"]),
            "all_jobs_pass_readiness": bool(jobs) and all(row["ready"] for row in job_checks),
            "job_readiness_blocker_count": job_blocker_count,
            "manifest_status": manifest_status,
            "manifest_review_status": review_status,
            "manifest_fingerprint": manifest_fingerprint,
            "recorded_manifest_fingerprint": recorded_manifest_fingerprint,
            "review_manifest_fingerprint": review_manifest_fingerprint,
            "manifest_fingerprints_match": (
                recorded_manifest_fingerprint == manifest_fingerprint
                and review_manifest_fingerprint == manifest_fingerprint
            ),
            "execution_readiness_blockers": blockers,
            "existing_output_count": sum(1 for row in job_checks if row["output_exists"]),
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
            "stage7_training_row_count": 0,
            "protected_stack_status": protected_stack.get("status"),
            "protected_stack_ready": protected_stack.get("ready"),
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
            "protected_stack_hard_blockers": protected_stack_hard_blockers,
            "readiness_checked_flag_count": readiness_boundaries.get(
                "checked_flag_count"
            ),
            "readiness_boundary_violation_count": boundary_violation_count,
            "readiness_source_artifact_count": len(
                full_suite_readiness.get("source_artifacts") or {}
            ),
        },
        "job_checks": job_checks,
        "decision": {
            "status": (
                "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                if ready
                else "protected_plan_window_failure_contrast_execution_readiness_blocked"
            ),
            "recommended_next_step": (
                "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
                if ready
                else "fix_protected_plan_window_failure_contrast_execution_readiness"
            ),
            "collection_run_allowed": False,
            "label_run_allowed": False,
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "approval_required_before_collection": True,
        },
    }
    payload["summary"]["readiness_fingerprint"] = _readiness_fingerprint(payload)
    return payload


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Protected Plan-Window Failure Contrast Execution Readiness v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a dry-run preflight only. It does not execute collection, run labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Jobs", ""])
    for row in payload["job_checks"]:
        lines.append(
            f"- `{row['job_id']}` ready=`{row['ready']}` output_exists=`{row['output_exists']}` blockers=`{row['readiness_blockers']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- collection_run_allowed: `false`",
            "- label_run_allowed: `false`",
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

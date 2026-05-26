#!/usr/bin/env python3
"""Review the protected plan-window failure-contrast collection manifest."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
OUTPUT_JSON = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_review_v0.json"
)
OUTPUT_MD = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_review_v0.md"
)

SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_manifest_review.v0"
MAX_COLLECTION_JOBS = 6
OUTPUT_ROOT = Path("reports/strategy_arbitration/protected_plan_window_failure_contrasts")

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


def _safe_relative(path_value: Any, *, required_root: Path | None = None) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        return False
    if required_root is None:
        return True
    return path.parts[: len(required_root.parts)] == required_root.parts


def _topology_path(job: dict[str, Any]) -> str:
    return str((job.get("execution_binding") or {}).get("topology_path") or "")


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


def build_payload(*, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    jobs = manifest.get("jobs") or []
    violations: list[dict[str, Any]] = []
    manifest_fingerprint = _manifest_fingerprint(manifest)
    recorded_manifest_fingerprint = (manifest.get("summary") or {}).get(
        "manifest_fingerprint"
    )
    if recorded_manifest_fingerprint != manifest_fingerprint:
        violations.append(
            {
                "job_id": None,
                "violation": "manifest_fingerprint_missing_or_mismatch",
            }
        )
    seen: set[str] = set()
    for job in jobs:
        job_id = str(job.get("job_id"))
        if job_id in seen:
            violations.append({"job_id": job_id, "violation": "duplicate_job_id"})
        seen.add(job_id)
        if job.get("source_stage") not in {"stage4", "stage5", "stage6"}:
            violations.append({"job_id": job_id, "violation": "invalid_source_stage"})
        if int(job.get("horizon") or 0) != 40:
            violations.append({"job_id": job_id, "violation": "horizon_must_be_40"})
        if job.get("collection_mode") != "observation_only_trace_collection_pending_explicit_approval":
            violations.append({"job_id": job_id, "violation": "invalid_collection_mode"})
        for flag in FORBIDDEN_JOB_TRUE_FLAGS:
            if job.get(flag) is True:
                violations.append({"job_id": job_id, "violation": f"{flag}_forbidden"})
        if not _safe_relative(job.get("expected_output_json"), required_root=OUTPUT_ROOT):
            violations.append({"job_id": job_id, "violation": "unsafe_expected_output_json"})
        topology = _topology_path(job)
        if not _safe_relative(topology) or not topology or not (ROOT / topology).exists():
            violations.append({"job_id": job_id, "violation": "missing_or_invalid_topology_binding"})
    if len(jobs) > MAX_COLLECTION_JOBS:
        violations.append({"job_id": None, "violation": "job_count_exceeds_bound"})
    if not jobs:
        violations.append({"job_id": None, "violation": "no_jobs_bound"})
    if not (manifest.get("summary") or {}).get("all_bindings_valid"):
        violations.append({"job_id": None, "violation": "manifest_bindings_not_valid"})
    constraints = manifest.get("collection_constraints") or {}
    for key in (
        "requires_explicit_approval_before_collection",
        "observation_only",
        "no_runtime_default_change",
        "no_runtime_dtm_or_tablebase",
        "no_gameplay_topology_mutation",
        "no_stage7_promotion",
        "no_stage8_training",
    ):
        if constraints.get(key) is not True:
            violations.append({"job_id": None, "violation": f"constraint_missing_{key}"})
    stage_counts = Counter(str(job.get("source_stage")) for job in jobs)
    required_stages_present = all(stage_counts.get(stage, 0) > 0 for stage in ("stage4", "stage5", "stage6"))
    if not required_stages_present:
        violations.append({"job_id": None, "violation": "required_source_stage_missing"})
    review_passed = not violations
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_collection_manifest_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
        ],
        "review_summary": {
            "job_count": len(jobs),
            "max_collection_jobs": MAX_COLLECTION_JOBS,
            "stage_counts": dict(stage_counts),
            "family_counts": dict(Counter(str(job.get("source_family")) for job in jobs)),
            "manifest_fingerprint": manifest_fingerprint,
            "recorded_manifest_fingerprint": recorded_manifest_fingerprint,
            "manifest_fingerprint_matches": (
                recorded_manifest_fingerprint == manifest_fingerprint
            ),
            "required_stages_present": required_stages_present,
            "violation_count": len(violations),
            "violations": violations,
            "collection_run_allowed_now": False,
            "label_run_allowed_now": False,
            "runtime_work_allowed": False,
            "review_passed": review_passed,
        },
        "decision": {
            "status": (
                "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
                if review_passed
                else "protected_plan_window_failure_contrast_manifest_review_failed"
            ),
            "recommended_next_step": (
                "explicitly_approve_protected_plan_window_failure_contrast_collection"
                if review_passed
                else "fix_protected_plan_window_failure_contrast_manifest"
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


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["review_summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Protected Plan-Window Failure Contrast Manifest Review v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a non-causal manifest review. Passing review does not execute collection or authorize labels; explicit approval is still required.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
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

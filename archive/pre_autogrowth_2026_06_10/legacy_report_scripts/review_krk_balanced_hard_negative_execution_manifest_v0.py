#!/usr/bin/env python3
"""Review balanced hard-negative execution manifest before labels."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/krk_balanced_hard_negative_execution_manifest_v0.json")
OUT_JSON = Path("reports/krk_balanced_hard_negative_execution_manifest_review_v0.json")
OUT_MD = Path("reports/krk_balanced_hard_negative_execution_manifest_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    manifest = _load(MANIFEST)
    jobs = manifest.get("jobs") or []
    violations = []
    seen_job_ids = set()
    for job in jobs:
        job_id = job.get("job_id")
        if job_id in seen_job_ids:
            violations.append({"job_id": job_id, "violation": "duplicate_job_id"})
        seen_job_ids.add(job_id)
        if job.get("source_stage") == "stage7":
            violations.append({"job_id": job_id, "violation": "stage7_job_not_allowed"})
        if bool(job.get("stage7_training_row")):
            violations.append({"job_id": job_id, "violation": "stage7_training_row_not_allowed"})
        if int(job.get("horizon") or 0) != 40:
            violations.append({"job_id": job_id, "violation": "horizon_must_be_40"})
        binding = job.get("execution_binding") or {}
        if binding.get("execution_mode") != "force_provider_first_white_move_then_release":
            violations.append({"job_id": job_id, "violation": "invalid_execution_mode"})
        if not binding.get("enable_diagnostic_caches"):
            violations.append({"job_id": job_id, "violation": "diagnostic_caches_required"})
        if binding.get("trace_mode") != "failures_only":
            violations.append({"job_id": job_id, "violation": "trace_failures_only_required"})
        if binding.get("plasticity_scope") != "protected_frozen":
            violations.append({"job_id": job_id, "violation": "protected_frozen_scope_required"})
    if len(jobs) > 12:
        violations.append({"job_id": None, "violation": "job_count_exceeds_balanced_budget"})
    if not (manifest.get("binding_summary") or {}).get("all_bindings_valid"):
        violations.append({"job_id": None, "violation": "bindings_not_valid"})
    labels_allowed = not violations and len(jobs) > 0
    payload = {
        "schema_version": "krk_balanced_hard_negative_execution_manifest_review.v0",
        "causal_status": "non_causal_manifest_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "review_summary": {
            "job_count": len(jobs),
            "stage_counts": dict(Counter(str(job.get("source_stage")) for job in jobs)),
            "provider_family_counts": dict(Counter(str(job.get("provider_family")) for job in jobs)),
            "provider_counts": dict(Counter(str(job.get("provider_id")) for job in jobs)),
            "violation_count": len(violations),
            "violations": violations,
            "labels_allowed": labels_allowed,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
        "decision": {
            "status": (
                "balanced_hard_negative_manifest_review_passed_labels_allowed"
                if labels_allowed
                else "balanced_hard_negative_manifest_review_failed"
            ),
            "recommended_next_step": (
                "run_bounded_balanced_hard_negative_labels" if labels_allowed else "fix_manifest_before_labels"
            ),
            "labels_allowed": labels_allowed,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
    }
    validate_review(payload)
    return payload


def validate_review(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Balanced Hard-Negative Execution Manifest Review v0",
        "",
        "Non-causal review of the balanced hard-negative label execution manifest.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["review_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Review the KRK strategy-owner contrast execution manifest.

This review decides whether a bounded offline label run is allowed. It does not
run labels, change runtime behavior, implement a selector, promote Stage 7, or
train Stage 8.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/krk_strategy_owner_contrast_execution_manifest_v0.json")
OUT_JSON = Path("reports/krk_strategy_owner_contrast_execution_manifest_review_v0.json")
OUT_MD = Path("reports/krk_strategy_owner_contrast_execution_manifest_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    manifest = _load_json(MANIFEST)
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("manifest must remain non-causal")
    jobs = manifest.get("jobs") or []
    stage_counts = Counter(str(job.get("source_stage") or "unknown") for job in jobs)
    provider_versions = Counter(
        str((job.get("execution_binding") or {}).get("provider_version") or "unknown")
        for job in jobs
    )
    violations = []
    summary = manifest.get("binding_summary") or {}
    if not summary.get("all_bindings_valid"):
        violations.append("bindings_not_valid")
    if len(jobs) > 12:
        violations.append("job_count_exceeds_bound")
    if stage_counts.get("stage7", 0):
        violations.append("stage7_jobs_present")
    for stage in ("stage4", "stage5", "stage6"):
        if stage_counts.get(stage, 0) != 4:
            violations.append(f"{stage}_job_count_not_4")
    for job in jobs:
        binding = job.get("execution_binding") or {}
        if job.get("horizon") != 40:
            violations.append(f"{job.get('job_id')}:horizon_not_h40")
        if job.get("trace_mode") != "failures_only":
            violations.append(f"{job.get('job_id')}:trace_mode_not_failures_only")
        if binding.get("composition_profile") != "handoff_composition_v1":
            violations.append(f"{job.get('job_id')}:composition_profile_invalid")
        if binding.get("execution_mode") != "force_provider_first_white_move_then_release":
            violations.append(f"{job.get('job_id')}:execution_mode_invalid")
        if binding.get("enable_diagnostic_caches") is not True:
            violations.append(f"{job.get('job_id')}:diagnostic_caches_disabled")
        if binding.get("topology_version") != "stage6_overlay_composed_v1":
            violations.append(f"{job.get('job_id')}:topology_version_invalid")
        if not binding.get("provider_version") or not binding.get("source_checkpoint"):
            violations.append(f"{job.get('job_id')}:missing_provider_provenance")

    labels_allowed = not violations
    review = {
        "schema_version": "krk_strategy_owner_contrast_execution_manifest_review.v0",
        "causal_status": "non_causal_manifest_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST)],
        "review_summary": {
            "job_count": len(jobs),
            "job_count_by_stage": dict(sorted(stage_counts.items())),
            "provider_versions": dict(sorted(provider_versions.items())),
            "violations": violations,
            "labels_allowed": labels_allowed,
            "stage7_jobs": stage_counts.get("stage7", 0),
        },
        "label_run_bounds": {
            "horizon": 40,
            "trace_mode": "failures_only",
            "diagnostic_caches_required": True,
            "max_jobs": 12,
            "stop_if_projected_to_hours": True,
        },
        "decision": {
            "status": (
                "contrast_execution_manifest_review_passed_labels_allowed"
                if labels_allowed
                else "contrast_execution_manifest_review_failed"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "labels_allowed": labels_allowed,
            "recommended_next_step": (
                "run_bounded_contrast_control_labels"
                if labels_allowed
                else "fix_contrast_execution_manifest"
            ),
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    if review.get("causal_status") != "non_causal_manifest_review":
        raise ValueError("review must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "labels_generated_in_this_slice",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if (review.get("decision") or {}).get("runtime_arbiter_allowed") is not False:
        raise ValueError("runtime arbiter must remain blocked")


def render_markdown(review: dict[str, Any]) -> str:
    summary = review["review_summary"]
    bounds = review["label_run_bounds"]
    lines = [
        "# KRK Strategy Owner Contrast Execution Manifest Review v0",
        "",
        "This review authorizes at most a bounded offline label run. It does not "
        "run labels, change runtime behavior, implement a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
        f"- Job count: `{summary['job_count']}`",
        f"- Jobs by stage: `{summary['job_count_by_stage']}`",
        f"- Provider versions: `{summary['provider_versions']}`",
        f"- Stage 7 jobs: `{summary['stage7_jobs']}`",
        f"- Violations: `{summary['violations']}`",
        f"- Labels allowed: `{summary['labels_allowed']}`",
        "",
        "## Label Run Bounds",
        "",
        f"- Horizon: `{bounds['horizon']}`",
        f"- Trace mode: `{bounds['trace_mode']}`",
        f"- Diagnostic caches required: `{bounds['diagnostic_caches_required']}`",
        f"- Max jobs: `{bounds['max_jobs']}`",
        f"- Stop if projected to hours: `{bounds['stop_if_projected_to_hours']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{review['decision']['status']}`",
        f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
        "- Runtime arbiter, selector sandbox, Stage 7 promotion, and Stage 8 training remain blocked.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["review_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

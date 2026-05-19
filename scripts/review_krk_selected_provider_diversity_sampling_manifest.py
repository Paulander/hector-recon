#!/usr/bin/env python3
"""Review KRK selected-provider diversity sampling manifest."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/krk_selected_provider_diversity_sampling_manifest_v0.json")
OUT_JSON = Path("reports/krk_selected_provider_diversity_sampling_manifest_review_v0.json")
OUT_MD = Path("reports/krk_selected_provider_diversity_sampling_manifest_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    manifest = _load_json(MANIFEST)
    if manifest.get("causal_status") != "non_causal_sampling_manifest":
        raise ValueError("manifest must remain non-causal")
    jobs = manifest.get("jobs") or []
    stage_counts = Counter(str(job.get("source_stage") or "unknown") for job in jobs)
    violations = []
    if not (manifest.get("binding_summary") or {}).get("all_bindings_valid"):
        violations.append("bindings_invalid")
    if len(jobs) > 45:
        violations.append("job_count_exceeds_bound")
    if any(job.get("source_stage") == "stage7" for job in jobs):
        violations.append("stage7_jobs_present")
    if not all(stage_counts.get(stage, 0) > 0 for stage in ("stage4", "stage5", "stage6")):
        violations.append("missing_protected_stage_coverage")
    for stage, count in stage_counts.items():
        if count > 15:
            violations.append(f"{stage}_count_exceeds_bound")
    for job in jobs:
        binding = job.get("execution_binding") or {}
        if binding.get("execution_mode") != "observe_selected_provider_only":
            violations.append(f"{job.get('job_id')}:execution_mode_invalid")
        if binding.get("composition_profile") != "handoff_composition_v1":
            violations.append(f"{job.get('job_id')}:composition_profile_invalid")
        if binding.get("enable_diagnostic_caches") is not True:
            violations.append(f"{job.get('job_id')}:diagnostic_caches_disabled")

    observations_allowed = not violations
    review = {
        "schema_version": "krk_selected_provider_diversity_sampling_manifest_review.v0",
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
            "stage7_jobs": stage_counts.get("stage7", 0),
            "violations": violations,
            "observations_allowed": observations_allowed,
        },
        "observation_bounds": {
            "selection_only": True,
            "playout_labels": False,
            "max_jobs": 45,
            "per_stage_max": 15,
            "diagnostic_caches_required": True,
        },
        "decision": {
            "status": (
                "selected_provider_diversity_sampling_manifest_review_passed"
                if observations_allowed
                else "selected_provider_diversity_sampling_manifest_review_failed"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "observations_allowed": observations_allowed,
            "recommended_next_step": (
                "run_bounded_selected_provider_observation_scan"
                if observations_allowed
                else "fix_selected_provider_diversity_sampling_manifest"
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


def render_markdown(review: dict[str, Any]) -> str:
    summary = review["review_summary"]
    bounds = review["observation_bounds"]
    lines = [
        "# KRK Selected Provider Diversity Sampling Manifest Review v0",
        "",
        "This review authorizes at most a bounded selection-only observation scan. "
        "It does not run playout labels, implement a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
        f"- Jobs: `{summary['job_count']}`",
        f"- Jobs by stage: `{summary['job_count_by_stage']}`",
        f"- Stage 7 jobs: `{summary['stage7_jobs']}`",
        f"- Violations: `{summary['violations']}`",
        f"- Observations allowed: `{summary['observations_allowed']}`",
        "",
        "## Bounds",
        "",
        f"- Selection only: `{bounds['selection_only']}`",
        f"- Playout labels: `{bounds['playout_labels']}`",
        f"- Max jobs: `{bounds['max_jobs']}`",
        f"- Per-stage max: `{bounds['per_stage_max']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{review['decision']['status']}`",
        f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
        "- Runtime arbiter and selector sandbox remain blocked.",
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

#!/usr/bin/env python3
"""Review the bounded KRK strategy-owner contrast label plan.

This is a non-causal review only. It does not bind jobs, run labels, implement
a runtime selector, promote Stage 7, or train Stage 8.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_strategy_owner_contrast_label_plan_v0.json")
OUT_JSON = Path("reports/krk_strategy_owner_contrast_label_plan_review_v0.json")
OUT_MD = Path("reports/krk_strategy_owner_contrast_label_plan_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    plan = _load_json(PLAN)
    if plan.get("causal_status") != "non_causal_label_plan":
        raise ValueError("label plan must remain non-causal")
    jobs = plan.get("jobs") or []
    stage_counts = Counter(str(job.get("source_stage") or "unknown") for job in jobs)
    provider_counts = Counter(str(job.get("provider_id") or "unknown") for job in jobs)
    violations = []
    if plan.get("labels_generated_in_this_slice") is not False:
        violations.append("labels_already_generated")
    if len(jobs) > 12:
        violations.append("job_count_exceeds_bound")
    if any(job.get("source_stage") == "stage7" for job in jobs):
        violations.append("stage7_jobs_present")
    for stage, count in stage_counts.items():
        if count > 4:
            violations.append(f"{stage}_job_count_exceeds_bound")
    for job in jobs:
        if job.get("causal_status") != "non_causal_label_job":
            violations.append(f"{job.get('job_id')}:causal_status_invalid")
        if job.get("horizon") != 40:
            violations.append(f"{job.get('job_id')}:horizon_not_h40")
        if job.get("trace_mode") != "failures_only":
            violations.append(f"{job.get('job_id')}:trace_mode_not_failures_only")
        if job.get("diagnostic_caches_required") is not True:
            violations.append(f"{job.get('job_id')}:diagnostic_caches_not_required")
        if not job.get("fen") or not job.get("provider_id"):
            violations.append(f"{job.get('job_id')}:missing_fen_or_provider")

    allowed_to_bind = not violations
    review = {
        "schema_version": "krk_strategy_owner_contrast_label_plan_review.v0",
        "causal_status": "non_causal_plan_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN)],
        "review_summary": {
            "job_count": len(jobs),
            "job_count_by_stage": dict(sorted(stage_counts.items())),
            "provider_counts": dict(sorted(provider_counts.items())),
            "stage7_jobs": stage_counts.get("stage7", 0),
            "violations": violations,
            "allowed_to_bind_execution_manifest": allowed_to_bind,
            "allowed_to_run_labels": False,
        },
        "binding_requirements": [
            "bind every job to explicit handoff_composition_v1 or stage6_overlay_composed topology",
            "make Stage4 forced-provider skill matching explicit and visible",
            "preserve frozen Stage5/6 provider metadata",
            "include source checkpoint/provider_version per job",
            "review binding manifest before running labels",
        ],
        "decision": {
            "status": (
                "contrast_label_plan_review_passed_binding_required"
                if allowed_to_bind
                else "contrast_label_plan_review_failed"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "labels_allowed_now": False,
            "recommended_next_step": (
                "bind_contrast_label_jobs_to_explicit_topologies"
                if allowed_to_bind
                else "fix_contrast_label_plan"
            ),
        },
        "blocked_next_steps": [
            "run_labels_without_binding_review",
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
    if review.get("causal_status") != "non_causal_plan_review":
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
    decision = review.get("decision") or {}
    if decision.get("runtime_arbiter_allowed") is not False:
        raise ValueError("runtime arbiter must remain blocked")
    if decision.get("labels_allowed_now") is not False:
        raise ValueError("labels must remain blocked until binding review")


def render_markdown(review: dict[str, Any]) -> str:
    summary = review["review_summary"]
    lines = [
        "# KRK Strategy Owner Contrast Label Plan Review v0",
        "",
        "This review checks the bounded non-causal label plan. It does not bind "
        "jobs, run labels, change runtime behavior, implement a selector, promote "
        "Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
        f"- Job count: `{summary['job_count']}`",
        f"- Jobs by stage: `{summary['job_count_by_stage']}`",
        f"- Provider counts: `{summary['provider_counts']}`",
        f"- Stage 7 jobs: `{summary['stage7_jobs']}`",
        f"- Violations: `{summary['violations']}`",
        f"- Allowed to bind execution manifest: `{summary['allowed_to_bind_execution_manifest']}`",
        f"- Allowed to run labels now: `{summary['allowed_to_run_labels']}`",
        "",
        "## Binding Requirements",
        "",
    ]
    for item in review["binding_requirements"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{review['decision']['status']}`",
            f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
            "- Runtime arbiter, selector sandbox, Stage 7 promotion, and Stage 8 training remain blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["review_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

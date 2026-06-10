#!/usr/bin/env python3
"""Review KRK strategy-arbiter out-of-sample execution manifest readiness.

This validates the manifest only. It does not execute labels, change runtime
behavior, implement a selector, promote Stage 7, train Stage 8, or mutate
topology.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_out_of_sample_execution_manifest_review_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_out_of_sample_execution_manifest_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    manifest = _load_json(MANIFEST)
    jobs = manifest.get("jobs") or []
    stage_counts = Counter(str(job.get("source_stage") or "unknown") for job in jobs)
    source_counts = Counter(str(job.get("source_kind") or "unknown") for job in jobs)
    target_semantics = Counter()
    invalid_jobs: list[dict[str, Any]] = []
    missing_paths: set[str] = set()
    for job in jobs:
        binding = job.get("execution_binding") or {}
        for path_key in ("topology_path", "source_checkpoint"):
            path = binding.get(path_key)
            if path and not (ROOT / str(path)).exists():
                missing_paths.add(str(path))
        for semantic in job.get("target_label_semantics") or []:
            target_semantics[str(semantic)] += 1
        problems = []
        if job.get("causal_status") != "non_causal_label_job":
            problems.append("job_not_non_causal")
        if job.get("labels_generated") is not False:
            problems.append("labels_already_generated")
        if job.get("stage7_training_row") is not False:
            problems.append("stage7_training_row_not_false")
        if job.get("source_stage") == "stage7":
            problems.append("stage7_job_present")
        if binding.get("composition_profile") != "handoff_composition_v1":
            problems.append("wrong_composition_profile")
        if binding.get("selected_provider_resolved_at_execution") is not True:
            problems.append("selected_provider_not_resolved_at_execution")
        if problems:
            invalid_jobs.append(
                {
                    "job_id": job.get("job_id"),
                    "state_id": job.get("state_id"),
                    "problems": problems,
                }
            )

    required_stage_coverage = {"stage4", "stage5", "stage6"}
    required_target_semantics = {
        "selected_playout_success",
        "forced_provider_conversion_for_selected_provider",
        "same_move_provider_compatibility_when_available",
        "guardrail_safe_ownership",
        "shadow_candidate_delta",
    }
    missing_stages = sorted(stage for stage in required_stage_coverage if stage_counts.get(stage, 0) == 0)
    missing_semantics = sorted(
        semantic for semantic in required_target_semantics if target_semantics.get(semantic, 0) == 0
    )
    binding_summary = manifest.get("binding_summary") or {}
    pass_review = (
        manifest.get("causal_status") == "non_causal_execution_manifest"
        and manifest.get("runtime_behavior_changed") is False
        and manifest.get("runtime_defaults_changed") is False
        and manifest.get("runtime_arbiter_implemented") is False
        and manifest.get("runtime_terminals_added") is False
        and manifest.get("runtime_dtm_or_tablebase_lookup") is False
        and manifest.get("gameplay_topology_mutation") is False
        and manifest.get("labels_generated_in_this_slice") is False
        and manifest.get("stage7_promotion_allowed") is False
        and manifest.get("stage8_training_allowed") is False
        and binding_summary.get("all_bindings_valid") is True
        and not missing_paths
        and not missing_stages
        and not missing_semantics
        and not invalid_jobs
    )
    return {
        "schema_version": "krk_strategy_arbiter_out_of_sample_execution_manifest_review.v0",
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
        "summary": {
            "job_count": len(jobs),
            "job_count_by_stage": dict(sorted(stage_counts.items())),
            "job_count_by_source_kind": dict(sorted(source_counts.items())),
            "target_semantic_counts": dict(sorted(target_semantics.items())),
            "missing_stage_coverage": missing_stages,
            "missing_target_semantics": missing_semantics,
            "missing_path_count": len(missing_paths),
            "missing_paths": sorted(missing_paths),
            "invalid_job_count": len(invalid_jobs),
            "invalid_jobs": invalid_jobs,
            "stage7_training_rows": sum(1 for job in jobs if job.get("stage7_training_row") is not False),
        },
        "risk_notes": [
            "This review validates manifest structure only; it does not prove h40 execution cost.",
            "The future label run should stop if runtime projects to hours.",
            "Generated curriculum samples are protected controls, not selector training from Stage7.",
        ],
        "decision": {
            "status": (
                "execution_manifest_review_passed_bounded_label_run_allowed"
                if pass_review
                else "execution_manifest_review_failed_fix_manifest_before_labels"
            ),
            "execute_labels_now": False,
            "bounded_label_run_allowed_after_review": pass_review,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "run_bounded_out_of_sample_control_labels"
                if pass_review
                else "fix_out_of_sample_execution_manifest"
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


def render_markdown(review: dict[str, Any]) -> str:
    summary = review["summary"]
    lines = [
        "# KRK Strategy Arbiter Out-of-Sample Execution Manifest Review v0",
        "",
        "This review validates the execution manifest only. It does not run h40 labels, "
        "change runtime behavior, implement a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
        f"- Job count: `{summary['job_count']}`",
        f"- Jobs by stage: `{summary['job_count_by_stage']}`",
        f"- Jobs by source kind: `{summary['job_count_by_source_kind']}`",
        f"- Missing stage coverage: `{summary['missing_stage_coverage']}`",
        f"- Missing target semantics: `{summary['missing_target_semantics']}`",
        f"- Missing path count: `{summary['missing_path_count']}`",
        f"- Invalid job count: `{summary['invalid_job_count']}`",
        f"- Stage 7 training rows: `{summary['stage7_training_rows']}`",
        f"- Decision: `{review['decision']['status']}`",
        "",
        "## Risk Notes",
        "",
    ]
    lines.extend(f"- {note}" for note in review["risk_notes"])
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            f"`{review['decision']['recommended_next_step']}`",
            "",
            "This authorizes only a bounded non-causal label run after review; it does not authorize a runtime arbiter or selector sandbox.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    review = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(review), encoding="utf-8")
    print(json.dumps(review["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

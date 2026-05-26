#!/usr/bin/env python3
"""Write a follow-up Stage 7 clean sampling manifest for the remaining success gap.

This manifest is review-only. It uses the post-label distribution review to
target source cells that produced genuinely new clean success controls, but it
does not execute labels or authorize runtime/training/promotion changes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_STACK = ROOT / "reports/krk_active_protected_stack_v0.json"
LABEL_DISTRIBUTION_REVIEW = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.json"
)
OUT_JSON = ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
OUT_MD = ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.md"

SCHEMA_VERSION = "stage7_additional_clean_sampling_manifest.v0"

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

FORBIDDEN_FLAGS = [
    "--enable-stage7-king-tempo",
    "--enable-stage7-drive-repair",
    "--enable-stage7-post-king-tempo",
    "--enable-stage7-post-box-continuation",
    "--enable-stage7-learned-post-box-continuation",
    "--enable-stage7-post-box-frozen-model-candidate",
    "--enable-stage7-plan-capsule",
    "--enable-candidate-move-layer",
    "--enable-stage7-king-support-fence-stabilizer",
    "--enable-krk-strategy-arbiter-sandbox",
    "--enable-krk-two-stage-abstention-selector",
    "--enable-krk-progress-window-reconsideration",
]

FOLLOWUP_CELLS = [
    ("edge_fence_deep_followup_a", "Edge_Fence_Deep", 149),
    ("edge_fence_deep_followup_b", "Edge_Fence_Deep", 151),
    ("edge_fence_deep_followup_c", "Edge_Fence_Deep", 157),
    ("edge_fence_deep_followup_d", "Edge_Fence_Deep", 163),
]


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _active_topology(active_stack: dict[str, Any]) -> str:
    topology = (
        active_stack.get("active_protected_stack", {})
        .get("stage6_drive_overlay", {})
        .get("topology")
    )
    if not topology:
        raise ValueError("active Stage 6 topology missing from active stack manifest")
    return str(topology)


def _job(cell_id: str, source_stage_names: str, seed: int, topology: str) -> dict[str, Any]:
    output = (
        "reports/structural_candidates/"
        f"stage7_additional_clean_{cell_id}_seed{seed}_8_h40.json"
    )
    command = [
        "uv",
        "run",
        "python",
        "scripts/test_krk_landmark_progress.py",
        "--topology",
        topology,
        "--label",
        "box_shrink",
        "--samples",
        "8",
        "--seed",
        str(seed),
        "--position-mode",
        "curriculum",
        "--source-stage-names",
        source_stage_names,
        "--playout-max-plies",
        "40",
        "--composition-profile",
        "handoff_composition_v1",
        "--enable-diagnostic-caches",
        "--early-stop-stable-suggestions",
        "2",
        "--json-output",
        output,
        "--no-json-stdout",
    ]
    return {
        "schema_version": "stage7_additional_clean_sampling_job.v0",
        "job_id": f"stage7.additional_clean.{cell_id}.seed{seed}.samples8.h40",
        "purpose": "recover_one_remaining_unique_clean_stage7_success_control",
        "label": "box_shrink",
        "source_stage_names": source_stage_names.split(","),
        "seed": seed,
        "samples": 8,
        "playout_max_plies": 40,
        "composition_profile": "handoff_composition_v1",
        "topology": topology,
        "json_output": output,
        "forbidden_flags": FORBIDDEN_FLAGS,
        "command": command,
        "runtime_work_allowed": False,
        "stage7_training_row": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }


def build_payload(
    *,
    active_stack: dict[str, Any] | None = None,
    label_distribution_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_stack = active_stack or _load(ACTIVE_STACK)
    label_distribution_review = label_distribution_review or _load(LABEL_DISTRIBUTION_REVIEW)
    topology = _active_topology(active_stack)
    jobs = [_job(cell_id, sources, seed, topology) for cell_id, sources, seed in FOLLOWUP_CELLS]
    review_summary = label_distribution_review.get("summary") or {}
    guidance = label_distribution_review.get("followup_sampling_guidance") or {}
    success_gap = int(review_summary.get("success_gap") or 0)
    highest_yield = guidance.get("highest_yield_job_ids") or []
    success_gate_closed = success_gap <= 0
    scheduled_jobs = [] if success_gate_closed else jobs
    status = (
        "stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed"
        if success_gate_closed
        else "stage7_additional_clean_sampling_manifest_ready_pending_explicit_approval"
    )
    next_step = (
        "rerun_passive_sequence_policy_gate_stack"
        if success_gate_closed
        else "dry_run_validate_stage7_additional_clean_sampling_manifest"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_label_manifest_review_only",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_active_protected_stack_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.json",
        ],
        "review_basis": {
            "label_distribution_review_status": (
                label_distribution_review.get("decision") or {}
            ).get("status"),
            "success_gap": success_gap,
            "unique_new_success_key_count_vs_pre_run": review_summary.get(
                "unique_new_success_key_count_vs_pre_run"
            ),
            "duplicate_playout_count": review_summary.get("duplicate_playout_count"),
            "highest_yield_prior_job_ids": highest_yield,
            "same_manifest_reuse_expected_to_help": guidance.get(
                "reuse_same_manifest_without_overwrite_expected_to_help"
            ),
        },
        "sampling_policy": {
            "max_jobs": len(scheduled_jobs),
            "samples_per_job": 8,
            "max_total_samples": len(scheduled_jobs) * 8,
            "max_horizon": 40,
            "source_bias": "edge_fence_deep_followup_from_distribution_review",
            "stage7_rows_are_labels_only_not_training_rows": True,
            "requires_explicit_approval_before_execution": not success_gate_closed,
            "closed_reason": "stage7_success_gate_closed"
            if success_gate_closed
            else None,
        },
        "jobs": scheduled_jobs,
        "summary": {
            "job_count": len(scheduled_jobs),
            "max_total_samples": len(scheduled_jobs) * 8,
            "candidate_job_count_if_gap_reopens": len(jobs),
            "success_gap_target": success_gap,
            "topology_exists": (ROOT / topology).exists(),
            "runtime_work_allowed": False,
            "label_run_allowed_by_this_manifest": False,
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
            "stage8_training_allowed": False,
        },
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "implementation_authorized_by_this_manifest": False,
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "explicitly_forbidden": [
            "running_this_manifest_without_explicit_approval",
            "stage7_promotion",
            "stage8_training",
            "runtime_selector_or_arbiter",
            "stage7_support_adapter_or_score_bonus",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    review = payload["review_basis"]
    summary = payload["summary"]
    if summary.get("job_count") == 0 and review.get("success_gap") == 0:
        description = (
            "This review-only follow-up label manifest is not applicable because "
            "the Stage 7 clean success-control gate is closed. It does not "
            "authorize execution."
        )
    else:
        description = (
            "This is a review-only follow-up label manifest for the remaining "
            "Stage 7 clean success-control gap. It does not authorize execution."
        )
    lines = [
        "# Stage 7 Additional Clean Sampling Manifest v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        description,
        "",
        "## Review Basis",
        "",
    ]
    for key, value in review.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Sampling Policy", ""])
    for key, value in payload["sampling_policy"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Jobs", ""])
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['job_id']}` sources=`{job['source_stage_names']}` "
            f"seed=`{job['seed']}` samples=`{job['samples']}`"
        )
    lines.extend(["", "## Decision", ""])
    lines.append(f"- recommended_next_step: `{decision['recommended_next_step']}`")
    lines.append("- runtime_changes_allowed: `false`")
    lines.append("- label_run_allowed: `false`")
    lines.append("- selector_training_allowed: `false`")
    lines.append("- stage7_promotion_allowed: `false`")
    lines.append("- stage8_training_allowed: `false`")
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

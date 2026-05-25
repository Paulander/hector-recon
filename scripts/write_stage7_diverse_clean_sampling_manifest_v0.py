#!/usr/bin/env python3
"""Write a reviewed diverse Stage 7 clean-control sampling manifest v0.

This manifest is a non-causal run plan only. It exists because replay-free
Stage 7 clean-control recovery has enough hard negatives but too few unique
success controls, and the previous bounded label job overlapped existing
samples. The jobs below are source-family/seed stratified and capped, but still
require explicit approval before execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_STACK = ROOT / "reports/krk_active_protected_stack_v0.json"
RECOVERY = ROOT / "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json"
SAMPLING_REVIEW = ROOT / "reports/structural_candidates/stage7_clean_control_sampling_review_v0.json"
OUTPUT_JSON = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
OUTPUT_MD = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.md"

SCHEMA_VERSION = "stage7_diverse_clean_sampling_manifest.v0"


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


SOURCE_CELLS = [
    ("box_small", "Box_Small", 101),
    ("box_medium", "Box_Medium", 103),
    ("edge_fence_deep", "Edge_Fence_Deep", 107),
    ("box_small_medium", "Box_Small,Box_Medium", 109),
    ("box_medium_edge_deep", "Box_Medium,Edge_Fence_Deep", 113),
    ("all_stage7_sources_a", "Box_Small,Box_Medium,Edge_Fence_Deep", 127),
    ("all_stage7_sources_b", "Box_Small,Box_Medium,Edge_Fence_Deep", 131),
    ("all_stage7_sources_c", "Box_Small,Box_Medium,Edge_Fence_Deep", 137),
]


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


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        f"stage7_diverse_clean_{cell_id}_seed{seed}_8_h40.json"
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
        "schema_version": "stage7_diverse_clean_sampling_job.v0",
        "job_id": f"stage7.diverse_clean.{cell_id}.seed{seed}.samples8.h40",
        "purpose": "recover_diverse_clean_stage7_sequence_controls",
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
    recovery: dict[str, Any] | None = None,
    sampling_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active_stack = active_stack or _load(ACTIVE_STACK)
    recovery = recovery or _load(RECOVERY)
    sampling_review = sampling_review or _load(SAMPLING_REVIEW)
    topology = _active_topology(active_stack)
    jobs = [_job(cell_id, sources, seed, topology) for cell_id, sources, seed in SOURCE_CELLS]
    success_have = int(
        recovery.get("acceptance", {}).get("clean_sequence_success_controls_required", 5)
    )
    current_success = int(
        recovery.get("summary", {}).get("role_counts", {}).get("clean_sequence_success_control", 0)
    )
    current_hard_negatives = int(
        recovery.get("summary", {}).get("role_counts", {}).get("clean_sequence_hard_negative", 0)
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_label_manifest_review_only",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_active_protected_stack_v0.json",
            "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json",
            "reports/structural_candidates/stage7_clean_control_sampling_review_v0.json",
        ],
        "current_gap": {
            "clean_sequence_success_controls_have": current_success,
            "clean_sequence_success_controls_required": success_have,
            "clean_sequence_hard_negatives_have": current_hard_negatives,
            "sampling_overlap_detected": bool(
                sampling_review.get("summary", {}).get("sampling_overlap_detected")
            ),
        },
        "sampling_policy": {
            "max_jobs": len(jobs),
            "samples_per_job": 8,
            "max_total_samples": len(jobs) * 8,
            "max_horizon": 40,
            "stage7_rows_are_labels_only_not_training_rows": True,
            "stop_after_this_manifest_if_overlap_repeats": True,
            "requires_explicit_approval_before_execution": True,
        },
        "jobs": jobs,
        "summary": {
            "job_count": len(jobs),
            "max_total_samples": len(jobs) * 8,
            "unique_source_cell_count": len({tuple(job["source_stage_names"]) for job in jobs}),
            "topology_exists": (ROOT / topology).exists(),
            "runtime_work_allowed": False,
            "label_run_allowed_by_this_manifest": False,
            "stage7_training_row_count": 0,
            "stage8_training_allowed": False,
        },
        "decision": {
            "status": "stage7_diverse_clean_sampling_manifest_review_ready_pending_explicit_approval",
            "recommended_next_step": "approve_or_reject_bounded_diverse_stage7_clean_label_run",
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
    gap = payload["current_gap"]
    summary = payload["summary"]
    lines = [
        "# Stage 7 Diverse Clean Sampling Manifest v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "This is a reviewed label-run manifest only. It does not authorize execution by itself.",
        "",
        "## Current Gap",
        "",
        f"- clean_sequence_success_controls_have: `{gap['clean_sequence_success_controls_have']}`",
        f"- clean_sequence_success_controls_required: `{gap['clean_sequence_success_controls_required']}`",
        f"- clean_sequence_hard_negatives_have: `{gap['clean_sequence_hard_negatives_have']}`",
        f"- sampling_overlap_detected: `{gap['sampling_overlap_detected']}`",
        "",
        "## Sampling Policy",
        "",
        f"- job_count: `{summary['job_count']}`",
        f"- max_total_samples: `{summary['max_total_samples']}`",
        f"- unique_source_cell_count: `{summary['unique_source_cell_count']}`",
        f"- topology_exists: `{summary['topology_exists']}`",
        "- h40 only",
        "- Stage 7 labels are held-out challenge evidence, not training rows.",
        "- Explicit approval is required before running.",
        "",
        "## Jobs",
        "",
    ]
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['job_id']}` sources=`{job['source_stage_names']}` "
            f"seed=`{job['seed']}` samples=`{job['samples']}`"
        )
    lines.extend([
        "",
        "## Forbidden",
        "",
    ])
    lines.extend(f"- {item}" for item in payload["explicitly_forbidden"])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "job_count": payload["summary"]["job_count"],
        "max_total_samples": payload["summary"]["max_total_samples"],
    }, indent=2))


if __name__ == "__main__":
    main()

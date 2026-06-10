#!/usr/bin/env python3
"""Plan bounded protected KRK strategy-owner contrast labels.

This creates non-causal label jobs only. It does not run playouts, implement a
runtime arbiter, change defaults, promote Stage 7, or train Stage 8.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRAST = Path("reports/krk_strategy_owner_contrast_dataset_v0.json")
FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
BALANCED = Path("reports/krk_selector_balanced_label_dataset_v1.json")
READINESS = Path("reports/krk_selector_readiness_v2_plan.json")
OUT_JSON = Path("reports/krk_strategy_owner_contrast_label_plan_v0.json")
OUT_MD = Path("reports/krk_strategy_owner_contrast_label_plan_v0.md")


PROTECTED_PROVIDERS_BY_STAGE = {
    "stage4": [
        "krk.edge_trap_wrong_tempo",
        "krk.edge_trap_close",
        "krk.fence_established",
    ],
    "stage5": [
        "krk.edge_trap_close",
        "krk.edge_trap_enemy_between",
        "krk.edge_trap_wrong_tempo",
        "krk.fence_established",
    ],
    "stage6": [
        "krk.drive_to_edge",
        "krk.fence_established",
        "krk.edge_trap_close",
    ],
}

EXECUTION_LANDMARK_BY_STAGE = {
    "stage4": "edge_trap_wrong_tempo",
    "stage5": "fence_established",
    "stage6": "drive_to_edge",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _job_id(state_id: str, provider_id: str) -> str:
    raw = f"{state_id}|{provider_id}|strategy_owner_contrast_v0".encode("utf-8")
    return "job.krk.strategy_owner_contrast." + hashlib.sha1(raw).hexdigest()[:12]


def _existing_labeled_pairs(contrast: dict[str, Any]) -> set[tuple[str, str]]:
    pairs = set()
    for row in contrast.get("rows") or []:
        state_id = str(row.get("state_id") or "")
        for label in row.get("provider_labels") or []:
            provider_id = str(label.get("provider_id") or "")
            if state_id and provider_id:
                pairs.add((state_id, provider_id))
    return pairs


def _candidate_states(frames: dict[str, Any], balanced: dict[str, Any]) -> list[dict[str, Any]]:
    frame_by_state = {frame.get("state_id"): frame for frame in frames.get("frames") or []}
    seen: set[str] = set()
    candidates = []
    for row in balanced.get("rows") or []:
        stage = str(row.get("source_stage") or "")
        state_id = str(row.get("state_id") or "")
        if stage not in PROTECTED_PROVIDERS_BY_STAGE or not state_id or state_id in seen:
            continue
        frame = frame_by_state.get(state_id)
        if not frame:
            continue
        candidates.append(
            {
                "state_id": state_id,
                "frame_id": frame.get("frame_id"),
                "source_stage": stage,
                "active_landmark_label": frame.get("active_landmark_label"),
                "fen": frame.get("fen"),
                "source_label": row.get("label"),
                "source_provider_id": row.get("provider_id"),
                "source_target_kind": row.get("target_kind"),
            }
        )
        seen.add(state_id)
    return candidates


def build_plan(*, max_jobs: int = 12, max_jobs_per_stage: int = 4) -> dict[str, Any]:
    contrast = _load_json(CONTRAST)
    frames = _load_json(FRAMES)
    balanced = _load_json(BALANCED)
    readiness = _load_json(READINESS)
    if contrast.get("causal_status") != "non_causal_dataset":
        raise ValueError("contrast dataset must remain non-causal")
    if frames.get("causal_status") != "non_causal_augmented_frame_export":
        raise ValueError("frames must remain non-causal")
    if balanced.get("causal_status") != "non_causal_balanced_label_dataset":
        raise ValueError("balanced labels must remain non-causal")
    if readiness.get("causal_status") != "non_causal_design_plan":
        raise ValueError("readiness plan must remain non-causal")

    existing = _existing_labeled_pairs(contrast)
    stage_counts: Counter[str] = Counter()
    jobs = []
    for state in _candidate_states(frames, balanced):
        stage = state["source_stage"]
        if stage_counts[stage] >= max_jobs_per_stage:
            continue
        for provider_id in PROTECTED_PROVIDERS_BY_STAGE[stage]:
            if len(jobs) >= max_jobs or stage_counts[stage] >= max_jobs_per_stage:
                break
            if (state["state_id"], provider_id) in existing:
                continue
            jobs.append(
                {
                    "schema_version": "krk_strategy_owner_contrast_label_job.v0",
                    "causal_status": "non_causal_label_job",
                    "labels_generated": False,
                    "runtime_behavior_changed": False,
                    "job_id": _job_id(state["state_id"], provider_id),
                    "state_id": state["state_id"],
                    "frame_id": state["frame_id"],
                    "source_stage": stage,
                    "active_landmark_label": EXECUTION_LANDMARK_BY_STAGE[stage],
                    "source_active_landmark_label": state["active_landmark_label"],
                    "fen": state["fen"],
                    "provider_id": provider_id,
                    "horizon": 40,
                    "trace_mode": "failures_only",
                    "diagnostic_caches_required": True,
                    "target_label_semantics": "forced_provider_first_white_move_then_release",
                    "purpose": "Fill protected non-stage0 strategy-owner contrast evidence without using Stage 7 training rows.",
                    "source_selected_label": {
                        "label": state["source_label"],
                        "provider_id": state["source_provider_id"],
                        "target_kind": state["source_target_kind"],
                    },
                }
            )
            stage_counts[stage] += 1

    plan = {
        "schema_version": "krk_strategy_owner_contrast_label_plan.v0",
        "causal_status": "non_causal_label_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(CONTRAST), str(FRAMES), str(BALANCED), str(READINESS)],
        "job_selection": {
            "max_jobs": max_jobs,
            "max_jobs_per_stage": max_jobs_per_stage,
            "selected_job_count": len(jobs),
            "selected_job_count_by_stage": dict(sorted(stage_counts.items())),
            "stage7_jobs": 0,
        },
        "jobs": jobs,
        "execution_preconditions": [
            "review_plan_before_execution",
            "bind_all_jobs_to_handoff_composition_v1_or_stage6_overlay_composed_topology",
            "confirm_stage4_forced-provider binding is explicit and visible",
            "run h40 only",
            "trace failures only",
            "diagnostic caches enabled",
            "stop if projected runtime is hours",
        ],
        "decision": {
            "status": "protected_strategy_owner_contrast_label_plan_defined_execution_review_required",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "review_and_bind_bounded_contrast_label_plan_before_execution",
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
    validate_plan(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("causal_status") != "non_causal_label_plan":
        raise ValueError("plan must remain non-causal")
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
        if plan.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for job in plan.get("jobs") or []:
        if job.get("causal_status") != "non_causal_label_job":
            raise ValueError("jobs must remain non-causal")
        if job.get("labels_generated") is not False:
            raise ValueError("jobs must not claim labels")
        if job.get("source_stage") == "stage7":
            raise ValueError("Stage 7 must remain held out")


def render_markdown(plan: dict[str, Any]) -> str:
    selection = plan["job_selection"]
    lines = [
        "# KRK Strategy Owner Contrast Label Plan v0",
        "",
        "This is a bounded non-causal label plan. It does not run labels, "
        "change runtime behavior, implement an arbiter, promote Stage 7, or train Stage 8.",
        "",
        "## Job Selection",
        "",
        f"- Jobs: `{selection['selected_job_count']}`",
        f"- Jobs by stage: `{selection['selected_job_count_by_stage']}`",
        f"- Stage 7 jobs: `{selection['stage7_jobs']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{plan['decision']['status']}`",
        f"- Recommended next step: `{plan['decision']['recommended_next_step']}`",
        "- Runtime arbiter and selector sandbox remain blocked.",
        "",
        "## Execution Preconditions",
        "",
    ]
    for item in plan["execution_preconditions"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Jobs", ""])
    for job in plan["jobs"]:
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` state=`{job['state_id']}` "
            f"provider=`{job['provider_id']}`"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    plan = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(plan), encoding="utf-8")
    print(json.dumps(plan["job_selection"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

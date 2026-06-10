#!/usr/bin/env python3
"""Write a bounded protected plan-window failure-contrast collection manifest.

The manifest is a review artifact only. It binds candidate seed contexts for a
future explicitly approved observation-only trace collection, but it does not
execute labels, change runtime behavior, train selectors, promote Stage 7, or
authorize Stage 8.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_STACK = ROOT / "reports/krk_active_protected_stack_v0.json"
PLAN = (
    ROOT / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json"
)
PROTECTED_WINDOWS = ROOT / "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json"
OUTPUT_JSON = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
OUTPUT_MD = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.md"
)

SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_manifest.v0"
MAX_COLLECTION_JOBS = 6

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

OUTPUT_ROOT = Path("reports/strategy_arbitration/protected_plan_window_failure_contrasts")
FORBIDDEN_JOB_FLAGS = (
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


TARGETS = [
    {
        "source_stage": "stage5",
        "source_family": "fence_handoff_plan_window",
        "target_failure_mode": "fence_handoff_abort_or_max_plies",
        "priority": "high_no_current_stage_failure_contrast",
        "take": 2,
    },
    {
        "source_stage": "stage6",
        "source_family": "drive_to_edge_plan_window",
        "target_failure_mode": "drive_to_edge_abort_or_max_plies",
        "priority": "high_no_current_stage_failure_contrast",
        "take": 2,
    },
    {
        "source_stage": "stage4",
        "source_family": "wrong_tempo_plan_window",
        "target_failure_mode": "wrong_tempo_stage0_or_handoff_abort",
        "priority": "medium_existing_stage_failure_contrast",
        "take": 2,
    },
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


def _safe_relative(path_value: Any, *, required_root: Path | None = None) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        return False
    if required_root is None:
        return True
    return path.parts[: len(required_root.parts)] == required_root.parts


def _safe_output_path(path_value: Any) -> bool:
    return _safe_relative(path_value, required_root=OUTPUT_ROOT)


def _forbidden_job_flag_count(jobs: list[dict[str, Any]]) -> int:
    return sum(1 for job in jobs if any(job.get(flag) is True for flag in FORBIDDEN_JOB_FLAGS))


def _manifest_fingerprint_from_parts(
    *,
    jobs: list[dict[str, Any]],
    constraints: dict[str, Any],
    summary: dict[str, Any],
) -> str:
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
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_collection_manifest",
        "collection_constraints": constraints,
        "summary": fingerprint_summary,
        "jobs": jobs,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _success_frames(payload: dict[str, Any], *, source_stage: str, source_family: str) -> list[dict[str, Any]]:
    return [
        frame
        for frame in payload.get("frames") or []
        if frame.get("source_stage") == source_stage
        and frame.get("source_family") == source_family
        and frame.get("outcome_bucket") == "success"
    ]


def _job_from_frame(
    frame: dict[str, Any],
    *,
    index: int,
    target: dict[str, Any],
    topology: str,
) -> dict[str, Any]:
    job_id = f"protected_plan_failure.{index:02d}.{frame['frame_id']}"
    return {
        "schema_version": "krk_protected_plan_window_failure_contrast_job.v0",
        "job_id": job_id,
        "source_stage": frame.get("source_stage"),
        "source_family": frame.get("source_family"),
        "seed_frame_id": frame.get("frame_id"),
        "seed_fen": frame.get("fen"),
        "anchor_move_uci": frame.get("move_uci"),
        "active_landmark_label": frame.get("active_landmark_label"),
        "seed_result": frame.get("result"),
        "seed_h40_outcome_label": frame.get("h40_outcome_label"),
        "handoff_targets": frame.get("handoff_targets") or [],
        "selected_successor": frame.get("selected_successor"),
        "selected_successor_contract_met": frame.get("selected_successor_contract_met"),
        "target_failure_mode": target["target_failure_mode"],
        "priority": target["priority"],
        "horizon": 40,
        "collection_mode": "observation_only_trace_collection_pending_explicit_approval",
        "expected_output_json": (
            "reports/strategy_arbitration/protected_plan_window_failure_contrasts/"
            f"{job_id}.json"
        ),
        "failure_label_goal": "conversion_failure",
        "expected_output_group": "protected_plan_window_failure_contrast",
        "execution_binding": {
            "topology_path": topology,
            "composition_profile": "handoff_composition_v1",
            "black_policy": "adversarial",
            "max_ticks": 200,
            "suggestion_limit": 10,
            "early_stop_stable_suggestions": 2,
            "enable_diagnostic_caches": True,
            "trace_failures_only": True,
            "profile_settings": {
                "successor_affordance_layer_enabled": True,
                "successor_role_license_enabled": True,
                "successor_role_scoped_move_shape_enabled": True,
                "successor_role_scoped_move_shape_bonus": 0.05,
                "stagnation_breaker_enabled": True,
                "stagnation_breaker_bonus": 0.5,
                "post_break_continuation_enabled": True,
                "post_break_continuation_bonus": 0.25,
                "successor_stage0_drift_penalty": 6.0,
            },
        },
        "labels_generated": False,
        "usable_for_selector_training": False,
        "usable_for_runtime_authorization": False,
        "stage7_heldout_challenge": False,
        "runtime_behavior_changed": False,
        "causal_status": "non_causal_collection_manifest_job",
    }


def build_payload(
    *,
    plan: dict[str, Any] | None = None,
    protected_windows: dict[str, Any] | None = None,
    active_stack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = plan or _load(PLAN)
    protected_windows = protected_windows or _load(PROTECTED_WINDOWS)
    active_stack = active_stack or _load(ACTIVE_STACK)
    topology = _active_topology(active_stack)
    failure_gap = int(
        plan.get("summary", {}).get("minimum_new_unique_failures_needed") or 0
    )
    jobs: list[dict[str, Any]] = []
    for target in TARGETS:
        frames = _success_frames(
            protected_windows,
            source_stage=target["source_stage"],
            source_family=target["source_family"],
        )
        for frame in frames[: int(target["take"])]:
            jobs.append(
                _job_from_frame(
                    frame,
                    index=len(jobs) + 1,
                    target=target,
                    topology=topology,
                )
            )
    jobs = jobs[:MAX_COLLECTION_JOBS]
    stage_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for job in jobs:
        stage_counts[str(job["source_stage"])] = stage_counts.get(str(job["source_stage"]), 0) + 1
        family_counts[str(job["source_family"])] = (
            family_counts.get(str(job["source_family"]), 0) + 1
        )
    required_stages = {"stage4", "stage5", "stage6"}
    missing_stages = sorted(required_stages - set(stage_counts))
    topology_path_safe = _safe_relative(topology)
    topology_exists = topology_path_safe and (ROOT / topology).exists()
    output_paths_valid = all(_safe_output_path(job.get("expected_output_json")) for job in jobs)
    forbidden_job_flag_count = _forbidden_job_flag_count(jobs)
    bindings_valid = (
        failure_gap > 0
        and 0 < len(jobs) <= MAX_COLLECTION_JOBS
        and not missing_stages
        and all(job.get("horizon") == 40 for job in jobs)
        and topology_path_safe
        and topology_exists
        and output_paths_valid
        and forbidden_job_flag_count == 0
    )
    status = (
        "protected_plan_window_failure_contrast_manifest_ready_for_review"
        if bindings_valid
        else "protected_plan_window_failure_contrast_manifest_blocked"
    )
    constraints = {
        "requires_explicit_approval_before_collection": True,
        "observation_only": True,
        "horizon": 40,
        "stop_after_unique_failures": failure_gap,
        "no_runtime_default_change": True,
        "no_runtime_dtm_or_tablebase": True,
        "no_gameplay_topology_mutation": True,
        "no_stage7_promotion": True,
        "no_stage8_training": True,
    }
    summary = {
        "job_count": len(jobs),
        "max_collection_jobs": MAX_COLLECTION_JOBS,
        "minimum_new_unique_failures_needed": failure_gap,
        "target_failure_label_goal": "conversion_failure",
        "source_stage_counts": stage_counts,
        "source_family_counts": family_counts,
        "missing_required_source_stages": missing_stages,
        "all_bindings_valid": bindings_valid,
        "topology_path": topology,
        "topology_path_safe": topology_path_safe,
        "topology_exists": topology_exists,
        "output_paths_valid": output_paths_valid,
        "forbidden_job_flag_count": forbidden_job_flag_count,
        "selector_training_row_count": 0,
        "runtime_authorization_row_count": 0,
        "stage7_training_row_count": 0,
    }
    summary["manifest_fingerprint"] = _manifest_fingerprint_from_parts(
        jobs=jobs,
        constraints=constraints,
        summary=summary,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_collection_manifest",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json",
            "reports/krk_active_protected_stack_v0.json",
        ],
        "summary": summary,
        "collection_constraints": constraints,
        "jobs": jobs,
        "decision": {
            "status": status,
            "recommended_next_step": "review_protected_plan_window_failure_contrast_manifest",
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
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Protected Plan-Window Failure Contrast Manifest v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a bounded non-causal collection manifest for review. It does not execute collection, run labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Jobs", ""])
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` family=`{job['source_family']}` seed=`{job['seed_frame_id']}` target=`{job['target_failure_mode']}`"
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

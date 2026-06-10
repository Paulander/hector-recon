#!/usr/bin/env python3
"""Bind protected missing-provider capacity audit jobs for execution review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_protected_missing_provider_capacity_audit_plan_v0.json")
OUT_JSON = Path("reports/krk_protected_missing_provider_capacity_execution_manifest_v0.json")
OUT_MD = Path("reports/krk_protected_missing_provider_capacity_execution_manifest_v0.md")
TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)


PROFILE_SETTINGS = {
    "successor_affordance_layer_enabled": True,
    "successor_role_license_enabled": True,
    "successor_role_scoped_move_shape_enabled": True,
    "successor_role_scoped_move_shape_bonus": 0.05,
    "stagnation_breaker_enabled": True,
    "stagnation_breaker_bonus": 0.5,
    "post_break_continuation_enabled": True,
    "post_break_continuation_bonus": 0.25,
    "successor_stage0_drift_penalty": 6.0,
}


PROVIDER_VERSION = {
    "krk.stage0_basin": "foundation_frozen_v1",
    "krk.edge_trap_close": "stage5_validated_v1",
    "krk.edge_trap_wrong_tempo": "stage5_validated_v1",
    "krk.edge_trap_enemy_between": "stage5_validated_v1",
    "krk.fence_established": "stage5_validated_v1",
    "krk.drive_to_edge": "stage6_overlay_v1",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _contains_value(payload: Any, needle: str) -> bool:
    if isinstance(payload, dict):
        return any(_contains_value(value, needle) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_value(value, needle) for value in payload)
    return payload == needle


def build_manifest() -> dict[str, Any]:
    plan = _load(PLAN)
    topology_exists = (ROOT / TOPOLOGY).exists()
    topology_payload = _load(TOPOLOGY) if topology_exists else {}
    jobs = []
    missing_provider_skill_ids = []
    for job in plan.get("jobs") or []:
        provider_id = str(job.get("provider_id") or "")
        if topology_payload and not _contains_value(topology_payload, provider_id):
            missing_provider_skill_ids.append(provider_id)
        bound = {
            **job,
            "schema_version": "krk_protected_missing_provider_capacity_execution_job.v0",
            "labels_generated": False,
            "runtime_behavior_changed": False,
            "execution_binding": {
                "execution_mode": "force_provider_first_white_move_then_release",
                "topology_path": str(TOPOLOGY),
                "topology_version": "stage6_overlay_composed_v1",
                "composition_profile": "handoff_composition_v1",
                "black_policy": "adversarial",
                "trace_mode": "failures_only",
                "enable_diagnostic_caches": True,
                "early_stop_stable_suggestions": 3,
                "max_ticks": 200,
                "suggestion_limit": 10,
                "plasticity_scope": "protected_frozen",
                "provider_version": PROVIDER_VERSION.get(provider_id, "unknown_provider_version"),
                "profile_settings": PROFILE_SETTINGS,
            },
        }
        jobs.append(bound)
    missing_provider_skill_ids = sorted(set(missing_provider_skill_ids))
    all_bindings_valid = topology_exists and not missing_provider_skill_ids and len(jobs) <= 36
    return {
        "schema_version": "krk_protected_missing_provider_capacity_execution_manifest.v0",
        "causal_status": "non_causal_execution_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN)],
        "jobs": jobs,
        "binding_summary": {
            "job_count": len(jobs),
            "topology_path": str(TOPOLOGY),
            "topology_exists": topology_exists,
            "missing_provider_skill_ids": missing_provider_skill_ids,
            "stage7_jobs": sum(1 for job in jobs if job.get("source_stage") == "stage7"),
            "all_bindings_valid": all_bindings_valid,
        },
        "decision": {
            "status": "protected_missing_provider_capacity_execution_manifest_bound",
            "recommended_next_step": "review_protected_missing_provider_capacity_execution_manifest",
            "labels_allowed_now": False,
            "runtime_work_allowed": False,
        },
        "blocked_actions": [
            "run_labels_without_manifest_review",
            "runtime_selector_changes",
            "Stage 7 repair or promotion",
            "Stage 8 training",
            "runtime DTM/tablebase use",
            "gameplay topology mutation",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Protected Missing-Provider Capacity Execution Manifest v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Bound execution manifest for protected missing-provider/capacity labels. It does not execute labels.",
        "",
        "## Binding Summary",
        "",
    ]
    for key, value in payload["binding_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Jobs", ""])
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` provider=`{job['provider_id']}` "
            f"version=`{job['execution_binding']['provider_version']}`"
        )
    lines.extend(["", f"Recommended next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_manifest()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()

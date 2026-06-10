#!/usr/bin/env python3
"""Bind KRK strategy-owner contrast label jobs to explicit topology metadata.

This creates an execution manifest only. It does not run labels, change
runtime behavior, implement a selector, promote Stage 7, or train Stage 8.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_strategy_owner_contrast_label_plan_v0.json")
REVIEW = Path("reports/krk_strategy_owner_contrast_label_plan_review_v0.json")
OUT_JSON = Path("reports/krk_strategy_owner_contrast_execution_manifest_v0.json")
OUT_MD = Path("reports/krk_strategy_owner_contrast_execution_manifest_v0.md")

STAGE6_TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
STAGE5_CHECKPOINT = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl"
)
STAGE6_CHECKPOINT = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/best_by_stage/drive_to_edge.pkl"
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


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_binding(provider_id: str) -> dict[str, Any]:
    if provider_id == "krk.drive_to_edge":
        return {
            "provider_version": "stage6_overlay_v1",
            "source_checkpoint": str(STAGE6_CHECKPOINT),
            "topology_component": "stage6_overlay_provider",
            "plasticity_scope": "overlay_validated_low_plasticity",
        }
    return {
        "provider_version": "stage5_validated_v1",
        "source_checkpoint": str(STAGE5_CHECKPOINT),
        "topology_component": "stage5_frozen_base_provider_pack",
        "plasticity_scope": "protected_frozen",
    }


def _binding_for_job(job: dict[str, Any]) -> dict[str, Any]:
    provider_id = str(job.get("provider_id") or "")
    provider = _provider_binding(provider_id)
    return {
        "topology_path": str(STAGE6_TOPOLOGY),
        "topology_version": "stage6_overlay_composed_v1",
        "composition_profile": "handoff_composition_v1",
        "execution_mode": "force_provider_first_white_move_then_release",
        "black_policy": "adversarial",
        "max_ticks": 200,
        "suggestion_limit": 10,
        "early_stop_stable_suggestions": 3,
        "enable_diagnostic_caches": True,
        "profile_settings": dict(PROFILE_SETTINGS),
        **provider,
    }


def build_manifest() -> dict[str, Any]:
    plan = _load_json(PLAN)
    review = _load_json(REVIEW)
    if plan.get("causal_status") != "non_causal_label_plan":
        raise ValueError("label plan must remain non-causal")
    if review.get("causal_status") != "non_causal_plan_review":
        raise ValueError("plan review must remain non-causal")
    if not (review.get("review_summary") or {}).get("allowed_to_bind_execution_manifest"):
        raise ValueError("plan review must allow binding before manifest creation")

    topology_text = (ROOT / STAGE6_TOPOLOGY).read_text(encoding="utf-8")
    missing_paths = []
    missing_provider_skill_ids = []
    jobs = []
    for job in plan.get("jobs") or []:
        binding = _binding_for_job(job)
        for path_key in ("topology_path", "source_checkpoint"):
            if not (ROOT / binding[path_key]).exists():
                missing_paths.append(binding[path_key])
        provider_id = str(job.get("provider_id") or "")
        if provider_id not in topology_text:
            missing_provider_skill_ids.append(provider_id)
        jobs.append({**job, "execution_binding": binding})

    manifest = {
        "schema_version": "krk_strategy_owner_contrast_execution_manifest.v0",
        "causal_status": "non_causal_execution_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN), str(REVIEW), "reports/stage6_overlay_validation_manifest.md"],
        "binding_summary": {
            "job_count": len(jobs),
            "missing_path_count": len(set(missing_paths)),
            "missing_paths": sorted(set(missing_paths)),
            "missing_provider_skill_ids": sorted(set(missing_provider_skill_ids)),
            "all_bindings_valid": not missing_paths and not missing_provider_skill_ids,
            "stage7_jobs": sum(1 for job in jobs if job.get("source_stage") == "stage7"),
        },
        "jobs": jobs,
        "decision": {
            "status": (
                "contrast_execution_manifest_bound_review_required"
                if not missing_paths and not missing_provider_skill_ids
                else "contrast_execution_manifest_binding_invalid"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "labels_allowed_now": False,
            "recommended_next_step": (
                "review_contrast_execution_manifest_before_labels"
                if not missing_paths and not missing_provider_skill_ids
                else "fix_contrast_execution_manifest_bindings"
            ),
        },
        "blocked_next_steps": [
            "run_labels_without_manifest_review",
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("causal_status") != "non_causal_execution_manifest":
        raise ValueError("manifest must remain non-causal")
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
        if manifest.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for job in manifest.get("jobs") or []:
        if job.get("source_stage") == "stage7":
            raise ValueError("Stage 7 jobs must not be bound")
        binding = job.get("execution_binding") or {}
        if binding.get("composition_profile") != "handoff_composition_v1":
            raise ValueError("jobs must bind to handoff_composition_v1")
        if binding.get("execution_mode") != "force_provider_first_white_move_then_release":
            raise ValueError("unexpected execution mode")


def render_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["binding_summary"]
    lines = [
        "# KRK Strategy Owner Contrast Execution Manifest v0",
        "",
        "This is a non-causal execution-binding manifest. It does not run labels, "
        "change runtime behavior, implement a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Binding Summary",
        "",
        f"- Job count: `{summary['job_count']}`",
        f"- All bindings valid: `{summary['all_bindings_valid']}`",
        f"- Missing path count: `{summary['missing_path_count']}`",
        f"- Missing provider skill IDs: `{summary['missing_provider_skill_ids']}`",
        f"- Stage 7 jobs: `{summary['stage7_jobs']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{manifest['decision']['status']}`",
        f"- Recommended next step: `{manifest['decision']['recommended_next_step']}`",
        "- Labels are not allowed until this manifest is reviewed.",
        "",
        "## Bound Jobs",
        "",
    ]
    for job in manifest["jobs"]:
        binding = job["execution_binding"]
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` provider=`{job['provider_id']}` "
            f"version=`{binding['provider_version']}` topology=`{binding['topology_version']}`"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    manifest = build_manifest()
    (ROOT / OUT_JSON).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(manifest), encoding="utf-8")
    print(json.dumps(manifest["binding_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Bind KRK forced-provider control label jobs to explicit topologies.

This creates an execution manifest only. It does not run labels or change
runtime behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PLAN = Path("reports/krk_forced_provider_control_label_plan_v0.json")

STAGE5_TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json"
)
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
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _binding_for_job(job: dict[str, Any]) -> dict[str, Any]:
    stage = str(job.get("source_stage") or "")
    provider_id = str(job.get("provider_id") or "")
    if stage == "stage5":
        topology = STAGE5_TOPOLOGY
        topology_version = "stage5_validated_v1"
        provider_version = "stage5_validated_v1"
        source_checkpoint = STAGE5_CHECKPOINT
    elif stage == "stage6":
        topology = STAGE6_TOPOLOGY
        topology_version = "stage6_overlay_composed_v1"
        provider_version = "stage6_overlay_v1" if provider_id == "krk.drive_to_edge" else "stage5_validated_v1"
        source_checkpoint = STAGE6_CHECKPOINT if provider_id == "krk.drive_to_edge" else STAGE5_CHECKPOINT
    else:
        raise ValueError(f"unsupported stage for forced-provider control label: {stage}")
    return {
        "topology_path": str(topology),
        "topology_version": topology_version,
        "composition_profile": "handoff_composition_v1",
        "provider_version": provider_version,
        "source_checkpoint": str(source_checkpoint),
        "execution_mode": "force_provider_first_white_move_then_release",
        "black_policy": "adversarial",
        "max_ticks": 200,
        "suggestion_limit": 10,
        "early_stop_stable_suggestions": 3,
        "enable_diagnostic_caches": True,
        "profile_settings": dict(PROFILE_SETTINGS),
    }


def build_manifest(repo_root: Path) -> dict[str, Any]:
    plan = _load_json(repo_root / PLAN)
    if plan.get("causal_status") != "non_causal_label_plan":
        raise ValueError("label plan must remain non-causal")
    bound_jobs = []
    missing_paths = []
    for job in plan.get("jobs") or []:
        binding = _binding_for_job(job)
        for path_key in ("topology_path", "source_checkpoint"):
            path = repo_root / binding[path_key]
            if not path.exists():
                missing_paths.append(str(path))
        bound_jobs.append({**job, "execution_binding": binding})
    manifest = {
        "schema_version": "krk_forced_provider_label_execution_manifest.v0",
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
        "source_artifacts": [str(PLAN), "reports/stage6_overlay_validation_manifest.md"],
        "binding_summary": {
            "job_count": len(bound_jobs),
            "missing_path_count": len(missing_paths),
            "missing_paths": missing_paths,
            "all_bindings_valid": not missing_paths,
        },
        "jobs": bound_jobs,
        "recommended_next_step": (
            "run_bounded_forced_provider_control_labels"
            if not missing_paths
            else "resolve_missing_topology_bindings"
        ),
        "blocked_next_steps": [
            "runtime_arbiter",
            "runtime_internal_terminal",
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
    if not manifest["binding_summary"]["all_bindings_valid"]:
        return
    for job in manifest.get("jobs") or []:
        binding = job.get("execution_binding") or {}
        if binding.get("composition_profile") != "handoff_composition_v1":
            raise ValueError("jobs must bind to handoff_composition_v1")
        if binding.get("execution_mode") != "force_provider_first_white_move_then_release":
            raise ValueError("unexpected forced-provider execution mode")


def render_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["binding_summary"]
    lines = [
        "# KRK Forced Provider Label Execution Manifest v0",
        "",
        "This is a non-causal execution-binding manifest. It does not run labels, "
        "change runtime behavior, implement an arbiter, promote Stage 7, or train Stage 8.",
        "",
        "## Binding Summary",
        "",
        f"- Job count: `{summary['job_count']}`",
        f"- All bindings valid: `{summary['all_bindings_valid']}`",
        f"- Missing path count: `{summary['missing_path_count']}`",
        "",
        "## Bound Jobs",
        "",
    ]
    for job in manifest["jobs"]:
        binding = job["execution_binding"]
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` provider=`{job['provider_id']}` "
            f"topology=`{binding['topology_version']}` profile=`{binding['composition_profile']}`"
        )
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            f"`{manifest['recommended_next_step']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(manifest: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_forced_provider_label_execution_manifest_v0.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_forced_provider_label_execution_manifest_v0.md").write_text(
        render_markdown(manifest), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    manifest = build_manifest(repo_root)
    write_outputs(manifest, report_root)
    print(json.dumps(manifest["binding_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

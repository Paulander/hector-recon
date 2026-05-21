#!/usr/bin/env python3
"""Generate a bounded manifest for historical non-stage0 ownership replays.

This is a non-causal source-diversity diagnostic. It asks whether states that
previously selected non-stage0 owners still do so under the current protected
handoff profile. It does not change runtime behavior or train a selector.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_krk_strategy_arbiter_out_of_sample_execution_manifest import (  # noqa: E402
    STAGE_CONFIGS,
    _binding_for_stage,
)
from recon_lite_chess.routing import stable_record_id  # noqa: E402


SOURCE = Path("reports/krk_strategy_arbiter_labeled_observation_controls_v0.json")
OUT_JSON = Path("reports/krk_targeted_non_stage0_ownership_manifest_v0.json")
OUT_MD = Path("reports/krk_targeted_non_stage0_ownership_manifest_v0.md")

TARGET_PROVIDERS_EXCLUDED = {"", "krk.stage0_basin", "None", "none", "null"}


def _load_json(repo_root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _historical_selected_provider(record: dict[str, Any]) -> str:
    observation = record.get("observation") or {}
    return str(
        record.get("selected_provider_before_observation")
        or observation.get("selected_provider_before_observation")
        or observation.get("selected_provider")
        or ""
    )


def _historical_selected_move(record: dict[str, Any]) -> str:
    observation = record.get("observation") or {}
    return str(
        record.get("selected_move_before_observation")
        or observation.get("selected_move_before_observation")
        or observation.get("selected_move")
        or ""
    )


def _job_for_record(record: dict[str, Any], *, horizon: int) -> dict[str, Any]:
    stage = str(record.get("source_stage") or "")
    historical_provider = _historical_selected_provider(record)
    state_id = str(record.get("state_id") or "")
    return {
        "schema_version": "krk_targeted_non_stage0_ownership_job.v0",
        "job_id": stable_record_id(
            "job.krk.targeted_non_stage0_ownership",
            state_id,
            stage,
            historical_provider,
        ),
        "causal_status": "non_causal_label_job",
        "labels_generated": False,
        "runtime_behavior_changed": False,
        "stage7_training_row": False,
        "source_kind": "historical_non_stage0_selected_owner",
        "source_artifact": str(SOURCE),
        "frame_id": record.get("frame_id"),
        "state_id": state_id,
        "source_stage": stage,
        "stage_role": STAGE_CONFIGS[stage]["stage_role"],
        "active_landmark_label": record.get("active_landmark_label") or STAGE_CONFIGS[stage]["label"],
        "fen": record.get("fen"),
        "historical_selected_provider": historical_provider,
        "historical_selected_move": _historical_selected_move(record),
        "historical_negative_providers": record.get("negative_providers") or [],
        "historical_known_label_count": record.get("known_label_count"),
        "target_label_semantics": [
            "current_profile_selected_owner_h40",
            "historical_owner_preservation",
            "current_profile_owner_collapse_check",
            "forced_current_selected_provider_h40",
        ],
        "horizon": horizon,
        "diagnostic_caches_required": True,
        "parallel_workers_allowed": True,
        "exhaustive_legal_first_sweeps": False,
        "purpose": (
            "Check whether historically non-stage0 protected-control owners are "
            "preserved by the current handoff profile before selector training."
        ),
        "execution_binding": _binding_for_stage(stage),
    }


def build_manifest(repo_root: Path, *, horizon: int = 40, max_jobs: int = 4) -> dict[str, Any]:
    source = _load_json(repo_root, SOURCE)
    if source.get("causal_status") != "non_causal_labeled_observation_controls":
        raise ValueError("source controls must remain non-causal")

    selected_records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for record in source.get("records") or []:
        stage = str(record.get("source_stage") or "")
        provider = _historical_selected_provider(record)
        state_id = str(record.get("state_id") or "")
        if stage == "stage7" or stage not in STAGE_CONFIGS:
            continue
        if provider in TARGET_PROVIDERS_EXCLUDED:
            continue
        key = (state_id, provider)
        if key in seen:
            continue
        seen.add(key)
        selected_records.append(record)

    selected_records = sorted(
        selected_records,
        key=lambda item: (
            str(item.get("source_stage") or ""),
            _historical_selected_provider(item),
            str(item.get("state_id") or ""),
        ),
    )[:max_jobs]

    jobs = [_job_for_record(record, horizon=horizon) for record in selected_records]
    missing_paths: list[str] = []
    for job in jobs:
        binding = job["execution_binding"]
        for path_key in ("topology_path", "source_checkpoint"):
            path = repo_root / str(binding[path_key])
            if not path.exists():
                missing_paths.append(str(path))

    provider_counts = Counter(job["historical_selected_provider"] for job in jobs)
    stage_counts = Counter(job["source_stage"] for job in jobs)
    manifest = {
        "schema_version": "krk_targeted_non_stage0_ownership_manifest.v0",
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
        "source_artifacts": [str(SOURCE)],
        "selection_policy": {
            "horizon": horizon,
            "max_jobs": max_jobs,
            "stage7_training_rows": 0,
            "selected_provider_excluded": sorted(TARGET_PROVIDERS_EXCLUDED),
            "prefer_historical_non_stage0_selected_owners": True,
        },
        "binding_summary": {
            "job_count": len(jobs),
            "job_count_by_stage": dict(sorted(stage_counts.items())),
            "historical_selected_provider_counts": dict(sorted(provider_counts.items())),
            "missing_path_count": len(missing_paths),
            "missing_paths": sorted(missing_paths),
            "all_bindings_valid": not missing_paths,
            "max_jobs_respected": len(jobs) <= max_jobs,
            "stage7_job_count": sum(1 for job in jobs if job.get("source_stage") == "stage7"),
        },
        "jobs": jobs,
        "decision": {
            "status": (
                "targeted_non_stage0_manifest_ready"
                if jobs and not missing_paths
                else "targeted_non_stage0_manifest_blocked"
            ),
            "execute_labels_now": bool(jobs and not missing_paths),
            "runtime_arbiter_allowed": False,
            "selector_training_allowed": False,
            "recommended_next_step": (
                "run_bounded_current_profile_labels_for_historical_non_stage0_owners"
                if jobs and not missing_paths
                else "review_missing_non_stage0_sources_or_bindings"
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
        if job.get("causal_status") != "non_causal_label_job":
            raise ValueError("jobs must remain non-causal")
        if job.get("source_stage") == "stage7":
            raise ValueError("targeted non-stage0 jobs must exclude Stage 7")
        if job.get("historical_selected_provider") in TARGET_PROVIDERS_EXCLUDED:
            raise ValueError("targeted jobs must use historical non-stage0 providers")
        binding = job.get("execution_binding") or {}
        if binding.get("composition_profile") != "handoff_composition_v1":
            raise ValueError("jobs must bind to handoff_composition_v1")
        if binding.get("topology_version") != "stage6_overlay_composed_v1":
            raise ValueError("jobs must use the protected composed topology")


def render_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["binding_summary"]
    lines = [
        "# KRK Targeted Non-Stage0 Ownership Manifest v0",
        "",
        "This manifest is a bounded non-causal source-diversity diagnostic. It "
        "replays historical protected-control states that selected non-stage0 "
        "owners and checks current-profile ownership without changing runtime behavior.",
        "",
        "## Summary",
        "",
        f"- Job count: `{summary['job_count']}`",
        f"- Jobs by stage: `{summary['job_count_by_stage']}`",
        f"- Historical selected provider counts: `{summary['historical_selected_provider_counts']}`",
        f"- All bindings valid: `{summary['all_bindings_valid']}`",
        f"- Stage 7 job count: `{summary['stage7_job_count']}`",
        f"- Decision: `{manifest['decision']['status']}`",
        "",
        "## Jobs",
        "",
    ]
    for job in manifest["jobs"]:
        lines.append(
            f"- `{job['state_id']}` stage=`{job['source_stage']}` "
            f"historical_provider=`{job['historical_selected_provider']}` "
            f"historical_move=`{job.get('historical_selected_move')}`"
        )
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            f"`{manifest['decision']['recommended_next_step']}`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(repo_root: Path, manifest: dict[str, Any]) -> None:
    (repo_root / OUT_JSON).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (repo_root / OUT_MD).write_text(render_markdown(manifest), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument("--max-jobs", type=int, default=4)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    manifest = build_manifest(repo_root, horizon=args.horizon, max_jobs=args.max_jobs)
    write_outputs(repo_root, manifest)
    print(json.dumps(manifest["binding_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Write retry1 protected-stack snapshot and rollback manifest.

This manifest records the current protected checkpoint paths and retry1 candidate
paths. It deliberately does not copy, replace, or promote any checkpoint.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

STAGE4_REVIEW = Path("reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json")
PRESERVATION_CHECKS = Path("reports/krk_clean_retrain_retry1_preservation_checks_v0.json")
OUT_JSON = Path("reports/krk_clean_retrain_retry1_protected_stack_snapshot_manifest_v0.json")
OUT_MD = Path("reports/krk_clean_retrain_retry1_protected_stack_snapshot_manifest_v0.md")


CURRENT_PROTECTED_STACK = {
    "stage5_fence": {
        "topology": "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/topology/krk_entry_topology.json",
        "provider": "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl",
        "run_manifest": "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/run_manifest.json",
    },
    "stage6_drive_overlay": {
        "topology": "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json",
        "promotion_eval": "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/promotion_eval_stage6_overlay.json",
        "stage6_validation": "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage6_drive_overlay_300_seed7_h40.json",
        "stage5_guardrail": "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage5_fence_overlay_300_seed7_h40.json",
        "stage4_caveat_control": "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/stage4_wrong_tempo_stage5_base_control_300_seed7_h40.json",
    },
}


RETRY1_CANDIDATE_STACK = {
    "stage5_fence": {
        "topology": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage5_fence_handoff/topology/krk_entry_topology.json",
        "provider": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage5_fence_handoff/baseline/best_by_stage/fence_established.pkl",
        "run_manifest": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage5_fence_handoff/baseline/curriculum_history.json",
    },
    "stage6_drive_overlay": {
        "topology": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/topology/krk_entry_topology.json",
        "provider": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_drive_overlay_candidate/baseline/best_by_stage/drive_to_edge.pkl",
        "promotion_eval": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/promotion_eval_stage6_overlay_profile_bonus.json",
        "stage6_validation": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/stage6_drive_overlay_300_seed7_h40_profile_bonus.json",
        "stage5_guardrail": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/stage5_fence_overlay_300_seed7_h40_profile_bonus.json",
        "stage4_caveat_control": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/stage4_wrong_tempo_stage5_base_control_300_seed7_h40_profile_bonus.json",
    },
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _exists_map(paths: dict[str, dict[str, str]]) -> dict[str, dict[str, bool]]:
    return {
        stack_name: {key: (ROOT / value).exists() for key, value in entries.items()}
        for stack_name, entries in paths.items()
    }


def build_payload() -> dict[str, Any]:
    stage4 = _load(STAGE4_REVIEW)
    preservation = _load(PRESERVATION_CHECKS)
    protected_exists = _exists_map(CURRENT_PROTECTED_STACK)
    candidate_exists = _exists_map(RETRY1_CANDIDATE_STACK)
    missing_paths = [
        f"current_protected_stack.{stack}.{key}"
        for stack, entries in protected_exists.items()
        for key, exists in entries.items()
        if not exists
    ] + [
        f"retry1_candidate_stack.{stack}.{key}"
        for stack, entries in candidate_exists.items()
        for key, exists in entries.items()
        if not exists
    ]
    return {
        "schema_version": "krk_clean_retrain_retry1_protected_stack_snapshot_manifest.v0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "retry1_protected_stack_snapshot_manifest_ready_no_replacement",
        "source_artifacts": [str(STAGE4_REVIEW), str(PRESERVATION_CHECKS)],
        "upstream_status": {
            "stage4_caveat_control_review": stage4.get("status"),
            "preservation_checks": preservation.get("status"),
        },
        "current_protected_stack": CURRENT_PROTECTED_STACK,
        "retry1_candidate_stack": RETRY1_CANDIDATE_STACK,
        "path_existence": {
            "current_protected_stack": protected_exists,
            "retry1_candidate_stack": candidate_exists,
            "missing_paths": missing_paths,
        },
        "rollback_requirements": [
            "Record exact current protected topology/provider paths before any replacement.",
            "Do not delete or overwrite current protected snapshots.",
            "Any replacement packet must name the rollback source paths and candidate target paths explicitly.",
            "A rollback must restore the previous protected topology/provider pointers without retraining.",
            "Stage 7 remains held-out/quarantined and cannot be included in the replacement stack.",
        ],
        "decision": {
            "manifest_records_current_protected_stack": True,
            "manifest_records_retry1_candidate_stack": True,
            "all_referenced_paths_exist": not missing_paths,
            "clean_stack_replacement_allowed_by_manifest": False,
            "recommended_next_step": "write_clean_stack_replacement_review_packet_before_any_file_change",
        },
        "invariants": {
            "files_copied_or_replaced": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion": False,
            "stage8_training": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    current = "\n".join(
        f"- `{stack}`: " + ", ".join(f"{key}=`{value}`" for key, value in entries.items())
        for stack, entries in payload["current_protected_stack"].items()
    )
    candidate = "\n".join(
        f"- `{stack}`: " + ", ".join(f"{key}=`{value}`" for key, value in entries.items())
        for stack, entries in payload["retry1_candidate_stack"].items()
    )
    rollback = "\n".join(f"- {item}" for item in payload["rollback_requirements"])
    missing = payload["path_existence"]["missing_paths"]
    missing_text = "\n".join(f"- `{item}`" for item in missing) if missing else "- none"
    return f"""# KRK Retry1 Protected Stack Snapshot Manifest v0

Status: `{payload['status']}`

## Decision

- Manifest records current protected stack: `{payload['decision']['manifest_records_current_protected_stack']}`
- Manifest records retry1 candidate stack: `{payload['decision']['manifest_records_retry1_candidate_stack']}`
- All referenced paths exist: `{payload['decision']['all_referenced_paths_exist']}`
- Clean stack replacement allowed by manifest: `{payload['decision']['clean_stack_replacement_allowed_by_manifest']}`
- Recommended next step: `{payload['decision']['recommended_next_step']}`

## Current Protected Stack

{current}

## Retry1 Candidate Stack

{candidate}

## Missing Paths

{missing_text}

## Rollback Requirements

{rollback}

## Boundary

This manifest is reference-only. It does not copy, replace, delete, promote, train, route, score, mutate topology, or change runtime defaults.
"""


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "json_output": str(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()

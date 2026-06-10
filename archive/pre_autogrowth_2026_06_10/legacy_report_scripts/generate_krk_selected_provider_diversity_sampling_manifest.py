#!/usr/bin/env python3
"""Generate bounded protected selected-provider diversity sampling manifest.

This creates non-causal selection-observation jobs only. It does not execute
selection, run playout labels, implement a selector, promote Stage 7, or train
Stage 8.
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import test_krk_landmark_progress as diag  # noqa: E402
from recon_lite_chess.routing import stable_record_id  # noqa: E402


PLAN = Path("reports/krk_selected_provider_diversity_evidence_plan_v0.json")
SCAN = Path("reports/krk_selected_provider_diversity_replay_free_scan_v0.json")
OUT_JSON = Path("reports/krk_selected_provider_diversity_sampling_manifest_v0.json")
OUT_MD = Path("reports/krk_selected_provider_diversity_sampling_manifest_v0.md")

STAGE6_COMPOSED_TOPOLOGY = Path(
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

STAGE_CONFIGS = {
    "stage4": {
        "label": "edge_trap_wrong_tempo",
        "provider_version": "stage5_validated_v1",
        "source_checkpoint": STAGE5_CHECKPOINT,
    },
    "stage5": {
        "label": "fence_established",
        "provider_version": "stage5_validated_v1",
        "source_checkpoint": STAGE5_CHECKPOINT,
    },
    "stage6": {
        "label": "drive_to_edge",
        "provider_version": "stage6_overlay_v1",
        "source_checkpoint": STAGE6_CHECKPOINT,
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _state_id_from_board(board: Any) -> str:
    return stable_record_id("state", board.board_fen(), board.turn)


def _binding_for_stage(stage: str) -> dict[str, Any]:
    config = STAGE_CONFIGS[stage]
    return {
        "topology_path": str(STAGE6_COMPOSED_TOPOLOGY),
        "topology_version": "stage6_overlay_composed_v1",
        "composition_profile": "handoff_composition_v1",
        "provider_version": config["provider_version"],
        "source_checkpoint": str(config["source_checkpoint"]),
        "execution_mode": "observe_selected_provider_only",
        "max_ticks": 200,
        "suggestion_limit": 10,
        "early_stop_stable_suggestions": 3,
        "enable_diagnostic_caches": True,
        "profile_settings": dict(PROFILE_SETTINGS),
    }


def build_manifest(
    *,
    max_jobs: int = 45,
    per_stage_max: int = 15,
    base_seed: int = 19,
    max_sample_index: int = 500,
) -> dict[str, Any]:
    plan = _load_json(PLAN)
    scan = _load_json(SCAN)
    if plan.get("causal_status") != "non_causal_design_plan":
        raise ValueError("evidence plan must remain non-causal")
    if scan.get("causal_status") != "non_causal_scan":
        raise ValueError("replay-free scan must remain non-causal")

    jobs = []
    stage_counts: Counter[str] = Counter()
    seen_state_ids: set[str] = set()
    for stage, config in STAGE_CONFIGS.items():
        source_names = tuple(diag.source_stage_names_for_label(config["label"]))
        for sample_index in range(max_sample_index):
            if len(jobs) >= max_jobs or stage_counts[stage] >= per_stage_max:
                break
            sample_seed = base_seed * 1_000_000 + sample_index
            sample_rng = random.Random(sample_seed)
            random.seed(sample_seed)
            board = diag.select_eval_position(
                sample_rng,
                config["label"],
                "curriculum",
                source_names,
            )
            state_id = _state_id_from_board(board)
            if state_id in seen_state_ids:
                continue
            seen_state_ids.add(state_id)
            stage_counts[stage] += 1
            jobs.append(
                {
                    "schema_version": "krk_selected_provider_diversity_sampling_job.v0",
                    "causal_status": "non_causal_selection_observation_job",
                    "labels_generated": False,
                    "runtime_behavior_changed": False,
                    "job_id": stable_record_id(
                        "job.krk.selected_provider_diversity",
                        state_id,
                        stage,
                        sample_index,
                    ),
                    "source_stage": stage,
                    "active_landmark_label": config["label"],
                    "state_id": state_id,
                    "frame_id": f"cp.krk.{state_id}",
                    "fen": board.fen(),
                    "generation": {
                        "base_seed": base_seed,
                        "sample_index": sample_index,
                        "sample_seed": sample_seed,
                        "position_mode": "curriculum",
                        "source_stage_names": list(source_names),
                    },
                    "target_observation": "selected_provider_family",
                    "stage7_training_row": False,
                    "execution_binding": _binding_for_stage(stage),
                }
            )

    missing_paths = []
    for job in jobs:
        binding = job["execution_binding"]
        for path_key in ("topology_path", "source_checkpoint"):
            if not (ROOT / binding[path_key]).exists():
                missing_paths.append(binding[path_key])

    manifest = {
        "schema_version": "krk_selected_provider_diversity_sampling_manifest.v0",
        "causal_status": "non_causal_sampling_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN), str(SCAN)],
        "selection_policy": {
            "max_jobs": max_jobs,
            "per_stage_max": per_stage_max,
            "base_seed": base_seed,
            "max_sample_index": max_sample_index,
            "stage7_jobs": 0,
            "observation_only": True,
            "playout_labels": False,
        },
        "binding_summary": {
            "job_count": len(jobs),
            "job_count_by_stage": dict(sorted(stage_counts.items())),
            "missing_path_count": len(set(missing_paths)),
            "missing_paths": sorted(set(missing_paths)),
            "all_bindings_valid": not missing_paths,
        },
        "jobs": jobs,
        "decision": {
            "status": (
                "selected_provider_diversity_sampling_manifest_review_required"
                if jobs and not missing_paths
                else "selected_provider_diversity_sampling_manifest_invalid"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "observations_allowed_now": False,
            "recommended_next_step": (
                "review_selected_provider_diversity_sampling_manifest"
                if jobs and not missing_paths
                else "fix_selected_provider_diversity_sampling_manifest"
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
    if manifest.get("causal_status") != "non_causal_sampling_manifest":
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
            raise ValueError("Stage 7 jobs must remain excluded")
        if (job.get("execution_binding") or {}).get("execution_mode") != "observe_selected_provider_only":
            raise ValueError("sampling jobs must be selection-observation only")


def render_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["binding_summary"]
    lines = [
        "# KRK Selected Provider Diversity Sampling Manifest v0",
        "",
        "This is a bounded non-causal selection-observation manifest. It does not "
        "run observations, run playout labels, implement a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
        f"- Jobs: `{summary['job_count']}`",
        f"- Jobs by stage: `{summary['job_count_by_stage']}`",
        f"- All bindings valid: `{summary['all_bindings_valid']}`",
        f"- Missing paths: `{summary['missing_paths']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{manifest['decision']['status']}`",
        f"- Recommended next step: `{manifest['decision']['recommended_next_step']}`",
        "- Runtime arbiter and selector sandbox remain blocked.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    manifest = build_manifest()
    (ROOT / OUT_JSON).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(manifest), encoding="utf-8")
    print(json.dumps(manifest["binding_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

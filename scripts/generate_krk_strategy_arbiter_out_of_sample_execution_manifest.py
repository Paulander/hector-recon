#!/usr/bin/env python3
"""Generate KRK strategy-arbiter out-of-sample control execution manifest.

This creates bounded, non-causal label jobs only. It does not execute h40
labels, change runtime defaults, implement an arbiter, promote Stage 7, train
Stage 8, or mutate topology.
"""

from __future__ import annotations

import argparse
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


PLAN = Path("reports/krk_strategy_arbiter_out_of_sample_control_plan_v0.json")
PLAN_REVIEW = Path("reports/krk_strategy_arbiter_out_of_sample_plan_review_v0.json")
BALANCED = Path("reports/krk_selector_balanced_label_dataset_v1.json")
FRAMES_WITH_FORCED = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_out_of_sample_execution_manifest_v0.md")

STAGE4_CHECKPOINT = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage2c_clean/baseline/best_by_stage/"
    "edge_trap_wrong_tempo.pkl"
)
STAGE5_CHECKPOINT = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/"
    "fence_established.pkl"
)
STAGE6_CHECKPOINT = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/"
    "best_by_stage/drive_to_edge.pkl"
)
STAGE6_COMPOSED_TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/"
    "krk_entry_topology.json"
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
        "primary_provider_skill_id": "krk.edge_trap_wrong_tempo",
        "provider_version": "stage5_validated_v1",
        "source_checkpoint": STAGE4_CHECKPOINT,
        "topology_component": "stage5_frozen_base_provider_pack_with_skill_ids",
        "stage_role": "stage4_wrong_tempo_control",
    },
    "stage5": {
        "label": "fence_established",
        "primary_provider_skill_id": "krk.fence_established",
        "provider_version": "stage5_validated_v1",
        "source_checkpoint": STAGE5_CHECKPOINT,
        "topology_component": "stage5_frozen_base_provider_pack_with_skill_ids",
        "stage_role": "stage5_fence_handoff",
    },
    "stage6": {
        "label": "drive_to_edge",
        "primary_provider_skill_id": "krk.drive_to_edge",
        "provider_version": "stage6_overlay_v1",
        "source_checkpoint": STAGE6_CHECKPOINT,
        "topology_component": "stage6_overlay_composed",
        "stage_role": "stage6_drive_to_edge",
    },
}


def _load_json(repo_root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _result(label: dict[str, Any]) -> str | None:
    return label.get("result") or label.get("playout_result") or label.get("label")


def _used_state_ids(balanced: dict[str, Any]) -> set[str]:
    return {
        str(row.get("state_id"))
        for row in balanced.get("rows", []) or []
        if row.get("state_id")
    }


def _replay_free_candidates(
    frames: list[dict[str, Any]], used_state_ids: set[str]
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for frame in frames:
        stage = str(frame.get("source_stage") or "")
        state_id = str(frame.get("state_id") or "")
        if stage not in STAGE_CONFIGS or state_id in used_state_ids or state_id in seen:
            continue
        selected_label = None
        for proposal in frame.get("strategy_proposal_frames") or []:
            label = proposal.get("known_outcome_label") or {}
            if not isinstance(label, dict):
                continue
            result = _result(label)
            if result:
                selected_label = {
                    "provider_id": proposal.get("provider_id"),
                    "move_uci": proposal.get("move_uci"),
                    "result": result,
                    "label_source": label.get("source") or "existing_provider_label",
                }
                break
        if selected_label is None:
            continue
        seen.add(state_id)
        candidates.append(
            {
                "source_kind": "replay_free_existing_control",
                "state_id": state_id,
                "frame_id": frame.get("frame_id"),
                "source_stage": stage,
                "active_landmark_label": frame.get("active_landmark_label")
                or STAGE_CONFIGS[stage]["label"],
                "fen": frame.get("fen"),
                "prior_label": selected_label,
            }
        )
    return candidates


def _state_id_from_board(board: Any) -> str:
    return stable_record_id("state", board.board_fen(), board.turn)


def _generated_candidates(
    *,
    used_state_ids: set[str],
    existing_state_ids: set[str],
    per_stage_target: int,
    base_seed: int,
    max_sample_index: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()
    for stage, config in STAGE_CONFIGS.items():
        source_names = tuple(diag.source_stage_names_for_label(str(config["label"])))
        for sample_index in range(max_sample_index):
            if stage_counts[stage] >= per_stage_target:
                break
            sample_seed = base_seed * 1_000_000 + sample_index
            sample_rng = random.Random(sample_seed)
            random.seed(sample_seed)
            board = diag.select_eval_position(
                sample_rng,
                str(config["label"]),
                "curriculum",
                source_names,
            )
            state_id = _state_id_from_board(board)
            if state_id in used_state_ids or state_id in existing_state_ids:
                continue
            existing_state_ids.add(state_id)
            stage_counts[stage] += 1
            candidates.append(
                {
                    "source_kind": "deterministic_curriculum_sample",
                    "state_id": state_id,
                    "frame_id": f"cp.krk.{state_id}",
                    "source_stage": stage,
                    "active_landmark_label": config["label"],
                    "fen": board.fen(),
                    "generation": {
                        "base_seed": base_seed,
                        "sample_index": sample_index,
                        "sample_seed": sample_seed,
                        "sample_seed_formula": "base_seed * 1_000_000 + sample_index",
                        "position_mode": "curriculum",
                        "source_stage_names": list(source_names),
                    },
                    "prior_label": None,
                }
            )
    return candidates


def _binding_for_stage(stage: str) -> dict[str, Any]:
    config = STAGE_CONFIGS[stage]
    return {
        "topology_path": str(STAGE6_COMPOSED_TOPOLOGY),
        "topology_version": "stage6_overlay_composed_v1",
        "composition_profile": "handoff_composition_v1",
        "topology_component": config["topology_component"],
        "primary_provider_skill_id": config["primary_provider_skill_id"],
        "provider_version": config["provider_version"],
        "source_checkpoint": str(config["source_checkpoint"]),
        "selected_provider_resolved_at_execution": True,
        "execution_modes": [
            "selected_playout_h40",
            "force_selected_provider_first_white_move_then_release_h40",
            "same_move_provider_compatibility_when_available",
            "shadow_candidate_delta",
        ],
        "black_policy": "adversarial",
        "max_ticks": 200,
        "suggestion_limit": 10,
        "early_stop_stable_suggestions": 3,
        "enable_diagnostic_caches": True,
        "trace_mode": "failures_only",
        "profile_settings": dict(PROFILE_SETTINGS),
    }


def _job_for_candidate(candidate: dict[str, Any], horizon: int) -> dict[str, Any]:
    stage = str(candidate["source_stage"])
    return {
        "schema_version": "krk_strategy_arbiter_out_of_sample_control_job.v0",
        "job_id": stable_record_id(
            "job.krk.out_of_sample_control",
            candidate["state_id"],
            stage,
            candidate.get("source_kind"),
        ),
        "causal_status": "non_causal_label_job",
        "labels_generated": False,
        "runtime_behavior_changed": False,
        "stage7_training_row": False,
        "source_kind": candidate.get("source_kind"),
        "frame_id": candidate.get("frame_id"),
        "state_id": candidate.get("state_id"),
        "source_stage": stage,
        "stage_role": STAGE_CONFIGS[stage]["stage_role"],
        "active_landmark_label": candidate.get("active_landmark_label"),
        "fen": candidate.get("fen"),
        "generation": candidate.get("generation"),
        "prior_replay_free_label": candidate.get("prior_label"),
        "target_label_semantics": [
            "selected_playout_success",
            "forced_provider_conversion_for_selected_provider",
            "same_move_provider_compatibility_when_available",
            "guardrail_safe_ownership",
            "shadow_candidate_delta",
        ],
        "horizon": horizon,
        "diagnostic_caches_required": True,
        "parallel_workers_allowed": True,
        "exhaustive_legal_first_sweeps": False,
        "purpose": (
            "Collect bounded out-of-sample protected-control labels before any "
            "KRK strategy-arbiter sandbox review."
        ),
        "execution_binding": _binding_for_stage(stage),
    }


def build_manifest(
    repo_root: Path,
    *,
    max_states: int | None = None,
    per_stage_max: int | None = None,
    base_seed: int = 7,
    max_sample_index: int = 200,
) -> dict[str, Any]:
    plan = _load_json(repo_root, PLAN)
    review = _load_json(repo_root, PLAN_REVIEW)
    balanced = _load_json(repo_root, BALANCED)
    frames_payload = _load_json(repo_root, FRAMES_WITH_FORCED)
    if plan.get("causal_status") != "non_causal_collection_plan":
        raise ValueError("control plan must remain non-causal")
    if review.get("causal_status") != "non_causal_plan_review":
        raise ValueError("plan review must remain non-causal")
    if frames_payload.get("causal_status") not in {
        "non_causal_filtered_frame_export",
        "non_causal_augmented_frame_export",
    }:
        raise ValueError("source frames must remain non-causal")

    bounds = plan.get("collection_bounds") or {}
    max_states = int(max_states or bounds.get("max_states") or 12)
    per_stage_max = int(per_stage_max or bounds.get("per_stage_max") or 4)
    horizon = int(bounds.get("horizon") or 40)
    used_state_ids = _used_state_ids(balanced)

    replay_free = _replay_free_candidates(frames_payload.get("frames") or [], used_state_ids)
    selected: list[dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()
    seen_state_ids: set[str] = set()
    for candidate in sorted(replay_free, key=lambda item: (item["source_stage"], item["state_id"])):
        stage = str(candidate["source_stage"])
        if len(selected) >= max_states or stage_counts[stage] >= per_stage_max:
            continue
        selected.append(candidate)
        seen_state_ids.add(str(candidate["state_id"]))
        stage_counts[stage] += 1

    generated = _generated_candidates(
        used_state_ids=used_state_ids,
        existing_state_ids=seen_state_ids,
        per_stage_target=per_stage_max,
        base_seed=base_seed,
        max_sample_index=max_sample_index,
    )
    for candidate in generated:
        stage = str(candidate["source_stage"])
        if len(selected) >= max_states or stage_counts[stage] >= per_stage_max:
            continue
        selected.append(candidate)
        stage_counts[stage] += 1

    jobs = [_job_for_candidate(candidate, horizon) for candidate in selected]
    missing_paths: list[str] = []
    for job in jobs:
        binding = job["execution_binding"]
        for path_key in ("topology_path", "source_checkpoint"):
            path = repo_root / str(binding[path_key])
            if not path.exists():
                missing_paths.append(str(path))

    result = {
        "schema_version": "krk_strategy_arbiter_out_of_sample_execution_manifest.v0",
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
        "source_artifacts": [str(PLAN), str(PLAN_REVIEW), str(BALANCED), str(FRAMES_WITH_FORCED)],
        "selection_policy": {
            "max_states": max_states,
            "per_stage_max": per_stage_max,
            "horizon": horizon,
            "base_seed": base_seed,
            "max_sample_index": max_sample_index,
            "excluded_balanced_state_count": len(used_state_ids),
            "stage7_training_rows": 0,
            "prefer_replay_free_existing_controls": True,
            "fill_missing_coverage_with_deterministic_curriculum_samples": True,
        },
        "binding_summary": {
            "job_count": len(jobs),
            "job_count_by_stage": dict(sorted(Counter(job["source_stage"] for job in jobs).items())),
            "job_count_by_source_kind": dict(
                sorted(Counter(job["source_kind"] for job in jobs).items())
            ),
            "missing_path_count": len(missing_paths),
            "missing_paths": sorted(missing_paths),
            "all_bindings_valid": not missing_paths,
            "required_stage_coverage_met": all(stage_counts.get(stage, 0) > 0 for stage in STAGE_CONFIGS),
            "per_stage_max_respected": all(count <= per_stage_max for count in stage_counts.values()),
            "max_states_respected": len(jobs) <= max_states,
        },
        "jobs": jobs,
        "decision": {
            "status": (
                "execution_manifest_ready_for_review"
                if not missing_paths and jobs
                else "execution_manifest_blocked_by_missing_bindings"
            ),
            "execute_labels_now": False,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "review_execution_manifest_before_any_h40_label_run"
                if not missing_paths and jobs
                else "resolve_missing_topology_or_checkpoint_bindings"
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
    validate_manifest(result)
    return result


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
    if any(job.get("source_stage") == "stage7" for job in manifest.get("jobs") or []):
        raise ValueError("out-of-sample control jobs must not include Stage 7 training rows")
    for job in manifest.get("jobs") or []:
        if job.get("causal_status") != "non_causal_label_job":
            raise ValueError("jobs must remain non-causal")
        if job.get("labels_generated") is not False:
            raise ValueError("jobs must not claim generated labels")
        binding = job.get("execution_binding") or {}
        if binding.get("composition_profile") != "handoff_composition_v1":
            raise ValueError("jobs must bind to handoff_composition_v1")
        if binding.get("topology_version") != "stage6_overlay_composed_v1":
            raise ValueError("jobs must use the protected composed topology")
        if binding.get("selected_provider_resolved_at_execution") is not True:
            raise ValueError("selected provider must be resolved during label execution")


def render_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["binding_summary"]
    lines = [
        "# KRK Strategy Arbiter Out-of-Sample Execution Manifest v0",
        "",
        "This is a non-causal execution manifest. It does not run labels, change "
        "runtime behavior, implement a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
        f"- Job count: `{summary['job_count']}`",
        f"- Jobs by stage: `{summary['job_count_by_stage']}`",
        f"- Jobs by source kind: `{summary['job_count_by_source_kind']}`",
        f"- All bindings valid: `{summary['all_bindings_valid']}`",
        f"- Required stage coverage met: `{summary['required_stage_coverage_met']}`",
        f"- Missing path count: `{summary['missing_path_count']}`",
        f"- Decision: `{manifest['decision']['status']}`",
        "",
        "## Bounds",
        "",
        f"- Max states: `{manifest['selection_policy']['max_states']}`",
        f"- Per-stage max: `{manifest['selection_policy']['per_stage_max']}`",
        f"- Horizon: `h{manifest['selection_policy']['horizon']}`",
        f"- Stage 7 training rows: `{manifest['selection_policy']['stage7_training_rows']}`",
        "",
        "## Jobs",
        "",
    ]
    for job in manifest["jobs"]:
        prior = job.get("prior_replay_free_label") or {}
        prior_text = f" prior=`{prior.get('result')}`" if prior else ""
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` state=`{job['state_id']}` "
            f"source=`{job['source_kind']}` label=`{job['active_landmark_label']}`{prior_text}"
        )
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            f"`{manifest['decision']['recommended_next_step']}`",
            "",
            "Do not execute h40 labels until this manifest is reviewed.",
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
    parser.add_argument("--max-states", type=int, default=None)
    parser.add_argument("--per-stage-max", type=int, default=None)
    parser.add_argument("--base-seed", type=int, default=7)
    parser.add_argument("--max-sample-index", type=int, default=200)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    manifest = build_manifest(
        repo_root,
        max_states=args.max_states,
        per_stage_max=args.per_stage_max,
        base_seed=args.base_seed,
        max_sample_index=args.max_sample_index,
    )
    write_outputs(repo_root, manifest)
    print(json.dumps(manifest["binding_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
